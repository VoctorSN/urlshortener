from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient


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
        self, client: AsyncClient, db_session
    ):
        """Create a URL, manually set expiration to the past, then try redirecting."""
        from app.models.url import URL
        from sqlalchemy import select

        # Create a URL via API
        payload = {"original_url": "https://example.com"}
        create_resp = await client.post("/api/urls", json=payload)
        short_code = create_resp.json()["short_code"]

        # Manually expire it in the database
        result = await db_session.execute(
            select(URL).where(URL.short_code == short_code)
        )
        url = result.scalar_one()
        url.expires_at = datetime.now(tz=timezone.utc) - timedelta(hours=1)
        await db_session.commit()

        # Try to redirect
        response = await client.get(f"/{short_code}", follow_redirects=False)
        assert response.status_code == 410

    async def test_expired_url_metadata_still_accessible(
        self, client: AsyncClient, db_session
    ):
        """Expired URLs should still be viewable via the metadata endpoint."""
        from app.models.url import URL
        from sqlalchemy import select

        payload = {"original_url": "https://example.com"}
        create_resp = await client.post("/api/urls", json=payload)
        short_code = create_resp.json()["short_code"]

        # Manually expire it
        result = await db_session.execute(
            select(URL).where(URL.short_code == short_code)
        )
        url = result.scalar_one()
        url.expires_at = datetime.now(tz=timezone.utc) - timedelta(hours=1)
        await db_session.commit()

        # Metadata should still be accessible
        response = await client.get(f"/api/urls/{short_code}")
        assert response.status_code == 200
