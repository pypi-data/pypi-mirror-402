"""Base vocabulary store protocol.

This module defines the abstract interface that all vocabulary store backends must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..models.api_models import Term, VocabularyDetail, VocabularySummary


class VocabularyStore(ABC):
    """Abstract base class for vocabulary storage backends.

    This defines the interface that all store implementations (YAML, PostgreSQL, etc.)
    must implement to provide vocabulary data to the REST API.
    """

    @abstractmethod
    def list_vocabularies(self) -> List[VocabularySummary]:
        """List all available vocabularies.

        Returns:
            List[VocabularySummary]: List of vocabulary summaries.
        """
        pass

    @abstractmethod
    def get_vocabulary(self, vocabulary_id: str) -> VocabularyDetail:
        """Get detailed information about a specific vocabulary.

        Args:
            vocabulary_id: The unique identifier of the vocabulary.

        Returns:
            VocabularyDetail: Detailed vocabulary information including terms.

        Raises:
            KeyError: If the vocabulary is not found.
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def get_registry(self) -> dict:
        """Get the complete registry for validation.

        Returns:
            dict: The complete vocabulary registry.
        """
        pass
