from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.url import URL


class ClickEvent(Base):
    """Records a single click on a shortened URL."""

    __tablename__ = "click_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    url_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("urls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    clicked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    browser: Mapped[str | None] = mapped_column(String(100), nullable=True)
    os: Mapped[str | None] = mapped_column(String(100), nullable=True)
    referrer: Mapped[str | None] = mapped_column(Text, nullable=True)
    country: Mapped[str | None] = mapped_column(
        String(100), nullable=True, default="Unknown"
    )

    url: Mapped[URL] = relationship("URL", back_populates="clicks")
