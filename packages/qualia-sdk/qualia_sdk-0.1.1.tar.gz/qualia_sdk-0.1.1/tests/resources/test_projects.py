"""Tests for the Projects resource."""

from uuid import UUID

from pytest_httpx import HTTPXMock

from qualia import Qualia
from qualia.models import Project, ProjectCreateResult, ProjectDeleteResult


class TestProjectsResource:
    """Tests for ProjectsResource."""

    def test_create_minimal(
        self, httpx_mock: HTTPXMock, client: Qualia, base_url: str
    ) -> None:
        """create() with only name."""
        project_id = "550e8400-e29b-41d4-a716-446655440000"

        httpx_mock.add_response(
            url=f"{base_url}/v1/projects",
            method="POST",
            json={"created": True, "project_id": project_id},
        )

        result = client.projects.create(name="My Robot Project")

        assert isinstance(result, ProjectCreateResult)
        assert result.created is True
        assert result.project_id == UUID(project_id)

        # Verify request body
        request = httpx_mock.get_request()
        assert request is not None
        body = request.content.decode()
        assert "My Robot Project" in body
        assert "description" not in body

    def test_create_with_description(
        self, httpx_mock: HTTPXMock, client: Qualia, base_url: str
    ) -> None:
        """create() with name and description."""
        project_id = "550e8400-e29b-41d4-a716-446655440000"

        httpx_mock.add_response(
            url=f"{base_url}/v1/projects",
            method="POST",
            json={"created": True, "project_id": project_id},
        )

        result = client.projects.create(
            name="Robot Arm Project",
            description="Fine-tuning for our 6-DOF robot arm",
        )

        assert result.created is True

        # Verify description in request
        request = httpx_mock.get_request()
        assert request is not None
        body = request.content.decode()
        assert "6-DOF" in body

    def test_list(self, httpx_mock: HTTPXMock, client: Qualia, base_url: str) -> None:
        """list() returns all projects."""
        project_id = "550e8400-e29b-41d4-a716-446655440000"

        httpx_mock.add_response(
            url=f"{base_url}/v1/projects",
            json={
                "data": [
                    {
                        "project_id": project_id,
                        "name": "Project Alpha",
                        "description": "First project",
                        "created_at": "2024-01-15T10:00:00Z",
                        "jobs": [
                            {
                                "job_id": "660e8400-e29b-41d4-a716-446655440000",
                                "name": "Training Run 1",
                                "model": "smolvla",
                                "dataset": "lerobot/pusht",
                                "status": "completed",
                                "created_at": "2024-01-15T11:00:00Z",
                            }
                        ],
                    }
                ]
            },
        )

        projects = client.projects.list()

        assert len(projects) == 1
        assert isinstance(projects[0], Project)
        assert projects[0].project_id == UUID(project_id)
        assert projects[0].name == "Project Alpha"
        assert len(projects[0].jobs) == 1
        assert projects[0].jobs[0].status == "completed"

    def test_list_empty(
        self, httpx_mock: HTTPXMock, client: Qualia, base_url: str
    ) -> None:
        """list() handles empty response."""
        httpx_mock.add_response(
            url=f"{base_url}/v1/projects",
            json={"data": []},
        )

        projects = client.projects.list()
        assert projects == []

    def test_delete(self, httpx_mock: HTTPXMock, client: Qualia, base_url: str) -> None:
        """delete() deletes a project."""
        project_id = "550e8400-e29b-41d4-a716-446655440000"

        httpx_mock.add_response(
            url=f"{base_url}/v1/projects/{project_id}",
            method="DELETE",
            json={"deleted": True, "project_id": project_id},
        )

        result = client.projects.delete(project_id)

        assert isinstance(result, ProjectDeleteResult)
        assert result.deleted is True
        assert result.project_id == UUID(project_id)

    def test_delete_with_uuid(
        self, httpx_mock: HTTPXMock, client: Qualia, base_url: str
    ) -> None:
        """delete() accepts UUID object."""
        project_id = UUID("550e8400-e29b-41d4-a716-446655440000")

        httpx_mock.add_response(
            url=f"{base_url}/v1/projects/{project_id}",
            method="DELETE",
            json={"deleted": True, "project_id": str(project_id)},
        )

        result = client.projects.delete(project_id)
        assert result.deleted is True
