"""
Supero Core - High-level Pythonic wrapper for ApiLib

UPDATED: 
- Integrated with schema metadata for dynamic method injection
- Auto-detects system vs tenant schemas based on domain name
- FIXED: Dynamic schema discovery (no longer hardcoded)
- ADDED: Explicit schema registry (org.schemas.Project.create())
- ADDED: Collision detection and warnings
- ADDED: Smart mode detection (auto-detects proxy vs direct mode)
- ADDED: No-auth testing mode support
- FIXED: Domain parameter name in login (domain_name → domain)
- FIXED: Added manager properties (users, schemas_manager, sdks)
- FIXED: Added explicit _domain_uuid storage and property
- FIXED: Improved validation to support testing mode
- FIXED: Uses _OBJ_TYPE and _PARENT_TYPE class attributes (no schema_metadata.py dependency)
- FIXED: All normalization uses normalize_schema_name()
- ADDED: Per-call api_key support for RBAC enforcement (v2.1)

Provides intuitive, fluent API for object management without boilerplate.
"""

import importlib
import inflection
import pkgutil
import inspect
from typing import Any, Dict, List, Optional, Type, Union
from pathlib import Path
import sys
import os
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from .schema_naming import normalize_schema_name

# Local/relative imports
from .schema_manager import SchemaManager
from .user_manager import UserManager
from .sdk_manager import SDKManager
from .aggregate_manager import AggregateManager
from .crud_manager import CrudManager
from .platform_client import (
    PlatformClient,
    AuthenticationError,
    AuthorizationError,
    RateLimitError
)

class APIError(Exception):
    """API error exception."""
    pass

def _get_py_api_lib_for_domain(domain_name: str = None) -> str:
    """
    Get the correct py_api_lib package for a specific domain.

    DETERMINISTIC: No guessing! Computes exact package name from domain.

    Args:
        domain_name: The domain/tenant name (e.g., 'ecom-demo-30045')

    Returns:
        Package name to import from
    """
    # 1. Check for explicit override first
    override = os.environ.get('SUPERO_PY_API_LIB')
    if override:
        return override

    # 2. If domain_name provided, compute exact package name
    if domain_name and domain_name != 'system':
        # Convert domain name to package name: ecom-demo-30045 -> py_api_lib_ecom_demo_30045
        tenant_slug = domain_name.replace('-', '_').lower()
        tenant_package = f'py_api_lib_{tenant_slug}'

        # Try to import it
        try:
            importlib.import_module(tenant_package)
            return tenant_package
        except ImportError:
            pass  # Fall through to system/legacy

    # 3. Try system package (platform builds)
    try:
        importlib.import_module('py_api_lib_system')
        return 'py_api_lib_system'
    except ImportError:
        pass

    # 4. Fallback to legacy shared package
    return 'py_api_lib'


# Module-level default (will be updated in Supero.__init__)
_PY_API_LIB_PKG = _get_py_api_lib_for_domain(None)

ApiLib = None
SCHEMA_NAMESPACES = None
TENANT_NAMESPACE = None
PRIMARY_SCHEMA_NAMESPACE = None

_api_logger_module = importlib.import_module(f'{_PY_API_LIB_PKG}.api_logger')
initialize_logger = _api_logger_module.initialize_logger

# ============================================================================
# Dynamic Imports from Detected Package
# ============================================================================

try:
    # Import ApiLib
    _api_lib_module = importlib.import_module(f'{_PY_API_LIB_PKG}.api_lib')
    ApiLib = _api_lib_module.ApiLib

    # Import runtime config
    _runtime_config = importlib.import_module(f'{_PY_API_LIB_PKG}._runtime_config')
    SCHEMA_NAMESPACES = _runtime_config.SCHEMA_NAMESPACES
    TENANT_NAMESPACE = getattr(_runtime_config, 'TENANT_NAMESPACE', None)
    PRIMARY_SCHEMA_NAMESPACE = _runtime_config.PRIMARY_SCHEMA_NAMESPACE
    BUILD_MODE = getattr(_runtime_config, 'BUILD_MODE', 'platform')
    BUILD_TENANT = getattr(_runtime_config, 'BUILD_TENANT', 'system')

    # Log which package we're using (debug level)
    print(f"✓ Using py_api_lib package: {_PY_API_LIB_PKG}")
    print(f"  SCHEMA_NAMESPACES: {SCHEMA_NAMESPACES}")
    print(f"  PRIMARY_SCHEMA_NAMESPACE: {PRIMARY_SCHEMA_NAMESPACE}")
    print(f"  BUILD_MODE: {BUILD_MODE}")

except ImportError as e:
    raise ImportError(
        f"Could not import from '{_PY_API_LIB_PKG}'. "
        f"Ensure the SDK is properly installed. Error: {e}"
    )

print(f"[SUPERO] Using py_api_lib package: {_PY_API_LIB_PKG}")

# Verify critical imports
if ApiLib is None:
    raise ImportError(
        f"Could not load ApiLib from {_PY_API_LIB_PKG} or py_api_lib. "
        f"SDK installation may be corrupted."
    )

def _load_py_api_lib_for_domain(domain_name: str):
    """Load the correct py_api_lib for a domain."""
    pkg = _get_py_api_lib_for_domain(domain_name)
    try:
        _api_lib_mod = importlib.import_module(f'{pkg}.api_lib')
        _runtime_cfg = importlib.import_module(f'{pkg}._runtime_config')
        return (
            _api_lib_mod.ApiLib,
            _runtime_cfg.SCHEMA_NAMESPACES,
            _runtime_cfg.PRIMARY_SCHEMA_NAMESPACE,
            getattr(_runtime_cfg, 'TENANT_NAMESPACE', None),
            pkg
        )
    except ImportError:
        # ✅ Fallback to module-level defaults (for tests and backwards compat)
        return (
            ApiLib,
            SCHEMA_NAMESPACES,
            PRIMARY_SCHEMA_NAMESPACE,
            TENANT_NAMESPACE,
            _PY_API_LIB_PKG
        )

DEFAULT_PLATFORM_UI_HOST = "api.supero.dev"
DEFAULT_PLATFORM_UI_PORT =  443
default_platform_core_host = os.getenv('PLATFORM_UI_HOST', DEFAULT_PLATFORM_UI_HOST)
default_platform_core_port = int(os.getenv('PLATFORM_UI_PORT', DEFAULT_PLATFORM_UI_PORT))

# ============================================================================
# NEW: Schema Registry Classes (Optional - Explicit Access Pattern)
# ============================================================================

