"""
Custom exceptions for py_api_lib
Consolidated exception hierarchy with backward compatibility
"""


# ===== Base Exception Classes =====

class BaseError(Exception):
    """Legacy base exception - kept for backward compatibility"""
    pass


class ApiException(Exception):
    """
    Modern base exception for all API-related errors
    Use this for new code
    """
    
    def __init__(self, message, response=None, status_code=None):
        self.message = message
        self.response = response
        self.status_code = status_code or (response.status_code if response else None)
        super().__init__(self.message)
    
    def __str__(self):
        if self.status_code:
            return f"{self.__class__.__name__}: {self.message} (status: {self.status_code})"
        return f"{self.__class__.__name__}: {self.message}"


# ===== Authentication & Authorization Errors =====

class AuthenticationError(ApiException):
    """Raised when API key authentication fails (401)"""
    pass


class AuthorizationError(ApiException):
    """Raised when API key lacks required permissions (403)"""
    pass


class PermissionDenied(BaseError):
    """Legacy permission denied exception - kept for backward compatibility"""
    pass


# ===== Validation & Request Errors =====

class ValidationError(ApiException):
    """Validation error (400)"""
    pass


class BadRequest(BaseError):
    """Legacy bad request exception - kept for backward compatibility"""
    
    def __init__(self, status_code, content):
        self.status_code = status_code
        self.content = content
        super().__init__()
    
    def __str__(self):
        return f'HTTP Status: {self.status_code} Content: {self.content}'


# ===== Resource Errors =====

class NotFoundError(ApiException):
    """Resource not found (404)"""
    pass


class NoIdError(BaseError):
    """Raised when object has no ID or ID is unknown"""
    
    def __init__(self, unknown_id=None):
        self._unknown_id = unknown_id
        super().__init__()
    
    def __str__(self):
        if self._unknown_id:
            return f'Unknown id: {self._unknown_id}'
        return 'Object has no ID'


class ResourceExistsError(BaseError):
    """Raised when trying to create a resource that already exists"""
    
    def __init__(self, eexists_fq_name, eexists_id):
        self._eexists_fq_name = eexists_fq_name
        self._eexists_id = eexists_id
        super().__init__()
    
    def __str__(self):
        return f'FQ Name: {self._eexists_fq_name} exists already with ID: {self._eexists_id}'


class ConflictError(ApiException):
    """Resource conflict (409)"""
    pass


class ResourceTypeUnknownError(BaseError):
    """Raised when object type is unknown"""
    
    def __init__(self, obj_type):
        self._unknown_type = obj_type
        super().__init__()
    
    def __str__(self):
        return f'Unknown object type: {self._unknown_type}'


class RefsExistError(BaseError):
    """Raised when references exist and prevent deletion"""
    pass


class ResourceExhaustionError(BaseError):
    """Raised when resource limits are exceeded"""
    pass


class AmbiguousParentError(BaseError):
    """Raised when parent resource is ambiguous"""
    pass


# ===== Server & Service Errors =====

class ServerError(ApiException):
    """Server error (500+)"""
    pass


class ServiceUnavailableError(BaseError):
    """Raised when service is unavailable"""
    
    def __init__(self, code):
        self._reason_code = code
        super().__init__()
    
    def __str__(self):
        return f'Service unavailable time out due to: {self._reason_code}'


class HttpError(BaseError):
    """Generic HTTP error - kept for backward compatibility"""
    
    def __init__(self, status_code, content):
        self.status_code = status_code
        self.content = content
        super().__init__()
    
    def __str__(self):
        return f'HTTP Status: {self.status_code} Content: {self.content}'


# ===== Rate Limiting Errors =====

class RateLimitError(ApiException):
    """Raised when rate limit is exceeded (429)"""
    
    def __init__(self, message, response=None, retry_after=None):
        super().__init__(message, response)
        self.retry_after = retry_after


# ===== Network & Connection Errors =====

class NetworkError(ApiException):
    """Network-related error (connection, timeout, etc.)"""
    pass


class TimeOutError(BaseError):
    """Legacy timeout exception - kept for backward compatibility"""
    
    def __init__(self, code):
        self._reason_code = code
        super().__init__()
    
    def __str__(self):
        return f'Timed out due to: {self._reason_code}'


class TimeoutError(NetworkError):
    """Modern timeout error"""
    pass


class ConnectionError(NetworkError):
    """Connection error"""
    pass


# ===== Security & Encryption Errors =====

class EncryptionRequiredError(ApiException):
    """Raised when attempting to read/update encrypted data without encryption enabled"""
    pass


class NoUserAgentKey(BaseError):
    """Raised when user agent key is missing"""
    pass


class UnknownAuthMethod(BaseError):
    """Raised when authentication method is unknown"""
    pass


class InvalidSessionID(BaseError):
    """Raised when session ID is invalid"""
    pass


# ===== Message Queue Errors =====

class MaxRabbitPendingError(BaseError):
    """Raised when too many pending updates to RabbitMQ"""
    
    def __init__(self, npending):
        self._npending = npending
        super().__init__()
    
    def __str__(self):
        return f'Too many pending updates to RabbitMQ: {self._npending}'


# ===== Exception Hierarchy Summary =====
"""
Modern API Exceptions (inherit from ApiException):
- ApiException (base)
  ├── AuthenticationError (401)
  ├── AuthorizationError (403)
  ├── ValidationError (400)
  ├── NotFoundError (404)
  ├── ConflictError (409)
  ├── ServerError (500+)
  ├── RateLimitError (429)
  ├── EncryptionRequiredError
  └── NetworkError
      ├── TimeoutError
      └── ConnectionError

Legacy Exceptions (inherit from BaseError):
- BaseError (base)
  ├── ServiceUnavailableError
  ├── TimeOutError
  ├── BadRequest
  ├── NoIdError
  ├── MaxRabbitPendingError
  ├── ResourceExistsError
  ├── ResourceTypeUnknownError
  ├── PermissionDenied
  ├── RefsExistError
  ├── ResourceExhaustionError
  ├── NoUserAgentKey
  ├── UnknownAuthMethod
  ├── HttpError
  ├── AmbiguousParentError
  └── InvalidSessionID
"""
