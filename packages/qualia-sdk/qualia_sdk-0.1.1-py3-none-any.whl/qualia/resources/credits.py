"""
Credits resource for the Qualia API.
"""

from __future__ import annotations

from ..models import CreditBalance
from .base import BaseResource

__all__ = ["CreditsResource"]


class CreditsResource(BaseResource):
    """
    Manage your credit balance.

    Usage:
        ```python
        balance = client.credits.get()
        print(f"Available credits: {balance.balance}")
        ```
    """

    def get(self) -> CreditBalance:
        """
        Get your current credit balance.

        Returns:
            CreditBalance: Your current credit balance.
        """
        data = self._get("/v1/credits")
        return CreditBalance.model_validate(data)
