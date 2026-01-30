"""
Synchronous client for Infinium API.
"""
from __future__ import annotations
import json
import time
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone
from dataclasses import asdict

import httpx

from .types import (
    AgentType, TaskData, ApiResponse, HealthCheck, BatchResult,
    TimeTracking, Customer, Support, Sales, Marketing, Content, Research,
    Project, Development, Executive, General
)
from .exceptions import (
    InfiniumError, AuthenticationError, ValidationError, RateLimitError,
    NetworkError, TimeoutError, ServerError, NotFoundError, BatchError
)
from .utils import (
    validate_agent_credentials, validate_iso_datetime,
    validate_agent_type, validate_duration, validate_required_field,
    get_current_iso_datetime, dataclass_to_dict, exponential_backoff,
    safe_json_loads, merge_dicts, RateLimiter
)


class InfiniumClient:
    """
    Synchronous client for Infinium API.
    
    Example:
        ```python
        from infinium import InfiniumClient, TaskData, AgentType
        
        client = InfiniumClient(
            agent_id="your-agent-id",
            agent_secret="your-agent-secret"
        )
        
        # Send a simple task
        response = client.send_task(
            name="Process customer inquiry",
            description="Handled customer question about pricing",
            duration=120.5,
            agent_type=AgentType.CUSTOMER_SUPPORT_ASSISTANT
        )
        
        # Send with additional data
        task_data = TaskData(
            name="Marketing campaign analysis",
            description="Analyzed Q3 campaign performance",
            current_datetime=client.get_current_iso_datetime(),
            duration=300.0,
            agent_type=AgentType.MARKETING_ASSISTANT
        )
        response = client.send_task_data(task_data)
        ```
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_secret: str,
        base_url: str = "https://api.i42m.ai/api/v1",
        timeout: float = 30.0,
        max_retries: int = 3,
        enable_rate_limiting: bool = True,
        requests_per_second: float = 10.0,
        user_agent: str = "infinium-python/1.0.0",
        enable_logging: bool = False,
        log_level: str = "INFO",
        verify_ssl: bool = True
    ):
        """
        Initialize the Infinium client.
        
        Args:
            agent_id: Your agent ID from Infinium
            agent_secret: Your agent secret from Infinium
            base_url: Base URL for the API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            enable_rate_limiting: Whether to enable client-side rate limiting
            requests_per_second: Rate limit for requests per second
            user_agent: User agent string
            enable_logging: Whether to enable SDK logging
            log_level: Log level (DEBUG, INFO, WARNING, ERROR)
            verify_ssl: Whether to verify SSL certificates (set to False for self-signed certs)
        """
        validate_agent_credentials(agent_id, agent_secret)
        
        self.agent_id = agent_id
        self.agent_secret = agent_secret
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.user_agent = user_agent
        self.verify_ssl = verify_ssl
        
        # Setup logging
        if enable_logging:
            logging.basicConfig(level=getattr(logging, log_level.upper()))
        
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting
        self.rate_limiter = RateLimiter(requests_per_second) if enable_rate_limiting else None
        
        # HTTP client
        self._client = httpx.Client(
            timeout=timeout,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            verify=verify_ssl
        )
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def close(self) -> None:
        """Close the HTTP client and cleanup resources."""
        if hasattr(self, '_client') and self._client is not None:
            try:
                self._client.close()
            except Exception as e:
                self.logger.warning(f"Error closing HTTP client: {e}")
            finally:
                self._client = None
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        return {
            "User-Agent": self.user_agent,
            "x-agent-id": self.agent_id,
            "x-agent-key": self.agent_secret,
            "Content-Type": "application/json",
        }
    
    def _handle_response(self, response: httpx.Response) -> ApiResponse:
        """Handle HTTP response and convert to ApiResponse."""
        try:
            data = response.json() if response.content else None
        except json.JSONDecodeError:
            data = None
        
        # Handle different status codes
        if response.status_code == 401:
            raise AuthenticationError(
                "Authentication failed. Check your agent_id and agent_secret.",
                status_code=response.status_code,
                details={"response_data": data}
            )
        elif response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise RateLimitError(
                f"Rate limit exceeded. Retry after {retry_after} seconds.",
                retry_after=retry_after,
                details={"response_data": data}
            )
        elif response.status_code == 404:
            raise NotFoundError(
                "Resource not found",
                details={"response_data": data}
            )
        elif 500 <= response.status_code < 600:
            raise ServerError(
                f"Server error: {response.status_code}",
                status_code=response.status_code,
                details={"response_data": data}
            )
        elif not response.is_success:
            error_msg = data.get("error", f"Request failed with status {response.status_code}") if data else f"Request failed with status {response.status_code}"
            raise InfiniumError(
                error_msg,
                status_code=response.status_code,
                details={"response_data": data}
            )
        
        return ApiResponse(
            success=True,
            status_code=response.status_code,
            message=data.get("message", "Success") if data else "Success",
            data=data
        )
    
    def _make_request(
        self,
        method: str,
        url: str,
        json_data: Optional[Dict[str, Any]] = None,
        max_retries: Optional[int] = None
    ) -> ApiResponse:
        """Make HTTP request with retries."""
        if max_retries is None:
            max_retries = self.max_retries
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                # Rate limiting
                if self.rate_limiter:
                    self.rate_limiter.acquire_sync()
                
                response = self._client.request(
                    method=method,
                    url=url,
                    headers=self._get_headers(),
                    json=json_data
                )
                
                return self._handle_response(response)
                
            except (httpx.TimeoutException, httpx.ConnectTimeout, httpx.ReadTimeout) as e:
                last_exception = TimeoutError(
                    f"Request timed out after {self.timeout} seconds",
                    timeout_duration=self.timeout
                )
            except (httpx.NetworkError, httpx.ConnectError) as e:
                last_exception = NetworkError(
                    f"Network error: {str(e)}",
                    original_error=e
                )
            except (RateLimitError, AuthenticationError, NotFoundError, ServerError) as e:
                # Don't retry these errors
                raise e
            except Exception as e:
                last_exception = InfiniumError(f"Unexpected error: {str(e)}")
            
            if attempt < max_retries:
                delay = exponential_backoff(attempt)
                self.logger.debug(f"Retry attempt {attempt + 1}/{max_retries} failed. Retrying in {delay:.2f}s")
                time.sleep(delay)
        
        raise last_exception
    
    def test_connection(self) -> HealthCheck:
        """
        Test connection to the API.
        
        Returns:
            HealthCheck object with connection status
            
        Raises:
            AuthenticationError: If authentication fails
            NetworkError: If network request fails
            InfiniumError: For other API errors
        """
        url = f"{self.base_url}/agents/{self.agent_id}/health"
        response = self._make_request("GET", url)
        
        if not response.data:
            raise InfiniumError("Empty response from health check")
        
        return HealthCheck(
            status=response.data.get("status", "unknown"),
            agent_name=response.data.get("agentName", "Unknown"),
            timestamp=response.data.get("timestamp", "Unknown")
        )
    
    def send_task(
        self,
        name: str,
        description: str,
        duration: Union[int, float],
        agent_type: Union[str, AgentType],
        current_datetime: Optional[str] = None,
        **kwargs
    ) -> ApiResponse:
        """
        Send a task to the API with simple parameters.
        
        Args:
            name: Task name
            description: Task description  
            duration: Task duration in seconds
            agent_type: Agent type
            current_datetime: ISO datetime string (auto-generated if not provided)
            **kwargs: Additional task sections (time_tracking, customer, etc.)
            
        Returns:
            ApiResponse with the result
            
        Raises:
            ValidationError: If validation fails
            AuthenticationError: If authentication fails
            RateLimitError: If rate limited
            NetworkError: If network request fails
            InfiniumError: For other API errors
        """
        # Validation
        validate_required_field(name, "name")
        validate_required_field(description, "description")
        validate_required_field(agent_type, "agent_type")
        
        validated_agent_type = validate_agent_type(agent_type)
        validated_duration = validate_duration(duration)
        
        if current_datetime is None:
            current_datetime = get_current_iso_datetime()
        elif not validate_iso_datetime(current_datetime):
            raise ValidationError("current_datetime must be a valid ISO 8601 string", field="current_datetime")
        
        # Build task data
        task_data = TaskData(
            name=name,
            description=description,
            current_datetime=current_datetime,
            duration=validated_duration,
            agent_type=validated_agent_type
        )
        
        # Add optional sections from kwargs
        for section_name in ['time_tracking', 'customer', 'support', 'sales', 'marketing', 
                           'content', 'research', 'project', 'development', 'executive', 'general']:
            if section_name in kwargs:
                setattr(task_data, section_name, kwargs[section_name])
        
        return self.send_task_data(task_data)
    
    def send_task_data(self, task_data: TaskData) -> ApiResponse:
        """
        Send a TaskData object to the API.
        
        Args:
            task_data: TaskData object containing all task information
            
        Returns:
            ApiResponse with the result
            
        Raises:
            ValidationError: If validation fails
            AuthenticationError: If authentication fails
            RateLimitError: If rate limited
            NetworkError: If network request fails
            InfiniumError: For other API errors
        """
        # Convert task data to API format
        payload = self._task_data_to_dict(task_data)
        
        url = f"{self.base_url}/agents/{self.agent_id}/trace"
        
        self.logger.info(f"Sending task '{task_data.name}' to {url}")
        
        response = self._make_request("POST", url, json_data=payload)
        
        self.logger.info(f"Task '{task_data.name}' sent successfully")
        
        return response
    
    def send_tasks_batch(self, tasks: List[TaskData], max_concurrent: int = 5) -> BatchResult:
        """
        Send multiple tasks in parallel (limited concurrency).
        
        Args:
            tasks: List of TaskData objects
            max_concurrent: Maximum number of concurrent requests
            
        Returns:
            BatchResult with success/failure counts and individual results
            
        Raises:
            ValidationError: If input validation fails
        """
        if not tasks:
            raise ValidationError("tasks list cannot be empty")
        
        if max_concurrent < 1:
            raise ValidationError("max_concurrent must be at least 1")
        
        results = []
        errors = []
        successful = 0
        failed = 0
        
        # Process in chunks
        for i in range(0, len(tasks), max_concurrent):
            chunk = tasks[i:i + max_concurrent]
            
            for task in chunk:
                try:
                    result = self.send_task_data(task)
                    results.append(result)
                    successful += 1
                except Exception as e:
                    error_msg = f"Task '{task.name}' failed: {str(e)}"
                    errors.append(error_msg)
                    results.append(ApiResponse(
                        success=False,
                        message=error_msg,
                        data={"task_name": task.name}
                    ))
                    failed += 1
                    self.logger.error(error_msg)
        
        return BatchResult(
            successful=successful,
            failed=failed,
            results=results,
            errors=errors
        )
    
    def get_interpreted_task_result(self, task_id: str) -> ApiResponse:
        """
        Get the AI-interpreted result for a task.
        
        Args:
            task_id: The task ID
            
        Returns:
            ApiResponse with the interpreted result
            
        Raises:
            ValidationError: If task_id is invalid
            AuthenticationError: If authentication fails
            NotFoundError: If task not found
            NetworkError: If network request fails
            InfiniumError: For other API errors
        """
        validate_required_field(task_id, "task_id")
        
        url = f"{self.base_url}/agents/{self.agent_id}/interpreted-result/{task_id}"
        return self._make_request("GET", url)
    
    def _task_data_to_dict(self, task_data: TaskData) -> Dict[str, Any]:
        """Convert TaskData to dictionary for API request."""
        result = {
            "name": task_data.name,
            "description": task_data.description,
            "current_datetime": task_data.current_datetime,
            "duration": task_data.duration,
            "agent_type": task_data.agent_type.value if isinstance(task_data.agent_type, AgentType) else task_data.agent_type,
        }
        
        # Add optional sections
        sections = [
            'time_tracking', 'customer', 'support', 'sales', 'marketing',
            'content', 'research', 'project', 'development', 'executive', 'general'
        ]
        
        for section_name in sections:
            section_data = getattr(task_data, section_name, None)
            if section_data is not None:
                section_dict = dataclass_to_dict(section_data)
                if section_dict:  # Only include non-empty sections
                    result.update(section_dict)
        
        return result
    
    @staticmethod
    def get_current_iso_datetime() -> str:
        """Get current datetime as ISO 8601 string."""
        return get_current_iso_datetime()
    
    @staticmethod
    def create_task_data(
        name: str,
        description: str,
        duration: Union[int, float],
        agent_type: Union[str, AgentType],
        current_datetime: Optional[str] = None,
        **sections
    ) -> TaskData:
        """
        Create a TaskData object with validation.
        
        Args:
            name: Task name
            description: Task description
            duration: Task duration
            agent_type: Agent type
            current_datetime: ISO datetime (auto-generated if not provided)
            **sections: Additional task sections
            
        Returns:
            TaskData object
        """
        if current_datetime is None:
            current_datetime = get_current_iso_datetime()
        
        return TaskData(
            name=name,
            description=description,
            current_datetime=current_datetime,
            duration=validate_duration(duration),
            agent_type=validate_agent_type(agent_type),
            **sections
        )
