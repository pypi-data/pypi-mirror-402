"""
Models resource for the Qualia API.
"""

from __future__ import annotations

from ..models import VLAModel
from .base import BaseResource

__all__ = ["ModelsResource"]


class ModelsResource(BaseResource):
    """
    List available VLA model types for fine-tuning.

    Usage:
        ```python
        models = client.models.list()
        for model in models:
            print(f"{model.id}: {model.name}")
            print(f"  Camera slots: {model.camera_slots}")
        ```
    """

    def list(self) -> list[VLAModel]:
        """
        List available VLA model types.

        Returns:
            list[VLAModel]: Available VLA model types with their camera slot requirements.
        """
        data = self._get("/v1/models")
        return [VLAModel.model_validate(item) for item in data.get("data", [])]
