from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import limiter
from app.services.qr_service import generate_qr_code
from app.services.url_service import get_url_metadata

router = APIRouter()


@router.get(
    "/{short_code}/qr",
    summary="Generate QR code",
    description="Generate a QR code PNG image for a shortened URL.",
    responses={200: {"content": {"image/png": {}}}},
)
@limiter.limit("30/minute")
async def get_qr_code(
    short_code: str,
    request: Request,
    size: int = Query(default=10, ge=1, le=40, description="QR code box size"),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Generate and return a QR code PNG for a shortened URL."""
    url = await get_url_metadata(db, short_code)
    short_url = f"{settings.BASE_URL}/{url.short_code}"
    image_bytes = generate_qr_code(data=short_url, size=size)
    return Response(content=image_bytes, media_type="image/png")
