import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHealthCheck:
    async def test_health_check_returns_200(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200

    async def test_health_check_body(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.json() == {"status": "healthy"}

    async def test_health_check_status_field(self, client: AsyncClient):
        response = await client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


@pytest.mark.asyncio
class TestFavicon:
    async def test_favicon_returns_204(self, client: AsyncClient):
        response = await client.get("/favicon.ico")
        assert response.status_code == 204
