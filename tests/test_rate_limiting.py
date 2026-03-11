import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestRateLimiting:
    async def test_rate_limit_allows_within_limit(
        self, client: AsyncClient, sample_url: dict
    ):
        """A few requests should succeed without triggering rate limits."""
        for _ in range(3):
            response = await client.post("/api/urls", json=sample_url)
            assert response.status_code == 201

    async def test_health_endpoint_no_rate_limit(self, client: AsyncClient):
        """Health endpoint should always respond regardless of rate limiting."""
        for _ in range(10):
            response = await client.get("/health")
            assert response.status_code == 200
            assert response.json() == {"status": "healthy"}

    async def test_get_urls_within_limit(self, client: AsyncClient):
        """GET /api/urls should work within rate limit."""
        for _ in range(5):
            response = await client.get("/api/urls")
            assert response.status_code == 200

    async def test_redirect_within_limit(
        self, client: AsyncClient, sample_url: dict
    ):
        """Redirect should work within rate limit."""
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        for _ in range(5):
            response = await client.get(f"/{short_code}", follow_redirects=False)
            assert response.status_code == 307
