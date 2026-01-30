"""Unit tests for the Cerver SDK."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import os

from cerver import Sandbox, CerverError, TimeoutError, SandboxError
from cerver.sandbox import ExecutionResult


class TestExecutionResult:
    """Test the ExecutionResult dataclass."""

    def test_basic_result(self):
        result = ExecutionResult(
            output="hello",
            error="",
            exit_code=0,
            duration=10
        )
        assert result.output == "hello"
        assert result.error == ""
        assert result.exit_code == 0
        assert result.duration == 10

    def test_text_property(self):
        """text property is alias for output (E2B compatibility)."""
        result = ExecutionResult(output="hello", error="", exit_code=0, duration=0)
        assert result.text == "hello"

    def test_str_returns_output(self):
        result = ExecutionResult(output="hello", error="", exit_code=0, duration=0)
        assert str(result) == "hello"


class TestSandboxInit:
    """Test Sandbox initialization."""

    def test_default_api_url(self):
        sandbox = Sandbox()
        assert sandbox.api_url == "https://api.cerver.ai"

    def test_custom_api_url(self):
        sandbox = Sandbox(api_url="https://custom.api.com")
        assert sandbox.api_url == "https://custom.api.com"

    def test_api_url_from_env(self):
        with patch.dict(os.environ, {"CERVER_API_URL": "https://env.api.com"}):
            sandbox = Sandbox()
            assert sandbox.api_url == "https://env.api.com"

    def test_api_key_from_param(self):
        sandbox = Sandbox(api_key="sk_test_123")
        assert sandbox.api_key == "sk_test_123"

    def test_api_key_from_env(self):
        with patch.dict(os.environ, {"CERVER_API_KEY": "sk_env_456"}):
            sandbox = Sandbox()
            assert sandbox.api_key == "sk_env_456"

    def test_default_timeout(self):
        sandbox = Sandbox()
        assert sandbox.default_timeout == 60

    def test_custom_timeout(self):
        sandbox = Sandbox(timeout=120)
        assert sandbox.default_timeout == 120


class TestSandboxCreate:
    """Test sandbox creation."""

    def test_create_returns_sandbox_id(self):
        sandbox = Sandbox()

        mock_response = Mock()
        mock_response.json.return_value = {"sandbox_id": "abc-123", "status": "ready"}
        sandbox._session.post = Mock(return_value=mock_response)

        sandbox_id = sandbox.create()

        assert sandbox_id == "abc-123"
        assert sandbox.sandbox_id == "abc-123"

    def test_create_handles_401(self):
        from cerver import AuthenticationError
        import requests

        sandbox = Sandbox()

        mock_response = Mock()
        mock_response.status_code = 401
        error = requests.exceptions.HTTPError(response=mock_response)
        mock_response.raise_for_status.side_effect = error
        sandbox._session.post = Mock(return_value=mock_response)
        sandbox._session.post.return_value.raise_for_status.side_effect = error

        with pytest.raises(AuthenticationError):
            sandbox.create()


class TestSandboxRun:
    """Test code execution."""

    def test_run_returns_result(self):
        sandbox = Sandbox()
        sandbox.sandbox_id = "test-123"  # Skip create

        mock_response = Mock()
        mock_response.json.return_value = {
            "output": "hello",
            "error": "",
            "exit_code": 0,
            "duration": 5
        }
        sandbox._session.post = Mock(return_value=mock_response)

        result = sandbox.run("print('hello')")

        assert result.output == "hello"
        assert result.error == ""
        assert result.exit_code == 0
        assert result.duration == 5

    def test_run_auto_creates_sandbox(self):
        sandbox = Sandbox()

        mock_create_response = Mock()
        mock_create_response.json.return_value = {"sandbox_id": "auto-123"}

        mock_run_response = Mock()
        mock_run_response.json.return_value = {
            "output": "", "error": "", "exit_code": 0, "duration": 0
        }

        sandbox._session.post = Mock(side_effect=[mock_create_response, mock_run_response])

        assert sandbox.sandbox_id is None
        sandbox.run("x = 1")
        assert sandbox.sandbox_id == "auto-123"

    def test_run_with_custom_timeout(self):
        sandbox = Sandbox()
        sandbox.sandbox_id = "test-123"

        mock_response = Mock()
        mock_response.json.return_value = {
            "output": "", "error": "", "exit_code": 0, "duration": 0
        }
        sandbox._session.post = Mock(return_value=mock_response)

        sandbox.run("x = 1", timeout=30)

        # Check that timeout was passed in the JSON body
        call_args = sandbox._session.post.call_args
        assert call_args[1]["json"]["timeout"] == 30

    def test_run_detects_timeout_error(self):
        sandbox = Sandbox()
        sandbox.sandbox_id = "test-123"

        mock_response = Mock()
        mock_response.json.return_value = {
            "output": "",
            "error": "Execution timed out after 60 seconds",
            "exit_code": 1,
            "duration": 60000
        }
        sandbox._session.post = Mock(return_value=mock_response)

        with pytest.raises(TimeoutError):
            sandbox.run("while True: pass")

    def test_run_code_alias(self):
        """run_code is alias for run (E2B compatibility)."""
        sandbox = Sandbox()
        sandbox.sandbox_id = "test-123"

        mock_response = Mock()
        mock_response.json.return_value = {
            "output": "test", "error": "", "exit_code": 0, "duration": 0
        }
        sandbox._session.post = Mock(return_value=mock_response)

        result = sandbox.run_code("print('test')")
        assert result.output == "test"


class TestSandboxContextManager:
    """Test context manager behavior."""

    def test_context_manager_creates_and_closes(self):
        with patch.object(Sandbox, 'create') as mock_create:
            mock_create.return_value = "ctx-123"

            with Sandbox() as sandbox:
                sandbox.sandbox_id = "ctx-123"  # Simulate create setting this
                assert sandbox.sandbox_id == "ctx-123"

            # After exiting, sandbox_id should be None
            assert sandbox.sandbox_id is None

    def test_context_manager_on_exception(self):
        with patch.object(Sandbox, 'create') as mock_create:
            mock_create.return_value = "ctx-123"

            try:
                with Sandbox() as sandbox:
                    sandbox.sandbox_id = "ctx-123"
                    raise ValueError("test error")
            except ValueError:
                pass

            # Sandbox should still be closed
            assert sandbox.sandbox_id is None


class TestSandboxClose:
    """Test sandbox close behavior."""

    def test_close_clears_sandbox_id(self):
        sandbox = Sandbox()
        sandbox.sandbox_id = "test-123"
        sandbox.close()
        assert sandbox.sandbox_id is None

    def test_close_when_no_sandbox(self):
        sandbox = Sandbox()
        sandbox.close()  # Should not raise
        assert sandbox.sandbox_id is None


class TestSandboxInstall:
    """Test package installation."""

    def test_install_package(self):
        sandbox = Sandbox()
        sandbox.sandbox_id = "test-123"

        mock_response = Mock()
        mock_response.json.return_value = {"success": True}
        sandbox._session.post = Mock(return_value=mock_response)

        result = sandbox.install("pandas")
        assert result is True

    def test_install_failure(self):
        sandbox = Sandbox()
        sandbox.sandbox_id = "test-123"

        mock_response = Mock()
        mock_response.json.return_value = {"success": False}
        sandbox._session.post = Mock(return_value=mock_response)

        result = sandbox.install("nonexistent-package")
        assert result is False