class SchemaProxy:
    """
    Provides explicit access to schema operations without collision risk.

    Usage:
        Project = org.schemas.Project
        project = Project.create(name="Alpha")
        projects = Project.find(status="active")

    ✅ FIXED: Properly handles module vs class distinction
    ✅ FIXED: Safely extracts _OBJ_TYPE from schema class
    ✅ ADDED: Per-call api_key support for RBAC (v2.1)
    """

    def __init__(self, schema_name: str, supero: 'Supero'):
        """Initialize SchemaProxy - SIMPLE!"""
        self._display_name = schema_name  # CamelCase: 'Project', 'UserAccount'
        self._schema_name = normalize_schema_name(schema_name)  # snake_case: 'project', 'user_account'
        self._supero = supero
        self._schema_class = None
        self._obj_type_cache = None  # ✅ NEW: Cache for _OBJ_TYPE

    def __repr__(self):
        return f"<SchemaProxy: {self._display_name}>"

    def _extract_class_from_module(self, module_or_class):
        """
        Extract the actual class from a module or return the class if already a class.

        ✅ NEW: Handles both module and class objects

        Args:
            module_or_class: Either a module or class object

        Returns:
            The class object
        """
        if module_or_class is None:
            return None

        # If it's already a class (has _type_metadata), return it
        if hasattr(module_or_class, '_type_metadata'):
            return module_or_class

        # If it's a module, try to extract the class
        # Class name is PascalCase version of schema name
        class_name = ''.join(word.capitalize() for word in self._schema_name.split('_'))

        if hasattr(module_or_class, class_name):
            extracted_class = getattr(module_or_class, class_name)
            # Verify it's actually a class with _type_metadata
            if hasattr(extracted_class, '_type_metadata'):
                return extracted_class

        # If we can't extract a proper class, return what we got
        return module_or_class

    @property
    def schema_class(self):
        """
        Lazy-load the actual schema class.

        ✅ FIXED: Properly extracts class from module if needed
        """
        if self._schema_class is None:
            # Get schema (might be module or class)
            schema = self._supero.get_schema(self._schema_name)

            # ✅ NEW: Extract class from module if necessary
            self._schema_class = self._extract_class_from_module(schema)

        return self._schema_class

    def _get_obj_type(self):
        """
        Get the _OBJ_TYPE from the schema class.

        ✅ NEW: Safe access to _OBJ_TYPE with proper error handling

        Returns:
            str: The object type string
        """
        # Return cached value if available
        if self._obj_type_cache:
            return self._obj_type_cache

        # Get the schema class
        schema_cls = self.schema_class

        if schema_cls is None:
            raise ValueError(f"Schema class not found for {self._schema_name}")

        # Try to get _OBJ_TYPE from class
        if hasattr(schema_cls, '_OBJ_TYPE'):
            self._obj_type_cache = schema_cls._OBJ_TYPE
            return self._obj_type_cache

        # Fallback: use schema_name
        self._obj_type_cache = self._schema_name
        return self._obj_type_cache

    def create(self, *args, api_key: str = None, **kwargs):
        """
        Create a new instance of this schema and save it.

        SMART PARENT ASSIGNMENT:
        - Accepts parent= kwarg or uses domain as parent
        - Uses generated set_parent() method for validation

        Args:
            *args: Positional arguments for schema constructor
            api_key: Optional API key for RBAC (overrides instance default)
            **kwargs: Keyword arguments for schema constructor

        Returns:
            Created and saved schema instance
        """
        # ✅ Extract parent from kwargs BEFORE creating instance
        parent = kwargs.pop('parent', None)

        # Create instance
        schema_class = self.schema_class
        instance = schema_class(*args, **kwargs)

        if not hasattr(instance, 'obj_type') or not instance.obj_type:
            raise ValueError(f"obj_type not set for {self._schema_name}")

        if instance.obj_type != self._schema_name:
            raise ValueError(
                f"obj_type mismatch: expected '{self._schema_name}', "
                f"got '{instance.obj_type}'"
            )

        # Get expected parent type from class attribute
        expected_parent_type = getattr(schema_class, '_PARENT_TYPE', None)

        # ✅ Set parent using generated set_parent() method
        if parent:
            # Use provided parent
            try:
                instance.set_parent(parent)
                self._supero.logger.debug(
                    f"Set parent for {self._schema_name}: "
                    f"parent_type={instance.parent_type}, "
                    f"parent_uuid={instance.parent_uuid}, "
                    f"fq_name={instance.fq_name}"
                )
            except Exception as e:
                raise ValueError(
                    f"Cannot create {self._schema_name}: failed to set parent: {e}"
                )
        elif expected_parent_type == 'domain':
            # Fall back to domain for domain children
            if hasattr(self._supero, '_domain_obj') and self._supero._domain_obj:
                domain = self._supero._domain_obj
                try:
                    instance.set_parent(domain)
                    self._supero.logger.debug(
                        f"Auto-set domain as parent for {self._schema_name}"
                    )
                except Exception as e:
                    raise ValueError(
                        f"Cannot create {self._schema_name}: failed to set domain as parent: {e}"
                    )
            else:
                raise ValueError(
                    f"Cannot create {self._schema_name}: requires parent but none provided. "
                    f"Use parent= kwarg or Supero.quickstart() first."
                )
        elif expected_parent_type:
            # Non-domain parent required but not provided
            raise ValueError(
                f"Cannot create {self._schema_name}: requires parent_type='{expected_parent_type}' "
                f"but no parent provided. Use parent= kwarg."
            )

        # ✅ Validate required fields are set (after set_parent())
        if not instance.parent_type:
            raise ValueError(
                f"Cannot create {self._schema_name}: parent_type not set after set_parent()"
            )

        if not instance.parent_uuid:
            raise ValueError(
                f"Cannot create {self._schema_name}: parent_uuid not set after set_parent()"
            )

        if not instance.fq_name or len(instance.fq_name) == 0:
            raise ValueError(
                f"Cannot create {self._schema_name}: fq_name not set after set_parent()"
            )

        # Save - ✅ RBAC: Pass api_key through
        try:
            saved = self._supero.save(instance, validate=False, api_key=api_key)
            return saved
        except Exception as e:
            self._supero.logger.error(
                f"Failed to save {self._schema_name}: {e}"
            )
            raise

    def _auto_fetch_and_validate_parent_fields(self, instance, api_key: str = None):
        """
        Auto-fetch missing parent fields and validate required fields.

        Logic:
        1. If has parent_uuid but missing fq_name → fetch fq_name
        2. If has fq_name but missing parent_uuid → fetch parent_uuid
        3. Validate all required fields are set

        Args:
            instance: Schema instance to validate and populate
            api_key: Optional API key for RBAC (overrides instance default)

        Raises:
            ValueError: If required fields cannot be fetched or validated
        """
        # ========================================================================
        # AUTO-FETCH MISSING PARENT FIELDS
        # ========================================================================

        if instance.parent_type in ['config_root', 'config-root']:
            self._supero.logger.debug(
                f"{self._schema_name} is config-root object, skipping parent validation"
            )
            return

        # Case 1: Has parent_uuid but missing fq_name → fetch fq_name
        if instance.parent_uuid and (not instance.fq_name or len(instance.fq_name) == 0):
            try:
                self._supero.logger.debug(
                    f"Auto-fetching fq_name for {self._schema_name} using parent_uuid={instance.parent_uuid}"
                )

                # Get parent_type to know which object type to query
                if not instance.parent_type:
                    raise ValueError(
                        f"Cannot fetch fq_name: parent_type is required when only parent_uuid is provided"
                    )

                # ✅ RBAC: Pass api_key through
                parent_fq_name = self._supero._api_lib.uuid_to_fq_name(
                    instance.parent_type,
                    instance.parent_uuid,
                    domain_name=self._supero.domain_name,
                    api_key=api_key
                )

                if not parent_fq_name:
                    raise ValueError(
                        f"Cannot fetch fq_name: parent object not found for "
                        f"parent_type={instance.parent_type}, parent_uuid={instance.parent_uuid}"
                    )

                # Construct child's fq_name by appending name to parent's fq_name
                instance.fq_name = parent_fq_name + [instance.name]

                self._supero.logger.debug(
                    f"✓ Auto-fetched fq_name for {self._schema_name}: {instance.fq_name}"
                )

            except Exception as e:
                raise ValueError(
                    f"Failed to auto-fetch fq_name for {self._schema_name}: {str(e)}"
                )

        # Case 2: Has fq_name but missing parent_uuid → fetch parent_uuid
        if (not instance.parent_uuid) and instance.fq_name and len(instance.fq_name) > 1:
            try:
                self._supero.logger.debug(
                    f"Auto-fetching parent_uuid for {self._schema_name} using fq_name={instance.fq_name}"
                )

                # Get parent_type to know which object type to query
                if not instance.parent_type:
                    raise ValueError(
                        f"Cannot fetch parent_uuid: parent_type is required when only fq_name is provided"
                    )

                # Parent's fq_name is all elements except the last one
                parent_fq_name = instance.fq_name[:-1]

                # ✅ RBAC: Pass api_key through
                parent_uuid = self._supero._api_lib.fq_name_to_uuid(
                    instance.parent_type,
                    parent_fq_name,
                    api_key=api_key
                )

                if not parent_uuid:
                    raise ValueError(
                        f"Cannot fetch parent_uuid: parent object not found for "
                        f"parent_type={instance.parent_type}, parent_fq_name={parent_fq_name}"
                    )

                instance.parent_uuid = parent_uuid

                self._supero.logger.debug(
                    f"✓ Auto-fetched parent_uuid for {self._schema_name}: {parent_uuid}"
                )

            except Exception as e:
                raise ValueError(
                    f"Failed to auto-fetch parent_uuid for {self._schema_name}: {str(e)}"
                )

        # ========================================================================
        # VALIDATE REQUIRED FIELDS (after auto-fetch)
        # ========================================================================

        # Verify parent_type is set
        if not instance.parent_type:
            raise ValueError(
                f"Cannot create {self._schema_name}: parent_type is required but not set. "
                f"Instance state: parent_uuid={instance.parent_uuid}, "
                f"fq_name={getattr(instance, 'fq_name', None)}"
            )

        # Verify parent_uuid is set
        if not instance.parent_uuid:
            raise ValueError(
                f"Cannot create {self._schema_name}: parent_uuid is required but not set. "
                f"Instance state: parent_type={instance.parent_type}, "
                f"fq_name={getattr(instance, 'fq_name', None)}"
            )

        # Verify fq_name is set
        if not instance.fq_name or len(instance.fq_name) == 0:
            raise ValueError(
                f"Cannot create {self._schema_name}: fq_name is required but not set. "
                f"Instance state: parent_uuid={instance.parent_uuid}, "
                f"parent_type={instance.parent_type}"
            )

        # Final validation: name must match last element of fq_name
        if instance.name != instance.fq_name[-1]:
            self._supero.logger.warning(
                f"Name mismatch for {self._schema_name}: "
                f"name='{instance.name}' but fq_name[-1]='{instance.fq_name[-1]}'. "
                f"Using fq_name[-1] as authoritative."
            )
            instance.name = instance.fq_name[-1]

    def find(self, api_key: str = None, **filters):
        """
        Find instances matching filters.

        Args:
            api_key: Optional API key for RBAC (overrides instance default)
            **filters: Filter conditions

        Returns:
            List of matching schema instances

        ✅ FIXED: Uses _get_obj_type() for safe access
        ✅ ADDED: Per-call api_key support for RBAC (v2.1)
        """
        # ✅ FIXED: Get object type safely
        obj_type = self._get_obj_type()

        try:
            # ✅ RBAC: Pass api_key through to ApiLib
            result = self._supero._api_lib._objects_list(
                obj_type, 
                detail=True, 
                domain_name=self._supero.domain_name,
                api_key=api_key
            )

            # ✅ DEFENSIVE: Validate result is actually a list
            if not isinstance(result, list):
                self._supero.logger.warning(
                    f"_objects_list returned non-list type: {type(result).__name__}"
                )
                return []

            all_objects = result

            # Apply filters
            if filters:
                filtered = []
                for obj in all_objects:
                    matches = True
                    for key, value in filters.items():
                        # Handle Django-style lookups (e.g., price__gt)
                        if '__' in key:
                            field, operator = key.split('__', 1)
                            obj_value = getattr(obj, field, None)

                            if operator == 'gt' and not (obj_value is not None and obj_value > value):
                                matches = False
                                break
                            elif operator == 'gte' and not (obj_value is not None and obj_value >= value):
                                matches = False
                                break
                            elif operator == 'lt' and not (obj_value is not None and obj_value < value):
                                matches = False
                                break
                            elif operator == 'lte' and not (obj_value is not None and obj_value <= value):
                                matches = False
                                break
                            elif operator == 'contains' and not (obj_value is not None and value in str(obj_value)):
                                matches = False
                                break
                            elif operator == 'startswith' and not (obj_value is not None and str(obj_value).startswith(value)):
                                matches = False
                                break
                        else:
                            # Exact match
                            if not hasattr(obj, key) or getattr(obj, key) != value:
                                matches = False
                                break

                    if matches:
                        filtered.append(obj)

                return filtered

            return all_objects
        except Exception as e:
            self._supero.logger.error(f"Failed to find {self._schema_name}: {e}")
            return []

    def get(self, object_id: str, api_key: str = None):
        """
        Get instance by ID.

        Args:
            object_id: UUID of the object to retrieve
            api_key: Optional API key for RBAC (overrides instance default)

        Returns:
            Schema instance or None if not found

        ✅ ADDED: Per-call api_key support for RBAC (v2.1)
        """
        obj_type = self._get_obj_type()

        try:
            # ✅ RBAC: Pass api_key through to ApiLib
            result = self._supero._api_lib._object_read(
                obj_type, 
                id=object_id, 
                domain_name=self._supero.domain_name,
                api_key=api_key
            )

            # Check if it's a real schema object
            if result is not None:
                # Check if it's a mock object (unittest.mock)
                result_type_name = type(result).__name__
                if 'Mock' in result_type_name:
                    self._supero.logger.warning(
                        f"_object_read returned mock object: {result_type_name}"
                    )
                    return None

                # Check if it's a real schema object (has _type_metadata class attribute)
                result_class = result.__class__
                if not hasattr(result_class, '_type_metadata'):
                    self._supero.logger.warning(
                        f"_object_read returned non-schema object: {result_type_name}"
                    )
                    return None

                # Add fluent API methods to retrieved object
                self._supero._inject_child_methods_auto(result)

            return result
        except (AuthorizationError, AuthenticationError):
            # Re-raise auth errors - callers should handle these
            raise
        except Exception as e:
            self._supero.logger.error(f"Failed to get {self._schema_name} {object_id}: {e}")
            return None

    def get_by_fq_name(self, fq_name: List[str], api_key: str = None):
        """
        Get instance by fully-qualified name.

        Args:
            fq_name: Fully-qualified name as list of strings
            api_key: Optional API key for RBAC (overrides instance default)

        Returns:
            Schema instance or None if not found

        ✅ ADDED: Per-call api_key support for RBAC (v2.1)
        """
        obj_type = self._get_obj_type()

        try:
            # ✅ RBAC: Pass api_key through to ApiLib
            result = self._supero._api_lib._object_read(
                obj_type, 
                fq_name=fq_name, 
                domain_name=self._supero.domain_name,
                api_key=api_key
            )

            # Validate it's a real object
            if result is not None:
                result_type_name = type(result).__name__
                if 'Mock' in result_type_name:
                    return None
                result_class = result.__class__
                if not hasattr(result_class, '_type_metadata'):
                    return None

                # Add fluent API methods to retrieved object
                self._supero._inject_child_methods_auto(result)

            return result
        except (AuthorizationError, AuthenticationError):
            # Re-raise auth errors - callers should handle these
            raise
        except Exception as e:
            self._supero.logger.error(f"Failed to get {self._schema_name} by fq_name {fq_name}: {e}")
            return None

    def all(self, limit: int = None, api_key: str = None):
        """
        Get all instances.

        Args:
            limit: Maximum number of results (not currently used)
            api_key: Optional API key for RBAC (overrides instance default)

        Returns:
            List of all schema instances

        ✅ ADDED: Per-call api_key support for RBAC (v2.1)
        """
        return self.find(api_key=api_key)

    def count(self, api_key: str = None, **filters):
        """
        Count instances.

        Args:
            api_key: Optional API key for RBAC (overrides instance default)
            **filters: Filter conditions

        Returns:
            int: Number of matching instances

        ✅ ADDED: Per-call api_key support for RBAC (v2.1)
        """
        return len(self.find(api_key=api_key, **filters))

    def stats(
        self,
        fields: Optional[List[str]] = None,
        match: Optional[Dict[str, Any]] = None,
        api_key: str = None
    ) -> Dict[str, Any]:
        """
        Get statistics for numeric fields.
        
        Args:
            fields: Fields to get stats for (None = all numeric)
            match: Filter conditions
            api_key: Optional API key for RBAC
        
        Returns:
            Dict with count and field statistics
        
        Example:
            >>> stats = org.Order.stats(fields=['amount', 'quantity'])
            >>> print(f"Total: {stats['count']}")
            >>> print(f"Avg amount: ${stats['fields']['amount']['avg']:.2f}")
            >>> 
            >>> # With filter
            >>> stats = org.Order.stats(
            ...     fields=['amount'],
            ...     match={'status': 'completed'}
            ... )
            >>> print(f"Completed revenue: ${stats['fields']['amount']['sum']:.2f}")
            
            >>> # With RBAC
            >>> stats = org.Order.stats(fields=['amount'], api_key=user_key)
        """
        return self._supero.aggregate.stats(
            self._schema_name,
            fields=fields,
            match=match,
            api_key=api_key
        )

    def distinct(
        self,
        field: str,
        match: Optional[Dict[str, Any]] = None,
        limit: int = 1000,
        api_key: str = None
    ) -> List[Any]:
        """
        Get distinct values for a field.
        
        Args:
            field: Field name to get distinct values for
            match: Filter conditions
            limit: Max values to return (1-10000, default 1000)
            api_key: Optional API key for RBAC
        
        Returns:
            List of distinct values
        
        Example:
            >>> statuses = org.Order.distinct('status')
            >>> print(statuses)  # ['pending', 'completed', 'cancelled']
            
            >>> # Get unique customers for completed orders
            >>> customers = org.Order.distinct(
            ...     'customer_id',
            ...     match={'status': 'completed'},
            ...     limit=100
            ... )
            
            >>> # With RBAC
            >>> statuses = org.Order.distinct('status', api_key=user_key)
        """
        return self._supero.aggregate.distinct(
            self._schema_name,
            field=field,
            match=match,
            limit=limit,
            api_key=api_key
        )

    def count_by(
        self,
        field: str,
        match: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        sort: str = '-count',
        api_key: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get counts grouped by field values.
        
        Args:
            field: Field to group by
            match: Filter conditions
            limit: Max groups to return (1-1000, default 100)
            sort: Sort order ('count', '-count', 'value', '-value')
            api_key: Optional API key for RBAC
        
        Returns:
            List of {'value': field_value, 'count': count} dicts
        
        Example:
            >>> by_status = org.Order.count_by('status')
            >>> for item in by_status:
            ...     print(f"{item['value']}: {item['count']} orders")
            
            >>> # Top 10 categories by count
            >>> by_category = org.Order.count_by(
            ...     'category',
            ...     limit=10,
            ...     sort='-count'
            ... )
            
            >>> # Active users by role
            >>> by_role = org.UserAccount.count_by(
            ...     'role',
            ...     match={'enabled': True}
            ... )
            
            >>> # With RBAC
            >>> by_status = org.Order.count_by('status', api_key=user_key)
        """
        return self._supero.aggregate.count_by(
            self._schema_name,
            field=field,
            match=match,
            limit=limit,
            sort=sort,
            api_key=api_key
        )

    def aggregate(
        self,
        pipeline: List[Dict[str, Any]],
        api_key: str = None
    ) -> List[Dict[str, Any]]:
        """
        Execute aggregation pipeline.
        
        Args:
            pipeline: MongoDB-style aggregation pipeline
            api_key: Optional API key for RBAC
        
        Returns:
            List of result documents
        
        Example:
            >>> # Sales by category
            >>> results = org.Order.aggregate([
            ...     {'$match': {'status': 'completed'}},
            ...     {'$group': {
            ...         '_id': '$category',
            ...         'total': {'$sum': '$amount'},
            ...         'count': {'$sum': 1}
            ...     }},
            ...     {'$sort': {'total': -1}}
            ... ])
            >>> for item in results:
            ...     print(f"{item['_id']}: ${item['total']:.2f}")
            
            >>> # Top customers
            >>> top_customers = org.Order.aggregate([
            ...     {'$group': {
            ...         '_id': '$customer_id',
            ...         'total_spent': {'$sum': '$amount'}
            ...     }},
            ...     {'$sort': {'total_spent': -1}},
            ...     {'$limit': 10}
            ... ])
            
            >>> # With RBAC
            >>> results = org.Order.aggregate(pipeline, api_key=user_key)
        """
        return self._supero.aggregate.pipeline(
            self._schema_name,
            pipeline=pipeline,
            api_key=api_key
        )

    def query(self, api_key: str = None):
        """
        Get a QueryBuilder for fluent query construction.

        Returns a QueryBuilder that allows chaining filter, order, limit
        operations with optional per-call API key for RBAC.

        Args:
            api_key: Optional API key for RBAC (overrides instance default)

        Returns:
            QueryBuilder: Fluent query builder instance

        Examples:
            # Basic query
            tasks = org.Task.query().filter(status='open').all()

            # With RBAC
            tasks = (org.Task.query()
                .filter(status='in_progress')
                .filter(priority='high')
                .order_by('-created_at')
                .with_api_key(user_key)
                .all())

            # Complex filters
            tasks = (org.Task.query()
                .filter(priority__in=['high', 'critical'])
                .filter(assignee__contains='alice')
                .limit(10)
                .with_api_key(user_key)
                .all())

        ✅ NEW: Added for fluent query API with RBAC support (v2.1)
        """
        from .query import QueryBuilder
        
        # Get the schema class (which has _OBJ_TYPE)
        schema_cls = self.schema_class
        
        return QueryBuilder(
            obj_class=schema_cls,
            supero_context=self._supero,
            api_key=api_key
        )


class SchemaRegistry:
    """
    Registry for explicit schema access.
    
    Usage:
        org.schemas.Project.create(name="Alpha")
        org.schemas.User.find(role="admin")
    """
    
    def __init__(self, supero: 'Supero'):
        self._supero = supero
        self._proxies = {}
    
    def __getattr__(self, schema_name: str):
        """Get schema proxy by name (with normalized lookup)."""
        if schema_name in self._proxies:
            return self._proxies[schema_name]

        # Check if schema exists
        available_schemas = self._supero._list_schemas()

        # Fast path: exact match
        if schema_name in available_schemas:
            proxy = SchemaProxy(schema_name, self._supero)
            self._proxies[schema_name] = proxy
            return proxy

        normalized_requested = normalize_schema_name(schema_name)
        for available in available_schemas:
            if normalize_schema_name(available) == normalized_requested:
                proxy = SchemaProxy(available, self._supero)
                self._proxies[schema_name] = proxy  # Cache under requested name too
                return proxy

        raise AttributeError(
            f"Schema '{schema_name}' not found. "
            f"Available: {', '.join(sorted(available_schemas))}"
        )
    
    def __dir__(self):
        """List available schemas for IDE autocomplete."""
        try:
            return self._supero._list_schemas()
        except:
            return []
    
    def list(self):
        """List all available schemas."""
        return sorted(self._supero._list_schemas())


# ============================================================================
# Main Supero Class
# ============================================================================

class Supero:
    """
    High-level wrapper providing Rails/Django-like ORM experience.

    🔥 ULTIMATE SIMPLIFIED API:

    Quick Start:
        >>> org = Supero.quickstart("acme-corp", jwt_token="...")
        >>> org.upload_schemas("schemas/")
        >>> org.install_sdk()
        >>> project = org.Project.create(name="My Project")

    Or even simpler:
        >>> org = Supero.quickstart("acme-corp", jwt_token="...")
        >>> org.setup("schemas/")  # Upload + install in one!
        >>> project = org.Project.create(name="My Project")

    Key Methods:
        Schema Management:
            - upload_schema() - Upload single schema
            - upload_schemas() - Upload entire directory
            - list_schemas() - List all schemas

        SDK Operations:
            - install_sdk() - Generate + download + install (one call!)
            - refresh_sdk() - Rebuild after schema changes
            - setup() - Complete setup (schemas + SDK)

        Object Operations:
            - Project.create() - Create objects via schema classes
            - Project.find() - Query objects
            - save() - Save objects

    RBAC Support (v2.1):
        All CRUD methods accept optional api_key parameter for per-call
        API key override, enabling multi-user server applications:

        >>> # Multi-user server scenario
        >>> org = Supero.quickstart("acme-corp", api_key=admin_key)
        >>> 
        >>> # Each request uses user's API key
        >>> user_projects = org.Project.find(api_key=user_a_key)
        >>> org.save(project, api_key=user_b_key)
    """

    # System/platform domains that use pymodel_system namespace
    SYSTEM_DOMAINS = {'default-domain', 'platform', 'system', 'admin'}
    
    def __init__(self, domain_name: str, api_lib: ApiLib = None, auto_create_domain=True,
                 package_namespace: str = None,
                 # NEW: Proxy mode parameters
                 use_proxy: bool = False,  # Default to direct mode for backward compat
                 proxy_prefix: str = '/api/v1/crud',
                 jwt_token: str = None,
                 api_key: str = None,
                 platform_core_host: str = None,
                 platform_core_port: int = 443,
                 login_context: Dict[str, Any] = None, project: str = None, tenant: str = None):
        """
        Initialize Supero context.

        Args:
            domain_name: Organization/domain name
            api_lib: Optional ApiLib instance (creates default if None)
            auto_create_domain: Create domain if it doesn't exist
            package_namespace: Package namespace for schema imports
                             If None, auto-detects based on domain_name:
                             - System domains → "pymodel_system"
                             - All others → "pymodel"
            use_proxy: If True, connect through platform-core (default: False)
            proxy_prefix: Proxy endpoint prefix (default: /api/v1/crud)
            jwt_token: JWT token for authentication (proxy mode)
            api_key: API key for authentication (direct mode, internal use only)
            platform_core_host: Platform Core hostname (default: detected from env)
            platform_core_port: Platform Core port (default: 443)

        Examples:
            # Testing mode (no auth required)
            org = Supero(
                domain_name="test-corp",
                auto_create_domain=False
            )

            # Proxy mode with JWT
            org = Supero(
                domain_name="acme-corp",
                use_proxy=True,
                jwt_token="eyJhbGc..."
            )

            # Direct mode with API key
            org = Supero(
                domain_name="default-domain",
                use_proxy=False,
                api_key="ak_admin_xxx"
            )
        """
        # ✅ FIX: Load the correct py_api_lib for this domain (DETERMINISTIC)
        (
            self._ApiLib,
            self._schema_namespaces,
            self._primary_namespace,
            self._tenant_namespace,
            self._py_api_lib_pkg
        ) = _load_py_api_lib_for_domain(domain_name)

        self.logger = initialize_logger(domain_name)
        self.logger.debug(f"Using py_api_lib: {self._py_api_lib_pkg}")
        self.logger.debug(f"Schema namespaces: {self._schema_namespaces}")

        self.domain_name = domain_name

        self.__domain_uuid = None
        self._project_name = None
        self._project_uuid = None
        self._tenant_name = None
        self._tenant_uuid = None
        self._login_context = None
        self._jwt_token = jwt_token 

        if login_context:
            self.__domain_uuid = login_context.get('domain_uuid')
            self._project_name = login_context.get('project') or login_context.get('project_name')
            self._project_uuid = login_context.get('project_uuid')
            self._tenant_name = login_context.get('tenant') or login_context.get('tenant_name')
            self._tenant_uuid = login_context.get('tenant_uuid')
            self._login_context = login_context

        if project:
            self._project_name = project
        if tenant:
            self._tenant_name = tenant

        # Auto-detect package namespace if not provided
        if package_namespace is None:
            package_namespace = self._auto_detect_namespace(domain_name)

        self.package_namespace = package_namespace

        # NEW: Create ApiLib with proxy mode if not provided
        if api_lib is None:
            # Auto-detect platform-core host if not provided
            if platform_core_host is None:
                platform_core_host = default_platform_core_host

            # Build ApiLib kwargs
            api_lib_kwargs = {
                'timeout': 30,
                'max_retries': 3,
                'use_proxy': use_proxy,
                'proxy_prefix': proxy_prefix,
                'default_domain': domain_name,
            }

            # Add authentication (NO VALIDATION - allow no-auth for testing)
            if jwt_token:
                api_lib_kwargs['jwt_token'] = jwt_token
            if api_key:
                api_lib_kwargs['api_key'] = api_key

            # Set server host/port
            if use_proxy:
                api_lib_kwargs['api_server_host'] = platform_core_host
                api_lib_kwargs['api_server_port'] = str(platform_core_port)
            else:
                api_lib_kwargs['api_server_host'] = default_platform_core_host
                api_lib_kwargs['api_server_port'] = default_platform_core_port

            # ✅ FIX: Use self._ApiLib (domain-specific) instead of global ApiLib
            api_lib = self._ApiLib(**api_lib_kwargs)

        self._api_lib = api_lib
        self._schema_cache = {}
        self._domain_obj = None
        self._domain = None

        self.__domain_uuid = None
        if login_context:
            self.__domain_uuid = login_context.get('domain_uuid')
            self._login_context = login_context

        self._jwt_token = jwt_token

        self._ensure_domain()

        # Explicit schema registry (always available)
        self.schemas = SchemaRegistry(self)

        # Initialize AI manager as None (lazy-loaded via property)
        self._ai_manager = None

        # Determine mode and auth status for logging
        mode = "PROXY" if use_proxy else "DIRECT"
        if jwt_token:
            auth_status = "JWT auth"
        elif api_key:
            auth_status = "API key auth"
        else:
            auth_status = "NO AUTH (testing/development)"

        self.logger.info(
            f"Supero initialized: domain='{domain_name}', "
            f"namespace='{self.package_namespace}', mode='{mode}', auth='{auth_status}'"
        )

        self._get_platform_client()
        self._load_existing_domain()
        if self._domain_obj:
            self._wrap_domain()
        else:
            raise ValueError(
                f"domain '{domain_name}' not found. "
                f"Register tenant first via Platform Core."
            )

        # CHANGED: Initialize managers as None (lazy-loaded via properties)
        self._schema_manager = None
        self._user_manager = None
        self._sdk_manager = None
        self._aggregate_manager = None


    def _attach_login_context(self, context: Dict[str, Any]):
        """
        Attach login context from authentication response.

        Called by platform_operations.login() after successful authentication
        to store user/project/tenant context in the Supero instance.

        Args:
            context: Dict containing:
                - user_uuid: User UUID
                - user_email: User email
                - username: Username
                - role: User role
                - domain_name: Domain name
                - domain_uuid: Domain UUID
                - project_name: Project name
                - project_uuid: Project UUID
                - tenant_name: Tenant name
                - tenant_uuid: Tenant UUID

        Example:
            >>> # Called automatically by login()
            >>> org = supero.login('acme-corp', 'user@acme.com', 'password',
            ...                    project='production', tenant='customer-123')
            >>> # Context is now available:
            >>> print(org.project_name)  # 'production'
            >>> print(org.tenant_name)   # 'customer-123'
        """
        self._login_context = context

        # Also set as attributes for convenient access
        # This allows: org.project_name instead of org._login_context['project_name']
        for key, value in context.items():
            setattr(self, f"_{key}", value)  # Store as private attributes

    def _load_existing_domain(self, api_key: str = None):
        """
        Load existing domain if it exists.

        Args:
            api_key: Optional API key for RBAC (overrides instance default)
        """
        try:
            self._domain_obj = self._api_lib._object_read(
                'domain',
                fq_name=[self.domain_name],
                domain_name=self.domain_name,
                api_key=api_key
            )
            if self._domain_obj:
                self.__domain_uuid = getattr(self._domain_obj, 'uuid', None)
                self.logger.info(f"Loaded existing domain: {self.domain_name}")
                self._wrap_domain()
            else:
                self.logger.debug(f"Domain {self.domain_name} not found")
        except Exception as e:
            self.logger.debug(f"Could not load domain {self.domain_name}: {e}")

    @property
    def project_name(self) -> Optional[str]:
        """
        Get current project name from login context.

        Returns:
            Project name or None if not logged in

        Example:
            >>> org = supero.login('acme-corp', 'user@acme.com', 'password',
            ...                    project='production')
            >>> org.project_name
            'production'
        """
        login_context = getattr(self, '_login_context', None)
        if login_context:
            return login_context.get('project') or login_context.get('project_name')
        return getattr(self, '_project_name', None)

    @property
    def project_uuid(self) -> Optional[str]:
        """
        Get current project UUID from login context.

        Returns:
            Project UUID or None if not logged in
        """
        if self._login_context:
            return self._login_context.get('project_uuid')
        return getattr(self, '_project_uuid', None)

    @property
    def tenant_name(self) -> Optional[str]:
        """
        Get current tenant name from login context.

        Returns:
            Tenant name or None if not logged in

        Example:
            >>> org = supero.login('acme-corp', 'user@acme.com', 'password',
            ...                    project='production', tenant='customer-123')
            >>> org.tenant_name
            'customer-123'
        """
        login_context = getattr(self, '_login_context', None)
        if login_context:
            return login_context.get('tenant') or login_context.get('tenant_name')
        return getattr(self, '_tenant_name', None)

    @property
    def tenant_uuid(self) -> Optional[str]:
        """
        Get current tenant UUID from login context.

        Returns:
            Tenant UUID or None if not logged in
        """
        if self._login_context:
            return self._login_context.get('tenant_uuid')
        return getattr(self, '_tenant_uuid', None)

    @property
    def user_email(self) -> Optional[str]:
        """
        Get current user email from login context.

        Returns:
            User email or None if not logged in

        Example:
            >>> org = supero.login('acme-corp', 'user@acme.com', 'password')
            >>> org.user_email
            'user@acme.com'
        """
        if self._login_context:
            return self._login_context.get('user_email')
        return getattr(self, '_user_email', None)

    @property
    def user_uuid(self) -> Optional[str]:
        """
        Get current user UUID from login context.

        Returns:
            User UUID or None if not logged in
        """
        if self._login_context:
            return self._login_context.get('user_uuid')
        return getattr(self, '_user_uuid', None)

    @property
    def username(self) -> Optional[str]:
        """
        Get current username from login context.

        Returns:
            Username or None if not logged in
        """
        if self._login_context:
            return self._login_context.get('username')
        return getattr(self, '_username', None)

    @property
    def role(self) -> Optional[str]:
        """
        Get current user role from login context.

        Returns:
            User role (e.g., 'developer', 'admin') or None if not logged in

        Example:
            >>> org = supero.login('acme-corp', 'admin@acme.com', 'password')
            >>> org.role
            'domain_admin'
        """
        if self._login_context:
            return self._login_context.get('role')
        return getattr(self, '_role', None)

    def get_login_context(self) -> Optional[Dict[str, Any]]:
        """
        Get complete login context as dictionary.

        Returns:
            Dict with all context fields or None if not logged in

        Example:
            >>> org = supero.login('acme-corp', 'user@acme.com', 'password',
            ...                    project='production', tenant='customer-123')
            >>> context = org.get_login_context()
            >>> print(context)
            {
                'user_uuid': '...',
                'user_email': 'user@acme.com',
                'username': 'user',
                'role': 'developer',
                'domain_name': 'acme-corp',
                'domain_uuid': '...',
                'project_name': 'production',
                'project_uuid': '...',
                'tenant_name': 'customer-123',
                'tenant_uuid': '...'
            }
        """
        return self._login_context

    def switch_project(
        self,
        project_name: Optional[str] = None,
        *,  # Force keyword args after this
        project_uuid: Optional[str] = None,
        tenant_name: Optional[str] = None,
        tenant_uuid: Optional[str] = None
    ) -> 'Supero':
        """
        Switch project context and re-issue JWT tokens.

        POST /api/v1/auth/switch-project

        Request body:
        {
            "project_uuid": "...",      # Required (or project_name)
            "project_name": "...",      # Optional
            "tenant_uuid": "...",       # Optional
            "tenant_name": "..."        # Optional (defaults to 'default-tenant')
        }

        Response:
        {
            "success": true,
            "auth": {
                "access_token": "...",
                "refresh_token": "...",
                "expires_in": 28800
            },
            "context": {
                "domain": "...",
                "domain_uuid": "...",
                "project": "...",
                "project_uuid": "...",
                "tenant": "...",
                "tenant_uuid": "..."
            }
        }

        Args:
            project_name: Name of the project to switch to (can be positional)
            project_uuid: UUID of the project to switch to
            tenant_name: Name of the tenant (optional, defaults to 'default-tenant')
            tenant_uuid: UUID of the tenant (optional)

        Returns:
            Self with updated project/tenant context and new JWT token

        Raises:
            ValueError: If neither project_name nor project_uuid is provided
            APIError: If the switch fails

        Example:
            # Switch by project name (positional)
            org = org.switch_project("ecommerce")

            # Switch by project name (keyword)
            org = org.switch_project(project_name="ecommerce")

            # Switch to specific project and tenant
            org = org.switch_project("hr-system", tenant_name="sales")

            # Switch by UUID
            org = org.switch_project(project_uuid="abc-123", tenant_uuid="def-456")
        """
        if not project_name and not project_uuid:
            raise ValueError("Must provide either project_name or project_uuid")

        # Build request body
        body = {}

        if project_uuid:
            body["project_uuid"] = project_uuid
        if project_name:
            body["project_name"] = project_name
        if tenant_uuid:
            body["tenant_uuid"] = tenant_uuid
        if tenant_name:
            body["tenant_name"] = tenant_name
        # If neither tenant_uuid nor tenant_name provided, backend defaults to 'default-tenant'

        # Make the API call
        # PlatformClient.post() returns dict directly and raises exceptions on HTTP errors
        try:
            data = self._platform_client.post("/api/v1/auth/switch-project", json=body)
        except Exception as e:
            raise APIError(f"Switch project failed: {e}")

        # Check success
        if not data.get("success"):
            raise APIError("Switch project failed: success=false")

        # Extract auth tokens
        auth = data.get("auth", {})
        new_access_token = auth.get("access_token")
        new_refresh_token = auth.get("refresh_token")
        expires_in = auth.get("expires_in")

        if new_access_token:
            self._jwt_token = new_access_token
            self._platform_client.set_jwt_token(new_access_token)

        if new_refresh_token:
            self._refresh_token = new_refresh_token

        if expires_in:
            self._token_expires_in = expires_in

        # Extract context - note: backend returns 'project' not 'project_name'
        context = data.get("context", {})
        self.domain_name = context.get("domain", self.domain_name)
        self._Supero__domain_uuid = context.get("domain_uuid", self._Supero__domain_uuid)
        self._project_name = context.get("project", project_name)
        self._project_uuid = context.get("project_uuid", project_uuid)
        self._tenant_name = context.get("tenant", tenant_name or "default-tenant")
        self._tenant_uuid = context.get("tenant_uuid", tenant_uuid)

        self._login_context = context

        return self

    # Alias - add this line at class level (same indentation as def)
    use_project = switch_project

    def get(self, endpoint: str, params: Dict = None, **kwargs) -> Any:
        """
        HTTP GET request.

        Args:
            endpoint: API endpoint (e.g., "/crud/my-app/task")
            params: Query parameters

        Example:
            tasks = org.get("/crud/my-app/task")
        """
        return self._platform_client.get(endpoint, params=params, **kwargs)

    def post(self, endpoint: str, json: Dict = None, **kwargs) -> Any:
        """
        HTTP POST request.

        Args:
            endpoint: API endpoint
            json: Request body

        Example:
            result = org.post("/crud/my-app/task", json={"name": "t1", "title": "Task"})
        """
        return self._platform_client.post(endpoint, json=json, **kwargs)

    def put(self, endpoint: str, json: Dict = None, **kwargs) -> Any:
        """
        HTTP PUT request.

        Args:
            endpoint: API endpoint
            json: Request body

        Example:
            org.put("/crud/my-app/task/uuid", json={"done": True})
        """
        return self._platform_client.put(endpoint, json=json, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> Any:
        """
        HTTP DELETE request.

        Args:
            endpoint: API endpoint

        Example:
            org.delete("/crud/my-app/task/uuid")
        """
        return self._platform_client.delete(endpoint, **kwargs)

    # =========================================
    # CRUD Manager (no-SDK path)
    # =========================================

    @property
    def crud(self) -> CrudManager:
        """
        CRUD operations without SDK download.

        Provides REST-based CRUD that works immediately without install_sdk().

        Example:
            # Basic CRUD
            task = org.crud.create("task", name="t1", title="Learn Supero")
            tasks = org.crud.list("task")
            org.crud.update("task", uuid, done=True)
            org.crud.delete("task", uuid)

            # Query with filters
            tasks = org.crud.query("task").filter(done=False).order_by("-created").all()

            # Aggregations
            total = org.crud.count("task")
            revenue = org.crud.sum("order", "amount")
        """
        if not hasattr(self, '_crud_manager'):
            self._crud_manager = CrudManager(self)
        return self._crud_manager

    @property
    def users(self) -> UserManager:
        """
        Get UserManager instance for user operations.
        
        Returns:
            UserManager instance
        
        Example:
            >>> user_mgr = org.users
            >>> domain_uuid = org._domain_uuid
            >>> user = user_mgr.add_user(
            ...     domain_uuid=domain_uuid,
            ...     email='dev@acme.com',
            ...     password='Pass123!',
            ...     name='Developer'
            ... )
        """
        return self._get_user_manager()
    
    @property
    def schemas_manager(self) -> SchemaManager:
        """
        Get SchemaManager instance for schema operations.
        
        Returns:
            SchemaManager instance
        
        Example:
            >>> schema_mgr = org.schemas_manager
            >>> domain_uuid = org._domain_uuid
            >>> result = schema_mgr.upload_schema(
            ...     domain_uuid=domain_uuid,
            ...     schema_file='schemas/project.json'
            ... )
        """
        return self._get_schema_manager()
    
    @property
    def sdks(self) -> SDKManager:
        """
        Get SDKManager instance for SDK operations.
        
        Returns:
            SDKManager instance
        
        Example:
            >>> sdk_mgr = org.sdks
            >>> domain_uuid = org._domain_uuid
            >>> result = sdk_mgr.generate_sdk(
            ...     domain_uuid=domain_uuid,
            ...     languages=['python']
            ... )
        """
        return self._get_sdk_manager()

    @property
    def aggregate(self) -> AggregateManager:
        """
        Get AggregateManager instance for analytics operations.

        Returns:
            AggregateManager instance

        Example:
            >>> agg_mgr = org.aggregate
            >>>
            >>> # Get stats
            >>> stats = agg_mgr.stats('order', fields=['amount'])
            >>> print(f"Total: {stats['count']}")
            >>>
            >>> # Count by field
            >>> by_status = agg_mgr.count_by('order', 'status')
            >>> for item in by_status:
            ...     print(f"{item['value']}: {item['count']}")
            >>>
            >>> # Custom pipeline
            >>> results = agg_mgr.aggregate('order', [
            ...     {'$match': {'status': 'completed'}},
            ...     {'$group': {'_id': '$category', 'total': {'$sum': '$amount'}}}
            ... ])
            >>>
            >>> # Convenience methods
            >>> total_revenue = agg_mgr.sum('order', 'amount')
            >>> avg_order = agg_mgr.avg('order', 'amount')
            >>> order_count = agg_mgr.count('order', match={'status': 'completed'})
        """
        return self._get_aggregate_manager()

    # FIX #3: Add _domain_uuid property
    @property
    def _domain_uuid(self) -> Optional[str]:
        """
        Get domain UUID for manager operations.
        
        This property provides easy access to the domain UUID needed
        for all manager operations (user, schema, SDK management).
        
        Returns:
            Domain UUID string or None if domain not initialized
        
        Example:
            >>> org = Supero.quickstart("acme-corp", jwt_token="...")
            >>> domain_uuid = org._domain_uuid
            >>> user_mgr = org.users
            >>> user_mgr.add_user(domain_uuid, "dev@acme.com", "Pass123!", ...)
        """
        # Return cached value if set
        if self.__domain_uuid:
            return self.__domain_uuid
        
        # Try to get from domain object
        if self._domain_obj:
            uuid = getattr(self._domain_obj, 'uuid', None)
            if uuid:
                self.__domain_uuid = uuid
                return uuid
        
        return None
    
    @_domain_uuid.setter
    def _domain_uuid(self, value: str):
        """Set domain UUID."""
        self.__domain_uuid = value

    def __getattr__(self, name: str):
        """
        Enable direct schema access: org.Project instead of org.schemas.Project

        ✅ CamelCase schema names are allowed (case-insensitive via normalization)

        Valid examples:
            project = org.Project.create(name="Backend")
            user = org.UserAccount.create(name="Alice")
            key = org.ApiKey.find_one(name="prod-key")
            # Both work:
            item = org.POLineItem.create(...)  # Original name
            item = org.PoLineItem.create(...)  # Also works!

        Invalid examples:
            org.project.create()      # ❌ Use org.Project
            org.user_account.create() # ❌ Use org.UserAccount
            org.api_key.find()        # ❌ Use org.ApiKey

        Args:
            name: Attribute name (must be CamelCase for schemas)

        Returns:
            SchemaProxy for the schema if name matches a schema

        Raises:
            AttributeError: If attribute is not found or not in CamelCase
        """
        # Avoid recursion for private/internal attributes
        if name.startswith('_'):
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )

        # Special case: 'schemas' property
        if name == 'schemas':
            if not hasattr(self, '_schema_registry'):
                self._schema_registry = SchemaRegistry(self)
            return self._schema_registry

        # Don't intercept other known Supero attributes
        known_attrs = {
            'domain_name', 'package_namespace', 'api_lib', 'logger',
            'domain', 'SYSTEM_DOMAINS',
            'users', 'schemas_manager', 'sdks'  # Manager properties
        }
        if name in known_attrs:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )

        # Get available schemas
        try:
            available_schemas = self._list_schemas()
        except Exception as e:
            self.logger.error(f"Schema discovery failed: {e}", exc_info=True)
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'. "
                f"Schema discovery failed: {e}"
            )

        # ✅ ENFORCE: Validate CamelCase format
        if not self._is_valid_camelcase(name):
            suggestion = self._suggest_camelcase(name)

            # Check if suggestion exists in available schemas
            suggestion_exists = suggestion in available_schemas

            error_parts = [
                f"Schema names must be in CamelCase format.",
                f"Use 'org.{suggestion}' instead of 'org.{name}'",
                "",
                "Examples:",
                "  • org.Project (not org.project)",
                "  • org.UserAccount (not org.user_account)",
                "  • org.ApiKey (not org.api_key)"
            ]

            if suggestion_exists:
                error_parts.append(f". Did you mean: '{suggestion}'?")

            raise AttributeError('\n'.join(error_parts))

        # Initialize schema proxies cache
        if not hasattr(self, '_schema_proxies'):
            self._schema_proxies = {}

        # =========================================================================
        # SCHEMA LOOKUP (with normalization for case-insensitive matching)
        # =========================================================================

        # Fast path: exact match
        if name in available_schemas:
            if name not in self._schema_proxies:
                self._schema_proxies[name] = SchemaProxy(name, self)
            return self._schema_proxies[name]

        normalized_requested = normalize_schema_name(name)
        for schema_name in available_schemas:
            if normalize_schema_name(schema_name) == normalized_requested:
                # Found! Use the actual registered schema name
                if schema_name not in self._schema_proxies:
                    self._schema_proxies[schema_name] = SchemaProxy(schema_name, self)
                return self._schema_proxies[schema_name]

        # =========================================================================
        # NOT FOUND - show helpful error message
        # =========================================================================
        suggestions = self._find_similar_schemas(name, available_schemas)
        error_msg = f"Schema '{name}' not found.\nAvailable schemas: {', '.join(sorted(available_schemas))}"

        if suggestions:
            suggestions_formatted = ', '.join(f"'{s}'" for s in suggestions)
            error_msg += f". Did you mean: {suggestions_formatted}?"

        raise AttributeError(error_msg)

    @staticmethod
    def _is_valid_camelcase(name: str) -> bool:
        """
        Validate that name is in CamelCase format.
        
        Valid: Project, UserAccount, ApiKey, MyCustomSchema
        Invalid: project, user_account, api_key, myCustomSchema (camelCase)
        
        Args:
            name: String to validate
        
        Returns:
            bool: True if valid CamelCase (PascalCase)
        """
        import re
        # Must start with uppercase letter
        # Can contain letters and numbers (no underscores or dashes)
        return bool(re.match(r'^[A-Z][a-zA-Z0-9]*$', name))

    @staticmethod
    def _suggest_camelcase(name: str) -> str:
        """
        Suggest CamelCase version of a name.
        
        Examples:
            project → Project
            user_account → UserAccount
            api_key → ApiKey
            mySchema → MySchema
        
        Args:
            name: Input name in any format
        
        Returns:
            str: Suggested CamelCase name
        """
        import re
        
        if '_' in name or '-' in name:
            # Split on underscores/dashes and capitalize each part
            parts = re.split(r'[_-]', name)
            return ''.join(part.capitalize() for part in parts)
        elif name.islower():
            # Simple lowercase -> Capitalize
            return name.capitalize()
        else:
            # Already has some caps, ensure first letter is uppercase
            return name[0].upper() + name[1:]
    
    @staticmethod
    def _find_similar_schemas(name: str, available: list) -> list:
        """
        Find schemas with similar names (case-insensitive match or close spelling).
        
        Args:
            name: Schema name being searched
            available: List of available schema names
        
        Returns:
            list: List of similar schema names
        """
        suggestions = []
        name_lower = name.lower()
        
        # First, check for exact case-insensitive match
        for schema in available:
            if schema.lower() == name_lower:
                suggestions.append(schema)
        
        # If no exact match, check for partial matches or typos
        if not suggestions:
            for schema in available:
                # Check if names are very similar (Levenshtein-like)
                if (name_lower in schema.lower() or 
                    schema.lower() in name_lower or
                    name_lower.replace('_', '') == schema.lower()):
                    suggestions.append(schema)
        
        return suggestions[:3]  # Return max 3 suggestions

    @staticmethod
    def _is_valid_camelcase(name: str) -> bool:
        """
        Validate that name is in CamelCase format.
        
        Valid: Project, UserAccount, ApiKey, MyCustomSchema
        Invalid: project, user_account, api_key, myCustomSchema (camelCase)
        
        Args:
            name: String to validate
        
        Returns:
            bool: True if valid CamelCase (PascalCase)
        """
        import re
        # Must start with uppercase letter
        # Can contain letters and numbers (no underscores or dashes)
        return bool(re.match(r'^[A-Z][a-zA-Z0-9]*$', name))

    @staticmethod
    def _suggest_camelcase(name: str) -> str:
        """
        Suggest CamelCase version of a name.
        
        Examples:
            project → Project
            user_account → UserAccount
            api_key → ApiKey
            mySchema → MySchema
        
        Args:
            name: Input name in any format
        
        Returns:
            str: Suggested CamelCase name
        """
        import re
        
        if '_' in name or '-' in name:
            # Split on underscores/dashes and capitalize each part
            parts = re.split(r'[_-]', name)
            return ''.join(part.capitalize() for part in parts)
        elif name.islower():
            # Simple lowercase -> Capitalize
            return name.capitalize()
        else:
            # Already has some caps, ensure first letter is uppercase
            return name[0].upper() + name[1:]
    
    def __dir__(self):
        """
        Enable IDE autocomplete for schema names.
        
        Returns all Supero attributes plus available schema names,
        allowing IDE autocomplete to suggest org.Project, org.User, etc.
        
        Returns:
            List of attribute names including schema names
        
        Example:
            >>> org = quickstart("acme-corp")
            >>> dir(org)
            ['Project', 'User', 'Task', 'domain', 'schemas', ...]
        """
        # Get default object attributes
        default_attrs = list(object.__dir__(self))
        
        # Add schema names for autocomplete
        try:
            schemas = self._list_schemas()
            # Combine and deduplicate
            all_attrs = list(set(default_attrs + schemas))
            return sorted(all_attrs)
        except Exception:
            # If schema discovery fails, just return default attributes
            return default_attrs

    # ============================================================================
    # Find this method in your existing core.py (around line 1041)
    # REPLACE the existing method with this version:
    # ============================================================================

    @classmethod
    def _auto_detect_namespace(cls, domain_name: str) -> str:
        """
        Auto-detect package namespace based on domain name.
        
        ✅ FIXED: Properly imports TENANT_NAMESPACE from _runtime_config
        
        Args:
            domain_name: Domain name

        Returns:
            Package namespace string (e.g., 'pymodel_system', 'pymodel_my_tenant')

        Logic:
            - System domains (Domain, ApiKey, etc.) → pymodel_system
            - All other domains → tenant namespace from build config
            - If no tenant namespace configured → try to find non-system namespace
            - Final fallback → pymodel_system
        """
        # ✅ FIX: Import at function level to get current runtime values
        # This is important for tests that mock _runtime_config
        TENANT_NAMESPACE = None
        SCHEMA_NAMESPACES = ['pymodel_system']
        
        try:
            from py_api_lib._runtime_config import TENANT_NAMESPACE, SCHEMA_NAMESPACES
        except ImportError:
            # Fallback values if import fails
            pass
        
        # System domains always use pymodel_system
        if domain_name in cls.SYSTEM_DOMAINS:
            return "pymodel_system"
        
        # For non-system domains, use tenant namespace
        else:
            # Priority 1: Use explicitly configured TENANT_NAMESPACE
            if TENANT_NAMESPACE:
                return TENANT_NAMESPACE
            
            # Priority 2: Scan SCHEMA_NAMESPACES for non-system namespace
            if SCHEMA_NAMESPACES:
                for ns in SCHEMA_NAMESPACES:
                    if ns != 'pymodel_system':
                        return ns
            
            # Priority 3: Fallback to system namespace
            return "pymodel_system"

    @classmethod
    def quickstart(cls, name: str, project: str = 'default-project', jwt_token: str = None,
                   package_namespace: str = None, tenant: str = 'default-tenant', **kwargs) -> 'Supero':
        """One-line initialization for tenant applications."""
        # Initialize Supero environment (loggers, etc.)
        app_name = kwargs.pop('app_name', name)
        log_level = kwargs.pop('log_level', 'INFO')
        from supero import init
        init(app_name=app_name, log_level=log_level)

        # Extract proxy-specific kwargs
        platform_core_host = kwargs.pop('platform_core_host', None)
        platform_core_port = kwargs.pop('platform_core_port', 443)
        api_key = kwargs.pop('api_key', None)

        # Extract and discard kwargs that aren't for Supero.__init__
        _ = kwargs.pop('timeout', None)
        _ = kwargs.pop('api_server_host', None)
        _ = kwargs.pop('api_server_port', None)
        _ = kwargs.pop('max_retries', None)

        # Smart mode detection
        if 'use_proxy' in kwargs:
            use_proxy = kwargs.pop('use_proxy')
        else:
            if jwt_token and not api_key:
                use_proxy = True
            elif api_key and not jwt_token:
                use_proxy = False
            elif not jwt_token and not api_key:
                use_proxy = False  # Testing mode
            else:
                use_proxy = True

        # FIX #4: More lenient validation that allows testing mode
        is_testing = not jwt_token and not api_key

        if not is_testing:
            # Only validate when NOT in testing mode
            if use_proxy and not jwt_token:
                raise ValueError(
                    "jwt_token is required for proxy mode. "
                    "Provide jwt_token or set use_proxy=False to use api_key. "
                    "For testing without auth, omit both jwt_token and api_key."
                )

            if not use_proxy and not api_key:
                raise ValueError(
                    "api_key is required for direct mode. "
                    "Provide api_key or set use_proxy=True to use jwt_token. "
                    "For testing without auth, omit both jwt_token and api_key."
                )

        return cls(
            domain_name=name,
            package_namespace=package_namespace,
            use_proxy=use_proxy,
            jwt_token=jwt_token,
            api_key=api_key,
            platform_core_host=platform_core_host,
            platform_core_port=platform_core_port,
            project=project,      # ← ADDED
            tenant=tenant,        # ← ADDED
            **kwargs
        )

    @classmethod
    def connect(cls, domain_name: str, project: str = 'default-project',
                jwt_token: str = None, package_namespace: str = None,
                tenant: str = 'default-tenant', **kwargs) -> 'Supero':
        """Connect to existing domain."""
        api_key = kwargs.pop('api_key', None)

        # Extract and discard kwargs that aren't for Supero.__init__
        _ = kwargs.pop('timeout', None)
        _ = kwargs.pop('api_server_host', None)
        _ = kwargs.pop('api_server_port', None)
        _ = kwargs.pop('max_retries', None)

        # Smart mode detection
        if 'use_proxy' in kwargs:
            use_proxy = kwargs.pop('use_proxy')
        else:
            if jwt_token and not api_key:
                use_proxy = True
            elif api_key and not jwt_token:
                use_proxy = False
            elif not jwt_token and not api_key:
                use_proxy = False  # Testing mode
            else:
                use_proxy = True

        # FIX #4: Same improved validation
        is_testing = not jwt_token and not api_key

        if not is_testing:
            if use_proxy and not jwt_token:
                raise ValueError(
                    "jwt_token is required for proxy mode. "
                    "For testing without auth, omit both jwt_token and api_key."
                )

            if not use_proxy and not api_key:
                raise ValueError(
                    "api_key is required for direct mode. "
                    "For testing without auth, omit both jwt_token and api_key."
                )

        return cls(
            domain_name=domain_name,
            package_namespace=package_namespace,
            auto_create_domain=False,
            use_proxy=use_proxy,
            jwt_token=jwt_token,
            api_key=api_key,
            project=project,      # ← ADDED
            tenant=tenant,        # ← ADDED
            **kwargs
        )

    def _get_platform_client(self) -> PlatformClient:
        """Get or create Platform Client instance."""
        if not hasattr(self, '_platform_client'):
            # Extract connection info from api_lib
            host = default_platform_core_host
            port = default_platform_core_port
            
            # Build base_url for v3.0 API
            protocol = "https" if port == 443 else "http"
            base_url = f"{protocol}://{host}:{port}/api/v1"
            
            # Get JWT token if available
            jwt_token = getattr(self._api_lib, '_jwt_token', None)
            
            self._platform_client = PlatformClient(
                base_url=base_url,
                jwt_token=jwt_token
            )
        
        return self._platform_client

    @property
    def jwt_token(self) -> Optional[str]:
        """
        Get current JWT token.

        Returns:
            JWT token string or None if not authenticated

        Example:
            >>> org = login("acme", "user@acme.com", "password")
            >>> token = org.jwt_token
            >>> headers = {"Authorization": f"Bearer {token}"}
        """
        return self._jwt_token

    def get_token(self):
        return self._jwt_token

    @classmethod
    def login(cls, domain_name: str, email: str, password: str,
              project: str = "default-project", tenant: str = "default-tenant",
              platform_core_host: str = None, platform_core_port: int = 443,
              **kwargs) -> 'Supero':
        """
        Login and connect in one step (for tenant applications).

        Performs authentication and returns connected Supero instance.

        Args:
            domain_name: Domain name
            email: User email
            password: User password
            project: Project name (default: 'default-project')
            tenant: Tenant name (default: 'default-tenant')
            platform_core_host: Platform Core hostname
            platform_core_port: Platform Core port
            **kwargs: Additional parameters

        Returns:
            Connected Supero instance with JWT authentication

        Raises:
            AuthenticationError: If login fails

        Examples:
            # Login and connect
            >>> org = Supero.login(
            ...     domain_name="acme-corp",
            ...     email="alice@acme.com",
            ...     password="secret123"
            ... )
            >>> project = org.Project.create(name="Backend")

            # With custom platform-core
            >>> org = Supero.login(
            ...     domain_name="acme-corp",
            ...     email="alice@acme.com",
            ...     password="secret123",
            ...     platform_core_host="platform.acme.com"
            ... )
        """
        import requests
        import os

        # Auto-detect platform-core host
        if platform_core_host is None:
            platform_core_host = default_platform_core_host

        # Perform login
        login_url = f"http://{platform_core_host}:{platform_core_port}/api/v1/auth/login"

        try:
            response = requests.post(
                login_url,
                json={
                    'project': project,
                    'tenant': tenant,
                    'email': email,
                    'password': password,
                    'domain': domain_name
                },
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                jwt_token = data.get('token')

                if not jwt_token:
                    raise ValueError("Login response missing JWT token")

                # Connect with JWT
                return cls.quickstart(
                    name=domain_name,
                    project=project,      # ← ADDED
                    tenant=tenant,        # ← ADDED
                    jwt_token=jwt_token,
                    platform_core_host=platform_core_host,
                    platform_core_port=platform_core_port,
                    **kwargs
                )
            else:
                error_msg = response.json().get('error', response.text)
                raise AuthenticationError(
                    f"Login failed: {error_msg}"
                )

        except requests.exceptions.RequestException as e:
            raise ConnectionError(
                f"Could not connect to Platform Core at {login_url}: {e}"
            )
    
    
    # ============================================
    # SCHEMA MANAGEMENT (Domain Operations)
    # ============================================

    def _get_schema_manager(self) -> SchemaManager:
        """Get or create SchemaManager instance."""
        if self._schema_manager is None:
            self._schema_manager = SchemaManager(
                platform_client=self._get_platform_client(),
                logger=self.logger
            )
        return self._schema_manager

    def upload_schema(
        self,
        schema_file: str,
        schema_type: str = None,
        description: str = None,
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        Upload schema definition (JSON format) to this domain.

        See SchemaManager.upload_schema() for full documentation.

        Example:
            >>> result = org.upload_schema('schemas/objects/project.json')
            >>> print(f"Uploaded: {result['filename']}.json")
        """
        return self._get_schema_manager().upload_schema(
            schema_file=schema_file,
            schema_type=schema_type,
            description=description,
            validate=validate
        )

    def upload_schemas(
        self,
        directory: str,
        recursive: bool = True,
        **kwargs
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Upload multiple schemas from directory structure.

        See SchemaManager.upload_schemas() for full documentation.

        Example:
            >>> results = org.upload_schemas('schemas/')
            >>> print(f"Objects: {len(results['objects'])}")
        """
        return self._get_schema_manager().upload_schemas(
            directory=directory,
            recursive=recursive,
            **kwargs
        )

    def list_schemas_info(
        self,
        schema_type: str = None,
        status: str = 'active'
    ) -> List[Dict[str, Any]]:
        """
        List schemas in this domain from Platform Core.

        See SchemaManager.list_schemas() for full documentation.

        Example:
            >>> schemas = org.list_schemas_info(schema_type='object')
            >>> for schema in schemas:
            ...     print(f"{schema['filename']}.json")
        """
        return self._get_schema_manager().list_schemas(
            schema_type=schema_type,
            status=status
        )

    def get_schema_info(
        self,
        filename: str
    ) -> Dict[str, Any]:
        """
        Get schema definition and metadata from Platform Core.

        See SchemaManager.get_schema() for full documentation.

        Example:
            >>> schema = org.get_schema_info('project')
            >>> print(f"Type: {schema['schema_type']}")
        """
        return self._get_schema_manager().get_schema(filename)

    def validate_schema(
        self,
        schema_data: Dict[str, Any],
        schema_type: str = 'object'
    ) -> Dict[str, Any]:
        """
        Validate schema definition against schema rules.

        See SchemaManager.validate_schema() for full documentation.

        Example:
            >>> validation = org.validate_schema(schema_dict, 'object')
            >>> if not validation['valid']:
            ...     print(f"Errors: {validation['errors']}")
        """
        return self._get_schema_manager().validate_schema(
            schema_data=schema_data,
            schema_type=schema_type
        )

    def delete_schema(
        self,
        filename: str
    ) -> bool:
        """
        Delete schema from this domain.

        See SchemaManager.delete_schema() for full documentation.

        Example:
            >>> org.delete_schema('old_schema')
        """
        return self._get_schema_manager().delete_schema(filename)

    def get_schema_hierarchy(self) -> Dict[str, Any]:
        """
        Get complete schema hierarchy for this domain.

        See SchemaManager.get_hierarchy() for full documentation.

        Example:
            >>> hierarchy = org.get_schema_hierarchy()
            >>> domain_children = hierarchy['domain']['children']
        """
        return self._get_schema_manager().get_hierarchy()

    def export_schemas(
        self,
        output_directory: str,
        schema_type: str = None,
        create_structure: bool = True
    ) -> Dict[str, Any]:
        """
        Export schemas to local directory in standard structure.

        See SchemaManager.export_schemas() for full documentation.

        Example:
            >>> result = org.export_schemas('my_schemas/')
            >>> for item in result['exported']:
            ...     print(f"✓ {item['filename']} → {item['path']}")
        """
        return self._get_schema_manager().export_schemas(
            output_directory=output_directory,
            schema_type=schema_type,
            create_structure=create_structure
        )

        # ========================================================================
    # AI MANAGER (Lazy-loaded)
    # ========================================================================

    @property
    def ai(self) -> 'AIManager':
        """
        Get AI Manager for natural language interactions.

        The AI Manager provides:
        - Natural language chat with schema-aware tools
        - Conversation sessions for context continuity
        - Direct tool invocation
        - Vector search for RAG

        Returns:
            AIManager instance

        Example:
            >>> org = Supero.quickstart("acme-corp", jwt_token="...")
            >>>
            >>> # Simple chat
            >>> response = org.ai.chat("Show me all active projects")
            >>> print(response.content)
            >>>
            >>> # With session for multi-turn conversation
            >>> session = org.ai.sessions.create()
            >>> org.ai.chat("What projects exist?", session_id=session.id)
            >>> org.ai.chat("Create a task for the first one", session_id=session.id)
            >>>
            >>> # Streaming response
            >>> for chunk in org.ai.chat_stream("Explain our architecture"):
            ...     print(chunk, end="", flush=True)
            >>>
            >>> # List AI tools (generated from schemas)
            >>> tools = org.ai.tools.list()
            >>> for tool in tools:
            ...     print(f"{tool.name}: {tool.description}")
            >>>
            >>> # Direct tool invocation
            >>> result = org.ai.tools.invoke("list_projects", status="active")
            >>>
            >>> # Vector search for RAG
            >>> org.ai.vectors.index(content="...", metadata={...})
            >>> results = org.ai.vectors.search("backend architecture")
            >>>
            >>> # Quick question-answer
            >>> answer = org.ai.ask("How many users do we have?")
            >>>
            >>> # Natural language query
            >>> projects = org.ai.query("active projects with high priority")
        """
        return self._get_ai_manager()

    def _get_ai_manager(self) -> 'AIManager':
        """Get or create AIManager instance."""
        if self._ai_manager is None:
            from .ai_manager import AIManager

            self._ai_manager = AIManager(
                platform_client=self._get_platform_client(),
                logger=self.logger
            )
        return self._ai_manager

    # ========================================================================
    # CONVENIENCE AI METHODS (Direct on org object)
    # ========================================================================

    def chat(
        self,
        message: str,
        session_id: str = None,
        **kwargs
    ):
        """
        Quick chat with AI (convenience method).

        Shortcut for org.ai.chat().

        Args:
            message: Your message
            session_id: Optional session for context
            **kwargs: Additional chat options

        Returns:
            ChatResponse with AI reply

        Example:
            >>> response = org.chat("Show me active projects")
            >>> print(response.content)
        """
        return self.ai.chat(message, session_id=session_id, **kwargs)

    def ask(
        self,
        question: str,
        **kwargs
    ) -> str:
        """
        Quick question (returns just text).

        Shortcut for org.ai.ask().

        Args:
            question: Your question
            **kwargs: Additional options

        Returns:
            Answer text

        Example:
            >>> answer = org.ask("How many users exist?")
            >>> print(answer)
        """
        return self.ai.ask(question, **kwargs)

    # ============================================
    # USER MANAGEMENT (Domain Operations)
    # ============================================

    def _get_user_manager(self) -> UserManager:
        """Get or create UserManager instance."""
        if self._user_manager is None:
            self._user_manager = UserManager(
                platform_client=self._get_platform_client(),
                logger=self.logger,
            )
        return self._user_manager

    # ========================================================================
    # USER MANAGEMENT (Domain Operations)
    # 
    # NOTE: These manage platform authentication users (who can login).
    # For business user objects (data models), use your SDK schemas.
    # ========================================================================

    def add_user(
        self,
        email: str,
        password: str,
        name: str,
        role: str = 'user',
        permissions: List[str] = None,
        **profile_data
    ) -> Dict[str, Any]:
        """
        Add user to this domain.

        See UserManager.add_user() for full documentation.

        Example:
            >>> user = org.add_user(
            ...     email='dev@acme.com',
            ...     password='SecurePass123!',
            ...     name='Developer',
            ...     role='developer'
            ... )
        """
        return self._get_user_manager().add_user(
            email=email,
            password=password,
            name=name,
            role=role,
            permissions=permissions,
            **profile_data
        )

    def list_users(
        self,
        role: str = None,
        status: str = 'active',
        limit: int = None,
        offset: int = None
    ) -> List[Dict[str, Any]]:
        """
        List users in this domain.

        See UserManager.list_users() for full documentation.

        Example:
            >>> all_users = org.list_users()
            >>> admins = org.list_users(role='admin')
        """
        return self._get_user_manager().list_users(
            role=role,
            status=status,
            limit=limit,
            offset=offset
        )

    def get_user(
        self,
        user_uuid: str
    ) -> Dict[str, Any]:
        """
        Get user details by UUID.

        See UserManager.get_user() for full documentation.

        Example:
            >>> user = org.get_user('user-uuid-123')
            >>> print(f"Name: {user['name']}")
        """
        return self._get_user_manager().get_user(user_uuid)

    def update_user(
        self,
        user_uuid: str,
        **updates
    ) -> Dict[str, Any]:
        """
        Update user in this domain.

        See UserManager.update_user() for full documentation.

        Example:
            >>> org.update_user(
            ...     user_uuid='user-123',
            ...     role='admin'
            ... )
        """
        return self._get_user_manager().update_user(user_uuid, **updates)

    def remove_user(
        self,
        user_uuid: str,
        permanent: bool = False
    ) -> bool:
        """
        Remove user from this domain.

        See UserManager.remove_user() for full documentation.

        Example:
            >>> org.remove_user('user-123')
        """
        return self._get_user_manager().remove_user(user_uuid, permanent)

    def search_users(
        self,
        query: str,
        fields: List[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search users by query string.

        See UserManager.search_users() for full documentation.

        Example:
            >>> users = org.search_users('john')
        """
        return self._get_user_manager().search_users(query, fields, limit)

    # ============================================
    # USER ROLES & PERMISSIONS
    # ============================================

    def list_roles(self) -> List[Dict[str, Any]]:
        """
        List available roles in this domain.

        See UserManager.list_roles() for full documentation.

        Example:
            >>> roles = org.list_roles()
        """
        return self._get_user_manager().list_roles()

    def assign_role(
        self,
        user_uuid: str,
        role: str
    ) -> Dict[str, Any]:
        """
        Assign role to user.

        See UserManager.assign_role() for full documentation.

        Example:
            >>> org.assign_role('user-123', 'admin')
        """
        return self._get_user_manager().assign_role(user_uuid, role)

    def grant_permissions(
        self,
        user_uuid: str,
        permissions: List[str]
    ) -> Dict[str, Any]:
        """
        Grant additional permissions to user.

        See UserManager.grant_permissions() for full documentation.

        Example:
            >>> org.grant_permissions('user-123', ['write'])
        """
        return self._get_user_manager().grant_permissions(user_uuid, permissions)

    def revoke_permissions(
        self,
        user_uuid: str,
        permissions: List[str]
    ) -> Dict[str, Any]:
        """
        Revoke permissions from user.

        See UserManager.revoke_permissions() for full documentation.

        Example:
            >>> org.revoke_permissions('user-123', ['write'])
        """
        return self._get_user_manager().revoke_permissions(user_uuid, permissions)

    # ============================================
    # CURRENT USER OPERATIONS (Profile)
    # ============================================

    def whoami(self) -> Dict[str, Any]:
        """
        Get current authenticated user info.

        See UserManager.whoami() for full documentation.

        Example:
            >>> user = org.whoami()
            >>> print(f"Logged in as: {user['email']}")
        """
        return self._get_user_manager().whoami()

    def update_profile(
        self,
        **updates
    ) -> Dict[str, Any]:
        """
        Update current user's profile.

        See UserManager.update_profile() for full documentation.

        Example:
            >>> org.update_profile(name='New Name', phone='+1-555-0100')
        """
        return self._get_user_manager().update_profile(**updates)

    def change_password(
        self,
        old_password: str,
        new_password: str
    ) -> bool:
        """
        Change current user's password.

        See UserManager.change_password() for full documentation.

        Example:
            >>> success = org.change_password('OldPass123', 'NewPass456')
        """
        return self._get_user_manager().change_password(old_password, new_password)

    def request_password_reset(
        self,
        email: str
    ) -> bool:
        """
        Request password reset for a user.

        See UserManager.request_password_reset() for full documentation.

        Example:
            >>> org.request_password_reset('user@acme.com')
        """
        return self._get_user_manager().request_password_reset(email)

    # ============================================
    # BULK USER OPERATIONS
    # ============================================

    def bulk_add_users(
        self,
        users: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Add multiple users in bulk.

        See UserManager.bulk_add_users() for full documentation.

        Example:
            >>> users = [
            ...     {'email': 'dev1@acme.com', 'password': 'Pass123!', 'name': 'Dev 1', 'role': 'developer'},
            ...     {'email': 'dev2@acme.com', 'password': 'Pass456!', 'name': 'Dev 2', 'role': 'developer'}
            ... ]
            >>> result = org.bulk_add_users(users)
        """
        return self._get_user_manager().bulk_add_users(users)

    def bulk_update_users(
        self,
        updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Update multiple users in bulk.

        See UserManager.bulk_update_users() for full documentation.

        Example:
            >>> updates = [
            ...     {'user_uuid': 'user-1', 'role': 'admin'},
            ...     {'user_uuid': 'user-2', 'role': 'admin'}
            ... ]
            >>> result = org.bulk_update_users(updates)
        """
        return self._get_user_manager().bulk_update_users(updates)

    def get_user_stats(self) -> Dict[str, Any]:
        """
        Get user statistics for this domain.

        See UserManager.get_user_stats() for full documentation.

        Example:
            >>> stats = org.get_user_stats()
            >>> print(f"Total users: {stats['total_users']}")
        """
        return self._get_user_manager().get_user_stats()

    # ============================================
    # SDK GENERATION (Domain Operations)
    # ============================================

    def _get_sdk_manager(self) -> SDKManager:
        """Get or create SDKManager instance."""
        if self._sdk_manager is None:
            self._sdk_manager = SDKManager(
                platform_client=self._get_platform_client(),
                logger=self.logger
            )
        return self._sdk_manager

    def _get_aggregate_manager(self) -> AggregateManager:
        """Get or create AggregateManager instance with context from client."""
        if self._aggregate_manager is None:
            self._aggregate_manager = AggregateManager(
                platform_client=self._get_platform_client(),
                logger=self.logger
            )
        return self._aggregate_manager

    def generate_sdk(
        self,
        language: str = 'python',
        version: str = None,
        include_schemas: List[str] = None,
        exclude_schemas: List[str] = None,
        output_format: str = 'wheel',
        **options
    ) -> Dict[str, Any]:
        """
        Generate SDK package for this domain's schemas.
        
        See SDKManager.generate_sdk() for full documentation.
        
        Example:
            >>> result = org.generate_sdk(language='python')
            >>> print(f"SDK version: {result['version']}")
        """
        return self._get_sdk_manager().generate_sdk(
            language=language,
            version=version,
            include_schemas=include_schemas,
            exclude_schemas=exclude_schemas,
            output_format=output_format,
            **options
        )

    def generate_multi_language(
        self,
        languages: List[str],
        **common_options
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate SDKs for multiple languages simultaneously.
        
        See SDKManager.generate_multi_language() for full documentation.
        
        Example:
            >>> results = org.generate_multi_language(
            ...     languages=['python', 'javascript', 'go']
            ... )
        """
        return self._get_sdk_manager().generate_multi_language(
            languages=languages,
            **common_options
        )

    def download_sdk(
        self,
        sdk_uuid: str = None,
        version: str = None,
        language: str = None,
        output_path: str = None
    ) -> str:
        """
        Download SDK package.
        
        See SDKManager.download_sdk() for full documentation.
        
        Example:
            >>> path = org.download_sdk(sdk_uuid='sdk-123')
            >>> print(f"Downloaded to: {path}")
        """
        return self._get_sdk_manager().download_sdk(
            sdk_uuid=sdk_uuid,
            version=version,
            language=language,
            output_path=output_path
        )

    def download_all_languages(
        self,
        version: str = None,
        output_directory: str = '.'
    ) -> Dict[str, str]:
        """
        Download SDKs for all available languages.
        
        See SDKManager.download_all_languages() for full documentation.
        
        Example:
            >>> paths = org.download_all_languages(output_directory='./sdks/')
        """
        return self._get_sdk_manager().download_all_languages(
            version=version,
            output_directory=output_directory
        )

    def list_sdks(
        self,
        language: str = None,
        version: str = None
    ) -> List[Dict[str, Any]]:
        """
        List available SDK packages for this domain.
        
        See SDKManager.list_sdks() for full documentation.
        
        Example:
            >>> sdks = org.list_sdks(language='python')
            >>> for sdk in sdks:
            ...     print(f"v{sdk['version']} - {sdk['created_at']}")
        """
        return self._get_sdk_manager().list_sdks(
            language=language,
            version=version
        )

    def get_sdk_info(
        self,
        sdk_uuid: str
    ) -> Dict[str, Any]:
        """
        Get detailed SDK information.
        
        See SDKManager.get_sdk_info() for full documentation.
        
        Example:
            >>> info = org.get_sdk_info('sdk-uuid-123')
            >>> print(f"Schemas: {info['schemas_included']}")
        """
        return self._get_sdk_manager().get_sdk_info(sdk_uuid)

    def get_latest_sdk_version(
        self,
        language: str = None
    ) -> str:
        """
        Get latest SDK version for domain.
        
        See SDKManager.get_latest_version() for full documentation.
        
        Example:
            >>> version = org.get_latest_sdk_version('python')
            >>> print(f"Latest: {version}")
        """
        return self._get_sdk_manager().get_latest_version(language)

    def delete_sdk(
        self,
        sdk_uuid: str
    ) -> bool:
        """
        Delete SDK package.
        
        See SDKManager.delete_sdk() for full documentation.
        
        Example:
            >>> org.delete_sdk('old-sdk-uuid')
        """
        return self._get_sdk_manager().delete_sdk(sdk_uuid)

    def install_python_sdk(
        self,
        sdk_uuid: str = None,
        version: str = None,
        upgrade: bool = True
    ) -> bool:
        """
        Download and install Python SDK using pip.
        
        See SDKManager.install_python_sdk() for full documentation.
        
        Example:
            >>> org.install_python_sdk(version='1.0.0')
        """
        return self._get_sdk_manager().install_python_sdk(
            sdk_uuid=sdk_uuid,
            version=version,
            upgrade=upgrade
        )

    def get_sdk_installation_instructions(
        self,
        language: str,
        sdk_uuid: str = None,
        version: str = None
    ) -> str:
        """
        Get installation instructions for SDK.
        
        See SDKManager.get_installation_instructions() for full documentation.
        
        Example:
            >>> instructions = org.get_sdk_installation_instructions('python')
            >>> print(instructions)
        """
        return self._get_sdk_manager().get_installation_instructions(
            language=language,
            sdk_uuid=sdk_uuid,
            version=version
        )

    # ============================================================================
    # HIGH-LEVEL SDK CONVENIENCE METHODS (Add to Supero class)
    # ============================================================================

    def install_sdk(
        self,
        languages: Optional[List[str]] = None,
        force_rebuild: bool = False,
        upgrade: bool = True,
        timeout: int = 600  # 10 minutes default
    ) -> str:
        """
        🔥 ULTIMATE CONVENIENCE: Generate, download, and install SDK in one call!
        
        Args:
            languages: SDK languages (default: ['python'])
            force_rebuild: Force rebuild even if cached
            upgrade: Upgrade existing installation
            timeout: Max wait time in seconds
            
        Returns:
            Path to installed SDK
        """
        if languages is None:
            languages = ['python']
        
        self.logger.info(f"🚀 Installing SDK for {', '.join(languages)}...")
        
        try:
            # Step 1: Generate SDK (async)
            self.logger.info("Step 1/3: Generating SDK...")
            result = self.generate_sdk(
                language=languages[0],
                include_schemas=None,
                exclude_schemas=None,
                output_format='wheel'
            )
            
            # Check if cached
            status = result.get('status')
            if status == 'completed' and result.get('cached'):
                sdk_uuids = result.get('sdk_uuids', [])
                if sdk_uuids:
                    sdk_uuid = sdk_uuids[0]
                    self.logger.info(f"✅ Using cached SDK: {sdk_uuid}")
                else:
                    raise ValueError("Cached SDK but no SDK UUIDs returned")
            else:
                # Build queued - poll for completion
                request_id = result.get('request_id')
                if not request_id:
                    raise ValueError("SDK generation failed - no request ID returned")
                
                self.logger.info(f"⏳ SDK build queued (request: {request_id[:8]}...)")
                
                # Poll for completion
                sdk_uuid = self._poll_sdk_build(request_id, timeout)
            
            # Step 2: Download SDK
            self.logger.info(f"Step 2/3: Downloading SDK {sdk_uuid}...")
            sdk_path = self.download_sdk(
                sdk_uuid=sdk_uuid,
                output_path=None
            )
            
            # Step 3: Install SDK
            self.logger.info("Step 3/3: Installing SDK...")
            success = self.install_python_sdk(
                sdk_uuid=sdk_uuid,
                upgrade=upgrade
            )
            
            if success:
                self.logger.info(f"✅ SDK installed successfully: {sdk_path}")
                return sdk_path
            else:
                raise RuntimeError(f"Failed to install SDK from {sdk_path}")
        
        except Exception as e:
            self.logger.error(f"Failed to install SDK: {e}")
            raise

    def _poll_sdk_build(
        self,
        request_id: str,
        timeout: int = 600,
        poll_interval: int = 5
    ) -> str:
        """
        Poll SDK build status until completion.
        
        Args:
            request_id: Build request ID
            timeout: Max wait time in seconds
            poll_interval: Seconds between polls
            
        Returns:
            SDK UUID
        """
        import time
        
        start_time = time.time()
        last_progress = -1
        
        while time.time() - start_time < timeout:
            # Get status
            status_result = self._get_sdk_manager().get_sdk_status(request_id)
            
            status = status_result.get('status')
            progress = status_result.get('progress_percentage', 0)
            current_step = status_result.get('current_step', 'Processing')
            
            # Show progress if changed
            if progress != last_progress:
                self.logger.info(f"   Progress: {progress}% - {current_step}")
                last_progress = progress
            
            # Check completion
            if status == 'completed':
                generated_uuids = status_result.get('generated_sdk_uuids', [])
                
                # Handle string-encoded JSON (same as e2e client)
                if isinstance(generated_uuids, str):
                    import json
                    try:
                        generated_uuids = json.loads(generated_uuids)
                    except (json.JSONDecodeError, ValueError):
                        self.logger.warning(f"Could not parse generated_sdk_uuids: {generated_uuids}")
                        generated_uuids = []
                
                if not generated_uuids:
                    raise RuntimeError("SDK build completed but no UUIDs returned")
                
                sdk_uuid = generated_uuids[0]
                self.logger.info(f"✅ SDK build completed: {sdk_uuid}")
                return sdk_uuid
            
            elif status == 'failed':
                error = status_result.get('error_details', {})
                raise RuntimeError(f"SDK build failed: {error}")
            
            # Wait before next poll
            time.sleep(poll_interval)
        
        # Timeout
        raise TimeoutError(f"SDK build timeout after {timeout}s")


    def refresh_sdk(
        self,
        languages: Optional[List[str]] = None,
        reload: Optional[bool] = None
    ) -> str:
        """
        Regenerate and reinstall SDK (useful after schema changes).

        Auto-detects environment:
        - Jupyter/IPython: Attempts to reload schemas automatically
        - Scripts/Production: Warns to restart application

        Args:
            languages: Languages to regenerate (default: ['python'])
            reload: Force reload behavior (auto-detects if None)

        Returns:
            Path to installed SDK file

        Example:
            >>> org.upload_schema('new_schema.json')
            >>> org.refresh_sdk()  # Rebuild with new schema
            >>> # In Jupyter: schemas reload automatically
            >>> # In scripts: restart required
        """
        # Auto-detect interactive environment if not specified
        if reload is None:
            reload = self._is_interactive()

        self.logger.info("🔄 Refreshing SDK...")

        try:
            # Regenerate and install with force_rebuild=True
            sdk_path = self.install_sdk(
                languages=languages,
                force_rebuild=True
            )

            # Handle reload based on environment
            if reload:
                try:
                    self._reload_schema_classes()
                    self.logger.info("✅ SDK refreshed and schemas reloaded!")
                    self.logger.info("💡 New schemas are now available in your current session.")
                except Exception as e:
                    self.logger.warning(
                        f"⚠️  SDK refreshed but auto-reload failed: {e}"
                    )
                    self.logger.warning(
                        "💡 Restart your Python session to use new schemas."
                    )
            else:
                self.logger.warning(
                    "⚠️  SDK refreshed. Restart your application to use new schemas."
                )

            return sdk_path

        except Exception as e:
            self.logger.error(f"Failed to refresh SDK: {e}")
            raise


    def setup(
        self,
        schemas_dir: Optional[str] = 'schemas/',
        install_sdk: bool = True,
        languages: Optional[List[str]] = None
    ) -> bool:
        """
        🔥 COMPLETE SETUP: Upload schemas + install SDK in one call!

        The ultimate convenience method for initial setup.

        Args:
            schemas_dir: Directory containing schema files (default: 'schemas/')
            install_sdk: Install SDK after uploading (default: True)
            languages: SDK languages (default: ['python'])

        Returns:
            True if successful

        Example:
            >>> org = Supero.quickstart('acme-corp', jwt_token='...')
            >>> org.setup('my_schemas/')
            >>> # Everything is ready! Start building!
            >>> project = org.Project.create(name='My Project')
        """
        self.logger.info("🚀 Running complete setup...")

        try:
            # Step 1: Upload schemas
            self.logger.info(f"Step 1/2: Uploading schemas from {schemas_dir}...")
            result = self.upload_schemas(
                directory=schemas_dir,
                recursive=True
            )

            uploaded = (
            result.get('objects', []) +
            result.get('types', []) +
            result.get('enums', []) +
            result.get('operational', [])
        )
            self.logger.info(f"✅ Uploaded {len(uploaded)} schemas")

            # Step 2: Install SDK
            if install_sdk:
                self.logger.info("Step 2/2: Installing SDK...")
                self.install_sdk(languages=languages)
                self.logger.info("✅ SDK installed")

            self.logger.info("🎉 Setup complete! Ready to build!")
            return True

        except Exception as e:
            self.logger.error(f"Setup failed: {e}")
            raise


    def _is_interactive(self) -> bool:
        """
        Detect if running in interactive environment (Jupyter/IPython).

        Returns:
            True if in Jupyter/IPython, False otherwise
        """
        try:
            # Check for IPython/Jupyter
            get_ipython()
            return True
        except NameError:
            # Check for interactive Python shell
            import sys
            return hasattr(sys, 'ps1')


    def _reload_schema_classes(self):
        """
        Dynamically reload schema classes (for Jupyter/interactive environments).

        Note: This is experimental and may not work in all cases.
        Production applications should restart instead.
        """
        import sys
        import importlib

        # Find all loaded schema modules
        schema_modules = [
            name for name in sys.modules.keys()
            if name.startswith(f'{self.package_namespace}.')
        ]

        # Reload each module
        for module_name in schema_modules:
            try:
                module = sys.modules[module_name]
                importlib.reload(module)
                self.logger.debug(f"Reloaded module: {module_name}")
            except Exception as e:
                self.logger.debug(f"Could not reload {module_name}: {e}")

        # Clear schema cache
        self._schema_cache.clear()

        # Refresh schema list
        try:
            self.refresh_schemas()
        except Exception as e:
            self.logger.debug(f"Could not refresh schemas: {e}")


    # ============================================================================
    # SIMPLIFIED ALIASES (Add to Supero class)
    # ============================================================================

    def list_schemas(
        self,
        schema_type: str = None,
        status: str = 'active'
    ) -> List[Dict[str, Any]]:
        """
        List schemas in this domain (simplified alias).

        Alias for list_schemas_info() with cleaner name.

        Args:
            schema_type: Filter by type ('object', 'type', 'enum', 'operational')
            status: Filter by status (default: 'active')

        Returns:
            List of schema information dictionaries

        Example:
            >>> schemas = org.list_schemas()
            >>> objects = org.list_schemas(schema_type='object')
        """
        return self.list_schemas_info(schema_type=schema_type, status=status)


    def get_schema_details(
        self,
        filename: str
    ) -> Dict[str, Any]:
        """
        Get schema definition and metadata (simplified alias).

        Alias for get_schema_info() with clearer name.

        Args:
            filename: Schema filename (without .json)

        Returns:
            Schema definition and metadata

        Example:
            >>> schema = org.get_schema_details('project')
            >>> print(schema['schema_type'])
        """
        return self.get_schema_info(filename)

    @classmethod
    def system(cls, api_key: str = None, **kwargs) -> 'Supero':
        """
        Convenience method for system/admin operations.
        
        Args:
            api_key: Admin API key (optional for testing)
            **kwargs: Additional ApiLib parameters
            
        Returns:
            Supero instance connected to default-domain with pymodel_system
            
        Example:
            >>> admin = Supero.system(api_key="ak_admin_...")
            >>> new_domain = admin.domain.create_domain("new-tenant")
            >>> api_keys = admin.domain.api_keys()
            
            >>> # Testing mode (no auth)
            >>> admin = Supero.system()
        """
        return cls.connect(
            domain_name="default-domain",
            api_key=api_key,
            package_namespace="pymodel_system",
            use_proxy=False,  # System always uses direct mode
            **kwargs
        )
    
    def _ensure_domain(self, api_key: str = None):
        """
        Load existing domain.

        SDK should NEVER create domains - use tenant registration flow instead!

        Args:
            api_key: Optional API key for RBAC (overrides instance default)

        ✅ ADDED: Per-call api_key support for RBAC (v2.1)
        """
        try:
            if self._jwt_token:
                # Extract domain_uuid from JWT if needed, or skip verification
                self.logger.debug("Skipping domain verification - JWT already validated")
                return


            # ✅ RBAC: Pass api_key through to ApiLib
            self._domain_obj = self._api_lib._object_read(
                'domain',
                fq_name=[self.domain_name],
                domain_name=self.domain_name,
                api_key=api_key
            )

            if self._domain_obj:
                self._domain_uuid = getattr(self._domain_obj, 'uuid', None)
                self.logger.info(f"Connected to existing domain: {self.domain_name}")
                return
            else:
                raise ValueError(
                    f"Domain '{self.domain_name}' not found. "
                    f"Domains must be created via tenant registration flow. "
                    f"Use Platform Core /api/v1/tenant/register endpoint."
                )
        except Exception as e:
            self.logger.error(f"Failed to load domain '{self.domain_name}': {e}")
            raise ValueError(
                f"Domain '{self.domain_name}' not found or inaccessible. "
                f"Ensure domain exists via tenant registration before connecting."
            )

    def _wrap_domain(self):
        """
        Wrap domain object to add dynamic create_* methods.
        
        UPDATED: Now uses _PARENT_TYPE class attributes instead of schema_metadata.
        
        For each child type (where _PARENT_TYPE = "domain"):
        - Add create_<child_type>() method (if no collision)
        - Add <child_type>s() query method (if no collision)
        """
        if not self._domain_obj:
            self.logger.warning("no domain object to wrap")
            return
        
        domain_obj_type = "domain"
        
        child_schemas = self._get_children_of_type(domain_obj_type)
        
        if not child_schemas:
            self.logger.debug(f"No children found for parent type: {domain_obj_type}")
            return
        
        self.logger.debug(
            f"Injecting methods for {len(child_schemas)} children of {domain_obj_type}: "
            f"{', '.join(child_schemas)}"
        )
        
        # Inject methods for child schemas
        self._domain = self._domain_obj
        self._inject_child_methods(self._domain, child_schemas)
    
    def _get_children_of_type(self, parent_obj_type: str) -> List[str]:
        """
        Get all schema names that have the given parent type.
        
        Uses _PARENT_TYPE class attribute from generated classes.
        
        Args:
            parent_obj_type: Parent obj_type (e.g., "domain", "project")
        
        Returns:
            List of child schema names (e.g., ["Project", "User"])
        """
        children = []
        
        # Get all available schemas
        all_schemas = self._list_schemas()
        
        for schema_name in all_schemas:
            try:
                # Load the schema class
                schema_class = self.get_schema(schema_name)
                
                # ✅ Check if _PARENT_TYPE matches
                schema_parent_type = getattr(schema_class, '_PARENT_TYPE', None)
                
                if schema_parent_type == parent_obj_type:
                    children.append(schema_name)
                    self.logger.debug(
                        f"Found child: {schema_name} (parent_type={schema_parent_type})"
                    )
                    
            except Exception as e:
                self.logger.debug(f"Could not check parent for {schema_name}: {e}")
                continue
        
        return children
    
    def _inject_child_methods(self, parent_obj, child_schemas: List[str]):
        """
        Inject create_* and query methods for child schemas.
        
        UPDATED: Simplified to use child_schemas list directly.
        
        Args:
            parent_obj: Parent object to inject methods into
            child_schemas: List of child schema names
        """
        # Reserved method names that should not be overridden
        RESERVED = {'get', 'save', 'delete', 'update', 'create', 'find', 'all', 
                   'refresh', 'to_dict', 'from_dict'}
        
        for child_name in child_schemas:
            try:
                self._add_child_methods(parent_obj, child_name, RESERVED)
            except Exception as e:
                self.logger.warning(f"Failed to add methods for {child_name}: {e}")
    
    def _inject_child_methods_auto(self, parent_obj):
        """
        Auto-inject child methods for a parent object.
        
        Uses _OBJ_TYPE from parent to find children.
        """
        if not hasattr(parent_obj, '__class__'):
            return
        
        # ✅ Get parent's obj_type
        parent_obj_type = getattr(parent_obj.__class__, '_OBJ_TYPE', None)
        if not parent_obj_type:
            return
        
        # Find children and inject methods
        child_schemas = self._get_children_of_type(parent_obj_type)
        if child_schemas:
            self._inject_child_methods(parent_obj, child_schemas)

    def _add_child_methods(self, parent_obj, child_schema_name: str, reserved_methods: set):
        """
        Add complete CRUD methods for child objects.
        
        Methods injected:
        - {child}_create(name, **kwargs)           → Create single child
        - {child}_list(limit, offset, **filters)   → List children
        - {child}_find(**filters)                  → Find with filters
        - {child}_count(**filters)                 → Count children
        - {child}_delete(uuid)                     → Delete by UUID
        - {child}_delete_all(**filters)            → Bulk delete

        ✅ ADDED: All methods accept api_key parameter for RBAC (v2.1)
        """
        
        # Convert schema name to method names
        child_snake = normalize_schema_name(child_schema_name)
        
        # Define all method names
        create_method_name = f"{child_snake}_create"
        list_method_name = f"{child_snake}_list"
        find_method_name = f"{child_snake}_find"
        count_method_name = f"{child_snake}_count"
        delete_method_name = f"{child_snake}_delete"           # ← NEW!
        delete_all_method_name = f"{child_snake}_delete_all"   # ← NEW!
        
        # Check for collisions
        collision_checks = {
            create_method_name: "create",
            list_method_name: "list",
            find_method_name: "find",
            count_method_name: "count",
            delete_method_name: "delete",
            delete_all_method_name: "delete_all"
        }
        
        methods_to_inject = {}
        
        for method_name, operation in collision_checks.items():
            if method_name not in reserved_methods and not hasattr(parent_obj, method_name):
                methods_to_inject[method_name] = operation
            else:
                self.logger.warning(
                    f"Skipping '{method_name}' for schema '{child_schema_name}' - "
                    f"method already exists"
                )
        
        # Load child schema class
        try:
            ChildClass = self.get_schema(child_schema_name)
        except Exception as e:
            self.logger.debug(f"Could not load schema {child_schema_name}: {e}")
            return
        
        # Get obj_type from class attribute
        child_obj_type = getattr(ChildClass, '_OBJ_TYPE', None)
        if not child_obj_type:
            self.logger.warning(
                f"Schema {child_schema_name} missing _OBJ_TYPE attribute"
            )
            return
        
        self.logger.debug(
            f"Adding methods for {child_schema_name}: "
            f"create, list, find, count, delete, delete_all"
        )
        
        # ========================================================================
        # METHOD 1: {child}_create()
        # ✅ RBAC: Added api_key parameter
        # ========================================================================
        def make_create_method(Child, parent):
            def child_create(name: str, api_key: str = None, **kwargs):
                """
                Create a new child object with this instance as parent.

                Args:
                    name: Name for the child object
                    api_key: Optional API key for RBAC (overrides instance default)
                    **kwargs: Additional attributes

                Returns:
                    Created child instance
                """
                child_obj = Child(name=name, **kwargs)
                child_obj.set_parent(parent)
                # ✅ RBAC: Pass api_key through
                saved_obj = self.save(child_obj, api_key=api_key)
                if saved_obj and hasattr(saved_obj, '__class__'):
                    self._inject_child_methods_auto(saved_obj)
                return saved_obj
            
            child_create.__doc__ = (
                f"Create a new {child_schema_name} as child of this object.\n\n"
                f"Args:\n"
                f"    name: Name for the {child_schema_name}\n"
                f"    api_key: Optional API key for RBAC (overrides instance default)\n"
                f"    **kwargs: Additional attributes\n\n"
                f"Returns:\n"
                f"    Created {child_schema_name} instance\n\n"
                f"Example:\n"
                f"    child = parent.{child_snake}_create(name='example')\n"
                f"    child = parent.{child_snake}_create(name='example', api_key=user_key)"
            )
            return child_create
        
        # ========================================================================
        # METHOD 2: {child}_list()
        # ✅ RBAC: Added api_key parameter
        # ========================================================================
        def make_list_method(Child, child_name, child_type, parent):
            def child_list(limit=100, offset=0, api_key: str = None, **filters):
                """
                List child objects belonging to this parent.

                Args:
                    limit: Max results (default: 100)
                    offset: Pagination offset (default: 0)
                    api_key: Optional API key for RBAC (overrides instance default)
                    **filters: Filter conditions

                Returns:
                    List of child instances
                """
                try:
                    # ✅ RBAC: Pass api_key through to ApiLib
                    all_objects = self._api_lib._objects_list(
                        child_type,
                        detail=True,
                        domain_name=self.domain_name,
                        api_key=api_key
                    )
                except Exception as e:
                    self.logger.error(f"Failed to list {child_type}: {e}")
                    return []
                
                # Filter by parent UUID
                parent_uuid = getattr(parent, 'uuid', None)
                if parent_uuid:
                    objects = [
                        obj for obj in all_objects
                        if getattr(obj, 'parent_uuid', None) == parent_uuid
                    ]
                else:
                    objects = all_objects
                
                # Apply additional filters
                if filters:
                    objects = [
                        obj for obj in objects
                        if self._matches_filters(obj, filters)
                    ]
                
                # Apply pagination
                if offset > 0:
                    objects = objects[offset:]
                if limit > 0:
                    objects = objects[:limit]
                
                # Inject child methods
                for obj in objects:
                    if hasattr(obj, '__class__'):
                        self._inject_child_methods_auto(obj)
                
                return objects
            
            child_list.__doc__ = (
                f"List {child_schema_name} children of this object.\n\n"
                f"Args:\n"
                f"    limit: Max results (default: 100)\n"
                f"    offset: Pagination offset (default: 0)\n"
                f"    api_key: Optional API key for RBAC (overrides instance default)\n"
                f"    **filters: Filter conditions\n\n"
                f"Returns:\n"
                f"    List of {child_schema_name} instances"
            )
            return child_list
        
        # ========================================================================
        # METHOD 3: {child}_find()
        # ✅ RBAC: Added api_key parameter
        # ========================================================================
        def make_find_method(child_name, child_snake):
            def child_find(api_key: str = None, **filters):
                """
                Find child objects matching filters.

                Args:
                    api_key: Optional API key for RBAC (overrides instance default)
                    **filters: Filter conditions

                Returns:
                    List of matching instances
                """
                list_method = getattr(parent_obj, f"{child_snake}_list", None)
                if list_method:
                    # ✅ RBAC: Pass api_key through
                    return list_method(api_key=api_key, **filters)
                return []
            
            child_find.__doc__ = (
                f"Find {child_schema_name} children matching filters.\n\n"
                f"Args:\n"
                f"    api_key: Optional API key for RBAC (overrides instance default)\n"
                f"    **filters: Filter conditions\n\n"
                f"Returns:\n"
                f"    List of matching {child_schema_name} instances"
            )
            return child_find
        
        # ========================================================================
        # METHOD 4: {child}_count()
        # ✅ RBAC: Added api_key parameter
        # ========================================================================
        def make_count_method(child_name, child_snake):
            def child_count(api_key: str = None, **filters):
                """
                Count child objects, optionally with filters.

                Args:
                    api_key: Optional API key for RBAC (overrides instance default)
                    **filters: Optional filter conditions

                Returns:
                    int: Number of matching children
                """
                list_method = getattr(parent_obj, f"{child_snake}_list", None)
                if list_method:
                    # ✅ RBAC: Pass api_key through
                    results = list_method(api_key=api_key, **filters)
                    return len(results) if results else 0
                return 0
            
            child_count.__doc__ = (
                f"Count {child_schema_name} children.\n\n"
                f"Args:\n"
                f"    api_key: Optional API key for RBAC (overrides instance default)\n"
                f"    **filters: Optional filter conditions\n\n"
                f"Returns:\n"
                f"    int: Number of matching children"
            )
            return child_count
        
        # ========================================================================
        # METHOD 5: {child}_delete() - DELETE BY UUID
        # ✅ RBAC: Added api_key parameter
        # ========================================================================
        def make_delete_method(child_type, child_name, child_snake):
            def child_delete(uuid: str, api_key: str = None):
                """
                Delete a specific child object by UUID.
                
                Args:
                    uuid: UUID of the child object to delete
                    api_key: Optional API key for RBAC (overrides instance default)
                    
                Returns:
                    bool: True if deletion succeeded
                    
                Example:
                    project = org.Project.get(uuid)
                    project.user_account_delete(user_uuid)
                    project.user_account_delete(user_uuid, api_key=admin_key)
                """
                if not uuid:
                    raise ValueError("UUID is required for deletion")
                
                try:
                    # ✅ RBAC: Pass api_key through to ApiLib
                    self._api_lib._object_delete(
                        child_type,
                        id=uuid,
                        domain_name=self.domain_name,
                        api_key=api_key
                    )
                    return True
                except Exception as e:
                    self.logger.error(f"Failed to delete {child_name} {uuid}: {e}")
                    return False
            
            child_delete.__doc__ = (
                f"Delete a specific {child_schema_name} child by UUID.\n\n"
                f"Args:\n"
                f"    uuid: UUID of the {child_schema_name} to delete\n"
                f"    api_key: Optional API key for RBAC (overrides instance default)\n\n"
                f"Returns:\n"
                f"    bool: True if deletion succeeded\n\n"
                f"Example:\n"
                f"    parent.{child_snake}_delete(child_uuid)\n"
                f"    parent.{child_snake}_delete(child_uuid, api_key=admin_key)"
            )
            return child_delete
        
        # ========================================================================
        # METHOD 6: {child}_delete_all() - BULK DELETE WITH FILTERS
        # ✅ RBAC: Added api_key parameter
        # ========================================================================
        def make_delete_all_method(child_type, child_name, child_snake):
            def child_delete_all(api_key: str = None, **filters):
                """
                Delete all child objects matching filters.
                
                Args:
                    api_key: Optional API key for RBAC (overrides instance default)
                    **filters: Filter conditions (REQUIRED for safety)
                    
                Returns:
                    int: Number of objects deleted
                    
                Example:
                    project = org.Project.get(uuid)
                    
                    # Delete with filters (safe)
                    deleted = project.user_account_delete_all(status="inactive")
                    
                    # Delete all children (dangerous - requires confirmation)
                    deleted = project.user_account_delete_all(confirm=True)
                """
                # Safety check - require either filters or explicit confirmation
                if not filters:
                    raise ValueError(
                        f"Safety check: {child_snake}_delete_all() requires filters or confirm=True. "
                        f"To delete all children without filters, use: "
                        f"{child_snake}_delete_all(confirm=True)"
                    )
                
                # Check for confirmation flag
                confirm = filters.pop('confirm', False)
                
                # If no filters and no confirmation, raise error
                if not filters and not confirm:
                    raise ValueError(
                        f"Safety check: To delete all {child_name} without filters, "
                        f"use {child_snake}_delete_all(confirm=True)"
                    )
                
                # Get matching children
                list_method = getattr(parent_obj, f"{child_snake}_list", None)
                if not list_method:
                    return 0
                
                # ✅ RBAC: Pass api_key through
                children = list_method(api_key=api_key, **filters)
                
                if not children:
                    return 0
                
                # Delete each child
                deleted_count = 0
                for child in children:
                    child_uuid = getattr(child, 'uuid', None)
                    if child_uuid:
                        try:
                            # ✅ RBAC: Pass api_key through to ApiLib
                            self._api_lib._object_delete(
                                child_type,
                                id=child_uuid,
                                domain_name=self.domain_name,
                                api_key=api_key
                            )
                            deleted_count += 1
                        except Exception as e:
                            self.logger.error(
                                f"Failed to delete {child_name} {child_uuid}: {e}"
                            )
                
                return deleted_count
            
            child_delete_all.__doc__ = (
                f"Delete all {child_schema_name} children matching filters.\n\n"
                f"Safety: Requires filters or confirm=True to prevent accidental mass deletion.\n\n"
                f"Args:\n"
                f"    api_key: Optional API key for RBAC (overrides instance default)\n"
                f"    **filters: Filter conditions or confirm=True\n\n"
                f"Returns:\n"
                f"    int: Number of objects deleted\n\n"
                f"Examples:\n"
                f"    # Delete with filters (safe)\n"
                f"    deleted = parent.{child_snake}_delete_all(status='inactive')\n\n"
                f"    # Delete all children (requires confirmation)\n"
                f"    deleted = parent.{child_snake}_delete_all(confirm=True)\n\n"
                f"    # With RBAC override\n"
                f"    deleted = parent.{child_snake}_delete_all(status='inactive', api_key=admin_key)"
            )
            return child_delete_all
        
        # ========================================================================
        # INJECT ALL METHODS
        # ========================================================================
        
        # Inject create
        if create_method_name in methods_to_inject:
            setattr(parent_obj, create_method_name,
                    make_create_method(ChildClass, parent_obj))
            self.logger.debug(f"✓ Added method: {create_method_name}")
        
        # Inject list
        if list_method_name in methods_to_inject:
            setattr(parent_obj, list_method_name,
                    make_list_method(ChildClass, child_schema_name, child_obj_type, parent_obj))
            self.logger.debug(f"✓ Added method: {list_method_name}")
        
        # Inject find
        if find_method_name in methods_to_inject and list_method_name in methods_to_inject:
            setattr(parent_obj, find_method_name,
                    make_find_method(child_schema_name, child_snake))
            self.logger.debug(f"✓ Added method: {find_method_name}")
        
        # Inject count
        if count_method_name in methods_to_inject and list_method_name in methods_to_inject:
            setattr(parent_obj, count_method_name,
                    make_count_method(child_schema_name, child_snake))
            self.logger.debug(f"✓ Added method: {count_method_name}")
        
        # Inject delete (single)
        if delete_method_name in methods_to_inject:
            setattr(parent_obj, delete_method_name,
                    make_delete_method(child_obj_type, child_schema_name, child_snake))
            self.logger.debug(f"✓ Added method: {delete_method_name}")
        
        # Inject delete_all (bulk)
        if delete_all_method_name in methods_to_inject and list_method_name in methods_to_inject:
            setattr(parent_obj, delete_all_method_name,
                    make_delete_all_method(child_obj_type, child_schema_name, child_snake))
            self.logger.debug(f"✓ Added method: {delete_all_method_name}")

    
    def _list_schemas(self) -> List[str]:
        """
        Get all available schema names across all packages.

        Returns schema names (e.g., ['Project', 'Task', 'ApiKey'])
        """

        schema_names = set()

        # Source 1: Get from ApiLib's loaded object types
        if self.api_lib and hasattr(self.api_lib, 'object_types'):
            for obj_type in self.api_lib.object_types.keys():
                schema_names.add(obj_type)

            self.logger.debug(
                f"get_all_schemas: Found {len(self.api_lib.object_types)} "
                f"schemas from ApiLib"
            )

        # Source 2: Scan filesystem for additional schemas
        packages_to_scan = list(self._schema_namespaces)

        for package_name in packages_to_scan:
            for submodule in ['objects', 'types', 'enums', 'operational']:
                try:
                    module = importlib.import_module(f"{package_name}.{submodule}")
                    module_path = os.path.dirname(module.__file__)

                    for filename in os.listdir(module_path):
                        if filename.endswith('.py') and not filename.startswith('_'):
                            class_name = ''.join(
                                word.capitalize()
                                for word in filename[:-3].split('_')
                            )
                            schema_names.add(class_name)

                except (ImportError, AttributeError, FileNotFoundError):
                    continue

        return sorted(list(schema_names))

    
    def _extract_schemas_from_module(self, module) -> set:
        """
        Extract schema class names from a module.
        
        Identifies schemas by checking for:
        - from_dict classmethod
        - to_dict instance method
        - _type_metadata class attribute
        
        Args:
            module: Python module to scan
            
        Returns:
            Set of schema class names found in the module
        """
        schemas = set()
        
        for name, obj in inspect.getmembers(module):
            # Skip private attributes
            if name.startswith('_'):
                continue
            
            # Must be a class
            if not inspect.isclass(obj):
                continue
            
            # Must be defined in this module (not imported)
            if obj.__module__ != module.__name__:
                continue
            
            # Check if it's a schema class by looking for required methods/attributes
            has_from_dict = hasattr(obj, 'from_dict') and callable(getattr(obj, 'from_dict'))
            has_to_dict = hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict'))
            has_metadata = hasattr(obj, '_type_metadata')
            
            if has_from_dict and has_to_dict and has_metadata:
                schemas.add(name)
        
        return schemas
    
    def refresh_schemas(self) -> List[str]:
        """
        Force refresh of schema discovery.
        
        Useful when schemas are added/removed dynamically.
        
        Returns:
            Updated list of schema names
        """
        # Clear the cache
        cache_key = f'_schema_list_{self.package_namespace}'
        if hasattr(self, cache_key):
            delattr(self, cache_key)
        
        # Clear loaded schema cache too
        self._schema_cache.clear()
        
        return self._list_schemas()
    
    def get_schema(self, schema_name: str) -> Type:
        """
        Get existing schema class with Supero context.
        
        Args:
            schema_name: Name of generated schema class (e.g., "Project", "UserAccount")
        
        Returns:
            Class with Supero context attached
        
        Example:
            >>> Project = org.get_schema("Project")
            >>> project = Project.create(name="Alpha", parent=org.domain)
        """
        # Check cache
        schema_name = normalize_schema_name(schema_name)

        if schema_name in self._schema_cache:
            return self._schema_cache[schema_name]
        
        # Load from generated code
        obj_class = self._load_existing_schema(schema_name)
        
        # Attach context
        obj_class._supero_context = self
        self._schema_cache[schema_name] = obj_class
        
        self.logger.debug(f"Loaded schema: {schema_name}")
        return obj_class
    
    def _load_existing_schema(self, schema_name: str) -> Type:
        """
        Load schema class from generated package code.

        Tries both primary namespace (e.g., pymodel) and alternate namespace (pymodel_system).

        FIXED: Uses normalize_schema_name() and snake_case alias.
        """
        # ✅ Use consistent normalization for file name
        normalized_name = normalize_schema_name(schema_name)

        # ✅ Use snake_case alias for class name (generated at end of file)
        class_name = normalized_name

        self.logger.debug(
            f"Loading schema: '{schema_name}' → "
            f"file: '{normalized_name}.py', class: '{class_name}' (snake_case alias)"
        )

        self.logger.debug(
            f"  file: '{normalized_name}.py', class: '{class_name}' (snake_case alias)"
        )

        packages_to_try = list(self._schema_namespaces) 

        for package_name in packages_to_try:
            for submodule in ['objects', 'types', 'enums', 'operational']:
                module_name = f"{package_name}.{submodule}.{normalized_name}"

                try:
                    module = importlib.import_module(module_name)

                    # Check if class exists in module
                    if hasattr(module, class_name):
                        self.logger.debug(
                            f"✓ Found schema in {module_name}.{class_name}"
                        )
                        return module
                    else:
                        self.logger.debug(
                            f"  Module {module_name} exists but no '{class_name}' class"
                        )
                except ImportError as e:
                    self.logger.debug(
                        f"  Could not import {module_name}: {e}"
                    )
                    continue

        self.logger.warning(
            f"Schema '{schema_name}' not found in any package: {packages_to_try}"
        )
        return None
    
    def validate_parent_child_relationship(self, child_obj, parent_obj) -> bool:
        """
        Validate that a parent-child relationship is valid.
        
        FIXED: Uses _OBJ_TYPE and _PARENT_TYPE class attributes.
        
        Args:
            child_obj: Child object instance
            parent_obj: Parent object instance
            
        Returns:
            True if relationship is valid
            
        Raises:
            ValueError: If relationship is invalid
        """
        # ✅ Get child's obj_type and expected parent type from class attributes
        child_obj_type = getattr(child_obj.__class__, '_OBJ_TYPE', None)
        expected_parent_type = getattr(child_obj.__class__, '_PARENT_TYPE', None)
        
        if not child_obj_type:
            raise ValueError(
                f"Child object missing _OBJ_TYPE class attribute. "
                f"Class: {child_obj.__class__.__name__}"
            )
        
        if not expected_parent_type:
            raise ValueError(
                f"Child object missing _PARENT_TYPE class attribute. "
                f"Class: {child_obj.__class__.__name__}"
            )
        
        # ✅ Get actual parent's obj_type from instance or class
        if hasattr(parent_obj, 'obj_type'):
            actual_parent_type = parent_obj.obj_type
        else:
            actual_parent_type = getattr(parent_obj.__class__, '_OBJ_TYPE', None)
            if not actual_parent_type:
                raise ValueError(
                    f"Parent object missing obj_type attribute and _OBJ_TYPE class attribute. "
                    f"Class: {parent_obj.__class__.__name__}"
                )
        
        # Validate
        if expected_parent_type != actual_parent_type:
            raise ValueError(
                f"Invalid parent-child relationship: "
                f"Schema '{child_obj_type}' expects parent type '{expected_parent_type}', "
                f"but got '{actual_parent_type}'"
            )
        
        self.logger.debug(
            f"✓ Valid relationship: {child_obj_type} → {actual_parent_type}"
        )
        return True
    
    def discover_schema_hierarchy(self) -> Dict[str, Any]:
        """
        Discover and return the complete schema hierarchy.
        
        UPDATED: Builds hierarchy from _PARENT_TYPE class attributes.
        
        Returns:
            Dictionary with hierarchy information
        """
        hierarchy = {}
        
        # Get all schemas
        all_schemas = self._list_schemas()
        
        for schema_name in all_schemas:
            try:
                schema_class = self.get_schema(schema_name)
                obj_type = getattr(schema_class, '_OBJ_TYPE', None)
                parent_type = getattr(schema_class, '_PARENT_TYPE', None)
                
                if obj_type:
                    if obj_type not in hierarchy:
                        hierarchy[obj_type] = {
                            'name': schema_name,
                            'obj_type': obj_type,
                            'parent_type': parent_type,
                            'children': []
                        }
                    
                    # Add to parent's children list
                    if parent_type and parent_type in hierarchy:
                        hierarchy[parent_type]['children'].append(obj_type)
                        
            except Exception as e:
                self.logger.debug(f"Could not process {schema_name}: {e}")
                continue
        
        return hierarchy
    
    def save(self, obj: Any, validate=None, api_key: str = None) -> Any:
        """
        Save object (create or update) with optional validation.

        Args:
            obj: Object instance to save
            validate: If None, auto-detect (strict for creates, lenient for updates)
                     If True, always validate
                     If False, never validate
            api_key: Optional API key for RBAC (overrides instance default)

        Returns:
            Saved object with updated fields and child methods injected

        Raises:
            ValueError: If mandatory fields are missing (when validate=True)

        ✅ ADDED: Per-call api_key support for RBAC (v2.1)
        """
        obj_type = getattr(obj, 'obj_type', None)
        if not obj_type:
            raise ValueError("Object must have obj_type attribute")

        # Auto-detect validation mode
        if validate is None:
            # Strict for new objects (no UUID), lenient for updates (has UUID)
            is_create = not (hasattr(obj, 'uuid') and obj.uuid)
            validate = is_create

        # Validate if requested
        if validate and hasattr(obj, 'validate_mandatory_fields'):
            validation_result = obj.validate_mandatory_fields()

            if not validation_result['valid']:
                missing = validation_result['missing_fields']
                error_msg = (
                    f"Cannot save {obj_type}: Missing mandatory fields: {', '.join(missing)}.\n\n"
                    f"Provide these fields when creating the object."
                )
                raise ValueError(error_msg)

        # Check if object has UUID (update) or not (create)
        if hasattr(obj, 'uuid') and obj.uuid:
            # Update - ✅ RBAC: Pass api_key through
            self._api_lib._object_update(
                obj_type, obj, 
                domain_name=self.domain_name,
                api_key=api_key
            )
            saved_obj = self._api_lib._object_read(
                obj_type, id=obj.uuid, 
                domain_name=self.domain_name,
                api_key=api_key
            )
        else:
            # Create - ✅ RBAC: Pass api_key through
            uuid = self._api_lib._object_create(
                obj_type, obj, 
                domain_name=self.domain_name,
                api_key=api_key
            )
            if uuid:
                saved_obj = self._api_lib._object_read(
                    obj_type, id=uuid, 
                    domain_name=self.domain_name,
                    api_key=api_key
                )
            else:
                return None

        # Inject child methods on saved object
        if saved_obj and hasattr(saved_obj, '__class__'):
            self._inject_child_methods_auto(saved_obj)

        return saved_obj

    def delete(self, obj: Any, api_key: str = None) -> bool:
        """
        Delete object.
        
        Args:
            obj: Object instance to delete
            api_key: Optional API key for RBAC (overrides instance default)
            
        Returns:
            True if successful

        ✅ ADDED: Per-call api_key support for RBAC (v2.1)
        """
        obj_type = getattr(obj, 'obj_type', None)
        if not obj_type:
            raise ValueError("Object must have obj_type attribute")
        
        if not hasattr(obj, 'uuid') or not obj.uuid:
            raise ValueError("Object must have UUID to delete")
        
        # ✅ RBAC: Pass api_key through to ApiLib
        self._api_lib._object_delete(
            obj_type, id=obj.uuid, 
            domain_name=self.domain_name,
            api_key=api_key
        )
        return True
    
    
    def refresh(self, obj: Any, api_key: str = None) -> Any:
        """
        Reload object from server.

        Args:
            obj: Object instance to refresh
            api_key: Optional API key for RBAC (overrides instance default)

        Returns:
            Refreshed object with child methods injected

        ✅ ADDED: Per-call api_key support for RBAC (v2.1)
        """
        obj_type = getattr(obj, 'obj_type', None)
        if not obj_type or not obj.uuid:
            raise ValueError("Object must have obj_type and uuid")

        # ✅ RBAC: Pass api_key through to ApiLib
        refreshed_obj = self._api_lib._object_read(
            obj_type, id=obj.uuid, 
            domain_name=self.domain_name,
            api_key=api_key
        )

        # Inject child methods on refreshed object
        if refreshed_obj and hasattr(refreshed_obj, '__class__'):
            self._inject_child_methods_auto(refreshed_obj)

        return refreshed_obj

    def _matches_filters(self, obj: Any, filters: Dict[str, Any]) -> bool:
        """Check if object matches filter conditions."""
        for key, value in filters.items():
            if not hasattr(obj, key):
                return False
            obj_value = getattr(obj, key)
            if obj_value != value:
                return False
        return True
    
    @property
    def domain(self):
        """
        Get wrapped domain object with create_* methods.
        
        Returns:
            Domain object with dynamic create_<child>() methods
        """
        return getattr(self, '_domain_obj', None)  # ← Use _domain_obj!

    @domain.setter
    def domain(self, value):
        """Set the domain context."""
        if value is None:
            self._domain_obj = None
            self._domain = None  # ✅ Keep in sync
            return

        if isinstance(value, str):
            # Try to fetch domain
            try:
                domain_obj = self.get('Domain', value)
                self._domain_obj = domain_obj
                self._domain = self._domain_obj  # ✅ Keep in sync
            except Exception as e:
                self._domain_obj = None
                self._domain = None
        else:
            # Domain object provided
            self._domain_obj = value
            self._domain = self._domain_obj  # ✅ Keep in sync
    
    @property
    def domain_uuid(self):
        """Get domain UUID."""
        return self.__domain_uuid or getattr(self._domain, 'uuid', None)
    
    @property
    def api_lib(self) -> ApiLib:
        """Access underlying ApiLib for advanced operations."""
        return self._api_lib


# ============================================================================
# Convenience Functions
# ============================================================================

def quickstart(name: str, package_namespace: str = None, **kwargs):
    """Convenience function for Supero.quickstart()"""
    return Supero.quickstart(name, package_namespace=package_namespace, **kwargs)


def connect(domain_name: str, api_key: str = None, package_namespace: str = None, **kwargs):
    """Convenience function for Supero.connect()"""
    return Supero.connect(domain_name, api_key=api_key,
                           package_namespace=package_namespace, **kwargs)
