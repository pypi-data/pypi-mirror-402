"""
Projects resource for the Qualia API.
"""

from __future__ import annotations

from uuid import UUID

from ..models import Project, ProjectCreateResult, ProjectDeleteResult
from .base import BaseResource

__all__ = ["ProjectsResource"]


class ProjectsResource(BaseResource):
    """
    Create and manage projects.

    Projects are used to organize finetune jobs.

    Usage:
        ```python
        # Create a project
        result = client.projects.create(name="My Robot Project")
        print(f"Created project: {result.project_id}")

        # List all projects
        projects = client.projects.list()
        for project in projects:
            print(f"{project.name}: {len(project.jobs)} jobs")

        # Delete a project
        client.projects.delete(result.project_id)
        ```
    """

    def create(
        self,
        *,
        name: str,
        description: str | None = None,
    ) -> ProjectCreateResult:
        """
        Create a new project.

        Args:
            name: Project name (1-255 characters).
            description: Optional project description (max 1000 characters).

        Returns:
            ProjectCreateResult: Contains the created project's ID.
        """
        body = {"name": name}
        if description is not None:
            body["description"] = description

        data = self._post("/v1/projects", json=body)
        return ProjectCreateResult.model_validate(data)

    def list(self) -> list[Project]:
        """
        List all projects for the current user.

        Returns:
            list[Project]: All projects with their associated jobs.
        """
        data = self._get("/v1/projects")
        return [Project.model_validate(item) for item in data.get("data", [])]

    def delete(self, project_id: UUID | str) -> ProjectDeleteResult:
        """
        Delete a project.

        This will fail if the project has active finetune jobs.

        Args:
            project_id: The project ID to delete.

        Returns:
            ProjectDeleteResult: Confirmation of deletion.

        Raises:
            NotFoundError: If the project is not found.
            QualiaAPIError: If the project has active jobs.
        """
        data = self._delete(f"/v1/projects/{project_id}")
        return ProjectDeleteResult.model_validate(data)
