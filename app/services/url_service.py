from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.exceptions import (
    InvalidURLException,
    ShortCodeExistsException,
    URLExpiredException,
    URLNotFoundException,
)
from app.models.url import URL
from app.services.shortcode import generate_short_code, is_valid_custom_alias


async def create_short_url(
    db: AsyncSession,
    original_url: str,
    custom_alias: str | None = None,
    expires_at: datetime | None = None,
) -> URL:
    """Create a new shortened URL entry."""
    if custom_alias:
        if not is_valid_custom_alias(custom_alias):
            raise InvalidURLException(
                f"Invalid custom alias: '{custom_alias}'. "
                "Must be 3-30 alphanumeric characters (hyphens and underscores allowed), "
                "and must not be a reserved path."
            )
        existing = await db.execute(
            select(URL).where(URL.short_code == custom_alias)
        )
        if existing.scalar_one_or_none() is not None:
            raise ShortCodeExistsException(
                f"Short code '{custom_alias}' is already in use."
            )
        short_code = custom_alias
    else:
        short_code = await _generate_unique_code(db)

    url = URL(
        short_code=short_code,
        original_url=original_url,
        expires_at=expires_at,
    )
    db.add(url)
    await db.flush()
    return url


async def _generate_unique_code(
    db: AsyncSession, max_attempts: int = 10
) -> str:
    """Generate a unique short code, retrying on collision."""
    for _ in range(max_attempts):
        code = generate_short_code(settings.SHORT_CODE_LENGTH)
        result = await db.execute(select(URL).where(URL.short_code == code))
        if result.scalar_one_or_none() is None:
            return code
    raise RuntimeError("Failed to generate a unique short code after multiple attempts")


async def get_url_by_short_code(db: AsyncSession, short_code: str) -> URL:
    """Retrieve a URL by short code. Raises if not found, inactive, or expired."""
    result = await db.execute(select(URL).where(URL.short_code == short_code))
    url = result.scalar_one_or_none()
    if url is None:
        raise URLNotFoundException(f"URL with short code '{short_code}' not found.")
    if not url.is_active:
        raise URLExpiredException(f"URL with short code '{short_code}' has been deactivated.")
    if url.expires_at is not None:
        expires = url.expires_at
        if expires.tzinfo is None:
            now = datetime.now(tz=timezone.utc).replace(tzinfo=None)
        else:
            now = datetime.now(tz=timezone.utc)
        if expires <= now:
            raise URLExpiredException(
                f"URL with short code '{short_code}' has expired."
            )
    return url


async def get_url_metadata(db: AsyncSession, short_code: str) -> URL:
    """Retrieve URL metadata (does not check expiration/active status)."""
    result = await db.execute(select(URL).where(URL.short_code == short_code))
    url = result.scalar_one_or_none()
    if url is None:
        raise URLNotFoundException(f"URL with short code '{short_code}' not found.")
    return url


async def list_urls(
    db: AsyncSession, skip: int = 0, limit: int = 20
) -> list[URL]:
    """List all URLs with pagination."""
    result = await db.execute(
        select(URL).order_by(URL.created_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def update_url(
    db: AsyncSession, short_code: str, **kwargs: object
) -> URL:
    """Update URL properties."""
    url = await get_url_metadata(db, short_code)
    for key, value in kwargs.items():
        if value is not None:
            setattr(url, key, value)
    await db.flush()
    await db.refresh(url)
    return url


async def deactivate_url(db: AsyncSession, short_code: str) -> None:
    """Soft-delete a URL by marking it inactive."""
    url = await get_url_metadata(db, short_code)
    url.is_active = False
    await db.flush()
