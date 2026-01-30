"""
Exception classes for the Infinium SDK.
"""
from typing import Optional, Any, Dict


class InfiniumError(Exception):
    """Base exception for all Infinium SDK errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class AuthenticationError(InfiniumError):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", status_code: Optional[int] = 401, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code, details)


class ValidationError(InfiniumError):
    """Raised when request validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, None, details)
        self.field = field


class RateLimitError(InfiniumError):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 429, details)
        self.retry_after = retry_after


class NetworkError(InfiniumError):
    """Raised when network-related errors occur."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, None, details)
        self.original_error = original_error


class TimeoutError(NetworkError):
    """Raised when requests timeout."""
    
    def __init__(self, message: str = "Request timed out", timeout_duration: Optional[float] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, None, details)
        self.timeout_duration = timeout_duration


class ServerError(InfiniumError):
    """Raised when server returns 5xx errors."""
    
    def __init__(self, message: str = "Server error", status_code: Optional[int] = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code, details)


class NotFoundError(InfiniumError):
    """Raised when a resource is not found."""
    
    def __init__(self, message: str = "Resource not found", resource_type: Optional[str] = None, resource_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 404, details)
        self.resource_type = resource_type
        self.resource_id = resource_id


class BatchError(InfiniumError):
    """Raised when batch operations fail."""
    
    def __init__(self, message: str, successful_count: int = 0, failed_count: int = 0, errors: Optional[list] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, None, details)
        self.successful_count = successful_count
        self.failed_count = failed_count
        self.errors = errors or []


class ConfigurationError(InfiniumError):
    """Raised when SDK configuration is invalid."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, None, details)
        self.config_key = config_key
