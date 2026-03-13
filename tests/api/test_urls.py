from datetime import datetime, timedelta, timezone

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
        assert data["short_url"].endswith(data["short_code"])
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert data["expires_at"] is None

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
        assert "detail" in response2.json()

    async def test_create_url_invalid_url(self, client: AsyncClient):
        response = await client.post("/api/urls", json={"original_url": "not-a-url"})
        assert response.status_code == 422

    async def test_create_url_reserved_alias_api(self, client: AsyncClient):
        payload = {"original_url": "https://example.com", "custom_alias": "api"}
        response = await client.post("/api/urls", json=payload)
        assert response.status_code == 422

    async def test_create_url_reserved_alias_health(self, client: AsyncClient):
        payload = {"original_url": "https://example.com", "custom_alias": "health"}
        response = await client.post("/api/urls", json=payload)
        assert response.status_code == 422

    async def test_create_url_reserved_alias_docs(self, client: AsyncClient):
        payload = {"original_url": "https://example.com", "custom_alias": "docs"}
        response = await client.post("/api/urls", json=payload)
        assert response.status_code == 422

    async def test_create_url_reserved_alias_redoc(self, client: AsyncClient):
        payload = {"original_url": "https://example.com", "custom_alias": "redoc"}
        response = await client.post("/api/urls", json=payload)
        assert response.status_code == 422

    async def test_create_url_alias_too_short(self, client: AsyncClient):
        payload = {"original_url": "https://example.com", "custom_alias": "ab"}
        response = await client.post("/api/urls", json=payload)
        assert response.status_code == 422

    async def test_create_url_alias_too_long(self, client: AsyncClient):
        payload = {
            "original_url": "https://example.com",
            "custom_alias": "a" * 31,
        }
        response = await client.post("/api/urls", json=payload)
        assert response.status_code == 422

    async def test_create_url_alias_invalid_characters(self, client: AsyncClient):
        payload = {
            "original_url": "https://example.com",
            "custom_alias": "my link!",
        }
        response = await client.post("/api/urls", json=payload)
        assert response.status_code == 422

    async def test_create_url_with_future_expiration(self, client: AsyncClient):
        future = (datetime.now(tz=timezone.utc) + timedelta(days=7)).isoformat()
        payload = {"original_url": "https://example.com", "expires_at": future}
        response = await client.post("/api/urls", json=payload)
        assert response.status_code == 201
        assert response.json()["expires_at"] is not None

    async def test_create_url_with_past_expiration_rejected(self, client: AsyncClient):
        past = (datetime.now(tz=timezone.utc) - timedelta(days=1)).isoformat()
        payload = {"original_url": "https://example.com", "expires_at": past}
        response = await client.post("/api/urls", json=payload)
        assert response.status_code == 422

    async def test_create_url_missing_original_url(self, client: AsyncClient):
        response = await client.post("/api/urls", json={})
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
        assert "detail" in response.json()

    async def test_get_url_response_has_all_fields(
        self, client: AsyncClient, sample_url: dict
    ):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        response = await client.get(f"/api/urls/{short_code}")
        assert response.status_code == 200
        data = response.json()
        expected_fields = {
            "id", "short_code", "original_url", "short_url",
            "is_active", "click_count", "created_at", "updated_at", "expires_at",
        }
        assert expected_fields.issubset(data.keys())


@pytest.mark.asyncio
class TestListURLs:
    async def test_list_urls_empty(self, client: AsyncClient):
        response = await client.get("/api/urls")
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_urls_pagination(self, client: AsyncClient):
        for i in range(5):
            await client.post(
                "/api/urls",
                json={"original_url": f"https://example.com/{i}"},
            )

        response = await client.get("/api/urls?skip=0&limit=2")
        assert response.status_code == 200
        assert len(response.json()) == 2

        response = await client.get("/api/urls?skip=2&limit=2")
        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_list_urls_skip_beyond_total(self, client: AsyncClient):
        await client.post(
            "/api/urls", json={"original_url": "https://example.com"}
        )
        response = await client.get("/api/urls?skip=100&limit=10")
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_urls_returns_all_created(self, client: AsyncClient):
        for i in range(3):
            await client.post(
                "/api/urls",
                json={"original_url": f"https://example.com/{i}"},
            )
        response = await client.get("/api/urls")
        assert response.status_code == 200
        assert len(response.json()) == 3


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

    async def test_update_url_expiration(self, client: AsyncClient, sample_url: dict):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        future = (datetime.now(tz=timezone.utc) + timedelta(days=30)).isoformat()
        response = await client.patch(
            f"/api/urls/{short_code}",
            json={"expires_at": future},
        )
        assert response.status_code == 200
        assert response.json()["expires_at"] is not None

    async def test_update_url_not_found(self, client: AsyncClient):
        response = await client.patch(
            "/api/urls/nonexistent",
            json={"original_url": "https://updated.com"},
        )
        assert response.status_code == 404
        assert "detail" in response.json()

    async def test_update_url_is_active(self, client: AsyncClient, sample_url: dict):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        response = await client.patch(
            f"/api/urls/{short_code}",
            json={"is_active": False},
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False


@pytest.mark.asyncio
class TestDeleteURL:
    async def test_delete_url(self, client: AsyncClient, sample_url: dict):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        response = await client.delete(f"/api/urls/{short_code}")
        assert response.status_code == 204

    async def test_delete_url_sets_inactive(
        self, client: AsyncClient, sample_url: dict
    ):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        await client.delete(f"/api/urls/{short_code}")

        get_resp = await client.get(f"/api/urls/{short_code}")
        assert get_resp.status_code == 200
        assert get_resp.json()["is_active"] is False

    async def test_delete_url_metadata_still_accessible(
        self, client: AsyncClient, sample_url: dict
    ):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        await client.delete(f"/api/urls/{short_code}")

        get_resp = await client.get(f"/api/urls/{short_code}")
        assert get_resp.status_code == 200
        assert get_resp.json()["short_code"] == short_code
        assert get_resp.json()["original_url"] is not None

    async def test_delete_url_not_found(self, client: AsyncClient):
        response = await client.delete("/api/urls/nonexistent")
        assert response.status_code == 404
