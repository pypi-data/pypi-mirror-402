class CerverError(Exception):
    """Base exception for Cerver errors."""
    pass


class TimeoutError(CerverError):
    """Raised when code execution times out."""
    pass


class AuthenticationError(CerverError):
    """Raised when authentication fails."""
    pass


class SandboxError(CerverError):
    """Raised when sandbox operations fail."""
    pass
