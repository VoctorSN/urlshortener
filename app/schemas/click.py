from datetime import date, datetime, timezone

from pydantic import BaseModel, model_validator


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

    @model_validator(mode="after")
    def ensure_utc_clicked_at(self) -> "ClickEventResponse":
        """Ensure clicked_at is timezone-aware (UTC)."""
        if self.clicked_at is not None and self.clicked_at.tzinfo is None:
            object.__setattr__(self, "clicked_at", self.clicked_at.replace(tzinfo=timezone.utc))
        return self


class AnalyticsSummary(BaseModel):
    """Aggregated analytics for a URL."""

    short_code: str
    total_clicks: int
    unique_visitors: int
    browsers: dict[str, int]
    operating_systems: dict[str, int]
    referrers: dict[str, int]
    clicks_by_date: dict[date, int]
