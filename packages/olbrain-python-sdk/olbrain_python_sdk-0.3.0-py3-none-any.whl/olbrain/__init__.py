"""
Olbrain Python SDK
Simple client for Olbrain AI agents

Example:
    >>> from olbrain import AgentClient
    >>>
    >>> client = AgentClient(agent_id="agent-123", api_key="sk_live_...")
    >>>
    >>> # Create session and send messages
    >>> session_id = client.create_session(title="My Chat")
    >>> response = client.send(session_id, "Hello!")
    >>> print(response['response'])
    >>>
    >>> # Parse response as ChatResponse object
    >>> from olbrain import ChatResponse
    >>> chat_response = ChatResponse.from_dict(response, session_id)
    >>> print(chat_response.text)
    >>> print(f"Tokens: {chat_response.token_usage.total_tokens}")
"""

from .client import AgentClient
from .session import ChatResponse, SessionInfo, TokenUsage, Message, Session
from .exceptions import (
    OlbrainError,
    AuthenticationError,
    NetworkError,
    SessionError,
    SessionNotFoundError,
    RateLimitError,
    ValidationError,
    StreamingError
)

__version__ = "0.3.0"
__author__ = "Olbrain Team"
__email__ = "support@olbrain.com"

__all__ = [
    # Main client
    'AgentClient',
    # Data classes
    'ChatResponse',
    'SessionInfo',
    'TokenUsage',
    'Message',
    'Session',
    # Exceptions
    'OlbrainError',
    'AuthenticationError',
    'NetworkError',
    'SessionError',
    'SessionNotFoundError',
    'RateLimitError',
    'ValidationError',
    'StreamingError'
]
