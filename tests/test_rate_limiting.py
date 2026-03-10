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

    async def test_health_endpoint_works(self, client: AsyncClient):
        """Health endpoint should always respond."""
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
