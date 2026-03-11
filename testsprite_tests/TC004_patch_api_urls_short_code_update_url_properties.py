import requests
import datetime
import time

BASE_URL = "http://localhost:8000"
API_URLS = f"{BASE_URL}/api/urls"
TIMEOUT = 30


def test_patch_api_urls_update_url_properties():
    # Prepare headers for JSON content
    headers = {"Content-Type": "application/json"}

    # Create a new shortened URL resource to update
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    expires_future = (now_utc + datetime.timedelta(days=7)).isoformat()
    create_payload = {
        "original_url": "https://example.com/original",
        "expires_at": expires_future
    }
    create_resp = requests.post(API_URLS, json=create_payload, headers=headers, timeout=TIMEOUT)
    assert create_resp.status_code == 201, f"Create URL failed: {create_resp.text}"
    created_url = create_resp.json()
    short_code = created_url["short_code"]

    try:
        # Define new values to patch: new original_url, new expires_at and is_active
        expires_past = (now_utc - datetime.timedelta(days=1)).isoformat()
        patch_payload = {
            "original_url": "https://example.com/updated",
            "expires_at": expires_past,
            "is_active": False
        }

        patch_resp = requests.patch(f"{API_URLS}/{short_code}", json=patch_payload, headers=headers, timeout=TIMEOUT)
        assert patch_resp.status_code == 200, f"Patch failed: {patch_resp.text}"
        patched_url = patch_resp.json()

        # Validate updated fields
        assert patched_url["short_code"] == short_code
        assert patched_url["original_url"] == patch_payload["original_url"]
        # expires_at may be string or null, ensure it's equals and timezone aware
        patched_expires_at = patched_url.get("expires_at")
        assert patched_expires_at is not None
        dt_expires = datetime.datetime.fromisoformat(patched_expires_at)
        expected_expires = datetime.datetime.fromisoformat(patch_payload["expires_at"])
        assert dt_expires == expected_expires
        # Validate is_active field is updated to False
        assert patched_url["is_active"] is False

        # Also test updating only original_url to a new valid URL, with no expires_at and is_active fields
        patch_resp2 = requests.patch(f"{API_URLS}/{short_code}", json={"original_url": "https://example.com/partial-update"}, headers=headers, timeout=TIMEOUT)
        assert patch_resp2.status_code == 200, f"Patch partial update failed: {patch_resp2.text}"
        patched_url2 = patch_resp2.json()
        assert patched_url2["original_url"] == "https://example.com/partial-update"

        # Test 404 on patch for non-existent short_code
        non_existent_sc = "nonexistentcode12345"
        patch_resp_404 = requests.patch(f"{API_URLS}/{non_existent_sc}", json={"original_url": "https://x.com"}, headers=headers, timeout=TIMEOUT)
        assert patch_resp_404.status_code == 404

    finally:
        # Clean up: delete the created short_code to avoid residue after test
        requests.delete(f"{API_URLS}/{short_code}", timeout=TIMEOUT)


test_patch_api_urls_update_url_properties()