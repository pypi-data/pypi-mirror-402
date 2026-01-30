"""
Infinium SDK for Python.

A production-ready SDK for interacting with the Infinium Hosted MCP Bridge API.
"""

from .client import InfiniumClient
from .async_client import AsyncInfiniumClient
from .types import (
    AgentType, TaskData, ApiResponse, HealthCheck, BatchResult,
    TimeTracking, Customer, Support, Sales, Marketing, Content, Research,
    Project, Development, Executive, General
)
from .exceptions import (
    InfiniumError, AuthenticationError, ValidationError, RateLimitError,
    NetworkError, TimeoutError, ServerError, NotFoundError, BatchError,
    ConfigurationError
)
from .utils import (
    get_current_iso_datetime, validate_iso_datetime,
    validate_agent_type, validate_duration, setup_logging
)

__version__ = "1.0.0"
__author__ = "Infinium"
__email__ = "support@infinium.com"
__description__ = "Python SDK for Infinium Hosted MCP Bridge API"

__all__ = [
    # Main clients
    "InfiniumClient",
    "AsyncInfiniumClient",
    
    # Types
    "AgentType",
    "TaskData",
    "ApiResponse",
    "HealthCheck",
    "BatchResult",
    "TimeTracking",
    "Customer",
    "Support", 
    "Sales",
    "Marketing",
    "Content",
    "Research",
    "Project",
    "Development",
    "Executive",
    "General",
    
    # Exceptions
    "InfiniumError",
    "AuthenticationError",
    "ValidationError", 
    "RateLimitError",
    "NetworkError",
    "TimeoutError",
    "ServerError",
    "NotFoundError",
    "BatchError",
    "ConfigurationError",
    
    # Utilities
    "get_current_iso_datetime",
    "validate_iso_datetime",
    "validate_agent_type", 
    "validate_duration",
    "setup_logging",
]
