"""Tests for health endpoints.

This module tests the health and readiness check endpoints.
"""

from fastapi.testclient import TestClient

from jps_controlled_vocabularies_rest_api.main import app

client = TestClient(app)


def test_health_check() -> None:
    """Test the /healthz endpoint."""
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_readiness_check() -> None:
    """Test the /readyz endpoint."""
    response = client.get("/readyz")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "backend" in data
    assert "registry_loaded" in data
    assert "vocabulary_count" in data
    assert "warnings" in data
