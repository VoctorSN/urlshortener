import requests
import uuid
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_get_api_urls_short_code_retrieve_url_metadata():
    # Create a new shortened URL to use its short_code for retrieval test
    create_url = f"{BASE_URL}/api/urls"
    unique_alias = f"testalias-{uuid.uuid4().hex[:8]}"
    future_date = (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z"
    payload = {
        "original_url": "https://example.com/test-get-metadata",
        "custom_alias": unique_alias,
        "expires_at": future_date,
    }
    created_short_code = None

    try:
        # Create URL
        create_resp = requests.post(create_url, json=payload, timeout=TIMEOUT)
        assert create_resp.status_code == 201, f"Expected 201 Created, got {create_resp.status_code}"
        create_data = create_resp.json()
        created_short_code = create_data.get("short_code")
        assert created_short_code == unique_alias

        # Retrieve metadata by short_code - expected 200
        get_url = f"{BASE_URL}/api/urls/{created_short_code}"
        get_resp = requests.get(get_url, timeout=TIMEOUT)
        assert get_resp.status_code == 200, f"Expected 200 OK, got {get_resp.status_code}"
        get_data = get_resp.json()
        
        # Validate essential URLResponse fields and values
        assert get_data["short_code"] == created_short_code
        assert get_data["original_url"] == payload["original_url"]
        assert isinstance(get_data["is_active"], bool)
        assert isinstance(get_data["click_count"], int)
        assert "created_at" in get_data and isinstance(get_data["created_at"], str)
        assert "updated_at" in get_data and isinstance(get_data["updated_at"], str)

        # Instead of strict string equality, parse ISO strings and compare
        from datetime import datetime as dt
        def parse_iso8601(date_str):
            if date_str.endswith('Z'):
                date_str = date_str[:-1]
            try:
                return dt.fromisoformat(date_str)
            except Exception:
                assert False, f"Invalid ISO datetime format: {date_str}"

        expected_dt = parse_iso8601(future_date)
        returned_dt = parse_iso8601(get_data["expires_at"])
        assert expected_dt == returned_dt, f"Expected expires_at {expected_dt}, got {returned_dt}"

        # Retrieve metadata for a non-existent short_code - expected 404
        nonexistent_code = "nonexistentcode12345"
        get_resp_404 = requests.get(f"{BASE_URL}/api/urls/{nonexistent_code}", timeout=TIMEOUT)
        assert get_resp_404.status_code == 404, f"Expected 404 Not Found, got {get_resp_404.status_code}"

    finally:
        # Clean up: soft-delete the created URL
        if created_short_code:
            delete_url = f"{BASE_URL}/api/urls/{created_short_code}"
            requests.delete(delete_url, timeout=TIMEOUT)

test_get_api_urls_short_code_retrieve_url_metadata()
