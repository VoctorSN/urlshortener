import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestQRCode:
    async def test_qr_code_returns_png(self, client: AsyncClient, sample_url: dict):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        response = await client.get(f"/api/urls/{short_code}/qr")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    async def test_qr_code_valid_image(self, client: AsyncClient, sample_url: dict):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        response = await client.get(f"/api/urls/{short_code}/qr")
        assert response.content[:8] == b"\x89PNG\r\n\x1a\n"

    async def test_qr_code_not_found(self, client: AsyncClient):
        response = await client.get("/api/urls/nonexistent/qr")
        assert response.status_code == 404
        assert "detail" in response.json()

    async def test_qr_code_custom_size(self, client: AsyncClient, sample_url: dict):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        small = await client.get(f"/api/urls/{short_code}/qr?size=5")
        large = await client.get(f"/api/urls/{short_code}/qr?size=20")

        assert small.status_code == 200
        assert large.status_code == 200
        assert len(large.content) > len(small.content)

    async def test_qr_code_default_size(self, client: AsyncClient, sample_url: dict):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        response = await client.get(f"/api/urls/{short_code}/qr")
        assert response.status_code == 200
        assert len(response.content) > 0

    async def test_qr_code_min_size(self, client: AsyncClient, sample_url: dict):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        response = await client.get(f"/api/urls/{short_code}/qr?size=1")
        assert response.status_code == 200
        assert response.content[:8] == b"\x89PNG\r\n\x1a\n"

    async def test_qr_code_max_size(self, client: AsyncClient, sample_url: dict):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        response = await client.get(f"/api/urls/{short_code}/qr?size=40")
        assert response.status_code == 200
        assert response.content[:8] == b"\x89PNG\r\n\x1a\n"

    async def test_qr_code_size_out_of_range(self, client: AsyncClient, sample_url: dict):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        response = await client.get(f"/api/urls/{short_code}/qr?size=0")
        assert response.status_code == 422

        response = await client.get(f"/api/urls/{short_code}/qr?size=41")
        assert response.status_code == 422
