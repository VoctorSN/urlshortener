import requests
import uuid

BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_get_api_urls_list_urls_with_pagination():
    created_short_code = None
    # Create a URL resource first to ensure at least one URL exists in the list
    url_create_endpoint = f"{BASE_URL}/api/urls"
    create_payload = {
        "original_url": "https://example.com/test-list-" + str(uuid.uuid4()),
    }
    try:
        create_resp = requests.post(url_create_endpoint, json=create_payload, timeout=TIMEOUT)
        assert create_resp.status_code == 201, f"Expected 201 Created, got {create_resp.status_code}"
        create_data = create_resp.json()
        created_short_code = create_data.get("short_code")
        assert isinstance(created_short_code, str) and created_short_code != ""

        # Now test listing URLs with pagination parameters
        url_list_endpoint = f"{BASE_URL}/api/urls"
        params = {
            "skip": 0,
            "limit": 20
        }
        list_resp = requests.get(url_list_endpoint, params=params, timeout=TIMEOUT)
        assert list_resp.status_code == 200, f"Expected 200 OK, got {list_resp.status_code}"
        list_data = list_resp.json()
        assert isinstance(list_data, list), "Response is not a list"

        # Validate each item in the list to be URLResponse schema like
        for item in list_data:
            assert isinstance(item, dict), "List item is not a dict"
            # Required keys in URLResponse response schema based on PRD:
            expected_keys = {
                "id", "short_code", "original_url", "short_url",
                "is_active", "click_count", "created_at", "updated_at", "expires_at"
            }
            assert expected_keys.issubset(item.keys()), f"Item missing keys, got keys: {item.keys()}"
            # Basic validations of types:
            assert isinstance(item["id"], int), "id is not integer"
            assert isinstance(item["short_code"], str), "short_code is not str"
            assert isinstance(item["original_url"], str), "original_url is not str"
            assert isinstance(item["short_url"], str), "short_url is not str"
            assert isinstance(item["is_active"], bool), "is_active is not bool"
            assert isinstance(item["click_count"], int), "click_count is not int"
            assert isinstance(item["created_at"], str), "created_at is not str"
            assert isinstance(item["updated_at"], str), "updated_at is not str"
            # expires_at may be None or str
            assert item["expires_at"] is None or isinstance(item["expires_at"], str), "expires_at invalid type"
    finally:
        # Cleanup: delete the created URL if it exists
        if created_short_code:
            delete_endpoint = f"{BASE_URL}/api/urls/{created_short_code}"
            try:
                del_resp = requests.delete(delete_endpoint, timeout=TIMEOUT)
                # Accept 204 or 404 (if already deleted)
                assert del_resp.status_code in [204, 404], f"Unexpected delete status {del_resp.status_code}"
            except Exception:
                pass


test_get_api_urls_list_urls_with_pagination()