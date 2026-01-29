"""FastAPI application factory and entry point.

This module creates and configures the FastAPI application instance,
including all routers and middleware.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .deps import get_store
from .routers import health, search, validate, vocabularies

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Lifespan context manager for application startup and shutdown.

    Args:
        app: The FastAPI application instance.

    Yields:
        None: Control during the application's lifetime.
    """
    # Startup: validate configuration and initialize store
    logger.info("Starting jps-controlled-vocabularies-rest-api...")

    try:
        settings.validate_backend_config()
        store = get_store()
        logger.info(f"Backend configured: {settings.vocab_backend}")
        logger.info(f"Store initialized: {type(store).__name__}")

        # Pre-load vocabularies to fail fast if there are issues
        vocabularies_list = store.list_vocabularies()
        logger.info(f"Loaded {len(vocabularies_list)} vocabularies")

    except Exception as e:
        logger.error(f"Failed to initialize application: {e}", exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("Shutting down jps-controlled-vocabularies-rest-api...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance.
    """
    app = FastAPI(
        title="JPS Controlled Vocabularies REST API",
        description=(
            "A lightweight REST service that exposes controlled vocabularies "
            "and terms over HTTP for programmatic retrieval and validation."
        ),
        version="0.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Configure CORS if enabled
    if settings.cors_allow_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_allow_origins,
            allow_credentials=settings.cors_allow_credentials,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info(f"CORS enabled for origins: {settings.cors_allow_origins}")

    # Include routers
    app.include_router(health.router, tags=["health"])
    app.include_router(vocabularies.router, prefix="/v1", tags=["vocabularies"])
    app.include_router(search.router, prefix="/v1", tags=["search"])
    app.include_router(validate.router, prefix="/v1", tags=["validate"])

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle uncaught exceptions.

        Args:
            request: The HTTP request.
            exc: The exception that was raised.

        Returns:
            JSONResponse: Error response in standardized format.
        """
        logger.error(f"Unhandled exception: {exc}", exc_info=True)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {"error": str(exc)} if settings.log_request_bodies else {},
            },
        )

    return app


# Application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "jps_controlled_vocabularies_rest_api.main:app",
        host=settings.uvicorn_host,
        port=settings.uvicorn_port,
        reload=True,
    )
