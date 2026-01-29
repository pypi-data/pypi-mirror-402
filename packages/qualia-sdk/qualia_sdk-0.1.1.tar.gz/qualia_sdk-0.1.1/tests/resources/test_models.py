"""Tests for the Models resource."""

from pytest_httpx import HTTPXMock

from qualia import Qualia
from qualia.models import VLAModel


class TestModelsResource:
    """Tests for ModelsResource."""

    def test_list(self, httpx_mock: HTTPXMock, client: Qualia, base_url: str) -> None:
        """list() returns available VLA models."""
        httpx_mock.add_response(
            url=f"{base_url}/v1/models",
            json={
                "data": [
                    {
                        "id": "smolvla",
                        "name": "SmolVLA",
                        "description": "Lightweight VLA for simple tasks",
                        "base_model_id": "lerobot/smolvla_base",
                        "camera_slots": ["cam_1"],
                    },
                    {
                        "id": "pi0",
                        "name": "Pi0",
                        "description": "General purpose VLA model",
                        "base_model_id": "lerobot/pi0_base",
                        "camera_slots": ["cam_1", "cam_2"],
                    },
                ]
            },
        )

        models = client.models.list()

        assert len(models) == 2
        assert all(isinstance(m, VLAModel) for m in models)
        assert models[0].id == "smolvla"
        assert models[0].camera_slots == ["cam_1"]
        assert models[1].id == "pi0"
        assert len(models[1].camera_slots) == 2

    def test_list_empty(
        self, httpx_mock: HTTPXMock, client: Qualia, base_url: str
    ) -> None:
        """list() handles empty response."""
        httpx_mock.add_response(
            url=f"{base_url}/v1/models",
            json={"data": []},
        )

        models = client.models.list()
        assert models == []
