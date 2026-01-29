"""Tests for the Finetune resource."""

from uuid import UUID

from pytest_httpx import HTTPXMock

from qualia import Qualia
from qualia.models import FinetuneCancelResult, FinetuneJob, FinetuneStatus, VLAType


class TestFinetuneResource:
    """Tests for FinetuneResource."""

    def test_create_minimal(
        self, httpx_mock: HTTPXMock, client: Qualia, base_url: str
    ) -> None:
        """create() with minimal required parameters."""
        job_id = "550e8400-e29b-41d4-a716-446655440000"
        project_id = "660e8400-e29b-41d4-a716-446655440000"

        httpx_mock.add_response(
            url=f"{base_url}/v1/finetune",
            method="POST",
            json={"job_id": job_id, "status": "queued", "message": "Job created"},
        )

        job = client.finetune.create(
            project_id=project_id,
            model_id="lerobot/smolvla_base",
            vla_type="smolvla",
            dataset_id="lerobot/pusht",
            hours=2.0,
            camera_mappings={"cam_1": "observation.images.top"},
        )

        assert isinstance(job, FinetuneJob)
        assert job.job_id == UUID(job_id)
        assert job.status == "queued"

        # Verify request body
        request = httpx_mock.get_request()
        assert request is not None
        body = request.content.decode()
        assert "smolvla" in body
        assert "lerobot/pusht" in body

    def test_create_with_vla_type_enum(
        self, httpx_mock: HTTPXMock, client: Qualia, base_url: str
    ) -> None:
        """create() accepts VLAType enum."""
        job_id = "550e8400-e29b-41d4-a716-446655440000"

        httpx_mock.add_response(
            url=f"{base_url}/v1/finetune",
            method="POST",
            json={"job_id": job_id, "status": "queued", "message": None},
        )

        job = client.finetune.create(
            project_id="660e8400-e29b-41d4-a716-446655440000",
            model_id="lerobot/smolvla_base",
            vla_type=VLAType.SMOLVLA,
            dataset_id="lerobot/pusht",
            hours=1.0,
            camera_mappings={"cam_1": "observation.images.top"},
        )

        assert job.job_id == UUID(job_id)

    def test_create_with_all_options(
        self, httpx_mock: HTTPXMock, client: Qualia, base_url: str
    ) -> None:
        """create() with all optional parameters."""
        job_id = "550e8400-e29b-41d4-a716-446655440000"

        httpx_mock.add_response(
            url=f"{base_url}/v1/finetune",
            method="POST",
            json={"job_id": job_id, "status": "queued", "message": "Job created"},
        )

        job = client.finetune.create(
            project_id="660e8400-e29b-41d4-a716-446655440000",
            model_id="lerobot/smolvla_base",
            vla_type="smolvla",
            dataset_id="lerobot/pusht",
            hours=4.0,
            camera_mappings={"cam_1": "observation.images.top"},
            instance_type="gpu-a100-40gb",
            region="us-east-1",
            batch_size=64,
            name="My Training Job",
        )

        assert job.job_id == UUID(job_id)

        # Verify all options in request body
        request = httpx_mock.get_request()
        assert request is not None
        body = request.content.decode()
        assert "gpu-a100-40gb" in body
        assert "us-east-1" in body
        assert "64" in body
        assert "My Training Job" in body

    def test_get(self, httpx_mock: HTTPXMock, client: Qualia, base_url: str) -> None:
        """get() returns finetune status."""
        job_id = "550e8400-e29b-41d4-a716-446655440000"

        httpx_mock.add_response(
            url=f"{base_url}/v1/finetune/{job_id}",
            json={
                "job_id": job_id,
                "current_phase": "training",
                "status": "running",
                "phases": [
                    {"name": "setup", "status": "completed"},
                    {"name": "training", "status": "in_progress"},
                ],
            },
        )

        status = client.finetune.get(job_id)

        assert isinstance(status, FinetuneStatus)
        assert status.job_id == UUID(job_id)
        assert status.current_phase == "training"
        assert status.status == "running"
        assert len(status.phases) == 2

    def test_get_with_uuid(
        self, httpx_mock: HTTPXMock, client: Qualia, base_url: str
    ) -> None:
        """get() accepts UUID object."""
        job_id = UUID("550e8400-e29b-41d4-a716-446655440000")

        httpx_mock.add_response(
            url=f"{base_url}/v1/finetune/{job_id}",
            json={
                "job_id": str(job_id),
                "current_phase": "done",
                "status": "completed",
                "phases": [],
            },
        )

        status = client.finetune.get(job_id)
        assert status.job_id == job_id

    def test_cancel(self, httpx_mock: HTTPXMock, client: Qualia, base_url: str) -> None:
        """cancel() cancels a finetune job."""
        job_id = "550e8400-e29b-41d4-a716-446655440000"

        httpx_mock.add_response(
            url=f"{base_url}/v1/finetune/{job_id}/cancel",
            method="POST",
            json={
                "job_id": job_id,
                "cancelled": True,
                "message": "Job cancelled successfully",
            },
        )

        result = client.finetune.cancel(job_id)

        assert isinstance(result, FinetuneCancelResult)
        assert result.job_id == UUID(job_id)
        assert result.cancelled is True
        assert result.message == "Job cancelled successfully"

    def test_cancel_with_uuid(
        self, httpx_mock: HTTPXMock, client: Qualia, base_url: str
    ) -> None:
        """cancel() accepts UUID object."""
        job_id = UUID("550e8400-e29b-41d4-a716-446655440000")

        httpx_mock.add_response(
            url=f"{base_url}/v1/finetune/{job_id}/cancel",
            method="POST",
            json={"job_id": str(job_id), "cancelled": True, "message": None},
        )

        result = client.finetune.cancel(job_id)
        assert result.cancelled is True
