from collections import Counter
from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from user_agents import parse as ua_parse

from app.models.click import ClickEvent
from app.models.url import URL
from app.schemas.click import AnalyticsSummary


def parse_user_agent(ua_string: str) -> tuple[str, str]:
    """Parse a User-Agent string into (browser, os) tuple."""
    ua = ua_parse(ua_string)
    browser = f"{ua.browser.family} {ua.browser.version_string}".strip()
    os_name = f"{ua.os.family} {ua.os.version_string}".strip()
    return browser, os_name


async def record_click(
    db: AsyncSession,
    url_id: int,
    ip_address: str | None = None,
    user_agent_str: str | None = None,
    referrer: str | None = None,
) -> ClickEvent:
    """Record a click event and increment the URL's click counter."""
    browser = None
    os_name = None
    if user_agent_str:
        browser, os_name = parse_user_agent(user_agent_str)

    click = ClickEvent(
        url_id=url_id,
        ip_address=ip_address,
        user_agent=user_agent_str,
        browser=browser,
        os=os_name,
        referrer=referrer,
    )
    db.add(click)

    # Increment click_count atomically
    result = await db.execute(select(URL).where(URL.id == url_id))
    url = result.scalar_one()
    url.click_count = URL.click_count + 1  # type: ignore[assignment]

    await db.flush()
    return click


async def get_analytics_summary(
    db: AsyncSession,
    short_code: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> AnalyticsSummary:
    """Aggregate click analytics for a URL."""
    # Get the URL
    url_result = await db.execute(select(URL).where(URL.short_code == short_code))
    url = url_result.scalar_one_or_none()
    if url is None:
        from app.exceptions import URLNotFoundException
        raise URLNotFoundException(f"URL with short code '{short_code}' not found.")

    # Build query for click events
    query = select(ClickEvent).where(ClickEvent.url_id == url.id)
    if start_date:
        start_dt = datetime(start_date.year, start_date.month, start_date.day, tzinfo=timezone.utc)
        query = query.where(ClickEvent.clicked_at >= start_dt)
    if end_date:
        end_dt = datetime(
            end_date.year, end_date.month, end_date.day, 23, 59, 59, tzinfo=timezone.utc
        )
        query = query.where(ClickEvent.clicked_at <= end_dt)

    result = await db.execute(query)
    clicks = list(result.scalars().all())

    # Aggregate
    unique_ips: set[str] = set()
    browsers: Counter[str] = Counter()
    operating_systems: Counter[str] = Counter()
    referrers: Counter[str] = Counter()
    clicks_by_date: Counter[date] = Counter()

    for click in clicks:
        if click.ip_address:
            unique_ips.add(click.ip_address)
        if click.browser:
            browsers[click.browser] += 1
        if click.os:
            operating_systems[click.os] += 1
        if click.referrer:
            referrers[click.referrer] += 1
        if click.clicked_at:
            click_date = click.clicked_at.date() if isinstance(click.clicked_at, datetime) else click.clicked_at
            clicks_by_date[click_date] += 1

    return AnalyticsSummary(
        short_code=short_code,
        total_clicks=len(clicks),
        unique_visitors=len(unique_ips),
        browsers=dict(browsers),
        operating_systems=dict(operating_systems),
        referrers=dict(referrers),
        clicks_by_date=dict(clicks_by_date),
    )


async def get_click_events(
    db: AsyncSession,
    short_code: str,
    skip: int = 0,
    limit: int = 20,
) -> list[ClickEvent]:
    """Get paginated raw click events for a URL."""
    url_result = await db.execute(select(URL).where(URL.short_code == short_code))
    url = url_result.scalar_one_or_none()
    if url is None:
        from app.exceptions import URLNotFoundException
        raise URLNotFoundException(f"URL with short code '{short_code}' not found.")

    result = await db.execute(
        select(ClickEvent)
        .where(ClickEvent.url_id == url.id)
        .order_by(ClickEvent.clicked_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())
