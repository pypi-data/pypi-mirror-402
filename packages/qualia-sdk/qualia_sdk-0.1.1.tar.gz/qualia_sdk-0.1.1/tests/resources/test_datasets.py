"""Tests for the Datasets resource."""

from pytest_httpx import HTTPXMock

from qualia import Qualia
from qualia.models import DatasetImageKeys


class TestDatasetsResource:
    """Tests for DatasetsResource."""

    def test_get_image_keys(
        self, httpx_mock: HTTPXMock, client: Qualia, base_url: str
    ) -> None:
        """get_image_keys() returns dataset image keys."""
        httpx_mock.add_response(
            url=f"{base_url}/v1/datasets/lerobot/pusht/image-keys",
            json={
                "dataset_id": "lerobot/pusht",
                "image_keys": ["observation.images.top", "observation.images.wrist"],
            },
        )

        keys = client.datasets.get_image_keys("lerobot/pusht")

        assert isinstance(keys, DatasetImageKeys)
        assert keys.dataset_id == "lerobot/pusht"
        assert "observation.images.top" in keys.image_keys
        assert len(keys.image_keys) == 2

    def test_get_image_keys_empty(
        self, httpx_mock: HTTPXMock, client: Qualia, base_url: str
    ) -> None:
        """get_image_keys() handles datasets with no image keys."""
        httpx_mock.add_response(
            url=f"{base_url}/v1/datasets/user/text-only/image-keys",
            json={
                "dataset_id": "user/text-only",
                "image_keys": [],
            },
        )

        keys = client.datasets.get_image_keys("user/text-only")
        assert keys.image_keys == []
