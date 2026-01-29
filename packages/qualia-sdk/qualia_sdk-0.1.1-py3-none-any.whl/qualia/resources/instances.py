"""
Instances resource for the Qualia API.
"""

from __future__ import annotations

from ..models import Instance
from .base import BaseResource

__all__ = ["InstancesResource"]


class InstancesResource(BaseResource):
    """
    List available GPU instances and pricing.

    Usage:
        ```python
        instances = client.instances.list()
        for inst in instances:
            print(f"{inst.id}: {inst.gpu_description} - {inst.credits_per_hour} credits/hr")
        ```
    """

    def list(self) -> list[Instance]:
        """
        List available GPU instances.

        Returns:
            list[Instance]: Available GPU instance types with pricing.
        """
        data = self._get("/v1/instances")
        return [Instance.model_validate(item) for item in data.get("data", [])]
