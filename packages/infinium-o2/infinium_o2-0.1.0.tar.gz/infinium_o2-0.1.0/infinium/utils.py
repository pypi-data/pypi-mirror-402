"""
Utility functions for the Infinium SDK.
"""
from __future__ import annotations
import json
import time
import random
import asyncio
import threading
from typing import Any, Dict, Optional, Union, Callable, TypeVar
from datetime import datetime, timezone
from dataclasses import asdict, is_dataclass
import logging

from .exceptions import ValidationError
from .types import AgentType

T = TypeVar('T')

logger = logging.getLogger(__name__)


def validate_agent_credentials(agent_id: Optional[str], agent_secret: Optional[str]) -> None:
    """
    Validate agent credentials.
    
    Args:
        agent_id: The agent ID
        agent_secret: The agent secret
        
    Raises:
        ValidationError: If credentials are invalid
    """
    if not agent_id or not isinstance(agent_id, str) or not agent_id.strip():
        raise ValidationError("agent_id is required and must be a non-empty string", field="agent_id")
    
    if not agent_secret or not isinstance(agent_secret, str) or not agent_secret.strip():
        raise ValidationError("agent_secret is required and must be a non-empty string", field="agent_secret")
    
    # Additional security validation
    if len(agent_id.strip()) < 3:
        raise ValidationError("agent_id must be at least 3 characters long", field="agent_id")
    
    if len(agent_secret.strip()) < 8:
        raise ValidationError("agent_secret must be at least 8 characters long", field="agent_secret")


def validate_iso_datetime(datetime_str: str) -> bool:
    """
    Validate ISO 8601 datetime string.
    
    Args:
        datetime_str: The datetime string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(datetime_str, str) or not datetime_str.strip():
        return False
    
    try:
        # Handle Z suffix by replacing with +00:00
        normalized = datetime_str.strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        
        # Ensure it's a reasonable datetime (not too far in past/future)
        min_year = 1900
        max_year = 2100
        if dt.year < min_year or dt.year > max_year:
            return False
            
        return True
    except (ValueError, TypeError, OverflowError):
        return False


def validate_agent_type(agent_type: Union[str, AgentType]) -> AgentType:
    """
    Validate and convert agent type.
    
    Args:
        agent_type: The agent type to validate
        
    Returns:
        Validated AgentType enum
        
    Raises:
        ValidationError: If agent type is invalid
    """
    if isinstance(agent_type, AgentType):
        return agent_type
    
    if isinstance(agent_type, str):
        try:
            return AgentType(agent_type.upper())
        except ValueError:
            valid_types = ", ".join([t.value for t in AgentType])
            raise ValidationError(
                f"Invalid agent_type '{agent_type}'. Valid options: {valid_types}",
                field="agent_type"
            )
    
    raise ValidationError("agent_type must be a string or AgentType enum", field="agent_type")


def validate_duration(duration: Union[int, float]) -> float:
    """
    Validate task duration.
    
    Args:
        duration: The duration value
        
    Returns:
        Validated duration as float
        
    Raises:
        ValidationError: If duration is invalid
    """
    try:
        duration_float = float(duration)
        
        # Check for infinity and NaN first
        if not (duration_float == duration_float):  # NaN check
            raise ValidationError("duration cannot be NaN", field="duration")
        
        if duration_float == float('inf'):
            raise ValidationError("duration cannot be infinite", field="duration")
        
        if duration_float < 0:
            raise ValidationError("duration must be non-negative", field="duration")
        
        # Reasonable upper limit to prevent abuse (24 hours)
        max_duration = 24 * 60 * 60  # 86400 seconds
        if duration_float > max_duration:
            raise ValidationError(f"duration cannot exceed {max_duration} seconds (24 hours)", field="duration")
            
        return duration_float
    except (ValueError, TypeError):
        raise ValidationError("duration must be a number", field="duration")


def validate_required_field(value: Any, field_name: str) -> None:
    """
    Validate that a required field is present and non-empty.
    
    Args:
        value: The value to validate
        field_name: The name of the field
        
    Raises:
        ValidationError: If field is missing or empty
    """
    if value is None:
        raise ValidationError(f"{field_name} is required", field=field_name)
    
    if isinstance(value, str) and not value.strip():
        raise ValidationError(f"{field_name} cannot be empty", field=field_name)


def get_current_iso_datetime() -> str:
    """
    Get current datetime as ISO 8601 string.
    
    Returns:
        Current datetime in ISO format
    """
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def dataclass_to_dict(obj: Any) -> Dict[str, Any]:
    """
    Convert dataclass to dictionary, filtering None values recursively.
    
    Args:
        obj: The dataclass object
        
    Returns:
        Dictionary representation with None values filtered out
    """
    if obj is None:
        return {}
    
    if is_dataclass(obj):
        from dataclasses import fields
        result = {}
        
        # Process each field directly from the dataclass instance
        for field in fields(obj):
            value = getattr(obj, field.name)
            if value is not None:
                if is_dataclass(value):
                    # Recursively process nested dataclasses
                    nested = dataclass_to_dict(value)
                    if nested:  # Only include if not empty
                        result[field.name] = nested
                elif isinstance(value, (list, tuple)):
                    # Handle lists/tuples that might contain dataclasses
                    processed_list = []
                    for item in value:
                        if is_dataclass(item):
                            nested_item = dataclass_to_dict(item)
                            if nested_item:  # Only include non-empty items
                                processed_list.append(nested_item)
                        elif item is not None:
                            processed_list.append(item)
                    if processed_list:  # Only include non-empty lists
                        result[field.name] = processed_list
                else:
                    result[field.name] = value
        return result
    
    return obj if isinstance(obj, dict) else {}


def exponential_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True
) -> float:
    """
    Calculate exponential backoff delay.
    
    Args:
        attempt: The current attempt number (starting from 0)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        jitter: Whether to add random jitter
        
    Returns:
        Delay in seconds
    """
    delay = min(base_delay * (2 ** attempt), max_delay)
    
    if jitter:
        # Add ±25% jitter
        jitter_range = delay * 0.25
        delay += random.uniform(-jitter_range, jitter_range)
    
    return max(0, delay)


async def retry_with_backoff(
    func: Callable[[], T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,)
) -> T:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: The function to retry
        max_retries: Maximum number of retries
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exceptions: Tuple of exceptions to catch and retry
        
    Returns:
        Result of the function call
        
    Raises:
        The last exception if all retries are exhausted
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func()
            else:
                return func()
        except exceptions as e:
            last_exception = e
            
            if attempt == max_retries:
                break
            
            delay = exponential_backoff(attempt, base_delay, max_delay)
            logger.debug(f"Retry attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {delay:.2f}s")
            await asyncio.sleep(delay)
    
    raise last_exception


def safe_json_loads(json_str: Union[str, dict]) -> Optional[dict]:
    """
    Safely parse JSON string or return dict if already parsed.
    
    Args:
        json_str: JSON string or dict
        
    Returns:
        Parsed dict or None if parsing fails
    """
    if isinstance(json_str, dict):
        return json_str
    
    if isinstance(json_str, str):
        # Basic safety checks
        json_str = json_str.strip()
        if not json_str:
            return None
        
        # Prevent excessively large JSON strings (1MB limit)
        if len(json_str) > 1024 * 1024:
            logger.warning("JSON string exceeds 1MB limit, skipping parse")
            return None
        
        try:
            result = json.loads(json_str)
            return result if isinstance(result, dict) else None
        except (json.JSONDecodeError, ValueError, RecursionError):
            return None
    
    return None


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple dictionaries, filtering None values.
    
    Args:
        *dicts: Dictionaries to merge
        
    Returns:
        Merged dictionary
    """
    result = {}
    
    for d in dicts:
        if isinstance(d, dict):
            for key, value in d.items():
                if value is not None:
                    result[key] = value
    
    return result


