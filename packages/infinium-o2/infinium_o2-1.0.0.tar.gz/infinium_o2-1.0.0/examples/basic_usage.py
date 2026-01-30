"""
Basic synchronous usage examples for the Infinium SDK.
"""
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from infinium import InfiniumClient, AgentType, TaskData
from infinium.types import Customer, Sales, Support, Marketing
from infinium.exceptions import InfiniumError, AuthenticationError, RateLimitError


def main():
    """Main example function."""
    # Initialize client with credentials from environment variables
    client = InfiniumClient(
        agent_id=os.getenv("INFINIUM_AGENT_ID"),
        agent_secret=os.getenv("INFINIUM_AGENT_SECRET"),
        enable_logging=True,  # Enable SDK logging
        log_level="INFO"
    )
    
    # Test connection
    print("Testing connection...")
    try:
        health = client.test_connection()
        print(f"✅ Connected successfully!")
        print(f"   Agent: {health.agent_name}")
        print(f"   Status: {health.status}")
        print(f"   Timestamp: {health.timestamp}")
    except AuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        return
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    print("\n" + "="*50)
    
    # Example 1: Simple task
    print("Example 1: Simple task")
    try:
        response = client.send_task(
            name="Process customer inquiry",
            description="Handled customer question about pricing for enterprise package",
            duration=125.5,  # Duration in seconds
            agent_type=AgentType.CUSTOMER_SUPPORT_ASSISTANT
        )
        
        print(f"✅ Task sent successfully!")
        print(f"   Status Code: {response.status_code}")
        print(f"   Message: {response.message}")
        if response.data:
            print(f"   Task ID: {response.data.get('task_id', 'N/A')}")
    
    except InfiniumError as e:
        print(f"❌ Task failed: {e}")
    
    print("\n" + "="*50)
    
    # Example 2: Task with additional data
    print("Example 2: Task with customer and sales data")
    
    customer_data = Customer(
        customer_name="John Smith",
        customer_email="john.smith@acmecorp.com",
        customer_phone="+1-555-0123",
        client_company="Acme Corporation",
        client_industry="Manufacturing"
    )
    
    sales_data = Sales(
        lead_source="Website Contact Form",
        sales_stage="Qualified Lead",
        deal_value=15000.0,
        conversion_rate=0.75,
        sales_notes="Interested in enterprise features, budget approved"
    )
    
    try:
        response = client.send_task(
            name="Qualify enterprise lead",
            description="Evaluated enterprise customer needs and provided pricing information",
            duration=1800.0,  # 30 minutes
            agent_type=AgentType.SALES_ASSISTANT,
            customer=customer_data,
            sales=sales_data
        )
        
        print(f"✅ Sales task sent successfully!")
        print(f"   Customer: {customer_data.customer_name}")
        print(f"   Deal Value: ${sales_data.deal_value:,.2f}")
        
    except InfiniumError as e:
        print(f"❌ Sales task failed: {e}")
    
    print("\n" + "="*50)
    
    # Example 3: Marketing task
    print("Example 3: Marketing campaign analysis")
    
    marketing_data = Marketing(
        campaign_name="Q4 2025 Product Launch",
        campaign_type="Multi-channel",
        target_audience="Enterprise decision makers",
        marketing_channel="Email + LinkedIn + Webinar",
        engagement_metrics="Email open rate: 24%, LinkedIn CTR: 3.2%",
        conversion_metrics="Webinar signup rate: 8.5%, Demo requests: 42"
    )
    
    try:
        response = client.send_task(
            name="Analyze Q4 campaign performance",
            description="Comprehensive analysis of multi-channel marketing campaign effectiveness",
            duration=7200.0,  # 2 hours
            agent_type=AgentType.MARKETING_ASSISTANT,
            marketing=marketing_data
        )
        
        print(f"✅ Marketing analysis task sent!")
        print(f"   Campaign: {marketing_data.campaign_name}")
        print(f"   Channels: {marketing_data.marketing_channel}")
        
    except InfiniumError as e:
        print(f"❌ Marketing task failed: {e}")
    
    print("\n" + "="*50)
    
    # Example 5: Support ticket resolution
    print("Example 5: Support ticket resolution")
    
    support_data = Support(
        call_id="TICKET-2025-10-001",
        issue_description="Customer unable to access dashboard after recent update",
        issue_type="Authentication",
        resolution="Cleared browser cache and reset API tokens",
        priority="High",
        follow_up_required=False
    )
    
    try:
        response = client.send_task(
            name="Resolve dashboard access issue",
            description="Diagnosed and fixed customer authentication problem",
            duration=900.0,  # 15 minutes
            agent_type=AgentType.CUSTOMER_SUPPORT_ASSISTANT,
            support=support_data
        )
        
        print(f"✅ Support ticket resolution logged!")
        print(f"   Ticket ID: {support_data.call_id}")
        print(f"   Resolution: {support_data.resolution}")
        
    except InfiniumError as e:
        print(f"❌ Support task failed: {e}")
    
    print("\n" + "="*50)
    
    # Example 6: Using TaskData object directly
    print("Example 6: Using TaskData object")
    
    task_data = TaskData(
        name="Generate monthly report",
        description="Created comprehensive monthly performance and analytics report",
        current_datetime=client.get_current_iso_datetime(),
        duration=5400.0,  # 1.5 hours
        agent_type=AgentType.DATA_ANALYST
    )
    
    try:
        response = client.send_task_data(task_data)
        print(f"✅ TaskData object sent successfully!")
        print(f"   Task: {task_data.name}")
        print(f"   Agent Type: {task_data.agent_type.value}")
        
    except InfiniumError as e:
        print(f"❌ TaskData submission failed: {e}")
    
    # Close the client (or use context manager)
    client.close()
    print("\n🎉 All examples completed!")


