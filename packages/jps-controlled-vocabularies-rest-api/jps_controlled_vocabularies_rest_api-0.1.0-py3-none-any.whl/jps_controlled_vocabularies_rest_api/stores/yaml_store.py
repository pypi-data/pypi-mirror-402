"""YAML-based vocabulary store implementation.

This module implements the VocabularyStore interface using YAML files as the backend.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from ..models.api_models import Term, VocabularyDetail, VocabularySummary
from .base import VocabularyStore

logger = logging.getLogger(__name__)


class YamlStore(VocabularyStore):
    """YAML-based implementation of VocabularyStore.

    Loads vocabulary data from YAML files and provides read-only access.
    Supports optional hot-reload functionality.
    """

    def __init__(self, path: str, reload_enabled: bool = False) -> None:
        """Initialize the YAML store.

        Args:
            path: Path to a YAML file or directory containing YAML files.
            reload_enabled: Whether to enable hot-reload of vocabularies.
        """
        self.path = Path(path)
        self.reload_enabled = reload_enabled
        self._registry: Dict[str, Dict[str, Any]] = {}
        self._last_load_error: Optional[str] = None

        # Initial load
        self._load_vocabularies()

    def _load_vocabularies(self) -> None:
        """Load vocabularies from YAML files.

        Raises:
            FileNotFoundError: If the path does not exist.
            yaml.YAMLError: If YAML parsing fails.
        """
        if not self.path.exists():
            raise FileNotFoundError(f"Vocabulary path not found: {self.path}")

        new_registry: Dict[str, Dict[str, Any]] = {}

        try:
            if self.path.is_file():
                # Load single file
                logger.info(f"Loading vocabulary from file: {self.path}")
                with open(self.path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data and isinstance(data, dict):
                        vocab_id = data.get("vocabulary_id", self.path.stem)
                        new_registry[vocab_id] = data
            else:
                # Load all YAML files from directory
                logger.info(f"Loading vocabularies from directory: {self.path}")
                yaml_files = list(self.path.glob("*.yaml")) + list(
                    self.path.glob("*.yml")
                )

                for yaml_file in yaml_files:
                    logger.debug(f"Loading {yaml_file}")
                    with open(yaml_file, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                        if data and isinstance(data, dict):
                            vocab_id = data.get("vocabulary_id", yaml_file.stem)
                            new_registry[vocab_id] = data

            # Successfully loaded, update registry
            self._registry = new_registry
            self._last_load_error = None
            logger.info(f"Successfully loaded {len(self._registry)} vocabularies")

        except Exception as e:
            error_msg = f"Failed to load vocabularies: {e}"
            logger.error(error_msg, exc_info=True)

            # If we have no registry yet, raise the error
            if not self._registry:
                raise

            # Otherwise, keep the last known good registry
            self._last_load_error = error_msg
            logger.warning("Keeping last known good registry")

    def _reload_if_enabled(self) -> None:
        """Reload vocabularies if reload is enabled."""
        if self.reload_enabled:
            try:
                self._load_vocabularies()
            except Exception as e:
                logger.error(f"Failed to reload vocabularies: {e}", exc_info=True)

    def list_vocabularies(self) -> List[VocabularySummary]:
        """List all available vocabularies.

        Returns:
            List[VocabularySummary]: List of vocabulary summaries.
        """
        self._reload_if_enabled()

        summaries = []
        for vocab_id, vocab_data in self._registry.items():
            terms = vocab_data.get("terms", [])
            summaries.append(
                VocabularySummary(
                    vocabulary_id=vocab_id,
                    schema_version=vocab_data.get("schema_version", "1.0"),
                    title=vocab_data.get("title", vocab_id),
                    description=vocab_data.get("description"),
                    term_count=len(terms),
                )
            )

        return summaries

    def get_vocabulary(self, vocabulary_id: str) -> VocabularyDetail:
        """Get detailed information about a specific vocabulary.

        Args:
            vocabulary_id: The unique identifier of the vocabulary.

        Returns:
            VocabularyDetail: Detailed vocabulary information including terms.

        Raises:
            KeyError: If the vocabulary is not found.
        """
        self._reload_if_enabled()

        if vocabulary_id not in self._registry:
            raise KeyError(f"Vocabulary not found: {vocabulary_id}")

        vocab_data = self._registry[vocabulary_id]
        terms_data = vocab_data.get("terms", [])

        # Convert terms to Term objects
        terms = []
        for term_data in terms_data:
            terms.append(
                Term(
                    key=term_data.get("key", term_data.get("name", "")),
                    name=term_data.get("name", ""),
                    description=term_data.get("description"),
                    vocabulary_id=vocabulary_id,
                    metadata=term_data.get("metadata", {}),
                )
            )

        return VocabularyDetail(
            vocabulary_id=vocabulary_id,
            schema_version=vocab_data.get("schema_version", "1.0"),
            title=vocab_data.get("title", vocabulary_id),
            description=vocab_data.get("description"),
            metadata=vocab_data.get("metadata", {}),
            term_count=len(terms),
            terms=terms,
        )

    def list_terms(
        self, vocabulary_id: str, *, limit: int = 100, offset: int = 0
    ) -> List[Term]:
        """List terms in a vocabulary with pagination.

        Args:
            vocabulary_id: The unique identifier of the vocabulary.
            limit: Maximum number of terms to return (default: 100).
            offset: Number of terms to skip (default: 0).

        Returns:
            List[Term]: List of terms.

        Raises:
            KeyError: If the vocabulary is not found.
        """
        self._reload_if_enabled()

        if vocabulary_id not in self._registry:
            raise KeyError(f"Vocabulary not found: {vocabulary_id}")

        vocab_data = self._registry[vocabulary_id]
        terms_data = vocab_data.get("terms", [])

        # Apply pagination
        paginated_terms = terms_data[offset : offset + limit]

        terms = []
        for term_data in paginated_terms:
            terms.append(
                Term(
                    key=term_data.get("key", term_data.get("name", "")),
                    name=term_data.get("name", ""),
                    description=term_data.get("description"),
                    vocabulary_id=vocabulary_id,
                    metadata=term_data.get("metadata", {}),
                )
            )

        return terms

    def get_term(self, vocabulary_id: str, term_key: str) -> Term:
        """Get a specific term by its key.

        Args:
            vocabulary_id: The unique identifier of the vocabulary.
            term_key: The unique key of the term within the vocabulary.

        Returns:
            Term: The requested term.

        Raises:
            KeyError: If the vocabulary or term is not found.
        """
        self._reload_if_enabled()

        if vocabulary_id not in self._registry:
            raise KeyError(f"Vocabulary not found: {vocabulary_id}")

        vocab_data = self._registry[vocabulary_id]
        terms_data = vocab_data.get("terms", [])

        for term_data in terms_data:
            if term_data.get("key") == term_key or term_data.get("name") == term_key:
                return Term(
                    key=term_data.get("key", term_data.get("name", "")),
                    name=term_data.get("name", ""),
                    description=term_data.get("description"),
                    vocabulary_id=vocabulary_id,
                    metadata=term_data.get("metadata", {}),
                )

        raise KeyError(f"Term not found: {term_key} in vocabulary {vocabulary_id}")

    def search_terms(
        self,
        query: str,
        vocabulary_id: Optional[str] = None,
        *,
        limit: int = 100,
        offset: int = 0,
        case_sensitive: bool = False,
    ) -> List[Term]:
        """Search for terms matching a query string.

        Args:
            query: The search query string.
            vocabulary_id: Optional vocabulary to search within (searches all if None).
            limit: Maximum number of results to return (default: 100).
            offset: Number of results to skip (default: 0).
            case_sensitive: Whether the search should be case-sensitive (default: False).

        Returns:
            List[Term]: List of matching terms.
        """
        self._reload_if_enabled()

        # Prepare query for comparison
        search_query = query if case_sensitive else query.lower()

        matching_terms = []

        # Determine which vocabularies to search
        vocab_ids = (
            [vocabulary_id] if vocabulary_id else list(self._registry.keys())
        )

        for vid in vocab_ids:
            if vid not in self._registry:
                continue

            vocab_data = self._registry[vid]
            terms_data = vocab_data.get("terms", [])

            for term_data in terms_data:
                # Search in key, name, and description
                key = term_data.get("key", "")
                name = term_data.get("name", "")
                description = term_data.get("description", "")

                # Prepare term fields for comparison
                if not case_sensitive:
                    key = key.lower()
                    name = name.lower()
                    description = description.lower()

                # Check if query matches any field
                if (
                    search_query in key
                    or search_query in name
                    or search_query in description
                ):
                    matching_terms.append(
                        Term(
                            key=term_data.get("key", term_data.get("name", "")),
                            name=term_data.get("name", ""),
                            description=term_data.get("description"),
                            vocabulary_id=vid,
                            metadata=term_data.get("metadata", {}),
                        )
                    )

        # Apply pagination
        paginated_terms = matching_terms[offset : offset + limit]

        return paginated_terms

    def get_registry(self) -> dict:
        """Get the complete registry for validation.

        Returns:
            dict: The complete vocabulary registry.
        """
        self._reload_if_enabled()
        return self._registry

    def get_last_load_error(self) -> Optional[str]:
        """Get the last load error if any.

        Returns:
            Optional[str]: The last load error message, or None if no error.
        """
        return self._last_load_error
