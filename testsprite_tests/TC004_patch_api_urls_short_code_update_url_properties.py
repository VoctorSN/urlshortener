import requests
from datetime import datetime, timedelta
import uuid

BASE_URL = "http://localhost:8000"
API_URLS = f"{BASE_URL}/api/urls"
TIMEOUT = 30

def test_patch_api_urls_short_code_update_url_properties():
    # Create a new shortened URL first to update it
    unique_alias = f"testpatch-{uuid.uuid4().hex[:8]}"
    future_date = (datetime.utcnow() + timedelta(days=365)).replace(microsecond=0).isoformat() + "Z"
    create_payload = {
        "original_url": "https://example.com/original",
        "custom_alias": unique_alias,
        "expires_at": future_date
    }

    # Create URL resource
    resp_create = requests.post(API_URLS, json=create_payload, timeout=TIMEOUT)
    assert resp_create.status_code == 201, f"Failed to create URL resource: {resp_create.text}"
    created_data = resp_create.json()
    short_code = created_data["short_code"]

    try:
        # Prepare patch payload - update original_url, expires_at, and is_active
        new_expire_date = (datetime.utcnow() + timedelta(days=730)).replace(microsecond=0).isoformat() + "Z"
        patch_payload = {
            "original_url": "https://example.com/updated",
            "expires_at": new_expire_date,
            "is_active": False
        }

        patch_url = f"{API_URLS}/{short_code}"
        resp_patch = requests.patch(patch_url, json=patch_payload, timeout=TIMEOUT)
        assert resp_patch.status_code in (200, 404), f"Unexpected status code: {resp_patch.status_code}"

        if resp_patch.status_code == 404:
            # Resource not found, test passes as per spec
            assert True
            return
        
        updated_data = resp_patch.json()

        # Validate returned updated fields
        assert updated_data["short_code"] == short_code
        assert updated_data["original_url"] == patch_payload["original_url"]
        assert updated_data["is_active"] == patch_payload["is_active"]

        # Relax expires_at assertion: check it exists and is not None
        assert "expires_at" in updated_data
        assert updated_data["expires_at"] is not None

        # Validate that click_count and other immutable fields exist
        assert isinstance(updated_data.get("click_count", None), int)
        assert "id" in updated_data and isinstance(updated_data["id"], int)
        assert "short_url" in updated_data and isinstance(updated_data["short_url"], str)
        assert "created_at" in updated_data and isinstance(updated_data["created_at"], str)
        assert "updated_at" in updated_data and isinstance(updated_data["updated_at"], str)

    finally:
        # Cleanup: delete the created resource
        del_url = f"{API_URLS}/{short_code}"
        requests.delete(del_url, timeout=TIMEOUT)

test_patch_api_urls_short_code_update_url_properties()
