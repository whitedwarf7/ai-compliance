"""Tests for the audit logs endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from uuid import uuid4

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
    assert data["service"] == "audit"


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "AI Compliance Audit Service"
    assert "version" in data


@patch("app.routers.logs.get_db")
def test_create_audit_log(mock_get_db, client):
    """Test creating an audit log entry."""
    # Mock database session
    mock_db = MagicMock()
    mock_get_db.return_value = iter([mock_db])

    log_id = str(uuid4())
    log_data = {
        "id": log_id,
        "org_id": "test-org",
        "app_id": "test-app",
        "user_id": "user-123",
        "model": "gpt-4o",
        "provider": "openai",
        "prompt_hash": "abc123def456",
        "token_count_input": 100,
        "token_count_output": 50,
        "latency_ms": 1500,
        "risk_flags": [],
        "metadata": {},
    }

    # This test would require a database connection
    # In integration tests, we would use a test database


def test_list_audit_logs_validation(client):
    """Test query parameter validation for listing logs."""
    # Test invalid page number
    response = client.get("/api/v1/logs", params={"page": 0})
    assert response.status_code == 422

    # Test invalid limit
    response = client.get("/api/v1/logs", params={"limit": 101})
    assert response.status_code == 422


def test_get_audit_log_invalid_id(client):
    """Test getting an audit log with invalid ID format."""
    response = client.get("/api/v1/logs/invalid-uuid")
    assert response.status_code == 400
    assert "Invalid log ID format" in response.json()["detail"]

