# File: py_api_lib/extensions.py
"""
ApiLib Extensions Framework

This module provides a plugin-based extension system for ApiLib that allows
domain-specific functionality to be added while maintaining clean separation
of concerns and backward compatibility.

The extension system is designed to be:
- Completely optional (existing ApiLib works without any extensions)
- Non-intrusive (doesn't break existing functionality)
- Dynamic (extensions can be loaded/unloaded at runtime)
- Domain-agnostic (no hardcoded domain knowledge)
"""

import logging
import importlib
import threading
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Type, Callable, Union
from pathlib import Path


class ApiLibExtension(ABC):
    """
    Base class for all ApiLib extensions.
    
    Extensions provide domain-specific functionality like query builders,
    response parsers, and convenience methods that build on top of the
    core ApiLib functionality.
    
    This is a minimal interface - extensions decide what methods to provide.
    """
    
    def __init__(self, api_lib=None):
        """
        Initialize the extension.
        
        Args:
            api_lib: ApiLib instance this extension is attached to (can be None initially)
        """
        self.api_lib = api_lib
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
    
    def get_extension_name(self) -> str:
        """
        Return unique name for this extension.
        
        Default implementation uses class name with 'Extension' suffix removed.
        Override this method to provide a custom name.
        
        Returns:
            Unique extension name
        """
        class_name = self.__class__.__name__
        if class_name.endswith('Extension'):
            return class_name[:-9].lower()
        return class_name.lower()
    
    def get_methods(self) -> Dict[str, Callable]:
        """
        Return dictionary of methods to inject into ApiLib.
        
        Each key is the method name that will be added to ApiLib,
        each value is the callable method.
        
        Returns:
            Dict mapping method names to bound methods
        """
        return {}
    
    def register_with_api_lib(self, api_lib):
        """
        Register this extension with an ApiLib instance.
        
        This method handles the actual injection of methods into ApiLib.
        
        Args:
            api_lib: ApiLib instance to extend
        """
        self.api_lib = api_lib
        methods = self.get_methods()
        
        for method_name, method_func in methods.items():
            if hasattr(api_lib, method_name):
                self.logger.warning(f"Extension '{self.get_extension_name()}' overriding existing method: {method_name}")
            setattr(api_lib, method_name, method_func)
            
        self.logger.info(f"Registered extension '{self.get_extension_name()}' with {len(methods)} methods")
    
    def unregister_from_api_lib(self, api_lib):
        """
        Unregister this extension from ApiLib instance.
        
        Args:
            api_lib: ApiLib instance to remove extension from
        """
        methods = self.get_methods()
        for method_name in methods.keys():
            if hasattr(api_lib, method_name):
                delattr(api_lib, method_name)
                
        self.api_lib = None
        self.logger.info(f"Unregistered extension '{self.get_extension_name()}'")


class ExtensionRegistry:
    """
    Generic registry for managing extension classes.
    
    This registry has no knowledge of specific domains or extension types.
    It's purely a generic plugin management system.
    """
    
    def __init__(self):
        self.extensions: Dict[str, Type[ApiLibExtension]] = {}
        self.extension_packages: Dict[str, str] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_extension_class(self, extension_class: Type[ApiLibExtension]):
        """
        Register an extension class.
        
        Args:
            extension_class: Extension class to register
        """
        if not issubclass(extension_class, ApiLibExtension):
            raise ValueError(f"Extension class must inherit from ApiLibExtension")
        
        # Create temporary instance to get name
        temp_instance = extension_class()
        name = temp_instance.get_extension_name()
        
        if name in self.extensions:
            self.logger.warning(f"Replacing existing extension: {name}")
        
        self.extensions[name] = extension_class
        self.logger.debug(f"Registered extension class: {name}")
    
    def register_extension_by_path(self, module_path: str, class_name: str = None):
        """
        Register extension by module path.
        
        Args:
            module_path: Python module path (e.g., 'store_extensions.deals')
            class_name: Specific class name, or None to auto-discover
        """
        try:
            module = importlib.import_module(module_path)
            
            if class_name:
                # Register specific class
                if not hasattr(module, class_name):
                    raise AttributeError(f"Class '{class_name}' not found in module '{module_path}'")
                
                ext_class = getattr(module, class_name)
                if not issubclass(ext_class, ApiLibExtension):
                    raise ValueError(f"Class '{class_name}' must inherit from ApiLibExtension")
                
                self.register_extension_class(ext_class)
            else:
                # Auto-discover extension classes in module
                discovered_count = 0
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, ApiLibExtension) and 
                        attr != ApiLibExtension):
                        self.register_extension_class(attr)
                        discovered_count += 1
                
                if discovered_count == 0:
                    self.logger.warning(f"No ApiLibExtension classes found in module: {module_path}")
                else:
                    self.logger.info(f"Auto-discovered {discovered_count} extensions in {module_path}")
                        
        except Exception as e:
            self.logger.error(f"Failed to register extension from {module_path}: {e}")
            raise
    
    def register_extension_package(self, package_name: str):
        """
        Register all extensions from a package.
        
        Args:
            package_name: Package name (e.g., 'store_extensions')
        """
        try:
            package = importlib.import_module(package_name)
            
            # Look for register_extensions function in package
            if hasattr(package, 'register_extensions'):
                register_func = getattr(package, 'register_extensions')
                extensions = register_func()
                
                if not isinstance(extensions, (list, tuple)):
                    raise ValueError(f"register_extensions() must return list of extension classes")
                
                for ext_class in extensions:
                    self.register_extension_class(ext_class)
                    
                self.logger.info(f"Registered {len(extensions)} extensions from package {package_name}")
            else:
                # Auto-discover extensions in package
                self.register_extension_by_path(package_name)
                
            self.extension_packages[package_name] = package_name
            
        except Exception as e:
            self.logger.error(f"Failed to register extension package {package_name}: {e}")
            raise
    
    def get_extension_class(self, name: str) -> Optional[Type[ApiLibExtension]]:
        """Get extension class by name."""
        return self.extensions.get(name)
    
    def list_available_extensions(self) -> List[str]:
        """List all available extension names."""
        return list(self.extensions.keys())
    
    def create_extension_instance(self, name: str) -> Optional[ApiLibExtension]:
        """Create instance of extension by name."""
        ext_class = self.get_extension_class(name)
        if ext_class:
            return ext_class()
        return None
    
    def clear(self):
        """Clear all registered extensions (useful for testing)."""
        self.extensions.clear()
        self.extension_packages.clear()


