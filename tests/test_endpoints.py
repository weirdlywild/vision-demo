import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns basic info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "DIY Repair Diagnosis API"
    assert "endpoints" in data


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "cache_stats" in data
    assert "active_sessions" in data


def test_diagnose_missing_image():
    """Test diagnose endpoint without image."""
    response = client.post("/diagnose")
    assert response.status_code == 422  # Validation error


# Note: Full integration tests require:
# - Mock OpenAI API responses
# - Sample test images
# - Session management tests
# Add these tests with proper fixtures and mocks
