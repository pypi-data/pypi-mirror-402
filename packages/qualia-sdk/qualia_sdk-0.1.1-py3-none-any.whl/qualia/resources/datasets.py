"""
Datasets resource for the Qualia API.
"""

from __future__ import annotations

from ..models import DatasetImageKeys
from .base import BaseResource

__all__ = ["DatasetsResource"]


class DatasetsResource(BaseResource):
    """
    Inspect HuggingFace datasets for camera mapping.

    Usage:
        ```python
        image_keys = client.datasets.get_image_keys("lerobot/pusht")
        print(f"Available keys: {image_keys.image_keys}")
        ```
    """

    def get_image_keys(self, dataset_id: str) -> DatasetImageKeys:
        """
        Get available image keys from a HuggingFace dataset.

        Use these keys as values in camera_mappings when creating a finetune job.

        Args:
            dataset_id: HuggingFace dataset identifier (e.g., "lerobot/pusht")

        Returns:
            DatasetImageKeys: Available image keys in the dataset.
        """
        # URL-encode the dataset_id since it contains a slash
        data = self._get(f"/v1/datasets/{dataset_id}/image-keys")
        return DatasetImageKeys.model_validate(data)
