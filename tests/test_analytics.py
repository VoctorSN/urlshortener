from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
class TestAnalyticsSummary:
    async def test_analytics_summary_empty(self, client: AsyncClient, sample_url: dict):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        response = await client.get(f"/api/urls/{short_code}/analytics")
        assert response.status_code == 200
        data = response.json()
        assert data["short_code"] == short_code
        assert data["total_clicks"] == 0
        assert data["unique_visitors"] == 0
        assert data["browsers"] == {}
        assert data["operating_systems"] == {}
        assert data["referrers"] == {}
        assert data["clicks_by_date"] == {}

    async def test_analytics_summary_with_clicks(
        self, client: AsyncClient, sample_url: dict
    ):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        headers_list = [
            {
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0"
            },
            {
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Firefox/121.0"
            },
            {
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0"
            },
        ]
        for headers in headers_list:
            await client.get(
                f"/{short_code}", follow_redirects=False, headers=headers
            )

        response = await client.get(f"/api/urls/{short_code}/analytics")
        assert response.status_code == 200
        data = response.json()
        assert data["total_clicks"] == 3
        assert len(data["browsers"]) > 0
        assert len(data["operating_systems"]) > 0
        assert len(data["clicks_by_date"]) > 0

    async def test_analytics_not_found(self, client: AsyncClient):
        response = await client.get("/api/urls/nonexistent/analytics")
        assert response.status_code == 404
        assert "detail" in response.json()

    async def test_analytics_unique_visitors(
        self, client: AsyncClient, sample_url: dict
    ):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        # Same IP (testserver), 3 clicks = 1 unique visitor
        for _ in range(3):
            await client.get(f"/{short_code}", follow_redirects=False)

        response = await client.get(f"/api/urls/{short_code}/analytics")
        data = response.json()
        assert data["total_clicks"] == 3
        assert data["unique_visitors"] >= 1

    async def test_analytics_filter_by_dates(
        self, client: AsyncClient, db_session: AsyncSession, sample_url: dict
    ):
        from app.models.click import ClickEvent
        from app.models.url import URL

        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        # Generate a click
        await client.get(f"/{short_code}", follow_redirects=False)

        today = datetime.now(tz=timezone.utc).date()
        start = today.isoformat()
        end = today.isoformat()

        response = await client.get(
            f"/api/urls/{short_code}/analytics?start_date={start}&end_date={end}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_clicks"] >= 1

    async def test_analytics_filter_excludes_out_of_range(
        self, client: AsyncClient, sample_url: dict
    ):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        await client.get(f"/{short_code}", follow_redirects=False)

        # Filter to a past date range that shouldn't include today's click
        past = (datetime.now(tz=timezone.utc) - timedelta(days=30)).date().isoformat()
        past2 = (datetime.now(tz=timezone.utc) - timedelta(days=20)).date().isoformat()

        response = await client.get(
            f"/api/urls/{short_code}/analytics?start_date={past}&end_date={past2}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_clicks"] == 0

    async def test_analytics_referrers(
        self, client: AsyncClient, sample_url: dict
    ):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        await client.get(
            f"/{short_code}",
            follow_redirects=False,
            headers={"referer": "https://twitter.com"},
        )
        await client.get(
            f"/{short_code}",
            follow_redirects=False,
            headers={"referer": "https://google.com"},
        )

        response = await client.get(f"/api/urls/{short_code}/analytics")
        data = response.json()
        assert data["total_clicks"] == 2
        assert len(data["referrers"]) == 2


@pytest.mark.asyncio
class TestClickEvents:
    async def test_click_events_pagination(
        self, client: AsyncClient, sample_url: dict
    ):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        for _ in range(5):
            await client.get(f"/{short_code}", follow_redirects=False)

        response = await client.get(f"/api/urls/{short_code}/clicks?skip=0&limit=2")
        assert response.status_code == 200
        assert len(response.json()) == 2

        response = await client.get(f"/api/urls/{short_code}/clicks?skip=0&limit=10")
        assert response.status_code == 200
        assert len(response.json()) == 5

    async def test_click_events_contain_browser_info(
        self, client: AsyncClient, sample_url: dict
    ):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        await client.get(
            f"/{short_code}",
            follow_redirects=False,
            headers={
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
            },
        )

        response = await client.get(f"/api/urls/{short_code}/clicks")
        assert response.status_code == 200
        events = response.json()
        assert len(events) == 1
        assert events[0]["browser"] is not None
        assert events[0]["os"] is not None

    async def test_click_events_contain_all_fields(
        self, client: AsyncClient, sample_url: dict
    ):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        await client.get(
            f"/{short_code}",
            follow_redirects=False,
            headers={
                "user-agent": "Mozilla/5.0 (X11; Linux x86_64) Firefox/121.0",
                "referer": "https://example.org",
            },
        )

        response = await client.get(f"/api/urls/{short_code}/clicks")
        events = response.json()
        assert len(events) == 1
        event = events[0]
        expected_fields = {
            "id", "clicked_at", "ip_address", "user_agent",
            "browser", "os", "referrer", "country",
        }
        assert expected_fields.issubset(event.keys())
        assert event["referrer"] == "https://example.org"

    async def test_click_events_not_found(self, client: AsyncClient):
        response = await client.get("/api/urls/nonexistent/clicks")
        assert response.status_code == 404
        assert "detail" in response.json()

    async def test_click_events_empty(
        self, client: AsyncClient, sample_url: dict
    ):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        response = await client.get(f"/api/urls/{short_code}/clicks")
        assert response.status_code == 200
        assert response.json() == []

    async def test_click_events_ip_address(
        self, client: AsyncClient, sample_url: dict
    ):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        await client.get(f"/{short_code}", follow_redirects=False)

        response = await client.get(f"/api/urls/{short_code}/clicks")
        events = response.json()
        assert len(events) == 1
        assert events[0]["ip_address"] is not None
