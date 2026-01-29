"""
Enhanced ApiLib implementation with proxy mode support and domain-aware operations.

Provides high-level API for interacting with the platform's API server,
with support for both direct mode (internal use) and proxy mode (external tenant apps).

Version 2.1 - Per-Call API Key Support for RBAC:
- All operations accept optional api_key parameter
- Per-call api_key overrides instance default for RBAC enforcement
- Enables user-specific operations with user's API key
- Maintains backward compatibility (api_key parameter is optional)

Version 2.0 - Domain-Aware Architecture:
- All operations require domain_name parameter
- Platform registry objects automatically use 'default-domain'
- Tenant objects use authenticated user's domain

Args:
    ...
    api_key: API key for direct mode authentication (default key)
    use_proxy: If True, use platform-core proxy instead of direct API server
    proxy_prefix: Proxy endpoint prefix (default: /api/v1/crud)
    jwt_token: JWT token for proxy mode authentication
    default_domain: Default domain for operations (default: 'default-domain')

Examples:
    # Direct mode with default API key (platform-core internal use)
    api_lib = ApiLib(
        api_server_host='localhost',
        api_server_port='8082',
        api_key='ak_admin_prod_xxx',  # Default/fallback key
        default_domain='default-domain'
    )
    
    # Per-call API key for RBAC enforcement
    user_api_key = session_manager.get_api_key(session_id)
    schema = api_lib.schema_registry_read(
        uuid='abc123',
        domain_name='acme-corp',
        api_key=user_api_key  # User's key for RBAC
    )

    # Proxy mode (external tenant apps)
    api_lib = ApiLib(
        api_server_host='platform-core.acme.com',
        api_server_port='8083',
        use_proxy=True,
        jwt_token='eyJhbGciOiJIUzI1NiIs...',
        default_domain='acme-corp'
    )
"""

import logging
import functools
import importlib
import pkgutil
import inflection
import time
import threading
from typing import Dict, List, Any, Optional, Union
import pprint

from .api_client import ApiClient
from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    EncryptionRequiredError,
    NoIdError
)

import json
from .api_logger import initialize_logger 
from .extensions import ExtensionManager, ApiLibExtension

# Import everything from centralized config
from ._runtime_config import (
    BUILD_MODE,
    PRIMARY_SCHEMA_NAMESPACE,
    SCHEMA_NAMESPACES,
    BUILD_TENANT,
    TENANT_NAMESPACE,
    get_build_info,
    is_platform,
    SerializationError,
    ObjectSerializationError,
    ObjectDeserializationError,
    JSONSerializationError,
    JSONDeserializationError,
    safe_serialize_to_dict,
    safe_serialize_to_json,
    safe_deserialize_from_dict,
    safe_deserialize_from_json,
)

# Platform registry objects that ALWAYS use 'default-domain'
PLATFORM_REGISTRY_OBJECTS = {'audit_log', 'global_system_config'}

def to_dasherize(obj_type):
    '''
    inflection.underscore('UserAccount')  # → 'user_account'
    inflection.underscore('APIKey')       # → 'api_key'
    inflection.dasherize('user_account')  # → 'user-account'
    inflection.dasherize('api_key')       # → 'api-key'
    '''
    return inflection.dasherize(inflection.underscore(obj_type))

def to_underscore(obj_type):
    '''
    inflection.underscore('UserAccount')  # → 'user_account'
    inflection.underscore('APIKey')       # → 'api_key'
    '''
    return inflection.underscore(obj_type)


