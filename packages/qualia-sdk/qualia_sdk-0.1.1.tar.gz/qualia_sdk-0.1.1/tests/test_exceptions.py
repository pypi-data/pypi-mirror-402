"""Tests for exception classes."""

import httpx

from qualia.exceptions import (
    AuthenticationError,
    NotFoundError,
    QualiaAPIError,
    QualiaError,
    RateLimitError,
    ValidationError,
)


class TestQualiaError:
    """Tests for the base QualiaError."""

    def test_init(self) -> None:
        """QualiaError stores message."""
        error = QualiaError("Something went wrong")
        assert error.message == "Something went wrong"
        assert str(error) == "Something went wrong"


class TestQualiaAPIError:
    """Tests for QualiaAPIError."""

    def test_init(self) -> None:
        """QualiaAPIError stores message, status code, and response."""
        error = QualiaAPIError("Bad request", status_code=400)
        assert error.message == "Bad request"
        assert error.status_code == 400
        assert error.response is None

    def test_init_with_response(self) -> None:
        """QualiaAPIError can store response object."""
        response = httpx.Response(400)
        error = QualiaAPIError("Bad request", status_code=400, response=response)
        assert error.response is response

    def test_str_format(self) -> None:
        """QualiaAPIError formats as [status_code] message."""
        error = QualiaAPIError("Not found", status_code=404)
        assert str(error) == "[404] Not found"


class TestAuthenticationError:
    """Tests for AuthenticationError."""

    def test_init(self) -> None:
        """AuthenticationError inherits from QualiaError."""
        error = AuthenticationError("Invalid API key")
        assert error.message == "Invalid API key"
        assert isinstance(error, QualiaError)


class TestNotFoundError:
    """Tests for NotFoundError."""

    def test_init(self) -> None:
        """NotFoundError has status code 404."""
        error = NotFoundError("Resource not found")
        assert error.message == "Resource not found"
        assert error.status_code == 404
        assert isinstance(error, QualiaAPIError)

    def test_init_with_response(self) -> None:
        """NotFoundError can store response."""
        response = httpx.Response(404)
        error = NotFoundError("Not found", response=response)
        assert error.response is response


class TestValidationError:
    """Tests for ValidationError."""

    def test_init_defaults(self) -> None:
        """ValidationError defaults to status 400."""
        error = ValidationError("Invalid input")
        assert error.message == "Invalid input"
        assert error.status_code == 400
        assert error.errors == []

    def test_init_with_status(self) -> None:
        """ValidationError can have custom status code."""
        error = ValidationError("Unprocessable", status_code=422)
        assert error.status_code == 422

    def test_init_with_errors(self) -> None:
        """ValidationError can store validation errors list."""
        errors = [{"field": "name", "message": "required"}]
        error = ValidationError("Invalid", errors=errors)
        assert error.errors == errors

    def test_init_with_response(self) -> None:
        """ValidationError can store response."""
        response = httpx.Response(400)
        error = ValidationError("Invalid", response=response)
        assert error.response is response


class TestRateLimitError:
    """Tests for RateLimitError."""

    def test_init_defaults(self) -> None:
        """RateLimitError has default message and status 429."""
        error = RateLimitError()
        assert error.message == "Rate limit exceeded"
        assert error.status_code == 429
        assert error.retry_after is None

    def test_init_with_retry_after(self) -> None:
        """RateLimitError can store retry_after."""
        error = RateLimitError(retry_after=60)
        assert error.retry_after == 60

    def test_init_with_custom_message(self) -> None:
        """RateLimitError can have custom message."""
        error = RateLimitError(message="Too many requests")
        assert error.message == "Too many requests"

    def test_init_with_response(self) -> None:
        """RateLimitError can store response."""
        response = httpx.Response(429)
        error = RateLimitError(response=response)
        assert error.response is response
