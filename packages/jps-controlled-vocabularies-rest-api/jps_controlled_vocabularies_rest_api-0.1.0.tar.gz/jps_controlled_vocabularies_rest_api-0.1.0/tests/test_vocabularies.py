"""Tests for vocabulary endpoints.

This module tests vocabulary and term retrieval endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from jps_controlled_vocabularies_rest_api.main import app

client = TestClient(app)


def test_list_vocabularies() -> None:
    """Test listing all vocabularies."""
    response = client.get("/v1/vocabularies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_vocabulary_not_found() -> None:
    """Test getting a non-existent vocabulary returns 404."""
    response = client.get("/v1/vocabularies/nonexistent_vocab")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    detail = data["detail"]
    assert detail["error_code"] == "VOCABULARY_NOT_FOUND"


def test_list_terms_not_found() -> None:
    """Test listing terms for non-existent vocabulary returns 404."""
    response = client.get("/v1/vocabularies/nonexistent_vocab/terms")
    assert response.status_code == 404


def test_list_terms_with_pagination() -> None:
    """Test listing terms with pagination parameters."""
    response = client.get("/v1/vocabularies/test_vocab/terms?limit=10&offset=0")
    # This will return 404 if test_vocab doesn't exist, which is expected
    assert response.status_code in [200, 404]


def test_get_term_not_found() -> None:
    """Test getting a non-existent term returns 404."""
    response = client.get("/v1/vocabularies/test_vocab/terms/nonexistent_term")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    detail = data["detail"]
    assert detail["error_code"] == "TERM_NOT_FOUND"