def truncate_string(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """
    Truncate string to maximum length.
    
    Args:
        text: The text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncating
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def setup_logging(level: str = "INFO", format_string: Optional[str] = None) -> None:
    """
    Setup logging for the SDK.
    
    Args:
        level: Log level
        format_string: Custom format string
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        datefmt="%Y-%m-%d %H:%M:%S"
    )


class RateLimiter:
    """Thread-safe rate limiter using token bucket algorithm."""
    
    def __init__(self, requests_per_second: float = 10.0, burst_size: int = 20):
        if requests_per_second <= 0:
            raise ValueError("requests_per_second must be positive")
        if burst_size <= 0:
            raise ValueError("burst_size must be positive")
            
        self.requests_per_second = requests_per_second
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = time.time()
        self._lock = threading.Lock()  # Thread safety
    
    def acquire_sync(self) -> None:
        """
        Acquire a token synchronously, waiting if necessary.
        Thread-safe version for sync clients.
        """
        with self._lock:
            current_time = time.time()
            elapsed = current_time - self.last_update
            
            # Add tokens based on elapsed time
            self.tokens = min(
                self.burst_size,
                self.tokens + elapsed * self.requests_per_second
            )
            self.last_update = current_time
            
            if self.tokens >= 1:
                self.tokens -= 1
                return
            
            # Calculate wait time
            wait_time = (1 - self.tokens) / self.requests_per_second
            self.tokens = 0
        
        # Wait outside the lock to avoid blocking other threads
        if wait_time > 0:
            time.sleep(wait_time)
    
    async def acquire(self) -> None:
        """
        Acquire a token asynchronously, waiting if necessary.
        Thread-safe version for async clients.
        """
        with self._lock:
            current_time = time.time()
            elapsed = current_time - self.last_update
            
            # Add tokens based on elapsed time
            self.tokens = min(
                self.burst_size,
                self.tokens + elapsed * self.requests_per_second
            )
            self.last_update = current_time
            
            if self.tokens >= 1:
                self.tokens -= 1
                return
            
            # Calculate wait time
            wait_time = (1 - self.tokens) / self.requests_per_second
            self.tokens = 0
        
        # Wait outside the lock to avoid blocking other coroutines
        if wait_time > 0:
            await asyncio.sleep(wait_time)
