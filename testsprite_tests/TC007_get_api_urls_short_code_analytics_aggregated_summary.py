import requests
import datetime
import time

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_get_api_urls_short_code_analytics_aggregated_summary():
    # Step 1: Create a new shortened URL to obtain a valid short_code
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    expires_at = (now_utc + datetime.timedelta(days=1)).isoformat()
    create_payload = {
        "original_url": "https://example.com/analytics-test",
        "expires_at": expires_at
    }
    created_short_code = None
    try:
        create_resp = requests.post(
            f"{BASE_URL}/api/urls",
            json=create_payload,
            timeout=TIMEOUT
        )
        assert create_resp.status_code == 201, f"Setup failed: Expected 201, got {create_resp.status_code}"
        create_data = create_resp.json()
        created_short_code = create_data["short_code"]

        # Step 2: Simulate at least one redirect to generate analytics data
        redirect_resp = requests.get(
            f"{BASE_URL}/{created_short_code}",
            allow_redirects=False,
            timeout=TIMEOUT,
            headers={"User-Agent": "TestAgent/1.0", "X-Forwarded-For": "127.0.0.1"}
        )
        assert redirect_resp.status_code == 307, f"Redirect failed: Expected 307, got {redirect_resp.status_code}"
        location_header = redirect_resp.headers.get("Location")
        assert location_header == create_data["original_url"], "Redirect Location header does not match original_url"

        # Step 3: Wait a short moment to ensure click event recorded
        time.sleep(1)

        # Step 4: GET analytics summary without date filters
        analytics_resp = requests.get(
            f"{BASE_URL}/api/urls/{created_short_code}/analytics",
            timeout=TIMEOUT
        )
        assert analytics_resp.status_code == 200, f"Analytics fetch failed: Expected 200, got {analytics_resp.status_code}"
        analytics_data = analytics_resp.json()
        # Validate expected fields and types
        assert analytics_data["short_code"] == created_short_code
        assert isinstance(analytics_data["total_clicks"], int) and analytics_data["total_clicks"] >= 1
        assert isinstance(analytics_data["unique_visitors"], int) and analytics_data["unique_visitors"] >= 1
        for field in ["browsers", "operating_systems", "referrers", "clicks_by_date"]:
            assert field in analytics_data and isinstance(analytics_data[field], dict)

        # Step 5: GET analytics summary with valid start_date and end_date filters
        start_date = (now_utc - datetime.timedelta(days=1)).date().isoformat()
        end_date = (now_utc + datetime.timedelta(days=1)).date().isoformat()
        filtered_resp = requests.get(
            f"{BASE_URL}/api/urls/{created_short_code}/analytics",
            params={"start_date": start_date, "end_date": end_date},
            timeout=TIMEOUT
        )
        assert filtered_resp.status_code == 200, f"Filtered analytics fetch failed: Expected 200, got {filtered_resp.status_code}"
        filtered_data = filtered_resp.json()
        assert filtered_data["short_code"] == created_short_code
        assert isinstance(filtered_data["total_clicks"], int)
        assert isinstance(filtered_data["unique_visitors"], int)

        # Step 6: GET analytics summary for a nonexistent short_code to verify 404
        nonexistent_resp = requests.get(
            f"{BASE_URL}/api/urls/nonexistentcode123/analytics",
            timeout=TIMEOUT
        )
        assert nonexistent_resp.status_code == 404, f"Expected 404 for nonexistent code, got {nonexistent_resp.status_code}"

    finally:
        # Cleanup: Delete the created short_code to not pollute DB
        if created_short_code:
            requests.delete(f"{BASE_URL}/api/urls/{created_short_code}", timeout=TIMEOUT)


if __name__ == "__main__":
    test_get_api_urls_short_code_analytics_aggregated_summary()
