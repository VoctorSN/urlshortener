import requests
import datetime
import time

BASE_URL = "http://localhost:8000"
CREATE_URL_PATH = "/api/urls"
CLICK_EVENTS_PATH_TEMPLATE = "/api/urls/{short_code}/clicks"
DELETE_URL_PATH_TEMPLATE = "/api/urls/{short_code}"

def test_get_api_urls_short_code_clicks_list_raw_click_events():
    timeout = 30
    # Step 1: Create a new short URL to test clicks listing
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    future_expire = (utc_now + datetime.timedelta(days=10)).isoformat()
    create_payload = {
        "original_url": "https://example.com/test-click-events",
        "expires_at": future_expire
    }
    resp_create = requests.post(
        BASE_URL + CREATE_URL_PATH,
        json=create_payload,
        timeout=timeout
    )
    assert resp_create.status_code == 201, f"Failed to create URL, status: {resp_create.status_code}, body: {resp_create.text}"
    created_data = resp_create.json()
    assert "short_code" in created_data and isinstance(created_data["short_code"], str)
    short_code = created_data["short_code"]

    try:
        # Step 2: Call redirect endpoint multiple times to generate click events
        redirect_url = f"{BASE_URL}/{short_code}"
        headers = {
            "User-Agent": "pytest-agent/1.0",
            "Referer": "https://referrer.example.com",
            "X-Forwarded-For": "203.0.113.5"
        }
        n_clicks = 3
        for _ in range(n_clicks):
            r = requests.get(redirect_url, headers=headers, allow_redirects=False, timeout=timeout)
            assert r.status_code == 307, f"Redirect failed with status {r.status_code}"
            location = r.headers.get("Location")
            assert location == created_data["original_url"], f"Redirect location mismatch: {location}"
            time.sleep(0.1)  # slight delay to ensure distinct timestamps if recorded

        # Step 3: Test listing raw click events for this short_code with pagination
        clicks_url = f"{BASE_URL}{CLICK_EVENTS_PATH_TEMPLATE.format(short_code=short_code)}"
        params = {"skip": 0, "limit": 20}
        resp_clicks = requests.get(clicks_url, params=params, timeout=timeout)
        assert resp_clicks.status_code == 200, f"Expected 200 OK listing clicks, got {resp_clicks.status_code}"
        clicks_data = resp_clicks.json()
        assert isinstance(clicks_data, list), "Clicks response is not a list"

        # Validate fields in each click event
        allowed_keys = {"clicked_at", "ip_address", "user_agent", "browser", "os", "referrer", "country"}
        # Must have at least one click, since we triggered 3 clicks
        assert len(clicks_data) >= 1, "No click events returned, expected at least one"
        for click_event in clicks_data:
            assert isinstance(click_event, dict), "Click event is not a dictionary"
            keys = set(click_event.keys())
            # Check fields exactly match expected keys
            assert keys == allowed_keys, f"Click event keys mismatch: {keys}"
            # Validate clicked_at is ISO8601 with timezone suffix +00:00 (UTC)
            clicked_at = click_event.get("clicked_at")
            assert isinstance(clicked_at, str)
            try:
                dt_clicked_at = datetime.datetime.fromisoformat(clicked_at)
            except Exception:
                assert False, f"clicked_at is not valid ISO8601 datetime with tz: {clicked_at}"
            assert dt_clicked_at.tzinfo is not None, "clicked_at datetime is naive, expected timezone aware"

        # Step 4: Test pagination skip & limit parameters by requesting zero limit to get empty list
        resp_clicks_empty = requests.get(clicks_url, params={"skip": 0, "limit": 0}, timeout=timeout)
        assert resp_clicks_empty.status_code == 200
        assert isinstance(resp_clicks_empty.json(), list)
        # Limit=0 means no items (assuming API honors limit=0)
        assert len(resp_clicks_empty.json()) == 0

        # Step 5: Test 404 response for nonexistent short_code
        bad_code = "nonexistent-code-xyz"
        resp_404 = requests.get(f"{BASE_URL}/api/urls/{bad_code}/clicks", timeout=timeout)
        assert resp_404.status_code == 404, f"Expected 404 for nonexistent short_code, got {resp_404.status_code}"

    finally:
        # Clean up: delete the created short URL
        delete_url = f"{BASE_URL}{DELETE_URL_PATH_TEMPLATE.format(short_code=short_code)}"
        resp_delete = requests.delete(delete_url, timeout=timeout)
        assert resp_delete.status_code == 204, f"Failed to delete URL, status: {resp_delete.status_code}"

test_get_api_urls_short_code_clicks_list_raw_click_events()