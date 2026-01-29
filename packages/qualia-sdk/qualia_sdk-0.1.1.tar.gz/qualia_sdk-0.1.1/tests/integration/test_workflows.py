"""Integration workflow tests that run real training jobs.

These tests run actual training workflows against the dev API.
They are meant to be run on merge to master to validate end-to-end functionality.

Run with: pytest tests/integration/test_workflows.py -v -m integration_workflow

Requires environment variables:
    QUALIA_TEST_API_KEY: API key for dev environment
    QUALIA_TEST_BASE_URL: https://dev-api.qualiastudios.dev
"""

import concurrent.futures
import time

import pytest

from qualia import Qualia
from qualia.models import FinetuneJob, FinetuneStatus

# Terminal states for job polling
TERMINAL_STATES = {"completed", "failed", "cancelled"}

# Polling configuration
POLL_INTERVAL_SECONDS = 10
POLL_TIMEOUT_SECONDS = 1800  # 30 minutes max per job


def wait_for_terminal_state(
    client: Qualia,
    job_id: str,
    timeout: int = POLL_TIMEOUT_SECONDS,
    interval: int = POLL_INTERVAL_SECONDS,
) -> FinetuneStatus:
    """Poll job status until it reaches a terminal state."""
    start_time = time.time()

    while True:
        status = client.finetune.get(job_id)
        current_phase = status.current_phase.lower()

        print(
            f"[POLL] job_id={job_id} current_phase={current_phase} status={status.status}"
        )

        if current_phase in TERMINAL_STATES:
            return status

        elapsed = time.time() - start_time
        if elapsed >= timeout:
            raise TimeoutError(
                f"Job {job_id} did not reach terminal state within {timeout}s. "
                f"Current phase: {current_phase}"
            )

        time.sleep(interval)


@pytest.mark.integration_workflow
class TestTrainingWorkflows:
    """Run real training jobs for all available models."""

    def _run_training_for_model(self, integration_client: Qualia, model_id: str) -> None:
        """Helper to run a training job for a specific model."""
        models = integration_client.models.list()
        model = next((m for m in models if m.id == model_id), None)
        assert model is not None, f"Model {model_id} not found"

        image_keys = integration_client.datasets.get_image_keys("lerobot/pusht")
        assert len(image_keys.image_keys) > 0

        # Create project for this model
        project = integration_client.projects.create(
            name=f"SDK Workflow Test - {model.id}",
            description=f"Integration test - {model.id} training",
        )
        project_id = project.project_id

        final_status = None
        try:
            # Build camera mappings
            camera_mappings = {
                slot: image_keys.image_keys[0] for slot in model.camera_slots
            }

            # Build finetune args - only include model_id if model supports custom models
            finetune_args = {
                "project_id": project_id,
                "vla_type": model.id,
                "dataset_id": "lerobot/pusht",
                "hours": 0.01,
                "camera_mappings": camera_mappings,
                "name": f"SDK Workflow Test - {model.id}",
            }
            if model.supports_custom_model:
                finetune_args["model_id"] = model.base_model_id

            # Start training
            job = integration_client.finetune.create(**finetune_args)

            assert isinstance(job, FinetuneJob)
            assert job.job_id is not None

            # Wait for completion
            final_status = wait_for_terminal_state(
                integration_client,
                str(job.job_id),
            )

            assert isinstance(final_status, FinetuneStatus)
            assert final_status.job_id == job.job_id
            assert final_status.current_phase.lower() == "completed", (
                f"Job failed with phase: {final_status.current_phase}, status: {final_status.status}"
            )

        finally:
            # Only delete project if job completed successfully
            if final_status and final_status.current_phase.lower() == "completed":
                integration_client.projects.delete(project_id)

    def test_all_models_parallel(self, integration_client: Qualia) -> None:
        """Run training jobs for all models in parallel."""
        model_ids = ["smolvla", "pi0", "pi05", "gr00t_n1_5", "act"]

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(model_ids)
        ) as executor:
            futures = {
                executor.submit(
                    self._run_training_for_model, integration_client, model_id
                ): model_id
                for model_id in model_ids
            }
            results = {}
            for future in concurrent.futures.as_completed(futures):
                model_id = futures[future]
                try:
                    future.result()
                    results[model_id] = None
                except Exception as e:
                    results[model_id] = str(e)

        failed = {k: v for k, v in results.items() if v is not None}
        assert len(failed) == 0, f"Jobs failed: {failed}"
