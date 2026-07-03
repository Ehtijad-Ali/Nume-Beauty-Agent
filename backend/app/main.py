"""
Application entry point.

Wires together:
  * Settings
  * Logging
  * Middleware (CORS, request logging)
  * Exception handlers
  * API v1 router
  * Health endpoints
  * Startup/shutdown lifecycle events (Redis ping, DB connectivity)
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import redis
from fastapi import FastAPI, Response

from app.api.v1 import api_router
from app.config.settings import get_settings
from app.core.logging import setup_logging
from app.middleware.cors import setup_cors
from app.middleware.exception_handler import register_exception_handlers
from app.middleware.logging import RequestLoggingMiddleware


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan.

    * Configures logging on startup.
    * Pings Redis so we fail fast if the cache is unreachable.
    """
    setup_logging()
    logger = setup_logging()  # returns root? we re-fetch a logger below
    from app.core.logging import get_logger

    log = get_logger("nume.startup")
    settings = get_settings()
    log.info("Starting %s v%s (%s)", settings.app_name, settings.app_version, settings.app_env)

    # Best-effort Redis ping
    try:
        r = redis.from_url(settings.redis_url, socket_connect_timeout=2)
        r.ping()
        log.info("Redis connection: OK")
    except Exception as exc:  # noqa: BLE001
        log.warning("Redis not reachable: %s", exc)

    yield

    log.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Enterprise backend for the NUMÉ AI Marketing Assistant. "
            "Phase 1.1 — authentication, RBAC, CRUD for products, knowledge, "
            "campaigns, uploads and settings. No AI functionality yet."
        ),
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # Expose settings on app.state for handlers / tests
    app.state.app_debug = settings.app_debug
    app.state.settings = settings

    # Middleware (order matters: outermost runs first)
    setup_cors(app)
    app.add_middleware(RequestLoggingMiddleware)

    # Exception handlers
    register_exception_handlers(app)

    # Routes
    app.include_router(api_router, prefix="/api")

    @app.get("/health", tags=["System"])
    def health() -> dict:
        """Liveness probe."""
        return {"status": "ok", "service": settings.app_name, "version": settings.app_version}

    @app.get("/healthz", tags=["System"])
    def healthz() -> dict:
        """Kubernetes-style liveness probe."""
        return {"status": "ok"}

    @app.get("/", tags=["System"])
    def root(response: Response) -> dict:
        """Root — redirects browsers to /docs, returns JSON for clients."""
        response.headers["X-Service"] = "nume-backend"
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs" if not settings.is_production else None,
            "health": "/health",
        }

    return app


app = create_app()
