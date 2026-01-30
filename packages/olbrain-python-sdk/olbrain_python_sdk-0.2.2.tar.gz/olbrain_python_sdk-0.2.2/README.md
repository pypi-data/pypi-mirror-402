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
from olbrain import AgentClient

# Initialize client
client = AgentClient(
    agent_id="your-agent-id",
    api_key="sk_live_your_api_key"
)

# Create a session and send a message
session_id = client.create_session(title="My Chat")
response = client.send_and_wait(session_id, "Hello!")

print(response.text)
client.close()
```

## Features

- **Simple API** - Just `agent_id` and `api_key` to get started
- **Session Management** - Create, update, archive sessions with metadata
- **Sync & Streaming** - Both request-response and real-time streaming
- **Token Tracking** - Monitor usage and costs per request
- **Model Override** - Switch models per-message
- **Error Handling** - Comprehensive exception hierarchy

## Usage

### Synchronous Messaging

```python
from olbrain import AgentClient

with AgentClient(agent_id="your-agent-id", api_key="sk_live_your_key") as client:
    session_id = client.create_session()
    response = client.send_and_wait(session_id, "What is Python?")

    print(response.text)
    print(f"Tokens: {response.token_usage.total_tokens}")
```

### Real-Time Streaming

```python
from olbrain import AgentClient

client = AgentClient(agent_id="your-agent-id", api_key="sk_live_your_key")

def on_message(msg):
    print(f"[{msg['role']}]: {msg['content']}")

session_id = client.create_session(on_message=on_message)
client.send(session_id, "Tell me a story")
client.run()  # Blocks and processes messages
```

### Session Management

```python
# Create session with metadata
session_id = client.create_session(
    title="Support Chat",
    user_id="user-123",
    metadata={"source": "web"},
    mode="production"
)

# Get session info
info = client.get_session(session_id)
print(f"Messages: {info.message_count}")

# Get message history
messages = client.get_messages(session_id, limit=20)

# Archive session
client.delete_session(session_id)
```

### Model Override

```python
response = client.send_and_wait(
    session_id,
    "Complex question here",
    model="gpt-4"  # Override default model
)
```

### Error Handling

```python
from olbrain import AgentClient
from olbrain.exceptions import (
    AuthenticationError,
    SessionNotFoundError,
    RateLimitError,
    OlbrainError
)

try:
    client = AgentClient(agent_id="...", api_key="...")
    response = client.send_and_wait(session_id, "Hello")
except AuthenticationError:
    print("Invalid API key")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
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
| `send(session_id, message)` | Send message (async, use callback) |
| `send_and_wait(session_id, message)` | Send message and wait for response |
| `get_session(session_id)` | Get session details |
| `update_session(session_id, ...)` | Update session title/metadata |
| `delete_session(session_id)` | Archive a session |
| `get_messages(session_id)` | Get message history |
| `get_session_stats(session_id)` | Get token usage stats |
| `close()` | Clean up resources |

### Response Objects

**ChatResponse**
- `text` - Response text
- `success` - Success status
- `token_usage` - TokenUsage object
- `model_used` - Model that generated response

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
| `StreamingError` | Streaming error |

## Examples

See the [examples/](examples/) directory:

- `basic_usage.py` - Core SDK features
- `session_management.py` - Session CRUD operations
- `streaming_responses.py` - Real-time streaming
- `error_handling.py` - Error handling patterns
- `advanced_features.py` - Advanced usage

## License

MIT License - see [LICENSE](LICENSE)

## Links

- [PyPI](https://pypi.org/project/olbrain-python-sdk/)
- [GitHub](https://github.com/Olbrain/olbrain-python-sdk)
- [Issues](https://github.com/Olbrain/olbrain-python-sdk/issues)
