import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAnalyticsSummary:
    async def test_analytics_summary_empty(self, client: AsyncClient, sample_url: dict):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        response = await client.get(f"/api/urls/{short_code}/analytics")
        assert response.status_code == 200
        data = response.json()
        assert data["total_clicks"] == 0
        assert data["unique_visitors"] == 0
        assert data["browsers"] == {}

    async def test_analytics_summary_with_clicks(
        self, client: AsyncClient, sample_url: dict
    ):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        # Generate clicks with different user agents
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

    async def test_analytics_not_found(self, client: AsyncClient):
        response = await client.get("/api/urls/nonexistent/analytics")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestClickEvents:
    async def test_click_events_pagination(
        self, client: AsyncClient, sample_url: dict
    ):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        # Generate 5 clicks
        for _ in range(5):
            await client.get(f"/{short_code}", follow_redirects=False)

        # Get first 2
        response = await client.get(f"/api/urls/{short_code}/clicks?skip=0&limit=2")
        assert response.status_code == 200
        assert len(response.json()) == 2

        # Get all
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
