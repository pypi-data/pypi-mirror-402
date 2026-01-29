"""Term search endpoint.

This module provides search functionality for finding terms across vocabularies.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..config import settings
from ..deps import get_store
from ..models.api_models import Term
from ..stores.base import VocabularyStore

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/search",
    response_model=List[Term],
    summary="Search for terms",
    description=(
        "Search for terms matching a query string. "
        "Searches across name, key, and description fields."
    ),
)
def search_terms(
    q: str = Query(..., description="Search query string", min_length=1),
    vocabulary_id: Optional[str] = Query(
        None, description="Optional vocabulary ID to search within"
    ),
    limit: int = Query(
        default=100, ge=1, le=1000, description="Maximum number of results to return"
    ),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
    store: VocabularyStore = Depends(get_store),
) -> List[Term]:
    """Search for terms matching a query string.

    Args:
        q: The search query string (required).
        vocabulary_id: Optional vocabulary to search within (searches all if None).
        limit: Maximum number of results to return (1-1000, default: 100).
        offset: Number of results to skip (default: 0).
        store: The vocabulary store dependency.

    Returns:
        List[Term]: List of matching terms.
    """
    try:
        case_sensitive = settings.vocab_search_case_sensitive
        return store.search_terms(
            query=q,
            vocabulary_id=vocabulary_id,
            limit=limit,
            offset=offset,
            case_sensitive=case_sensitive,
        )
    except Exception as e:
        logger.error(f"Search failed for query '{q}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "SEARCH_ERROR",
                "message": "Search operation failed",
                "details": {"error": str(e)},
            },
        )
