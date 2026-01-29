"""Workflow tests with mocked HTTP.

These tests verify complete user workflows and error handling paths
using mocked HTTP responses (no real API calls).
"""

from uuid import UUID

import httpx
import pytest
from pytest_httpx import HTTPXMock

from qualia import Qualia
from qualia.exceptions import AuthenticationError, QualiaAPIError, QualiaError
from qualia.models import VLAType


class TestCompleteTrainingWorkflow:
    """Test the complete workflow from project creation to job completion."""

    def test_full_training_workflow(
        self, httpx_mock: HTTPXMock, client: Qualia, base_url: str
    ) -> None:
        """Complete workflow: create project -> check models -> create job -> monitor."""
        project_id = "550e8400-e29b-41d4-a716-446655440000"
        job_id = "660e8400-e29b-41d4-a716-446655440000"

        # 1. Create project
        httpx_mock.add_response(
            url=f"{base_url}/v1/projects",
            method="POST",
            json={"created": True, "project_id": project_id},
        )

        # 2. List available models
        httpx_mock.add_response(
            url=f"{base_url}/v1/models",
            json={
                "data": [
                    {
                        "id": "smolvla",
                        "name": "SmolVLA",
                        "description": "Lightweight VLA",
                        "base_model_id": "lerobot/smolvla_base",
                        "camera_slots": ["cam_1"],
                    }
                ]
            },
        )

        # 3. Get dataset image keys
        httpx_mock.add_response(
            url=f"{base_url}/v1/datasets/lerobot/pusht/image-keys",
            json={
                "dataset_id": "lerobot/pusht",
                "image_keys": ["observation.images.top"],
            },
        )

        # 4. Check credits
        httpx_mock.add_response(
            url=f"{base_url}/v1/credits",
            json={"balance": 10000},
        )

        # 5. Create finetune job
        httpx_mock.add_response(
            url=f"{base_url}/v1/finetune",
            method="POST",
            json={"job_id": job_id, "status": "queued", "message": "Job created"},
        )

        # 6. Check job status
        httpx_mock.add_response(
            url=f"{base_url}/v1/finetune/{job_id}",
            json={
                "job_id": job_id,
                "current_phase": "training",
                "status": "running",
                "phases": [],
            },
        )

        # Execute workflow
        project = client.projects.create(name="E2E Test Project")
        assert project.project_id == UUID(project_id)

        models = client.models.list()
        assert len(models) == 1
        assert models[0].camera_slots == ["cam_1"]

        image_keys = client.datasets.get_image_keys("lerobot/pusht")
        assert "observation.images.top" in image_keys.image_keys

        credits = client.credits.get()
        assert credits.balance >= 1000

        job = client.finetune.create(
            project_id=project.project_id,
            model_id=models[0].base_model_id,
            vla_type=models[0].id,
            dataset_id="lerobot/pusht",
            hours=2.0,
            camera_mappings={"cam_1": image_keys.image_keys[0]},
        )
        assert job.status == "queued"

        status = client.finetune.get(job.job_id)
        assert status.status == "running"


