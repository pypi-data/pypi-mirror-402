"""Tests for YAML store implementation.

This module tests the YamlStore class.
"""

import tempfile
from pathlib import Path

import pytest
import yaml

from jps_controlled_vocabularies_rest_api.stores.yaml_store import YamlStore


@pytest.fixture
def sample_vocabulary() -> dict:
    """Create a sample vocabulary for testing."""
    return {
        "vocabulary_id": "test_vocab",
        "schema_version": "1.0",
        "title": "Test Vocabulary",
        "description": "A test vocabulary",
        "terms": [
            {
                "key": "term1",
                "name": "Term 1",
                "description": "First test term",
                "metadata": {"allowed_values": ["value1", "value2", "value3"]},
            },
            {
                "key": "term2",
                "name": "Term 2",
                "description": "Second test term",
            },
        ],
    }


@pytest.fixture
def yaml_file(sample_vocabulary: dict) -> Path:
    """Create a temporary YAML file with sample vocabulary."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        yaml.dump(sample_vocabulary, f)
        path = Path(f.name)
    yield path
    path.unlink()


@pytest.fixture
def yaml_directory(sample_vocabulary: dict) -> Path:
    """Create a temporary directory with YAML files."""
    temp_dir = Path(tempfile.mkdtemp())

    # Create first vocabulary
    vocab1_path = temp_dir / "vocab1.yaml"
    with open(vocab1_path, "w") as f:
        yaml.dump(sample_vocabulary, f)

    # Create second vocabulary
    vocab2 = sample_vocabulary.copy()
    vocab2["vocabulary_id"] = "test_vocab_2"
    vocab2["title"] = "Test Vocabulary 2"
    vocab2_path = temp_dir / "vocab2.yaml"
    with open(vocab2_path, "w") as f:
        yaml.dump(vocab2, f)

    yield temp_dir

    # Cleanup
    for file in temp_dir.glob("*.yaml"):
        file.unlink()
    temp_dir.rmdir()


def test_yaml_store_loads_single_file(yaml_file: Path) -> None:
    """Test that YamlStore can load a single YAML file."""
    store = YamlStore(path=str(yaml_file), reload_enabled=False)
    vocabularies = store.list_vocabularies()
    assert len(vocabularies) == 1
    assert vocabularies[0].vocabulary_id == "test_vocab"
    assert vocabularies[0].term_count == 2


def test_yaml_store_loads_directory(yaml_directory: Path) -> None:
    """Test that YamlStore can load multiple YAML files from a directory."""
    store = YamlStore(path=str(yaml_directory), reload_enabled=False)
    vocabularies = store.list_vocabularies()
    assert len(vocabularies) == 2
    vocab_ids = {v.vocabulary_id for v in vocabularies}
    assert "test_vocab" in vocab_ids
    assert "test_vocab_2" in vocab_ids


def test_yaml_store_get_vocabulary(yaml_file: Path) -> None:
    """Test getting a specific vocabulary."""
    store = YamlStore(path=str(yaml_file), reload_enabled=False)
    vocab = store.get_vocabulary("test_vocab")
    assert vocab.vocabulary_id == "test_vocab"
    assert vocab.title == "Test Vocabulary"
    assert len(vocab.terms or []) == 2


def test_yaml_store_get_vocabulary_not_found(yaml_file: Path) -> None:
    """Test that getting a non-existent vocabulary raises KeyError."""
    store = YamlStore(path=str(yaml_file), reload_enabled=False)
    with pytest.raises(KeyError):
        store.get_vocabulary("nonexistent")


def test_yaml_store_list_terms(yaml_file: Path) -> None:
    """Test listing terms in a vocabulary."""
    store = YamlStore(path=str(yaml_file), reload_enabled=False)
    terms = store.list_terms("test_vocab")
    assert len(terms) == 2
    assert terms[0].key == "term1"
    assert terms[1].key == "term2"


def test_yaml_store_list_terms_with_pagination(yaml_file: Path) -> None:
    """Test listing terms with pagination."""
    store = YamlStore(path=str(yaml_file), reload_enabled=False)
    terms = store.list_terms("test_vocab", limit=1, offset=0)
    assert len(terms) == 1
    assert terms[0].key == "term1"

    terms = store.list_terms("test_vocab", limit=1, offset=1)
    assert len(terms) == 1
    assert terms[0].key == "term2"


def test_yaml_store_get_term(yaml_file: Path) -> None:
    """Test getting a specific term."""
    store = YamlStore(path=str(yaml_file), reload_enabled=False)
    term = store.get_term("test_vocab", "term1")
    assert term.key == "term1"
    assert term.name == "Term 1"
    assert term.description == "First test term"


def test_yaml_store_get_term_not_found(yaml_file: Path) -> None:
    """Test that getting a non-existent term raises KeyError."""
    store = YamlStore(path=str(yaml_file), reload_enabled=False)
    with pytest.raises(KeyError):
        store.get_term("test_vocab", "nonexistent_term")


def test_yaml_store_search_terms(yaml_file: Path) -> None:
    """Test searching for terms."""
    store = YamlStore(path=str(yaml_file), reload_enabled=False)

    # Search by name
    results = store.search_terms("Term 1")
    assert len(results) == 1
    assert results[0].key == "term1"

    # Search by description
    results = store.search_terms("Second")
    assert len(results) == 1
    assert results[0].key == "term2"

    # Search case-insensitive
    results = store.search_terms("TERM", case_sensitive=False)
    assert len(results) == 2


def test_yaml_store_search_with_vocabulary_filter(yaml_directory: Path) -> None:
    """Test searching within a specific vocabulary."""
    store = YamlStore(path=str(yaml_directory), reload_enabled=False)

    # Search in specific vocabulary
    results = store.search_terms("Term", vocabulary_id="test_vocab")
    assert len(results) == 2
    assert all(t.vocabulary_id == "test_vocab" for t in results)


def test_yaml_store_get_registry(yaml_file: Path) -> None:
    """Test getting the complete registry."""
    store = YamlStore(path=str(yaml_file), reload_enabled=False)
    registry = store.get_registry()
    assert isinstance(registry, dict)
    assert "test_vocab" in registry
    assert registry["test_vocab"]["title"] == "Test Vocabulary"
