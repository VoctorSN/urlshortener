from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import limiter
from app.schemas.click import AnalyticsSummary, ClickEventResponse
from app.services.analytics_service import get_analytics_summary, get_click_events

router = APIRouter()


@router.get(
    "/{short_code}/analytics",
    response_model=AnalyticsSummary,
    summary="Get analytics summary",
    description="Retrieve aggregated click analytics for a shortened URL.",
)
@limiter.limit("60/minute")
async def analytics_summary(
    short_code: str,
    request: Request,
    start_date: date | None = Query(default=None, description="Filter from this date (inclusive)"),
    end_date: date | None = Query(default=None, description="Filter until this date (inclusive)"),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsSummary:
    """Get aggregated analytics for a URL."""
    return await get_analytics_summary(db, short_code, start_date, end_date)


@router.get(
    "/{short_code}/clicks",
    response_model=list[ClickEventResponse],
    summary="Get raw click events",
    description="Retrieve paginated raw click event data for a shortened URL.",
)
@limiter.limit("60/minute")
async def click_events(
    short_code: str,
    request: Request,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[ClickEventResponse]:
    """Get raw click events for a URL."""
    events = await get_click_events(db, short_code, skip, limit)
    return [ClickEventResponse.model_validate(e) for e in events]
