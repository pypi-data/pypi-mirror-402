# py-usepylon-sdk

[![PyPI version](https://img.shields.io/pypi/v/py-usepylon-sdk.svg)](https://pypi.org/project/py-usepylon-sdk/)
[![Python versions](https://img.shields.io/pypi/pyversions/py-usepylon-sdk.svg)](https://pypi.org/project/py-usepylon-sdk/)
[![Tests](https://github.com/mgmonteleone/py-usepylon-sdk/actions/workflows/tests.yml/badge.svg)](https://github.com/mgmonteleone/py-usepylon-sdk/actions)
[![Coverage](https://img.shields.io/codecov/c/github/mgmonteleone/py-usepylon-sdk)](https://codecov.io/gh/mgmonteleone/py-usepylon-sdk)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A modern, fully-typed Python SDK for the [Pylon](https://usepylon.com) customer support API.

## Features

- ✨ **Full API Coverage** - Issues, accounts, contacts, messages, webhooks, and more
- 🔒 **Type-safe** - Complete type hints with Pydantic v2 models
- ⚡ **Async Support** - Both sync and async clients for maximum flexibility
- 🔄 **Automatic Pagination** - Seamlessly iterate through all results
- 🎯 **Filter Builder** - Fluent API for building complex queries
- 🔔 **Webhook Handler** - Secure webhook signature verification and event routing
- 🛡️ **Robust Error Handling** - Detailed exception hierarchy for all error types
- 🐍 **Modern Python** - Requires Python 3.11+, uses modern typing syntax

## Installation

```bash
pip install py-usepylon-sdk
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv add py-usepylon-sdk
```

## Quick Start

### Basic Usage

```python
from pylon import PylonClient

# Initialize the client (uses PYLON_API_KEY env var by default)
with PylonClient(api_key="your-api-key") as client:
    # List recent issues
    for issue in client.issues.list(days=7):
        print(f"#{issue.number}: {issue.title}")

    # Get a specific issue
    issue = client.issues.get("issue_123")
    print(f"Status: {issue.state}")

    # List accounts
    for account in client.accounts.list():
        print(f"Account: {account.name}")
```

### Async Usage

```python
import asyncio
from pylon import AsyncPylonClient

async def main():
    async with AsyncPylonClient(api_key="your-api-key") as client:
        # Iterate through issues asynchronously
        async for issue in client.issues.list(days=7):
            print(f"#{issue.number}: {issue.title}")

        # Get a specific issue
        issue = await client.issues.get("issue_123")
        print(f"Status: {issue.state}")

asyncio.run(main())
```

### Pagination

The SDK handles pagination automatically. Just iterate:

```python
# All pages are fetched automatically as you iterate
for issue in client.issues.list():
    print(issue.title)

# Or collect all results at once
all_issues = client.issues.list().collect()
print(f"Found {len(all_issues)} issues")
```

### Filter Builder

Build complex queries with the fluent filter API:

```python
from pylon.filters import Field, And, Or

# Simple equality filter
issues = client.issues.list(
    filter=Field("state").eq("open")
)

# Complex filters with AND/OR
issues = client.issues.list(
    filter=(
        Field("state").eq("open") &
        Field("priority").gte(3)
    ) | Field("assignee_id").is_null()
)

# Date range filters
from datetime import datetime, timedelta
issues = client.issues.list(
    filter=Field("created_at").between(
        datetime.now() - timedelta(days=30),
        datetime.now()
    )
)
```

## Webhook Handling

Securely handle incoming Pylon webhooks:

```python
from pylon.webhooks import WebhookHandler
from pylon.webhooks.events import IssueNewEvent, IssueAssignedEvent

handler = WebhookHandler(secret="your-webhook-secret")

@handler.on(IssueNewEvent)
def handle_new_issue(event: IssueNewEvent):
    print(f"New issue created: {event.issue_title}")

@handler.on(IssueAssignedEvent)
def handle_assigned(event: IssueAssignedEvent):
    print(f"Issue assigned to: {event.assignee_id}")

@handler.on_any()
def handle_all_events(event):
    print(f"Received event: {event.event_type}")

# In your web framework (Flask example)
@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Pylon-Signature")
    timestamp = request.headers.get("X-Pylon-Timestamp")

    handler.handle(
        payload=request.get_data(),
        signature=signature,
        timestamp=timestamp
    )
    return "OK", 200
```

## Error Handling

The SDK provides a detailed exception hierarchy:

```python
from pylon.exceptions import (
    PylonError,              # Base exception
    PylonAPIError,           # API-related errors
    PylonAuthenticationError,  # 401 - Invalid API key
    PylonNotFoundError,      # 404 - Resource not found
    PylonValidationError,    # 400 - Invalid request
    PylonRateLimitError,     # 429 - Rate limited
    PylonServerError,        # 5xx - Server errors
)

try:
    issue = client.issues.get("nonexistent")
except PylonNotFoundError as e:
    print(f"Issue not found: {e.message}")
except PylonAuthenticationError:
    print("Invalid API key")
except PylonRateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except PylonAPIError as e:
    print(f"API error [{e.status_code}]: {e.message}")
```

## Available Resources

| Resource | Description |
|----------|-------------|
| `client.issues` | Support tickets and conversations |
| `client.accounts` | Customer accounts/companies |
| `client.contacts` | Customer contacts |
| `client.users` | Team members/agents |
| `client.teams` | Support teams |
| `client.tags` | Issue and account tags |
| `client.messages` | Conversation messages |
| `client.tasks` | Follow-up tasks |
| `client.projects` | Customer projects |

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/mgmonteleone/py-usepylon-sdk.git
cd py-usepylon-sdk

# Install with development dependencies
uv sync --all-extras
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/pylon --cov-report=term-missing
```

### Linting and Type Checking

```bash
uv run ruff check .
uv run mypy src/
```

### Documentation

Documentation is built with MkDocs:

```bash
uv run mkdocs serve  # Local development server
uv run mkdocs build  # Build static site
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.
