"""Tests for the Qualia client."""

import pytest
from pytest_httpx import HTTPXMock

from qualia import Qualia
from qualia.exceptions import AuthenticationError, QualiaAPIError


class TestClientInit:
    """Tests for client initialization."""

    def test_init_with_api_key(self) -> None:
        """Client initializes with explicit API key."""
        client = Qualia(api_key="test-key")
        assert client._api_key == "test-key"
        client.close()

    def test_init_from_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Client reads API key from environment variable."""
        monkeypatch.setenv("QUALIA_API_KEY", "env-key")
        client = Qualia()
        assert client._api_key == "env-key"
        client.close()

    def test_init_without_api_key_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Client raises error when no API key is provided."""
        monkeypatch.delenv("QUALIA_API_KEY", raising=False)
        with pytest.raises(AuthenticationError, match="API key is required"):
            Qualia()

    def test_init_custom_base_url(self) -> None:
        """Client accepts custom base URL."""
        client = Qualia(api_key="test-key", base_url="https://custom.api.com")
        assert client._base_url == "https://custom.api.com"
        client.close()

    def test_init_strips_trailing_slash(self) -> None:
        """Client strips trailing slash from base URL."""
        client = Qualia(api_key="test-key", base_url="https://api.example.com/")
        assert client._base_url == "https://api.example.com"
        client.close()

    def test_context_manager(self) -> None:
        """Client works as context manager."""
        with Qualia(api_key="test-key") as client:
            assert client._api_key == "test-key"


class TestClientRequests:
    """Tests for client HTTP requests."""

    def test_authentication_error_on_401(self, httpx_mock: HTTPXMock) -> None:
        """Client raises AuthenticationError on 401 response."""
        httpx_mock.add_response(status_code=401)

        with (
            Qualia(api_key="bad-key") as client,
            pytest.raises(AuthenticationError, match="Invalid API key"),
        ):
            client.models.list()

    def test_api_error_on_4xx(self, httpx_mock: HTTPXMock) -> None:
        """Client raises QualiaAPIError on 4xx responses."""
        httpx_mock.add_response(
            status_code=400,
            json={"detail": "Bad request"},
        )

        with Qualia(api_key="test-key") as client:
            with pytest.raises(QualiaAPIError) as exc_info:
                client.models.list()
            assert exc_info.value.status_code == 400

    def test_default_headers(self) -> None:
        """Client sends correct default headers."""
        client = Qualia(api_key="test-key")
        headers = client._default_headers()

        assert headers["X-API-Key"] == "test-key"
        assert headers["Content-Type"] == "application/json"
        assert "qualia-python" in headers["User-Agent"]
        client.close()
