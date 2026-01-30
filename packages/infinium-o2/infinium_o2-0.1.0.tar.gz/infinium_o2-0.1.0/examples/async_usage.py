"""
Asynchronous usage examples for the Infinium SDK.
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from infinium import AsyncInfiniumClient, AgentType, TaskData
from infinium.types import Customer, Development, Research
from infinium.exceptions import InfiniumError


async def main():
    """Main async example function."""
    # Use async context manager for proper resource cleanup
    async with AsyncInfiniumClient(
        agent_id=os.getenv("INFINIUM_AGENT_ID"),
        agent_secret=os.getenv("INFINIUM_AGENT_SECRET"),
        enable_logging=True,
        log_level="INFO"
    ) as client:
        
        # Test connection
        print("Testing async connection...")
        try:
            health = await client.test_connection()
            print(f"✅ Connected successfully!")
            print(f"   Agent: {health.agent_name}")
            print(f"   Status: {health.status}")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return
        
        print("\n" + "="*50)
        
        # Example 1: Simple async task
        print("Example 1: Simple async task")
        try:
            response = await client.send_task(
                name="Async data processing",
                description="Processed large dataset using async operations",
                duration=1500.0,
                agent_type=AgentType.DATA_ANALYST
            )
            
            print(f"✅ Async task sent successfully!")
            print(f"   Status: {response.status_code}")
            print(f"   Message: {response.message}")
        
        except InfiniumError as e:
            print(f"❌ Async task failed: {e}")
        
        print("\n" + "="*50)
        
        # Example 2: Development task with detailed info
        print("Example 2: Development task")
        
        dev_data = Development(
            programming_language="Python",
            framework_used="FastAPI + AsyncIO",
            bugs_found=2,
            bugs_fixed=2,
            test_coverage=96.5
        )
        
        try:
            response = await client.send_task(
                name="Implement async API endpoints",
                description="Created new async endpoints for user management with comprehensive error handling",
                duration=14400.0,  # 4 hours
                agent_type=AgentType.DEVELOPMENT_ASSISTANT,
                development=dev_data
            )
            
            print(f"✅ Development task logged!")
            print(f"   Language: {dev_data.programming_language}")
            print(f"   Test Coverage: {dev_data.test_coverage}%")
        
        except InfiniumError as e:
            print(f"❌ Development task failed: {e}")
        
        print("\n" + "="*50)
        
        # Example 3: Research task
        print("Example 3: Research analysis")
        
        research_data = Research(
            research_topic="AI/ML Integration Patterns",
            research_method="Literature Review + Case Studies",
            data_sources="Academic papers, industry reports, competitor analysis",
            research_findings="Microservices architecture with event-driven ML pipelines shows 40% better scalability",
            analysis_type="Mixed Methods"
        )
        
        try:
            response = await client.send_task(
                name="Research ML integration patterns",
                description="Comprehensive research on machine learning integration patterns for microservices",
                duration=10800.0,  # 3 hours
                agent_type=AgentType.RESEARCH_ASSISTANT,
                research=research_data
            )
            
            print(f"✅ Research task completed!")
            print(f"   Topic: {research_data.research_topic}")
            print(f"   Method: {research_data.research_method}")
        
        except InfiniumError as e:
            print(f"❌ Research task failed: {e}")


async def concurrent_tasks_example():
    """Example of sending multiple tasks concurrently."""
    print("Concurrent Tasks Example")
    
    async with AsyncInfiniumClient(
        agent_id=os.getenv("INFINIUM_AGENT_ID"),
        agent_secret=os.getenv("INFINIUM_AGENT_SECRET")
    ) as client:
        
        # Create multiple tasks for different departments
        tasks = [
            TaskData(
                name="Morning standup meeting",
                description="Facilitated daily standup for development team",
                current_datetime=client.get_current_iso_datetime(),
                duration=900.0,  # 15 minutes
                agent_type=AgentType.PROJECT_MANAGER
            ),
            TaskData(
                name="Customer feedback analysis",
                description="Analyzed recent customer feedback and identified improvement areas",
                current_datetime=client.get_current_iso_datetime(),
                duration=3600.0,  # 1 hour
                agent_type=AgentType.DATA_ANALYST
            ),
            TaskData(
                name="Blog post creation",
                description="Created technical blog post about API best practices",
                current_datetime=client.get_current_iso_datetime(),
                duration=7200.0,  # 2 hours
                agent_type=AgentType.CONTENT_CREATOR
            ),
            TaskData(
                name="Security audit review",
                description="Reviewed quarterly security audit findings and created action plan",
                current_datetime=client.get_current_iso_datetime(),
                duration=5400.0,  # 1.5 hours
                agent_type=AgentType.DEVELOPMENT_ASSISTANT
            )
        ]
        
        try:
            # Send all tasks concurrently with limited concurrency
            result = await client.send_tasks_batch(
                tasks, 
                max_concurrent=2,  # Limit to 2 concurrent requests
                fail_fast=False    # Continue even if some tasks fail
            )
            
            print(f"✅ Concurrent batch completed!")
            print(f"   Successful: {result.successful}")
            print(f"   Failed: {result.failed}")
            print(f"   Total: {len(result.results)}")
            
            # Show individual results
            for i, task_result in enumerate(result.results):
                task_name = tasks[i].name
                status = "✅" if task_result.success else "❌"
                print(f"   {status} {task_name}")
        
        except InfiniumError as e:
            print(f"❌ Batch operation failed: {e}")


async def rate_limiting_example():
    """Example showing rate limiting in action."""
    print("Rate Limiting Example")
    
    # Create client with aggressive rate limiting for demo
    async with AsyncInfiniumClient(
        agent_id=os.getenv("INFINIUM_AGENT_ID"),
        agent_secret=os.getenv("INFINIUM_AGENT_SECRET"),
        requests_per_second=2.0  # Very low rate limit for demo
    ) as client:
        
        print("Sending tasks with rate limiting...")
        start_time = asyncio.get_event_loop().time()
        
        tasks = []
        for i in range(5):
            task = asyncio.create_task(
                client.send_task(
                    name=f"Rate limited task {i+1}",
                    description=f"Task {i+1} sent with rate limiting",
                    duration=10.0,
                    agent_type=AgentType.OTHER
                )
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time
        
        successful = sum(1 for r in results if not isinstance(r, Exception))
        failed = len(results) - successful
        
        print(f"✅ Rate limiting demo completed!")
        print(f"   Duration: {duration:.1f} seconds")
        print(f"   Successful: {successful}")
        print(f"   Failed: {failed}")
        print(f"   Average time per task: {duration/len(tasks):.1f}s")


async def error_handling_example():
    """Example of async error handling."""
    print("Async Error Handling Example")
    
    try:
        # This will fail due to invalid credentials
        async with AsyncInfiniumClient(
            agent_id="invalid-id",
            agent_secret="invalid-secret"
        ) as client:
            
            await client.send_task(
                name="This will fail",
                description="Testing error handling",
                duration=100,
                agent_type=AgentType.OTHER
            )
    
    except InfiniumError as e:
        print(f"❌ Expected error caught: {e}")
        print(f"   Type: {type(e).__name__}")
        print(f"   Status Code: {e.status_code}")


async def stream_tasks_example():
    """Example of processing tasks as a stream."""
    print("Stream Processing Example")
    
    async with AsyncInfiniumClient(
        agent_id=os.getenv("INFINIUM_AGENT_ID"),
        agent_secret=os.getenv("INFINIUM_AGENT_SECRET")
    ) as client:
        
        # Simulate a stream of tasks arriving over time
        async def task_generator():
            """Generate tasks asynchronously."""
            for i in range(10):
                await asyncio.sleep(0.5)  # Simulate tasks arriving every 500ms
                yield TaskData(
                    name=f"Streaming task {i+1}",
                    description=f"Task {i+1} from the stream",
                    current_datetime=client.get_current_iso_datetime(),
                    duration=float(i * 100),
                    agent_type=AgentType.OTHER
                )
        
        # Process tasks as they arrive
        processed = 0
        async for task in task_generator():
            try:
                response = await client.send_task_data(task)
                processed += 1
                print(f"   📤 Processed: {task.name}")
            except InfiniumError as e:
                print(f"   ❌ Failed: {task.name} - {e}")
        
        print(f"✅ Stream processing completed! Processed {processed} tasks")


if __name__ == "__main__":
    # Check for required environment variables
    if not os.getenv("INFINIUM_AGENT_ID") or not os.getenv("INFINIUM_AGENT_SECRET"):
        print("❌ Please set INFINIUM_AGENT_ID and INFINIUM_AGENT_SECRET environment variables")
        exit(1)
    
    async def run_all_examples():
        """Run all async examples."""
        await main()
        print("\n" + "="*60 + "\n")
        
        await concurrent_tasks_example()
        print("\n" + "="*60 + "\n")
        
        await rate_limiting_example()
        print("\n" + "="*60 + "\n")
        
        await error_handling_example()
        print("\n" + "="*60 + "\n")
        
        await stream_tasks_example()
        print("\n🎉 All async examples completed!")
    
    # Run all examples
    asyncio.run(run_all_examples())
