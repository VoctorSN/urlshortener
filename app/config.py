from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str = "sqlite+aiosqlite:///./data/urlshortener.db"
    BASE_URL: str = "http://localhost:8000"
    SHORT_CODE_LENGTH: int = 7
    DEFAULT_RATE_LIMIT: str = "60/minute"
    URL_MAX_AGE_DAYS: int | None = None
    CORS_ORIGINS: list[str] = ["*"]


settings = Settings()
