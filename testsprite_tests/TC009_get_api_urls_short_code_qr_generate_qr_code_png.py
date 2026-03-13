import requests
import datetime
import io

BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_generate_qr_code_png():
    headers = {"Content-Type": "application/json"}
    # Step 1: Create a new shortened URL to get a valid short_code
    post_url = f"{BASE_URL}/api/urls"
    original_url = "https://example.com/qr-code-test"
    post_data = {"original_url": original_url}

    response = requests.post(post_url, json=post_data, headers=headers, timeout=TIMEOUT)
    assert response.status_code == 201, f"Failed to create short URL: {response.text}"
    resp_json = response.json()
    short_code = resp_json["short_code"]

    try:
        qr_base_url = f"{BASE_URL}/api/urls/{short_code}/qr"

        # Test default size (no size param, should default to 10)
        resp_default = requests.get(qr_base_url, timeout=TIMEOUT)
        assert resp_default.status_code == 200, f"QR code PNG request failed: {resp_default.text}"
        assert resp_default.headers.get("Content-Type") == "image/png", "Content-Type is not image/png"
        # Validate PNG magic bytes
        png_magic_bytes = b"\x89PNG\r\n\x1a\n"
        assert resp_default.content.startswith(png_magic_bytes), "Response is not a valid PNG file"

        # Test valid size parameter within range (e.g., size=20)
        params = {"size": 20}
        resp_size = requests.get(qr_base_url, params=params, timeout=TIMEOUT)
        assert resp_size.status_code == 200, f"QR code PNG with size=20 failed: {resp_size.text}"
        assert resp_size.headers.get("Content-Type") == "image/png", "Content-Type is not image/png for size=20"
        assert resp_size.content.startswith(png_magic_bytes), "Response with size=20 is not a valid PNG file"

        # Test edge size values 1 and 40
        for size_edge in [1, 40]:
            resp_edge = requests.get(qr_base_url, params={"size": size_edge}, timeout=TIMEOUT)
            assert resp_edge.status_code == 200, f"QR code PNG with size={size_edge} failed: {resp_edge.text}"
            assert resp_edge.headers.get("Content-Type") == "image/png", f"Content-Type is not image/png for size={size_edge}"
            assert resp_edge.content.startswith(png_magic_bytes), f"Response with size={size_edge} is not a valid PNG file"

        # Test size parameter out of valid range (e.g., 0 and 41)
        for invalid_size in [0, 41, 100]:
            resp_invalid = requests.get(qr_base_url, params={"size": invalid_size}, timeout=TIMEOUT)
            # Per FastAPI Query validation, invalid parameter values return 422 Unprocessable Entity
            assert resp_invalid.status_code == 422, f"Expected 422 for invalid size={invalid_size}, got {resp_invalid.status_code}"

        # Test 404 for nonexistent short_code
        nonexist_qr_url = f"{BASE_URL}/api/urls/nonexistentcode12345/qr"
        resp_404 = requests.get(nonexist_qr_url, timeout=TIMEOUT)
        assert resp_404.status_code == 404, f"Expected 404 for nonexistent short_code QR request, got {resp_404.status_code}"

    finally:
        # Cleanup: delete created short_code
        del_url = f"{BASE_URL}/api/urls/{short_code}"
        del_resp = requests.delete(del_url, timeout=TIMEOUT)
        # 204 expected on successful delete, or 404 if already deleted
        assert del_resp.status_code in (204, 404), f"Failed to delete short_code {short_code}: {del_resp.status_code}"



if __name__ == "__main__":
    test_generate_qr_code_png()
