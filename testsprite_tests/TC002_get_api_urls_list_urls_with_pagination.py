import requests
import datetime

BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_get_api_urls_list_urls_with_pagination():
    # Create a new shortened URL to ensure there's at least one URL in the list
    create_url = f"{BASE_URL}/api/urls"
    payload = {
        "original_url": "https://example.com/test-get-list",
    }
    created_short_code = None
    try:
        create_resp = requests.post(create_url, json=payload, timeout=TIMEOUT)
        assert create_resp.status_code == 201, f"Expected 201 Created, got {create_resp.status_code}"
        created_data = create_resp.json()
        created_short_code = created_data.get("short_code")
        # Validate response fields of the created URL
        assert isinstance(created_data.get("id"), int)
        assert created_data.get("original_url") == payload["original_url"]
        assert isinstance(created_data.get("short_code"), str) and created_data.get("short_code") != ""
        assert isinstance(created_data.get("short_url"), str) and created_data.get("short_url").startswith(BASE_URL)
        assert isinstance(created_data.get("is_active"), bool)
        assert isinstance(created_data.get("click_count"), int)
        # Validate created_at and updated_at are timezone aware ISO 8601 strings with +00:00
        created_at = created_data.get("created_at")
        updated_at = created_data.get("updated_at")
        expires_at = created_data.get("expires_at")
        # Parse ISO 8601 with possible fractional seconds and 'Z' timezone
        def parse_iso_datetime(dt_str):
            if dt_str is None:
                return None
            if dt_str.endswith('Z'):
                dt_str = dt_str[:-1] + '+00:00'
            return datetime.datetime.fromisoformat(dt_str)

        dt_created_at = parse_iso_datetime(created_at)
        dt_updated_at = parse_iso_datetime(updated_at)
        # Check datetime timezone aware UTC (+00:00)
        assert dt_created_at is not None and dt_created_at.tzinfo is not None and dt_created_at.utcoffset().total_seconds() == 0
        assert dt_updated_at is not None and dt_updated_at.tzinfo is not None and dt_updated_at.utcoffset().total_seconds() == 0
        # expires_at may be null
        if expires_at is not None:
            dt_expires_at = parse_iso_datetime(expires_at)
            assert dt_expires_at is not None and dt_expires_at.tzinfo is not None and dt_expires_at.utcoffset().total_seconds() == 0

        # Now test listing all URLs with pagination
        list_url = f"{BASE_URL}/api/urls"
        params = {"skip": 0, "limit": 10}
        resp = requests.get(list_url, params=params, timeout=TIMEOUT)
        assert resp.status_code == 200, f"Expected 200 OK, got {resp.status_code}"
        urls = resp.json()
        assert isinstance(urls, list), f"Expected list response, got {type(urls)}"
        # Validate each item in list corresponds to URLResponse schema
        for url_item in urls:
            assert isinstance(url_item.get("id"), int)
            assert isinstance(url_item.get("short_code"), str)
            assert isinstance(url_item.get("original_url"), str)
            assert isinstance(url_item.get("short_url"), str)
            assert isinstance(url_item.get("is_active"), bool)
            assert isinstance(url_item.get("click_count"), int)
            # Validate date times format and timezone aware
            created_at = url_item.get("created_at")
            updated_at = url_item.get("updated_at")
            expires_at = url_item.get("expires_at")
            dt_created_at = parse_iso_datetime(created_at)
            dt_updated_at = parse_iso_datetime(updated_at)
            assert dt_created_at is not None and dt_created_at.tzinfo is not None and dt_created_at.utcoffset().total_seconds() == 0
            assert dt_updated_at is not None and dt_updated_at.tzinfo is not None and dt_updated_at.utcoffset().total_seconds() == 0
            if expires_at is not None:
                dt_expires_at = parse_iso_datetime(expires_at)
                assert dt_expires_at is not None and dt_expires_at.tzinfo is not None and dt_expires_at.utcoffset().total_seconds() == 0
    finally:
        # Clean up by deleting the created URL if short_code is available
        if created_short_code:
            requests.delete(f"{BASE_URL}/api/urls/{created_short_code}", timeout=TIMEOUT)


test_get_api_urls_list_urls_with_pagination()
