"""
Tests for utils module.
"""
import pytest
import time
import logging
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from typing import Optional

from infinium.utils import (
    validate_agent_credentials, validate_iso_datetime, normalize_status,
    validate_agent_type, validate_duration, validate_required_field,
    get_current_iso_datetime, dataclass_to_dict, exponential_backoff,
    safe_json_loads, merge_dicts, RateLimiter, setup_logging, truncate_string,
    retry_with_backoff
)
from infinium.types import AgentType, TaskData, Customer
from infinium.exceptions import ValidationError


class TestUtilsFunctions:
    """Test utility functions."""
    
    def test_validate_agent_credentials_valid(self):
        """Test valid agent credentials."""
        # Should not raise any exception
        validate_agent_credentials("valid-agent", "valid-secret")
    
    def test_validate_agent_credentials_invalid_agent_id(self):
        """Test invalid agent ID."""
        with pytest.raises(ValidationError, match="agent_id is required"):
            validate_agent_credentials("", "valid-secret")
        
        with pytest.raises(ValidationError, match="agent_id is required"):
            validate_agent_credentials(None, "valid-secret")
        
        with pytest.raises(ValidationError, match="agent_id is required"):
            validate_agent_credentials("   ", "valid-secret")
    
    def test_validate_agent_credentials_invalid_agent_secret(self):
        """Test invalid agent secret."""
        with pytest.raises(ValidationError, match="agent_secret is required"):
            validate_agent_credentials("valid-agent", "")
        
        with pytest.raises(ValidationError, match="agent_secret is required"):
            validate_agent_credentials("valid-agent", None)
        
        with pytest.raises(ValidationError, match="agent_secret is required"):
            validate_agent_credentials("valid-agent", "   ")
    
    def test_validate_iso_datetime_valid(self):
        """Test valid ISO datetime strings."""
        assert validate_iso_datetime("2025-10-07T12:00:00Z") is True
        assert validate_iso_datetime("2025-10-07T12:00:00+00:00") is True
        assert validate_iso_datetime("2025-10-07T12:00:00.123Z") is True
        assert validate_iso_datetime("2025-10-07T12:00:00-05:00") is True
    
    def test_validate_iso_datetime_invalid(self):
        """Test invalid ISO datetime strings."""
        assert validate_iso_datetime("invalid-date") is False
        assert validate_iso_datetime("2025-13-01T12:00:00Z") is False
        assert validate_iso_datetime("2025-10-32T12:00:00Z") is False
        assert validate_iso_datetime("2025-10-07T25:00:00Z") is False
        assert validate_iso_datetime("") is False
        assert validate_iso_datetime("   ") is False  # Whitespace only
        # Test None and non-string types
        assert validate_iso_datetime(None) is False
        assert validate_iso_datetime(123) is False
        assert validate_iso_datetime([]) is False
        # Test year boundaries
        assert validate_iso_datetime("1800-01-01T00:00:00Z") is False  # Too old
        assert validate_iso_datetime("2200-01-01T00:00:00Z") is False  # Too future
    
    def test_normalize_status_valid(self):
        """Test valid status normalization."""
        assert normalize_status("pass") == "Pass"
        assert normalize_status("PASS") == "Pass"
        assert normalize_status("Pass") == "Pass"
        assert normalize_status("passed") == "Pass"
        assert normalize_status("success") == "Pass"
        assert normalize_status("ok") == "Pass"
        assert normalize_status("completed") == "Pass"
        
        assert normalize_status("fail") == "Fail"
        assert normalize_status("FAIL") == "Fail"
        assert normalize_status("Fail") == "Fail"
        assert normalize_status("failed") == "Fail"
        assert normalize_status("error") == "Fail"
        assert normalize_status("failure") == "Fail"
    
    def test_normalize_status_invalid(self):
        """Test invalid status normalization."""
        with pytest.raises(ValidationError, match="Invalid status"):
            normalize_status("invalid")
        
        with pytest.raises(ValidationError, match="status must be a string"):
            normalize_status(123)
        
        with pytest.raises(ValidationError, match="status must be a string"):
            normalize_status(None)
    
    def test_validate_agent_type_valid(self):
        """Test valid agent type validation."""
        assert validate_agent_type(AgentType.OTHER) == AgentType.OTHER
        assert validate_agent_type("OTHER") == AgentType.OTHER
        assert validate_agent_type("other") == AgentType.OTHER
        assert validate_agent_type("SALES_ASSISTANT") == AgentType.SALES_ASSISTANT
        assert validate_agent_type("sales_assistant") == AgentType.SALES_ASSISTANT
    
    def test_validate_agent_type_invalid(self):
        """Test invalid agent type validation."""
        with pytest.raises(ValidationError, match="Invalid agent_type"):
            validate_agent_type("INVALID_TYPE")
        
        with pytest.raises(ValidationError, match="agent_type must be a string or AgentType enum"):
            validate_agent_type(123)
        
        with pytest.raises(ValidationError, match="agent_type must be a string or AgentType enum"):
            validate_agent_type(None)
    
    def test_validate_duration_valid(self):
        """Test valid duration validation."""
        assert validate_duration(100) == 100.0
        assert validate_duration(100.5) == 100.5
        assert validate_duration(0) == 0.0
        assert validate_duration("100") == 100.0
        assert validate_duration("100.5") == 100.5
    
    def test_validate_duration_invalid(self):
        """Test invalid duration validation."""
        with pytest.raises(ValidationError, match="duration must be non-negative"):
            validate_duration(-1)
        
        with pytest.raises(ValidationError, match="duration must be non-negative"):
            validate_duration(-100.5)
        
        with pytest.raises(ValidationError, match="duration must be a number"):
            validate_duration("invalid")
        
        with pytest.raises(ValidationError, match="duration must be a number"):
            validate_duration(None)
        
        # Test new validation rules
        with pytest.raises(ValidationError, match="duration cannot exceed"):
            validate_duration(25 * 60 * 60)  # 25 hours
        
        with pytest.raises(ValidationError, match="duration cannot be NaN"):
            validate_duration(float('nan'))
        
        with pytest.raises(ValidationError, match="duration cannot be infinite"):
            validate_duration(float('inf'))
    
    def test_validate_required_field_valid(self):
        """Test valid required field validation."""
        # Should not raise any exception
        validate_required_field("valid", "field_name")
        validate_required_field(123, "field_name")
        validate_required_field([], "field_name")
        validate_required_field({}, "field_name")
    
    def test_validate_required_field_invalid(self):
        """Test invalid required field validation."""
        with pytest.raises(ValidationError, match="field_name is required"):
            validate_required_field(None, "field_name")
        
        with pytest.raises(ValidationError, match="field_name cannot be empty"):
            validate_required_field("", "field_name")
        
        with pytest.raises(ValidationError, match="field_name cannot be empty"):
            validate_required_field("   ", "field_name")
    
    def test_get_current_iso_datetime(self):
        """Test getting current ISO datetime."""
        datetime_str = get_current_iso_datetime()
        assert isinstance(datetime_str, str)
        assert "T" in datetime_str
        assert datetime_str.endswith("Z")
        
        # Should be valid ISO format
        assert validate_iso_datetime(datetime_str) is True
    
    def test_dataclass_to_dict(self):
        """Test dataclass to dict conversion."""
        customer = Customer(
            customer_name="John Doe",
            customer_email="john@example.com",
            customer_phone=None
        )
        
        result = dataclass_to_dict(customer)
        assert isinstance(result, dict)
        assert result["customer_name"] == "John Doe"
        assert result["customer_email"] == "john@example.com"
        assert "customer_phone" not in result  # None values should be excluded
        
        # Test None object
        result = dataclass_to_dict(None)
        assert result == {}
        
        # Test with regular dict (doesn't filter None values)
        regular_dict = {"key": "value", "none_key": None}
        result = dataclass_to_dict(regular_dict)
        assert result == {"key": "value", "none_key": None}  # Returns dict as-is
        
        # Test with non-dict, non-dataclass object
        result = dataclass_to_dict("string")
        assert result == {}
        
        result = dataclass_to_dict(123)
        assert result == {}
        
        # Test nested dataclass with proper recursive None filtering
        from dataclasses import dataclass
        
        @dataclass
        class EmptyNested:
            optional_field: Optional[str] = None
            another_field: Optional[int] = None
        
        @dataclass
        class WithNestedData:
            name: str
            empty_nested: EmptyNested
            filled_nested: EmptyNested
        
        # Create nested dataclasses - one empty, one with data
        empty_nested_obj = EmptyNested(optional_field=None, another_field=None)
        filled_nested_obj = EmptyNested(optional_field="value", another_field=42)
        
        with_nested = WithNestedData(name="test", empty_nested=empty_nested_obj, filled_nested=filled_nested_obj)
        result = dataclass_to_dict(with_nested)
        
        # Empty nested dataclass should be excluded, filled one should be included
        expected = {
            "name": "test", 
            "filled_nested": {"optional_field": "value", "another_field": 42}
        }
        assert result == expected
        assert "empty_nested" not in result  # Empty nested dataclass excluded
        
        # Test nested dataclass lists
        @dataclass
        class WithList:
            items: list
        
        nested_list = WithList(items=[
            EmptyNested(optional_field=None, another_field=None),  # Empty - should be excluded
            EmptyNested(optional_field="keep", another_field=None),  # Partial - should be included
            "regular_string",  # Non-dataclass - should be included
            None  # None - should be excluded
        ])
        
        result = dataclass_to_dict(nested_list)
        expected = {
            "items": [
                {"optional_field": "keep"},  # Only non-None fields
                "regular_string"
            ]
        }
        assert result == expected
    
    def test_exponential_backoff(self):
        """Test exponential backoff calculation."""
        # Test without jitter for predictable results
        assert exponential_backoff(0, jitter=False) == 1.0
        assert exponential_backoff(1, jitter=False) == 2.0
        assert exponential_backoff(2, jitter=False) == 4.0
        assert exponential_backoff(3, jitter=False) == 8.0
        
        # Test with max_delay
        assert exponential_backoff(10, max_delay=5.0, jitter=False) == 5.0
    
    def test_safe_json_loads_valid(self):
        """Test safe JSON loading with valid JSON."""
        assert safe_json_loads('{"key": "value"}') == {"key": "value"}
        # Function only returns dicts, not other types
        assert safe_json_loads('[]') is None  # List not dict  
        assert safe_json_loads('null') is None
        assert safe_json_loads('"string"') is None  # String not dict
        assert safe_json_loads('123') is None  # Number not dict
        
        # Test with dict input (covers line 275)
        existing_dict = {"already": "dict"}
        assert safe_json_loads(existing_dict) == {"already": "dict"}
        
        # Test with non-string, non-dict input (covers return None branch)
        assert safe_json_loads(123) is None
        assert safe_json_loads(None) is None
        assert safe_json_loads([1, 2, 3]) is None
    
    def test_safe_json_loads_invalid(self):
        """Test safe JSON loading with invalid JSON."""
        assert safe_json_loads('invalid json') is None
        assert safe_json_loads('{"incomplete":') is None
        assert safe_json_loads('') is None
        assert safe_json_loads(None) is None
    
    def test_merge_dicts(self):
        """Test dictionary merging."""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"b": 3, "c": 4}
        dict3 = {"c": 5, "d": 6}
        
        result = merge_dicts(dict1, dict2, dict3)
        assert result == {"a": 1, "b": 3, "c": 5, "d": 6}
        
        # Test with empty dicts
        assert merge_dicts({}, {"a": 1}) == {"a": 1}
        assert merge_dicts() == {}
        
        # Test with non-dict arguments (covers lines 300->299, 302->301)
        result = merge_dicts({"a": 1}, "not_a_dict", {"b": 2}, None, {"c": 3})
        assert result == {"a": 1, "b": 2, "c": 3}  # Non-dict args ignored
    
    def test_truncate_string(self):
        """Test truncate_string function."""
        # Test short string (no truncation needed) - covers line 320
        short_text = "Hello World"
        result = truncate_string(short_text, max_length=20)
        assert result == "Hello World"
        
        # Test long string (truncation needed) - covers line 322
        long_text = "This is a very long string that needs to be truncated"
        result = truncate_string(long_text, max_length=20)
        assert len(result) == 20
        assert result.endswith("...")
        assert result == "This is a very lo..."
        
        # Test custom suffix
        result = truncate_string(long_text, max_length=20, suffix="[...]")
        assert len(result) == 20
        assert result.endswith("[...]")
    
    def test_setup_logging(self):
        """Test logging setup."""
        # Test with default format_string (tests line 335)
        with patch('logging.basicConfig') as mock_basic_config:
            setup_logging(level="INFO")
            expected_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            mock_basic_config.assert_called_once_with(
                level=logging.INFO,
                format=expected_format,
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        
        # Test with custom format_string
        with patch('logging.basicConfig') as mock_basic_config:
            setup_logging(level="DEBUG", format_string="custom format")
            mock_basic_config.assert_called_once_with(
                level=logging.DEBUG,
                format="custom format",
                datefmt="%Y-%m-%d %H:%M:%S"
            )

    def test_retry_with_backoff(self):
        """Test retry_with_backoff function."""
        import asyncio
        
        # Test successful function (no retries needed)
        def success_func():
            return "success"
        
        async def async_success_func():
            return "async_success"
        
        # Test sync function success
        result = asyncio.run(retry_with_backoff(success_func))
        assert result == "success"
        
        # Test async function success  
        result = asyncio.run(retry_with_backoff(async_success_func))
        assert result == "async_success"
        
        # Test synchronous function that fails (covers sync exception handling)
        def sync_fail():
            raise RuntimeError("Sync failure")
        
        with pytest.raises(RuntimeError, match="Sync failure"):
            asyncio.run(retry_with_backoff(sync_fail, max_retries=1))
        
        # Test function that fails then succeeds
        call_count = 0
        def retry_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "finally_success"
        
        call_count = 0
        result = asyncio.run(retry_with_backoff(retry_func, max_retries=3))
        assert result == "finally_success"
        assert call_count == 3
        
        # Test function that always fails (exhausts retries)
        def fail_func():
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError, match="Always fails"):
            asyncio.run(retry_with_backoff(fail_func, max_retries=1))


