from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, model_validator


class URLCreate(BaseModel):
    """Schema for creating a new shortened URL."""

    original_url: HttpUrl
    custom_alias: str | None = Field(
        default=None,
        min_length=3,
        max_length=30,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Optional custom short code (3-30 chars, alphanumeric, hyphens, underscores)",
    )
    expires_at: datetime | None = Field(
        default=None,
        description="Optional expiration timestamp (UTC). Must be in the future.",
    )

    @model_validator(mode="after")
    def validate_expiration(self) -> "URLCreate":
        if self.expires_at is not None:
            now = datetime.now(tz=self.expires_at.tzinfo)
            if self.expires_at <= now:
                raise ValueError("expires_at must be a future datetime")
        return self


class URLResponse(BaseModel):
    """Schema for a URL response."""

    model_config = {"from_attributes": True}

    id: int
    short_code: str
    original_url: str
    short_url: str
    is_active: bool
    click_count: int
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None


class URLUpdate(BaseModel):
    """Schema for partially updating a URL."""

    original_url: HttpUrl | None = None
    expires_at: datetime | None = None
    is_active: bool | None = None
