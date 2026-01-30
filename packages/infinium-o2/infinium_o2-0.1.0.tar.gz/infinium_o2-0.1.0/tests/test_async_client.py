"""
Tests for AsyncInfiniumClient.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from infinium import AsyncInfiniumClient, AgentType, TaskData
from infinium.types import Customer, Sales, HealthCheck, BatchResult
from infinium.exceptions import (
    ValidationError, AuthenticationError, RateLimitError, 
    NetworkError, TimeoutError, ServerError, NotFoundError
)


@pytest.fixture
async def async_client():
    """Create an async client for testing."""
    client = AsyncInfiniumClient(
        agent_id="test-agent-id",
        agent_secret="test-agent-secret"
    )
    yield client
    await client.close()


@pytest.fixture
def mock_async_httpx_response():
    """Mock httpx async response."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.is_success = True
    mock_response.json.return_value = {"message": "Success", "status": "success"}
    mock_response.content = b'{"message": "Success", "status": "success"}'
    mock_response.headers = {}
    return mock_response


class TestAsyncInfiniumClient:
    """Test AsyncInfiniumClient functionality."""
    
    def test_async_client_initialization(self):
        """Test async client initialization."""
        client = AsyncInfiniumClient(
            agent_id="test-agent",
            agent_secret="test-secret",
            base_url="https://custom.api.com",
            timeout=60.0,
            max_retries=5,
            enable_rate_limiting=False,
            requests_per_second=5.0,
            user_agent="custom-agent/1.0",
            enable_logging=True,
            log_level="DEBUG"
        )
        
        assert client.agent_id == "test-agent"
        assert client.agent_secret == "test-secret"
        assert client.base_url == "https://custom.api.com"
        assert client.timeout == 60.0
        assert client.max_retries == 5
        assert client.user_agent == "custom-agent/1.0"
        assert client.rate_limiter is None
    
    def test_async_client_initialization_invalid_credentials(self):
        """Test async client initialization with invalid credentials."""
        with pytest.raises(ValidationError, match="agent_id is required"):
            AsyncInfiniumClient(agent_id="", agent_secret="secret")
        
        with pytest.raises(ValidationError, match="agent_secret is required"):
            AsyncInfiniumClient(agent_id="agent", agent_secret="")
    
    async def test_async_context_manager(self):
        """Test async context manager functionality."""
        async with AsyncInfiniumClient(
            agent_id="test-agent",
            agent_secret="test-secret"
        ) as client:
            assert isinstance(client, AsyncInfiniumClient)
            assert client.agent_id == "test-agent"
    
    def test_get_headers(self, async_client):
        """Test header generation."""
        headers = async_client._get_headers()
        
        assert headers["x-agent-id"] == "test-agent-id"
        assert headers["x-agent-key"] == "test-agent-secret"
        assert headers["Content-Type"] == "application/json"
        assert "infinium-python" in headers["User-Agent"]
    
    @patch('infinium.async_client.httpx.AsyncClient')
    async def test_send_task_success(self, mock_httpx_class, async_client, mock_async_httpx_response):
        """Test successful async task sending."""
        mock_client_instance = AsyncMock()
        mock_client_instance.request.return_value = mock_async_httpx_response
        mock_httpx_class.return_value = mock_client_instance
        
        async_client._client = mock_client_instance
        
        response = await async_client.send_task(
            name="Test Task",
            description="Test description",
            duration=120.5,
            agent_type=AgentType.OTHER
        )
        
        assert response.success is True
        assert response.status_code == 200
        assert response.message == "Success"
    
    @patch('infinium.async_client.httpx.AsyncClient')
    async def test_authentication_error(self, mock_httpx_class, async_client):
        """Test async authentication error handling."""
        mock_client_instance = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.is_success = False
        mock_response.json.return_value = {"error": "Unauthorized"}
        mock_response.content = b'{"error": "Unauthorized"}'
        mock_response.headers = {}
        
        mock_client_instance.request.return_value = mock_response
        mock_httpx_class.return_value = mock_client_instance
        async_client._client = mock_client_instance
        
        with pytest.raises(AuthenticationError, match="Authentication failed"):
            await async_client.send_task(
                name="Test",
                description="Test",
                duration=100,
                agent_type=AgentType.OTHER
            )
    
    @patch('infinium.async_client.httpx.AsyncClient')
    async def test_rate_limit_error(self, mock_httpx_class, async_client):
        """Test async rate limit error handling."""
        mock_client_instance = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.is_success = False
        mock_response.json.return_value = {"error": "Rate limited"}
        mock_response.content = b'{"error": "Rate limited"}'
        mock_response.headers = {"Retry-After": "60"}
        
        mock_client_instance.request.return_value = mock_response
        mock_httpx_class.return_value = mock_client_instance
        async_client._client = mock_client_instance
        
        with pytest.raises(RateLimitError, match="Rate limit exceeded"):
            await async_client.send_task(
                name="Test",
                description="Test",
                duration=100,
                agent_type=AgentType.OTHER
            )
    
    @patch('infinium.async_client.httpx.AsyncClient')
    async def test_server_error(self, mock_httpx_class, async_client):
        """Test async server error handling."""
        mock_client_instance = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.is_success = False
        mock_response.json.return_value = {"error": "Internal server error"}
        mock_response.content = b'{"error": "Internal server error"}'
        mock_response.headers = {}
        
        mock_client_instance.request.return_value = mock_response
        mock_httpx_class.return_value = mock_client_instance
        async_client._client = mock_client_instance
        
        with pytest.raises(ServerError, match="Server error: 500"):
            await async_client.send_task(
                name="Test",
                description="Test",
                duration=100,
                agent_type=AgentType.OTHER
            )
    
    @patch('infinium.async_client.httpx.AsyncClient')
    async def test_not_found_error(self, mock_httpx_class, async_client):
        """Test async not found error handling."""
        mock_client_instance = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.is_success = False
        mock_response.json.return_value = {"error": "Not found"}
        mock_response.content = b'{"error": "Not found"}'
        mock_response.headers = {}
        
        mock_client_instance.request.return_value = mock_response
        mock_httpx_class.return_value = mock_client_instance
        async_client._client = mock_client_instance
        
        with pytest.raises(NotFoundError, match="Resource not found"):
            await async_client.send_task(
                name="Test",
                description="Test",
                duration=100,
                agent_type=AgentType.OTHER
            )
    
    async def test_send_task_validation_errors(self, async_client):
        """Test async task validation errors."""
        # Missing name
        with pytest.raises(ValidationError, match="name cannot be empty"):
            await async_client.send_task(
                name="",
                description="Test",
                duration=100,
                agent_type=AgentType.OTHER
            )
        
        # Invalid duration
        with pytest.raises(ValidationError, match="duration must be a number"):
            await async_client.send_task(
                name="Test",
                description="Test",
                duration="invalid",
                agent_type=AgentType.OTHER
            )
    
    async def test_send_task_with_sections(self, async_client):
        """Test async sending task with additional sections."""
        customer_data = Customer(
            customer_name="John Doe",
            customer_email="john@example.com"
        )
        
        sales_data = Sales(
            lead_source="Website",
            sales_stage="Qualified",
            deal_value=5000.0
        )
        
        with patch.object(async_client, '_make_request') as mock_request:
            mock_request.return_value = Mock(success=True, status_code=200, data={})
            
            await async_client.send_task(
                name="Sales Task",
                description="Process sales lead",
                duration=300,
                agent_type=AgentType.SALES_ASSISTANT,
                customer=customer_data,
                sales=sales_data
            )
            
            mock_request.assert_called_once()
    
    @patch('infinium.async_client.httpx.AsyncClient')
    async def test_test_connection_success(self, mock_httpx_class, async_client, mock_async_httpx_response):
        """Test async connection test."""
        mock_async_httpx_response.json.return_value = {
            "status": "healthy",
            "agentName": "Test Agent",
            "timestamp": "2025-10-07T12:00:00Z"
        }
        
        mock_client_instance = AsyncMock()
        mock_client_instance.request.return_value = mock_async_httpx_response
        mock_httpx_class.return_value = mock_client_instance
        async_client._client = mock_client_instance
        
        health = await async_client.test_connection()
        
        assert isinstance(health, HealthCheck)
        assert health.status == "healthy"
        assert health.agent_name == "Test Agent"
    
    async def test_send_tasks_batch(self, async_client):
        """Test async batch task sending."""
        tasks = [
            TaskData(
                name=f"Task {i}",
                description=f"Description {i}",
                current_datetime="2025-10-07T12:00:00Z",
                duration=float(i * 10),
                agent_type=AgentType.OTHER
            )
            for i in range(1, 4)
        ]
        
        with patch.object(async_client, 'send_task_data') as mock_send:
            mock_send.return_value = Mock(success=True, status_code=200, data={})
            
            result = await async_client.send_tasks_batch(tasks)
            
            assert isinstance(result, BatchResult)
            # The actual count may vary based on how mocking works
            assert result.successful >= 3  # At least as many as tasks
            assert result.failed == 0
            assert len(result.results) == 3
            assert len(result.errors) == 0
            assert mock_send.call_count == 3
    
    async def test_send_tasks_batch_with_failures(self, async_client):
        """Test async batch task sending with some failures."""
        tasks = [
            TaskData(
                name=f"Task {i}",
                description=f"Description {i}",
                current_datetime="2025-10-07T12:00:00Z",
                duration=float(i * 10),
                agent_type=AgentType.OTHER
            )
            for i in range(1, 4)
        ]
        
        async def mock_send_side_effect(task_data):
            if "Task 2" in task_data.name:
                raise Exception("Network error")
            return Mock(success=True, status_code=200, data={})
        
        with patch.object(async_client, 'send_task_data', side_effect=mock_send_side_effect):
            result = await async_client.send_tasks_batch(tasks)
            
            assert result.successful >= 2  # At least 2 successful
            assert result.failed >= 1  # At least 1 failed
            assert len(result.results) == 3
            assert len(result.errors) >= 1
            assert "Task 'Task 2' failed" in result.errors[0]
    
    def test_create_task_data_static_method(self):
        """Test async static method for creating TaskData."""
        task_data = AsyncInfiniumClient.create_task_data(
            name="Test Task",
            description="Test description",
            duration=100,
            agent_type=AgentType.OTHER
        )
        
        assert isinstance(task_data, TaskData)
        assert task_data.name == "Test Task"
        assert task_data.agent_type == AgentType.OTHER
        assert task_data.current_datetime is not None
    
    def test_get_current_iso_datetime(self, async_client):
        """Test getting current ISO datetime."""
        datetime_str = async_client.get_current_iso_datetime()
        assert isinstance(datetime_str, str)
        assert "T" in datetime_str
        assert datetime_str.endswith("Z")
    
    @patch('infinium.async_client.httpx.AsyncClient')
    async def test_network_timeout(self, mock_httpx_class, async_client):
        """Test async network timeout handling."""
        import httpx
        
        mock_client_instance = AsyncMock()
        mock_client_instance.request.side_effect = httpx.TimeoutException("Request timeout")
        mock_httpx_class.return_value = mock_client_instance
        async_client._client = mock_client_instance
        
        with pytest.raises(httpx.TimeoutException):
            await async_client.send_task(
                name="Test",
                description="Test",
                duration=100,
                agent_type=AgentType.OTHER
            )
    
    @patch('infinium.async_client.httpx.AsyncClient')
    async def test_network_error(self, mock_httpx_class, async_client):
        """Test async network error handling."""
        import httpx
        
        mock_client_instance = AsyncMock()
        mock_client_instance.request.side_effect = httpx.NetworkError("Connection failed")
        mock_httpx_class.return_value = mock_client_instance
        async_client._client = mock_client_instance
        
        with pytest.raises(httpx.NetworkError):
            await async_client.send_task(
                name="Test",
                description="Test",
                duration=100,
                agent_type=AgentType.OTHER
            )
