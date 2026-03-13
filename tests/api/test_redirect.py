from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
class TestRedirect:
    async def test_redirect_success(self, client: AsyncClient, sample_url: dict):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        response = await client.get(f"/{short_code}", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == sample_url["original_url"]

    async def test_redirect_not_found(self, client: AsyncClient):
        response = await client.get("/nonexistent", follow_redirects=False)
        assert response.status_code == 404
        assert "detail" in response.json()

    async def test_redirect_inactive_url(self, client: AsyncClient, sample_url: dict):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        await client.delete(f"/api/urls/{short_code}")

        response = await client.get(f"/{short_code}", follow_redirects=False)
        assert response.status_code == 410

    async def test_redirect_expired_url(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        from app.models.url import URL

        payload = {"original_url": "https://example.com"}
        create_resp = await client.post("/api/urls", json=payload)
        short_code = create_resp.json()["short_code"]

        result = await db_session.execute(
            select(URL).where(URL.short_code == short_code)
        )
        url = result.scalar_one()
        url.expires_at = datetime.now(tz=timezone.utc) - timedelta(hours=1)
        await db_session.commit()

        response = await client.get(f"/{short_code}", follow_redirects=False)
        assert response.status_code == 410

    async def test_redirect_increments_click_count(
        self, client: AsyncClient, sample_url: dict
    ):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        for _ in range(3):
            await client.get(f"/{short_code}", follow_redirects=False)

        get_resp = await client.get(f"/api/urls/{short_code}")
        assert get_resp.json()["click_count"] == 3

    async def test_redirect_records_click_event(
        self, client: AsyncClient, sample_url: dict
    ):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        await client.get(
            f"/{short_code}",
            follow_redirects=False,
            headers={
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
                "referer": "https://google.com",
            },
        )

        clicks_resp = await client.get(f"/api/urls/{short_code}/clicks")
        assert clicks_resp.status_code == 200
        events = clicks_resp.json()
        assert len(events) == 1
        assert events[0]["referrer"] == "https://google.com"

    async def test_redirect_with_custom_alias(self, client: AsyncClient):
        payload = {
            "original_url": "https://example.com/target",
            "custom_alias": "myalias",
        }
        create_resp = await client.post("/api/urls", json=payload)
        assert create_resp.status_code == 201

        response = await client.get("/myalias", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "https://example.com/target"