# Global registry instance
global_extension_registry = ExtensionRegistry()


class ExtensionManager:
    """
    Manager for handling extensions within an ApiLib instance.
    
    This class handles the loading, unloading, and management of extensions
    for a specific ApiLib instance.
    """
    
    def __init__(self, api_lib):
        """
        Initialize extension manager.
        
        Args:
            api_lib: ApiLib instance to manage extensions for
        """
        self.api_lib = api_lib
        self.loaded_extensions: Dict[str, ApiLibExtension] = {}
        self.extension_registry = global_extension_registry
        self.logger = logging.getLogger(__name__)
    
    def load_extensions(self, extensions: Union[List[str], List[Type], List[ApiLibExtension]]):
        """
        Load multiple extensions.
        
        Args:
            extensions: List of extension names, classes, or instances
        """
        for ext in extensions:
            try:
                self.load_extension(ext)
            except Exception as e:
                self.logger.error(f"Failed to load extension {ext}: {e}")
    
    def load_extension(self, extension: Union[str, Type[ApiLibExtension], ApiLibExtension]):
        """
        Load a single extension.
        
        Args:
            extension: Extension name (string), class, or instance
        """
        if isinstance(extension, str):
            # Load by name from registry
            ext_instance = self.extension_registry.create_extension_instance(extension)
            if not ext_instance:
                raise ValueError(f"Extension '{extension}' not found in registry")
        elif isinstance(extension, type) and issubclass(extension, ApiLibExtension):
            # Extension class provided
            ext_instance = extension()
        elif isinstance(extension, ApiLibExtension):
            # Extension instance provided
            ext_instance = extension
        else:
            raise ValueError(f"Invalid extension type: {type(extension)}")
        
        # Register the extension
        self._register_extension_instance(ext_instance)
    
    def _register_extension_instance(self, extension: ApiLibExtension):
        """Register an extension instance with the ApiLib."""
        extension_name = extension.get_extension_name()
        
        if extension_name in self.loaded_extensions:
            self.logger.warning(f"Extension '{extension_name}' already loaded, replacing")
            self.unload_extension(extension_name)
        
        # Register extension
        extension.register_with_api_lib(self.api_lib)
        self.loaded_extensions[extension_name] = extension
        
        self.logger.info(f"Loaded extension: {extension_name}")
    
    def unload_extension(self, extension_name: str):
        """
        Unload an extension.
        
        Args:
            extension_name: Name of extension to unload
        """
        if extension_name not in self.loaded_extensions:
            self.logger.warning(f"Extension '{extension_name}' not loaded")
            return
        
        extension = self.loaded_extensions[extension_name]
        extension.unregister_from_api_lib(self.api_lib)
        
        del self.loaded_extensions[extension_name]
        self.logger.info(f"Unloaded extension: {extension_name}")
    
    def reload_extension(self, extension_name: str):
        """Reload an extension (useful for development)."""
        if extension_name in self.loaded_extensions:
            self.unload_extension(extension_name)
        self.load_extension(extension_name)
    
    def get_loaded_extensions(self) -> List[str]:
        """Get list of currently loaded extension names."""
        return list(self.loaded_extensions.keys())
    
    def has_extension(self, extension_name: str) -> bool:
        """Check if an extension is loaded."""
        return extension_name in self.loaded_extensions
    
    def get_extension_methods(self) -> Dict[str, str]:
        """Get mapping of methods to their providing extensions."""
        method_mapping = {}
        for ext_name, extension in self.loaded_extensions.items():
            methods = extension.get_methods()
            for method_name in methods.keys():
                method_mapping[method_name] = ext_name
        return method_mapping
    
    def register_extension_class(self, extension_class: Type[ApiLibExtension]):
        """Register an extension class with the global registry."""
        self.extension_registry.register_extension_class(extension_class)
    
    def register_extension_package(self, package_name: str):
        """Register all extensions from a package."""
        self.extension_registry.register_extension_package(package_name)
    
    def register_extension_by_path(self, module_path: str, class_name: str = None):
        """Register extension by module path."""
        self.extension_registry.register_extension_by_path(module_path, class_name)
    
    def list_available_extensions(self) -> List[str]:
        """List all extensions available in the registry."""
        return self.extension_registry.list_available_extensions()
    
    def load_extensions_from_config(self, config: Union[str, Path, Dict]):
        """
        Load extensions from configuration.
        
        Args:
            config: Config file path, Path object, or config dictionary
        """
        if isinstance(config, (str, Path)):
            config_dict = self._load_config_file(config)
        else:
            config_dict = config
        
        # Load extension packages first
        packages = config_dict.get('extension_packages', [])
        for package in packages:
            try:
                self.register_extension_package(package)
            except Exception as e:
                self.logger.error(f"Failed to register package {package}: {e}")
        
        # Load specific extensions
        extensions = config_dict.get('extensions', [])
        if extensions:
            self.load_extensions(extensions)
    
    def _load_config_file(self, config_path: Union[str, Path]) -> Dict:
        """Load configuration from file."""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        if config_path.suffix.lower() in ['.yml', '.yaml']:
            import yaml
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        elif config_path.suffix.lower() == '.json':
            import json
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            raise ValueError(f"Unsupported config file format: {config_path.suffix}")


