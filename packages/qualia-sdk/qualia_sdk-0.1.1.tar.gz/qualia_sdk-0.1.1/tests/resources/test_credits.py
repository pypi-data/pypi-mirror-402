"""Tests for the Credits resource."""

from pytest_httpx import HTTPXMock

from qualia import Qualia
from qualia.models import CreditBalance


class TestCreditsResource:
    """Tests for CreditsResource."""

    def test_get(self, httpx_mock: HTTPXMock, client: Qualia, base_url: str) -> None:
        """get() returns credit balance."""
        httpx_mock.add_response(
            url=f"{base_url}/v1/credits",
            json={"balance": 5000},
        )

        balance = client.credits.get()

        assert isinstance(balance, CreditBalance)
        assert balance.balance == 5000

    def test_get_zero_balance(
        self, httpx_mock: HTTPXMock, client: Qualia, base_url: str
    ) -> None:
        """get() handles zero balance."""
        httpx_mock.add_response(
            url=f"{base_url}/v1/credits",
            json={"balance": 0},
        )

        balance = client.credits.get()
        assert balance.balance == 0
