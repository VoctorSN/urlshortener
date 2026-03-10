import requests
from datetime import datetime, timezone, timedelta

BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_get_api_urls_short_code_analytics_aggregated_summary():
    # Step 1: Create a new shortened URL to get a valid short_code for testing
    create_url = f"{BASE_URL}/api/urls"
    original_url = "https://example.com/test-get-analytics"
    create_payload = {
        "original_url": original_url
    }
    short_code = None
    try:
        create_resp = requests.post(create_url, json=create_payload, timeout=TIMEOUT)
        assert create_resp.status_code == 201, f"Expected 201 Created but got {create_resp.status_code}"
        create_json = create_resp.json()
        short_code = create_json.get("short_code")
        assert short_code, "Response missing 'short_code'"

        # Step 2: Call analytics endpoint without filters
        analytics_url = f"{BASE_URL}/api/urls/{short_code}/analytics"
        resp_no_filters = requests.get(analytics_url, timeout=TIMEOUT)
        assert resp_no_filters.status_code == 200, f"Expected 200 OK but got {resp_no_filters.status_code}"
        data = resp_no_filters.json()
        # Validate keys presence in analytics summary
        expected_keys = {
            "short_code",
            "total_clicks",
            "unique_visitors",
            "browsers",
            "operating_systems",
            "referrers",
            "clicks_by_date",
        }
        assert expected_keys.issubset(data.keys()), f"Missing keys in analytics response: {expected_keys - data.keys()}"
        assert data["short_code"] == short_code, "Analytics short_code mismatch"
        assert isinstance(data["total_clicks"], int), "total_clicks is not int"
        assert isinstance(data["unique_visitors"], int), "unique_visitors is not int"
        assert isinstance(data["browsers"], dict), "browsers is not dict"
        assert isinstance(data["operating_systems"], dict), "operating_systems is not dict"
        assert isinstance(data["referrers"], dict), "referrers is not dict"
        assert isinstance(data["clicks_by_date"], dict), "clicks_by_date is not dict"

        # Step 3: Call analytics endpoint with valid start_date and end_date filters
        # Use valid ISO 8601 date strings: start_date = 7 days ago, end_date = today
        today = datetime.now(timezone.utc).date()
        seven_days_ago = today - timedelta(days=7)
        params = {
            "start_date": seven_days_ago.isoformat(),
            "end_date": today.isoformat(),
        }
        resp_with_filters = requests.get(analytics_url, params=params, timeout=TIMEOUT)
        assert resp_with_filters.status_code == 200, f"Expected 200 OK with date filters but got {resp_with_filters.status_code}"
        data_filt = resp_with_filters.json()
        assert expected_keys.issubset(data_filt.keys()), "Filtered analytics missing expected keys"
        assert data_filt["short_code"] == short_code

        # Step 4: Call analytics endpoint on a nonexistent short_code expecting 404
        nonexistent_code = "nonexistentcode123"
        resp_404 = requests.get(f"{BASE_URL}/api/urls/{nonexistent_code}/analytics", timeout=TIMEOUT)
        assert resp_404.status_code == 404, f"Expected 404 Not Found but got {resp_404.status_code}"

    finally:
        # Clean up: delete the created short_code if it was created
        if short_code:
            delete_url = f"{BASE_URL}/api/urls/{short_code}"
            del_resp = requests.delete(delete_url, timeout=TIMEOUT)
            assert del_resp.status_code in (204, 404), f"Cleanup delete expected 204 or 404 but got {del_resp.status_code}"


test_get_api_urls_short_code_analytics_aggregated_summary()