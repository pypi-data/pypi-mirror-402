"""
Basic tests for Session classes
"""
import pytest
from olbrain.session import ChatResponse, TokenUsage


class TestChatResponse:
    def test_chat_response_from_dict_with_new_fields(self):
        """Test ChatResponse.from_dict() with new API response format."""
        response_data = {
            "success": True,
            "session_id": "test-session-123",
            "response": "Hello! How can I help you?",
            "token_usage": {
                "prompt_tokens": 10,
                "completion_tokens": 15,
                "total_tokens": 25,
                "cost": 0.0012
            },
            "model": "gpt-4o",
            "processing_time_ms": 1234,
            "cost": 0.0012,
            "mode": "sync"
        }

        chat_response = ChatResponse.from_dict(response_data)

        assert chat_response.text == "Hello! How can I help you?"
        assert chat_response.session_id == "test-session-123"
        assert chat_response.success == True
        assert chat_response.model == "gpt-4o"
        assert chat_response.processing_time_ms == 1234
        assert chat_response.cost == 0.0012
        assert chat_response.mode == "sync"
        assert chat_response.token_usage.total_tokens == 25

    def test_chat_response_from_dict_with_fallback_session_id(self):
        """Test ChatResponse.from_dict() uses fallback session_id."""
        response_data = {
            "response": "Test response",
            "success": True
        }

        chat_response = ChatResponse.from_dict(response_data, session_id="fallback-session")

        assert chat_response.session_id == "fallback-session"
        assert chat_response.text == "Test response"

    def test_chat_response_to_dict(self):
        """Test ChatResponse.to_dict() with new fields."""
        token_usage = TokenUsage(
            prompt_tokens=10,
            completion_tokens=15,
            total_tokens=25,
            cost=0.0012
        )

        chat_response = ChatResponse(
            text="Test response",
            session_id="test-session",
            success=True,
            token_usage=token_usage,
            model="gpt-4o",
            processing_time_ms=1234,
            cost=0.0012,
            mode="sync"
        )

        result = chat_response.to_dict()

        assert result["text"] == "Test response"
        assert result["session_id"] == "test-session"
        assert result["model"] == "gpt-4o"
        assert result["processing_time_ms"] == 1234
        assert result["cost"] == 0.0012
        assert result["mode"] == "sync"
        assert result["token_usage"]["total_tokens"] == 25


class TestTokenUsage:
    def test_token_usage_from_dict(self):
        """Test TokenUsage.from_dict()."""
        data = {
            "prompt_tokens": 10,
            "completion_tokens": 15,
            "total_tokens": 25,
            "cost": 0.0012
        }

        token_usage = TokenUsage.from_dict(data)

        assert token_usage.prompt_tokens == 10
        assert token_usage.completion_tokens == 15
        assert token_usage.total_tokens == 25
        assert token_usage.cost == 0.0012

    def test_token_usage_to_dict(self):
        """Test TokenUsage.to_dict()."""
        token_usage = TokenUsage(
            prompt_tokens=10,
            completion_tokens=15,
            total_tokens=25,
            cost=0.0012
        )

        result = token_usage.to_dict()

        assert result["prompt_tokens"] == 10
        assert result["completion_tokens"] == 15
        assert result["total_tokens"] == 25
        assert result["cost"] == 0.0012