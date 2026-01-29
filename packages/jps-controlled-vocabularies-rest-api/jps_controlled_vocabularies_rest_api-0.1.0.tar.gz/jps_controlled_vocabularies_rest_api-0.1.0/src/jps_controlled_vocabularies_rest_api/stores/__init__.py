"""Stores package initialization.

This package contains vocabulary store implementations.
"""

from .base import VocabularyStore
from .yaml_store import YamlStore

__all__ = ["VocabularyStore", "YamlStore"]