class TestErrorHandlingWorkflows:
    """Test error handling across different scenarios."""

    def test_invalid_api_key_workflow(
        self, httpx_mock: HTTPXMock, base_url: str
    ) -> None:
        """Workflow fails gracefully with invalid API key."""
        httpx_mock.add_response(
            url=f"{base_url}/v1/projects",
            status_code=401,
            json={"detail": "Invalid API key"},
        )

        with (
            Qualia(api_key="invalid-key") as client,
            pytest.raises(AuthenticationError, match="Invalid API key"),
        ):
            client.projects.list()

    def test_forbidden_access(
        self, httpx_mock: HTTPXMock, client: Qualia, base_url: str
    ) -> None:
        """403 response raises AuthenticationError."""
        httpx_mock.add_response(
            url=f"{base_url}/v1/projects",
            status_code=403,
            json={"detail": "Access denied"},
        )

        with pytest.raises(AuthenticationError, match="Access denied"):
            client.projects.list()

    def test_server_error_workflow(
        self, httpx_mock: HTTPXMock, client: Qualia, base_url: str
    ) -> None:
        """Server errors are handled properly."""
        httpx_mock.add_response(
            url=f"{base_url}/v1/credits",
            status_code=500,
            json={"detail": "Internal server error"},
        )

        with pytest.raises(QualiaAPIError) as exc_info:
            client.credits.get()

        assert exc_info.value.status_code == 500

    def test_server_error_non_json_response(
        self, httpx_mock: HTTPXMock, client: Qualia, base_url: str
    ) -> None:
        """Server errors with non-JSON responses are handled."""
        httpx_mock.add_response(
            url=f"{base_url}/v1/credits",
            status_code=502,
            text="Bad Gateway",
        )

        with pytest.raises(QualiaAPIError) as exc_info:
            client.credits.get()

        assert exc_info.value.status_code == 502
        assert "Bad Gateway" in exc_info.value.message

    def test_timeout_handling(self, httpx_mock: HTTPXMock, base_url: str) -> None:
        """Request timeouts are handled gracefully."""

        def raise_timeout(request: httpx.Request) -> httpx.Response:
            raise httpx.TimeoutException("Connection timed out", request=request)

        httpx_mock.add_callback(raise_timeout, url=f"{base_url}/v1/credits")

        with (
            Qualia(api_key="test-key", timeout=1.0) as client,
            pytest.raises(QualiaError, match="timed out"),
        ):
            client.credits.get()

    def test_connection_error_handling(
        self, httpx_mock: HTTPXMock, base_url: str
    ) -> None:
        """Connection errors are handled gracefully."""

        def raise_connection_error(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Connection refused", request=request)

        httpx_mock.add_callback(raise_connection_error, url=f"{base_url}/v1/credits")

        with (
            Qualia(api_key="test-key") as client,
            pytest.raises(QualiaError, match="failed"),
        ):
            client.credits.get()

    def test_204_no_content_response(
        self, httpx_mock: HTTPXMock, client: Qualia, base_url: str
    ) -> None:
        """204 No Content responses return None."""
        project_id = "550e8400-e29b-41d4-a716-446655440000"

        # Mock a hypothetical endpoint that returns 204
        httpx_mock.add_response(
            url=f"{base_url}/v1/projects/{project_id}",
            method="DELETE",
            status_code=204,
        )

        # The _handle_response should return None for 204
        result = client._request("DELETE", f"/v1/projects/{project_id}")
        assert result is None


class TestClientConfiguration:
    """Test various client configuration scenarios."""

    def test_custom_httpx_client(self, httpx_mock: HTTPXMock, base_url: str) -> None:
        """Client works with custom httpx client."""
        custom_client = httpx.Client(timeout=60.0)

        httpx_mock.add_response(
            url=f"{base_url}/v1/credits",
            json={"balance": 500},
        )

        client = Qualia(api_key="test-key", httpx_client=custom_client)

        # Custom client should be used (not owned by Qualia)
        assert client._owns_client is False

        balance = client.credits.get()
        assert balance.balance == 500

        # Close shouldn't close the custom client
        client.close()
        # custom_client should still be usable (not closed)

        custom_client.close()

    def test_base_url_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Client reads base URL from environment."""
        monkeypatch.setenv("QUALIA_BASE_URL", "https://custom.api.com")

        client = Qualia(api_key="test-key")
        assert client._base_url == "https://custom.api.com"
        client.close()


class TestJobCancellationWorkflow:
    """Test job cancellation scenarios."""

    def test_cancel_running_job(
        self, httpx_mock: HTTPXMock, client: Qualia, base_url: str
    ) -> None:
        """Cancel a running job and verify status."""
        job_id = "550e8400-e29b-41d4-a716-446655440000"

        # Create job
        httpx_mock.add_response(
            url=f"{base_url}/v1/finetune",
            method="POST",
            json={"job_id": job_id, "status": "queued", "message": None},
        )

        # Cancel job
        httpx_mock.add_response(
            url=f"{base_url}/v1/finetune/{job_id}/cancel",
            method="POST",
            json={"job_id": job_id, "cancelled": True, "message": "Job cancelled"},
        )

        # Check cancelled status
        httpx_mock.add_response(
            url=f"{base_url}/v1/finetune/{job_id}",
            json={
                "job_id": job_id,
                "current_phase": "cancelled",
                "status": "cancelled",
                "phases": [],
            },
        )

        job = client.finetune.create(
            project_id="660e8400-e29b-41d4-a716-446655440000",
            model_id="lerobot/smolvla_base",
            vla_type=VLAType.SMOLVLA,
            dataset_id="lerobot/pusht",
            hours=1.0,
            camera_mappings={"cam_1": "observation.images.top"},
        )

        cancel_result = client.finetune.cancel(job.job_id)
        assert cancel_result.cancelled is True

        status = client.finetune.get(job.job_id)
        assert status.status == "cancelled"


class TestProjectManagementWorkflow:
    """Test project lifecycle management."""

    def test_create_list_delete_project(
        self, httpx_mock: HTTPXMock, client: Qualia, base_url: str
    ) -> None:
        """Full project lifecycle: create, list, delete."""
        project_id = "550e8400-e29b-41d4-a716-446655440000"

        # Create
        httpx_mock.add_response(
            url=f"{base_url}/v1/projects",
            method="POST",
            json={"created": True, "project_id": project_id},
        )

        # List
        httpx_mock.add_response(
            url=f"{base_url}/v1/projects",
            method="GET",
            json={
                "data": [
                    {
                        "project_id": project_id,
                        "name": "Test Project",
                        "description": None,
                        "created_at": "2024-01-15T10:00:00Z",
                        "jobs": [],
                    }
                ]
            },
        )

        # Delete
        httpx_mock.add_response(
            url=f"{base_url}/v1/projects/{project_id}",
            method="DELETE",
            json={"deleted": True, "project_id": project_id},
        )

        # Execute workflow
        created = client.projects.create(name="Test Project")
        assert created.created is True

        projects = client.projects.list()
        assert len(projects) == 1
        assert projects[0].name == "Test Project"

        deleted = client.projects.delete(created.project_id)
        assert deleted.deleted is True
