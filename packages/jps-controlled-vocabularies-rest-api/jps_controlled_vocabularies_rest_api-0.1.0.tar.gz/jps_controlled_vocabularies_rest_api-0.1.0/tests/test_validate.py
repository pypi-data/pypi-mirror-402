"""Tests for validation endpoints.

This module tests value and registry validation endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from jps_controlled_vocabularies_rest_api.main import app

client = TestClient(app)


def test_validate_value_missing_fields() -> None:
    """Test that validate value requires all fields."""
    response = client.post("/v1/validate/value", json={})
    assert response.status_code == 422  # Unprocessable Entity


def test_validate_value_term_not_found() -> None:
    """Test validating against a non-existent term."""
    response = client.post(
        "/v1/validate/value",
        json={
            "vocabulary_id": "nonexistent_vocab",
            "term_key": "nonexistent_term",
            "value": "test_value",
        },
    )
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    detail = data["detail"]
    assert detail["error_code"] == "TERM_NOT_FOUND"


def test_validate_registry() -> None:
    """Test registry validation endpoint."""
    response = client.post("/v1/validate/registry")
    assert response.status_code == 200
    data = response.json()
    assert "is_valid" in data
    assert "total_vocabularies" in data
    assert "total_terms" in data
    assert "issues" in data
    assert "summary" in data
    assert isinstance(data["issues"], list)
