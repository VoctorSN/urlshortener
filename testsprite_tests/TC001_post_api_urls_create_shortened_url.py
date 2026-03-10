import requests
from datetime import datetime, timedelta
import uuid

BASE_URL = "http://localhost:8000"

def test_post_api_urls_create_shortened_url():
    url = f"{BASE_URL}/api/urls"
    headers = {"Content-Type": "application/json"}

    # Prepare data with required and optional fields
    original_url = "https://example.com/" + str(uuid.uuid4())
    custom_alias = "customalias" + str(uuid.uuid4()).replace("-", "")[:8]
    expires_at = (datetime.utcnow() + timedelta(days=7)).replace(microsecond=0).isoformat() + "Z"

    payload = {
        "original_url": original_url,
        "custom_alias": custom_alias,
        "expires_at": expires_at
    }

    response = None
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        assert response.status_code == 201, f"Expected 201 but got {response.status_code}. Response: {response.text}"

        resp_json = response.json()
        # Validate response fields
        assert isinstance(resp_json.get("id"), int), "Missing or invalid 'id'"
        short_code = resp_json.get("short_code")
        short_url = resp_json.get("short_url")
        assert short_code == custom_alias, f"Expected short_code to be the custom_alias '{custom_alias}', got '{short_code}'"
        assert short_url.endswith(f"/{short_code}"), f"short_url '{short_url}' does not end with '/{short_code}'"
        assert resp_json.get("original_url") == original_url, "original_url mismatch"
        assert resp_json.get("is_active") is True, "is_active should be True"
        assert isinstance(resp_json.get("click_count"), int), "click_count should be integer"
        assert isinstance(resp_json.get("created_at"), str), "created_at should be string"
        assert isinstance(resp_json.get("updated_at"), str), "updated_at should be string"
        assert resp_json.get("expires_at") == expires_at, "expires_at mismatch or missing"

    finally:
        # Clean up: delete the created resource if creation succeeded
        if response is not None and response.status_code == 201:
            try:
                del_resp = requests.delete(f"{BASE_URL}/api/urls/{custom_alias}", timeout=30)
                # Expected 204 No Content or 404 if already deleted
                assert del_resp.status_code in (204, 404), f"Unexpected delete status code {del_resp.status_code}"
            except Exception:
                pass

test_post_api_urls_create_shortened_url()