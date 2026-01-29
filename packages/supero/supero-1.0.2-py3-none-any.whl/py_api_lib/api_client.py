"""
Enhanced API Client with API Key authentication and domain-aware routing support.

Version 2.1 - Per-Call API Key Support:
- All HTTP methods accept optional api_key parameter for RBAC enforcement
- Per-call api_key overrides instance default (for user-specific operations)
- Maintains backward compatibility (api_key parameter is optional)

Version 2.0 - Domain-Aware Architecture:
- All methods accept optional domain_name parameter
- Configurable default_domain for operations
- URL construction: /{domain}/{resource} pattern
- Plural form for list operations: /{domain}/{resource}s

CHANGES v2.1:
1. Added api_key parameter to all _http_* methods
2. Added _get_request_headers(api_key) for per-call header override
3. Modified _make_request to accept api_key parameter
4. All high-level methods pass api_key through to HTTP layer
"""

import requests
import json
import time
import inflection
import re
import importlib
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from .api_logger import get_logger
from .exceptions import (
    AuthenticationError, AuthorizationError, RateLimitError
)

# Import everything from centralized config
from ._runtime_config import (
    BUILD_MODE,
    PRIMARY_SCHEMA_NAMESPACE,
    SCHEMA_NAMESPACES,
    TENANT_NAMESPACE,
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

def normalize_domain_name(name: str) -> str:
    """
    Normalize object/domain name to lowercase with preserved special characters.

    SPECIAL CASES (preserved as-is, only lowercased):
    - Email addresses (valid format: user@domain)
    - Phone numbers (start with + or are digit-heavy)

    For regular names:
    - Converts to lowercase
    - Allows: alphanumeric, hyphen (-), dot (.), underscore (_)
    - Replaces spaces and other chars with hyphen
    - Collapses multiple separators

    Args:
        name: Raw name (e.g., "Acme Corporation", "user@example.com", "+1-555-1234")

    Returns:
        Normalized name or preserved special format

    Examples:
        >>> normalize_name("Acme Corporation")
        'acme-corporation'
        >>> normalize_name("My_Project.Name")
        'my-project.name'
        >>> normalize_name("user@example.com")
        'user@example.com'
        >>> normalize_name("+1-555-1234")
        '+1-555-1234'
        >>> normalize_name("platform-admin@system.com")
        'platform-admin@system.com'
        >>> normalize_name("@@@")
        ''
    """
    if not name or not isinstance(name, str):
        return name

    # Strip whitespace
    name = name.strip()

    # SPECIAL CASE 1: Email addresses (valid format)
    # Must have: one @, something before @, something after @
    if '@' in name:
        parts = name.split('@')
        # Valid email: exactly one @, non-empty local and domain parts
        if len(parts) == 2 and parts[0] and parts[1]:
            # Additional check: domain should have at least one char
            # (could be "localhost" or "example.com")
            return name.lower()
        # Invalid email format - fall through to normal normalization

    # SPECIAL CASE 2: Phone numbers (starts with + or is digit-heavy)
    # Preserve as-is (including formatting)
    if name.startswith('+'):
        return name

    # Check if digit-heavy (>50% digits) - likely a phone number
    if len(name) > 0:
        digit_ratio = sum(c.isdigit() for c in name) / len(name)
        if digit_ratio > 0.5:
            return name

    # REGULAR NAME: Apply normalization
    # Convert to lowercase
    name = name.lower()

    # Allow: alphanumeric, hyphen, dot, underscore
    # Replace spaces and other special chars with hyphen
    name = re.sub(r'[^a-z0-9.\-_]+', '-', name)

    # Collapse multiple consecutive separators to single hyphen
    name = re.sub(r'[-_.]{2,}', '-', name)

    # Strip leading/trailing separators
    name = name.strip('-._')

    return name

class ApiClient:
    """
    Build-aware API client with API key authentication and domain-aware routing.
    Uses the correct schema namespace based on how it was built.

    Version 2.1 Features:
    - Per-call api_key parameter for RBAC enforcement
    - api_key can be passed to any HTTP method to override instance default
    
    Version 2.0 Features:
    - Domain-aware URL routing (domain in path, not query)
    - Configurable default domain for operations
    - All methods accept optional domain_name parameter

    BACKWARD COMPATIBLE: Works without API keys if server doesn't require them.
    """

    def __init__(self, server_ip: str = '127.0.0.1', port: int = 8080,
                 timeout: int = 30, max_retries: int = 3,
                 api_key: str = None,
                 use_proxy: bool = False,
                 proxy_prefix: str = '/api/v1/crud',
                 jwt_token: str = None,
                 domain_name: str = 'default-domain',
                 default_domain: str = 'default-domain'):
        """
        Initialize the API client with optional proxy mode and domain-aware routing.
        
        Args:
            server_ip: API server IP or platform-core IP (if use_proxy=True)
            port: API server port or platform-core port (if use_proxy=True)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            api_key: API key for direct mode authentication (default key)
            use_proxy: If True, talk to platform-core instead of api-server
            proxy_prefix: URL prefix for proxy endpoints (default: /api/v1/crud)
            jwt_token: JWT token for proxy mode authentication
            domain_name: Domain name for legacy compatibility (deprecated, use default_domain)
            default_domain: Default domain for all operations (default: 'default-domain')
        
        Raises:
            ValueError: If authentication configuration is invalid
        
        Examples:
            # Direct mode (for platform-core internal use)
            client = ApiClient(
                server_ip='api-server',
                port=8082,
                api_key='ak_acme_prod_xxx',
                default_domain='acme-corp'
            )
            
            # Proxy mode (for external tenant apps)
            client = ApiClient(
                server_ip='platform-core',
                port=8083,
                use_proxy=True,
                jwt_token='eyJhbGc...',
                default_domain='acme-corp'
            )
        """
        # Store configuration
        self.use_proxy = use_proxy
        # Use default_domain if provided, otherwise fall back to domain_name
        self._default_domain = normalize_domain_name(default_domain if default_domain else domain_name)
        self.proxy_prefix = proxy_prefix.rstrip('/')
        self._jwt_token = jwt_token
        self._api_key = api_key
        
        # Initialize logger early so validation can use it
        self.logger = get_logger()
        if not self._api_key:
            self.logger.warning(
                "APIClient initialized without API key."
            )
        
        # VALIDATE AUTH CONFIG - Fail fast on invalid combinations
        self._validate_auth_config(api_key, jwt_token, use_proxy)
        
        protocol = "https" if port == 443 else "http"

        # Build base URL based on mode
        if use_proxy:
            # Proxy mode: point to platform-core with prefix
            self.base_url = f"{protocol}://{server_ip}:{port}{self.proxy_prefix}"
        else:
            # Direct mode: point to api-server
            self.base_url = f"{protocol}://{server_ip}:{port}"
        
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.module_cache = {}
        
        # Build awareness - load from build config
        try:
            from ._build_config import (
                BUILD_MODE,
                PRIMARY_SCHEMA_NAMESPACE,
                SCHEMA_NAMESPACES
            )
            self.build_mode = BUILD_MODE
            self.primary_namespace = PRIMARY_SCHEMA_NAMESPACE
            self.expected_namespaces = SCHEMA_NAMESPACES
        except ImportError:
            # Fallback for development mode
            self.build_mode = 'platform'
            self.primary_namespace = 'pymodel_system'
            self.expected_namespaces = ['pymodel_system']
            self.logger.warning(
                "Build config not found, using default (platform mode). "
                "Run build.sh to generate proper configuration."
            )
        
        # Lazy-loaded serialization utilities
        self._serialization_helpers = None
        
        # Setup session headers (Content-Type only, Auth is per-request now)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'UnifiedApiClient/2.1'
        })
        
        # Set default authentication in session (used when no per-call key provided)
        if use_proxy and jwt_token:
            self._set_jwt_header(jwt_token)
            mode_str = "PROXY mode (JWT auth)"
        elif api_key:
            self._set_api_key_header(api_key)
            mode_str = "DIRECT mode (API key auth)"
        else:
            mode_str = "NO authentication"
        
        self.logger.info(
            f"ApiClient initialized in {mode_str} "
            f"(build={self.build_mode}, namespace={self.primary_namespace}, "
            f"default_domain={self._default_domain})"
        )
        self.logger.info(f"Base URL: {self.base_url}")
        self._test_connection()

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

    def _unwrap_response(self, result: dict) -> dict:
        """
        Handle platform-core wrapped responses.

        Platform-core formats:
          - {'success': True, 'data': {...}}     → return data
          - {'success': True, 'results': [...]}  → return {'objects': results}
          - {'success': True, 'uuid': '...'}     → return as-is (uuid at top)

        api-server format (passthrough):
          - {'domain': {...}}                    → return as-is
          - {'objects': [...]}                   → return as-is
        """
        if not result:
            return result

        # Already has 'objects' key (api-server format) - passthrough
        if 'objects' in result:
            return result

        # Platform-core wrapped format
        if 'success' in result:
            # List/query response: results → objects
            if 'results' in result:
                return {'objects': result['results']}

            # CRUD response: unwrap data
            if 'data' in result:
                return result['data']

        # Not wrapped - return as-is
        return result

    def set_default_domain(self, domain_name: str):
        """
        Set the default domain for operations.
        
        Args:
            domain_name: Domain name to use as default
        """
        self._default_domain = normalize_domain_name(domain_name)
        self.logger.info(f"Default domain updated to: {self._default_domain}")

    def get_default_domain(self) -> str:
        """Get the current default domain."""
        return self._default_domain

    def _set_api_key_header(self, api_key: str):
        """Set Authorization Bearer header for API key in session (default)."""
        self.session.headers['Authorization'] = f'Bearer {api_key}'

    def _set_jwt_header(self, jwt_token: str):
        """Set Authorization Bearer header for proxy mode in session (default)."""
        self.session.headers['Authorization'] = f'Bearer {jwt_token}'

    def _clear_auth_headers(self):
        """Remove all authentication headers from session."""
        self.session.headers.pop('Authorization', None)

    def _get_request_headers(self, api_key: Optional[str] = None) -> Dict[str, str]:
        """
        Get headers for a specific request, with optional per-call api_key override.
        
        This is the key method for RBAC support - allows each request to use
        a different API key (user's key) instead of the instance default.
        
        Args:
            api_key: Per-call API key override (None = use session default)
            
        Returns:
            Headers dict with appropriate Authorization header
        """
        if api_key:
            # Per-call override - use provided key
            return {
                'Content-Type': 'application/json',
                'User-Agent': 'UnifiedApiClient/2.1',
                'Authorization': f'Bearer {api_key}'
            }
        else:
            # No override - session headers will be used (includes default auth)
            return None  # Signal to use session headers

    def _get_serialization_helpers(self):
        """Load serialization helpers dynamically from available namespaces."""
        import importlib
        
        # Return cached helpers if already loaded
        if self._serialization_helpers is not None:
            return self._serialization_helpers
        # Try namespaces in priority order based on build config
        for namespace in self.expected_namespaces:
            try:
                # ✅ FIXED: Dynamic import - works with any namespace!
                module = importlib.import_module(f"{namespace}.serialization_errors")
                
                # Extract serialization utilities
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
                if namespace == 'pymodel_system':
                    source = f'{namespace} (system schemas)'
                elif namespace.startswith('pymodel_'):
                    source = f'{namespace} (tenant schemas)'
                else:
                    source = namespace
                # Successfully loaded serialization helpers
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
                    f"Could not load serialization helpers from {namespace}: {e}"
                )
                continue
        # If we get here, no schema packages were found
        # Provide basic fallback implementations
        self.logger.warning(
            f"No serialization helpers found in expected namespaces: {self.expected_namespaces}. "
            f"Build mode: {self.build_mode}. Using basic JSON serialization as fallback."
        )
        # Basic fallback implementations
        self._serialization_helpers = {
            'SerializationError': Exception,
            'ObjectSerializationError': Exception,
            'ObjectDeserializationError': Exception,
            'JSONSerializationError': Exception,
            'JSONDeserializationError': Exception,
            'safe_serialize_to_dict': self._basic_serialize_to_dict,
            'safe_serialize_to_json': self._basic_serialize_to_json,
            'safe_deserialize_from_dict': self._basic_deserialize_from_dict,
            'safe_deserialize_from_json': self._basic_deserialize_from_json,
        }
        return self._serialization_helpers


    # Basic fallback serialization methods
    def _basic_serialize_to_dict(self, obj):
        """Basic object to dict conversion"""
        if isinstance(obj, dict):
            return obj
        elif hasattr(obj, '__dict__'):
            return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
        else:
            return obj

    def _basic_serialize_to_json(self, obj):
        """Basic object to JSON string conversion"""
        obj_dict = self._basic_serialize_to_dict(obj)
        return json.dumps(obj_dict, default=str)

    def _basic_deserialize_from_dict(self, cls, data):
        """Basic dict to object conversion"""
        if not isinstance(data, dict):
            return data
        if callable(cls):
            try:
                return cls(**data)
            except TypeError:
                # If __init__ doesn't accept kwargs, try setting attributes
                obj = cls()
                for key, value in data.items():
                    setattr(obj, key, value)
                return obj
        return data

    def _basic_deserialize_from_json(self, cls, json_str):
        """Basic JSON string to object conversion"""
        data = json.loads(json_str)
        return self._basic_deserialize_from_dict(cls, data)

    def get_build_info(self):
        """
        Get build configuration information for this ApiClient instance.

        Returns:
            dict: Build information including mode, namespaces, etc.
        """
        return {
            'build_mode': self.build_mode,
            'primary_namespace': self.primary_namespace,
            'expected_namespaces': self.expected_namespaces,
            'serialization_loaded': self._serialization_helpers is not None,
            'default_domain': self._default_domain,
        }

    def set_api_key(self, api_key: Optional[str]):
        """Set or update default API key at runtime."""
        if self.use_proxy:
            self.logger.warning("Cannot set API key in proxy mode. Use set_jwt_token() instead.")
            return
        
        self._api_key = api_key
        
        if api_key:
            self._set_api_key_header(api_key)
            self.logger.info(f"API key updated: {api_key[:20]}***")
        else:
            self._clear_auth_headers()
            self.logger.info("API key cleared")

    def set_jwt_token(self, jwt_token: Optional[str]):
        """Set or update JWT token at runtime (proxy mode only)."""
        if not self.use_proxy:
            self.logger.warning("Cannot set JWT token in direct mode. Use set_api_key() instead.")
            return
        
        self._jwt_token = jwt_token
        
        if jwt_token:
            self._set_jwt_header(jwt_token)
            self.logger.info("JWT token updated")
        else:
            self._clear_auth_headers()
            self.logger.info("JWT token cleared")
    
    def get_api_key_prefix(self, api_key: Optional[str] = None) -> Optional[str]:
        """
        Get API key prefix (masked for security).
        
        Args:
            api_key: Specific key to mask (None = use instance default)
            
        Returns:
            Masked key prefix or None
        """
        key = api_key or self._api_key
        if not key:
            return None
        
        parts = key.split('_')
        # Handle new 5-part format (ak_domain_project_env_suffix)
        if len(parts) >= 5:
            return f"{parts[0]}_{parts[1]}_{parts[2]}_{parts[3]}_***"
        # Fallback for old 4-part format (ak_domain_env_suffix)
        elif len(parts) >= 4:
            return f"{parts[0]}_{parts[1]}_{parts[2]}_***"
        return "***"

    def _test_connection(self) -> bool:
        """Test connection to API server."""
        try:
            response = self.session.options(self.base_url, timeout=5)
            if response.status_code < 500:
                self.logger.info("Successfully connected to API server")
                return True
        except Exception as e:
            self.logger.warning(f"Could not verify connection to API server: {e}")
        return False

    
    def _make_request(self, method: str, endpoint: str, 
                      api_key: Optional[str] = None, **kwargs) -> Optional[requests.Response]:
        """
        Make HTTP request with retry logic, auth handling, and rate limit support.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: Full URL endpoint
            api_key: Per-call API key override (None = use session default)
            **kwargs: Additional requests parameters
            
        Returns:
            Response object or None
        """
        last_exception = None
        
        # Get per-call headers if api_key override provided
        override_headers = self._get_request_headers(api_key)
        if override_headers:
            # Merge with any existing headers in kwargs
            if 'headers' in kwargs:
                kwargs['headers'].update(override_headers)
            else:
                kwargs['headers'] = override_headers

        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.request(
                    method=method,
                    url=endpoint,
                    timeout=self.timeout,
                    **kwargs
                )

                # Log with masked key info
                key_info = self.get_api_key_prefix(api_key) if api_key else "session-default"
                # Always log errors, only log debug for non-health endpoints
                is_health_check = '/health' in endpoint or '/internal/logs' in endpoint  # FIX: url -> endpoint
                if response.status_code >= 400:
                    self.logger.warning(f"{method} {endpoint} - Status: {response.status_code} (key={key_info})")
                elif not is_health_check:
                    self.logger.debug(f"{method} {endpoint} - Status: {response.status_code} (key={key_info})")

                if response.status_code == 401:
                    error_msg = self._extract_error_message(response)
                    used_key = self.get_api_key_prefix(api_key) or self.get_api_key_prefix()
                    self.logger.error(f"Authentication failed: {error_msg} (key={used_key})")
                    raise AuthenticationError(
                        f"API key authentication failed: {error_msg}\n"
                        f"Used key: {used_key or 'None'}\n"
                        f"Hint: Check your API key or use set_api_key() to update it"
                    )

                if response.status_code == 403:
                    error_msg = self._extract_error_message(response)
                    used_key = self.get_api_key_prefix(api_key) or self.get_api_key_prefix()
                    self.logger.error(f"Authorization failed: {error_msg} (key={used_key})")
                    raise AuthorizationError(
                        f"API key lacks required permissions: {error_msg}\n"
                        f"Used key: {used_key}\n"
                        f"Hint: Check API key scopes (read, write, delete, admin)"
                    )

                if response.status_code == 429:
                    retry_after = self._get_retry_after(response)
                    error_msg = self._extract_error_message(response)

                    self.logger.warning(
                        f"Rate limit exceeded. Retry after {retry_after}s. "
                        f"Attempt {attempt + 1}/{self.max_retries + 1}"
                    )

                    if attempt < self.max_retries and retry_after and retry_after <= 60:
                        self.logger.info(f"Waiting {retry_after}s before retry...")
                        time.sleep(retry_after)
                        continue
                    else:
                        raise RateLimitError(
                            f"Rate limit exceeded: {error_msg}\n"
                            f"Retry after: {retry_after}s",
                            retry_after=retry_after
                        )

                if 400 <= response.status_code < 500:
                    return response

                if response.status_code >= 500:
                    if attempt < self.max_retries:
                        self.logger.warning(
                            f"Server error {response.status_code} on attempt {attempt + 1}, retrying..."
                        )
                        time.sleep(min(2 ** attempt, 10))
                        continue
                    else:
                        return response

                return response

            except (AuthenticationError, AuthorizationError, RateLimitError):
                raise
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                last_exception = e
                if attempt < self.max_retries:
                    self.logger.warning(f"Network error on attempt {attempt + 1}, retrying...")
                    time.sleep(min(2 ** attempt, 10))
                    continue
            except Exception as e:
                self.logger.error(f"Unexpected error during request: {e}")
                return None

        self.logger.error(f"Request failed after {self.max_retries} retries. Last error: {last_exception}")
        return None

    def _extract_error_message(self, response: requests.Response) -> str:
        """
        Extract detailed error message from response.
        
        Tries multiple common error response formats to get the most detailed message.
        """
        try:        
            error_data = response.json()
            
            # Try different response formats in order of detail/usefulness
            
            # 1. FastAPI style: {"detail": "message"} or {"detail": {...}}
            if 'detail' in error_data:
                detail = error_data['detail']
                if isinstance(detail, str):
                    return detail
                elif isinstance(detail, dict):
                    return detail.get('message', str(detail))
                elif isinstance(detail, list):
                    # List of validation errors
                    return '; '.join(str(d) for d in detail)
            
            # 2. Check for 'failed' array (schema upload errors, etc.)
            if 'failed' in error_data and error_data['failed']:
                failed_items = error_data['failed']
                if isinstance(failed_items, list) and len(failed_items) > 0:
                    # Build detailed error message from failed items
                    error_parts = []
                    for item in failed_items[:5]:  # Show first 5
                        if isinstance(item, dict):
                            error_parts.append(item.get('error', str(item)))
                        else:
                            error_parts.append(str(item))
                    
                    error_msg = '; '.join(error_parts)
                    if len(failed_items) > 5:
                        error_msg += f' (and {len(failed_items) - 5} more)'
                    
                    # Prepend main error message if present
                    main_error = error_data.get('error', error_data.get('message'))
                    if main_error:
                        return f"{main_error}: {error_msg}"
                    return error_msg
            
            # 3. Explicit message field: {"message": "..."}
            if 'message' in error_data:
                return error_data['message']
            
            # 4. Combined error + message: {"error": "Type", "message": "Details"}
            if 'error' in error_data and 'message' in error_data:
                return f"{error_data['error']}: {error_data['message']}"
            
            # 5. Error with details: {"error": "Type", "details": {...}}
            if 'error' in error_data and 'details' in error_data:
                return f"{error_data['error']}: {error_data['details']}"
            
            # 6. Just error field (may be just exception class name)
            if 'error' in error_data:
                return str(error_data['error'])
            
            # 7. Fallback: stringify entire response
            return str(error_data)
            
        except (ValueError, AttributeError):
            # Not JSON, return text response
            return response.text or f"HTTP {response.status_code}"

    def _get_retry_after(self, response: requests.Response) -> Optional[int]:
        """Extract Retry-After header value."""
        retry_after = response.headers.get('Retry-After')
        if retry_after:
            try:
                return int(retry_after)
            except ValueError:
                pass
        
        try:
            error_data = response.json()
            if 'retry_after' in error_data:
                return int(error_data['retry_after'])
        except:
            pass
        
        return None

    def _http_create(self, obj_type: str, payload: Dict[str, Any], 
                     domain_name: Optional[str] = None,
                     api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Low-level HTTP CREATE operation with domain-aware routing and per-call API key.
        
        Args:
            obj_type: Object type
            payload: Object data
            domain_name: Domain name (optional, uses default_domain if not provided)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            Response data or None
        """
        domain = domain_name or self._default_domain
        endpoint = f"{self.base_url}/{domain}/{obj_type}"
        
        try:
            safe_serialize_to_json(payload, obj_type)
            
            response = self._make_request('POST', endpoint, api_key=api_key, json=payload)
            if response and response.status_code == 201:
                try:
                    return self._unwrap_response(response.json())
                except json.JSONDecodeError as e:
                    raise JSONDeserializationError(
                        f"Invalid JSON response from server",
                        obj_type=obj_type,
                        original_error=e
                    )
            elif response:
                error_msg = self._extract_error_message(response)
                self.logger.error(f"HTTP create failed: {response.status_code} - {error_msg}")
                # Raise specific exceptions based on status code
                if response.status_code == 400:
                    raise ValueError(f"Bad request for {obj_type}: {error_msg}")
                elif response.status_code == 422:
                    raise ValueError(f"Validation failed for {obj_type}: {error_msg}")
                elif response.status_code == 409:
                    raise ValueError(f"{obj_type} already exists: {error_msg}")
                else:
                    raise RuntimeError(f"Failed to create {obj_type}: {error_msg}")
            return None
        except (SerializationError, JSONSerializationError, JSONDeserializationError):
            raise
        except (AuthenticationError, AuthorizationError, RateLimitError):
            raise
        except Exception as e:
            self.logger.error(f"HTTP create error for {obj_type}: {e}")
            raise

    def _http_read(self, obj_type: str, obj_id: str,
                   domain_name: Optional[str] = None,
                   api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Low-level HTTP READ operation with domain-aware routing and per-call API key.
        
        Args:
            obj_type: Object type
            obj_id: Object UUID
            domain_name: Domain name (optional, uses default_domain if not provided)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            Response data or None
        """
        domain = domain_name or self._default_domain
        endpoint = f"{self.base_url}/{domain}/{obj_type}/{obj_id}"
        
        try:
            response = self._make_request('GET', endpoint, api_key=api_key)
            if response and response.status_code == 200:
                try:
                    result = response.json()
                    result = self._unwrap_response(result)
                    return result
                except json.JSONDecodeError as e:
                    raise JSONDeserializationError(
                        f"Invalid JSON response from server",
                        obj_type=obj_type,
                        original_error=e
                    )
            elif response and response.status_code == 404:
                self.logger.debug(f"Object not found: {obj_type}/{obj_id}")
            elif response:
                self.logger.error(f"HTTP read failed: {response.status_code} - {response.text}")
            return None
        except (JSONDeserializationError, SerializationError):
            raise
        except (AuthenticationError, AuthorizationError, RateLimitError):
            raise
        except Exception as e:
            self.logger.error(f"HTTP read error for {obj_type}/{obj_id}: {e}")
            raise

    def _http_update(self, obj_type: str, obj_id: str, payload: Dict[str, Any],
                     domain_name: Optional[str] = None,
                     api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Low-level HTTP UPDATE operation with domain-aware routing and per-call API key.
        
        Args:
            obj_type: Object type
            obj_id: Object UUID
            payload: Update data
            domain_name: Domain name (optional, uses default_domain if not provided)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            Response data or None
            
        Raises:
            ValueError: For 400 Bad Request with error details
        """
        domain = domain_name or self._default_domain
        endpoint = f"{self.base_url}/{domain}/{obj_type}/{obj_id}"
        
        try:
            safe_serialize_to_json(payload, obj_type)
            
            response = self._make_request('PUT', endpoint, api_key=api_key, json=payload)
            if response and response.status_code == 200:
                try:
                    result = response.json()
                    result = self._unwrap_response(result)
                    return result
                except json.JSONDecodeError as e:
                    raise JSONDeserializationError(
                        f"Invalid JSON response from server",
                        obj_type=obj_type,
                        original_error=e
                    )
            elif response:
                # ✅ IMPROVED: Better error handling for 400 errors
                error_msg = response.text
                try:
                    error_data = response.json()
                    if isinstance(error_data, dict):
                        error_msg = error_data.get('error', error_data.get('message', error_msg))
                except:
                    pass
                
                self.logger.error(f"HTTP update failed: {response.status_code} - {error_msg}")
                
                # Raise exception with details for 400 errors
                if response.status_code == 400:
                    raise ValueError(f"Update validation failed: {error_msg}")
                    
            return None
        except (SerializationError, JSONSerializationError, JSONDeserializationError):
            raise
        except (AuthenticationError, AuthorizationError, RateLimitError):
            raise
        except ValueError:
            raise  # Re-raise our validation error
        except Exception as e:
            self.logger.error(f"HTTP update error for {obj_type}/{obj_id}: {e}")
            raise

    def _http_delete(self, obj_type: str, obj_id: str,
                     domain_name: Optional[str] = None,
                     api_key: Optional[str] = None) -> bool:
        """
        Low-level HTTP DELETE operation with domain-aware routing and per-call API key.
        
        Args:
            obj_type: Object type
            obj_id: Object UUID
            domain_name: Domain name (optional, uses default_domain if not provided)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            True if successful, False otherwise
        """
        domain = domain_name or self._default_domain
        endpoint = f"{self.base_url}/{domain}/{obj_type}/{obj_id}"
        
        try:
            response = self._make_request('DELETE', endpoint, api_key=api_key)
            if response and (response.status_code == 204 or response.status_code == 200 or response.status_code == 202):
                return True
            elif response:
                self.logger.error(f"HTTP delete failed: {response.status_code} - {response.text}")
            return False
        except (AuthenticationError, AuthorizationError, RateLimitError):
            raise
        except Exception as e:
            self.logger.error(f"HTTP delete error: {e}")
            raise

    def _http_list(self, obj_type: str, parent_id: str = None,
                   domain_name: Optional[str] = None,
                   api_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Low-level HTTP LIST operation with domain-aware routing and per-call API key.
        Uses : /{domain}/{obj_type}
        
        Args:
            obj_type: Object type
            parent_id: Optional parent UUID filter
            domain_name: Domain name (optional, uses default_domain if not provided)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            List of objects
        """
        domain = domain_name or self._default_domain
        endpoint = f"{self.base_url}/{domain}/{obj_type}"
        if parent_id:
            endpoint = f"{endpoint}?parent_id={parent_id}"

        self.logger.debug(f"<< _http_list : {endpoint}")
        
        try:
            response = self._make_request('GET', endpoint, api_key=api_key)
            if response and response.status_code == 200:
                try:
                    result = self._unwrap_response(response.json())
                except json.JSONDecodeError as e:
                    raise JSONDeserializationError(
                        f"Invalid JSON response from server",
                        obj_type=obj_type,
                        original_error=e
                    )
                
                self.logger.debug(f"List response for {obj_type}: {type(result)}")
                return result.get('objects') or []
            elif response:
                self.logger.error(f"HTTP list failed: {response.status_code} - {response.text}")
            return []
        except (JSONDeserializationError, SerializationError):
            raise
        except (AuthenticationError, AuthorizationError, RateLimitError):
            raise
        except Exception as e:
            self.logger.error(f"HTTP list error for {obj_type}: {e}")
            raise

    def _get_object_instance(self, obj_type: str, name: str, parent: Optional[Any] = None) -> Any:
        """Dynamically create object instance from available namespaces."""
        normalized_type = obj_type.replace('-', '_')
        class_name = inflection.camelize(normalized_type)
        
        # Try namespaces in priority order
        for namespace in SCHEMA_NAMESPACES:
            module_name = f"{namespace}.objects.{inflection.underscore(obj_type)}"
            
            try:
                if module_name not in self.module_cache:
                    self.logger.debug(f"Importing {module_name}")
                    self.module_cache[module_name] = importlib.import_module(module_name)
                
                module = self.module_cache[module_name]
                obj_class = getattr(module, class_name)
                
                # Found it!
                obj = obj_class.from_empty()
                obj.name = name
                
                if parent:
                    obj.parent_type = parent.obj_type
                    obj.parent_uuid = parent.uuid
                    obj.fq_name = parent.fq_name + [name]
                else:
                    obj.fq_name = [name]
                    obj.parent_type = "config-root"
                    obj.parent_uuid = ""
                
                if not hasattr(obj, 'uuid') or not obj.uuid:
                    import uuid as uuid_module
                    obj.uuid = str(uuid_module.uuid4())
                
                return obj
                
            except (ImportError, AttributeError):
                continue
        
        # Not found in any namespace
        raise ValueError(
            f"Schema '{class_name}' not found in {', '.join(SCHEMA_NAMESPACES)}. "
            f"Tried: {', '.join([f'{ns}.objects.{normalized_type}' for ns in SCHEMA_NAMESPACES])}"
        )

    def _hydrate_object(self, obj_type: str, data: Dict[str, Any]) -> Any:
        """Convert API response data back to object instance."""
        normalized_type = obj_type.replace('-', '_')
        class_name = inflection.camelize(normalized_type)
        
        # Try namespaces in priority order
        for namespace in SCHEMA_NAMESPACES:
            module_name = f"{namespace}.objects.{inflection.underscore(obj_type)}"
            
            try:
                if module_name not in self.module_cache:
                    self.module_cache[module_name] = importlib.import_module(module_name)
                
                obj_class = getattr(self.module_cache[module_name], class_name)
                return safe_deserialize_from_dict(data, obj_class, obj_type)
                
            except (ImportError, AttributeError):
                continue
        
        # Not found in any namespace
        raise ObjectDeserializationError(
            f"Schema '{class_name}' not found in {', '.join(SCHEMA_NAMESPACES)}. "
            f"Tried: {', '.join([f'{ns}.objects.{normalized_type}' for ns in SCHEMA_NAMESPACES])}",
            obj_type=obj_type
        )

    def create_object(self, obj_type: str, name: str, parent: Optional[Any] = None, 
                     params: Dict[str, Any] = None, refs: Dict[str, Any] = None, 
                     ignore_exists = True, domain_name: Optional[str] = None,
                     api_key: Optional[str] = None) -> Optional[Any]:
        """
        Create a new object with high-level interface, domain-aware routing, and per-call API key.
        
        Args:
            obj_type: Object type
            name: Object name
            parent: Parent object
            params: Object parameters
            refs: Object references
            ignore_exists: If True, return existing object instead of error
            domain_name: Domain name (optional, uses default_domain if not provided)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            Created object or None
        """
        if params is None:
            params = {}
        if refs is None:
            refs = {}
        
        domain = domain_name or self._default_domain
        self.logger.info(f"Creating {obj_type} '{name}' in domain '{domain}' with parent: {parent.obj_type if parent else 'None'}")
        
        try:
            if ignore_exists and parent:
                obj = self.read_object(obj_type, fq_name=parent.get_fq_name() + [name], 
                                      domain_name=domain, api_key=api_key)
                if obj:
                    return obj

            obj = self._get_object_instance(obj_type, name, parent)
            self.logger.warning(
                f"🔍 BEFORE serialization - {obj_type}: "
                f"name={getattr(obj, 'name', 'N/A')}, "
                f"fq_name={getattr(obj, 'fq_name', 'N/A')}, "
                f"parent_type={getattr(obj, 'parent_type', 'N/A')}"
            )

            for key, value in params.items():
                normalized_key = key.replace('-', '_')
                setattr(obj, normalized_key, value)
                self.logger.debug(f"Set attribute {normalized_key}={value}")
            
            if refs:
                self._add_object_refs(obj, refs)

            try:
                payload = safe_serialize_to_dict(obj, obj_type)
            except (ObjectSerializationError, SerializationError) as e:
                self.logger.error(f"Failed to serialize {obj_type} '{name}': {e}")
                raise

            # ✅ ADD THIS DEBUG LOGGING:
            self.logger.warning(
                f"🔍 AFTER serialization - {obj_type}: "
                f"payload keys={list(payload.keys())}, "
                f"name={payload.get('name')}, "
                f"fq_name={payload.get('fq_name')}, "
                f"parent_type={payload.get('parent_type')}"
            )

            
            result = self._http_create(obj_type, payload, domain_name=domain, api_key=api_key)
            
            if not result:
                self.logger.error(f"Create operation failed for {obj_type} '{name}', may be it exists already")
                return None

            normalized_type = obj_type.replace('-', '_')
            response_data = result.get(normalized_type)
            if not response_data or 'uuid' not in response_data:
                self.logger.error(f"Invalid create response: missing UUID")
                return None
                
            uuid = response_data['uuid']
            self.logger.info(f"Created {obj_type} '{name}' with UUID: {uuid}")

            for attempt in range(5):
                try:
                    read_result = self.read_object(obj_type, uuid=uuid, domain_name=domain, api_key=api_key)
                    if read_result:
                        self.logger.info(f"Successfully read back {obj_type}/{uuid}")
                        return read_result
                    time.sleep(0.5)
                except Exception as e:
                    self.logger.warning(f"Read-back attempt {attempt + 1} failed: {e}")
                    if attempt < 4:
                        time.sleep(0.5)
            
            self.logger.error(f"Failed to read back {obj_type}/{uuid} after creation")
            return uuid
            
        except (SerializationError, ObjectSerializationError, ObjectDeserializationError):
            raise
        except Exception as e:
            self.logger.error(f"Error creating {obj_type} '{name}': {str(e)}", exc_info=True)
            return None

    def read_object(self, obj_type: str, uuid: str = None, fq_name: Union[str, List[str]] = None,
                    domain_name: Optional[str] = None,
                    api_key: Optional[str] = None) -> Optional[Any]:
        """
        Read an object by UUID or fully qualified name with domain-aware routing and per-call API key.
        
        Args:
            obj_type: Object type
            uuid: Object UUID
            fq_name: Fully qualified name (list or string)
            domain_name: Domain name (optional, uses default_domain if not provided)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            Object instance or None
        """
        if not uuid and fq_name is None:
            self.logger.error("Either 'uuid' or 'fq_name' must be provided for read operation")
            return None
        
        if uuid and fq_name is not None:
            self.logger.error("Only one of 'uuid' or 'fq_name' should be provided, not both")
            return None
        
        domain = domain_name or self._default_domain
        
        try:
            if fq_name is not None:
                if isinstance(fq_name, list):
                    if not fq_name:
                        self.logger.error("fq_name list cannot be empty")
                        return None
                    
                    fq_name_str = ":".join(fq_name)
                    self.logger.debug(f"Converting fq_name {fq_name} (list) to UUID for {obj_type}")
                else:
                    if not fq_name.strip():
                        self.logger.error("fq_name string cannot be empty")
                        return None
                        
                    fq_name_str = fq_name
                    self.logger.debug(f"Converting fq_name '{fq_name}' (string) to UUID for {obj_type}")
                
                uuid = self.fq_name_to_uuid(obj_type, fq_name_str, domain_name=domain, api_key=api_key)
                if not uuid:
                    return None
            
            if not uuid:
                return None
            
            result = self._http_read(obj_type, uuid, domain_name=domain, api_key=api_key)
            if not result:
                return None
                
            normalized_type = obj_type.replace('-', '_')
            obj_data = result.get(normalized_type)
            if not obj_data:
                self.logger.error(f"Invalid read response: missing object data")
                return None
                
            return self._hydrate_object(obj_type, obj_data)
            
        except (SerializationError, ObjectDeserializationError, JSONDeserializationError):
            raise
        except Exception as e:
            if fq_name is not None:
                identifier = ":".join(fq_name) if isinstance(fq_name, list) else fq_name
            else:
                identifier = uuid
            self.logger.error(f"Error reading {obj_type}/{identifier}: {str(e)}", exc_info=True)
            return None

    def update_object(self, obj_type: str, uuid: str, params: Dict[str, Any] = None, 
                     add_refs: Dict[str, Any] = None, delete_refs: Dict[str, Any] = None,
                     domain_name: Optional[str] = None,
                     api_key: Optional[str] = None) -> Optional[Any]:
        """
        Update an existing object with domain-aware routing and per-call API key.
        
        Args:
            obj_type: Object type
            uuid: Object UUID
            params: Parameters to update
            add_refs: References to add
            delete_refs: References to delete
            domain_name: Domain name (optional, uses default_domain if not provided)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            Updated object or None
        """
        if params is None:
            params = {}
        if add_refs is None:
            add_refs = {}
        if delete_refs is None:
            delete_refs = {}
        
        domain = domain_name or self._default_domain
        self.logger.info(f"Updating {obj_type}/{uuid} in domain '{domain}'")
        
        try:
            obj = self.read_object(obj_type, uuid, domain_name=domain, api_key=api_key)
            if not obj:
                self.logger.error(f"Object {obj_type}/{uuid} not found for update")
                return None

            for key, value in params.items():
                normalized_key = key.replace('-', '_')
                setattr(obj, normalized_key, value)
            
            if add_refs:
                self._add_object_refs(obj, add_refs)
            if delete_refs:
                self._delete_object_refs(obj, delete_refs)

            try:
                payload = safe_serialize_to_dict(obj, obj_type)
            except (ObjectSerializationError, SerializationError) as e:
                self.logger.error(f"Failed to serialize {obj_type}/{uuid} for update: {e}")
                raise
                
            if 'uuid' in payload:
                del payload['uuid']
                
            result = self._http_update(obj_type, uuid, payload, domain_name=domain, api_key=api_key)
            if not result:
                return None
                
            self.logger.info(f"Successfully updated {obj_type}/{uuid}")
            return self.read_object(obj_type, uuid, domain_name=domain, api_key=api_key)
            
        except (SerializationError, ObjectSerializationError, ObjectDeserializationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating {obj_type}/{uuid}: {str(e)}", exc_info=True)
            return None

    def delete_object(self, obj_type: str, uuid: str, domain_name: Optional[str] = None,
                     api_key: Optional[str] = None) -> bool:
        """
        Delete an object by UUID with domain-aware routing and per-call API key.
        
        Args:
            obj_type: Object type
            uuid: Object UUID
            domain_name: Domain name (optional, uses default_domain if not provided)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            True if successful, False otherwise
        """
        domain = domain_name or self._default_domain
        self.logger.info(f"Deleting {obj_type}/{uuid} in domain '{domain}'")
        
        try:
            result = self._http_delete(obj_type, uuid, domain_name=domain, api_key=api_key)
            if result:
                self.logger.info(f"Successfully deleted {obj_type}/{uuid}")
            return result
        except Exception as e:
            self.logger.error(f"Error deleting {obj_type}/{uuid}: {str(e)}", exc_info=True)
            return False

    def list_objects(self, obj_type: str, parent_uuid: Optional[str] = None, domain_name: Optional[str] = None,
                    api_key: Optional[str] = None) -> List[Any]:
        """
        List all objects of given type and return as object instances with domain-aware routing and per-call API key.
        
        Args:
            obj_type: Object type
            domain_name: Domain name (optional, uses default_domain if not provided)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            List of object instances
        """
        domain = domain_name or self._default_domain
        self.logger.debug(f"Listing objects of type '{obj_type}' in domain '{domain}'")
        
        try:
            raw_objects = self._http_list(obj_type, parent_uuid, domain_name=domain, api_key=api_key)
            objects = []
            
            for obj_data in raw_objects:
                try:
                    obj = self._hydrate_object(obj_type, obj_data)
                    objects.append(obj)
                except (SerializationError, ObjectDeserializationError) as e:
                    self.logger.warning(f"Failed to hydrate {obj_type} object: {e}")
                    continue
                except Exception as e:
                    self.logger.warning(f"Failed to hydrate {obj_type} object: {e}")
                    continue
            
            self.logger.info(f"Listed {len(objects)} objects of type '{obj_type}'")
            return objects
            
        except (SerializationError, JSONDeserializationError):
            raise
        except Exception as e:
            self.logger.error(f"Error listing {obj_type} objects: {str(e)}", exc_info=True)
            return []


    def _http_query(self, json_data: str, domain_name: Optional[str] = None,
                   api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Low-level HTTP QUERY operation with domain-aware routing and per-call API key.
        
        Args:
            json_data: Query JSON string
            domain_name: Domain name (optional, uses default_domain if not provided)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            Query results or None
        """
        domain = domain_name or self._default_domain
        endpoint = f"{self.base_url}/{domain}/query"

        try:
            try:
                query_payload = json.loads(json_data)
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON data provided to query: {e}")
                raise ValueError(f"Invalid JSON data: {e}")

            response = self._make_request('POST', endpoint, api_key=api_key, json=query_payload)
            if response and response.status_code == 200:
                try:
                    result = response.json()
                    result = self._unwrap_response(result)
                    return result
                except json.JSONDecodeError as e:
                    raise JSONDeserializationError(
                        f"Invalid JSON response from query endpoint",
                        obj_type="query",
                        original_error=e
                    )
            elif response:
                self.logger.error(f"HTTP query failed: {response.status_code} - {response.text}")
            return None
        except (JSONDeserializationError, SerializationError):
            raise
        except (ValueError, TypeError):
            raise
        except Exception as e:
            self.logger.error(f"HTTP query error: {e}")
            raise

    def query(self, json_data: str, domain_name: Optional[str] = None,
             api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        High-level query operation with domain-aware routing and per-call API key.
        
        Args:
            json_data: Query JSON string
            domain_name: Domain name (optional, uses default_domain if not provided)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            Query results or None
        """
        return self._http_query(json_data, domain_name=domain_name, api_key=api_key)

    def _http_list_bulk(self, obj_type: str, obj_uuids: List[str] = None,
                        domain_name: Optional[str] = None,
                        api_key: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Low-level HTTP LIST-BULK operation with domain-aware routing and per-call API key.
        
        Args:
            obj_type: Object type
            obj_uuids: List of UUIDs to retrieve
            domain_name: Domain name (optional, uses default_domain if not provided)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            **kwargs: Additional parameters (detail, filters, etc.)
            
        Returns:
            List of objects
        """
        domain = domain_name or self._default_domain
        endpoint = f"{self.base_url}/{domain}/list-bulk"

        payload = {
            'type': obj_type,
            'detail': True
        }

        if obj_uuids:
            payload['obj_uuids'] = obj_uuids

        for key, value in kwargs.items():
            if value is not None:
                payload[key] = value

        try:
            self.logger.debug(f"List-bulk request for {obj_type} with {len(obj_uuids or [])} UUIDs")

            response = self._make_request('POST', endpoint, api_key=api_key, json=payload)
            if response and response.status_code == 200:
                try:
                    result = self._unwrap_response(response.json())
                except json.JSONDecodeError as e:
                    raise JSONDeserializationError(
                        f"Invalid JSON response from server",
                        obj_type=obj_type,
                        original_error=e
                    )
                self.logger.debug(f"List-bulk response for {obj_type}: {type(result)}")
                return result.get('objects') or []
            elif response:
                self.logger.error(f"HTTP list-bulk failed: {response.status_code} - {response.text}")
            return []

        except (JSONDeserializationError, SerializationError):
            raise
        except Exception as e:
            self.logger.error(f"HTTP list-bulk error for {obj_type}: {e}")
            raise

    def ref_update(self, from_type: str, from_uuid: str, to_type: str, to_uuid: str, 
                  to_fq_name: List[str], attr: Any, operation: str,
                  domain_name: Optional[str] = None,
                  api_key: Optional[str] = None) -> bool:
        """
        Update reference between objects with domain-aware routing and per-call API key.
        
        Args:
            from_type: Source object type
            from_uuid: Source object UUID
            to_type: Target object type
            to_uuid: Target object UUID
            to_fq_name: Target FQ name
            attr: Reference attributes
            operation: Operation (ADD/DELETE)
            domain_name: Domain name (optional, uses default_domain if not provided)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            True if successful, False otherwise
        """
        domain = domain_name or self._default_domain
        endpoint = f"{self.base_url}/{domain}/ref-update"
        payload = {
            'type': from_type,
            'uuid': from_uuid,
            'ref-type': to_type,
            'ref-uuid': to_uuid,
            'ref-fq-name': to_fq_name,
            'attr': attr,
            'operation': operation.upper()
        }

        self.logger.info(f"Reference {operation}: {from_type}/{from_uuid} -> {to_type}/{to_uuid}")
        
        try:
            response = self._make_request('PUT', endpoint, api_key=api_key, json=payload)
            if response and response.status_code == 200:
                self.logger.info(f"Reference {operation} successful")
                return True
            elif response:
                self.logger.error(f"Reference {operation} failed: {response.status_code} - {response.text}")
            return False
        except Exception as e:
            self.logger.error(f"Error in reference {operation}: {e}", exc_info=True)
            return False

    def ref_update_multi(self, ref_updates: List[Dict[str, Any]],
                        domain_name: Optional[str] = None,
                        api_key: Optional[str] = None) -> bool:
        """
        Update multiple references in single operation with domain-aware routing and per-call API key.
        
        Args:
            ref_updates: List of reference updates
            domain_name: Domain name (optional, uses default_domain if not provided)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            True if successful, False otherwise
        """
        if not ref_updates:
            self.logger.debug(f"No reference updates provided, no op")
            return True

        domain = domain_name or self._default_domain
        endpoint = f"{self.base_url}/{domain}/ref-update-multi"
        payload = {"refs": ref_updates}

        self.logger.info(f"Multi-reference update: {len(ref_updates)} operations")
        
        try:
            response = self._make_request('PUT', endpoint, api_key=api_key, json=payload)
            if response and response.status_code == 200:
                self.logger.info("Multi-reference update successful")
                return True
            elif response:
                self.logger.error(f"Multi-reference update failed: {response.status_code} - {response.text}")
            return False
        except Exception as e:
            self.logger.error(f"Error in multi-reference update: {e}", exc_info=True)
            return False

    def _add_object_refs(self, obj: Any, refs: Dict[str, List[Any]]) -> None:
        """Helper to add references to an object."""
        for key, values in refs.items():
            try:
                for ref in values:
                    add_method = f"add_{inflection.underscore(key)}_ref"
                    if hasattr(obj, add_method):
                        getattr(obj, add_method)(ref.uuid, ref.fq_name)
                        self.logger.debug(f"Added reference {key}: {ref.uuid}")
            except Exception as e:
                self.logger.error(f"Error adding references for {key}: {e}")

    def _delete_object_refs(self, obj: Any, refs: Dict[str, List[Any]]) -> None:
        """Helper to delete references from an object."""
        for key, values in refs.items():
            try:
                for ref in values:
                    del_method = f"del_{inflection.underscore(key)}_ref"
                    if hasattr(obj, del_method):
                        getattr(obj, del_method)(ref.uuid)
                        self.logger.debug(f"Deleted reference {key}: {ref.uuid}")
            except Exception as e:
                self.logger.error(f"Error deleting references for {key}: {e}")

    def fq_name_to_uuid(self, obj_type: str, fq_name: str,
                        domain_name: Optional[str] = None,
                        api_key: Optional[str] = None) -> Optional[str]:
        """
        Convert fully qualified name to UUID using POST request with domain-aware routing and per-call API key.
        
        Args:
            obj_type: Object type
            fq_name: Fully qualified name (colon-separated string)
            domain_name: Domain name (optional, uses default_domain if not provided)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            Object UUID or None
        """
        domain = domain_name or self._default_domain
        endpoint = f"{self.base_url}/{domain}/fq-name-to-uuid"
        payload = {
            'type': inflection.underscore(obj_type),
            'fq_name': fq_name
        }

        try:
            self.logger.debug(f"Converting fq_name to UUID: {obj_type} '{fq_name}' in domain '{domain}'")
            
            response = self._make_request('POST', endpoint, api_key=api_key, json=payload)
            
            if response is None:
                return None
                
            if response.status_code == 200:
                result = response.json()
                result = self._unwrap_response(result)
                uuid = result.get('uuid')
                if uuid:
                    self.logger.debug(f"fq_name to UUID conversion successful: {fq_name} -> {uuid}")
                    return uuid
                else:
                    return None
            elif response.status_code == 404:
                return None
            else:
                self.logger.error(f"fq_name lookup failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error in fq_name to UUID conversion: {e}", exc_info=True)
            return None

    def uuid_to_fq_name(self, obj_type: str, uuid: str,
                        domain_name: Optional[str] = None,
                        api_key: Optional[str] = None) -> Optional[List[str]]:
        """
        Convert UUID to fully qualified name using POST request with domain-aware routing and per-call API key.
        
        Args:
            obj_type: Object type
            uuid: Object UUID
            domain_name: Domain name (optional, uses default_domain if not provided)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            Fully qualified name as list or None
        """
        domain = domain_name or self._default_domain
        endpoint = f"{self.base_url}/{domain}/uuid-to-fq-name"
        payload = {
            'type': inflection.underscore(obj_type),
            'uuid': uuid
        }

        try:
            self.logger.debug(f"Converting UUID to fq_name: {obj_type} '{uuid}' in domain '{domain}'")

            response = self._make_request('POST', endpoint, api_key=api_key, json=payload)

            if response is None:
                return None

            if response.status_code == 200:
                result = response.json()
                result = self._unwrap_response(result)
                fq_name = result.get('fq_name')
                if fq_name:
                    self.logger.debug(f"UUID to fq_name conversion successful: {uuid} -> {fq_name}")
                    return fq_name
                else:
                    self.logger.warning(f"UUID to fq_name lookup failed: {obj_type}/{uuid}, server returned empty response with 200 code")
                    return None
            elif response.status_code == 404:
                return None
            else:
                self.logger.error(f"uuid lookup failed: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            self.logger.error(f"Error in UUID to fq_name conversion: {e}", exc_info=True)
            return None

    def _http_get_stats(self, obj_type: str, fields: Optional[List[str]] = None,
                        match: Optional[Dict] = None, domain_name: Optional[str] = None,
                        api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Low-level HTTP GET STATS operation with domain-aware routing and per-call API key.
        
        Args:
            obj_type: Object type
            fields: List of numeric field names (optional)
            match: Filter dict (optional)
            domain_name: Domain name (optional, uses default_domain if not provided)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            Stats data or None
        """
        domain = domain_name or self._default_domain
        endpoint = f"{self.base_url}/{domain}/{obj_type}/stats"
        
        params = {}
        if fields:
            params['fields'] = ','.join(fields) if isinstance(fields, list) else fields
        if match:
            params['match'] = json.dumps(match)
        
        try:
            self.logger.debug(f"Getting stats for {obj_type} in domain '{domain}'")
            
            response = self._make_request('GET', endpoint, api_key=api_key, params=params or None)
            
            if response and response.status_code == 200:
                try:
                    result = response.json()
                    result = self._unwrap_response(result)
                    return result
                except json.JSONDecodeError as e:
                    raise JSONDeserializationError(
                        f"Invalid JSON response from server",
                        obj_type=obj_type,
                        original_error=e
                    )
            elif response:
                self.logger.error(f"HTTP get stats failed: {response.status_code} - {response.text}")
            return None
            
        except (JSONDeserializationError, SerializationError):
            raise
        except (AuthenticationError, AuthorizationError, RateLimitError):
            raise
        except Exception as e:
            self.logger.error(f"HTTP get stats error for {obj_type}: {e}", exc_info=True)
            raise

    def get_stats(self, obj_type: str, fields: Optional[List[str]] = None,
                  match: Optional[Dict] = None, domain_name: Optional[str] = None,
                  api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        High-level get stats operation with domain-aware routing and per-call API key.
        
        Args:
            obj_type: Object type
            fields: List of numeric field names (optional)
            match: Filter dict (optional)
            domain_name: Domain name (optional, uses default_domain if not provided)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            Stats data or None
        """
        return self._http_get_stats(obj_type, fields=fields, match=match,
                                    domain_name=domain_name, api_key=api_key)

    def _http_aggregate(self, obj_type: str, pipeline: Optional[List[Dict]] = None,
                        match: Optional[Dict] = None, group_by: Optional[str] = None,
                        metrics: Optional[Dict] = None, sort: Optional[Dict] = None,
                        limit: Optional[int] = None, domain_name: Optional[str] = None,
                        api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Low-level HTTP AGGREGATE operation with domain-aware routing and per-call API key.
        
        Args:
            obj_type: Object type
            pipeline: Raw MongoDB pipeline (optional)
            match: Match filter (optional)
            group_by: Group by field (optional)
            metrics: Metrics dict (optional)
            sort: Sort specification (optional)
            limit: Result limit (optional)
            domain_name: Domain name (optional, uses default_domain if not provided)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            Aggregation results or None
        """
        domain = domain_name or self._default_domain
        endpoint = f"{self.base_url}/{domain}/{obj_type}/aggregate"
        
        body = {}
        if pipeline:
            body['pipeline'] = pipeline
        else:
            if match:
                body['match'] = match
            if group_by:
                body['group_by'] = group_by
            if metrics:
                body['metrics'] = metrics
            if sort:
                body['sort'] = sort
            if limit:
                body['limit'] = limit
        
        try:
            self.logger.debug(f"Aggregating {obj_type} in domain '{domain}'")
            
            response = self._make_request('POST', endpoint, api_key=api_key, json=body)
            
            if response and response.status_code == 200:
                try:
                    result = response.json()
                    result = self._unwrap_response(result)
                    return result
                except json.JSONDecodeError as e:
                    raise JSONDeserializationError(
                        f"Invalid JSON response from server",
                        obj_type=obj_type,
                        original_error=e
                    )
            elif response:
                error_msg = self._extract_error_message(response)
                self.logger.error(f"HTTP aggregate failed: {response.status_code} - {error_msg}")
            return None
            
        except (JSONDeserializationError, SerializationError):
            raise
        except (AuthenticationError, AuthorizationError, RateLimitError):
            raise
        except Exception as e:
            self.logger.error(f"HTTP aggregate error for {obj_type}: {e}", exc_info=True)
            raise

    def aggregate(self, obj_type: str, pipeline: Optional[List[Dict]] = None,
                  match: Optional[Dict] = None, group_by: Optional[str] = None,
                  metrics: Optional[Dict] = None, sort: Optional[Dict] = None,
                  limit: Optional[int] = None, domain_name: Optional[str] = None,
                  api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        High-level aggregate operation with domain-aware routing and per-call API key.
        
        Args:
            obj_type: Object type
            pipeline: Raw MongoDB pipeline (optional)
            match: Match filter (optional)
            group_by: Group by field (optional)
            metrics: Metrics dict (optional)
            sort: Sort specification (optional)
            limit: Result limit (optional)
            domain_name: Domain name (optional, uses default_domain if not provided)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            Aggregation results or None
        """
        return self._http_aggregate(obj_type, pipeline=pipeline, match=match,
                                    group_by=group_by, metrics=metrics, sort=sort,
                                    limit=limit, domain_name=domain_name, api_key=api_key)

    def _http_get_distinct(self, obj_type: str, field: str, match: Optional[Dict] = None,
                           limit: int = 1000, domain_name: Optional[str] = None,
                           api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Low-level HTTP GET DISTINCT operation with domain-aware routing and per-call API key.
        
        Args:
            obj_type: Object type
            field: Field name to get distinct values for
            match: Filter dict (optional)
            limit: Maximum values to return (default 1000, max 10000)
            domain_name: Domain name (optional, uses default_domain if not provided)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            Distinct values data or None
        """
        domain = domain_name or self._default_domain
        endpoint = f"{self.base_url}/{domain}/{obj_type}/distinct/{field}"
        
        params = {'limit': limit}
        if match:
            params['match'] = json.dumps(match)
        
        try:
            self.logger.debug(f"Getting distinct values for {obj_type}.{field} in domain '{domain}'")
            
            response = self._make_request('GET', endpoint, api_key=api_key, params=params)
            
            if response and response.status_code == 200:
                try:
                    result = response.json()
                    result = self._unwrap_response(result)
                    return result
                except json.JSONDecodeError as e:
                    raise JSONDeserializationError(
                        f"Invalid JSON response from server",
                        obj_type=obj_type,
                        original_error=e
                    )
            elif response:
                self.logger.error(f"HTTP get distinct failed: {response.status_code} - {response.text}")
            return None
            
        except (JSONDeserializationError, SerializationError):
            raise
        except (AuthenticationError, AuthorizationError, RateLimitError):
            raise
        except Exception as e:
            self.logger.error(f"HTTP get distinct error for {obj_type}.{field}: {e}", exc_info=True)
            raise

    def get_distinct(self, obj_type: str, field: str, match: Optional[Dict] = None,
                     limit: int = 1000, domain_name: Optional[str] = None,
                     api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        High-level get distinct values operation with domain-aware routing and per-call API key.
        
        Args:
            obj_type: Object type
            field: Field name to get distinct values for
            match: Filter dict (optional)
            limit: Maximum values to return (default 1000, max 10000)
            domain_name: Domain name (optional, uses default_domain if not provided)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            Distinct values data or None
        """
        return self._http_get_distinct(obj_type, field=field, match=match, limit=limit,
                                       domain_name=domain_name, api_key=api_key)

    def _http_get_count_by(self, obj_type: str, field: str, match: Optional[Dict] = None,
                           limit: int = 100, sort: str = '-count',
                           domain_name: Optional[str] = None,
                           api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Low-level HTTP GET COUNT-BY operation with domain-aware routing and per-call API key.
        
        Args:
            obj_type: Object type
            field: Field name to group by
            match: Filter dict (optional)
            limit: Maximum groups to return (default 100, max 1000)
            sort: Sort order - 'count', '-count', 'value', '-value' (default '-count')
            domain_name: Domain name (optional, uses default_domain if not provided)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            Count-by data or None
        """
        domain = domain_name or self._default_domain
        endpoint = f"{self.base_url}/{domain}/{obj_type}/count-by/{field}"
        
        params = {'limit': limit, 'sort': sort}
        if match:
            params['match'] = json.dumps(match)
        
        try:
            self.logger.debug(f"Getting count-by for {obj_type}.{field} in domain '{domain}'")
            
            response = self._make_request('GET', endpoint, api_key=api_key, params=params)
            
            if response and response.status_code == 200:
                try:
                    result = response.json()
                    result = self._unwrap_response(result)
                    return result
                except json.JSONDecodeError as e:
                    raise JSONDeserializationError(
                        f"Invalid JSON response from server",
                        obj_type=obj_type,
                        original_error=e
                    )
            elif response:
                self.logger.error(f"HTTP get count-by failed: {response.status_code} - {response.text}")
            return None
            
        except (JSONDeserializationError, SerializationError):
            raise
        except (AuthenticationError, AuthorizationError, RateLimitError):
            raise
        except Exception as e:
            self.logger.error(f"HTTP get count-by error for {obj_type}.{field}: {e}", exc_info=True)
            raise

    def get_count_by(self, obj_type: str, field: str, match: Optional[Dict] = None,
                     limit: int = 100, sort: str = '-count',
                     domain_name: Optional[str] = None,
                     api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        High-level get count-by operation with domain-aware routing and per-call API key.
        
        Args:
            obj_type: Object type
            field: Field name to group by
            match: Filter dict (optional)
            limit: Maximum groups to return (default 100, max 1000)
            sort: Sort order - 'count', '-count', 'value', '-value' (default '-count')
            domain_name: Domain name (optional, uses default_domain if not provided)
            api_key: Per-call API key override (optional, uses instance default if not provided)
            
        Returns:
            Count-by data or None
        """
        return self._http_get_count_by(obj_type, field=field, match=match, limit=limit,
                                       sort=sort, domain_name=domain_name, api_key=api_key)

    def health_check(self) -> bool:
        """Perform health check on API server."""
        try:
            endpoint = f"{self.base_url}/health"
            response = self._make_request('GET', endpoint)
            return response and response.status_code == 200
        except Exception:
            return False

    def close(self):
        """Close session and cleanup resources."""
        if hasattr(self, 'session'):
            self.session.close()
            self.logger.info("ApiClient session closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def create_api_client(server_ip: str = "localhost", port: int = 8082, **kwargs) -> ApiClient:
    """Utility function to create API client with common defaults."""
    return ApiClient(server_ip=server_ip, port=port, **kwargs)


def wait_for_api_server(server_ip: str, port: int, max_wait: int = 60) -> bool:
    """Wait for API server to become available."""
    import time
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            with ApiClient(server_ip, port, timeout=5) as client:
                if client.health_check():
                    return True
        except Exception:
            pass
        time.sleep(2)
    
    return False


def normalize_object_type(obj_type: str) -> str:
    """Normalize object type string (convert hyphens to underscores)."""
    return obj_type.replace('-', '_')


def get_class_name(obj_type: str) -> str:
    """Get Python class name from object type."""
    return inflection.camelize(normalize_object_type(obj_type))
