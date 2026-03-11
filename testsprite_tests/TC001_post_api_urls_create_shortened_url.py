import requests
import datetime
import string
import random

BASE_URL = "http://localhost:8000"
API_PATH = "/api/urls"
TIMEOUT = 30


def test_create_shortened_url():
    # Generate a random valid custom_alias for uniqueness in test
    def random_alias(length=8):
        chars = string.ascii_letters + string.digits + "-_"
        return ''.join(random.choice(chars) for _ in range(length))

    custom_alias = random_alias()
    original_url = "https://example.com/long/path"
    expires_at = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)).isoformat()

    payload = {
        "original_url": original_url,
        "custom_alias": custom_alias,
        "expires_at": expires_at
    }

    try:
        # POST to create shortened URL
        response = requests.post(
            BASE_URL + API_PATH,
            json=payload,
            timeout=TIMEOUT
        )
        assert response.status_code == 201, f"Expected 201 Created, got {response.status_code}"
        data = response.json()

        # Validate response fields
        # Required fields: id (int), short_code (str), original_url (str), short_url (str), is_active (bool), click_count (int), created_at (str), updated_at (str), expires_at (str or null)
        assert isinstance(data.get("id"), int), "id must be int"
        assert data.get("short_code") == custom_alias, "short_code must match custom_alias"
        assert data.get("original_url") == original_url, "original_url mismatch"
        assert isinstance(data.get("short_url"), str) and data["short_url"].endswith(custom_alias), "short_url must end with custom_alias"
        assert data.get("is_active") is True, "is_active must be True"
        assert isinstance(data.get("click_count"), int) and data["click_count"] == 0, "click_count must be int zero"
        created_at = datetime.datetime.fromisoformat(data.get("created_at"))
        updated_at = datetime.datetime.fromisoformat(data.get("updated_at"))
        expires_at_resp = data.get("expires_at")
        assert expires_at_resp is not None, "expires_at must be present"
        expires_at_dt = datetime.datetime.fromisoformat(expires_at_resp)

        # Validate that created_at, updated_at, expires_at are timezone-aware UTC datetimes
        for dt_field, dt_val in [("created_at", created_at), ("updated_at", updated_at), ("expires_at", expires_at_dt)]:
            assert dt_val.tzinfo is not None and dt_val.utcoffset().total_seconds() == 0, f"{dt_field} must be timezone-aware UTC"

    finally:
        # Clean up: delete the created resource by custom_alias
        delete_resp = requests.delete(
            f"{BASE_URL}{API_PATH}/{custom_alias}",
            timeout=TIMEOUT
        )
        # Accept 204 No Content or 404 Not Found if resource already deleted or missing
        assert delete_resp.status_code in (204, 404), f"Cleanup failed: Expected 204 or 404, got {delete_resp.status_code}"


test_create_shortened_url()