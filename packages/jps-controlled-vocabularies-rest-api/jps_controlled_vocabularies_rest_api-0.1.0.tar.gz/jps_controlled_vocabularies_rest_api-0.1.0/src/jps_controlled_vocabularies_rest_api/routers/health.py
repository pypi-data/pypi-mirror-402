"""Health and readiness check endpoints.

This module provides health and readiness check endpoints for operational monitoring.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends

from ..config import settings
from ..deps import get_store
from ..models.api_models import HealthResponse, ReadinessResponse
from ..stores.base import VocabularyStore
from ..stores.yaml_store import YamlStore

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/healthz", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns:
        HealthResponse: Simple health status indicating the service is running.
    """
    return HealthResponse(status="ok")


@router.get("/readyz", response_model=ReadinessResponse)
def readiness_check(store: VocabularyStore = Depends(get_store)) -> ReadinessResponse:
    """Readiness check endpoint.

    Checks if the service is ready to handle requests, including backend availability
    and vocabulary registry status.

    Args:
        store: The vocabulary store dependency.

    Returns:
        ReadinessResponse: Detailed readiness information.
    """
    warnings: List[str] = []

    try:
        vocabularies = store.list_vocabularies()
        vocabulary_count = len(vocabularies)
        registry_loaded = vocabulary_count > 0

        # Check for YAML store reload errors
        if isinstance(store, YamlStore):
            last_error = store.get_last_load_error()
            if last_error:
                warnings.append(f"Last reload error: {last_error}")

        return ReadinessResponse(
            status="ready" if registry_loaded else "not_ready",
            backend=settings.vocab_backend,
            registry_loaded=registry_loaded,
            vocabulary_count=vocabulary_count,
            warnings=warnings,
        )

    except Exception as e:
        logger.error(f"Readiness check failed: {e}", exc_info=True)
        return ReadinessResponse(
            status="not_ready",
            backend=settings.vocab_backend,
            registry_loaded=False,
            vocabulary_count=0,
            warnings=[f"Failed to check registry: {str(e)}"],
        )
