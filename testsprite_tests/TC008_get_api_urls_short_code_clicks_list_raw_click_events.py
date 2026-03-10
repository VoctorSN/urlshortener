import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_get_api_urls_short_code_clicks_list_raw_click_events():
    # Step 1: Create a new shortened URL to ensure we have a valid short_code
    create_url = f"{BASE_URL}/api/urls"
    payload = {
        "original_url": "https://example.com/long-click-test"
    }
    short_code = None
    try:
        create_resp = requests.post(create_url, json=payload, timeout=TIMEOUT)
        assert create_resp.status_code == 201, f"Failed to create URL, got {create_resp.status_code}"
        create_data = create_resp.json()
        short_code = create_data.get("short_code")
        assert short_code, "short_code missing in creation response"

        # Step 2: Make a GET request to list raw click events with pagination parameters skip=0, limit=20
        clicks_url = f"{BASE_URL}/api/urls/{short_code}/clicks"
        params = {"skip": 0, "limit": 20}
        clicks_resp = requests.get(clicks_url, params=params, timeout=TIMEOUT)

        # Possible responses: 200 with array or 404 if URL not found
        if clicks_resp.status_code == 200:
            clicks_data = clicks_resp.json()
            assert isinstance(clicks_data, list), "Expected list for click events"
            # If there are click events, check keys in first item
            if clicks_data:
                first_click = clicks_data[0]
                required_keys = {
                    "id", "timestamp", "ip_address", "user_agent",
                    "browser", "operating_system", "referrer"
                }
                missing_keys = required_keys - first_click.keys()
                assert not missing_keys, f"Missing keys in click event response: {missing_keys}"
        elif clicks_resp.status_code == 404:
            # URL not found scenario - fail only if we believe short_code should exist
            assert False, f"Click events returned 404 for existing short_code {short_code}"
        else:
            assert False, f"Unexpected status code {clicks_resp.status_code} for clicks list"
    finally:
        # Cleanup - delete the created short_code
        if short_code:
            del_url = f"{BASE_URL}/api/urls/{short_code}"
            requests.delete(del_url, timeout=TIMEOUT)

test_get_api_urls_short_code_clicks_list_raw_click_events()