class ApiLib(object):
    """
    Build-aware ApiLib with optional API key authentication support and domain-aware operations.
    Automatically discovers schemas based on build configuration.
    
    Version 2.1 Features:
    - Per-call api_key parameter for RBAC enforcement
    - All CRUD methods accept optional api_key to override instance default
    - Enables user-specific operations in multi-tenant environments
    
    Version 2.0 Features:
    - Domain-aware URL routing (domain in path, not query)
    - Automatic platform object detection (always use 'default-domain')
    - Configurable default domain for operations
    """

    def __init__(self, username=None, password=None, tenant_name=None,
                 api_server_host='127.0.0.1', api_server_port='8082',
                 api_server_url=None, conf_file=None, user_info=None,
                 auth_token=None, auth_host=None, auth_port=None,
                 auth_protocol=None, auth_url=None, auth_type=None,
                 wait_for_connect=False, timeout=30, max_retries=3,
                 extensions=None, enable_encryption=False,
                 encryption_key=None, domain_name=None, api_key=None,
                 use_proxy: bool = False,
                 proxy_prefix: str = '/api/v1/crud',
                 jwt_token: str = None,
                 default_domain: str = 'default-domain'):

        """
        Initialize ApiLib with optional proxy mode and domain-aware operations.
        Schema discovery is based on build configuration (platform vs tenant).

        Args:
            username: Username for authentication (legacy)
            password: Password for authentication (legacy)
            tenant_name: Tenant name
            api_server_host: API server hostname/IP (or platform-core if use_proxy=True)
            api_server_port: API server port (or platform-core port if use_proxy=True)
            api_server_url: Full API server URL (overrides host/port)
            conf_file: Configuration file path
            user_info: User information dictionary
            auth_token: Authentication token (legacy)
            auth_host: Auth server host (legacy)
            auth_port: Auth server port (legacy)
            auth_protocol: Auth protocol (legacy)
            auth_url: Auth server URL (legacy)
            auth_type: Authentication type (legacy)
            wait_for_connect: Wait for server connection on init
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            extensions: List of extensions to load
            enable_encryption: Enable field-level encryption
            encryption_key: Encryption key (required if enable_encryption=True)
            domain_name: Domain name for encryption (legacy, use default_domain)
            api_key: API key for direct mode authentication (default/fallback key)
            use_proxy: If True, use platform-core proxy instead of direct API server
            proxy_prefix: Proxy endpoint prefix (default: /api/v1/crud)
            jwt_token: JWT token for proxy mode authentication
            default_domain: Default domain for operations (default: 'default-domain')

        Raises:
            ValueError: If authentication configuration is invalid

        Examples:
            # Direct mode with default API key (platform-core internal use)
            api_lib = ApiLib(
                api_server_host='localhost',
                api_server_port='8082',
                api_key='ak_admin_prod_xxx',  # Default key
                default_domain='default-domain'
            )
            
            # Per-call API key usage for RBAC
            user_key = get_user_api_key(session_id)
            api_lib.project_read(uuid='...', api_key=user_key)

            # Proxy mode (external tenant apps)
            api_lib = ApiLib(
                api_server_host='platform-core.acme.com',
                api_server_port='8083',
                use_proxy=True,
                jwt_token='eyJhbGciOiJIUzI1NiIs...',
                default_domain='acme-corp'
            )
        """

        self.logger = initialize_logger("py-api-lib")
        self._api_key = api_key
        self._jwt_token = jwt_token
        self._use_proxy = use_proxy
        self._default_domain = default_domain  # Store default domain
        
        # VALIDATE AUTH CONFIG - Fail fast on invalid combinations
        self._validate_auth_config(api_key, jwt_token, use_proxy)

        # Build awareness - load from build config
        try:
            from ._build_config import (
                BUILD_MODE,
                PRIMARY_SCHEMA_NAMESPACE,
                SCHEMA_NAMESPACES,
                BUILD_TENANT,
                get_build_info
            )
            self.build_mode = BUILD_MODE
            self.primary_namespace = PRIMARY_SCHEMA_NAMESPACE
            self.expected_namespaces = SCHEMA_NAMESPACES
            self.build_tenant = BUILD_TENANT
            self._build_info_func = get_build_info
        except ImportError:
            # Fallback for development mode
            self.build_mode = 'platform'
            self.primary_namespace = 'pymodel_system'
            self.expected_namespaces = ['pymodel_system']
            self.build_tenant = 'system'
            self._build_info_func = lambda: {
                'mode': 'platform',
                'primary_namespace': 'pymodel_system',
                'tenant': 'system'
            }
            self.logger.warning(
                "Build config not found, using default (platform mode). "
                "Run build.sh to generate proper configuration."
            )

        # Lazy-loaded schema objects and serialization helpers
        self._object_types = None
        self._serialization_helpers = None
        self._schema_namespaces = None
        self.domain_name = domain_name or 'default-domain'

        # Parse API server URL if provided
        if api_server_url:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(api_server_url)
                api_server_host = parsed.hostname or api_server_host
                api_server_port = parsed.port or api_server_port
            except Exception as e:
                self.logger.warning(f"Failed to parse api_server_url: {e}")

        # Initialize API client with build awareness
        try:
            self.api_client = ApiClient(
                server_ip=api_server_host,
                port=int(api_server_port),
                timeout=timeout,
                max_retries=max_retries,
                api_key=api_key,
                use_proxy=use_proxy,
                proxy_prefix=proxy_prefix,
                jwt_token=jwt_token,
                domain_name=self.domain_name,
                default_domain=self._default_domain
            )
            mode = "PROXY" if use_proxy else "DIRECT"
            if use_proxy and jwt_token:
                auth_type = "JWT"
            elif api_key:
                auth_type = "API-KEY"
            else:
                auth_type = "NONE"

            self.logger.info(
                f"ApiLib initialized in {mode} mode "
                f"(auth={auth_type}, "
                f"server={api_server_host}:{api_server_port}, "
                f"build={self.build_mode}, "
                f"namespace={self.primary_namespace}, "
                f"default_domain={self._default_domain})"
            )
        except Exception as e:
            self.logger.error(f"Failed to create ApiClient: {e}")
            raise

        # Store legacy auth token if provided
        if auth_token:
            self._auth_token = auth_token

        # Encryption setup
        self.enable_encryption = enable_encryption
        self.encryption_manager = None

        if enable_encryption:
            try:
                from crypto_utils import EncryptionManager
                if encryption_key:
                    self.encryption_manager = EncryptionManager(encryption_key)
                    self.logger.info(
                        f"Field-level encryption ENABLED for domain: {domain_name or 'default'}"
                    )
                else:
                    raise ValueError("encryption_key is required when enable_encryption=True")
            except ImportError as e:
                self.logger.error(f"Failed to import encryption module: {e}")
                raise ImportError("Encryption module not available")

        # Load object types based on build configuration
        self.object_types = self._load_object_types()

        # Initialize module cache
        self._module_cache = {}

        # Create dynamic methods for discovered object types
        self._create_dynamic_methods()

        # Initialize extension manager
        self._extension_manager = ExtensionManager(self)

        # Load extensions if provided
        if extensions:
            try:
                self._extension_manager.load_extensions(extensions)
            except Exception as e:
                self.logger.error(f"Failed to load extensions: {e}")

        # Wait for server connection if requested
        if wait_for_connect:
            self._wait_for_connection()

        # Log summary of what was discovered
        self.logger.info(
            f"ApiLib ready: {len(self.object_types)} object types discovered "
            f"from {len(self._discover_schema_namespaces())} namespace(s)"
        )

    def _validate_auth_config(self, api_key: Optional[str], jwt_token: Optional[str], 
                             use_proxy: bool) -> None:
        """
        Validate authentication configuration - fail fast on invalid combinations.
        
        Args:
            api_key: API key for direct mode
            jwt_token: JWT token for proxy mode
            use_proxy: Whether proxy mode is enabled
            
        Raises:
            ValueError: If configuration is invalid
        """
        # 1. Can't provide both authentication methods
        if api_key and jwt_token:
            raise ValueError(
                "Cannot provide both api_key and jwt_token. "
                "Choose one:\n"
                "  - For direct mode (API server): use api_key only\n"
                "  - For proxy mode (platform-core): use jwt_token only"
            )
        
        # 2. Proxy mode requires jwt_token, not api_key
        if use_proxy and api_key and not jwt_token:
            raise ValueError(
                "Proxy mode requires jwt_token, not api_key.\n"
                "Fix:\n"
                "  - Change api_key='...' to jwt_token='...'\n"
                "  - Or set use_proxy=False for direct mode"
            )
        
        # 3. Direct mode should use api_key, not jwt_token
        if not use_proxy and jwt_token and not api_key:
            raise ValueError(
                "Direct mode should use api_key, not jwt_token.\n"
                "Fix:\n"
                "  - Change jwt_token='...' to api_key='...'\n"
                "  - Or set use_proxy=True for proxy mode"
            )
        
        # 4. Proxy mode without authentication (warning, not error)
        if use_proxy and not jwt_token and not api_key:
            self.logger.warning(
                "Proxy mode enabled without authentication. "
                "Requests will likely fail unless platform-core allows unauthenticated access."
            )

    def _resolve_domain_name(self, obj_type: str, domain_name: Optional[str] = None) -> str:
        """
        Resolve domain name based on object type and hierarchy.
        
        Platform registry objects (domain, audit_log) ALWAYS use 'default-domain'.
        Other objects use provided domain_name or fall back to default_domain.
        
        Args:
            obj_type: Object type (e.g., 'project', 'domain', 'api_key')
            domain_name: Explicitly provided domain name (optional)
            
        Returns:
            Resolved domain name
            
        Examples:
            >>> _resolve_domain_name('domain', 'acme-corp')
            'default-domain'  # Platform object always uses default-domain
            
            >>> _resolve_domain_name('project', 'acme-corp')
            'acme-corp'  # Tenant object uses provided domain
            
            >>> _resolve_domain_name('project', None)
            'default-domain'  # Falls back to default_domain
        """
        # Normalize obj_type to underscore format
        normalized_type = obj_type.replace('-', '_').lower()
        
        # Platform registry objects ALWAYS use 'default-domain'
        if normalized_type in PLATFORM_REGISTRY_OBJECTS:
            if domain_name and domain_name != 'default-domain':
                self.logger.debug(
                    f"Platform object '{obj_type}' requested with domain '{domain_name}', "
                    f"overriding to 'default-domain'"
                )
            return 'default-domain'
        
        # For other objects, use provided domain_name or fall back to default
        resolved = domain_name or self._default_domain
        self.logger.debug(f"Resolved domain for '{obj_type}': {resolved}")
        return resolved

    def _resolve_api_key(self, api_key: Optional[str] = None) -> Optional[str]:
        """
        Resolve API key for a request.
        
        Per-call api_key takes precedence over instance default.
        This enables RBAC by allowing user-specific API keys per request.
        
        Args:
            api_key: Per-call API key override (optional)
            
        Returns:
            Effective API key (per-call or instance default)
            
        Examples:
            >>> _resolve_api_key('ak_user_key')
            'ak_user_key'  # Per-call key takes precedence
            
            >>> _resolve_api_key(None)
            'ak_admin_key'  # Falls back to instance default
        """
        effective_key = api_key if api_key is not None else self._api_key
        
        if api_key and api_key != self._api_key:
            # Log when using per-call override (for debugging RBAC issues)
            self.logger.debug(
                f"Using per-call API key override: {api_key[:20] if api_key else 'None'}..."
            )
        
        return effective_key

    def set_default_domain(self, domain_name: str):
        """
        Set the default domain for operations.
        
        Args:
            domain_name: Domain name to use as default
        """
        self._default_domain = domain_name
        if hasattr(self, 'api_client'):
            self.api_client.set_default_domain(domain_name)
        self.logger.info(f"Default domain updated to: {domain_name}")

    def get_default_domain(self) -> str:
        """Get the current default domain."""
        return self._default_domain

    def _discover_schema_namespaces(self):
        """
        Discover available schema namespaces based on build configuration.
        Respects the priority order defined at build time.
        
        Returns:
            list: Available namespace modules in priority order
        """
        # Return cached namespaces if already discovered
        if self._schema_namespaces is not None:
            return self._schema_namespaces
        
        namespaces = []
        
        # Try namespaces dynamically (not hardcoded)
        for namespace_name in self.expected_namespaces:
            try:
                # Dynamic import - works with any namespace name!
                objects_module = importlib.import_module(f"{namespace_name}.objects")
                namespaces.append((namespace_name, objects_module))
                
                # Log what type of namespace this is
                if namespace_name == 'pymodel_system':
                    self.logger.info(f"✓ Loaded {namespace_name} (system schemas)")
                elif namespace_name.startswith('pymodel_'):
                    self.logger.info(f"✓ Loaded {namespace_name} (tenant schemas)")
                else:
                    self.logger.info(f"✓ Loaded {namespace_name}")
                    
            except ImportError as e:
                self.logger.warning(
                    f"Expected namespace '{namespace_name}' not available: {e}. "
                    f"This may indicate a build configuration mismatch."
                )
        
        if not namespaces:
            self.logger.error(
                f"CRITICAL: No schema namespaces found! "
                f"Expected: {self.expected_namespaces}. "
                f"Build mode: {self.build_mode}. "
                f"ApiLib will not function properly without schemas."
            )
        else:
            loaded = [name for name, _ in namespaces]
            self.logger.info(
                f"Schema namespaces loaded: {loaded} "
                f"(expected: {self.expected_namespaces}, "
                f"priority: {self.primary_namespace} first)"
            )
        
        self._schema_namespaces = namespaces
        return namespaces

    def _load_object_types(self):
        """
        Discover object types from available namespaces in priority order.

        Platform builds: Only pymodel_system objects
        Tenant builds: pymodel objects first, pymodel_system as fallback

        Returns:
            dict: Mapping of object type names to their classes
        """
        # Return cached object types if already loaded
        if self._object_types is not None:
            return self._object_types

        object_types = {}
        namespaces = self._discover_schema_namespaces()

        if not namespaces:
            self.logger.error("No schema namespaces available - cannot load object types")
            return object_types

        # Load object types from each namespace in priority order
        for namespace_name, namespace_module in namespaces:
            namespace_count = 0

            for name in dir(namespace_module):
                # Skip private attributes
                if name.startswith('_'):
                    continue

                try:
                    obj = getattr(namespace_module, name)

                    # Check if it's a valid object class
                    if hasattr(obj, '__init__') and callable(obj):
                        # First namespace wins (respects priority order)
                        if name not in object_types:
                            object_types[name] = obj
                            namespace_count += 1
                            self.logger.debug(f"Registered: {name} from {namespace_name}")
                        else:
                            # Already loaded from higher priority namespace
                            self.logger.debug(
                                f"Skipped: {name} from {namespace_name} "
                                f"(already loaded from higher priority namespace)"
                            )

                except Exception as e:
                    self.logger.debug(f"Skipping {name} from {namespace_name}: {e}")

            self.logger.info(
                f"Loaded {namespace_count} object types from {namespace_name}"
            )

        total_types = len(object_types)
        if total_types == 0:
            self.logger.error(
                "No object types discovered! Check schema packages are properly installed."
            )
        else:
            self.logger.info(
                f"Total: {total_types} object types from {len(namespaces)} namespace(s)"
            )

        self._object_types = object_types
        return object_types

    def _get_serialization_helpers(self):
        """
        Load serialization helpers from correct namespace based on build config.
        Returns:
            dict: Serialization helper functions
        """
        import importlib
        
        # Return cached helpers if already loaded
        if self._serialization_helpers is not None:
            return self._serialization_helpers
        # Try namespaces in priority order (dynamically)
        for namespace_name in self.expected_namespaces:
            try:
                # ✅ FIXED: Dynamic import - works with any namespace!
                module = importlib.import_module(f"{namespace_name}.serialization_errors")
                
                # Extract all required attributes
                SerializationError = getattr(module, 'SerializationError')
                ObjectSerializationError = getattr(module, 'ObjectSerializationError')
                ObjectDeserializationError = getattr(module, 'ObjectDeserializationError')
                JSONSerializationError = getattr(module, 'JSONSerializationError')
                JSONDeserializationError = getattr(module, 'JSONDeserializationError')
                safe_serialize_to_dict = getattr(module, 'safe_serialize_to_dict')
                safe_serialize_to_json = getattr(module, 'safe_serialize_to_json')
                safe_deserialize_from_dict = getattr(module, 'safe_deserialize_from_dict')
                safe_deserialize_from_json = getattr(module, 'safe_deserialize_from_json')
                
                # Determine source description for logging
                if namespace_name == 'pymodel_system':
                    source = f'{namespace_name} (system schemas)'
                elif namespace_name.startswith('pymodel_'):
                    source = f'{namespace_name} (tenant schemas)'
                else:
                    source = namespace_name
                # Successfully loaded
                self._serialization_helpers = {
                    'SerializationError': SerializationError,
                    'ObjectSerializationError': ObjectSerializationError,
                    'ObjectDeserializationError': ObjectDeserializationError,
                    'JSONSerializationError': JSONSerializationError,
                    'JSONDeserializationError': JSONDeserializationError,
                    'safe_serialize_to_dict': safe_serialize_to_dict,
                    'safe_serialize_to_json': safe_serialize_to_json,
                    'safe_deserialize_from_dict': safe_deserialize_from_dict,
                    'safe_deserialize_from_json': safe_deserialize_from_json,
                }
                self.logger.info(f"✓ Loaded serialization helpers from {source}")
                return self._serialization_helpers
            except (ImportError, AttributeError) as e:
                self.logger.debug(
                    f"Could not load serialization from {namespace_name}: {e}"
                )
        # Fallback: basic serialization
        self.logger.warning(
            f"No serialization helpers found in {self.expected_namespaces}. "
            f"Using basic JSON serialization."
        )
        self._serialization_helpers = {
            'SerializationError': Exception,
            'ObjectSerializationError': Exception,
            'ObjectDeserializationError': Exception,
            'JSONSerializationError': Exception,
            'JSONDeserializationError': Exception,
            'safe_serialize_to_dict': lambda obj: obj.__dict__ if hasattr(obj, '__dict__') else obj,
            'safe_serialize_to_json': lambda obj: json.dumps(obj.__dict__ if hasattr(obj, '__dict__') else obj, default=str),
            'safe_deserialize_from_dict': lambda cls, data: cls(**data) if callable(cls) else data,
            'safe_deserialize_from_json': lambda cls, json_str: cls(**json.loads(json_str)) if callable(cls) else json.loads(json_str),
        }
        return self._serialization_helpers

    def get_build_info(self):
        """
        Get comprehensive build configuration information.

        Returns:
            dict: Build information including mode, namespaces, object counts, etc.
        """
        namespaces = self._discover_schema_namespaces()

        return {
            'build_mode': self.build_mode,
            'build_tenant': self.build_tenant,
            'primary_namespace': self.primary_namespace,
            'expected_namespaces': self.expected_namespaces,
            'loaded_namespaces': [name for name, _ in namespaces],
            'object_types_count': len(self.object_types),
            'serialization_loaded': self._serialization_helpers is not None,
            'encryption_enabled': self.enable_encryption,
            'api_key_auth': self._api_key is not None,
            'default_domain': self._default_domain,
            **self._build_info_func()
        }

    def get_available_schemas(self):
        """ 
        Get information about available schema packages.
            
        Returns:
            dict: Schema availability status
        """
        namespaces = self._discover_schema_namespaces()
        loaded_names = [name for name, _ in namespaces]
        
        # ✅ FIXED: Dynamic namespace detection
        result = {
            'namespaces_loaded': loaded_names,
            'object_types_count': len(self.object_types),
            'build_mode': self.build_mode,
            'primary_namespace': self.primary_namespace,
            'tenant_namespace': getattr(self, 'tenant_namespace', None),
            'expected_namespaces': self.expected_namespaces,
        }
        
        # Add availability flags for each expected namespace
        for ns in self.expected_namespaces:
            result[f'{ns}_available'] = ns in loaded_names
        
        # Backward compatibility: check for system namespace
        result['pymodel_system'] = 'pymodel_system' in loaded_names
        
        # Check if tenant namespace is loaded (could be any pymodel_* name)
        result['tenant_schemas_loaded'] = any(
            name.startswith('pymodel_') and name != 'pymodel_system' 
            for name in loaded_names
        )
        
        return result

    def set_api_key(self, api_key: str):
        """Set or update the default API key at runtime."""
        self._api_key = api_key
        if hasattr(self, 'api_client'):
            self.api_client.set_api_key(api_key)
        self.logger.info("API key updated")
    
    
    def get_api_key(self) -> Optional[str]:
        """Get the current default API key (returns prefix only for security)."""
        if not self._api_key:
            return None
        parts = self._api_key.split('_')
        # Handle new 5-part format (ak_domain_project_env_suffix)
        if len(parts) >= 5:
            return f"{parts[0]}_{parts[1]}_{parts[2]}_{parts[3]}_***"
        # Fallback for old 4-part format (ak_domain_env_suffix)
        elif len(parts) >= 4:
            return f"{parts[0]}_{parts[1]}_{parts[2]}_***"
        return "***"

    def clear_api_key(self):
        """Clear the default API key."""
        self._api_key = None
        if hasattr(self, 'api_client'):
            self.api_client.set_api_key(None)
        self.logger.info("API key cleared")
    
    def _contains_encrypted_values(self, obj_data: dict) -> bool:
        if not self.encryption_manager:
            return False
        for key, value in obj_data.items():
            if key in ['_encrypted', '_id', 'uuid', 'obj_type', 'parent_type', 'topic']:
                continue
            if isinstance(value, str) and value.startswith("ENC:"):
                return True
            if isinstance(value, list):
                if any(isinstance(v, str) and v.startswith("ENC:") for v in value):
                    return True
            if isinstance(value, dict):
                if self._contains_encrypted_values(value):
                    return True
        return False
    
    def _list_encrypted_fields(self, obj_data: dict) -> list:
        encrypted_fields = []
        for key, value in obj_data.items():
            if key in ['_encrypted', '_id', 'uuid', 'obj_type']:
                continue
            if isinstance(value, str) and value.startswith("ENC:"):
                encrypted_fields.append(key)
            elif isinstance(value, list):
                if any(isinstance(v, str) and v.startswith("ENC:") for v in value):
                    encrypted_fields.append(key)
        return encrypted_fields
    
    def _encrypt_object_values(self, obj_dict: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enable_encryption or not self.encryption_manager:
            return obj_dict
        try:
            return self.encryption_manager.encrypt_object(obj_dict)
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            raise
    
    def _decrypt_object_values(self, obj_dict: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enable_encryption or not self.encryption_manager:
            return obj_dict
        try:
            return self.encryption_manager.decrypt_object(obj_dict)
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            raise
    
    def load_extension(self, extension: Union[str, type, ApiLibExtension]):
        return self._extension_manager.load_extension(extension)
    
    def unload_extension(self, extension_name: str):
        return self._extension_manager.unload_extension(extension_name)
    
    def reload_extension(self, extension_name: str):
        return self._extension_manager.reload_extension(extension_name)
    
    def get_loaded_extensions(self) -> List[str]:
        return self._extension_manager.get_loaded_extensions()
    
    def has_extension(self, extension_name: str) -> bool:
        return self._extension_manager.has_extension(extension_name)
    
    def get_extension_methods(self) -> Dict[str, str]:
        return self._extension_manager.get_extension_methods()
    
    def list_available_extensions(self) -> List[str]:
        return self._extension_manager.list_available_extensions()
    
    def register_extension_class(self, extension_class: type):
        return self._extension_manager.register_extension_class(extension_class)
    
    def register_extension_package(self, package_name: str):
        return self._extension_manager.register_extension_package(package_name)
    
    def register_extension_by_path(self, module_path: str, class_name: str = None):
        return self._extension_manager.register_extension_by_path(module_path, class_name)
    
    def load_extensions_from_config(self, config):
        return self._extension_manager.load_extensions_from_config(config)

    def _create_dynamic_methods(self):
        """
        Create dynamic CRUD methods for all discovered object types.
        
        For each object type, creates methods like:
        - {type}_create(obj, domain_name=None, api_key=None) 
        - {type}_read(obj_id, domain_name=None, api_key=None)
        - {type}_update(obj_id, obj, domain_name=None, api_key=None)
        - {type}_delete(obj_id, domain_name=None, api_key=None)
        - {type}s_list(filters=None, domain_name=None, api_key=None)
        - {type}_get_default_id(domain_name=None, api_key=None)
        
        All methods accept optional domain_name and api_key parameters.
        """
        for obj_type in self.object_types:
            # Convert PascalCase to snake_case
            # GlobalSystemConfig -> global_system_config
            method_prefix = inflection.underscore(obj_type)
            
            # Create CRUD methods with domain_name and api_key support
            for operation in ('_create', '_read', '_update', '_delete'):
                method_name = f"{method_prefix}{operation}"
                method_func = getattr(self, f'_object{operation}')
                
                # Create wrapper that accepts domain_name and api_key
                def make_wrapper(func, obj_type_arg):
                    @functools.wraps(func)
                    def wrapper(*args, domain_name=None, api_key=None, **kwargs):
                        return func(obj_type_arg, *args, domain_name=domain_name, api_key=api_key, **kwargs)
                    return wrapper
                
                setattr(self, method_name, make_wrapper(method_func, obj_type))
            
            # Create list method (plural) with domain_name and api_key support
            list_method_name = f"{method_prefix}s_list"
            list_method_func = getattr(self, '_objects_list')
            
            def make_list_wrapper(func, obj_type_arg):
                @functools.wraps(func)
                def wrapper(*args, domain_name=None, api_key=None, **kwargs):
                    return func(obj_type_arg, *args, domain_name=domain_name, api_key=api_key, **kwargs)
                return wrapper
            
            setattr(self, list_method_name, make_list_wrapper(list_method_func, obj_type))
            
            # Create get_default_id method with domain_name and api_key support
            default_id_method_name = f"{method_prefix}_get_default_id"
            default_id_method_func = getattr(self, '_object_get_default_id')
            
            def make_default_id_wrapper(func, obj_type_arg):
                @functools.wraps(func)
                def wrapper(domain_name=None, api_key=None):
                    return func(obj_type_arg, domain_name=domain_name, api_key=api_key)
                return wrapper
            
            setattr(self, default_id_method_name, make_default_id_wrapper(default_id_method_func, obj_type))
        
        self.logger.info(f"Created dynamic methods for {len(self.object_types)} object types")

    def _wait_for_connection(self, max_wait: int = 60):
        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                if self.api_client.health_check():
                    self.logger.info("Successfully connected to API server")
                    return True
            except Exception:
                pass
            time.sleep(2)
        self.logger.warning(f"Failed to connect to API server within {max_wait} seconds")
        return False
    
    @classmethod
    def from_config(cls, config_file: str = None, **kwargs) -> 'ApiLib':
        import os
        config = {
            'api_server_host': '127.0.0.1',
            'api_server_port': '8082',
            'timeout': 30,
            'max_retries': 3,
            'enable_encryption': False,
            'encryption_key': None,
            'domain_name': None,
            'api_key': None,
            # Proxy defaults
            'use_proxy': False,
            'proxy_prefix': '/api/v1/crud',
            'jwt_token': None,
            # Domain defaults
            'default_domain': 'default-domain'
        }

        if config_file and os.path.exists(config_file):
            try:
                import yaml
                with open(config_file, 'r') as f:
                    if config_file.endswith('.json'):
                        file_config = json.load(f)
                    else:
                        file_config = yaml.safe_load(f)
                    config.update(file_config.get('api_lib', {}))

                    # Load encryption config
                    if 'encryption' in file_config:
                        enc_config = file_config['encryption']
                        config['enable_encryption'] = enc_config.get('enabled', False)
                        if 'key' in enc_config:
                            import base64
                            config['encryption_key'] = base64.b64decode(enc_config['key'])
                        config['domain_name'] = enc_config.get('domain')

                    # Load proxy config
                    if 'proxy' in file_config:
                        proxy_config = file_config['proxy']
                        config['use_proxy'] = proxy_config.get('enabled', False)
                        config['proxy_prefix'] = proxy_config.get('prefix', '/api/v1/crud')
                    
                    # Load domain config
                    if 'domain' in file_config:
                        domain_config = file_config['domain']
                        config['default_domain'] = domain_config.get('default', 'default-domain')

            except Exception as e:
                print(f"Warning: Could not load config from {config_file}: {e}")

        # Environment variable mappings
        env_mappings = {
            'API_SERVER_HOST': 'api_server_host',
            'API_SERVER_PORT': 'api_server_port',
            'API_SERVER_TIMEOUT': 'timeout',
            'API_SERVER_MAX_RETRIES': 'max_retries',
            'ENCRYPTION_ENABLED': 'enable_encryption',
            'ENCRYPTION_KEY': 'encryption_key',
            'DOMAIN_NAME': 'domain_name',
            'API_KEY': 'api_key',
            # Proxy environment variables
            'USE_PROXY': 'use_proxy',
            'PROXY_PREFIX': 'proxy_prefix',
            'JWT_TOKEN': 'jwt_token',
            # Domain environment variables
            'DEFAULT_DOMAIN': 'default_domain'
        }

        for env_var, config_key in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                # Handle boolean values
                if config_key in ['enable_encryption', 'use_proxy']:
                    config[config_key] = env_value.lower() == 'true'
                elif config_key == 'encryption_key':
                    import base64
                    config[config_key] = base64.b64decode(env_value)
                elif config_key in ['timeout', 'max_retries']:
                    try:
                        config[config_key] = int(env_value)
                    except ValueError:
                        pass
                else:
                    config[config_key] = env_value

        config.update(kwargs)
        return cls(**config)

    @classmethod  
    def get_default_instance(cls) -> 'ApiLib':
        if not hasattr(cls, '_default_instance'):
            cls._default_instance = cls.from_config()
        return cls._default_instance
    
    @classmethod
    def reset_default_instance(cls):
        if hasattr(cls, '_default_instance'):
            try:
                cls._default_instance.close()
            except:
                pass
            delattr(cls, '_default_instance')

    def _object_create(self, res_type: str, obj, 
                       domain_name: Optional[str] = None,
                       api_key: Optional[str] = None) -> str:
        """
        Create object with domain-aware routing and per-call API key support.
        
        Args:
            res_type: Resource type
            obj: Object instance to create
            domain_name: Domain name (optional, resolved automatically)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            Object UUID
        """
        try:
            # Resolve domain name and API key
            resolved_domain = self._resolve_domain_name(res_type, domain_name)
            effective_key = self._resolve_api_key(api_key)
            
            name = getattr(obj, 'name', None)
            if not name:
                raise ValueError("Object must have a 'name' attribute")
            
            fq_name = getattr(obj, 'fq_name', None)
            parent_type = getattr(obj, 'parent_type', None)
            if not fq_name:
                if parent_type in ['config-root', 'config_root']:
                    obj.fq_name = [name]
                    obj.parent_type = "config-root"
                    obj.parent_uuid = ""
                else:
                    self.logger.error(f"object create failed: {res_type} '{name}', fq_name is not set")
                    raise
            
            if not hasattr(obj, 'uuid') or not obj.uuid:
                import uuid as uuid_module
                obj.uuid = str(uuid_module.uuid4())
            
            payload = safe_serialize_to_dict(obj, res_type)
            
            if self.enable_encryption:
                payload = self._encrypt_object_values(payload)
                payload['_encrypted'] = True
            else:
                payload['_encrypted'] = False
            
            # Pass domain_name and api_key to ApiClient
            result = self.api_client._http_create(
                to_dasherize(res_type),
                payload,
                domain_name=resolved_domain,
                api_key=effective_key
            )
            if not result:
                return None

            normalized_type = to_underscore(res_type)
            obj_data = result.get(normalized_type)
            if not obj_data:
                self.logger.error(f"can't find {res_type} in response, result: {result}, normalized_type: {normalized_type}")
                return None
            if not obj_data.get('uuid'):
                self.logger.error(f"can't get uuid in response, obj_data: {obj_data}")
                return None
                
            uuid = obj_data['uuid']
            obj.uuid = uuid
            
            if hasattr(obj, 'set_server_conn'):
                obj.set_server_conn(self)
            if hasattr(obj, 'clear_pending_updates'):
                obj.clear_pending_updates()

            return uuid
        except Exception as e:
            self.logger.error(f"Error creating {res_type}: {str(e)}", exc_info=True)
            raise
    
    def _object_read(self, res_type: str, fq_name=None, fq_name_str=None, id=None, 
                     uuid=None, fields=None, 
                     domain_name: Optional[str] = None,
                     api_key: Optional[str] = None):
        """
        Read object with domain-aware routing and per-call API key support.
        
        Args:
            res_type: Resource type
            fq_name: Fully qualified name (list)
            fq_name_str: FQ name as string
            id: Object ID/UUID
            uuid: Object UUID
            fields: Fields to retrieve
            domain_name: Domain name (optional, resolved automatically)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            Object instance or None
        """
        try:
            # Resolve domain name and API key
            resolved_domain = self._resolve_domain_name(res_type, domain_name)
            effective_key = self._resolve_api_key(api_key)
            
            if id or uuid:
                obj_uuid = id or uuid
            elif fq_name:
                obj_uuid = self.fq_name_to_uuid(res_type, fq_name, domain_name=resolved_domain, api_key=effective_key)
                if not obj_uuid:
                    return None
            elif fq_name_str:
                obj_uuid = self.fq_name_to_uuid(res_type, fq_name_str, domain_name=resolved_domain, api_key=effective_key)
                if not obj_uuid:
                    return None
            else:
                raise ValueError("Must provide either 'id', 'fq_name', or 'fq_name_str'")
            
            # Pass domain_name and api_key to ApiClient
            result = self.api_client._http_read(
                to_dasherize(res_type),
                obj_uuid,
                domain_name=resolved_domain,
                api_key=effective_key
            )
            if not result:
                return None
                
            normalized_type = to_underscore(res_type)
            obj_data = result.get(normalized_type)
            if not obj_data:
                self.logger.error(f"can't find {res_type} in response, result: {result}, normalized_type: {normalized_type}")
                return None
            
            server_marked_encrypted = obj_data.get('_encrypted', False)
            has_encrypted_values = self._contains_encrypted_values(obj_data)
            
            if (server_marked_encrypted or has_encrypted_values) and not self.enable_encryption:
                raise EncryptionRequiredError(
                    f"Object {res_type}/{obj_uuid} contains encrypted data. "
                    f"Encrypted fields: {self._list_encrypted_fields(obj_data)}"
                )
            
            if self.enable_encryption and has_encrypted_values:
                obj_data = self._decrypt_object_values(obj_data)
            
            obj = self._hydrate_object(res_type, obj_data)
            
            if obj:
                if hasattr(obj, 'clear_pending_updates'):
                    obj.clear_pending_updates()
                if hasattr(obj, 'set_server_conn'):
                    obj.set_server_conn(self)

            return obj
        except EncryptionRequiredError:
            raise
        except (SerializationError, ObjectDeserializationError):
            raise
        except (AuthenticationError, AuthorizationError, RateLimitError):
            raise  # Propagate auth errors
        except Exception as e:
            self.logger.error(f"Error reading {res_type}: {str(e)}", exc_info=True)
            raise
    
    def _object_update(self, res_type: str, obj, 
                       domain_name: Optional[str] = None,
                       api_key: Optional[str] = None) -> str:
        """
        Update object with domain-aware routing and per-call API key support.
        
        Args:
            res_type: Resource type
            obj: Object instance to update
            domain_name: Domain name (optional, resolved automatically)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            Success message
        """
        try:
            # Resolve domain name and API key
            resolved_domain = self._resolve_domain_name(res_type, domain_name)
            effective_key = self._resolve_api_key(api_key)
            
            obj_uuid = getattr(obj, 'uuid', None)
            if not obj_uuid:
                fq_name = getattr(obj, 'fq_name', None) or obj.get_fq_name()
                obj_uuid = self.fq_name_to_uuid(res_type, fq_name, domain_name=resolved_domain, api_key=effective_key)
                if obj_uuid:
                    obj.uuid = obj_uuid
                else:
                    raise ValueError("Object must have UUID or valid fq_name")
            
            payload = safe_serialize_to_dict(obj, res_type)
            
            # ✅ FIXED: Remove immutable fields that cannot be updated
            # These fields are set at creation time and cannot be modified
            immutable_fields = [
                'uuid',
                'name',
                'fq_name',
                'parent_type',
                'parent_uuid',
                'parent_fq_name',
                'id_perms',
                'perms2',
                'href',
                'created_at',
                'created_by',
                'obj_type',
                '_type_metadata',
            ]
            for field in immutable_fields:
                payload.pop(field, None)
            
            if self.enable_encryption:
                payload = self._encrypt_object_values(payload)
                payload['_encrypted'] = True
            else:
                payload['_encrypted'] = False
            
            # Log what we're sending (debug level)
            self.logger.debug(f"Update payload for {res_type}/{obj_uuid}: {list(payload.keys())}")
            
            # Pass domain_name and api_key to ApiClient
            result = self.api_client._http_update(
                to_dasherize(res_type),
                obj_uuid,
                payload,
                domain_name=resolved_domain,
                api_key=effective_key
            )
            if not result:
                raise Exception(f"Update operation failed for {res_type}/{obj_uuid}")
            
            if hasattr(obj, 'clear_pending_updates'):
                obj.clear_pending_updates()
            
            return "Updated successfully"
        except ValueError as e:
            # ✅ IMPROVED: Re-raise ValueError with context (from _http_update 400 errors)
            self.logger.error(f"Error updating {res_type}: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error updating {res_type}: {str(e)}", exc_info=True)
            raise
    
    def _object_delete(self, res_type: str, fq_name=None, id=None, uuid=None,
                       domain_name: Optional[str] = None,
                       api_key: Optional[str] = None) -> None:
        """
        Delete object with domain-aware routing and per-call API key support.
        
        Args:
            res_type: Resource type
            fq_name: Fully qualified name
            id: Object ID/UUID
            uuid: Object UUID
            domain_name: Domain name (optional, resolved automatically)
            api_key: Per-call API key override (optional, uses instance default if not provided)
        """
        try:
            # Resolve domain name and API key
            resolved_domain = self._resolve_domain_name(res_type, domain_name)
            effective_key = self._resolve_api_key(api_key)
            
            if id or uuid:
                obj_uuid = id or uuid
            elif fq_name:
                obj_uuid = self.fq_name_to_uuid(res_type, fq_name, domain_name=resolved_domain, api_key=effective_key)
                if not obj_uuid:
                    raise NoIdError(f"Could not find UUID for {res_type}")
            else:
                raise ValueError("Must provide either 'id' or 'fq_name'")
            
            # Pass domain_name and api_key to ApiClient
            success = self.api_client._http_delete(
                to_dasherize(res_type),
                obj_uuid,
                domain_name=resolved_domain,
                api_key=effective_key
            )
            if not success:
                raise Exception(f"Delete operation failed for {res_type}/{obj_uuid}")
        except Exception as e:
            self.logger.error(f"Error deleting {res_type}: {e}", exc_info=True)
            raise
    
    def _objects_list(self, res_type: str, parent=None, parent_id=None, parent_fq_name=None,
                     obj_uuids=None, back_ref_id=None, fields=None,
                     detail=False, count=False, filters=None,
                     domain_name: Optional[str] = None,
                     api_key: Optional[str] = None) -> List[Any]:
        """
        List objects of given type with domain-aware routing and per-call API key support.
        
        ALWAYS returns list of hydrated objects (never dicts).
        The 'detail' parameter is kept for backward compatibility but ignored.
        
        Args:
            res_type: Object type to list
            parent: Parent object (optional filter)
            parent_id: Parent UUID (optional filter)
            parent_fq_name: Parent FQ name (optional filter)
            obj_uuids: Specific UUIDs to retrieve (optional filter)
            detail: DEPRECATED - always hydrates objects now
            count: If True, return count instead of objects
            filters: Additional filters (optional)
            domain_name: Domain name (optional, resolved automatically)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            List of hydrated object instances (never dicts)
        """
        try:
            # Resolve domain name and API key
            resolved_domain = self._resolve_domain_name(res_type, domain_name)
            effective_key = self._resolve_api_key(api_key)
            
            # Get raw data from API
            if not parent_id:
                if parent:
                    parent_id = parent.uuid
            
            # Pass domain_name and api_key to ApiClient (list operations use plural form)
            raw_objects = self.api_client._http_list(
                to_dasherize(res_type),
                parent_id,
                domain_name=resolved_domain,
                api_key=effective_key
            )
            
            if not isinstance(raw_objects, list):
                self.logger.error(
                    f"Invalid API response for {res_type}: 'objects' is not a list. "
                    f"Type: {type(raw_objects)}"
                )
                return []

            self.logger.debug(f"Found {len(raw_objects)} {res_type} objects from API")
            
            # STEP 1: Validate obj_type in each object
            expected_type = to_underscore(res_type)  # 'api-key' → 'api_key'
            validated_objects = []
            
            for obj_data in raw_objects:
                if not isinstance(obj_data, dict):
                    self.logger.warning(f"Skipping non-dict item in {res_type} list: {type(obj_data)}")
                    continue
                
                self.logger.debug(f"{expected_type} - object dict:\n{pprint.pformat(obj_data, indent=2, width=100)}")

                obj_type = obj_data.get('obj_type')
                if not obj_type:
                    self.logger.warning(
                        f"Object missing 'obj_type' field in {res_type} list "
                        f"(uuid={obj_data.get('uuid', 'unknown')})"
                    )
                    continue
                
                if obj_type != expected_type:
                    self.logger.warning(
                        f"Object type mismatch: expected '{expected_type}', got '{obj_type}' "
                        f"(uuid={obj_data.get('uuid', 'unknown')})"
                    )
                    continue
                
                validated_objects.append(obj_data)
            
            if len(validated_objects) < len(raw_objects):
                self.logger.warning(
                    f"Filtered out {len(raw_objects) - len(validated_objects)} invalid objects "
                    f"from {res_type} list"
                )
            
            raw_objects = validated_objects
            
            # Validate parent parameter consistency
            if parent and parent_id and parent.get_uuid() != parent_id:
                raise Exception(
                    f"Wrong API usage: parent.uuid ({parent.uuid}) != parent_id ({parent_id})"
                )
            if parent and parent_fq_name and parent.get_fq_name() != parent_fq_name:
                raise Exception(
                    f"Wrong API usage: parent.fq_name ({parent.get_fq_name()}) != parent_fq_name ({parent_fq_name})"
                )

            # Extract parent info if parent object provided
            if parent:
                parent_id = parent.get_uuid()
                parent_fq_name = parent.get_fq_name()

            # STEP 2: Filter by parent/uuid if specified
            if parent_id or parent_fq_name or obj_uuids:
                filtered_objects = []
                for obj_data in raw_objects:
                    # Validate it's a dict
                    if not isinstance(obj_data, dict):
                        self.logger.warning(f"Skipping non-dict item in list: {type(obj_data)}")
                        continue
                    
                    # Filter by parent_id
                    if parent_id and obj_data.get('parent_uuid') != parent_id:
                        self.logger.error(f"parent_uuid is not match {obj_data.get('parent_uuid')} != {parent_id}")
                        continue
                    
                    # Filter by parent_fq_name
                    if parent_fq_name:
                        obj_fq_name = obj_data.get('fq_name', [])
                        if len(obj_fq_name) <= len(parent_fq_name):
                            self.logger.error(f" fq_name validaiton failure: {len(obj_fq_name)} <= {len(parent_fq_name)}")
                            continue
                        if obj_fq_name[:len(parent_fq_name)] != parent_fq_name:
                            self.logger.error(f" fq_name validaiton failure: {obj_fq_name[:len(parent_fq_name)]} != {parent_fq_name}")
                            continue
                    
                    # Filter by obj_uuids
                    if obj_uuids and obj_data.get('uuid') not in obj_uuids:
                        continue
                    
                    filtered_objects.append(obj_data)
                
                raw_objects = filtered_objects
            
            if not raw_objects:
                self.logger.error(f"list objects is empty: {parent_id}, {parent_fq_name}")
                return []
            
            # Handle count request
            if count:
                return raw_objects[:count]
            
            # STEP 3: ALWAYS hydrate dicts → objects (regardless of 'detail' parameter)
            objects = []
            skipped_encrypted = []
            hydration_failures = 0
            
            for obj_data in raw_objects:
                try:
                    # Validate obj_data is a dict
                    if not isinstance(obj_data, dict):
                        self.logger.warning(f"Skipping non-dict item: {type(obj_data)}")
                        hydration_failures += 1
                        continue
                    
                    # Check for encryption
                    is_encrypted = (
                        obj_data.get('_encrypted', False) or 
                        self._contains_encrypted_values(obj_data)
                    )
                    
                    if is_encrypted and not self.enable_encryption:
                        skipped_encrypted.append(obj_data.get('uuid', 'unknown'))
                        self.logger.warning(
                            f"Skipping encrypted {res_type} object (uuid={obj_data.get('uuid')}) "
                            f"- encryption not enabled"
                        )
                        continue
                    
                    if is_encrypted and self.enable_encryption:
                        obj_data = self._decrypt_object_values(obj_data)
                    
                    # HYDRATE: dict → object (ALWAYS, not just when detail=True)
                    obj = self._hydrate_object(res_type, obj_data)
                    
                    # Verify hydration succeeded
                    if not obj:
                        hydration_failures += 1
                        self.logger.error(
                            f"Hydration returned None for {res_type} "
                            f"(uuid={obj_data.get('uuid', 'unknown')})"
                        )
                        continue
                    
                    # Verify we got an object, not a dict
                    if isinstance(obj, dict):
                        hydration_failures += 1
                        self.logger.error(
                            f"Hydration returned dict instead of object for {res_type} "
                            f"(uuid={obj_data.get('uuid', 'unknown')})"
                        )
                        continue
                    
                    # Set up object references
                    if hasattr(obj, 'clear_pending_updates'):
                        obj.clear_pending_updates()
                    if hasattr(obj, 'set_server_conn'):
                        obj.set_server_conn(self)
                    
                    objects.append(obj)
                    
                except (ImportError, AttributeError) as e:
                    # Critical schema errors
                    hydration_failures += 1
                    self.logger.error(
                        f"Schema error hydrating {res_type} "
                        f"(uuid={obj_data.get('uuid', 'unknown')}): {e}"
                    )
                    
                except Exception as e:
                    # Other deserialization errors
                    hydration_failures += 1
                    self.logger.warning(
                        f"Failed to hydrate {res_type} object "
                        f"(uuid={obj_data.get('uuid', 'unknown')}): {e}",
                        exc_info=True
                    )
            
            # Log summary
            if skipped_encrypted:
                self.logger.warning(
                    f"Skipped {len(skipped_encrypted)} encrypted {res_type} objects "
                    f"(encryption not enabled)"
                )
            
            if hydration_failures > 0:
                self.logger.error(
                    f"Failed to hydrate {hydration_failures}/{len(raw_objects)} "
                    f"{res_type} objects"
                )
            
            self.logger.info(
                f"Listed {len(objects)} {res_type} objects "
                f"(total_raw={len(raw_objects)}, failures={hydration_failures}, "
                f"skipped_encrypted={len(skipped_encrypted)})"
            )
            
            # ALWAYS return list of OBJECTS (never dicts)
            return objects
                
        except (AuthenticationError, AuthorizationError, RateLimitError):
            raise  # Propagate auth errors
        except Exception as e:
            self.logger.error(f"Error listing {res_type}: {e}", exc_info=True)
            raise

    def list_bulk(self, obj_type: str, uuids: List[str] = None, 
                  domain_name: Optional[str] = None,
                  api_key: Optional[str] = None, **kwargs) -> List[Any]:
        """
        List objects in bulk with domain-aware routing and per-call API key support.
        
        Args:
            obj_type: Object type
            uuids: List of UUIDs to retrieve
            domain_name: Domain name (optional, resolved automatically)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            **kwargs: Additional parameters (detail, count, filters, etc.)
            
        Returns:
            List of objects
        """
        try:
            # Resolve domain name and API key
            resolved_domain = self._resolve_domain_name(obj_type, domain_name)
            effective_key = self._resolve_api_key(api_key)
            
            if uuids is None:
                uuids = []
            if 'detail' not in kwargs:
                kwargs['detail'] = True
            
            # Pass domain_name and api_key to ApiClient
            raw_objects = self.api_client._http_list_bulk(
                to_dasherize(obj_type),
                uuids,
                domain_name=resolved_domain,
                api_key=effective_key,
                **kwargs
            )
            if not raw_objects:
                return []
            
            count = kwargs.get('count', 0)
            
            objects = []
            for obj_data in raw_objects:
                if count and len(objects) == count:
                    break
                try:
                    is_encrypted = (obj_data.get('_encrypted', False) or
                                  self._contains_encrypted_values(obj_data))
                    
                    if is_encrypted and not self.enable_encryption:
                        continue
                    if is_encrypted and self.enable_encryption:
                        obj_data = self._decrypt_object_values(obj_data)
                    
                    obj = self._hydrate_object(obj_type, obj_data)
                    if obj:
                        if hasattr(obj, 'clear_pending_updates'):
                            obj.clear_pending_updates()
                        if hasattr(obj, 'set_server_conn'):
                            obj.set_server_conn(self)
                        objects.append(obj)

                except Exception as e:
                    self.logger.warning(f"Failed to hydrate object: {e}")
            
            return objects
        except Exception as e:
            self.logger.error(f"Error in list_bulk: {e}", exc_info=True)
            raise

    def query(self, json_data: str, 
              domain_name: Optional[str] = None,
              api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Execute query with domain-aware routing and per-call API key support.
        
        Args:
            json_data: Query JSON
            domain_name: Domain name (optional, uses default)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            Query results
        """
        try:
            # Use default domain if not specified
            resolved_domain = domain_name or self._default_domain
            effective_key = self._resolve_api_key(api_key)
            
            result = self.api_client.query(json_data, domain_name=resolved_domain, api_key=effective_key)
            return result or {}
        except (ValueError, TypeError):
            # Let validation errors propagate to caller
            raise
        except Exception as e:
            # Catch other exceptions (connection errors, etc.) and return None
            self.logger.error(f"Query operation failed: {e}", exc_info=True)
            raise
    
    def _object_get_default_id(self, res_type: str, 
                               domain_name: Optional[str] = None,
                               api_key: Optional[str] = None) -> Optional[str]:
        """
        Get default ID for object type with domain-aware routing and per-call API key support.
        
        Args:
            res_type: Resource type
            domain_name: Domain name (optional, resolved automatically)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            Default object UUID or None
        """
        try:
            # Resolve domain name and API key
            resolved_domain = self._resolve_domain_name(res_type, domain_name)
            effective_key = self._resolve_api_key(api_key)
            
            obj_instance = self.api_client._get_object_instance(res_type, "default", None)
            default_fq_name = obj_instance.get_fq_name()
            return self.fq_name_to_uuid(res_type, default_fq_name, domain_name=resolved_domain, api_key=effective_key)
        except Exception:
            raise
    
    def _hydrate_object(self, obj_type: str, data: Dict[str, Any]) -> Any:
        """
        Hydrate a dictionary into an object instance.
        Tries all available namespaces in priority order.

        Args:
            obj_type: Object type (e.g., 'api-key', 'api_key', 'ApiKey')
            data: Dictionary data from API
        Returns:
            Object instance
        Raises:
            ImportError: If module cannot be imported from any namespace
            AttributeError: If class not found in any namespace
            Exception: If deserialization fails
        """
        # Normalize type names
        normalized_type = obj_type.replace('-', '_')
        class_name = inflection.camelize(normalized_type)

        self.logger.debug(
            f"Hydrating {obj_type}: "
            f"normalized={normalized_type}, "
            f"class={class_name}"
        )

        # Try all available namespaces in priority order
        last_error = None
        tried_modules = []

        # ✅ FIXED: Use self.expected_namespaces (instance-level from _build_config)
        for namespace in self.expected_namespaces:
            module_name = f"{namespace}.objects.{inflection.underscore(obj_type)}"
            tried_modules.append(module_name)

            self.logger.debug(f"Attempting to import from: {module_name}")

            # Import module (with caching)
            if module_name not in self._module_cache:
                try:
                    self._module_cache[module_name] = importlib.import_module(module_name)
                    self.logger.debug(f"✓ Imported module: {module_name}")
                except ImportError as e:
                    self.logger.debug(f"✗ Failed to import {module_name}: {e}")
                    last_error = e
                    continue

            module = self._module_cache[module_name]

            # Get object class
            try:
                obj_class = getattr(module, class_name)
                self.logger.debug(f"✓ Found class: {class_name} in {namespace}")
            except AttributeError as e:
                self.logger.debug(f"✗ Class {class_name} not found in {module_name}: {e}")
                last_error = e
                continue

            # Successfully found the class! Now deserialize
            try:
                obj_instance = safe_deserialize_from_dict(data, obj_class, obj_type)

                # CRITICAL CHECK: Verify we got an object, not a dict
                if isinstance(obj_instance, dict):
                    self.logger.error(
                        f"✗ safe_deserialize_from_dict returned dict instead of {class_name} object! "
                        f"This is a bug in serialization_errors module."
                    )
                    # Fallback: Try manual instantiation
                    try:
                        obj_instance = obj_class(**data)
                        self.logger.warning(f"⚠ Used fallback instantiation for {class_name}")
                    except Exception as fallback_error:
                        self.logger.error(f"✗ Fallback instantiation failed: {fallback_error}")
                        raise Exception(
                            f"Failed to instantiate {class_name}: "
                            f"safe_deserialize_from_dict returned dict, fallback failed"
                        ) from fallback_error

                if obj_instance and hasattr(obj_instance, 'uuid'):
                    self.logger.debug(f"✓ Hydrated {class_name} with uuid={obj_instance.uuid}")
                else:
                    self.logger.warning(f"⚠ Hydrated {class_name} but no uuid attribute")

                return obj_instance

            except Exception as e:
                self.logger.error(f"✗ Failed to deserialize {class_name} from {namespace}: {e}")
                last_error = e
                continue

        # If we get here, schema wasn't found in any namespace
        error_msg = (
            f"Schema '{class_name}' not found in any available namespace. "
            f"Tried: {', '.join(tried_modules)}"
        )
        self.logger.error(f"✗ {error_msg}")

        if last_error:
            raise ImportError(error_msg) from last_error
        else:
            raise ImportError(error_msg)

    def fq_name_to_uuid(self, obj_type: str, fq_name: Union[str, List[str]],
                        domain_name: Optional[str] = None,
                        api_key: Optional[str] = None) -> Optional[str]:
        """
        Convert FQ name to UUID with domain-aware routing and per-call API key support.
        
        Args:
            obj_type: Object type
            fq_name: Fully qualified name (list or string)
            domain_name: Domain name (optional, resolved automatically)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            Object UUID or None
        """
        try:
            # Resolve domain name and API key
            resolved_domain = self._resolve_domain_name(obj_type, domain_name)
            effective_key = self._resolve_api_key(api_key)
            
            if isinstance(fq_name, list):
                fq_name_str = ':'.join(fq_name)
            else:
                fq_name_str = fq_name
            
            # Pass domain_name and api_key to ApiClient
            return self.api_client.fq_name_to_uuid(
                obj_type,
                fq_name_str,
                domain_name=resolved_domain,
                api_key=effective_key
            )
        except Exception:
            raise

    def uuid_to_fq_name(self, obj_type: str, uuid: str,
                        domain_name: Optional[str] = None,
                        api_key: Optional[str] = None) -> Optional[List[str]]:
        """
        Convert UUID to FQ name with domain-aware routing and per-call API key support.
        
        Args:
            obj_type: Object type
            uuid: Object UUID
            domain_name: Domain name (optional, resolved automatically)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            Fully qualified name as list or None
        """
        try:
            # Resolve domain name and API key
            resolved_domain = self._resolve_domain_name(obj_type, domain_name)
            effective_key = self._resolve_api_key(api_key)
            
            # Pass domain_name and api_key to ApiClient
            return self.api_client.uuid_to_fq_name(
                obj_type,
                uuid,
                domain_name=resolved_domain,
                api_key=effective_key
            )
        except Exception:
            raise
    
    def ref_update(self, obj_type: str, obj_uuid: str, ref_type: str, 
                   ref_uuid: str, ref_fq_name: List[str], operation: str, attr=None,
                   domain_name: Optional[str] = None,
                   api_key: Optional[str] = None) -> Optional[str]:
        """
        Update reference with domain-aware routing and per-call API key support.
        
        Args:
            obj_type: Source object type
            obj_uuid: Source object UUID
            ref_type: Reference type
            ref_uuid: Target object UUID
            ref_fq_name: Target FQ name
            operation: Operation (ADD/DELETE)
            attr: Optional attributes
            domain_name: Domain name (optional, resolved automatically)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            Object UUID on success, None on failure
        """
        try:
            # Resolve domain name and API key
            resolved_domain = self._resolve_domain_name(obj_type, domain_name)
            effective_key = self._resolve_api_key(api_key)

            ref_type = to_dasherize(ref_type)
            
            if ref_type.endswith('_refs'):
                ref_type = ref_type[:-5].replace('_', '-')
            
            # Pass domain_name and api_key to ApiClient
            success = self.api_client.ref_update(
                from_type=obj_type, from_uuid=obj_uuid, to_type=ref_type,
                to_uuid=ref_uuid, to_fq_name=ref_fq_name, attr=attr, operation=operation,
                domain_name=resolved_domain,
                api_key=effective_key
            )
            return obj_uuid if success else None
        except Exception:
            raise
    
    def obj_to_json(self, obj) -> str:
        try:
            if hasattr(obj, 'to_dict'):
                obj_dict = safe_serialize_to_dict(obj, getattr(obj, 'obj_type', 'unknown'))
            else:
                obj_dict = obj.__dict__
            return safe_serialize_to_json(obj_dict, getattr(obj, 'obj_type', 'unknown'))
        except Exception:
            raise
    
    def obj_to_dict(self, obj) -> dict:
        try:
            if hasattr(obj, 'to_dict'):
                return safe_serialize_to_dict(obj, getattr(obj, 'obj_type', 'unknown'))
            return safe_serialize_to_dict(obj.__dict__, getattr(obj, 'obj_type', 'unknown'))
        except Exception:
            raise
    
    def set_auth_token(self, token: str):
        self._auth_token = token
    
    def get_auth_token(self) -> Optional[str]:
        return getattr(self, '_auth_token', None)
    
    def obj_to_id(self, obj) -> Optional[str]:
        try:
            if hasattr(obj, 'uuid') and obj.uuid:
                return obj.uuid
            elif hasattr(obj, 'get_fq_name'):
                fq_name = obj.get_fq_name()
                obj_type = getattr(obj, 'obj_type', None)
                if obj_type:
                    return self.fq_name_to_uuid(obj_type, fq_name)
            return None
        except Exception:
            raise
    
    def resource_list(self, obj_type: str, 
                      domain_name: Optional[str] = None,
                      api_key: Optional[str] = None, **kwargs) -> List[Any]:
        """List resources with domain-aware routing and per-call API key support."""
        return self._objects_list(obj_type, domain_name=domain_name, api_key=api_key, **kwargs)

    def list_objects(self, obj_type: str, parent_uuid: Optional[str] = None,
                    domain_name: Optional[str] = None, api_key: Optional[str] = None,
                    filters: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        Wrapper for api_client.list_objects() - provides consistent API.

        List all objects of given type with optional filtering.

        Args:
            obj_type: Type of object to list (e.g., 'ApiKey', 'Project', 'Tenant')
            parent_uuid: Optional parent UUID for filtering
            domain_name: Domain name (optional, uses default if not provided)
            api_key: Per-call API key override (optional)
            filters: Optional dictionary of filters (e.g., {'enabled': True})

        Returns:
            List of object instances

        Example:
            # List all API keys for a tenant
            api_keys = api_lib.list_objects(
                obj_type='ApiKey',
                parent_uuid=tenant_uuid,
                domain_name='acme-corp',
                filters={'enabled': True}
            )

            # List all projects in a domain
            projects = api_lib.list_objects(
                obj_type='Project',
                domain_name='acme-corp'
            )
        """
        domain = domain_name or self._default_domain
        self.logger.debug(f"list_objects: {obj_type} in domain {domain}")

        try:
            # Delegate to api_client.list_objects
            objects = self.api_client.list_objects(
                obj_type=obj_type,
                parent_uuid=parent_uuid,
                domain_name=domain,
                api_key=api_key
            )

            # Apply filters if provided
            if filters and objects:
                filtered_objects = []
                for obj in objects:
                    match = True
                    for key, value in filters.items():
                        obj_value = getattr(obj, key, None)
                        if obj_value != value:
                            match = False
                            break
                    if match:
                        filtered_objects.append(obj)
                objects = filtered_objects

            # Filter by parent_uuid if provided
            if parent_uuid and objects:
                objects = [
                    obj for obj in objects
                    if getattr(obj, 'parent_uuid', None) == parent_uuid
                ]

            self.logger.debug(f"list_objects: Found {len(objects)} {obj_type} objects")
            return objects

        except Exception as e:
            self.logger.error(f"Error in list_objects({obj_type}): {e}", exc_info=True)
            raise

    def get_stats(self, obj_type: str, fields: Optional[List[str]] = None,
                  match: Optional[Dict] = None, domain_name: Optional[str] = None,
                  api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get statistics for numeric fields with domain-aware routing and per-call API key.
        
        Args:
            obj_type: Object type
            fields: List of numeric field names (optional)
            match: Filter dict (optional)
            domain_name: Domain name (optional, uses default_domain if not provided)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            Stats dict with count, sum, avg, min, max per field or None
            
        Example:
            stats = api_lib.get_stats(
                'order',
                fields=['amount', 'quantity'],
                match={'status': 'completed'},
                domain_name='acme-corp'
            )
        """
        try:
            # Resolve domain name and API key
            resolved_domain = self._resolve_domain_name(obj_type, domain_name)
            effective_key = self._resolve_api_key(api_key)
            
            return self.api_client.get_stats(
                obj_type=obj_type,
                fields=fields,
                match=match,
                domain_name=resolved_domain,
                api_key=effective_key
            )
        except Exception as e:
            self.logger.error(f"Error getting stats for {obj_type}: {e}", exc_info=True)
            raise

    def aggregate(self, obj_type: str, pipeline: Optional[List[Dict]] = None,
                  match: Optional[Dict] = None, group_by: Optional[str] = None,
                  metrics: Optional[Dict] = None, sort: Optional[Dict] = None,
                  limit: Optional[int] = None, domain_name: Optional[str] = None,
                  api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Execute aggregation pipeline with domain-aware routing and per-call API key.
        
        Args:
            obj_type: Object type to aggregate
            pipeline: Raw MongoDB pipeline (optional - expert mode)
            match: Match filter dict (optional - builder mode)
            group_by: Field to group by (optional - builder mode)
            metrics: Metrics to compute (optional - builder mode)
            sort: Sort specification (optional)
            limit: Result limit (optional)
            domain_name: Domain name (optional, uses default_domain if not provided)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            Aggregation results or None
            
        Examples:
            # Builder syntax
            results = api_lib.aggregate(
                'order',
                match={'status': 'completed'},
                group_by='customer_id',
                metrics={'total': {'$sum': 'amount'}},
                domain_name='acme-corp'
            )
            
            # Raw pipeline
            results = api_lib.aggregate(
                'order',
                pipeline=[
                    {'$match': {'status': 'completed'}},
                    {'$group': {'_id': '$customer_id', 'total': {'$sum': '$amount'}}}
                ],
                domain_name='acme-corp'
            )
        """
        try:
            # Resolve domain name and API key
            resolved_domain = self._resolve_domain_name(obj_type, domain_name)
            effective_key = self._resolve_api_key(api_key)
            
            return self.api_client.aggregate(
                obj_type=obj_type,
                pipeline=pipeline,
                match=match,
                group_by=group_by,
                metrics=metrics,
                sort=sort,
                limit=limit,
                domain_name=resolved_domain,
                api_key=effective_key
            )
        except Exception as e:
            self.logger.error(f"Error aggregating {obj_type}: {e}", exc_info=True)
            raise

    def get_distinct(self, obj_type: str, field: str, match: Optional[Dict] = None,
                     limit: int = 1000, domain_name: Optional[str] = None,
                     api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get distinct values for a field with domain-aware routing and per-call API key.
        
        Args:
            obj_type: Object type
            field: Field name to get distinct values for
            match: Filter dict (optional)
            limit: Maximum values to return (default 1000, max 10000)
            domain_name: Domain name (optional, uses default_domain if not provided)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            Dict with distinct values or None
            
        Example:
            distinct = api_lib.get_distinct(
                'project',
                field='status',
                match={'enabled': True},
                limit=100,
                domain_name='acme-corp'
            )
            # Returns: {'values': ['active', 'pending', 'completed'], 'count': 3}
        """
        try:
            # Resolve domain name and API key
            resolved_domain = self._resolve_domain_name(obj_type, domain_name)
            effective_key = self._resolve_api_key(api_key)
            
            return self.api_client.get_distinct(
                obj_type=obj_type,
                field=field,
                match=match,
                limit=limit,
                domain_name=resolved_domain,
                api_key=effective_key
            )
        except Exception as e:
            self.logger.error(f"Error getting distinct values for {obj_type}.{field}: {e}", exc_info=True)
            raise

    def get_count_by(self, obj_type: str, field: str, match: Optional[Dict] = None,
                     limit: int = 100, sort: str = '-count',
                     domain_name: Optional[str] = None,
                     api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get counts grouped by field values with domain-aware routing and per-call API key.
        
        Args:
            obj_type: Object type
            field: Field name to group by
            match: Filter dict (optional)
            limit: Maximum groups to return (default 100, max 1000)
            sort: Sort order - 'count', '-count', 'value', '-value' (default '-count')
            domain_name: Domain name (optional, uses default_domain if not provided)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            Dict with grouped counts or None
            
        Example:
            count_by = api_lib.get_count_by(
                'user_account',
                field='role',
                match={'enabled': True},
                sort='-count',
                limit=50,
                domain_name='acme-corp'
            )
            # Returns: {
            #   'groups': [
            #     {'value': 'developer', 'count': 45},
            #     {'value': 'admin', 'count': 12}
            #   ],
            #   'total_count': 57
            # }
        """
        try:
            # Resolve domain name and API key
            resolved_domain = self._resolve_domain_name(obj_type, domain_name)
            effective_key = self._resolve_api_key(api_key)
            
            return self.api_client.get_count_by(
                obj_type=obj_type,
                field=field,
                match=match,
                limit=limit,
                sort=sort,
                domain_name=resolved_domain,
                api_key=effective_key
            )
        except Exception as e:
            self.logger.error(f"Error getting count-by for {obj_type}.{field}: {e}", exc_info=True)
            raise
    
    def health_check(self) -> bool:
        try:
            return self.api_client.health_check()
        except Exception:
            return False
    
    def get_obj_class(self, obj_type: str):
        try:
            module_name = obj_type.replace('-', '_')
            module = importlib.import_module(f'{PRIMARY_SCHEMA_NAMESPACE}.objects.{module_name}')
            class_name = inflection.camelize(module_name)
            return getattr(module, class_name, None)
        except Exception:
            raise
    
    def create_object_instance(self, obj_type: str, name: str, parent=None, **kwargs):
        obj_class = self.get_obj_class(obj_type)
        if not obj_class:
            raise ValueError(f"Unknown object type: {obj_type}")
        obj = obj_class(name)
        if parent:
            obj.set_fq_name(parent.fq_name + [name])
        else:
            obj.set_fq_name([name])
        for key, value in kwargs.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        return obj
    
    def close(self):
        if hasattr(self, 'api_client'):
            self.api_client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class ApiLibSingleton:
    _instance: Optional['ApiLib'] = None
    _lock = threading.Lock()
    _initialized = False
    _logger = None
    
    @classmethod
    def initialize(cls, **config_overrides) -> 'ApiLib':
        with cls._lock:
            if cls._initialized:
                raise RuntimeError("ApiLib singleton already initialized")
            cls._logger = initialize_logger("py-api-lib")
            cls._instance = ApiLib.from_config(**config_overrides)
            cls._initialized = True
            return cls._instance
    
    @classmethod
    def get_instance(cls) -> 'ApiLib':
        if not cls._initialized or cls._instance is None:
            raise RuntimeError("ApiLib singleton not initialized")
        return cls._instance
    
    @classmethod
    def is_initialized(cls) -> bool:
        return cls._initialized and cls._instance is not None
    
    @classmethod
    def reset(cls):
        with cls._lock:
            if cls._instance:
                try:
                    cls._instance.close()
                except Exception:
                    pass
            cls._instance = None
            cls._initialized = False
    
    @classmethod
    def health_check(cls) -> bool:
        try:
            if not cls.is_initialized():
                return False
            return cls._instance.health_check()
        except Exception:
            return False


def create_api_lib(api_server_host='127.0.0.1', api_server_port='8082', 
                   extensions=None, **kwargs) -> ApiLib:
    return ApiLib(api_server_host=api_server_host, api_server_port=api_server_port,
                  extensions=extensions, **kwargs)


def get_api_lib_config(config_file: str = None, **kwargs) -> ApiLib:
    return ApiLib.from_config(config_file=config_file, **kwargs)


def get_default_api_lib() -> ApiLib:
    return ApiLib.get_default_instance()


def get_api_lib() -> 'ApiLib':
    return ApiLibSingleton.get_instance()


def initialize_api_lib(logger: Optional[logging.Logger] = None, **config) -> 'ApiLib':
    return ApiLibSingleton.initialize(logger=logger, **config)
