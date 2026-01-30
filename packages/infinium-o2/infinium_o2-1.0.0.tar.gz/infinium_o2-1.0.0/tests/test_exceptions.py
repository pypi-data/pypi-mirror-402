"""
Tests for exceptions module.
"""
import pytest
from infinium.exceptions import (
    InfiniumError, AuthenticationError, ValidationError, RateLimitError,
    NetworkError, TimeoutError, ServerError, NotFoundError, BatchError,
    ConfigurationError
)


class TestExceptions:
    """Test exception classes."""
    
    def test_infinium_error_basic(self):
        """Test basic InfiniumError."""
        error = InfiniumError("Test error")
        assert str(error) == "Test error"
        assert error.status_code is None
        assert error.details == {}  # defaults to empty dict
    
    def test_infinium_error_with_details(self):
        """Test InfiniumError with details."""
        details = {"key": "value", "error_code": 123}
        error = InfiniumError("Test error", status_code=400, details=details)
        assert str(error) == "Test error"
        assert error.status_code == 400
        assert error.details == details
    
    def test_authentication_error(self):
        """Test AuthenticationError."""
        error = AuthenticationError("Auth failed")
        assert str(error) == "Auth failed"
        assert isinstance(error, InfiniumError)
        
        error = AuthenticationError("Auth failed", status_code=401, details={"reason": "invalid_token"})
        assert error.status_code == 401
        assert error.details == {"reason": "invalid_token"}
    
    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError("Invalid input")
        assert str(error) == "Invalid input"
        assert isinstance(error, InfiniumError)
        assert error.field is None
        
        error = ValidationError("Field required", field="email")
        assert error.field == "email"
    
    def test_validation_error_with_field(self):
        """Test ValidationError with field specification."""
        error = ValidationError("Field is required", field="username")
        assert str(error) == "Field is required"
        assert error.field == "username"
        assert isinstance(error, InfiniumError)
    
    def test_rate_limit_error(self):
        """Test RateLimitError."""
        error = RateLimitError("Rate limit exceeded")
        assert str(error) == "Rate limit exceeded"
        assert isinstance(error, InfiniumError)
        assert error.retry_after is None
        
        error = RateLimitError("Rate limit exceeded", retry_after=60)
        assert error.retry_after == 60
    
    def test_rate_limit_error_with_retry_after(self):
        """Test RateLimitError with retry_after."""
        error = RateLimitError("Too many requests", retry_after=120, details={"host": "api.example.com"})
        assert str(error) == "Too many requests"
        assert error.retry_after == 120
        assert error.status_code == 429  # Set automatically
        assert isinstance(error, InfiniumError)
    
    def test_network_error(self):
        """Test NetworkError."""
        error = NetworkError("Connection failed")
        assert str(error) == "Connection failed"
        assert isinstance(error, InfiniumError)
        
        error = NetworkError("Connection failed", details={"host": "api.example.com"})
        assert error.details == {"host": "api.example.com"}
    
    def test_timeout_error(self):
        """Test TimeoutError."""
        error = TimeoutError("Request timeout")
        assert str(error) == "Request timeout"
        assert isinstance(error, InfiniumError)
        
        error = TimeoutError("Request timeout", details={"timeout": 30})
        assert error.details == {"timeout": 30}
    
    def test_server_error(self):
        """Test ServerError."""
        error = ServerError("Internal server error")
        assert str(error) == "Internal server error"
        assert isinstance(error, InfiniumError)
        
        error = ServerError("Internal server error", status_code=500)
        assert error.status_code == 500
    
    def test_not_found_error(self):
        """Test NotFoundError."""
        error = NotFoundError("Resource not found")
        assert str(error) == "Resource not found"
        assert isinstance(error, InfiniumError)
        
        error = NotFoundError("User not found", resource_type="user", resource_id="123", details={"user_id": 123})
        assert error.status_code == 404  # Set automatically
        assert error.resource_type == "user"
        assert error.resource_id == "123"
        assert error.details == {"user_id": 123}
    
    def test_batch_error(self):
        """Test BatchError."""
        error = BatchError("Batch operation failed")
        assert str(error) == "Batch operation failed"
        assert isinstance(error, InfiniumError)
        assert error.successful_count == 0
        assert error.failed_count == 0
        assert error.errors == []
        
        error = BatchError("Some items failed", successful_count=3, failed_count=2, errors=["error1", "error2"])
        assert error.successful_count == 3
        assert error.failed_count == 2
        assert error.errors == ["error1", "error2"]
    
    def test_batch_error_with_failed_items(self):
        """Test BatchError with detailed error information."""
        errors = ["Invalid data", "Duplicate entry"]
        error = BatchError("Batch processing failed", successful_count=3, failed_count=2, errors=errors, details={"total": 5})
        assert str(error) == "Batch processing failed"
        assert error.successful_count == 3
        assert error.failed_count == 2
        assert error.errors == errors
        assert error.details == {"total": 5}
        assert isinstance(error, InfiniumError)
    
    def test_configuration_error(self):
        """Test ConfigurationError."""
        error = ConfigurationError("Invalid configuration")
        assert str(error) == "Invalid configuration"
        assert isinstance(error, InfiniumError)
        
        error = ConfigurationError("Missing API key", details={"config_file": "settings.json"})
        assert error.details == {"config_file": "settings.json"}
    
    def test_exception_inheritance(self):
        """Test that all exceptions properly inherit from InfiniumError."""
        exceptions = [
            AuthenticationError("test"),
            ValidationError("test"),
            RateLimitError("test"),
            NetworkError("test"),
            TimeoutError("test"),
            ServerError("test"),
            NotFoundError("test"),
            BatchError("test"),
            ConfigurationError("test")
        ]
        
        for exc in exceptions:
            assert isinstance(exc, InfiniumError)
            assert isinstance(exc, Exception)
    
    def test_exception_string_representation(self):
        """Test string representation of exceptions."""
        error = InfiniumError("Base error", status_code=400, details={"key": "value"})
        assert str(error) == "Base error"
        
        # Test that the message is properly preserved
        error = ValidationError("Field validation failed", field="email")
        assert "Field validation failed" in str(error)
    
    def test_exception_with_none_values(self):
        """Test exceptions with None values."""
        error = InfiniumError("Test", status_code=None, details=None)
        assert error.status_code is None
        assert error.details == {}
        
        error = ValidationError("Test", field=None)
        assert error.field is None
        
        error = RateLimitError("Test", retry_after=None)
        assert error.retry_after is None
        
        error = BatchError("Test", errors=None)
        assert error.errors == []
    
    def test_exception_attributes_preserved(self):
        """Test that exception attributes are preserved."""
        details = {"error_code": "INVALID_INPUT", "field": "username"}
        error = ValidationError("Validation failed", field="username", details=details)
        
        assert error.field == "username"
        assert error.status_code is None  # ValidationError doesn't set status_code
        assert error.details == details
        assert str(error) == "Validation failed"
        
        # Test that we can access parent class attributes
        assert hasattr(error, 'status_code')
        assert hasattr(error, 'details')
    
    def test_raise_and_catch_exceptions(self):
        """Test raising and catching exceptions."""
        # Test raising and catching specific exception
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Test validation error", field="test_field")
        
        assert exc_info.value.field == "test_field"
        assert str(exc_info.value) == "Test validation error"
        
        # Test catching as base class
        with pytest.raises(InfiniumError):
            raise AuthenticationError("Auth failed")
        
        # Test catching as general Exception
        with pytest.raises(Exception):
            raise ServerError("Server error")
