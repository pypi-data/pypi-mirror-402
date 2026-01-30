"""
Type definitions for the Infinium SDK.
"""
from __future__ import annotations
from typing import Any, Dict, Optional, Union, Literal
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class AgentType(str, Enum):
    """Available agent types for Infinium."""
    OTHER = "OTHER"
    EXECUTIVE_ASSISTANT = "EXECUTIVE_ASSISTANT"
    MARKETING_ASSISTANT = "MARKETING_ASSISTANT"
    DATA_ANALYST = "DATA_ANALYST"
    RESEARCH_ASSISTANT = "RESEARCH_ASSISTANT"
    CUSTOMER_SUPPORT_ASSISTANT = "CUSTOMER_SUPPORT_ASSISTANT"
    CONTENT_CREATOR = "CONTENT_CREATOR"
    SALES_ASSISTANT = "SALES_ASSISTANT"
    PROJECT_MANAGER = "PROJECT_MANAGER"
    DEVELOPMENT_ASSISTANT = "DEVELOPMENT_ASSISTANT"


@dataclass
class TimeTracking:
    """Time tracking information for a task."""
    start_time: Optional[str] = None
    end_time: Optional[str] = None


@dataclass
class Customer:
    """Customer information for a task."""
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None
    client_company: Optional[str] = None
    client_industry: Optional[str] = None


@dataclass
class Support:
    """Support-specific information for a task."""
    call_id: Optional[str] = None
    issue_description: Optional[str] = None
    issue_type: Optional[str] = None
    resolution: Optional[str] = None
    priority: Optional[str] = None
    follow_up_required: Optional[bool] = None


@dataclass
class Sales:
    """Sales-specific information for a task."""
    lead_source: Optional[str] = None
    sales_stage: Optional[str] = None
    deal_value: Optional[float] = None
    conversion_rate: Optional[float] = None
    sales_notes: Optional[str] = None


@dataclass
class Marketing:
    """Marketing-specific information for a task."""
    campaign_name: Optional[str] = None
    campaign_type: Optional[str] = None
    target_audience: Optional[str] = None
    marketing_channel: Optional[str] = None
    engagement_metrics: Optional[str] = None
    conversion_metrics: Optional[str] = None


@dataclass
class Content:
    """Content creation information for a task."""
    content_type: Optional[str] = None
    content_format: Optional[str] = None
    content_length: Optional[int] = None
    content_topic: Optional[str] = None
    target_platform: Optional[str] = None


@dataclass
class Research:
    """Research-specific information for a task."""
    research_topic: Optional[str] = None
    research_method: Optional[str] = None
    data_sources: Optional[str] = None
    research_findings: Optional[str] = None
    analysis_type: Optional[str] = None


@dataclass
class Project:
    """Project management information for a task."""
    project_name: Optional[str] = None
    project_phase: Optional[str] = None
    deliverables: Optional[str] = None
    stakeholders: Optional[str] = None
    project_status: Optional[str] = None
    milestone_achieved: Optional[str] = None


@dataclass
class Development:
    """Development-specific information for a task."""
    programming_language: Optional[str] = None
    framework_used: Optional[str] = None
    bugs_found: Optional[int] = None
    bugs_fixed: Optional[int] = None
    test_coverage: Optional[float] = None


@dataclass
class Executive:
    """Executive assistant information for a task."""
    meeting_type: Optional[str] = None
    attendees_count: Optional[int] = None
    agenda_items: Optional[str] = None
    action_items: Optional[str] = None
    calendar_conflicts: Optional[int] = None


@dataclass
class General:
    """General task information."""
    tools_used: Optional[str] = None
    agent_notes: Optional[str] = None


@dataclass
class TaskData:
    """Complete task data structure."""
    name: str
    description: str
    current_datetime: str
    duration: float
    agent_type: AgentType
    
    # Optional sections
    time_tracking: Optional[TimeTracking] = None
    customer: Optional[Customer] = None
    support: Optional[Support] = None
    sales: Optional[Sales] = None
    marketing: Optional[Marketing] = None
    content: Optional[Content] = None
    research: Optional[Research] = None
    project: Optional[Project] = None
    development: Optional[Development] = None
    executive: Optional[Executive] = None
    general: Optional[General] = None


@dataclass
class ApiResponse:
    """Standard API response structure."""
    success: bool
    status_code: Optional[int] = None
    message: str = ""
    data: Optional[Dict[str, Any]] = None


@dataclass
class HealthCheck:
    """Health check response structure."""
    status: str
    agent_name: str
    timestamp: str


@dataclass
class BatchResult:
    """Result of a batch operation."""
    successful: int
    failed: int
    results: list[ApiResponse]
    errors: list[str]


# Type aliases for convenience
TaskSections = Dict[str, Union[
    TimeTracking, Customer, Support, Sales, Marketing,
    Content, Research, Project, Development, Executive, General
]]

ConfigDict = Dict[str, Any]
