"""Configuration management using pydantic-settings.

This module defines all environment-based configuration for the REST API service.
"""

from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be overridden via environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Backend configuration
    vocab_backend: str = Field(
        default="yaml",
        description="Backend type: 'yaml' or 'postgres'",
    )

    # YAML backend configuration
    vocab_yaml_path: Optional[str] = Field(
        default=None,
        description="Path to YAML file or directory (required when backend is yaml)",
    )

    vocab_yaml_reload: bool = Field(
        default=False,
        description="Enable hot-reload of YAML vocabularies",
    )

    # Search configuration
    vocab_search_case_sensitive: bool = Field(
        default=False,
        description="Whether search should be case-sensitive",
    )

    # Server configuration
    uvicorn_host: str = Field(
        default="0.0.0.0",
        description="Host to bind Uvicorn server",
    )

    uvicorn_port: int = Field(
        default=8000,
        description="Port to bind Uvicorn server",
    )

    # PostgreSQL configuration (optional)
    postgres_dsn: Optional[str] = Field(
        default=None,
        description="PostgreSQL connection string (required when backend is postgres)",
    )

    postgres_pool_min: int = Field(
        default=1,
        description="Minimum number of connections in the pool",
    )

    postgres_pool_max: int = Field(
        default=10,
        description="Maximum number of connections in the pool",
    )

    # CORS configuration (optional)
    cors_allow_origins: Optional[List[str]] = Field(
        default=None,
        description="List of allowed origins for CORS",
    )

    cors_allow_credentials: bool = Field(
        default=False,
        description="Allow credentials in CORS requests",
    )

    # Logging and observability
    log_request_bodies: bool = Field(
        default=False,
        description="Whether to log request bodies (set to False for PHI safety)",
    )

    def validate_backend_config(self) -> None:
        """Validate that required backend configuration is provided.

        Raises:
            ValueError: If backend-specific required configuration is missing.
        """
        if self.vocab_backend == "yaml" and not self.vocab_yaml_path:
            raise ValueError(
                "VOCAB_YAML_PATH is required when VOCAB_BACKEND is 'yaml'"
            )

        if self.vocab_backend == "postgres" and not self.postgres_dsn:
            raise ValueError(
                "POSTGRES_DSN is required when VOCAB_BACKEND is 'postgres'"
            )


# Global settings instance
settings = Settings()
