import logging

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestTokenSecurity:
    async def test_protected_route_requires_token(
        self, unauthenticated_client: AsyncClient, sample_url: dict
    ):
        response = await unauthenticated_client.post("/api/urls", json=sample_url)
        assert response.status_code == 401

    async def test_invalid_token_rejected(
        self,
        unauthenticated_client: AsyncClient,
        sample_url: dict,
        caplog: pytest.LogCaptureFixture,
    ):
        caplog.set_level(logging.WARNING, logger="app.security")
        response = await unauthenticated_client.post(
            "/api/urls",
            json=sample_url,
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401
        assert "JWT validation failed:" in caplog.text
        assert "(DecodeError)" in caplog.text

    async def test_invalid_authorization_header_format_rejected(
        self, unauthenticated_client: AsyncClient, sample_url: dict
    ):
        response = await unauthenticated_client.post(
            "/api/urls",
            json=sample_url,
            headers={"Authorization": "Basic abc123"},
        )
        assert response.status_code == 401
        assert response.headers.get("WWW-Authenticate") == "Bearer"

    async def test_api_token_allows_protected_route(
        self, client: AsyncClient, sample_url: dict
    ):
        response = await client.post("/api/urls", json=sample_url)
        assert response.status_code == 201

    async def test_jwt_allows_protected_route(
        self,
        unauthenticated_client: AsyncClient,
        sample_url: dict,
        jwt_token: str,
    ):
        response = await unauthenticated_client.post(
            "/api/urls",
            json=sample_url,
            headers={"Authorization": f"Bearer {jwt_token}"},
        )
        assert response.status_code == 201

    async def test_health_route_is_public(self, unauthenticated_client: AsyncClient):
        response = await unauthenticated_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    async def test_redirect_route_is_public(
        self, client: AsyncClient, unauthenticated_client: AsyncClient, sample_url: dict
    ):
        create_resp = await client.post("/api/urls", json=sample_url)
        short_code = create_resp.json()["short_code"]

        response = await unauthenticated_client.get(
            f"/{short_code}", follow_redirects=False
        )
        assert response.status_code == 307

    async def test_options_preflight_not_blocked_by_auth(
        self, unauthenticated_client: AsyncClient
    ):
        response = await unauthenticated_client.options("/api/urls")
        assert response.status_code != 401
