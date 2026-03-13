import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_get_health_check_application_status():
    url = f"{BASE_URL}/health"
    try:
        response = requests.get(url, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request to {url} failed: {e}"

    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    try:
        json_data = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"

    assert "status" in json_data, "Response JSON is missing 'status' key"
    assert json_data["status"] == "healthy", f"Expected status 'healthy', got '{json_data['status']}'"



if __name__ == "__main__":
    test_get_health_check_application_status()
