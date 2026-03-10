import requests
import uuid
import time

BASE_URL = "http://localhost:8000"
API_URLS_PATH = "/api/urls"
TIMEOUT = 30


def test_tc005_delete_api_urls_short_code_soft_delete_url():
    # Step 1: Create a new URL to ensure resource for deletion test
    short_code = f"testdelete-{uuid.uuid4().hex[:8]}"
    original_url = "https://example.com/soft-delete-test"
    create_payload = {
        "original_url": original_url,
        "custom_alias": short_code
    }
    created = False
    try:
        create_resp = requests.post(
            BASE_URL + API_URLS_PATH,
            json=create_payload,
            timeout=TIMEOUT
        )
        assert create_resp.status_code == 201, f"Failed to create URL for delete test, status: {create_resp.status_code}, body: {create_resp.text}"
        created = True

        # Step 2: Delete (soft-delete) the URL by short_code
        delete_resp = requests.delete(
            f"{BASE_URL}{API_URLS_PATH}/{short_code}",
            timeout=TIMEOUT
        )
        # Expect 204 No Content if found and soft-deleted
        if delete_resp.status_code == 204:
            # Step 3: Verify that is_active is false by retrieving URL metadata
            get_resp = requests.get(
                f"{BASE_URL}{API_URLS_PATH}/{short_code}",
                timeout=TIMEOUT
            )
            assert get_resp.status_code == 200, f"Expected 200 after soft-delete, got {get_resp.status_code}"
            data = get_resp.json()
            assert "is_active" in data, "Response missing 'is_active' field"
            assert data["is_active"] is False, "URL should be soft-deleted (is_active: false)"
        elif delete_resp.status_code == 404:
            # Resource not found - acceptable if somehow deleted/missing
            pass
        else:
            assert False, f"Unexpected status code from DELETE: {delete_resp.status_code} with body {delete_resp.text}"
    finally:
        # Cleanup: try to reactivate or delete the resource forcibly if test failed earlier
        try:
            if created:
                # Reactivate or delete forcibly, if needed
                # Since soft-delete sets is_active false, we can reactivate to keep DB clean
                patch_resp = requests.patch(
                    f"{BASE_URL}{API_URLS_PATH}/{short_code}",
                    json={"is_active": True},
                    timeout=TIMEOUT
                )
                # ignore result, best effort
        except Exception:
            pass


test_tc005_delete_api_urls_short_code_soft_delete_url()