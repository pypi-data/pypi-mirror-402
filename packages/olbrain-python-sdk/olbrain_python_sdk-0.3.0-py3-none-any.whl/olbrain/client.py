"""
Olbrain Python SDK - Simple Client
Clean API for agent interaction with real-time message streaming
"""

import requests
import logging
import time
import warnings
from typing import Callable, Optional, Dict, Any, List

from .streaming import MessageStream
from .session import ChatResponse, SessionInfo, TokenUsage
from .exceptions import (
    OlbrainError,
    AuthenticationError,
    NetworkError,
    SessionNotFoundError,
    RateLimitError
)

logger = logging.getLogger(__name__)


class AgentClient:
    """
    Simple client for interacting with Olbrain agents

    Provides unified message handling - all messages (responses + scheduled)
    come through the same callback stream.

    Args:
        agent_id: Agent identifier
        api_key: API key (starts with 'sk_live_' or 'org_live_')
        agent_url: Optional custom agent URL (auto-constructed if not provided)

    Example:
        >>> from olbrain import AgentClient
        >>>
        >>> client = AgentClient(agent_id="agent-123", api_key="sk_live_...")
        >>>
        >>> def on_message(msg):
        ...     print(f"{msg['role']}: {msg['content']}")
        >>>
        >>> session = client.create_session(on_message=on_message)
        >>> client.send(session, "Hello!")
        >>> client.run()  # Blocks, receives all messages
    """

    def __init__(
        self,
        agent_id: str,
        api_key: str,
        agent_url: Optional[str] = None
    ):
        """
        Initialize Olbrain client

        Args:
            agent_id: Agent identifier
            api_key: API key (must start with 'sk_live_', 'org_live_', 'sk_', or 'org_')
            agent_url: Optional agent URL (auto-constructed if not provided)

        Raises:
            ValueError: If agent_id or api_key is invalid
        """
        if not agent_id:
            raise ValueError("agent_id is required")

        valid_prefixes = ('sk_live_', 'org_live_', 'sk_', 'org_')
        if not api_key or not api_key.startswith(valid_prefixes):
            raise ValueError(
                "Invalid API key - must start with 'sk_live_', 'org_live_', 'sk_', or 'org_'"
            )

        self.agent_id = agent_id
        self.api_key = api_key

        # Auto-construct agent URL if not provided
        if agent_url:
            self.agent_url = agent_url.rstrip('/')
        else:
            # Use default Cloud Run URL pattern
            self.agent_url = f"https://agent-{agent_id}-851487020021.us-central1.run.app"

        self._streams = {}  # session_id -> MessageStream
        self._running = False

        logger.info(f"AgentClient initialized for {agent_id}")

    def create_session(
        self,
        on_message: Callable = None,
        title: str = None,
        user_id: str = None,
        metadata: Dict[str, Any] = None,
        mode: str = "production",
        description: str = None
    ) -> str:
        """
        Create new session and optionally start listening for messages.

        Args:
            on_message: Optional callback function(message_dict) for real-time messages.
                       If provided, starts listening automatically.
                       message_dict = {
                           'role': 'user' | 'assistant',
                           'content': str,
                           'timestamp': str,
                           'token_usage': {...}
                       }
            title: Optional title for the session
            user_id: Optional user identifier for tracking
            metadata: Optional metadata dict (can include 'session_description')
            mode: Session mode - 'development', 'testing', or 'production' (default)
            description: Optional session description

        Returns:
            session_id (string)

        Raises:
            OlbrainError: If session creation fails
            AuthenticationError: If API key is invalid

        Example:
            >>> # Create session with streaming
            >>> def handle_msg(msg):
            ...     print(msg['content'])
            >>> session = client.create_session(on_message=handle_msg, title="My Chat")

            >>> # Create session without streaming (for sync usage)
            >>> session = client.create_session(title="Support Chat", user_id="user-123")
        """
        if mode not in ['development', 'testing', 'production']:
            raise ValueError("mode must be 'development', 'testing', or 'production'")

        try:
            # Build request payload
            request_metadata = metadata.copy() if metadata else {}
            if description:
                request_metadata['session_description'] = description

            payload = {
                'message': title or "New Session",
                'response_mode': 'sync',
                'mode': mode
            }
            if user_id:
                payload['user_id'] = user_id
            if request_metadata:
                payload['metadata'] = request_metadata

            # Create session via webhook endpoint
            response = requests.post(
                f"{self.agent_url}/api/agent/webhook",
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                json=payload,
                timeout=30
            )

            self._handle_response_errors(response, "create session")

            data = response.json()
            session_id = data.get('session_id')

            if not session_id:
                raise OlbrainError("No session_id in response")

            logger.info(f"Created session {session_id}")

            # Warn if on_message callback provided (streaming no longer supported)
            if on_message:
                warnings.warn(
                    "on_message callback is no longer supported. SSE streaming has been removed. "
                    "Use send() for synchronous responses or send_async() with a webhook URL.",
                    DeprecationWarning,
                    stacklevel=2
                )

            return session_id

        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Network error creating session: {e}")

    def send(
        self,
        session_id: str,
        message: str,
        user_id: str = None,
        metadata: Dict[str, Any] = None,
        model: str = None,
        mode: str = "production",
        attachments: List[Dict] = None,
        response_mode: str = "sync",
        webhook_url: str = None
    ) -> Dict[str, Any]:
        """
        Send message to agent. Response comes via callback if listening,
        or returned directly in sync mode.

        Args:
            session_id: Session identifier
            message: Message text to send
            user_id: Optional user identifier
            metadata: Optional message metadata
            model: Optional model override (e.g., 'gpt-4', 'claude-3-opus')
            mode: Session mode - 'development', 'testing', or 'production'
            attachments: Optional list of file attachments
            response_mode: Response mode - 'sync' or 'async' (default: 'sync')
            webhook_url: Webhook URL for async responses (required if response_mode='async')

        Returns:
            Response dict with success, response, token_usage, etc.

        Raises:
            ValueError: If message is empty or webhook_url missing for async mode
            OlbrainError: If send fails
            SessionNotFoundError: If session doesn't exist

        Example:
            >>> response = client.send(session_id, "What's 2+2?")
            >>> print(response['response'])
        """
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")

        if response_mode == "async" and not webhook_url:
            raise ValueError("webhook_url is required when response_mode='async'")

        try:
            payload = {
                'session_id': session_id,
                'message': message.strip(),
                'response_mode': response_mode,
                'mode': mode
            }
            if user_id:
                payload['user_id'] = user_id
            if metadata:
                payload['metadata'] = metadata
            if model:
                payload['model'] = model
            if attachments:
                payload['attachments'] = attachments
            if webhook_url:
                payload['webhook_url'] = webhook_url

            response = requests.post(
                f"{self.agent_url}/api/agent/webhook",
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                json=payload,
                timeout=120
            )

            self._handle_response_errors(response, "send message")

            data = response.json()
            logger.debug(f"Sent message to session {session_id}")
            return data

        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Network error sending message: {e}")

    def send_and_wait(
        self,
        session_id: str,
        message: str,
        user_id: str = None,
        metadata: Dict[str, Any] = None,
        model: str = None,
        timeout: int = 120
    ) -> ChatResponse:
        """
        Send message and wait for response (synchronous).

        DEPRECATED: This method is deprecated. Use send() instead, which provides
        the same functionality with the correct API endpoint.

        This method sends a message and returns a ChatResponse object
        with the agent's reply. Use this for simple request-response patterns.

        Args:
            session_id: Session identifier
            message: Message text to send
            user_id: Optional user identifier
            metadata: Optional message metadata
            model: Optional model override
            timeout: Request timeout in seconds (default: 120, not used)

        Returns:
            ChatResponse with text, token_usage, model, etc.

        Raises:
            ValueError: If message is empty
            OlbrainError: If send fails
            SessionNotFoundError: If session doesn't exist

        Example:
            >>> response = client.send_and_wait(session_id, "Explain quantum computing")
            >>> print(response.text)
            >>> print(f"Tokens used: {response.token_usage.total_tokens}")
        """
        warnings.warn(
            "send_and_wait() is deprecated and will be removed in v0.4.0. "
            "Use send() instead, which provides the same functionality.",
            DeprecationWarning,
            stacklevel=2
        )

        response_data = self.send(
            session_id=session_id,
            message=message,
            user_id=user_id,
            metadata=metadata,
            model=model
        )
        return ChatResponse.from_dict(response_data, session_id)

    def send_async(
        self,
        session_id: str,
        message: str,
        webhook_url: str,
        user_id: str = None,
        metadata: Dict[str, Any] = None,
        model: str = None,
        mode: str = "production",
        attachments: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Send message with async processing - response delivered to webhook_url.

        The agent will process the message asynchronously and send the response
        to the specified webhook URL when ready.

        Args:
            session_id: Session identifier
            message: Message text to send
            webhook_url: URL to receive the async response
            user_id: Optional user identifier
            metadata: Optional message metadata
            model: Optional model override
            mode: Session mode - 'development', 'testing', or 'production'
            attachments: Optional list of file attachments

        Returns:
            Dict with acknowledgment (success, session_id, message)

        Raises:
            ValueError: If message or webhook_url is empty
            OlbrainError: If send fails

        Example:
            >>> result = client.send_async(
            ...     session_id="sess-123",
            ...     message="Process this in the background",
            ...     webhook_url="https://myapp.com/webhook"
            ... )
            >>> print(f"Message queued: {result['success']}")
        """
        return self.send(
            session_id=session_id,
            message=message,
            user_id=user_id,
            metadata=metadata,
            model=model,
            mode=mode,
            attachments=attachments,
            response_mode="async",
            webhook_url=webhook_url
        )

    def listen(self, session_id: str, on_message: Callable):
        """
        Start listening for messages on existing session

        DEPRECATED: SSE streaming is no longer supported by the current API.
        The webhook-only API does not provide SSE streaming endpoints.

        Args:
            session_id: Session to listen to
            on_message: Callback function(message_dict) for messages

        Raises:
            NotImplementedError: Always raised as this feature is no longer supported

        Example:
            >>> # This method is deprecated and will raise NotImplementedError
            >>> # client.listen("existing-session-id", on_message=handle_msg)
        """
        raise NotImplementedError(
            "SSE streaming is no longer supported. "
            "The agent API only supports synchronous message sending via the webhook endpoint. "
            "Use send() for synchronous responses or send_async() with a webhook URL for async processing."
        )

    def run(self):
        """
        Block forever and process message callbacks

        DEPRECATED: SSE streaming is no longer supported by the current API.
        The webhook-only API does not provide SSE streaming endpoints.

        Call this to keep your program running and receive messages.
        Press Ctrl+C to exit gracefully.

        Raises:
            NotImplementedError: Always raised as this feature is no longer supported

        Example:
            >>> # This method is deprecated and will raise NotImplementedError
            >>> # client.run()  # Blocks until Ctrl+C
        """
        raise NotImplementedError(
            "SSE streaming is no longer supported. "
            "The agent API only supports synchronous message sending via the webhook endpoint. "
            "Use send() for synchronous responses or send_async() with a webhook URL for async processing."
        )

    def close(self):
        """
        Stop all streams and cleanup resources

        Automatically called on Ctrl+C or when using context manager.
        """
        logger.info("Closing client...")
        self._running = False

        # Stop all streams
        for session_id, stream in list(self._streams.items()):
            stream.stop()

        self._streams.clear()
        logger.info("Client closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def __repr__(self) -> str:
        return f"AgentClient(agent_id={self.agent_id})"

    # -------------------------------------------------------------------------
    # Session Management Methods
    # -------------------------------------------------------------------------

    def get_session(self, session_id: str) -> SessionInfo:
        """
        Get session details.

        DEPRECATED: This method is no longer supported by the current API.
        The webhook-only API does not provide session management endpoints.

        Args:
            session_id: Session identifier

        Raises:
            NotImplementedError: Always raised as this feature is no longer supported

        Example:
            >>> # This method is deprecated and will raise NotImplementedError
            >>> # info = client.get_session(session_id)
        """
        raise NotImplementedError(
            "Session management is no longer supported. "
            "The agent API only supports message sending via the webhook endpoint. "
            "Use create_session() and send() for message interactions."
        )

    def update_session(
        self,
        session_id: str,
        title: str = None,
        metadata: Dict[str, Any] = None,
        status: str = None
    ) -> SessionInfo:
        """
        Update session details.

        DEPRECATED: This method is no longer supported by the current API.
        The webhook-only API does not provide session management endpoints.

        Args:
            session_id: Session identifier
            title: New session title (optional)
            metadata: New metadata dict (optional)
            status: New status - 'active' or 'archived' (optional)

        Raises:
            NotImplementedError: Always raised as this feature is no longer supported

        Example:
            >>> # This method is deprecated and will raise NotImplementedError
            >>> # updated = client.update_session(session_id, title="Renamed Chat")
        """
        raise NotImplementedError(
            "Session management is no longer supported. "
            "The agent API only supports message sending via the webhook endpoint. "
            "Use create_session() and send() for message interactions."
        )

    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """
        Archive/delete a session.

        DEPRECATED: This method is no longer supported by the current API.
        The webhook-only API does not provide session management endpoints.

        Args:
            session_id: Session identifier

        Raises:
            NotImplementedError: Always raised as this feature is no longer supported

        Example:
            >>> # This method is deprecated and will raise NotImplementedError
            >>> # result = client.delete_session(session_id)
        """
        raise NotImplementedError(
            "Session management is no longer supported. "
            "The agent API only supports message sending via the webhook endpoint. "
            "Sessions are managed automatically by the agent."
        )

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get session statistics (token usage, message counts, etc.).

        DEPRECATED: This method is no longer supported by the current API.
        The webhook-only API does not provide session statistics endpoints.

        Args:
            session_id: Session identifier

        Raises:
            NotImplementedError: Always raised as this feature is no longer supported

        Example:
            >>> # This method is deprecated and will raise NotImplementedError
            >>> # stats = client.get_session_stats(session_id)
        """
        raise NotImplementedError(
            "Session statistics are no longer supported. "
            "The agent API only supports message sending via the webhook endpoint. "
            "Token usage is returned with each message response."
        )

    def get_messages(
        self,
        session_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get message history for a session.

        DEPRECATED: This method is no longer supported by the current API.
        The webhook-only API does not provide message history endpoints.

        Args:
            session_id: Session identifier
            limit: Maximum messages to return (default: 20)
            offset: Number of messages to skip (default: 0)

        Raises:
            NotImplementedError: Always raised as this feature is no longer supported

        Example:
            >>> # This method is deprecated and will raise NotImplementedError
            >>> # result = client.get_messages(session_id, limit=50)
        """
        raise NotImplementedError(
            "Message history retrieval is no longer supported. "
            "The agent API only supports message sending via the webhook endpoint. "
            "You must maintain conversation history in your application if needed."
        )

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _handle_response_errors(self, response: requests.Response, operation: str):
        """Handle HTTP response errors and raise appropriate exceptions."""
        if response.status_code == 200:
            return

        if response.status_code == 401:
            raise AuthenticationError("Invalid API key")

        if response.status_code == 404:
            raise SessionNotFoundError(f"Session not found")

        if response.status_code == 429:
            try:
                data = response.json()
                retry_after = data.get('detail', {}).get('retry_after')
                raise RateLimitError(
                    f"Rate limit exceeded",
                    retry_after=retry_after
                )
            except (ValueError, KeyError):
                raise RateLimitError("Rate limit exceeded")

        # Generic error
        try:
            error_detail = response.json().get('detail', response.text)
        except ValueError:
            error_detail = response.text

        raise OlbrainError(
            f"Failed to {operation}: {response.status_code} - {error_detail}"
        )
