"""Tests for the chat completions endpoint."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "gateway"


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "AI Compliance Gateway"
    assert "version" in data


def test_chat_completions_streaming_not_supported(client):
    """Test that streaming is not supported in Phase 1."""
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": True,
        },
    )
    assert response.status_code == 400
    assert "Streaming is not supported" in response.json()["detail"]


@patch("app.routers.chat.get_provider")
@patch("app.routers.chat.send_audit_log")
def test_chat_completions_success(mock_audit, mock_provider, client):
    """Test successful chat completion request."""
    # Mock provider response
    mock_instance = AsyncMock()
    mock_instance.chat_completion.return_value = (
        {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "Hello!"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        },
        200,
    )
    mock_instance.get_provider_name.return_value = "openai"
    mock_instance.close = AsyncMock()
    mock_provider.return_value = mock_instance
    mock_audit.return_value = None

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "Hello"}],
        },
        headers={"X-App-Key": "test-app", "X-Org-Id": "test-org"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "chatcmpl-123"
    assert len(data["choices"]) == 1

