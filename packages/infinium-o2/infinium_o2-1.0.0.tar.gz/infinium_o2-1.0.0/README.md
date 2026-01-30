# Infinium Python SDK

A professional Python SDK for interacting with the Infinium API. This library provides both synchronous and asynchronous interfaces for seamless integration with your applications.

## Overview

The Infinium Python SDK enables developers to interact with Infinium's powerful API platform through a clean, type-safe interface. Built with modern Python practices, this SDK includes comprehensive error handling, automatic retries, rate limiting, and full async support.

## Key Features

- **Dual Interface Support**: Both synchronous and asynchronous client implementations
- **Robust Error Handling**: Comprehensive exception hierarchy with meaningful error messages
- **Automatic Retry Logic**: Built-in exponential backoff for resilient API interactions
- **Rate Limiting**: Client-side rate limiting to ensure API compliance
- **Type Safety**: Complete type hints for enhanced development experience
- **Input Validation**: Thorough validation of all inputs before API submission
- **Batch Operations**: Efficient handling of multiple tasks in a single operation
- **Flexible Configuration**: Extensive customization options for various use cases
- **Production Ready**: Designed for enterprise environments with proper logging and monitoring

## Installation

Install the SDK using pip:

```bash
pip install infinium
```

For development with additional tools:

```bash
pip install infinium[dev]
```

## Quick Start

### Basic Synchronous Usage

```python
from infinium import InfiniumClient, AgentType

# Initialize the client
client = InfiniumClient(
    agent_id="your-agent-id",
    agent_secret="your-agent-secret"
)

# Send a task
response = client.send_task(
    name="Customer Support Task",
    description="Resolved customer billing inquiry",
    duration=180.0,
    agent_type=AgentType.CUSTOMER_SUPPORT_ASSISTANT
)

print(f"Task submitted successfully: {response.success}")
```

### Asynchronous Usage

```python
import asyncio
from infinium import AsyncInfiniumClient, AgentType

async def main():
    async with AsyncInfiniumClient(
        agent_id="your-agent-id",
        agent_secret="your-agent-secret"
    ) as client:

        response = await client.send_task(
            name="Data Analysis Task",
            description="Analyzed quarterly sales performance",
            duration=3600.0,
            agent_type=AgentType.DATA_ANALYST
        )

        print(f"Async task completed: {response.success}")

asyncio.run(main())
```

## Authentication

### Environment Variables

Set your credentials as environment variables for security:

```bash
export INFINIUM_AGENT_ID="your-agent-id"
export INFINIUM_AGENT_SECRET="your-agent-secret"
```

### Direct Configuration

Alternatively, pass credentials directly to the client:

```python
client = InfiniumClient(
    agent_id="your-agent-id",
    agent_secret="your-agent-secret"
)
```

## Advanced Usage

### Enhanced Task Data

```python
from infinium.types import Customer, Sales

# Create structured data objects
customer = Customer(
    customer_name="Alice Johnson",
    customer_email="alice@company.com",
    client_company="Innovation Corp"
)

sales = Sales(
    lead_source="Conference",
    sales_stage="Negotiation",
    deal_value=45000.0
)

# Submit task with additional context
response = client.send_task(
    name="Enterprise Sales Qualification",
    description="Qualified enterprise prospect and provided technical demo",
    duration=2400.0,
    agent_type=AgentType.SALES_ASSISTANT,
    customer=customer,
    sales=sales
)
```

### Batch Operations

```python
from infinium import TaskData

# Prepare multiple tasks
tasks = [
    TaskData(
        name=f"Routine Task {i}",
        description=f"Completed scheduled maintenance task {i}",
        current_datetime=client.get_current_iso_datetime(),
        duration=float(i * 180),
        agent_type=AgentType.OTHER
    )
    for i in range(1, 11)
]

# Submit tasks in batch with concurrency control
result = client.send_tasks_batch(tasks, max_concurrent=5)
print(f"Completed: {result.successful}, Failed: {result.failed}")
```

### Error Handling

```python
from infinium.exceptions import (
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NetworkError
)

try:
    response = client.send_task(
        name="Test Task",
        description="Validating error handling implementation",
        duration=120.0
    )
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except RateLimitError as e:
    print(f"Rate limit exceeded. Retry after {e.retry_after} seconds")
except ValidationError as e:
    print(f"Invalid input for field '{e.field}': {e}")
except NetworkError as e:
    print(f"Network connectivity issue: {e}")
```

## Agent Types

