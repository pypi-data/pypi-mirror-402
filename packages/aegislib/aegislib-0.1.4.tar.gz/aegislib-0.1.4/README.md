# Aegis Python SDK

[![CI](https://github.com/mrsidrdx/aegis-python-sdk/workflows/CI/badge.svg)](https://github.com/mrsidrdx/aegis-python-sdk/actions)
[![PyPI version](https://badge.fury.io/py/aegis.svg)](https://pypi.org/project/aegis/)
[![Python versions](https://img.shields.io/pypi/pyversions/aegis.svg)](https://pypi.org/project/aegis/)
[![Code coverage](https://codecov.io/gh/aegis/aegis-python-sdk/branch/main/graph/badge.svg)](https://codecov.io/gh/aegis/aegis-python-sdk)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Secure AI tool guard integration for multi-agent frameworks.

Aegis enables developers to integrate policy-based AI tool security directly into their agent workflows with minimal effort. It provides a simple `@aegis_guard` decorator or wrapper to protect any tool call, with automatic decision requests to the Aegis Data Plane and enforcement of allow/deny/sanitize policies in real time.

## Features

- **Simple Decorator**: One-line `@aegis_guard` decorator for any Python function
- **Framework Agnostic**: Core SDK works with any Python code
- **Real-time Policy Enforcement**: Automatic allow/deny/sanitize decisions
- **Async Support**: Full async/await compatibility
- **Resilient**: Built-in retries, timeouts, and error handling

## Installation

```bash
pip install aegislib
```

## Quick Start

```python
from aegis import AegisConfig, DecisionClient, aegis_guard

# Configure the SDK
cfg = AegisConfig(api_key="your-api-key")
client = DecisionClient(cfg)

# Guard any tool function
@aegis_guard(client, agent_id="ops-agent", tool_name="slack.post_message")
def post_to_slack(channel: str, text: str):
    print(f"Sending message: {text} to {channel}")

# Use normally - Aegis will decide allow/deny/sanitize automatically
post_to_slack("#support", "Hello!")

# For approval-required operations
@aegis_guard(client, agent_id="admin-agent", tool_name="database.drop_table")
def drop_database_table(table_name: str) -> str:
    return f"Dropped table: {table_name}"

# This will trigger approval workflow if policy requires it
drop_database_table("users")  # Returns immediately, execution happens in background when approved
```

## Configuration

Configure via environment variables:

```bash
export AEGIS_API_KEY="your-api-key"
export AEGIS_TIMEOUT_S="1.0"
export AEGIS_RETRIES="2"
export AEGIS_LOG_LEVEL="info"
export AEGIS_DEBUG="false"
export AEGIS_APPROVAL_POLLING_ENABLED="true"
export AEGIS_APPROVAL_POLLING_INITIAL_DELAY_S="2.0"
export AEGIS_APPROVAL_POLLING_MAX_DELAY_S="60.0"
export AEGIS_APPROVAL_POLLING_MAX_ATTEMPTS="50"
export AEGIS_APPROVAL_POLLING_JITTER_RATIO="0.1"
```

Or programmatically:

```python
cfg = AegisConfig(
    api_key="your-api-key",
    timeout_s=1.0,
    retries=2,
    log_level="info",
    debug=False,
    # Approval workflow configuration
    approval_polling_enabled=True,
    approval_polling_initial_delay_s=2.0,
    approval_polling_max_delay_s=60.0,
    approval_polling_max_attempts=50,
    approval_polling_jitter_ratio=0.1,
)
```

## Advanced Usage

### Async Support

Aegis fully supports async functions:

```python
@aegis_guard(client, agent_id="async-agent", tool_name="async_tool")
async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient() as http:
        response = await http.get(url)
        return response.json()

# Use with await
data = await fetch_data("https://api.example.com/data")
```

### Approval Workflow Integration

Aegis supports approval-required decisions with automatic background polling:

```python
from aegis import get_global_task_manager, TaskStatus

# Configure with approval polling enabled (default)
config = AegisConfig(
    api_key="your-api-key",
    approval_polling_enabled=True,
    approval_polling_max_attempts=100,  # Poll longer for critical operations
)

client = DecisionClient(config)

def on_approval_complete(result, error):
    """Callback invoked when approval workflow completes."""
    if error:
        print(f"Operation failed or was denied: {error}")
    else:
        print(f"Operation completed successfully: {result}")

@aegis_guard(client, agent_id="admin", tool_name="server.shutdown", approval_callback=on_approval_complete)
def shutdown_server(server_id: str) -> str:
    return f"Server {server_id} shut down successfully"

# This returns immediately - execution happens in background when approved
task_message = shutdown_server("prod-server-01")
print(task_message)  # "Tool 'server.shutdown' execution pending approval: Manual approval needed"

# Monitor task status
task_manager = get_global_task_manager()
tasks = task_manager.list_tasks(agent_id="admin", status=TaskStatus.PENDING)
for task in tasks:
    print(f"Task {task.task_id} is {task.status} for {task.tool_name}")
```

### Task Management

Query and manage approval tasks programmatically:

```python
from aegis import get_global_task_manager, TaskStatus

task_manager = get_global_task_manager()

# Get all pending tasks
pending_tasks = task_manager.list_tasks(status=TaskStatus.PENDING)

# Get tasks for specific agent
agent_tasks = task_manager.list_tasks(agent_id="admin-agent")

# Get specific task details
task = task_manager.get_task("task-uuid-here")
if task:
    print(f"Task status: {task.status}, created: {task.created_at}")

# Clean up completed tasks older than 1 hour
task_manager.clear_completed(max_age_seconds=3600)

# Get task statistics
stats = task_manager.get_stats()
print(f"Total tasks: {stats['total']}, Pending: {stats['pending']}")
```

### Decision Effects

Aegis supports four decision effects:

1. **Allow**: Tool execution proceeds normally
2. **Deny**: Tool execution is blocked with `ForbiddenError`
3. **Sanitize**: Parameters are modified before execution
4. **Approval Needed**: Requires manual approval, execution happens in background when approved

### Error Handling

```python
from aegis import ForbiddenError, AuthError, TransportError

@aegis_guard(client, agent_id="agent", tool_name="risky_tool")
def risky_operation(data: str) -> str:
    return f"Processing: {data}"

try:
    result = risky_operation("sensitive data")
except ForbiddenError as e:
    print(f"Operation blocked: {e}")
except AuthError as e:
    print(f"Authentication failed: {e}")
except TransportError as e:
    print(f"Network error: {e}")
```

### Session Context

Pass additional context with your requests:

```python
session_data = {
    "user_id": "user-123",
    "session_id": "sess-456",
    "context": "production"
}

# Manually call decide with session
response = client.decide(
    agent_id="agent",
    tool_name="tool",
    params={"key": "value"},
    session=session_data
)
```

## API Reference

### AegisConfig

Configuration class for the SDK.

**Parameters:**
- `base_url` (str): Aegis Data Plane endpoint URL
- `api_key` (str): Tenant API key for authentication
- `timeout_s` (float): HTTP request timeout in seconds (default: 10.0)
- `retries` (int): Number of retry attempts (default: 2)
- `user_agent` (str): User agent string (default: "aegis-python-sdk/0.1.4")
- `log_level` (str): Logging level (default: "info")
- `debug` (bool): Enable debug mode (default: False)
- `approval_polling_enabled` (bool): Enable background polling for approval workflows (default: True)
- `approval_polling_initial_delay_s` (float): Initial delay before first approval status poll (default: 2.0)
- `approval_polling_max_delay_s` (float): Maximum delay between approval status polls (default: 60.0)
- `approval_polling_max_attempts` (int): Maximum polling attempts before timeout (default: 50)
- `approval_polling_jitter_ratio` (float): Jitter ratio for exponential backoff (default: 0.1)

**Environment Variables:**
- `AEGIS_BASE_URL`: Override base URL
- `AEGIS_API_KEY`: Override API key
- `AEGIS_TIMEOUT_S`: Override timeout
- `AEGIS_RETRIES`: Override retries
- `AEGIS_LOG_LEVEL`: Override log level
- `AEGIS_DEBUG`: Override debug mode
- `AEGIS_APPROVAL_POLLING_ENABLED`: Override approval polling enabled
- `AEGIS_APPROVAL_POLLING_INITIAL_DELAY_S`: Override initial polling delay
- `AEGIS_APPROVAL_POLLING_MAX_DELAY_S`: Override max polling delay
- `AEGIS_APPROVAL_POLLING_MAX_ATTEMPTS`: Override max polling attempts
- `AEGIS_APPROVAL_POLLING_JITTER_RATIO`: Override jitter ratio

### DecisionClient

Client for interacting with Aegis Decision API.

**Methods:**
- `decide(agent_id, tool_name, params, session=None)`: Request a decision
- `get_decision_status(decision_id)`: Poll for approval decision status
- `close()`: Close the HTTP client

### aegis_guard

Decorator for guarding tool functions.

**Parameters:**
- `client` (DecisionClient): Configured client instance
- `agent_id` (str): Agent identifier
- `tool_name` (str, optional): Tool name (defaults to function name)
- `approval_callback` (callable, optional): Callback for approval completion (result, error)

**Returns:** Decorated function

### ApprovalExecutor

Manages background polling and execution of approval tasks.

**Methods:**
- `start()`: Start the background executor
- `shutdown(wait=True)`: Shutdown the executor
- `submit_for_approval(task)`: Submit task for approval polling
- `get_queue_size()`: Get number of pending tasks
- `get_pending_tasks()`: Get list of pending approval tasks

### ApprovalTask

Represents a task awaiting approval.

**Attributes:**
- `task_id` (str): Unique task identifier
- `decision_id` (str): Decision identifier from API
- `func` (callable): Function to execute when approved
- `args` (tuple): Positional arguments for function
- `kwargs` (dict): Keyword arguments for function
- `callback` (callable): Optional completion callback
- `agent_id` (str): Agent identifier
- `tool_name` (str): Tool name
- `attempt_count` (int): Number of polling attempts

### TaskManager

Manages task lifecycle and provides query API.

**Methods:**
- `create_task(agent_id, tool_name, decision_id, task_id=None, metadata=None)`: Create new task
- `update_status(task_id, status, result=None, error=None)`: Update task status
- `get_task(task_id)`: Get task by ID
- `list_tasks(status=None, agent_id=None, tool_name=None)`: List tasks with filtering
- `delete_task(task_id)`: Delete a task
- `clear_completed(max_age_seconds=None)`: Clear completed tasks
- `get_stats()`: Get task statistics

### TaskInfo

Task information model.

**Attributes:**
- `task_id` (str): Task identifier
- `status` (TaskStatus): Current status
- `agent_id` (str): Agent identifier
- `tool_name` (str): Tool name
- `decision_id` (str): Decision identifier
- `created_at` (datetime): Creation timestamp
- `updated_at` (datetime): Last update timestamp
- `attempt_count` (int): Polling attempts
- `result` (any): Execution result
- `error` (str): Error message if failed

### Global Management Functions

- `get_global_executor()`: Get global approval executor
- `set_global_executor(executor)`: Set global approval executor
- `shutdown_global_executor()`: Shutdown global executor
- `get_global_task_manager()`: Get global task manager
- `reset_global_task_manager()`: Reset global task manager

## Developer Integration

### Quick Integration for Existing Codebases

Add Aegis to any Python function with minimal changes:

```python
# Before: Plain function
def send_email(to: str, subject: str, body: str):
    # Your email logic here
    pass

# After: Add one line decorator
from aegis import AegisConfig, DecisionClient, aegis_guard

config = AegisConfig(api_key="your-key")
client = DecisionClient(config)

@aegis_guard(client, agent_id="email-service")
def send_email(to: str, subject: str, body: str):
    # Your existing logic - no changes needed!
    pass
```

### Framework Integration Examples

#### FastAPI Services

```python
from fastapi import FastAPI
from aegis import AegisConfig, DecisionClient, aegis_guard, get_global_task_manager

app = FastAPI()
config = AegisConfig(api_key="your-key", approval_polling_enabled=True)
client = DecisionClient(config)

@aegis_guard(client, agent_id="api-service", tool_name="user.create")
def create_user(email: str, role: str):
    # User creation logic
    return {"user_id": "123", "email": email}

@app.post("/users")
def create_user_endpoint(email: str, role: str):
    try:
        result = create_user(email, role)
        return {"status": "success", "data": result}
    except ForbiddenError:
        return {"status": "denied", "message": "Operation not permitted"}

@app.get("/tasks")
def get_tasks():
    task_manager = get_global_task_manager()
    return task_manager.get_stats()
```

#### LangChain Agents

```python
from langchain_core.tools import tool
from aegis import AegisConfig, DecisionClient, aegis_guard

config = AegisConfig(api_key="your-key")
client = DecisionClient(config)

@tool
@aegis_guard(client, agent_id="langchain-agent", tool_name="web.search")
def web_search(query: str) -> str:
    """Search the web for information."""
    # Your search implementation
    return f"Search results for: {query}"

# Use in LangChain agent
from langchain.agents import create_react_agent
agent = create_react_agent(llm, [web_search], prompt)
```

#### Async Applications

```python
import asyncio
from aegis import AegisConfig, DecisionClient, aegis_guard

config = AegisConfig(api_key="your-key")
client = DecisionClient(config)

@aegis_guard(client, agent_id="async-service")
async def async_operation(data: dict) -> dict:
    # Async logic here
    await asyncio.sleep(1)
    return {"processed": True, "data": data}

# Works with both sync and async calls
result = await async_operation({"key": "value"})
```

### Approval Workflow Integration

For applications requiring manual approvals:

```python
from aegis import AegisConfig, DecisionClient, aegis_guard, get_global_task_manager, TaskStatus

# Enable approval polling
config = AegisConfig(
    api_key="your-key",
    approval_polling_enabled=True,
    approval_polling_max_attempts=200  # Poll longer for critical ops
)
client = DecisionClient(config)

def notify_admin(result, error):
    """Callback for approval completion."""
    if error:
        send_notification(f"Operation denied: {error}")
    else:
        send_notification(f"Operation completed: {result}")

@aegis_guard(client, agent_id="admin-ops", tool_name="server.reboot", approval_callback=notify_admin)
def reboot_server(server_id: str):
    # Critical operation requiring approval
    return f"Server {server_id} rebooted"

# In your web dashboard
def get_pending_approvals():
    task_manager = get_global_task_manager()
    return task_manager.list_tasks(status=TaskStatus.PENDING)
```

### Configuration Best Practices

```python
# Development
dev_config = AegisConfig(
    api_key="dev-key",
    debug=True,
    log_level="debug",
    approval_polling_enabled=False  # Disable polling in dev
)

# Production
prod_config = AegisConfig(
    api_key=os.getenv("AEGIS_API_KEY"),
    debug=False,
    approval_polling_enabled=True,
    approval_polling_max_attempts=100,
    timeout_s=30.0
)
```

### Error Handling Patterns

```python
from aegis import ForbiddenError, AuthError, TransportError

try:
    result = guarded_function(param="value")
except ForbiddenError as e:
    # Policy violation - log and handle
    logger.warning(f"Access denied: {e}")
    return {"error": "Operation not permitted"}
except AuthError as e:
    # Authentication issue
    logger.error(f"Auth failed: {e}")
    return {"error": "Authentication required"}
except TransportError as e:
    # Network/API issues
    logger.error(f"API error: {e}")
    return {"error": "Service temporarily unavailable"}
```

### Monitoring and Observability

```python
# Task monitoring
task_manager = get_global_task_manager()

# Get metrics for dashboards
stats = task_manager.get_stats()
print(f"Pending approvals: {stats['pending']}")

# Clean up old tasks periodically
task_manager.clear_completed(max_age_seconds=86400)  # 24 hours

# Query specific tasks
failed_tasks = task_manager.list_tasks(status=TaskStatus.FAILED)
for task in failed_tasks:
    logger.error(f"Task {task.task_id} failed: {task.error}")
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/mrsidrdx/aegis-python-sdk.git
cd aegis-python-sdk

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
make install-dev
```

### Running Tests

```bash
# Run all tests with coverage
make test-cov

# Run tests without coverage
make test-fast

# Run specific test file
pytest tests/test_config.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Run all linting checks
make lint

# Format code
make format

# Type checking
make type-check

# Security checks
make security
```

### Building

```bash
# Build distribution packages
make build

# Check packages
make check-dist
```

### Publishing

```bash
# Publish to Test PyPI
make publish-test

# Publish to PyPI (requires confirmation)
make publish
```

## Testing

The SDK includes comprehensive unit tests with 100% code coverage:

- Configuration management (`test_config.py`)
- Error handling (`test_errors.py`)
- Type definitions (`test_types.py`)
- Utility functions (`test_util.py`)
- Logging (`test_logging.py`)
- HTTP client (`test_http.py`)
- Decision client (`test_decision.py`)
- Guard decorator (`test_guard.py`)

Run tests with:

```bash
pytest --cov=aegis --cov-report=html
```

View coverage report at `htmlcov/index.html`.

## CI/CD

The project uses GitHub Actions for continuous integration and deployment:

- **CI Workflow**: Runs tests on multiple Python versions (3.11, 3.12, 3.13) and platforms (Linux, macOS, Windows)
- **Publish Workflow**: Automatically publishes to PyPI on release
- **Release Workflow**: Creates GitHub releases with changelog

## Versioning

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

See [CHANGELOG.md](CHANGELOG.md) for version history.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for:

- Development setup
- Code style guidelines
- Testing requirements
- Pull request process

## Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/mrsidrdx/aegis-python-sdk/issues)
- **Email**: bithal06@gmail.com

## Acknowledgments

Built with ❤️ by the Aegis team and contributors.