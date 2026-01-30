"""
Tests for types and data structures.
"""
import pytest
from datetime import datetime

from infinium.types import (
    AgentType, TaskData, ApiResponse, HealthCheck, BatchResult,
    TimeTracking, Customer, Support, Sales, Marketing, Content, Research,
    Project, Development, Executive, General
)


class TestAgentType:
    """Test AgentType enum."""
    
    def test_agent_type_values(self):
        """Test that all agent types have correct values."""
        assert AgentType.OTHER == "OTHER"
        assert AgentType.EXECUTIVE_ASSISTANT == "EXECUTIVE_ASSISTANT"
        assert AgentType.MARKETING_ASSISTANT == "MARKETING_ASSISTANT"
        assert AgentType.DATA_ANALYST == "DATA_ANALYST"
        assert AgentType.RESEARCH_ASSISTANT == "RESEARCH_ASSISTANT"
        assert AgentType.CUSTOMER_SUPPORT_ASSISTANT == "CUSTOMER_SUPPORT_ASSISTANT"
        assert AgentType.CONTENT_CREATOR == "CONTENT_CREATOR"
        assert AgentType.SALES_ASSISTANT == "SALES_ASSISTANT"
        assert AgentType.PROJECT_MANAGER == "PROJECT_MANAGER"
        assert AgentType.DEVELOPMENT_ASSISTANT == "DEVELOPMENT_ASSISTANT"
    
    def test_agent_type_iteration(self):
        """Test that we can iterate over agent types."""
        types = list(AgentType)
        assert len(types) == 10
        assert AgentType.OTHER in types


class TestTaskData:
    """Test TaskData dataclass."""
    
    def test_task_data_creation(self):
        """Test creating TaskData with required fields."""
        task = TaskData(
            name="Test Task",
            description="Test description",
            current_datetime="2025-10-07T12:00:00Z",
            duration=120.5,
            agent_type=AgentType.OTHER
        )
        
        assert task.name == "Test Task"
        assert task.description == "Test description"
        assert task.current_datetime == "2025-10-07T12:00:00Z"
        assert task.duration == 120.5
        assert task.agent_type == AgentType.OTHER
    
    def test_task_data_with_optional_fields(self):
        """Test TaskData with optional fields."""
        customer = Customer(customer_name="John Doe", customer_email="john@example.com")
        time_tracking = TimeTracking(start_time="2025-10-07T11:00:00Z", end_time="2025-10-07T13:00:00Z")
        
        task = TaskData(
            name="Customer Task",
            description="Handle customer inquiry",
            current_datetime="2025-10-07T12:00:00Z",
            duration=7200.0,
            agent_type=AgentType.CUSTOMER_SUPPORT_ASSISTANT,
            customer=customer,
            time_tracking=time_tracking
        )
        
        assert task.customer.customer_name == "John Doe"
        assert task.time_tracking.start_time == "2025-10-07T11:00:00Z"
        assert task.agent_type == AgentType.CUSTOMER_SUPPORT_ASSISTANT
    
