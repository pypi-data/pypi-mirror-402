"""Shared test fixtures."""

import pytest

from qualia import Qualia


@pytest.fixture
def api_key() -> str:
    """Test API key."""
    return "test-api-key-12345"


@pytest.fixture
def client(api_key: str) -> Qualia:
    """Create a Qualia client for testing."""
    client = Qualia(api_key=api_key)
    yield client
    client.close()


@pytest.fixture
def base_url() -> str:
    """Base URL for the API."""
    return "https://api.qualiastudios.dev"
