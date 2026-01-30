"""Integration tests for the Cerver API."""
import pytest
import requests

API_URL = "https://api.cerver.ai"


class TestAPIEndpoints:
    """Test the API endpoints directly."""

    def test_root_endpoint(self):
        """GET / returns API info."""
        response = requests.get(f"{API_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Cerver API"
        assert "endpoints" in data

    def test_create_sandbox(self):
        """POST /sandbox creates a new sandbox."""
        response = requests.post(f"{API_URL}/sandbox")
        assert response.status_code == 200
        data = response.json()
        assert "sandbox_id" in data
        assert data["status"] == "ready"
        assert len(data["sandbox_id"]) == 36  # UUID format

    def test_run_simple_code(self):
        """POST /sandbox/:id/run executes code."""
        response = requests.post(
            f"{API_URL}/sandbox/test/run",
            json={"code": "print('hello')"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["output"] == "hello"
        assert data["error"] == ""
        assert data["exit_code"] == 0

    def test_run_math(self):
        """Code can perform calculations."""
        response = requests.post(
            f"{API_URL}/sandbox/test/run",
            json={"code": "print(2 ** 10)"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["output"] == "1024"

    def test_run_multiline(self):
        """Code can span multiple lines."""
        code = """
for i in range(3):
    print(i)
"""
        response = requests.post(
            f"{API_URL}/sandbox/test/run",
            json={"code": code}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["output"] == "0\n1\n2"

    def test_run_function_definition(self):
        """Code can define and call functions."""
        code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

print(factorial(5))
"""
        response = requests.post(
            f"{API_URL}/sandbox/test/run",
            json={"code": code}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["output"] == "120"

    def test_run_with_error(self):
        """Syntax errors are captured in error field."""
        response = requests.post(
            f"{API_URL}/sandbox/test/run",
            json={"code": "print(undefined_var)"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["exit_code"] == 1
        assert "NameError" in data["error"]

    def test_run_syntax_error(self):
        """Syntax errors are captured."""
        response = requests.post(
            f"{API_URL}/sandbox/test/run",
            json={"code": "def foo("}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["exit_code"] == 1
        assert "SyntaxError" in data["error"]

    def test_run_empty_code(self):
        """Empty code returns error."""
        response = requests.post(
            f"{API_URL}/sandbox/test/run",
            json={"code": ""}
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    def test_sandbox_state_persistence(self):
        """Variables persist within a sandbox session."""
        # Create a sandbox
        create_response = requests.post(f"{API_URL}/sandbox")
        sandbox_id = create_response.json()["sandbox_id"]

        # Set a variable
        requests.post(
            f"{API_URL}/sandbox/{sandbox_id}/run",
            json={"code": "x = 42"}
        )

        # Read the variable
        response = requests.post(
            f"{API_URL}/sandbox/{sandbox_id}/run",
            json={"code": "print(x)"}
        )
        assert response.json()["output"] == "42"

    def test_sandbox_isolation(self):
        """Different sandboxes are isolated."""
        # Create two sandboxes
        sandbox1 = requests.post(f"{API_URL}/sandbox").json()["sandbox_id"]
        sandbox2 = requests.post(f"{API_URL}/sandbox").json()["sandbox_id"]

        # Set variable in sandbox1
        requests.post(
            f"{API_URL}/sandbox/{sandbox1}/run",
            json={"code": "secret = 'sandbox1'"}
        )

        # Try to access in sandbox2 - should fail
        response = requests.post(
            f"{API_URL}/sandbox/{sandbox2}/run",
            json={"code": "print(secret)"}
        )
        assert response.json()["exit_code"] == 1
        assert "NameError" in response.json()["error"]

    def test_duration_returned(self):
        """Execution duration is returned."""
        response = requests.post(
            f"{API_URL}/sandbox/test/run",
            json={"code": "x = 1"}
        )
        data = response.json()
        assert "duration" in data
        assert isinstance(data["duration"], int)
        assert data["duration"] >= 0

    def test_404_on_unknown_route(self):
        """Unknown routes return 404."""
        response = requests.get(f"{API_URL}/unknown/route")
        assert response.status_code == 404

    def test_cors_headers(self):
        """CORS headers are present."""
        response = requests.get(f"{API_URL}/")
        assert response.headers.get("Access-Control-Allow-Origin") == "*"

    def test_options_preflight(self):
        """OPTIONS requests return CORS preflight response."""
        response = requests.options(f"{API_URL}/sandbox")
        assert response.status_code == 204
        assert "Access-Control-Allow-Methods" in response.headers
