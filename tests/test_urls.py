import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestCreateURL:
    async def test_create_url_success(self, client: AsyncClient, sample_url: dict):
        response = await client.post("/api/urls", json=sample_url)
        assert response.status_code == 201
        data = response.json()
        assert "short_code" in data
        assert data["original_url"] == sample_url["original_url"]
        assert data["is_active"] is True
        assert data["click_count"] == 0
        assert "short_url" in data

    async def test_create_url_with_custom_alias(self, client: AsyncClient):
        payload = {
            "original_url": "https://example.com",
            "custom_alias": "my-custom",
        }
        response = await client.post("/api/urls", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["short_code"] == "my-custom"

    async def test_create_url_custom_alias_conflict(self, client: AsyncClient):
        payload = {
            "original_url": "https://example.com",
            "custom_alias": "taken",
        }
        response1 = await client.post("/api/urls", json=payload)
        assert response1.status_code == 201

        response2 = await client.post("/api/urls", json=payload)
        assert response2.status_code == 409

    async def test_create_url_invalid_url(self, client: AsyncClient):
        response = await client.post("/api/urls", json={"original_url": "not-a-url"})
        assert response.status_code == 422

    async def test_create_url_reserved_alias(self, client: AsyncClient):
        payload = {
            "original_url": "https://example.com",
            "custom_alias": "api",
        }
        response = await client.post("/api/urls", json=payload)
        assert response.status_code == 422


@pytest.mark.asyncio
class TestGetURL:
    async def test_get_url_by_short_code(self, client: AsyncClient, sample_url: dict):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        response = await client.get(f"/api/urls/{short_code}")
        assert response.status_code == 200
        data = response.json()
        assert data["short_code"] == short_code
        assert data["original_url"] == sample_url["original_url"]

    async def test_get_url_not_found(self, client: AsyncClient):
        response = await client.get("/api/urls/nonexistent")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestListURLs:
    async def test_list_urls_empty(self, client: AsyncClient):
        response = await client.get("/api/urls")
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_urls_pagination(self, client: AsyncClient):
        # Create 5 URLs
        for i in range(5):
            await client.post(
                "/api/urls",
                json={"original_url": f"https://example.com/{i}"},
            )

        # Get first 2
        response = await client.get("/api/urls?skip=0&limit=2")
        assert response.status_code == 200
        assert len(response.json()) == 2

        # Get next 2
        response = await client.get("/api/urls?skip=2&limit=2")
        assert response.status_code == 200
        assert len(response.json()) == 2


@pytest.mark.asyncio
class TestUpdateURL:
    async def test_update_url(self, client: AsyncClient, sample_url: dict):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        response = await client.patch(
            f"/api/urls/{short_code}",
            json={"original_url": "https://updated.com"},
        )
        assert response.status_code == 200
        assert response.json()["original_url"] == "https://updated.com/"


@pytest.mark.asyncio
class TestDeleteURL:
    async def test_delete_url(self, client: AsyncClient, sample_url: dict):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        response = await client.delete(f"/api/urls/{short_code}")
        assert response.status_code == 204

        # Verify it's deactivated
        get_resp = await client.get(f"/api/urls/{short_code}")
        assert get_resp.status_code == 200
        assert get_resp.json()["is_active"] is False
