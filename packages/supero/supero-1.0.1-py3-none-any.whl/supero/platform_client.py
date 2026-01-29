"""
Platform Client - HTTP client for Platform UI API.

Handles all HTTP communication with Platform UI server.

ENHANCED v3.0:
- ✅ Multi-tenant context: Extracts domain/project/tenant from JWT
- ✅ base_url parameter: Cleaner API (recommended)
- ✅ Backward compatible: host/port still works (deprecated)
- ✅ URL normalization: Auto-adds /api/v1 if missing
- ✅ Context properties: domain_name, domain_uuid, project_uuid, tenant_uuid
- ✅ ALL v2.2 features preserved: streaming, uploads, retries, RBAC
"""

import json
import logging
import base64
import requests
from typing import Dict, Any, Optional, Iterator
from urllib.parse import urlparse, urlunparse


class PlatformClient:
    """
    Low-level HTTP client for Platform UI API.
    
    Handles:
    - HTTP requests (GET, POST, PUT, DELETE)
    - JWT token management
    - Multi-tenant context extraction (v3.0)
    - API key authentication (for RBAC)
    - Error handling
    - Response parsing
    - Streaming responses (for AI chat)
    - File uploads (for schemas/SDKs)

    Multi-Tenant Support (v3.0):
        Client automatically extracts context from JWT:
        - domain_name, domain_uuid
        - project_name, project_uuid
        - tenant_name, tenant_uuid
        - user_uuid, user_email, username, role

        Access via properties:
        >>> client.domain_uuid
        >>> client.project_uuid  # NEW
        >>> client.tenant_uuid   # NEW

    RBAC Support (v2.2):
        All methods accept optional headers parameter for per-call
        API key override, enabling multi-user server applications:

        >>> client = PlatformClient(base_url='https://api.supero.dev', jwt_token=admin_jwt)
        >>> 
        >>> # Per-call API key override
        >>> headers = {'X-API-Key': user_api_key}
        >>> client.get('/schemas', headers=headers)
    """
    
    def __init__(
        self,
        base_url: str = None,
        jwt_token: str = None,
        api_key: str = None,
        timeout: int = 30,
        verify_ssl: bool = False,
        max_retries: int = 3,
        # Backward compatibility
        host: str = None,
        port: int = None
    ):
        """
        Initialize Platform Client.
        
        Args:
            base_url: Base URL (e.g., 'https://api.supero.dev' or 'http://localhost:8083')
                     Port and /api/v1 auto-added if missing (RECOMMENDED)
            jwt_token: JWT authentication token
            api_key: Default API key for authentication (can be overridden per-call)
            timeout: Request timeout in seconds
            verify_ssl: Verify SSL certificates
            max_retries: Maximum retry attempts for failed requests
            host: [DEPRECATED] Hostname - use base_url instead
            port: [DEPRECATED] Port - use base_url instead

        Examples:
            >>> # NEW style (recommended)
            >>> client = PlatformClient(
            ...     base_url='https://api.supero.dev',
            ...     jwt_token='eyJ...'
            ... )
            
            >>> # OLD style (still works, deprecated)
            >>> client = PlatformClient(
            ...     host='api.supero.dev',
            ...     port=443,
            ...     jwt_token='eyJ...'
            ... )

        v3.0: Added base_url, multi-tenant context
        v2.2: Added api_key parameter for RBAC
        """
        self.logger = logging.getLogger(__name__)
        
        # ============================================
        # 1. HANDLE BACKWARD COMPATIBILITY (host/port → base_url)
        # ============================================
        if base_url is None:
            if host is None:
                # Default to production
                host = 'api.supero.dev'
                port = port or 443
            else:
                # User provided host, port optional
                port = port or 443
            
            # Build base_url from host/port
            protocol = "https" if port == 443 else "http"
            base_url = f"{protocol}://{host}:{port}"
            
            # Log deprecation warning
            self.logger.warning(
                f"host/port parameters are deprecated. "
                f"Please use base_url='{base_url}' instead."
            )
        
        # ============================================
        # 2. NORMALIZE BASE_URL (add /api/v1 if missing)
        # ============================================
        base_url = self._normalize_base_url(base_url)
        
        # ============================================
        # 3. STORE CONFIGURATION
        # ============================================
        self.base_url = base_url.rstrip('/')
        self.jwt_token = jwt_token
        self._default_api_key = api_key
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.max_retries = max_retries
        self.session = requests.Session()
        
        # ============================================
        # 4. SETUP RETRY ADAPTER (v2.2 - preserved)
        # ============================================
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # ============================================
        # 5. SET DEFAULT HEADERS
        # ============================================
        try:
            from . import __version__
            user_agent = f'Supero-SDK/{__version__}'
        except ImportError:
            user_agent = 'Supero-SDK/3.0.0'

        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': user_agent
        })
        
        # ============================================
        # 6. SET AUTHENTICATION
        # ============================================
        if jwt_token:
            self.set_jwt_token(jwt_token)
        
        if api_key:
            self.set_api_key(api_key)
        
        # ============================================
        # 7. PARSE JWT CONTEXT (NEW v3.0)
        # ============================================
        self._context = self._parse_jwt_context(jwt_token) if jwt_token else {}
        if self._context:
            self.logger.debug(
                f"Multi-tenant context extracted: domain={self.domain_name}, "
                f"project={self.project_uuid[:8] if self.project_uuid else None}..., "
                f"tenant={self.tenant_uuid[:8] if self.tenant_uuid else None}..."
            )
    
    # ============================================
    # URL NORMALIZATION (NEW v3.0)
    # ============================================
    
    def _normalize_base_url(self, base_url: str) -> str:
        """
        Normalize base_url by adding /api/v1 if missing.
        
        Args:
            base_url: Input URL (may or may not have /api/v1)
        
        Returns:
            Normalized URL with /api/v1 path
        
        Examples:
            >>> self._normalize_base_url('https://api.supero.dev')
            'https://api.supero.dev/api/v1'
            
            >>> self._normalize_base_url('http://localhost:8083')
            'http://localhost:8083/api/v1'
            
            >>> self._normalize_base_url('https://api.supero.dev/api/v1')
            'https://api.supero.dev/api/v1'
        """
        try:
            parsed = urlparse(base_url)
            path = parsed.path.rstrip('/')
            
            # If no path or just '/', add /api/v1
            if not path or path == '':
                path = '/api/v1'
            # If path doesn't start with /api, assume it's missing /api/v1
            elif not path.startswith('/api'):
                path = f'/api/v1{path}'
            
            # Reconstruct URL
            normalized = urlunparse((
                parsed.scheme,
                parsed.netloc,
                path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
            
            return normalized
            
        except Exception as e:
            self.logger.warning(f"Failed to normalize base_url '{base_url}': {e}")
            return base_url
    
    @property
    def host(self) -> str:
        """Extract hostname from base_url for backward compatibility."""
        try:
            parsed = urlparse(self.base_url)
            return parsed.hostname
        except:
            return 'api.supero.dev'
    
    @property
    def port(self) -> int:
        """Extract port from base_url for backward compatibility."""
        try:
            parsed = urlparse(self.base_url)
            return parsed.port or (443 if parsed.scheme == 'https' else 80)
        except:
            return 443
    
    # ============================================
    # TOKEN MANAGEMENT
    # ============================================
    
    def set_jwt_token(self, jwt_token: str):
        """Set JWT token for authentication."""
        self.jwt_token = jwt_token
        self.session.headers['Authorization'] = f'Bearer {jwt_token}'
        # v3.0: Refresh context when token changes
        self._context = self._parse_jwt_context(jwt_token) if jwt_token else {}
        self.logger.debug("JWT token set")
    
    def clear_jwt_token(self):
        """Clear JWT token."""
        self.jwt_token = None
        self.session.headers.pop('Authorization', None)
        # v3.0: Clear context
        self._context = {}
        self.logger.debug("JWT token cleared")

    def set_api_key(self, api_key: str):
        """
        Set default API key for authentication.

        Args:
            api_key: API key to use for all requests

        v2.2: API key support for RBAC
        """
        self._default_api_key = api_key
        self.session.headers['X-API-Key'] = api_key
        self.logger.debug("API key set")

    def clear_api_key(self):
        """
        Clear default API key.

        v2.2: API key support for RBAC
        """
        self._default_api_key = None
        self.session.headers.pop('X-API-Key', None)
        self.logger.debug("API key cleared")

    # ============================================
    # HTTP METHODS (v2.2 - preserved)
    # ============================================

    def _merge_headers(self, headers: Dict[str, str] = None) -> Dict[str, str]:
        """
        Merge per-call headers with session headers.

        Per-call headers take precedence over session defaults.

        Args:
            headers: Per-call headers to merge

        Returns:
            Merged headers dict

        v2.2: Helper method for RBAC
        """
        if not headers:
            return None
        
        merged = dict(self.session.headers)
        merged.update(headers)
        return merged

    def _make_request(
        self,
        method: str,
        endpoint: str,
        headers: Dict[str, str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Platform UI.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., '/auth/login')
            headers: Optional per-call headers (for RBAC api_key override)
            **kwargs: Additional request parameters
        
        Returns:
            Response JSON as dict
        
        Raises:
            ConnectionError: If connection fails
            AuthenticationError: If authentication fails
            AuthorizationError: If permission denied
            ValueError: For other HTTP errors

        v2.2: Added headers parameter for RBAC
        """
        url = f"{self.base_url}{endpoint}"
        
        # RBAC: Merge per-call headers with session headers
        request_headers = self._merge_headers(headers)
        
        try:
            self.logger.debug(f"{method} {url}")
            
            response = self.session.request(
                method,
                url,
                headers=request_headers,
                timeout=self.timeout,
                verify=self.verify_ssl,
                **kwargs
            )
            
            self.logger.debug(f"Response: {response.status_code}")
            
            # Handle errors
            if response.status_code == 401:
                raise AuthenticationError("Authentication failed - invalid or expired token")
            elif response.status_code == 403:
                raise AuthorizationError("Permission denied")
            elif response.status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            elif response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', response.text)
                except (ValueError, AttributeError):
                    error_msg = response.text if response.text else 'Unknown error'
                
                raise ValueError(f"HTTP {response.status_code}: {error_msg}")
            
            # Parse JSON response
            if response.text:
                return response.json()
            return {}
        
        except requests.exceptions.Timeout:
            raise ConnectionError(f"Request to {url} timed out after {self.timeout}s")
        
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(f"Failed to connect to Platform UI at {url}: {e}")
        
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Request failed: {e}")
    
    def get(
        self, 
        endpoint: str, 
        params: Dict = None,
        headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """HTTP GET request."""
        return self._make_request('GET', endpoint, headers=headers, params=params)
    
    def post(
        self,
        endpoint: str,
        json: Dict = None,
        data: Dict = None,
        files: Dict = None,
        headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """HTTP POST request."""
        return self._make_request('POST', endpoint, headers=headers, json=json, data=data, files=files)
    
    def put(
        self, 
        endpoint: str, 
        json: Dict = None,
        headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """HTTP PUT request."""
        return self._make_request('PUT', endpoint, headers=headers, json=json)
    
    def patch(
        self, 
        endpoint: str, 
        json: Dict = None,
        headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """HTTP PATCH request."""
        return self._make_request('PATCH', endpoint, headers=headers, json=json)
    
    def delete(
        self, 
        endpoint: str, 
        params: Dict = None,
        headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """HTTP DELETE request."""
        return self._make_request('DELETE', endpoint, headers=headers, params=params)
    
    def get_file(
        self, 
        endpoint: str,
        headers: Dict[str, str] = None
    ) -> requests.Response:
        """Download file from Platform UI."""
        url = f"{self.base_url}{endpoint}"
        request_headers = self._merge_headers(headers)
        
        try:
            response = self.session.get(
                url,
                headers=request_headers,
                timeout=self.timeout,
                verify=self.verify_ssl,
                stream=True
            )
            
            if response.status_code >= 400:
                try:
                    error_msg = response.json().get('error', response.text)
                except (ValueError, AttributeError):
                    error_msg = response.text if response.text else 'Unknown error'
                raise ValueError(f"HTTP {response.status_code}: {error_msg}")
            
            return response
        
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to download file: {e}")

    def upload_file(
        self,
        endpoint: str,
        file_path: str = None,
        file_content: bytes = None,
        filename: str = None,
        field_name: str = 'file',
        additional_data: Dict = None,
        headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Upload file to Platform UI."""
        url = f"{self.base_url}{endpoint}"

        # Prepare file
        if file_path:
            with open(file_path, 'rb') as f:
                file_content = f.read()
            if not filename:
                import os
                filename = os.path.basename(file_path)
        elif not file_content:
            raise ValueError("Either file_path or file_content is required")
        elif not filename:
            raise ValueError("filename is required when using file_content")

        files = {field_name: (filename, file_content)}
        data = additional_data or {}

        request_headers = self._merge_headers(headers)
        if request_headers:
            request_headers.pop('Content-Type', None)

        try:
            response = self.session.post(
                url,
                files=files,
                data=data,
                headers=request_headers,
                timeout=self.timeout,
                verify=self.verify_ssl
            )

            if response.status_code == 401:
                raise AuthenticationError("Authentication failed - invalid or expired token")
            elif response.status_code == 403:
                raise AuthorizationError("Permission denied")
            elif response.status_code >= 400:
                try:
                    error_msg = response.json().get('error', response.text)
                except (ValueError, AttributeError):
                    error_msg = response.text if response.text else 'Unknown error'
                raise ValueError(f"HTTP {response.status_code}: {error_msg}")

            if response.text:
                return response.json()
            return {}

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to upload file: {e}")

    def stream_request(
        self,
        method: str,
        endpoint: str,
        json_data: Dict = None,
        headers: Dict[str, str] = None,
        **kwargs
    ) -> Iterator[str]:
        """Make streaming HTTP request for Server-Sent Events (SSE)."""
        url = f"{self.base_url}{endpoint}"
        
        request_headers = dict(self.session.headers)
        if headers:
            request_headers.update(headers)
        request_headers["Accept"] = "text/event-stream"
        
        self.logger.debug(f"STREAM {method} {url}")
        
        try:
            with self.session.request(
                method,
                url,
                headers=request_headers,
                json=json_data,
                stream=True,
                timeout=self.timeout,
                verify=self.verify_ssl,
                **kwargs
            ) as response:
                if response.status_code == 401:
                    raise AuthenticationError("Authentication failed - invalid or expired token")
                elif response.status_code == 403:
                    raise AuthorizationError("Permission denied")
                elif response.status_code == 429:
                    raise RateLimitError("Rate limit exceeded")
                elif response.status_code >= 400:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('error', response.text)
                    except (ValueError, AttributeError):
                        error_msg = response.text if response.text else 'Unknown error'
                    raise ValueError(f"HTTP {response.status_code}: {error_msg}")
                
                # Process SSE stream
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        
                        if line_str.startswith('data: '):
                            data = line_str[6:]
                            
                            if data == '[DONE]':
                                break
                            
                            try:
                                chunk = json.loads(data)
                                if 'content' in chunk:
                                    yield chunk['content']
                                elif 'delta' in chunk and 'content' in chunk['delta']:
                                    yield chunk['delta']['content']
                                elif 'text' in chunk:
                                    yield chunk['text']
                            except json.JSONDecodeError:
                                yield data
                        
                        elif line_str.startswith('event: '):
                            event_type = line_str[7:]
                            self.logger.debug(f"SSE event: {event_type}")
        
        except requests.exceptions.Timeout:
            raise ConnectionError(f"Streaming request to {url} timed out after {self.timeout}s")
        
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(f"Failed to connect to Platform UI at {url}: {e}")
        
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Streaming request failed: {e}")

    def stream_post(
        self,
        endpoint: str,
        json_data: Dict = None,
        headers: Dict[str, str] = None
    ) -> Iterator[str]:
        """Convenience method for streaming POST requests."""
        return self.stream_request('POST', endpoint, json_data=json_data, headers=headers)

    # ============================================
    # MULTI-TENANT CONTEXT PROPERTIES (NEW v3.0)
    # ============================================
    
    def _parse_jwt_context(self, jwt_token: str) -> Dict[str, Any]:
        """
        Parse JWT token to extract multi-tenant context.
        
        Extracts:
        - domain_name, domain_uuid
        - project_name, project_uuid  (v3.0)
        - tenant_name, tenant_uuid    (v3.0)
        - user_uuid, user_email, username, role
        
        Args:
            jwt_token: JWT token string
        
        Returns:
            Dict with context or empty dict if parse fails
        """
        if not jwt_token:
            return {}
        
        try:
            parts = jwt_token.split('.')
            if len(parts) != 3:
                self.logger.warning("Invalid JWT format")
                return {}
            
            payload = parts[1]
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += '=' * padding
            
            decoded = base64.urlsafe_b64decode(payload)
            context = json.loads(decoded)
            
            return context
            
        except Exception as e:
            self.logger.warning(f"Failed to parse JWT context: {e}")
            return {}
    
    @property
    def domain_name(self) -> Optional[str]:
        """Get domain name from JWT context."""
        return self._context.get('domain_name')
    
    @property
    def domain_uuid(self) -> Optional[str]:
        """Get domain UUID from JWT context."""
        return self._context.get('domain_uuid')
    
    @property
    def project_name(self) -> Optional[str]:
        """Get project name from JWT context (v3.0 multi-tenant)."""
        return self._context.get('project_name')
    
    @property
    def project_uuid(self) -> Optional[str]:
        """Get project UUID from JWT context (v3.0 multi-tenant)."""
        return self._context.get('project_uuid')
    
    @property
    def tenant_name(self) -> Optional[str]:
        """Get tenant name from JWT context (v3.0 multi-tenant)."""
        return self._context.get('tenant_name')
    
    @property
    def tenant_uuid(self) -> Optional[str]:
        """Get tenant UUID from JWT context (v3.0 multi-tenant)."""
        return self._context.get('tenant_uuid')
    
    @property
    def user_uuid(self) -> Optional[str]:
        """Get user UUID from JWT context."""
        return self._context.get('user_uuid')
    
    @property
    def user_email(self) -> Optional[str]:
        """Get user email from JWT context."""
        return self._context.get('user_email')
    
    @property
    def username(self) -> Optional[str]:
        """Get username from JWT context."""
        return self._context.get('username')
    
    @property
    def role(self) -> Optional[str]:
        """Get user role from JWT context."""
        return self._context.get('role')
    
    def get_context(self) -> Dict[str, Any]:
        """Get complete context as dictionary."""
        return self._context.copy()

    def update_token(self, jwt_token: str):
        """
        Update JWT token and refresh context.

        Args:
            jwt_token: New JWT token

        Example:
            >>> client.update_token(new_jwt_token)
            >>> print(client.domain_name)  # Updated

        v3.0: Token update with context refresh
        """
        self.jwt_token = jwt_token
        self.session.headers['Authorization'] = f'Bearer {jwt_token}'
        self._context = self._parse_jwt_context(jwt_token) if jwt_token else {}
        self.logger.debug("JWT token updated, context refreshed")

    def clear_context(self):
        """
        Clear cached context (useful for testing).

        Example:
            >>> client.clear_context()
            >>> print(client.domain_name)  # None

        v3.0: Context cleanup
        """
        self._context = {}
        self.logger.debug("Context cleared")

    # ============================================
    # CONVENIENCE METHODS FOR API KEY (v2.2)
    # ============================================

    def with_api_key(self, api_key: str) -> 'PlatformClientWithKey':
        """
        Create a context for requests with a specific API key.

        Args:
            api_key: API key to use

        Returns:
            PlatformClientWithKey context wrapper

        Example:
            >>> with client.with_api_key(user_key) as user_client:
            ...     schemas = user_client.get('/schemas')
            ...     sdks = user_client.get('/sdks')
        """
        return PlatformClientWithKey(self, api_key)


class PlatformClientWithKey:
    """
    Wrapper that adds API key headers to all requests.

    v2.2: Added for RBAC convenience
    """

    def __init__(self, client: PlatformClient, api_key: str):
        self._client = client
        self._api_key = api_key
        self._headers = {'X-API-Key': api_key}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def get(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        return self._client.get(endpoint, params=params, headers=self._headers)

    def post(self, endpoint: str, json: Dict = None, data: Dict = None, files: Dict = None) -> Dict[str, Any]:
        return self._client.post(endpoint, json=json, data=data, files=files, headers=self._headers)

    def put(self, endpoint: str, json: Dict = None) -> Dict[str, Any]:
        return self._client.put(endpoint, json=json, headers=self._headers)

    def patch(self, endpoint: str, json: Dict = None) -> Dict[str, Any]:
        return self._client.patch(endpoint, json=json, headers=self._headers)

    def delete(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        return self._client.delete(endpoint, params=params, headers=self._headers)

    def get_file(self, endpoint: str) -> requests.Response:
        return self._client.get_file(endpoint, headers=self._headers)

    def upload_file(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        return self._client.upload_file(endpoint, headers=self._headers, **kwargs)

    def stream_post(self, endpoint: str, json_data: Dict = None) -> Iterator[str]:
        return self._client.stream_post(endpoint, json_data=json_data, headers=self._headers)


# Custom exceptions
class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class AuthorizationError(Exception):
    """Raised when permission is denied."""
    pass


class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        super().__init__(message)
        self.retry_after = retry_after
