"""Routers package initialization.

This package contains all API route handlers.
"""

from . import health, search, validate, vocabularies

__all__ = ["health", "vocabularies", "search", "validate"]