# =============================================================================
# CONVENIENCE FUNCTIONS FOR GLOBAL REGISTRY
# =============================================================================

def register_global_extension_class(extension_class: Type[ApiLibExtension]):
    """Register extension class globally."""
    global_extension_registry.register_extension_class(extension_class)


def register_global_extension_package(package_name: str):
    """Register extension package globally."""
    global_extension_registry.register_extension_package(package_name)


def register_global_extension_by_path(module_path: str, class_name: str = None):
    """Register extension by module path globally."""
    global_extension_registry.register_extension_by_path(module_path, class_name)


def list_global_extensions() -> List[str]:
    """List all globally available extensions."""
    return global_extension_registry.list_available_extensions()


def clear_global_extensions():
    """Clear all global extensions (useful for testing)."""
    global_extension_registry.clear()


# =============================================================================
# UTILITY MIXINS FOR COMMON EXTENSION PATTERNS
# =============================================================================

class QueryBuilderMixin:
    """Mixin providing common query building utilities."""
    
    def _build_geo_query(self, lon: float, lat: float) -> Dict[str, Any]:
        """Build geographical query component."""
        if lon is not None and lat is not None:
            return {
                "geo_point": {
                    "coordinates": [lon, lat]
                }
            }
        return {}
    
    def _build_filters(self, **filters) -> Dict[str, Any]:
        """Build filter components from keyword arguments."""
        query_filters = {}
        
        # Common filter mappings (extensible by subclasses)
        filter_mappings = getattr(self, 'FILTER_MAPPINGS', {
            'kws': 'keywords',
            'keywords': 'keywords', 
            'city': 'city',
            'max_limit': 'max_limit'
        })
        
        for key, value in filters.items():
            if value is not None:
                mapped_key = filter_mappings.get(key, key)
                query_filters[mapped_key] = value
                
        return query_filters


class ResponseParserMixin:
    """Mixin providing common response parsing utilities."""
    
    def _parse_json_response(self, json_data: str) -> Dict[str, Any]:
        """Parse JSON response string to dictionary."""
        try:
            import json
            if isinstance(json_data, str):
                return json.loads(json_data)
            return json_data if json_data else {}
        except (json.JSONDecodeError, TypeError) as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            return {}
    
    def _extract_objects(self, response_data: Dict[str, Any], key: str) -> List[Dict[str, Any]]:
        """Extract objects list from response data."""
        if isinstance(response_data, dict):
            return response_data.get(key, [])
        return []
    
    def _hydrate_objects(self, objects_data: List[Dict[str, Any]], object_class: Type) -> List[Any]:
        """Convert list of dictionaries to domain objects."""
        hydrated_objects = []
        for obj_data in objects_data or []:
            try:
                if hasattr(object_class, 'from_dict'):
                    hydrated_obj = object_class.from_dict(**obj_data)
                else:
                    hydrated_obj = object_class(**obj_data)
                hydrated_objects.append(hydrated_obj)
            except Exception as e:
                self.logger.warning(f"Failed to hydrate {object_class.__name__} object: {e}")
                continue
        return hydrated_objects
