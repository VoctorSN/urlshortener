import requests
import datetime

BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_get_short_code_redirect_to_original_url():
    created_codes = []

    def create_url(original_url, custom_alias=None, expires_at=None):
        body = {"original_url": original_url}
        if custom_alias:
            body["custom_alias"] = custom_alias
        if expires_at:
            body["expires_at"] = expires_at
        resp = requests.post(f"{BASE_URL}/api/urls", json=body, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        created_codes.append(data["short_code"])
        return data

    def patch_url(short_code, patch_body):
        resp = requests.patch(f"{BASE_URL}/api/urls/{short_code}", json=patch_body, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def delete_url(short_code):
        resp = requests.delete(f"{BASE_URL}/api/urls/{short_code}", timeout=TIMEOUT)
        return resp

    try:
        # Create active URL (no expires_at means active)
        active_url_data = create_url("https://example.com/active", custom_alias=None)
        active_code = active_url_data["short_code"]

        # Test redirect for valid active short_code
        redirect_resp = requests.get(f"{BASE_URL}/{active_code}", allow_redirects=False, timeout=TIMEOUT)
        assert redirect_resp.status_code == 307
        assert "Location" in redirect_resp.headers
        assert redirect_resp.headers["Location"] == active_url_data["original_url"]

        # Verify click count increased by fetching URL metadata
        meta_resp = requests.get(f"{BASE_URL}/api/urls/{active_code}", timeout=TIMEOUT)
        meta_resp.raise_for_status()
        meta_data = meta_resp.json()
        assert meta_data["click_count"] >= 1
        assert meta_data["is_active"] is True

        # Test 404 for nonexistent code
        nonexist_code = "nonexistent12345"
        resp_404 = requests.get(f"{BASE_URL}/{nonexist_code}", allow_redirects=False, timeout=TIMEOUT)
        assert resp_404.status_code == 404

        # Create URL with future expires_at for expired test
        future_dt = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)).isoformat()
        expired_url_data = create_url("https://example.com/expired", expires_at=future_dt)
        expired_code = expired_url_data["short_code"]

        # Instead of patching expires_at to past (invalid), patch is_active to False to simulate expiration
        patch_url(expired_code, {"is_active": False})

        # Test 410 for expired (deactivated) code
        resp_410 = requests.get(f"{BASE_URL}/{expired_code}", allow_redirects=False, timeout=TIMEOUT)
        assert resp_410.status_code == 410

        # Create URL and soft-delete (deactivate) it to test 410 for deactivated
        deact_url_data = create_url("https://example.com/deactivated")
        deact_code = deact_url_data["short_code"]
        patch_url(deact_code, {"is_active": False})

        # Test 410 for deactivated code
        resp_410_deact = requests.get(f"{BASE_URL}/{deact_code}", allow_redirects=False, timeout=TIMEOUT)
        assert resp_410_deact.status_code == 410

    finally:
        # Cleanup all created URLs
        for code in created_codes:
            try:
                delete_url(code)
            except Exception:
                pass

test_get_short_code_redirect_to_original_url()
