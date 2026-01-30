"""
Asynchronous client for Infinium API.
"""
from __future__ import annotations
import json
import asyncio
import logging
from typing import Any, Dict, List, Optional, Union

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
    get_current_iso_datetime, dataclass_to_dict, retry_with_backoff,
    safe_json_loads, merge_dicts, RateLimiter
)


class AsyncInfiniumClient:
    """
    Asynchronous client for Infinium API.
    
    Example:
        ```python
        import asyncio
        from infinium import AsyncInfiniumClient, TaskData, AgentType
        
        async def main():
            async with AsyncInfiniumClient(
                agent_id="your-agent-id",
                agent_secret="your-agent-secret"
            ) as client:
                # Send a simple task
                response = await client.send_task(
                    name="Process customer inquiry",
                    description="Handled customer question about pricing",
                    duration=120.5,
                    agent_type=AgentType.CUSTOMER_SUPPORT_ASSISTANT
                )
                
                # Send multiple tasks concurrently
                tasks = [
                    TaskData(
                        name=f"Task {i}",
                        description=f"Description {i}",
                        current_datetime=client.get_current_iso_datetime(),
                        duration=float(i * 10),
                        agent_type=AgentType.OTHER
                    )
                    for i in range(5)
                ]
                
                batch_result = await client.send_tasks_batch(tasks)
                print(f"Sent {batch_result.successful} tasks successfully")
        
        asyncio.run(main())
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
        log_level: str = "INFO"
    ):
        """
        Initialize the async Infinium client.
        
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
        """
        validate_agent_credentials(agent_id, agent_secret)
        
        self.agent_id = agent_id
        self.agent_secret = agent_secret
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.user_agent = user_agent
        
        # Setup logging
        if enable_logging:
            logging.basicConfig(level=getattr(logging, log_level.upper()))
        
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting
        self.rate_limiter = RateLimiter(requests_per_second) if enable_rate_limiting else None
        
        # HTTP client (will be initialized on first use)
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        await self._ensure_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure HTTP client is initialized."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
            )
        return self._client
    
    async def close(self) -> None:
        """Close the HTTP client and cleanup resources."""
        if self._client is not None and not self._client.is_closed:
            try:
                await self._client.aclose()
            except Exception as e:
                self.logger.warning(f"Error closing async HTTP client: {e}")
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
    
    async def _make_request(
        self,
        method: str,
        url: str,
        json_data: Optional[Dict[str, Any]] = None,
        max_retries: Optional[int] = None
    ) -> ApiResponse:
        """Make HTTP request with retries."""
        if max_retries is None:
            max_retries = self.max_retries
        
        client = await self._ensure_client()
        
        async def make_single_request():
            # Rate limiting
            if self.rate_limiter:
                await self.rate_limiter.acquire()
            
            response = await client.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                json=json_data
            )
            
            return self._handle_response(response)
        
        # Retry with exponential backoff
        return await retry_with_backoff(
            make_single_request,
            max_retries=max_retries,
            exceptions=(
                httpx.TimeoutException, httpx.ConnectTimeout, httpx.ReadTimeout,
                httpx.NetworkError, httpx.ConnectError, InfiniumError
            )
        )
    
    async def test_connection(self) -> HealthCheck:
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
        response = await self._make_request("GET", url)
        
        if not response.data:
            raise InfiniumError("Empty response from health check")
        
        return HealthCheck(
            status=response.data.get("status", "unknown"),
            agent_name=response.data.get("agentName", "Unknown"),
            timestamp=response.data.get("timestamp", "Unknown")
        )
    
    async def send_task(
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
        
        return await self.send_task_data(task_data)
    
    async def send_task_data(self, task_data: TaskData) -> ApiResponse:
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
        
        response = await self._make_request("POST", url, json_data=payload)
        
        self.logger.info(f"Task '{task_data.name}' sent successfully")
        
        return response
    
    async def send_tasks_batch(
        self, 
        tasks: List[TaskData], 
        max_concurrent: int = 5,
        fail_fast: bool = False
    ) -> BatchResult:
        """
        Send multiple tasks concurrently.
        
        Args:
            tasks: List of TaskData objects
            max_concurrent: Maximum number of concurrent requests
            fail_fast: If True, stop on first error
            
        Returns:
            BatchResult with success/failure counts and individual results
            
        Raises:
            ValidationError: If input validation fails
            BatchError: If fail_fast is True and any task fails
        """
        if not tasks:
            raise ValidationError("tasks list cannot be empty")
        
        if max_concurrent < 1:
            raise ValidationError("max_concurrent must be at least 1")
        
        # Use semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []
        errors = []
        successful = 0
        failed = 0
        
        async def send_single_task(task: TaskData) -> ApiResponse:
            async with semaphore:
                try:
                    result = await self.send_task_data(task)
                    nonlocal successful
                    successful += 1
                    return result
                except Exception as e:
                    nonlocal failed
                    failed += 1
                    error_msg = f"Task '{task.name}' failed: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)
                    
                    if fail_fast:
                        raise BatchError(
                            f"Batch operation failed on task '{task.name}': {str(e)}",
                            successful_count=successful,
                            failed_count=failed,
                            errors=errors
                        )
                    
                    return ApiResponse(
                        success=False,
                        message=error_msg,
                        data={"task_name": task.name}
                    )
        
        # Execute all tasks concurrently
        results = await asyncio.gather(
            *[send_single_task(task) for task in tasks],
            return_exceptions=not fail_fast
        )
        
        # Handle exceptions if not fail_fast
        if not fail_fast:
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    task_name = tasks[i].name if i < len(tasks) else "unknown"
                    error_msg = f"Task '{task_name}' failed: {str(result)}"
                    errors.append(error_msg)
                    processed_results.append(ApiResponse(
                        success=False,
                        message=error_msg,
                        data={"task_name": task_name}
                    ))
                    failed += 1
                else:
                    processed_results.append(result)
                    if result.success:
                        successful += 1
                    else:
                        failed += 1
            results = processed_results
        
        return BatchResult(
            successful=successful,
            failed=failed,
            results=results,
            errors=errors
        )
    
    async def get_interpreted_task_result(self, task_id: str) -> ApiResponse:
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
        return await self._make_request("GET", url)
    
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
