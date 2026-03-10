from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import limiter
from app.services.analytics_service import record_click
from app.services.url_service import get_url_by_short_code
from app.utils import extract_client_ip

router = APIRouter()


@router.get(
    "/{short_code}",
    summary="Redirect to original URL",
    response_class=RedirectResponse,
    status_code=307,
    description="Look up a short code and redirect to the original URL. Records click analytics.",
)
@limiter.limit("120/minute")
async def redirect_to_url(
    short_code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Redirect to the original URL for a given short code."""
    url = await get_url_by_short_code(db, short_code)
    await record_click(
        db=db,
        url_id=url.id,
        ip_address=extract_client_ip(request),
        user_agent_str=request.headers.get("user-agent"),
        referrer=request.headers.get("referer"),
    )
    return RedirectResponse(url=url.original_url, status_code=307)
