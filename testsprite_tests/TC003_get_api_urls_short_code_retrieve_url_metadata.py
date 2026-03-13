import requests
import datetime
import uuid

BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_get_api_urls_shortcode_retrieve_url_metadata():
    # Helper to create a new URL resource
    def create_url(original_url=None, custom_alias=None, expires_at=None):
        payload = {"original_url": original_url or "https://example.com/" + str(uuid.uuid4())}
        if custom_alias:
            payload["custom_alias"] = custom_alias
        if expires_at:
            payload["expires_at"] = expires_at
        response = requests.post(f"{BASE_URL}/api/urls", json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()

    # Helper to delete a URL resource by short_code
    def delete_url(short_code):
        resp = requests.delete(f"{BASE_URL}/api/urls/{short_code}", timeout=TIMEOUT)
        # We accept 204 or 404 on delete
        assert resp.status_code in (204, 404)

    # Step 1: Create a new URL resource for testing retrieval
    created = None
    try:
        created = create_url()
        short_code = created["short_code"]

        # Step 2: Retrieve metadata for existing short_code, expect 200 with proper URLResponse structure
        resp_get = requests.get(f"{BASE_URL}/api/urls/{short_code}", timeout=TIMEOUT)
        assert resp_get.status_code == 200
        data = resp_get.json()
        # Validate keys and data types in response
        expected_keys = {"id", "short_code", "original_url", "short_url", "is_active", "click_count", "created_at", "updated_at", "expires_at"}
        assert expected_keys.issubset(data.keys())
        assert data["short_code"] == short_code
        assert isinstance(data["id"], int)
        assert isinstance(data["original_url"], str)
        assert isinstance(data["short_url"], str)
        assert isinstance(data["is_active"], bool)
        assert isinstance(data["click_count"], int)

        # Validate "created_at" and "updated_at" are timezone-aware ISO8601 strings ending with +00:00
        for dt_field in ["created_at", "updated_at"]:
            dt_val = data[dt_field]
            assert isinstance(dt_val, str)
            # Parse with fromisoformat and check tzinfo is timezone.utc
            dt_parsed = datetime.datetime.fromisoformat(dt_val)
            assert dt_parsed.tzinfo is not None and dt_parsed.tzinfo.utcoffset(dt_parsed).total_seconds() == 0

        # expires_at can be None or valid ISO8601 string with UTC tz
        if data["expires_at"] is not None:
            dt_exp = data["expires_at"]
            assert isinstance(dt_exp, str)
            dt_exp_parsed = datetime.datetime.fromisoformat(dt_exp)
            assert dt_exp_parsed.tzinfo is not None and dt_exp_parsed.tzinfo.utcoffset(dt_exp_parsed).total_seconds() == 0

        # Step 3: Attempt to retrieve metadata for a nonexistent short_code, expect 404
        fake_short_code = f"notfound-{uuid.uuid4().hex[:8]}"
        resp_404 = requests.get(f"{BASE_URL}/api/urls/{fake_short_code}", timeout=TIMEOUT)
        assert resp_404.status_code == 404

    finally:
        # Clean up created URL resource if exists
        if created:
            delete_url(created["short_code"])



if __name__ == "__main__":
    test_get_api_urls_shortcode_retrieve_url_metadata()
