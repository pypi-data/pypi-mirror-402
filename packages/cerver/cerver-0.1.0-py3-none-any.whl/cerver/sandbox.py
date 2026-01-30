import os
import requests
from typing import Optional
from dataclasses import dataclass
from .exceptions import CerverError, TimeoutError, AuthenticationError, SandboxError


@dataclass
class ExecutionResult:
    """Result of code execution."""
    output: str
    error: str
    exit_code: int
    duration: int  # milliseconds

    @property
    def text(self) -> str:
        """Alias for output (E2B compatibility)."""
        return self.output

    def __str__(self) -> str:
        return self.output


class Sandbox:
    """
    A sandboxed Python execution environment.

    Usage:
        with Sandbox() as sandbox:
            result = sandbox.run("print('Hello!')")
            print(result.output)
    """

    DEFAULT_API_URL = "https://api.cerver.ai"

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        timeout: int = 60
    ):
        """
        Initialize a new Sandbox.

        Args:
            api_key: Your Cerver API key. If not provided, uses CERVER_API_KEY env var.
            api_url: API URL override. Defaults to https://api.cerver.ai
            timeout: Default execution timeout in seconds.
        """
        self.api_key = api_key or os.environ.get("CERVER_API_KEY")
        self.api_url = api_url or os.environ.get("CERVER_API_URL", self.DEFAULT_API_URL)
        self.default_timeout = timeout
        self.sandbox_id: Optional[str] = None
        self._session = requests.Session()

        if self.api_key:
            self._session.headers["Authorization"] = f"Bearer {self.api_key}"
        self._session.headers["Content-Type"] = "application/json"

    def __enter__(self) -> "Sandbox":
        """Context manager entry - creates the sandbox."""
        self.create()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - closes the sandbox."""
        self.close()

    def create(self) -> str:
        """
        Create a new sandbox instance.

        Returns:
            The sandbox ID.
        """
        try:
            response = self._session.post(f"{self.api_url}/sandbox")
            response.raise_for_status()
            data = response.json()
            self.sandbox_id = data["sandbox_id"]
            return self.sandbox_id
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            raise SandboxError(f"Failed to create sandbox: {e}")
        except Exception as e:
            raise SandboxError(f"Failed to create sandbox: {e}")

    def run(self, code: str, timeout: Optional[int] = None) -> ExecutionResult:
        """
        Execute Python code in the sandbox.

        Args:
            code: Python code to execute.
            timeout: Execution timeout in seconds. Defaults to sandbox default.

        Returns:
            ExecutionResult with output, error, exit_code, and duration.
        """
        if not self.sandbox_id:
            self.create()

        timeout = timeout or self.default_timeout

        try:
            response = self._session.post(
                f"{self.api_url}/sandbox/{self.sandbox_id}/run",
                json={"code": code, "timeout": timeout}
            )
            response.raise_for_status()
            data = response.json()

            result = ExecutionResult(
                output=data.get("output", ""),
                error=data.get("error", ""),
                exit_code=data.get("exit_code", 0),
                duration=data.get("duration", 0)
            )

            # Check for timeout
            if "timed out" in result.error.lower():
                raise TimeoutError(result.error)

            return result

        except TimeoutError:
            raise
        except requests.exceptions.HTTPError as e:
            raise SandboxError(f"Failed to run code: {e}")
        except Exception as e:
            raise SandboxError(f"Failed to run code: {e}")

    def install(self, package: str) -> bool:
        """
        Install a Python package in the sandbox.

        Args:
            package: Package name (e.g., "pandas", "numpy==1.24.0")

        Returns:
            True if installation succeeded.
        """
        if not self.sandbox_id:
            self.create()

        try:
            response = self._session.post(
                f"{self.api_url}/sandbox/{self.sandbox_id}/install",
                json={"package": package}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("success", False)
        except Exception as e:
            raise SandboxError(f"Failed to install package: {e}")

    def close(self) -> None:
        """Close the sandbox and release resources."""
        # Sandbox will auto-terminate after sleepAfter timeout
        # This is a no-op for now but keeps the API consistent
        self.sandbox_id = None

    # Aliases for E2B compatibility
    def run_code(self, code: str, timeout: Optional[int] = None) -> ExecutionResult:
        """Alias for run() (E2B compatibility)."""
        return self.run(code, timeout)
