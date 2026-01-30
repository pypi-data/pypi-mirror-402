"""
Tests for the synchronous client.
"""
import pytest
import time
import json
from unittest.mock import Mock, patch
import httpx

from infinium import InfiniumClient, AgentType, TaskData
from infinium.exceptions import (
    ValidationError, AuthenticationError, RateLimitError, 
    NetworkError, ServerError, NotFoundError, TimeoutError, InfiniumError
)


class TestInfiniumClient:
    """Test cases for InfiniumClient."""
    
    def test_client_initialization(self, agent_credentials):
        """Test client initialization with valid credentials."""
        client = InfiniumClient(
            agent_id=agent_credentials["agent_id"],
            agent_secret=agent_credentials["agent_secret"]
        )
        
        assert client.agent_id == agent_credentials["agent_id"]
        assert client.agent_secret == agent_credentials["agent_secret"]
        assert client.base_url == "https://api.i42m.ai"
        assert client.timeout == 30.0
        assert client.max_retries == 3
    
    def test_client_initialization_invalid_credentials(self):
        """Test client initialization with invalid credentials."""
        with pytest.raises(ValidationError, match="agent_id is required"):
            InfiniumClient(agent_id="", agent_secret="valid")
        
        with pytest.raises(ValidationError, match="agent_secret is required"):
            InfiniumClient(agent_id="valid", agent_secret="")
    
    def test_client_custom_config(self, agent_credentials):
        """Test client initialization with custom configuration."""
        client = InfiniumClient(
            agent_id=agent_credentials["agent_id"],
            agent_secret=agent_credentials["agent_secret"],
            base_url="https://custom.api.com",
            timeout=60.0,
            max_retries=5,
            requests_per_second=20.0,
            user_agent="custom-agent/1.0"
        )
        
        assert client.base_url == "https://custom.api.com"
        assert client.timeout == 60.0
        assert client.max_retries == 5
        assert client.user_agent == "custom-agent/1.0"
    
    def test_get_headers(self, client):
        """Test header generation."""
        headers = client._get_headers()
        
        expected_headers = {
            "User-Agent": "infinium-python/1.0.0",
            "x-agent-id": "test-agent-123",
            "x-agent-key": "test-secret-456",
            "Content-Type": "application/json"
        }
        
        assert headers == expected_headers
    
    @patch('infinium.client.httpx.Client')
    def test_send_task_success(self, mock_httpx_class, client, mock_httpx_response, mock_success_response):
        """Test successful task sending."""
        mock_client_instance = Mock()
        mock_client_instance.request.return_value = mock_httpx_response
        mock_httpx_class.return_value = mock_client_instance
        
        client._client = mock_client_instance
        
        response = client.send_task(
            name="Test Task",
            description="Test description",
            duration=120.5,
            agent_type=AgentType.OTHER
        )
        
        assert response.success is True
        assert response.status_code == 200
        assert response.data == mock_success_response
        
        # Verify request was made correctly
        mock_client_instance.request.assert_called_once()
        call_args = mock_client_instance.request.call_args
        assert call_args[1]["method"] == "POST"
        assert call_args[1]["url"] == "https://api.i42m.ai/agents/test-agent-123/trace"
    
    def test_send_task_validation_errors(self, client):
        """Test task validation errors."""
        # Missing name
        with pytest.raises(ValidationError, match="name cannot be empty"):
            client.send_task(
                name="",
                description="Test",
                duration=100,
                agent_type=AgentType.OTHER
            )
        
        # Invalid duration
        with pytest.raises(ValidationError, match="duration must be a number"):
            client.send_task(
                name="Test",
                description="Test",
                duration="invalid",
                agent_type=AgentType.OTHER
            )
    
    def test_send_task_with_sections(self, client):
        """Test sending task with additional sections."""
        from infinium.types import Customer, Sales
        
        customer_data = Customer(
            customer_name="John Doe",
            customer_email="john@example.com"
        )
        
        sales_data = Sales(
            lead_source="Website",
            sales_stage="Qualified",
            deal_value=5000.0
        )
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = Mock(success=True, status_code=200, data={})
            
            client.send_task(
                name="Sales Task",
                description="Process sales lead",
                duration=300,
                agent_type=AgentType.SALES_ASSISTANT,
                customer=customer_data,
                sales=sales_data
            )
            
            # Verify the payload includes the sections
            call_args = mock_request.call_args
            payload = call_args[1]["json_data"]
            
            assert payload["customer_name"] == "John Doe"
            assert payload["customer_email"] == "john@example.com"
            assert payload["lead_source"] == "Website"
            assert payload["sales_stage"] == "Qualified"
            assert payload["deal_value"] == 5000.0
    
    @patch('infinium.client.httpx.Client')
    def test_authentication_error(self, mock_httpx_class, client):
        """Test authentication error handling."""
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.is_success = False
        mock_response.json.return_value = {"error": "Unauthorized"}
        mock_response.content = b'{"error": "Unauthorized"}'
        mock_response.headers = {}
        
        mock_client_instance.request.return_value = mock_response
        mock_httpx_class.return_value = mock_client_instance
        client._client = mock_client_instance
        
        with pytest.raises(AuthenticationError, match="Authentication failed"):
            client.send_task(
                name="Test",
                description="Test",
                duration=100,
                agent_type=AgentType.OTHER
            )

    @patch('infinium.client.httpx.Client')
    def test_rate_limit_error(self, mock_httpx_class, client):
        """Test rate limit error handling."""
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.is_success = False
        mock_response.json.return_value = {"error": "Rate limited"}
        mock_response.content = b'{"error": "Rate limited"}'
        mock_response.headers = {"Retry-After": "60"}
        
        mock_client_instance.request.return_value = mock_response
        mock_httpx_class.return_value = mock_client_instance
        client._client = mock_client_instance
        
        with pytest.raises(RateLimitError, match="Rate limit exceeded"):
            client.send_task(
                name="Test",
                description="Test",
                duration=100,
                agent_type=AgentType.OTHER
            )
    
    @patch('infinium.client.httpx.Client')
    def test_server_error(self, mock_httpx_class, client):
        """Test server error handling."""
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.is_success = False
        mock_response.json.return_value = {"error": "Internal server error"}
        mock_response.content = b'{"error": "Internal server error"}'
        mock_response.headers = {}
        
        mock_client_instance.request.return_value = mock_response
        mock_httpx_class.return_value = mock_client_instance
        client._client = mock_client_instance
        
        with pytest.raises(ServerError, match="Server error: 500"):
            client.send_task(
                name="Test",
                description="Test",
                duration=100,
                agent_type=AgentType.OTHER
            )
    
    @patch('infinium.client.httpx.Client')
    def test_test_connection_success(self, mock_httpx_class, client, mock_health_response):
        """Test successful connection test."""
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = mock_health_response
        mock_response.content = b'{"status": "healthy"}'
        mock_response.headers = {}
        
        mock_client_instance.request.return_value = mock_response
        mock_httpx_class.return_value = mock_client_instance
        client._client = mock_client_instance
        
        health = client.test_connection()
        
        assert health.status == "healthy"
        assert health.agent_name == "Test Agent"
        assert health.timestamp == "2025-10-07T12:00:00Z"
    
    def test_send_tasks_batch(self, client):
        """Test batch task sending."""
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
        
        with patch.object(client, 'send_task_data') as mock_send:
            mock_send.return_value = Mock(success=True, status_code=200, data={})
            
            result = client.send_tasks_batch(tasks)
            
            assert result.successful == 3
            assert result.failed == 0
            assert len(result.results) == 3
            assert len(result.errors) == 0
            assert mock_send.call_count == 3
    
    def test_send_tasks_batch_with_failures(self, client):
        """Test batch task sending with some failures."""
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
        
        def mock_send_side_effect(task_data):
            if "Task 2" in task_data.name:
                raise Exception("Network error")
            return Mock(success=True, status_code=200, data={})
        
        with patch.object(client, 'send_task_data', side_effect=mock_send_side_effect):
            result = client.send_tasks_batch(tasks)
            
            assert result.successful == 2
            assert result.failed == 1
            assert len(result.results) == 3
            assert len(result.errors) == 1
            assert "Task 'Task 2' failed" in result.errors[0]
    
    def test_context_manager(self, agent_credentials):
        """Test client as context manager."""
        with InfiniumClient(
            agent_id=agent_credentials["agent_id"],
            agent_secret=agent_credentials["agent_secret"]
        ) as client:
            assert client.agent_id == agent_credentials["agent_id"]
        
        # Client should be closed after context exit
        # This would be tested by checking if httpx client is closed
    
    def test_create_task_data_static_method(self):
        """Test static method for creating TaskData."""
        task_data = InfiniumClient.create_task_data(
            name="Test Task",
            description="Test description",
            duration=100,
            agent_type=AgentType.OTHER
        )
        
        assert isinstance(task_data, TaskData)
        assert task_data.name == "Test Task"
        assert task_data.agent_type == AgentType.OTHER
        assert task_data.current_datetime is not None
    
    @patch('infinium.client.httpx.Client')
    def test_network_timeout_error(self, mock_httpx_class, client):
        """Test network timeout error handling."""
        mock_client_instance = Mock()
        mock_client_instance.request.side_effect = httpx.TimeoutException("Request timeout")
        mock_httpx_class.return_value = mock_client_instance
        client._client = mock_client_instance
        
        with pytest.raises(TimeoutError, match=r"Request timed out after 30\.0 seconds"):
            client.send_task(
                name="Test",
                description="Test",
                duration=100,
                agent_type=AgentType.OTHER
            )
    
    @patch('infinium.client.httpx.Client')
    def test_network_connection_error(self, mock_httpx_class, client):
        """Test network connection error handling."""
        mock_client_instance = Mock()
        mock_client_instance.request.side_effect = httpx.NetworkError("Connection failed")
        mock_httpx_class.return_value = mock_client_instance
        client._client = mock_client_instance
        
        with pytest.raises(NetworkError, match=r"Network error: Connection failed"):
            client.send_task(
                name="Test",
                description="Test",
                duration=100,
                agent_type=AgentType.OTHER
            )
    
    @patch('infinium.client.httpx.Client')
    def test_general_request_error(self, mock_httpx_class, client):
        """Test general request error handling."""
        mock_client_instance = Mock()
        mock_client_instance.request.side_effect = httpx.RequestError("General error")
        mock_httpx_class.return_value = mock_client_instance
        client._client = mock_client_instance
        
        with pytest.raises(InfiniumError, match=r"Unexpected error: General error"):
            client.send_task(
                name="Test",
                description="Test",
                duration=100,
                agent_type=AgentType.OTHER
            )
    
    @patch('infinium.client.httpx.Client')
    def test_response_with_no_content(self, mock_httpx_class, client):
        """Test handling response with no content."""
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.content = b''
        mock_response.json.side_effect = json.JSONDecodeError("Empty", "", 0)
        
        mock_client_instance.request.return_value = mock_response
        mock_httpx_class.return_value = mock_client_instance
        client._client = mock_client_instance
        
        response = client.send_task(
            name="Test",
            description="Test",
            duration=100,
            agent_type=AgentType.OTHER
        )
        
        assert response.success is True
        assert response.message == "Success"
        assert response.data is None
    
    @patch('infinium.client.httpx.Client')
    def test_response_with_invalid_json(self, mock_httpx_class, client):
        """Test handling response with invalid JSON."""
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.content = b'invalid json'
        mock_response.json.side_effect = json.JSONDecodeError("Invalid", "", 0)
        
        mock_client_instance.request.return_value = mock_response
        mock_httpx_class.return_value = mock_client_instance
        client._client = mock_client_instance
        
        response = client.send_task(
            name="Test",
            description="Test",
            duration=100,
            agent_type=AgentType.OTHER
        )
        
        assert response.success is True
        assert response.data is None
    
    @patch('infinium.client.httpx.Client')
    def test_generic_api_error(self, mock_httpx_class, client):
        """Test generic API error handling."""
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.is_success = False
        mock_response.json.return_value = {"error": "Bad request"}
        mock_response.content = b'{"error": "Bad request"}'
        mock_response.headers = {}
        
        mock_client_instance.request.return_value = mock_response
        mock_httpx_class.return_value = mock_client_instance
        client._client = mock_client_instance
        
        with pytest.raises(InfiniumError, match="Bad request"):
            client.send_task(
                name="Test",
                description="Test",
                duration=100,
                agent_type=AgentType.OTHER
            )
    
    @patch('infinium.client.httpx.Client')
    def test_error_without_error_message(self, mock_httpx_class, client):
        """Test error handling when response has no error message."""
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.is_success = False
        mock_response.json.return_value = {"status": "failed"}
        mock_response.content = b'{"status": "failed"}'
        mock_response.headers = {}
        
        mock_client_instance.request.return_value = mock_response
        mock_httpx_class.return_value = mock_client_instance
        client._client = mock_client_instance
        
        with pytest.raises(InfiniumError, match="Request failed with status 400"):
            client.send_task(
                name="Test",
                description="Test",
                duration=100,
                agent_type=AgentType.OTHER
            )
    
    def test_get_current_iso_datetime(self, client):
        """Test getting current ISO datetime."""
        datetime_str = client.get_current_iso_datetime()
        assert isinstance(datetime_str, str)
        assert "T" in datetime_str
        assert datetime_str.endswith("Z")
    
    def test_close_client(self, client):
        """Test closing the client."""
        # Should not raise any exception
        client.close()
    
    @patch('infinium.client.httpx.Client')
    def test_retry_mechanism(self, mock_httpx_class, client):
        """Test retry mechanism on network errors."""
        mock_client_instance = Mock()
        
        # First two calls fail, third succeeds
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.is_success = True
        mock_response_success.json.return_value = {"status": "success"}
        mock_response_success.content = b'{"status": "success"}'
        
        mock_client_instance.request.side_effect = [
            httpx.NetworkError("Network error"),
            httpx.NetworkError("Network error"),
            mock_response_success
        ]
        
        mock_httpx_class.return_value = mock_client_instance
        client._client = mock_client_instance
        
        response = client.send_task(
            name="Test",
            description="Test",
            duration=100,
            agent_type=AgentType.OTHER
        )
        
        assert response.success is True
        assert mock_client_instance.request.call_count == 3
    
    @patch('infinium.client.httpx.Client')
    def test_max_retries_exceeded(self, mock_httpx_class, client):
        """Test behavior when max retries are exceeded."""
        mock_client_instance = Mock()
        mock_client_instance.request.side_effect = httpx.NetworkError("Persistent error")
        mock_httpx_class.return_value = mock_client_instance
        client._client = mock_client_instance
        
        with pytest.raises(NetworkError, match=r"Network error: Persistent error"):
            client.send_task(
                name="Test",
                description="Test",
                duration=100,
                agent_type=AgentType.OTHER
            )
        
        # Should try max_retries + 1 times (initial + retries)
        assert mock_client_instance.request.call_count == 4  # 3 retries + 1 initial
    
    def test_rate_limiter_integration(self, agent_credentials):
        """Test rate limiter integration."""
        client = InfiniumClient(
            agent_id=agent_credentials["agent_id"],
            agent_secret=agent_credentials["agent_secret"],
            enable_rate_limiting=True,
            requests_per_second=2.0
        )
        
        assert client.rate_limiter is not None
        assert client.rate_limiter.requests_per_second == 2.0
    
    def test_rate_limiter_disabled(self, agent_credentials):
        """Test rate limiter when disabled."""
        client = InfiniumClient(
            agent_id=agent_credentials["agent_id"],
            agent_secret=agent_credentials["agent_secret"],
            enable_rate_limiting=False
        )
        
        assert client.rate_limiter is None
    
    @patch('infinium.client.httpx.Client')
    def test_health_check_with_empty_response(self, mock_httpx_class, client):
        """Test health check with empty response data."""
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = None
        mock_response.content = b''
        
        mock_client_instance.request.return_value = mock_response
        mock_httpx_class.return_value = mock_client_instance
        client._client = mock_client_instance
        
        with pytest.raises(InfiniumError, match="Empty response from health check"):
            client.test_connection()
    
    def test_send_task_data_direct(self, client):
        """Test sending TaskData object directly."""
        task_data = TaskData(
            name="Direct Task",
            description="Sent directly",
            current_datetime="2025-10-07T12:00:00Z",
            duration=100.0,
            agent_type=AgentType.OTHER
        )
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = Mock(success=True, status_code=200, data={})
            
            response = client.send_task_data(task_data)
            
            assert response.success is True
            mock_request.assert_called_once()
    
    def test_create_task_data_with_sections(self):
        """Test creating TaskData with additional sections."""
        from infinium.types import Customer
        
        customer = Customer(customer_name="Test User")
        
        task_data = InfiniumClient.create_task_data(
            name="Test",
            description="Test task",
            duration=100,
            agent_type=AgentType.OTHER,
            customer=customer
        )
        
        assert task_data.customer == customer
    
    def test_create_task_data_with_current_datetime(self):
        """Test creating TaskData with custom datetime."""
        task_data = InfiniumClient.create_task_data(
            name="Test",
            description="Test task",
            duration=100,
            agent_type=AgentType.OTHER,
            current_datetime="2025-01-01T00:00:00Z"
        )
        
        assert task_data.current_datetime == "2025-01-01T00:00:00Z"