class TestRateLimiter:
    """Test RateLimiter functionality."""
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter()
        assert limiter.requests_per_second == 10.0
        assert limiter.burst_size == 20
        assert limiter.tokens == 20
        
        limiter = RateLimiter(requests_per_second=5.0, burst_size=10)
        assert limiter.requests_per_second == 5.0
        assert limiter.burst_size == 10
        assert limiter.tokens == 10
        
        # Test validation
        with pytest.raises(ValueError, match="requests_per_second must be positive"):
            RateLimiter(requests_per_second=0)
        
        with pytest.raises(ValueError, match="burst_size must be positive"):
            RateLimiter(burst_size=0)
    
    @pytest.mark.asyncio
    async def test_rate_limiter_acquire(self):
        """Test rate limiter token acquisition."""
        limiter = RateLimiter(requests_per_second=10.0, burst_size=5)
        
        # Should be able to acquire immediately with available tokens
        start_time = time.time()
        await limiter.acquire()
        elapsed = time.time() - start_time
        assert elapsed < 0.1  # Should be near-instant
        assert limiter.tokens == 4
    
    def test_rate_limiter_acquire_sync(self):
        """Test synchronous rate limiter token acquisition."""
        limiter = RateLimiter(requests_per_second=10.0, burst_size=5)
        
        # Should be able to acquire immediately with available tokens
        start_time = time.time()
        limiter.acquire_sync()
        elapsed = time.time() - start_time
        assert elapsed < 0.1  # Should be near-instant
        assert limiter.tokens == 4
    
    @pytest.mark.asyncio 
    async def test_rate_limiter_token_replenishment(self):
        """Test that tokens are replenished over time."""
        limiter = RateLimiter(requests_per_second=10.0, burst_size=2)
        
        # Use up all tokens
        await limiter.acquire()
        await limiter.acquire()
        assert limiter.tokens == 0
        
        # Wait for token replenishment and try again
        # This will test the waiting mechanism
        start_time = time.time()
        await limiter.acquire()  # This should wait
        elapsed = time.time() - start_time
        assert elapsed >= 0.05  # Should have waited at least some time
    
    @pytest.mark.asyncio
    async def test_rate_limiter_different_rates(self):
        """Test rate limiter with different rates."""
        fast_limiter = RateLimiter(requests_per_second=20.0, burst_size=1)
        slow_limiter = RateLimiter(requests_per_second=1.0, burst_size=1)
        
        assert fast_limiter.requests_per_second == 20.0
        assert slow_limiter.requests_per_second == 1.0
