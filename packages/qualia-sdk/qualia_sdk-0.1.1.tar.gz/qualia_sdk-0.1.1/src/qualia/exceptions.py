"""
Qualia SDK Exceptions

Custom exceptions for the Qualia SDK.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import httpx

__all__ = [
    "QualiaError",
    "QualiaAPIError",
    "AuthenticationError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
]


class QualiaError(Exception):
    """Base exception for all Qualia SDK errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class QualiaAPIError(QualiaError):
    """Exception raised when the API returns an error response."""

    def __init__(
        self,
        message: str,
        status_code: int,
        response: httpx.Response | None = None,
    ) -> None:
        self.status_code = status_code
        self.response = response
        super().__init__(message)

    def __str__(self) -> str:
        return f"[{self.status_code}] {self.message}"


class AuthenticationError(QualiaError):
    """Exception raised for authentication failures."""

    pass


class NotFoundError(QualiaAPIError):
    """Exception raised when a resource is not found (404)."""

    def __init__(self, message: str, response: httpx.Response | None = None) -> None:
        super().__init__(message, status_code=404, response=response)


class ValidationError(QualiaAPIError):
    """Exception raised for validation errors (400/422)."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        response: httpx.Response | None = None,
        errors: list[dict] | None = None,
    ) -> None:
        self.errors = errors or []
        super().__init__(message, status_code=status_code, response=response)


class RateLimitError(QualiaAPIError):
    """Exception raised when rate limit is exceeded (429)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        response: httpx.Response | None = None,
        retry_after: int | None = None,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(message, status_code=429, response=response)
