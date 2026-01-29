"""Tests for the Instances resource."""

from pytest_httpx import HTTPXMock

from qualia import Qualia
from qualia.models import Instance


class TestInstancesResource:
    """Tests for InstancesResource."""

    def test_list(self, httpx_mock: HTTPXMock, client: Qualia, base_url: str) -> None:
        """list() returns available instances."""
        httpx_mock.add_response(
            url=f"{base_url}/v1/instances",
            json={
                "data": [
                    {
                        "id": "n3-A100x1",
                        "name": "n3-A100x1",
                        "description": "NVIDIA A100 80GB x1",
                        "gpu_description": "NVIDIA A100 80GB",
                        "credits_per_hour": 250,
                        "specs": {
                            "vcpus": 12,
                            "memory_gib": 85,
                            "storage_gib": 500,
                            "gpu_count": 1,
                            "gpu_type": "NVIDIA A100 80GB",
                        },
                        "regions": [
                            {"name": "CANADA-1", "description": "Canada"},
                            {"name": "NORWAY-1", "description": "Norway"},
                        ],
                        "region_count": 2,
                    },
                    {
                        "id": "n3-H100x1",
                        "name": "n3-H100x1",
                        "description": "NVIDIA H100 80GB x1",
                        "gpu_description": "NVIDIA H100 80GB",
                        "credits_per_hour": 400,
                        "specs": {
                            "vcpus": 24,
                            "memory_gib": 200,
                            "storage_gib": 1000,
                            "gpu_count": 1,
                            "gpu_type": "NVIDIA H100 80GB",
                        },
                        "regions": [
                            {"name": "CANADA-1", "description": "Canada"},
                        ],
                        "region_count": 1,
                    },
                ]
            },
        )

        instances = client.instances.list()

        assert len(instances) == 2
        assert all(isinstance(i, Instance) for i in instances)
        assert instances[0].id == "n3-A100x1"
        assert instances[0].credits_per_hour == 250
        assert instances[0].specs.gpu_count == 1
        assert len(instances[0].regions) == 2
        assert instances[1].id == "n3-H100x1"

    def test_list_empty(
        self, httpx_mock: HTTPXMock, client: Qualia, base_url: str
    ) -> None:
        """list() handles empty response."""
        httpx_mock.add_response(
            url=f"{base_url}/v1/instances",
            json={"data": []},
        )

        instances = client.instances.list()
        assert instances == []
