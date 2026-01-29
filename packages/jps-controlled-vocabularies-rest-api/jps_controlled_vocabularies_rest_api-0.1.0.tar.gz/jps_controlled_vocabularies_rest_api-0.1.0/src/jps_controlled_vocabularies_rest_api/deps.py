"""Dependency injection for FastAPI.

This module provides dependency injection functions for the FastAPI application,
particularly for obtaining the appropriate VocabularyStore backend.
"""

from functools import lru_cache
from typing import Any

from .config import settings
from .stores.base import VocabularyStore
from .stores.yaml_store import YamlStore


@lru_cache()
def get_store() -> VocabularyStore:
    """Get the configured vocabulary store backend.

    This function is cached to ensure only one store instance is created.

    Returns:
        VocabularyStore: The configured vocabulary store instance.

    Raises:
        ValueError: If the backend is misconfigured or unsupported.
    """
    settings.validate_backend_config()

    backend = settings.vocab_backend.lower()

    if backend == "yaml":
        if not settings.vocab_yaml_path:
            raise ValueError("VOCAB_YAML_PATH is required for YAML backend")
        return YamlStore(
            path=settings.vocab_yaml_path,
            reload_enabled=settings.vocab_yaml_reload,
        )

    elif backend == "postgres":
        # PostgreSQL backend is implemented as a plugin
        # Try to import it dynamically
        try:
            from jps_controlled_vocabularies_postgresql import PostgresStore

            if not settings.postgres_dsn:
                raise ValueError("POSTGRES_DSN is required for PostgreSQL backend")

            return PostgresStore(
                dsn=settings.postgres_dsn,
                pool_min=settings.postgres_pool_min,
                pool_max=settings.postgres_pool_max,
            )
        except ImportError as e:
            raise ValueError(
                "PostgreSQL backend requires 'jps-controlled-vocabularies-postgresql' "
                f"package to be installed: {e}"
            ) from e

    else:
        raise ValueError(
            f"Unsupported backend: {backend}. Supported: yaml, postgres"
        )


def clear_store_cache() -> None:
    """Clear the store cache.

    Useful for testing or when configuration changes require a fresh store instance.
    """
    get_store.cache_clear()
