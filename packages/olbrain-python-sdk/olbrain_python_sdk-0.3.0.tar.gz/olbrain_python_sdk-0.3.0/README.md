# Olbrain Python SDK

[![PyPI version](https://badge.fury.io/py/olbrain-python-sdk.svg)](https://pypi.org/project/olbrain-python-sdk/)
[![Python Support](https://img.shields.io/pypi/pyversions/olbrain-python-sdk.svg)](https://pypi.org/project/olbrain-python-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Official Python SDK for integrating Olbrain AI agents into your applications.

## Installation

```bash
pip install olbrain-python-sdk
```

## Quick Start

```python
from olbrain import AgentClient, ChatResponse

# Initialize client
client = AgentClient(
    agent_id="your-agent-id",
    api_key="sk_live_your_api_key"
)

# Create a session
session_id = client.create_session(title="My Chat")

# Send a message
response_data = client.send(session_id, "Hello!")

# Parse response
response = ChatResponse.from_dict(response_data, session_id)
print(response.text)
print(f"Cost: ${response.cost:.6f}")

client.close()
```

## Features

- **Simple API** - Just `agent_id` and `api_key` to get started
- **Session-based Conversations** - Maintain conversation context across messages
- **Synchronous & Async** - Both sync responses and async webhook patterns
- **Token Tracking** - Monitor usage and costs per request
- **Model Override** - Switch models per-message
- **Error Handling** - Comprehensive exception hierarchy

## Usage

### Basic Messaging

```python
from olbrain import AgentClient, ChatResponse

with AgentClient(agent_id="your-agent-id", api_key="sk_live_your_key") as client:
    # Create session
    session_id = client.create_session(
        title="Support Chat",
        user_id="user-123",
        mode="production"
    )

    # Send message and get response
    response_data = client.send(session_id, "What is Python?")

    # Parse response
    response = ChatResponse.from_dict(response_data, session_id)
    print(response.text)
    print(f"Tokens: {response.token_usage.total_tokens}")
    print(f"Model: {response.model}")
    print(f"Cost: ${response.cost:.6f}")
```

### Continuing a Conversation

```python
# Send multiple messages in the same session
session_id = client.create_session(title="Q&A Session")

# First message
response1 = client.send(session_id, "What is machine learning?")
print(ChatResponse.from_dict(response1, session_id).text)

# Follow-up message - agent remembers context
response2 = client.send(session_id, "Can you give me an example?")
print(ChatResponse.from_dict(response2, session_id).text)
```

### Model Override

```python
# Use a specific model for a message
response_data = client.send(
    session_id,
    "Complex question here",
    model="gpt-4o"  # Override default model
)

response = ChatResponse.from_dict(response_data, session_id)
print(f"Used model: {response.model}")
```

### Async Webhook Pattern

```python
# Send message with async processing
# Response will be delivered to your webhook URL
result = client.send_async(
    session_id="existing-session",
    message="Process this in the background",
    webhook_url="https://your-app.com/webhook"
)

print(f"Message queued: {result['success']}")
```

### Message Metadata

```python
# Include custom metadata with messages
response_data = client.send(
    session_id,
    "Tell me a joke",
    metadata={"category": "humor", "source": "example"}
)
```

### Error Handling

```python
from olbrain import AgentClient
from olbrain.exceptions import (
    AuthenticationError,
    RateLimitError,
    NetworkError,
    OlbrainError
)

try:
    client = AgentClient(agent_id="...", api_key="...")
    response = client.send(session_id, "Hello")
except AuthenticationError:
    print("Invalid API key")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except NetworkError as e:
    print(f"Network error: {e}")
except OlbrainError as e:
    print(f"Error: {e}")
```

## Configuration

### Environment Variables

```bash
export OLBRAIN_API_KEY="sk_live_your_api_key"
export OLBRAIN_AGENT_ID="your-agent-id"
```

### Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## API Reference

### AgentClient

| Method | Description |
|--------|-------------|
| `create_session()` | Create a new chat session |
| `send(session_id, message, ...)` | Send message and get response (sync) |
| `send_async(session_id, message, webhook_url, ...)` | Send message for async processing |
| `close()` | Clean up resources |

#### Deprecated Methods (v0.3.0+)

The following methods are deprecated and raise `NotImplementedError`:
- `send_and_wait()` - Use `send()` instead
- `get_session()` - Not supported by webhook API
- `update_session()` - Not supported by webhook API
- `delete_session()` - Not supported by webhook API
- `get_messages()` - Not supported by webhook API
- `get_session_stats()` - Not supported by webhook API
- `listen()` - SSE streaming not supported
- `run()` - SSE streaming not supported

### Response Objects

**ChatResponse**
- `text` - Response text
- `session_id` - Session identifier
- `success` - Success status
- `token_usage` - TokenUsage object
- `model` - Model that generated response
- `processing_time_ms` - Processing time in milliseconds
- `cost` - Cost in USD
- `mode` - Response mode ("sync" or "session_created")
- `metadata` - Optional metadata
- `error` - Error message if failed

**TokenUsage**
- `prompt_tokens` - Input tokens
- `completion_tokens` - Output tokens
- `total_tokens` - Total tokens
- `cost` - Cost in USD

### Exceptions

| Exception | Description |
|-----------|-------------|
| `OlbrainError` | Base exception |
| `AuthenticationError` | Invalid API key |
| `SessionNotFoundError` | Session not found |
| `RateLimitError` | Rate limit exceeded |
| `NetworkError` | Connection issues |
| `ValidationError` | Invalid input |

## Migration from v0.2.x

See [MIGRATION.md](MIGRATION.md) for detailed migration guide from v0.2.x to v0.3.0.

Major changes in v0.3.0:
- Removed SSE streaming (use sync or async webhook patterns)
- Removed session management endpoints (get/update/delete)
- Removed message history retrieval
- Updated response schema field names (`model_used` → `model`, etc.)

## Examples

See the [examples/](examples/) directory:

- `basic_usage.py` - Core SDK features (current API)
- `error_handling.py` - Error handling patterns
- `advanced_features.py` - Advanced usage

**Note:** `streaming_responses.py` and `session_management.py` are deprecated and kept for reference only.

## License

MIT License - see [LICENSE](LICENSE)

## Links

- [PyPI](https://pypi.org/project/olbrain-python-sdk/)
- [GitHub](https://github.com/Olbrain/olbrain-python-sdk)
- [Issues](https://github.com/Olbrain/olbrain-python-sdk/issues)
