"""
Base resource class for API resources.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..client import Qualia

__all__ = ["BaseResource"]


class BaseResource:
    """Base class for API resources."""

    def __init__(self, client: Qualia) -> None:
        self._client = client

    def _get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return self._client._request("GET", path, params=params)

    def _post(
        self,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        return self._client._request("POST", path, json=json, params=params)

    def _delete(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return self._client._request("DELETE", path, params=params)
