"""
Basic tests for AgentClient
"""
import pytest
import requests_mock
from olbrain import AgentClient, ChatResponse
from olbrain.exceptions import AuthenticationError, OlbrainError


class TestAgentClient:
    def test_client_initialization(self):
        """Test AgentClient initialization with default parameters."""
        client = AgentClient(agent_id="test-agent", api_key="sk_live_test-key")
        assert client.agent_id == "test-agent"
        assert client.api_key == "sk_live_test-key"
        assert client.agent_url == "https://agent-test-agent-851487020021.us-central1.run.app"

    def test_client_initialization_with_custom_url(self):
        """Test AgentClient initialization with custom URL."""
        custom_url = "https://custom-agent-url.com"
        client = AgentClient(
            agent_id="test-agent",
            api_key="sk_live_test-key",
            agent_url=custom_url
        )
        assert client.agent_url == custom_url

    @requests_mock.Mocker()
    def test_create_session_success(self, m):
        """Test successful session creation."""
        client = AgentClient(agent_id="test-agent", api_key="sk_live_test-key")

        # Mock the webhook endpoint for session creation
        m.post(
            f"{client.agent_url}/api/agent/webhook",
            json={"session_id": "test-session-123", "success": True, "response": "Session created"},
            status_code=200
        )

        session_id = client.create_session()
        assert session_id == "test-session-123"

    @requests_mock.Mocker()
    def test_create_session_auth_error(self, m):
        """Test session creation with authentication error."""
        client = AgentClient(agent_id="test-agent", api_key="sk_live_invalid-key")

        # Mock authentication error
        m.post(
            f"{client.agent_url}/api/agent/webhook",
            json={"error": "Invalid API key"},
            status_code=401
        )

        with pytest.raises(AuthenticationError):
            client.create_session()

    @requests_mock.Mocker()
    def test_send_message_success(self, m):
        """Test successful message sending."""
        client = AgentClient(agent_id="test-agent", api_key="sk_live_test-key")
        session_id = "test-session-123"

        # Mock the webhook endpoint for sending message
        m.post(
            f"{client.agent_url}/api/agent/webhook",
            json={
                "success": True,
                "session_id": session_id,
                "response": "Hello! How can I help you?",
                "token_usage": {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25},
                "model": "gpt-4o",
                "processing_time_ms": 1234,
                "cost": 0.0012,
                "mode": "sync"
            },
            status_code=200
        )

        response_data = client.send(session_id, "Hello")
        assert response_data["success"] == True
        assert response_data["response"] == "Hello! How can I help you?"

        # Parse as ChatResponse
        chat_response = ChatResponse.from_dict(response_data, session_id)
        assert chat_response.text == "Hello! How can I help you?"
        assert chat_response.model == "gpt-4o"
        assert chat_response.cost == 0.0012
        assert chat_response.mode == "sync"

    def test_get_session_deprecated(self):
        """Test that get_session raises NotImplementedError."""
        client = AgentClient(agent_id="test-agent", api_key="sk_live_test-key")

        with pytest.raises(NotImplementedError):
            client.get_session("test-session-123")

    def test_update_session_deprecated(self):
        """Test that update_session raises NotImplementedError."""
        client = AgentClient(agent_id="test-agent", api_key="sk_live_test-key")

        with pytest.raises(NotImplementedError):
            client.update_session("test-session-123", title="New Title")

    def test_delete_session_deprecated(self):
        """Test that delete_session raises NotImplementedError."""
        client = AgentClient(agent_id="test-agent", api_key="sk_live_test-key")

        with pytest.raises(NotImplementedError):
            client.delete_session("test-session-123")

    # API Key Validation Tests
    def test_api_key_with_sk_live_prefix_accepted(self):
        """Test that API keys with sk_live_ prefix are accepted."""
        client = AgentClient(agent_id="test-agent", api_key="sk_live_test123456")
        assert client.api_key == "sk_live_test123456"

    def test_api_key_with_org_live_prefix_accepted(self):
        """Test that API keys with org_live_ prefix are accepted."""
        client = AgentClient(agent_id="test-agent", api_key="org_live_test123456")
        assert client.api_key == "org_live_test123456"

    def test_api_key_with_sk_prefix_accepted(self):
        """Test that API keys with sk_ prefix are accepted (dev/test)."""
        client = AgentClient(agent_id="test-agent", api_key="sk_test123456")
        assert client.api_key == "sk_test123456"

    def test_api_key_with_org_prefix_accepted(self):
        """Test that API keys with org_ prefix are accepted (dev/test)."""
        client = AgentClient(agent_id="test-agent", api_key="org_test123456")
        assert client.api_key == "org_test123456"

    def test_api_key_with_ak_prefix_rejected(self):
        """Test that API keys with ak_ prefix are rejected."""
        with pytest.raises(ValueError, match="Invalid API key"):
            AgentClient(agent_id="test-agent", api_key="ak_test123456")

    def test_api_key_with_invalid_prefix_rejected(self):
        """Test that API keys with invalid prefixes are rejected."""
        with pytest.raises(ValueError, match="Invalid API key"):
            AgentClient(agent_id="test-agent", api_key="invalid_key123")

    def test_empty_api_key_rejected(self):
        """Test that empty API keys are rejected."""
        with pytest.raises(ValueError, match="Invalid API key"):
            AgentClient(agent_id="test-agent", api_key="")

    def test_none_api_key_rejected(self):
        """Test that None API keys are rejected."""
        with pytest.raises(ValueError, match="Invalid API key"):
            AgentClient(agent_id="test-agent", api_key=None)