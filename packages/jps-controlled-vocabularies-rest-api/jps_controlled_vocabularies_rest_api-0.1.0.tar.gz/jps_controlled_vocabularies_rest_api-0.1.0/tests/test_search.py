"""Tests for search endpoint.

This module tests the term search functionality.
"""

import pytest
from fastapi.testclient import TestClient

from jps_controlled_vocabularies_rest_api.main import app

client = TestClient(app)


def test_search_terms_requires_query() -> None:
    """Test that search endpoint requires a query parameter."""
    response = client.get("/v1/search")
    assert response.status_code == 422  # Unprocessable Entity


def test_search_terms_with_query() -> None:
    """Test searching for terms with a query string."""
    response = client.get("/v1/search?q=test")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_search_terms_with_vocabulary_filter() -> None:
    """Test searching within a specific vocabulary."""
    response = client.get("/v1/search?q=test&vocabulary_id=test_vocab")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_search_terms_with_pagination() -> None:
    """Test searching with pagination parameters."""
    response = client.get("/v1/search?q=test&limit=5&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 5
