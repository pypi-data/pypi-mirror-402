"""
Test configuration and fixtures.
"""
import pytest
import httpx
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock

from infinium import InfiniumClient, AsyncInfiniumClient, AgentType, TaskData


@pytest.fixture
def agent_credentials():
    """Test agent credentials."""
    return {
        "agent_id": "test-agent-123",
        "agent_secret": "test-secret-456"
    }


@pytest.fixture
def client(agent_credentials):
    """Synchronous client for testing."""
    return InfiniumClient(
        agent_id=agent_credentials["agent_id"],
        agent_secret=agent_credentials["agent_secret"],
        enable_rate_limiting=False  # Disable for tests
    )


@pytest.fixture
def async_client(agent_credentials):
    """Asynchronous client for testing."""
    return AsyncInfiniumClient(
        agent_id=agent_credentials["agent_id"],
        agent_secret=agent_credentials["agent_secret"],
        enable_rate_limiting=False  # Disable for tests
    )


@pytest.fixture
def sample_task_data():
    """Sample task data for testing."""
    return TaskData(
        name="Test Task",
        description="A test task for unit testing",
        current_datetime="2025-10-07T12:00:00Z",
        duration=120.5,
        agent_type=AgentType.OTHER
    )


@pytest.fixture
def mock_success_response():
    """Mock successful API response."""
    return {
        "status": "success",
        "message": "Task sent successfully",
        "data": {
            "task_id": "task-123",
            "created_at": "2025-10-07T12:00:00Z"
        }
    }


@pytest.fixture
def mock_health_response():
    """Mock health check response."""
    return {
        "status": "healthy",
        "agentName": "Test Agent",
        "timestamp": "2025-10-07T12:00:00Z"
    }


@pytest.fixture
def mock_httpx_response(mock_success_response):
    """Mock httpx response."""
    response = Mock(spec=httpx.Response)
    response.status_code = 200
    response.is_success = True
    response.json.return_value = mock_success_response
    response.content = b'{"status": "success"}'
    response.headers = {}
    return response


@pytest.fixture
def mock_httpx_client(mock_httpx_response):
    """Mock httpx client."""
    client = Mock(spec=httpx.Client)
    client.request.return_value = mock_httpx_response
    client.close = Mock()
    return client


@pytest.fixture
def mock_async_httpx_client(mock_httpx_response):
    """Mock async httpx client."""
    client = AsyncMock(spec=httpx.AsyncClient)
    client.request.return_value = mock_httpx_response
    client.aclose = AsyncMock()
    client.is_closed = False
    return client


# Utility functions for tests
def create_task_data(**kwargs) -> TaskData:
    """Create task data with default values."""
    defaults = {
        "name": "Test Task",
        "description": "Test description",
        "current_datetime": "2025-10-07T12:00:00Z",
        "status": "Pass",
        "duration": 100.0,
        "agent_type": AgentType.OTHER
    }
    defaults.update(kwargs)
    return TaskData(**defaults)


def assert_api_request(mock_client, method: str, url: str, expected_headers: Dict[str, Any] = None):
    """Assert that an API request was made with expected parameters."""
    mock_client.request.assert_called_once()
    call_args = mock_client.request.call_args
    
    assert call_args[1]["method"] == method
    assert call_args[1]["url"] == url
    
    if expected_headers:
        for key, value in expected_headers.items():
            assert call_args[1]["headers"][key] == value
