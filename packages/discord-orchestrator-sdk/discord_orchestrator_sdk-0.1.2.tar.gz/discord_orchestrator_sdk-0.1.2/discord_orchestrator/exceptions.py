"""Custom exceptions for the Discord Bot Orchestrator SDK."""

from __future__ import annotations

from typing import Any, Optional


class OrchestratorError(Exception):
    """Base exception for all SDK errors.

    Attributes:
        message: Human-readable error message
        code: Error code from the API (if available)
        details: Additional error details (if available)
    """

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, code={self.code!r})"


class AuthenticationError(OrchestratorError):
    """Raised when authentication fails (401)."""

    pass


class AuthorizationError(OrchestratorError):
    """Raised when the user lacks permission (403)."""

    pass


class NotFoundError(OrchestratorError):
    """Raised when a resource is not found (404)."""

    pass


class ValidationError(OrchestratorError):
    """Raised when request validation fails (400)."""

    pass


class RateLimitError(OrchestratorError):
    """Raised when rate limit is exceeded (429)."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        retry_after: Optional[float] = None,
    ):
        super().__init__(message, code, details)
        self.retry_after = retry_after


class TimeoutError(OrchestratorError):
    """Raised when a request times out."""

    pass


class ServerError(OrchestratorError):
    """Raised when the server returns a 5xx error."""

    pass


class ConnectionError(OrchestratorError):
    """Raised when connection to the server fails."""

    pass