def batch_example():
    """Example of sending multiple tasks in batch."""
    print("Batch Example: Sending multiple tasks")
    
    client = InfiniumClient(
        agent_id=os.getenv("INFINIUM_AGENT_ID"),
        agent_secret=os.getenv("INFINIUM_AGENT_SECRET")
    )
    
    # Create multiple tasks
    tasks = []
    for i in range(5):
        task = TaskData(
            name=f"Daily task #{i+1}",
            description=f"Completed routine task number {i+1} for the day",
            current_datetime=client.get_current_iso_datetime(),
            duration=float((i + 1) * 300),  # Varying durations
            agent_type=AgentType.OTHER
        )
        tasks.append(task)
    
    try:
        # Send all tasks in batch
        result = client.send_tasks_batch(tasks, max_concurrent=3)
        
        print(f"✅ Batch operation completed!")
        print(f"   Successful: {result.successful}")
        print(f"   Failed: {result.failed}")
        print(f"   Total Results: {len(result.results)}")
        
        if result.errors:
            print("   Errors:")
            for error in result.errors:
                print(f"     - {error}")
    
    except InfiniumError as e:
        print(f"❌ Batch operation failed: {e}")
    
    client.close()


def error_handling_example():
    """Example of error handling."""
    print("Error Handling Example")
    
    # Example with invalid credentials
    try:
        client = InfiniumClient(
            agent_id="invalid-id",
            agent_secret="invalid-secret"
        )
        
        client.send_task(
            name="Test task",
            description="This will fail",
            duration=100,
            agent_type=AgentType.OTHER
        )
        
    except AuthenticationError as e:
        print(f"🔐 Authentication Error: {e}")
        print(f"   Status Code: {e.status_code}")
    
    except RateLimitError as e:
        print(f"⏱️ Rate Limited: {e}")
        print(f"   Retry After: {e.retry_after} seconds")
    
    except InfiniumError as e:
        print(f"❌ General SDK Error: {e}")
        print(f"   Status Code: {e.status_code}")
        print(f"   Details: {e.details}")
    
    except Exception as e:
        print(f"💥 Unexpected Error: {e}")


if __name__ == "__main__":
    # Check for required environment variables
    if not os.getenv("INFINIUM_AGENT_ID") or not os.getenv("INFINIUM_AGENT_SECRET"):
        print("❌ Please set INFINIUM_AGENT_ID and INFINIUM_AGENT_SECRET environment variables")
        print("   You can create a .env file with:")
        print("   INFINIUM_AGENT_ID=your-agent-id")
        print("   INFINIUM_AGENT_SECRET=your-agent-secret")
        exit(1)
    
    # Run examples
    main()
    print("\n" + "="*60 + "\n")
    batch_example()
    print("\n" + "="*60 + "\n")
    error_handling_example()