class TestDataclasses:
    """Test various dataclass structures."""
    
    def test_time_tracking(self):
        """Test TimeTracking dataclass."""
        time_tracking = TimeTracking(
            start_time="2025-10-07T10:00:00Z",
            end_time="2025-10-07T12:00:00Z"
        )
        
        assert time_tracking.start_time == "2025-10-07T10:00:00Z"
        assert time_tracking.end_time == "2025-10-07T12:00:00Z"
    
    def test_customer(self):
        """Test Customer dataclass."""
        customer = Customer(
            customer_name="Alice Johnson",
            customer_email="alice@example.com",
            customer_phone="+1-555-0123",
            customer_address="123 Main St, City, State",
            client_company="Acme Corp",
            client_industry="Technology"
        )
        
        assert customer.customer_name == "Alice Johnson"
        assert customer.customer_email == "alice@example.com"
        assert customer.client_company == "Acme Corp"
    
    def test_support(self):
        """Test Support dataclass."""
        support = Support(
            call_id="CALL-123",
            issue_description="Login problem",
            issue_type="Authentication",
            resolution="Password reset",
            priority="High",
            follow_up_required=False
        )
        
        assert support.call_id == "CALL-123"
        assert support.issue_description == "Login problem"
        assert support.follow_up_required is False
    
    def test_sales(self):
        """Test Sales dataclass."""
        sales = Sales(
            lead_source="Website",
            sales_stage="Qualified",
            deal_value=10000.0,
            conversion_rate=0.85,
            sales_notes="Interested in enterprise package"
        )
        
        assert sales.lead_source == "Website"
        assert sales.deal_value == 10000.0
        assert sales.conversion_rate == 0.85
    
    def test_marketing(self):
        """Test Marketing dataclass."""
        marketing = Marketing(
            campaign_name="Q4 2025 Launch",
            campaign_type="Email",
            target_audience="Enterprise customers",
            marketing_channel="Email",
            engagement_metrics="Click rate: 15%",
            conversion_metrics="Conversion rate: 3.2%"
        )
        
        assert marketing.campaign_name == "Q4 2025 Launch"
        assert marketing.target_audience == "Enterprise customers"
    
    def test_content(self):
        """Test Content dataclass."""
        content = Content(
            content_type="Blog Post",
            content_format="Markdown",
            content_length=2500,
            content_topic="API Best Practices",
            target_platform="Company Blog"
        )
        
        assert content.content_type == "Blog Post"
        assert content.content_length == 2500
        assert content.target_platform == "Company Blog"
    
    def test_research(self):
        """Test Research dataclass."""
        research = Research(
            research_topic="Market Analysis",
            research_method="Survey",
            data_sources="Customer interviews, market reports",
            research_findings="Strong demand for automation",
            analysis_type="Quantitative"
        )
        
        assert research.research_topic == "Market Analysis"
        assert research.research_method == "Survey"
        assert research.analysis_type == "Quantitative"
    
    def test_project(self):
        """Test Project dataclass."""
        project = Project(
            project_name="SDK Development",
            project_phase="Implementation",
            deliverables="Python SDK, Node.js SDK",
            stakeholders="Engineering, Product",
            project_status="On Track",
            milestone_achieved="Alpha Release"
        )
        
        assert project.project_name == "SDK Development"
        assert project.project_phase == "Implementation"
        assert project.project_status == "On Track"
    
    def test_development(self):
        """Test Development dataclass."""
        development = Development(
            programming_language="Python",
            framework_used="FastAPI",
            bugs_found=3,
            bugs_fixed=3,
            test_coverage=95.5
        )
        
        assert development.programming_language == "Python"
        assert development.bugs_found == 3
        assert development.test_coverage == 95.5
    
    def test_executive(self):
        """Test Executive dataclass."""
        executive = Executive(
            meeting_type="Board Meeting",
            attendees_count=8,
            agenda_items="Budget review, strategic planning",
            action_items="Approve Q1 budget, hire new VP",
            calendar_conflicts=2
        )
        
        assert executive.meeting_type == "Board Meeting"
        assert executive.attendees_count == 8
        assert executive.calendar_conflicts == 2
    
    def test_general(self):
        """Test General dataclass."""
        general = General(
            tools_used="VS Code, Git, Docker",
            agent_notes="Task completed efficiently"
        )
        
        assert general.tools_used == "VS Code, Git, Docker"
        assert general.agent_notes == "Task completed efficiently"


class TestApiResponse:
    """Test ApiResponse dataclass."""
    
    def test_api_response_success(self):
        """Test successful API response."""
        response = ApiResponse(
            success=True,
            status_code=200,
            message="Task sent successfully",
            data={"task_id": "123", "created_at": "2025-10-07T12:00:00Z"}
        )
        
        assert response.success is True
        assert response.status_code == 200
        assert response.message == "Task sent successfully"
        assert response.data["task_id"] == "123"
    
    def test_api_response_failure(self):
        """Test failed API response."""
        response = ApiResponse(
            success=False,
            status_code=400,
            message="Validation error",
            data={"field": "name", "error": "Required field missing"}
        )
        
        assert response.success is False
        assert response.status_code == 400
        assert response.message == "Validation error"


class TestHealthCheck:
    """Test HealthCheck dataclass."""
    
    def test_health_check(self):
        """Test health check response."""
        health = HealthCheck(
            status="healthy",
            agent_name="Test Agent",
            timestamp="2025-10-07T12:00:00Z"
        )
        
        assert health.status == "healthy"
        assert health.agent_name == "Test Agent"
        assert health.timestamp == "2025-10-07T12:00:00Z"


class TestBatchResult:
    """Test BatchResult dataclass."""
    
    def test_batch_result(self):
        """Test batch operation result."""
        results = [
            ApiResponse(success=True, status_code=200, message="Success"),
            ApiResponse(success=False, status_code=400, message="Failed")
        ]
        
        batch_result = BatchResult(
            successful=1,
            failed=1,
            results=results,
            errors=["Task 2 failed: validation error"]
        )
        
        assert batch_result.successful == 1
        assert batch_result.failed == 1
        assert len(batch_result.results) == 2
        assert len(batch_result.errors) == 1
