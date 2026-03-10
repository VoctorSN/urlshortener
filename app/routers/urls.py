from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import limiter
from app.models.url import URL
from app.schemas.url import URLCreate, URLResponse, URLUpdate
from app.services.url_service import (
    create_short_url,
    deactivate_url,
    get_url_metadata,
    list_urls,
    update_url,
)

router = APIRouter()


def _build_response(url: URL) -> URLResponse:
    """Build a URLResponse from a URL model instance."""
    return URLResponse(
        id=url.id,
        short_code=url.short_code,
        original_url=url.original_url,
        short_url=f"{settings.BASE_URL}/{url.short_code}",
        is_active=url.is_active,
        click_count=url.click_count,
        created_at=url.created_at,
        updated_at=url.updated_at,
        expires_at=url.expires_at,
    )


@router.post(
    "",
    response_model=URLResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a shortened URL",
    description="Shorten a URL with an optional custom alias and expiration date.",
)
@limiter.limit("30/minute")
async def create_url(
    request: Request,
    body: URLCreate,
    db: AsyncSession = Depends(get_db),
) -> URLResponse:
    """Create a new shortened URL."""
    url = await create_short_url(
        db=db,
        original_url=str(body.original_url),
        custom_alias=body.custom_alias,
        expires_at=body.expires_at,
    )
    return _build_response(url)


@router.get(
    "",
    response_model=list[URLResponse],
    summary="List all URLs",
    description="Retrieve a paginated list of all shortened URLs.",
)
@limiter.limit("60/minute")
async def list_all_urls(
    request: Request,
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Max records to return"),
    db: AsyncSession = Depends(get_db),
) -> list[URLResponse]:
    """List all shortened URLs with pagination."""
    urls = await list_urls(db, skip=skip, limit=limit)
    return [_build_response(u) for u in urls]


@router.get(
    "/{short_code}",
    response_model=URLResponse,
    summary="Get URL metadata",
    description="Retrieve metadata for a specific shortened URL.",
)
@limiter.limit("60/minute")
async def get_url(
    short_code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> URLResponse:
    """Get metadata for a shortened URL."""
    url = await get_url_metadata(db, short_code)
    return _build_response(url)


@router.patch(
    "/{short_code}",
    response_model=URLResponse,
    summary="Update a URL",
    description="Partially update a shortened URL's properties.",
)
@limiter.limit("30/minute")
async def patch_url(
    short_code: str,
    body: URLUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> URLResponse:
    """Update a shortened URL."""
    update_data: dict[str, object] = {}
    if body.original_url is not None:
        update_data["original_url"] = str(body.original_url)
    if body.expires_at is not None:
        update_data["expires_at"] = body.expires_at
    if body.is_active is not None:
        update_data["is_active"] = body.is_active

    url = await update_url(db, short_code, **update_data)
    return _build_response(url)


@router.delete(
    "/{short_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate a URL",
    description="Soft-delete a shortened URL by marking it as inactive.",
)
@limiter.limit("30/minute")
async def delete_url(
    short_code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Deactivate a shortened URL."""
    await deactivate_url(db, short_code)
