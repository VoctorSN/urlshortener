from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
class TestExpiration:
    async def test_create_url_with_expiration(self, client: AsyncClient):
        future = (datetime.now(tz=timezone.utc) + timedelta(days=7)).isoformat()
        payload = {
            "original_url": "https://example.com",
            "expires_at": future,
        }
        response = await client.post("/api/urls", json=payload)
        assert response.status_code == 201
        assert response.json()["expires_at"] is not None

    async def test_create_url_past_expiration_rejected(self, client: AsyncClient):
        past = (datetime.now(tz=timezone.utc) - timedelta(days=1)).isoformat()
        payload = {
            "original_url": "https://example.com",
            "expires_at": past,
        }
        response = await client.post("/api/urls", json=payload)
        assert response.status_code == 422

    async def test_expired_url_redirect_returns_410(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Create a URL, manually set expiration to the past, then try redirecting."""
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

    async def test_expired_url_metadata_still_accessible(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Expired URLs should still be viewable via the metadata endpoint."""
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

        response = await client.get(f"/api/urls/{short_code}")
        assert response.status_code == 200
        data = response.json()
        assert data["short_code"] == short_code
        assert data["original_url"] is not None

    async def test_non_expired_url_redirect_works(self, client: AsyncClient):
        """URL with future expiration should redirect normally."""
        future = (datetime.now(tz=timezone.utc) + timedelta(days=7)).isoformat()
        payload = {
            "original_url": "https://example.com",
            "expires_at": future,
        }
        create_resp = await client.post("/api/urls", json=payload)
        short_code = create_resp.json()["short_code"]

        response = await client.get(f"/{short_code}", follow_redirects=False)
        assert response.status_code == 307

    async def test_update_url_expiration(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Update expiration on a URL."""
        payload = {"original_url": "https://example.com"}
        create_resp = await client.post("/api/urls", json=payload)
        short_code = create_resp.json()["short_code"]

        future = (datetime.now(tz=timezone.utc) + timedelta(days=30)).isoformat()
        response = await client.patch(
            f"/api/urls/{short_code}",
            json={"expires_at": future},
        )
        assert response.status_code == 200
        assert response.json()["expires_at"] is not None

    async def test_expired_url_analytics_still_accessible(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Expired URL analytics should still be accessible."""
        from app.models.url import URL

        payload = {"original_url": "https://example.com"}
        create_resp = await client.post("/api/urls", json=payload)
        short_code = create_resp.json()["short_code"]

        # Generate a click before expiring
        await client.get(f"/{short_code}", follow_redirects=False)

        # Expire the URL
        result = await db_session.execute(
            select(URL).where(URL.short_code == short_code)
        )
        url = result.scalar_one()
        url.expires_at = datetime.now(tz=timezone.utc) - timedelta(hours=1)
        await db_session.commit()

        response = await client.get(f"/api/urls/{short_code}/analytics")
        assert response.status_code == 200
        assert response.json()["total_clicks"] == 1
