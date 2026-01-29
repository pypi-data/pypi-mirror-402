"""Integration test configuration.

These tests hit the real dev API at dev-api.qualiastudios.dev.
Requires a .env file with QUALIA_TEST_API_KEY set.
"""

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from qualia import Qualia

# Load .env from project root
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

DEV_BASE_URL = "https://dev-api.qualiastudios.dev"


def get_test_api_key() -> str | None:
    """Get API key from environment."""
    return os.environ.get("QUALIA_TEST_API_KEY")


def has_integration_credentials() -> bool:
    """Check if integration test credentials are available."""
    key = get_test_api_key()
    return key is not None and key != "your-dev-api-key-here"


# Skip all integration tests if no credentials
pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def integration_api_key() -> str:
    """Get the API key for integration tests."""
    key = get_test_api_key()
    if not key or key == "your-dev-api-key-here":
        pytest.skip("QUALIA_TEST_API_KEY not set in .env file")
    return key


@pytest.fixture(scope="module")
def integration_client(integration_api_key: str) -> Qualia:
    """Create a client pointing to dev API for integration tests."""
    base_url = os.environ.get("QUALIA_TEST_BASE_URL", DEV_BASE_URL)
    client = Qualia(api_key=integration_api_key, base_url=base_url)
    yield client
    client.close()
