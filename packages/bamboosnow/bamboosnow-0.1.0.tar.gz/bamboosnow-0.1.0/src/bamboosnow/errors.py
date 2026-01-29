"""
BambooSnow SDK Errors

Custom exception classes for the BambooSnow SDK.
"""

from __future__ import annotations

from typing import Any


class APIError(Exception):
    """Base exception for all BambooSnow API errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_body = response_body

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(APIError):
    """Raised when authentication fails (401)."""

    def __init__(
        self,
        message: str = "Invalid or missing API key",
        response_body: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, status_code=401, response_body=response_body)


class NotFoundError(APIError):
    """Raised when a resource is not found (404)."""

    def __init__(
        self,
        message: str = "Resource not found",
        response_body: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, status_code=404, response_body=response_body)


class ValidationError(APIError):
    """Raised when request validation fails (400, 422)."""

    def __init__(
        self,
        message: str = "Validation error",
        status_code: int = 400,
        response_body: dict[str, Any] | None = None,
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, response_body=response_body)
        self.errors = errors or []


class RateLimitError(APIError):
    """Raised when rate limit is exceeded (429)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        response_body: dict[str, Any] | None = None,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(message, status_code=429, response_body=response_body)
        self.retry_after = retry_after
