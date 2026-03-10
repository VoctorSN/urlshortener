import requests

def test_get_health_check_application_status():
    url = "http://localhost:8000/health"
    try:
        response = requests.get(url, timeout=30)
        assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
        json_data = response.json()
        assert isinstance(json_data, dict), "Response is not a JSON object"
        assert json_data.get("status") == "healthy", f"Expected status 'healthy', got {json_data.get('status')}"
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"

test_get_health_check_application_status()