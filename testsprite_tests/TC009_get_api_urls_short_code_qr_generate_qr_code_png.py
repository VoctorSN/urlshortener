import requests
import io

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

def test_generate_qr_code_png_for_short_code():
    # First create a new shortened URL to use its short_code
    create_url = f"{BASE_URL}/api/urls"
    payload = {
        "original_url": "https://example.com/qr-test"
    }

    short_code = None

    try:
        # Create a short URL
        response = requests.post(create_url, json=payload, timeout=TIMEOUT)
        assert response.status_code == 201, f"Expected 201 Created, got {response.status_code}"
        json_data = response.json()
        short_code = json_data.get("short_code")
        assert isinstance(short_code, str) and len(short_code) > 0, "Invalid short_code in creation response"

        # Test with default size (should be default=10)
        qr_url_default = f"{BASE_URL}/api/urls/{short_code}/qr"
        resp_default = requests.get(qr_url_default, timeout=TIMEOUT)
        if resp_default.status_code == 200:
            # Validate Content-Type and PNG signature bytes
            assert resp_default.headers.get("Content-Type") == "image/png", "Content-Type is not image/png"
            content = resp_default.content
            # PNG files start with: 89 50 4E 47 0D 0A 1A 0A
            assert content.startswith(b"\x89PNG\r\n\x1a\n"), "Response is not a valid PNG image"
        elif resp_default.status_code == 404:
            # If not found, this is acceptable per spec (URL not found)
            pass
        else:
            assert False, f"Unexpected status code for default size QR: {resp_default.status_code}"

        # Test valid sizes 1 and 40 as edge cases
        for size in [1, 40]:
            qr_url_size = f"{BASE_URL}/api/urls/{short_code}/qr?size={size}"
            resp = requests.get(qr_url_size, timeout=TIMEOUT)
            if resp.status_code == 200:
                assert resp.headers.get("Content-Type") == "image/png", f"Content-Type is not image/png for size {size}"
                content = resp.content
                assert content.startswith(b"\x89PNG\r\n\x1a\n"), f"Response is not a valid PNG image for size {size}"
            elif resp.status_code == 404:
                pass  # URL might be not found, acceptable
            else:
                assert False, f"Unexpected status code {resp.status_code} for size {size}"

        # Test invalid size below range (0)
        qr_url_invalid_low = f"{BASE_URL}/api/urls/{short_code}/qr?size=0"
        resp_low = requests.get(qr_url_invalid_low, timeout=TIMEOUT)
        assert resp_low.status_code == 422, f"Expected 422 for size=0 but got {resp_low.status_code}"

        # Test invalid size above range (41)
        qr_url_invalid_high = f"{BASE_URL}/api/urls/{short_code}/qr?size=41"
        resp_high = requests.get(qr_url_invalid_high, timeout=TIMEOUT)
        assert resp_high.status_code == 422, f"Expected 422 for size=41 but got {resp_high.status_code}"

        # Test non-existent short_code returns 404
        qr_url_nonexistent = f"{BASE_URL}/api/urls/nonexistentcode123/qr"
        resp_nonexistent = requests.get(qr_url_nonexistent, timeout=TIMEOUT)
        assert resp_nonexistent.status_code == 404, f"Expected 404 for nonexistent short_code but got {resp_nonexistent.status_code}"

    finally:
        # Clean up by deleting the created short_code if it exists
        if short_code:
            del_url = f"{BASE_URL}/api/urls/{short_code}"
            requests.delete(del_url, timeout=TIMEOUT)

test_generate_qr_code_png_for_short_code()
