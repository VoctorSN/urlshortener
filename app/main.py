from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
import logging
from typing import cast

from fastapi import Depends, FastAPI, Request
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.database import dispose_db, init_db
from app.dependencies import limiter
from app.exceptions import register_exception_handlers
from app.routers import analytics, health, qrcode, redirect, urls
from app.security import enforce_token_auth

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize database on startup, dispose on shutdown."""
    logger.info("app_lifecycle event=startup_begin")
    try:
        await init_db()
        logger.info("app_lifecycle event=startup_complete")
        yield
    finally:
        logger.info("app_lifecycle event=shutdown_begin")
        try:
            await dispose_db()
            logger.info("app_lifecycle event=shutdown_complete")
        except Exception as exc:
            logger.exception(
                "app_lifecycle event=shutdown_failed error_type=%s",
                exc.__class__.__name__,
            )
            raise


def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    client = request.client.host if request.client else "unknown"
    logger.warning(
        "rate_limit_exceeded event=http_429 method=%s path=%s client=%s detail=%s",
        request.method,
        request.url.path,
        client,
        str(exc),
    )
    return _rate_limit_exceeded_handler(request, exc)


def _rate_limit_exception_handler(request: Request, exc: Exception):
    return _rate_limit_handler(request, cast(RateLimitExceeded, exc))


def create_app() -> FastAPI:
    """Application factory for the URL Shortener API."""
    app = FastAPI(
        title="URL Shortener API",
        description=(
            "A full-featured URL shortening service with analytics, "
            "custom aliases, expiration, QR code generation, and rate limiting."
        ),
        version="1.0.0",
        lifespan=lifespan,
        dependencies=[Depends(enforce_token_auth)],
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exception_handler)

    # Custom exception handlers
    register_exception_handlers(app)

    # Routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(urls.router, prefix="/api/urls", tags=["URLs"])
    app.include_router(analytics.router, prefix="/api/urls", tags=["Analytics"])
    app.include_router(qrcode.router, prefix="/api/urls", tags=["QR Codes"])
    # Redirect router must be last to avoid shadowing /api/* and /health paths
    app.include_router(redirect.router, tags=["Redirect"])

    return app


app = create_app()
