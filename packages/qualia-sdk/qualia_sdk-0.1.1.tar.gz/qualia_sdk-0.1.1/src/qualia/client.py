"""
Qualia SDK Client

Main entry point for interacting with the Qualia API.
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from opentelemetry import baggage, context
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

from .exceptions import AuthenticationError, QualiaAPIError, QualiaError
from .resources.credits import CreditsResource
from .resources.datasets import DatasetsResource
from .resources.finetune import FinetuneResource
from .resources.instances import InstancesResource
from .resources.models import ModelsResource
from .resources.projects import ProjectsResource

__all__ = ["Qualia"]

DEFAULT_BASE_URL = "https://api.qualiastudios.dev"
DEFAULT_TIMEOUT = 30.0


def _setup_otel_baggage() -> None:
    """Set client_type baggage for trace propagation."""
    ctx = baggage.set_baggage("client_type", "sdk-python")
    context.attach(ctx)


class Qualia:
    """
    Client for the Qualia API.

    Usage:
        ```python
        from qualia import Qualia

        client = Qualia(api_key="your-api-key")

        # List available models
        models = client.models.list()

        # Create a project
        project = client.projects.create(name="My Project")

        # Start a finetune job
        job = client.finetune.create(
            project_id=project.project_id,
            model_id="lerobot/smolvla_base",
            vla_type="smolvla",
            dataset_id="lerobot/pusht",
            hours=2.0,
            camera_mappings={"cam_1": "observation.images.top"},
        )
        ```

    Args:
        api_key: Your Qualia API key. If not provided, reads from QUALIA_API_KEY env var.
        base_url: Base URL for the API. Defaults to https://api.qualiastudios.dev
        timeout: Request timeout in seconds. Defaults to 30.0
        httpx_client: Optional custom httpx.Client instance for advanced configuration.
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        httpx_client: httpx.Client | None = None,
    ) -> None:
        self._api_key = api_key or os.environ.get("QUALIA_API_KEY")
        if not self._api_key:
            raise AuthenticationError(
                "API key is required. Pass api_key or set QUALIA_API_KEY environment variable."
            )

        self._base_url = (
            base_url or os.environ.get("QUALIA_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self._timeout = timeout

        if httpx_client is not None:
            self._client = httpx_client
            self._owns_client = False
        else:
            self._client = httpx.Client(
                base_url=self._base_url,
                timeout=timeout,
                headers=self._default_headers(),
            )
            self._owns_client = True

        # Set up OTEL baggage and instrument httpx
        _setup_otel_baggage()
        HTTPXClientInstrumentor().instrument_client(self._client)

        # Initialize resources
        self.credits = CreditsResource(self)
        self.datasets = DatasetsResource(self)
        self.finetune = FinetuneResource(self)
        self.instances = InstancesResource(self)
        self.models = ModelsResource(self)
        self.projects = ProjectsResource(self)

    def _default_headers(self) -> dict[str, str]:
        return {
            "X-API-Key": self._api_key,
            "Content-Type": "application/json",
            "User-Agent": "qualia-python/0.1.0",
        }

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        """Make an HTTP request to the API."""
        url = f"{self._base_url}{path}"
        headers = self._default_headers()

        try:
            response = self._client.request(
                method=method,
                url=url,
                params=params,
                json=json,
                headers=headers,
            )
        except httpx.TimeoutException as e:
            raise QualiaError(f"Request timed out: {e}") from e
        except httpx.RequestError as e:
            raise QualiaError(f"Request failed: {e}") from e

        return self._handle_response(response)

    def _handle_response(self, response: httpx.Response) -> Any:
        """Handle API response and raise appropriate exceptions."""
        if response.status_code == 401:
            raise AuthenticationError("Invalid API key")

        if response.status_code == 403:
            raise AuthenticationError("Access denied")

        if response.status_code >= 400:
            try:
                error_data = response.json()
                detail = error_data.get("detail", response.text)
            except Exception:
                detail = response.text

            raise QualiaAPIError(
                message=str(detail),
                status_code=response.status_code,
                response=response,
            )

        if response.status_code == 204:
            return None

        return response.json()

    def close(self) -> None:
        """Close the HTTP client."""
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> Qualia:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