The SDK supports specialized agent types for different operational contexts:

- `AgentType.OTHER` - General purpose operations
- `AgentType.CUSTOMER_SUPPORT_ASSISTANT` - Customer service and support
- `AgentType.SALES_ASSISTANT` - Sales processes and lead management
- `AgentType.MARKETING_ASSISTANT` - Marketing campaigns and analytics
- `AgentType.DATA_ANALYST` - Data processing and analysis
- `AgentType.RESEARCH_ASSISTANT` - Research and information gathering
- `AgentType.CONTENT_CREATOR` - Content development and management
- `AgentType.PROJECT_MANAGER` - Project coordination and management
- `AgentType.DEVELOPMENT_ASSISTANT` - Software development support
- `AgentType.EXECUTIVE_ASSISTANT` - Administrative and executive support

## Data Models

### Customer Information

```python
from infinium.types import Customer

customer = Customer(
    customer_name="John Smith",
    customer_email="john.smith@enterprise.com",
    customer_phone="+1-555-0199",
    client_company="Enterprise Solutions LLC",
    client_industry="Financial Services"
)
```

### Support Ticket Data

```python
from infinium.types import Support

support = Support(
    call_id="SUP-2024-001",
    issue_description="Database connectivity timeout",
    issue_type="Technical",
    resolution="Updated connection pool configuration",
    priority="High",
    feedback_score=4
)
```

### Sales Information

```python
from infinium.types import Sales

sales = Sales(
    lead_source="Website Form",
    sales_stage="Qualified Lead",
    deal_value=75000.0,
    conversion_rate=0.65,
    sales_notes="Strong interest in enterprise package"
)
```

### Development Task Data

```python
from infinium.types import Development

development = Development(
    programming_language="Python",
    framework_used="Django",
    code_quality_score=92,
    bugs_found=3,
    bugs_fixed=3,
    test_coverage=96.5
)
```

## Configuration Options

### Client Configuration

```python
client = InfiniumClient(
    agent_id="your-agent-id",
    agent_secret="your-agent-secret",
    base_url="https://api.i42m.ai",             # API endpoint
    timeout=30.0,                               # Request timeout (seconds)
    max_retries=3,                             # Maximum retry attempts
    enable_rate_limiting=True,                 # Enable rate limiting
    requests_per_second=10.0,                  # Rate limit threshold
    user_agent="infinium-python/1.0.0",       # Custom user agent
    enable_logging=True,                       # Enable SDK logging
    log_level="INFO"                           # Logging level
)
```

### Connection Testing

Verify your configuration before sending tasks:

```python
try:
    health = client.test_connection()
    print(f"Connected to agent: {health.agent_name}")
    print(f"Connection status: {health.status}")
except AuthenticationError:
    print("Invalid credentials provided")
except Exception as e:
    print(f"Connection test failed: {e}")
```

## Best Practices

### Security

- Store credentials in environment variables, not in code
- Use secure credential management systems in production
- Regularly rotate API keys

### Performance

- Implement proper error handling for all API calls
- Use batch operations for multiple tasks to reduce overhead
- Enable rate limiting to prevent API throttling
- Monitor success and failure rates for optimal performance

### Development

- Use type hints and validation features provided by the SDK
- Implement proper logging for debugging and monitoring
- Use context managers with async clients for resource management
- Test connectivity before deploying to production

### Monitoring

- Track API response times and success rates
- Implement alerting for authentication failures
- Monitor rate limit usage to optimize request patterns

## Examples

Comprehensive examples are available in the `examples/` directory:

- `basic_usage.py` - Synchronous client implementation examples
- `async_usage.py` - Asynchronous client usage patterns
- `.env.example` - Environment variable configuration template

## API Reference

### InfiniumClient

Primary synchronous client for Infinium API interactions.

**Key Methods:**

- `send_task(**kwargs)` - Submit a single task
- `send_task_data(task_data)` - Submit a TaskData object
- `send_tasks_batch(tasks, max_concurrent=5)` - Submit multiple tasks
- `test_connection()` - Verify API connectivity
- `get_interpreted_task_result(task_id)` - Retrieve AI-generated insights
- `close()` - Clean up HTTP connections

### AsyncInfiniumClient

Asynchronous client with identical interface to InfiniumClient. All methods return coroutines.

### Exception Hierarchy

