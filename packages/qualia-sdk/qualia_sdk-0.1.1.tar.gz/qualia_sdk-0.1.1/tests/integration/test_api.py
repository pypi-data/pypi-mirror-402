"""Integration tests against the dev API.

These tests verify the SDK works correctly against the real dev API.
Run with: pytest tests/integration -v -m integration

Requires .env file with:
    QUALIA_TEST_API_KEY=your-dev-api-key
"""

import pytest

from qualia import Qualia
from qualia.exceptions import AuthenticationError, QualiaAPIError
from qualia.models import (
    CreditBalance,
    DatasetImageKeys,
    Instance,
    Project,
    ProjectCreateResult,
    ProjectDeleteResult,
    VLAModel,
)


@pytest.mark.integration
class TestCreditsIntegration:
    """Integration tests for credits endpoint."""

    def test_get_credits(self, integration_client: Qualia) -> None:
        """Can fetch credit balance from dev API."""
        balance = integration_client.credits.get()

        assert isinstance(balance, CreditBalance)
        assert isinstance(balance.balance, int)
        assert balance.balance >= 0


@pytest.mark.integration
class TestModelsIntegration:
    """Integration tests for models endpoint."""

    def test_list_models(self, integration_client: Qualia) -> None:
        """Can list available VLA models from dev API."""
        models = integration_client.models.list()

        assert isinstance(models, list)
        # Dev should have at least one model available
        assert len(models) > 0
        assert all(isinstance(m, VLAModel) for m in models)

        # Verify model structure
        model = models[0]
        assert model.id
        assert model.name
        assert model.base_model_id
        assert isinstance(model.camera_slots, list)


@pytest.mark.integration
class TestInstancesIntegration:
    """Integration tests for instances endpoint."""

    def test_list_instances(self, integration_client: Qualia) -> None:
        """Can list available GPU instances from dev API."""
        instances = integration_client.instances.list()

        assert isinstance(instances, list)
        # Dev should have at least one instance type
        assert len(instances) > 0
        assert all(isinstance(i, Instance) for i in instances)

        # Verify instance structure
        instance = instances[0]
        assert instance.id
        assert instance.gpu_description
        assert instance.specs.gpu_count > 0
        assert instance.credits_per_hour > 0
        assert isinstance(instance.regions, list)


@pytest.mark.integration
class TestDatasetsIntegration:
    """Integration tests for datasets endpoint."""

    def test_get_image_keys(self, integration_client: Qualia) -> None:
        """Can fetch image keys for a known dataset."""
        # Using a well-known LeRobot dataset that should exist
        keys = integration_client.datasets.get_image_keys("lerobot/pusht")

        assert isinstance(keys, DatasetImageKeys)
        assert keys.dataset_id == "lerobot/pusht"
        assert isinstance(keys.image_keys, list)
        assert len(keys.image_keys) > 0

    def test_get_image_keys_invalid_dataset(self, integration_client: Qualia) -> None:
        """Handles non-existent dataset gracefully."""
        with pytest.raises(QualiaAPIError):
            integration_client.datasets.get_image_keys("nonexistent/fake-dataset-12345")


@pytest.mark.integration
class TestProjectsIntegration:
    """Integration tests for projects endpoint."""

    def test_project_lifecycle(self, integration_client: Qualia) -> None:
        """Can create, list, and delete a project."""
        # Create
        project_name = "SDK Integration Test Project"
        result = integration_client.projects.create(
            name=project_name,
            description="Created by SDK integration tests - safe to delete",
        )

        assert isinstance(result, ProjectCreateResult)
        assert result.created is True
        assert result.project_id is not None

        project_id = result.project_id

        try:
            # List and verify our project exists
            projects = integration_client.projects.list()
            assert isinstance(projects, list)
            assert all(isinstance(p, Project) for p in projects)

            our_project = next((p for p in projects if p.project_id == project_id), None)
            assert our_project is not None
            assert our_project.name == project_name

        finally:
            # Clean up - delete the project
            delete_result = integration_client.projects.delete(project_id)
            assert isinstance(delete_result, ProjectDeleteResult)
            assert delete_result.deleted is True


@pytest.mark.integration
class TestAuthenticationIntegration:
    """Integration tests for authentication."""

    def test_invalid_api_key(self) -> None:
        """Invalid API key returns authentication error."""
        client = Qualia(
            api_key="invalid-api-key-12345",
            base_url="https://dev-api.qualiastudios.dev",
        )

        with pytest.raises(AuthenticationError):
            client.credits.get()

        client.close()


@pytest.mark.integration
class TestFullWorkflowIntegration:
    """Integration test for a realistic SDK workflow."""

    def test_exploration_workflow(self, integration_client: Qualia) -> None:
        """Test a typical user exploration workflow.

        This simulates a user exploring the API before starting a training job:
        1. Check available credits
        2. List available models and their camera requirements
        3. List available instances and pricing
        4. Check dataset compatibility
        """
        # 1. Check credits
        credits = integration_client.credits.get()
        assert credits.balance >= 0

        # 2. Explore models
        models = integration_client.models.list()
        assert len(models) > 0

        # Find a model and check its camera slots
        model = models[0]
        assert len(model.camera_slots) > 0

        # 3. Check instances
        instances = integration_client.instances.list()
        assert len(instances) > 0

        # Find cheapest instance
        cheapest = min(instances, key=lambda i: i.credits_per_hour)
        assert cheapest.credits_per_hour > 0

        # 4. Check a dataset's image keys
        image_keys = integration_client.datasets.get_image_keys("lerobot/pusht")
        assert len(image_keys.image_keys) > 0
