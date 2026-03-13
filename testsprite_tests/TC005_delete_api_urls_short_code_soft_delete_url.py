import requests
from datetime import datetime, timezone
import uuid

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_delete_api_urls_short_code_soft_delete_url():
    headers = {"Content-Type": "application/json"}
    short_code = None

    # Create a new shortened URL to delete
    create_payload = {
        "original_url": "https://example.com/" + str(uuid.uuid4())
    }

    try:
        create_resp = requests.post(
            f"{BASE_URL}/api/urls",
            json=create_payload,
            headers=headers,
            timeout=TIMEOUT
        )
        assert create_resp.status_code == 201, f"Expected 201 Created, got {create_resp.status_code}"
        create_data = create_resp.json()
        short_code = create_data.get("short_code")
        assert isinstance(short_code, str) and len(short_code) > 0, "short_code invalid in create response"

        # Delete (soft-delete) the URL by short_code
        delete_resp = requests.delete(
            f"{BASE_URL}/api/urls/{short_code}",
            headers=headers,
            timeout=TIMEOUT
        )
        assert delete_resp.status_code == 204, f"Expected 204 No Content, got {delete_resp.status_code}"

        # Verify that the URL is soft deleted by fetching metadata and checking is_active = false
        get_resp = requests.get(
            f"{BASE_URL}/api/urls/{short_code}",
            headers=headers,
            timeout=TIMEOUT
        )
        if get_resp.status_code == 200:
            get_data = get_resp.json()
            assert get_data.get("is_active") is False, "URL is_active should be False after soft-delete"
        else:
            assert False, f"Expected 200 on GET after delete, got {get_resp.status_code}"

        # Try deleting a non-existent short_code and expect 404
        non_existent_code = "nonexistent-" + str(uuid.uuid4())
        delete_nonexistent_resp = requests.delete(
            f"{BASE_URL}/api/urls/{non_existent_code}",
            headers=headers,
            timeout=TIMEOUT
        )
        assert delete_nonexistent_resp.status_code == 404, f"Expected 404 Not Found for non-existent short_code delete, got {delete_nonexistent_resp.status_code}"

    finally:
        # Cleanup: Ensure URL is deleted/inactive by soft-deletion if still exists
        if short_code is not None:
            try:
                _ = requests.delete(
                    f"{BASE_URL}/api/urls/{short_code}",
                    headers=headers,
                    timeout=TIMEOUT
                )
            except Exception:
                pass


if __name__ == "__main__":
    test_delete_api_urls_short_code_soft_delete_url()