- `InfiniumError` - Base exception class
- `AuthenticationError` - Invalid credentials or authorization
- `ValidationError` - Input validation failures
- `RateLimitError` - API rate limit exceeded
- `NetworkError` - Network connectivity issues
- `TimeoutError` - Request timeout exceeded
- `ServerError` - Server-side processing errors
- `NotFoundError` - Requested resource not found
- `BatchError` - Batch operation processing failures

## Requirements

- Python 3.9 or higher
- httpx >= 0.25.0
- typing-extensions >= 4.8.0 (for Python < 3.12)

## Development Setup

Clone and set up the development environment:

```bash
git clone <repository-url>
cd infinium-python-sdk
pip install -e .[dev]
```

Run the test suite:

```bash
pytest
```

Format code:

```bash
black infinium tests examples
isort infinium tests examples
```

Type checking:

```bash
mypy infinium
```

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Support

For support and questions:

- Create an issue in the project repository
- Contact support at support@i42m.ai
- Review documentation and examples for common use cases

## Contributing

Contributions are welcome. Please ensure all tests pass and code follows the project's formatting standards before submitting pull requests.

````

### Client Configuration

```python
client = InfiniumClient(
    agent_id="your-agent-id",
    agent_secret="your-agent-secret",
    base_url="https://api.i42m.ai",             # API endpoint
    timeout=30.0,                               # Request timeout (seconds)
    max_retries=3,                             # Maximum retry attempts
    enable_rate_limiting=True,                 # Enable rate limiting
    requests_per_second=10.0,                  # Rate limit threshold
    user_agent="infinium-python/1.0.0",       # Custom user agent
    enable_logging=True,                       # Enable SDK logging
    log_level="INFO"                           # Logging level
)
````

### Connection Testing

Verify your configuration before sending tasks:

```python
try:
    health = client.test_connection()
    print(f"Connected to agent: {health.agent_name}")
    print(f"Connection status: {health.status}")
except AuthenticationError:
    print("Invalid credentials provided")
except Exception as e:
    print(f"Connection test failed: {e}")
```

## Best Practices

### Security

- Store credentials in environment variables, not in code
- Use secure credential management systems in production
- Regularly rotate API keys

### Performance

- Implement proper error handling for all API calls
- Use batch operations for multiple tasks to reduce overhead
- Enable rate limiting to prevent API throttling
- Monitor success and failure rates for optimal performance

### Development

- Use type hints and validation features provided by the SDK
- Implement proper logging for debugging and monitoring
- Use context managers with async clients for resource management
- Test connectivity before deploying to production

### Monitoring

- Track API response times and success rates
- Implement alerting for authentication failures
- Monitor rate limit usage to optimize request patterns

## Examples

Comprehensive examples are available in the `examples/` directory:

- `basic_usage.py` - Synchronous client implementation examples
- `async_usage.py` - Asynchronous client usage patterns
- `.env.example` - Environment variable configuration template

## API Reference

### InfiniumClient

Primary synchronous client for Infinium API interactions.

**Key Methods:**

- `send_task(**kwargs)` - Submit a single task
- `send_task_data(task_data)` - Submit a TaskData object
- `send_tasks_batch(tasks, max_concurrent=5)` - Submit multiple tasks
- `test_connection()` - Verify API connectivity
- `get_interpreted_task_result(task_id)` - Retrieve AI-generated insights
- `close()` - Clean up HTTP connections

### AsyncInfiniumClient

Asynchronous client with identical interface to InfiniumClient. All methods return coroutines.

### Exception Hierarchy

- `InfiniumError` - Base exception class
- `AuthenticationError` - Invalid credentials or authorization
- `ValidationError` - Input validation failures
- `RateLimitError` - API rate limit exceeded
- `NetworkError` - Network connectivity issues
- `TimeoutError` - Request timeout exceeded
- `ServerError` - Server-side processing errors
- `NotFoundError` - Requested resource not found
- `BatchError` - Batch operation processing failures

## Requirements

- Python 3.9 or higher
- httpx >= 0.25.0
- typing-extensions >= 4.8.0 (for Python < 3.12)

## Development Setup

Clone and set up the development environment:

```bash
git clone <repository-url>
cd infinium-python-sdk
pip install -e .[dev]
```

Run the test suite:

```bash
pytest
```

Format code:

```bash
black infinium tests examples
isort infinium tests examples
```

Type checking:

```bash
mypy infinium
```

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Support

For support and questions:

- Create an issue in the project repository
- Contact support at support@i42m.ai
- Review documentation and examples for common use cases

## Contributing

Contributions are welcome. Please ensure all tests pass and code follows the project's formatting standards before submitting pull requests.
