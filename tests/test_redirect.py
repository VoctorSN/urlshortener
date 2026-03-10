import pytest
from httpx import AsyncClient


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

    async def test_redirect_inactive_url(self, client: AsyncClient, sample_url: dict):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        # Deactivate
        await client.delete(f"/api/urls/{short_code}")

        response = await client.get(f"/{short_code}", follow_redirects=False)
        assert response.status_code == 410

    async def test_redirect_increments_click_count(
        self, client: AsyncClient, sample_url: dict
    ):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        # Click 3 times
        for _ in range(3):
            await client.get(f"/{short_code}", follow_redirects=False)

        # Check click count
        get_resp = await client.get(f"/api/urls/{short_code}")
        assert get_resp.json()["click_count"] == 3
