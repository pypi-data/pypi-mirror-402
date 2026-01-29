"""Vocabulary and term retrieval endpoints.

This module provides endpoints for listing and retrieving vocabularies and terms.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..deps import get_store
from ..models.api_models import ErrorResponse, Term, VocabularyDetail, VocabularySummary
from ..stores.base import VocabularyStore

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/vocabularies",
    response_model=List[VocabularySummary],
    summary="List all vocabularies",
    description="Returns a list of all available vocabularies with summary information.",
)
def list_vocabularies(
    store: VocabularyStore = Depends(get_store),
) -> List[VocabularySummary]:
    """List all available vocabularies.

    Args:
        store: The vocabulary store dependency.

    Returns:
        List[VocabularySummary]: List of vocabulary summaries.
    """
    try:
        return store.list_vocabularies()
    except Exception as e:
        logger.error(f"Failed to list vocabularies: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to retrieve vocabularies",
                "details": {"error": str(e)},
            },
        )


@router.get(
    "/vocabularies/{vocabulary_id}",
    response_model=VocabularyDetail,
    summary="Get vocabulary details",
    description="Returns detailed information about a specific vocabulary, including all terms.",
)
def get_vocabulary(
    vocabulary_id: str,
    store: VocabularyStore = Depends(get_store),
) -> VocabularyDetail:
    """Get detailed information about a specific vocabulary.

    Args:
        vocabulary_id: The unique identifier of the vocabulary.
        store: The vocabulary store dependency.

    Returns:
        VocabularyDetail: Detailed vocabulary information.

    Raises:
        HTTPException: 404 if vocabulary not found.
    """
    try:
        return store.get_vocabulary(vocabulary_id)
    except KeyError as e:
        logger.warning(f"Vocabulary not found: {vocabulary_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "VOCABULARY_NOT_FOUND",
                "message": f"Vocabulary not found: {vocabulary_id}",
                "details": {},
            },
        )
    except Exception as e:
        logger.error(
            f"Failed to get vocabulary {vocabulary_id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to retrieve vocabulary",
                "details": {"error": str(e)},
            },
        )


@router.get(
    "/vocabularies/{vocabulary_id}/terms",
    response_model=List[Term],
    summary="List terms in a vocabulary",
    description="Returns a paginated list of terms from a specific vocabulary.",
)
def list_terms(
    vocabulary_id: str,
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of terms to return"),
    offset: int = Query(default=0, ge=0, description="Number of terms to skip"),
    store: VocabularyStore = Depends(get_store),
) -> List[Term]:
    """List terms in a vocabulary with pagination.

    Args:
        vocabulary_id: The unique identifier of the vocabulary.
        limit: Maximum number of terms to return (1-1000, default: 100).
        offset: Number of terms to skip (default: 0).
        store: The vocabulary store dependency.

    Returns:
        List[Term]: List of terms.

    Raises:
        HTTPException: 404 if vocabulary not found.
    """
    try:
        return store.list_terms(vocabulary_id, limit=limit, offset=offset)
    except KeyError as e:
        logger.warning(f"Vocabulary not found: {vocabulary_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "VOCABULARY_NOT_FOUND",
                "message": f"Vocabulary not found: {vocabulary_id}",
                "details": {},
            },
        )
    except Exception as e:
        logger.error(
            f"Failed to list terms for {vocabulary_id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to retrieve terms",
                "details": {"error": str(e)},
            },
        )


@router.get(
    "/vocabularies/{vocabulary_id}/terms/{term_key}",
    response_model=Term,
    summary="Get a specific term",
    description="Returns a single term by its key within a vocabulary.",
)
def get_term(
    vocabulary_id: str,
    term_key: str,
    store: VocabularyStore = Depends(get_store),
) -> Term:
    """Get a specific term by its key.

    Args:
        vocabulary_id: The unique identifier of the vocabulary.
        term_key: The unique key of the term.
        store: The vocabulary store dependency.

    Returns:
        Term: The requested term.

    Raises:
        HTTPException: 404 if vocabulary or term not found.
    """
    try:
        return store.get_term(vocabulary_id, term_key)
    except KeyError as e:
        error_msg = str(e)
        logger.warning(f"Term not found: {term_key} in {vocabulary_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "TERM_NOT_FOUND",
                "message": error_msg,
                "details": {"vocabulary_id": vocabulary_id, "term_key": term_key},
            },
        )
    except Exception as e:
        logger.error(
            f"Failed to get term {term_key} in {vocabulary_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to retrieve term",
                "details": {"error": str(e)},
            },
        )
