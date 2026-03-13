from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import Depends, FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.database import dispose_db, init_db
from app.dependencies import limiter
from app.exceptions import register_exception_handlers
from app.routers import analytics, health, qrcode, redirect, urls
from app.security import enforce_token_auth


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize database on startup, dispose on shutdown."""
    await init_db()
    yield
    await dispose_db()


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
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
