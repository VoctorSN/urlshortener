from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/urlshortener"
    BASE_URL: str = "http://localhost:8000"
    SHORT_CODE_LENGTH: int = 7
    DEFAULT_RATE_LIMIT: str = "60/minute"
    URL_MAX_AGE_DAYS: int | None = None
    CORS_ORIGINS: list[str] = ["*"]

    # Security settings
    AUTH_ENABLED: bool = True
    API_TOKENS: list[str] = []
    JWT_SECRET: str | None = None
    JWT_ALGORITHM: str = "HS256"
    JWT_AUDIENCE: str | None = None
    AUTH_PROTECTED_ROUTE_PATTERNS: list[str] = ["/api/urls/*"]
    AUTH_EXEMPT_ROUTE_PATTERNS: list[str] = [
        "GET /health",
        "GET /favicon.ico",
        "GET /docs",
        "GET /redoc",
        "GET /openapi.json",
        "GET /{short_code}",
    ]


settings = Settings()
