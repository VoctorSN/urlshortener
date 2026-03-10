import requests
import datetime

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_get_short_code_redirect_to_original_url():
    created_short_code = None
    headers = {
        "User-Agent": "test-agent",
        "Referer": "http://testreferrer.com",
    }
    # Step 1: Create a new active short URL
    try:
        future_date = (datetime.datetime.utcnow() + datetime.timedelta(days=10)).replace(microsecond=0).isoformat() + "Z"
        create_payload = {
            "original_url": "https://example.com/original-path",
            "expires_at": future_date
        }
        resp_create = requests.post(
            f"{BASE_URL}/api/urls",
            json=create_payload,
            timeout=TIMEOUT
        )
        assert resp_create.status_code == 201, f"Expected 201 Created but got {resp_create.status_code}"
        created = resp_create.json()
        assert "short_code" in created and created["short_code"], "Response missing short_code"
        assert created["original_url"] == create_payload["original_url"], "Original URL mismatch"
        created_short_code = created["short_code"]

        # Step 2: Redirect with valid active short_code: Expect HTTP 307 and Location header
        resp_redirect = requests.get(
            f"{BASE_URL}/{created_short_code}",
            headers=headers,
            allow_redirects=False,
            timeout=TIMEOUT
        )
        assert resp_redirect.status_code == 307, f"Expected 307 redirect but got {resp_redirect.status_code}"
        assert "Location" in resp_redirect.headers, "Missing Location header in redirect"
        assert resp_redirect.headers["Location"] == create_payload["original_url"], "Location header mismatch"

        # Step 3: Redirect with nonexistent short_code: Expect 404 Not Found
        resp_404 = requests.get(
            f"{BASE_URL}/nonexistentcode123456",
            allow_redirects=False,
            timeout=TIMEOUT
        )
        assert resp_404.status_code == 404, f"Expected 404 Not Found for nonexistent code but got {resp_404.status_code}"

        # Step 4: Create a deactivated URL and expect 410 Gone
        custom_alias_deactivated = f"deactivated-{int(datetime.datetime.utcnow().timestamp())}"
        create_payload_deactivated = {
            "original_url": "https://example.com/deactivated",
            "custom_alias": custom_alias_deactivated,
            "expires_at": future_date
        }
        resp_create_deactivated = requests.post(
            f"{BASE_URL}/api/urls",
            json=create_payload_deactivated,
            timeout=TIMEOUT
        )
        assert resp_create_deactivated.status_code == 201, "Failed to create deactivated URL for test"
        # Soft delete (deactivate) the URL
        resp_patch = requests.patch(
            f"{BASE_URL}/api/urls/{custom_alias_deactivated}",
            json={"is_active": False},
            timeout=TIMEOUT
        )
        assert resp_patch.status_code == 200, "Failed to deactivate URL"

        resp_410 = requests.get(
            f"{BASE_URL}/{custom_alias_deactivated}",
            allow_redirects=False,
            timeout=TIMEOUT
        )
        assert resp_410.status_code == 410, f"Expected 410 Gone for deactivated code but got {resp_410.status_code}"

        # Step 5: Create an expired URL and expect 410 Gone
        past_date = (datetime.datetime.utcnow() - datetime.timedelta(days=5)).replace(microsecond=0).isoformat() + "Z"
        custom_alias_expired = f"expired-{int(datetime.datetime.utcnow().timestamp())}"
        create_payload_expired = {
            "original_url": "https://example.com/expired",
            "custom_alias": custom_alias_expired,
            "expires_at": past_date
        }
        resp_create_expired = requests.post(
            f"{BASE_URL}/api/urls",
            json=create_payload_expired,
            timeout=TIMEOUT
        )
        assert resp_create_expired.status_code == 201, "Failed to create expired URL for test"

        resp_410_expired = requests.get(
            f"{BASE_URL}/{custom_alias_expired}",
            allow_redirects=False,
            timeout=TIMEOUT
        )
        assert resp_410_expired.status_code == 410, f"Expected 410 Gone for expired code but got {resp_410_expired.status_code}"
    finally:
        # Cleanup created URLs
        if created_short_code:
            requests.delete(f"{BASE_URL}/api/urls/{created_short_code}", timeout=TIMEOUT)
        if 'custom_alias_deactivated' in locals():
            requests.delete(f"{BASE_URL}/api/urls/{custom_alias_deactivated}", timeout=TIMEOUT)
        if 'custom_alias_expired' in locals():
            requests.delete(f"{BASE_URL}/api/urls/{custom_alias_expired}", timeout=TIMEOUT)

test_get_short_code_redirect_to_original_url()
