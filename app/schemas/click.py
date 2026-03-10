from datetime import date, datetime

from pydantic import BaseModel


class ClickEventResponse(BaseModel):
    """Schema for a single click event."""

    model_config = {"from_attributes": True}

    id: int
    clicked_at: datetime
    ip_address: str | None
    user_agent: str | None
    browser: str | None
    os: str | None
    referrer: str | None
    country: str | None


class AnalyticsSummary(BaseModel):
    """Aggregated analytics for a URL."""

    short_code: str
    total_clicks: int
    unique_visitors: int
    browsers: dict[str, int]
    operating_systems: dict[str, int]
    referrers: dict[str, int]
    clicks_by_date: dict[date, int]
