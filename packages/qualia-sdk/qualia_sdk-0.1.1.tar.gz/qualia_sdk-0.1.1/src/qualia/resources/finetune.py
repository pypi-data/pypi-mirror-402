"""
Finetune resource for the Qualia API.
"""

from __future__ import annotations

from uuid import UUID

from ..models import (
    VLA_TYPES_NO_CUSTOM_MODEL,
    FinetuneCancelResult,
    FinetuneJob,
    FinetuneStatus,
    VLAType,
)
from .base import BaseResource

__all__ = ["FinetuneResource"]


class FinetuneResource(BaseResource):
    """
    Create and manage finetune jobs.

    Usage:
        ```python
        # Create a finetune job
        job = client.finetune.create(
            project_id="...",
            model_id="lerobot/smolvla_base",
            vla_type="smolvla",
            dataset_id="lerobot/pusht",
            hours=2.0,
            camera_mappings={"cam_1": "observation.images.top"},
        )

        # Check status
        status = client.finetune.get(job.job_id)

        # Cancel if needed
        result = client.finetune.cancel(job.job_id)
        ```
    """

    def create(
        self,
        *,
        project_id: UUID | str,
        vla_type: VLAType | str,
        dataset_id: str,
        hours: float,
        camera_mappings: dict[str, str],
        model_id: str | None = None,
        instance_type: str | None = None,
        region: str | None = None,
        batch_size: int = 32,
        name: str | None = None,
    ) -> FinetuneJob:
        """
        Start a new finetune job.

        Args:
            project_id: Project ID to associate the job with.
            vla_type: VLA model type ("smolvla", "pi0", "pi05", "act", "gr00t_n1_5").
            dataset_id: HuggingFace dataset ID (e.g., "lerobot/pusht").
            hours: Training duration in hours (max 168).
            camera_mappings: Mapping from model camera slots to dataset image keys.
            model_id: HuggingFace model ID to finetune (e.g., "lerobot/smolvla_base").
                Required for smolvla, pi0, pi05. Must NOT be provided for act, gr00t_n1_5.
            instance_type: GPU instance type from /v1/instances. If not specified,
                cheapest available is used.
            region: Cloud region. If not specified, best available is selected.
            batch_size: Training batch size (default: 32, range: 1-512).
            name: Job name/description. Defaults to "SDK Job - {vla_type}".

        Returns:
            FinetuneJob: The created finetune job with job_id and status.

        Raises:
            ValueError: If model_id validation fails for the vla_type.
            ValidationError: If camera_mappings are invalid for the dataset.
            QualiaAPIError: If job creation fails.
        """
        # Convert enum to string value if needed
        vla_type_enum = VLAType(vla_type) if isinstance(vla_type, str) else vla_type
        vla_type_str = vla_type_enum.value

        # Validate model_id based on vla_type
        if vla_type_enum in VLA_TYPES_NO_CUSTOM_MODEL:
            if model_id is not None:
                raise ValueError(
                    f"model_id must not be provided for {vla_type_str}. "
                    "This model type uses a fixed base model."
                )
        else:
            if model_id is None:
                raise ValueError(f"model_id is required for {vla_type_str}.")

        body: dict = {
            "project_id": str(project_id),
            "vla_type": vla_type_str,
            "dataset_id": dataset_id,
            "hours": hours,
            "camera_mappings": camera_mappings,
            "batch_size": batch_size,
        }

        if model_id is not None:
            body["model_id"] = model_id
        if instance_type is not None:
            body["instance_type"] = instance_type
        if region is not None:
            body["region"] = region
        if name is not None:
            body["name"] = name

        data = self._post("/v1/finetune", json=body)
        return FinetuneJob.model_validate(data)

    def get(self, job_id: UUID | str) -> FinetuneStatus:
        """
        Get the status of a finetune job.

        Args:
            job_id: The job ID to check.

        Returns:
            FinetuneStatus: Detailed job status with phase history.

        Raises:
            NotFoundError: If the job is not found.
        """
        data = self._get(f"/v1/finetune/{job_id}")
        return FinetuneStatus.model_validate(data)

    def cancel(self, job_id: UUID | str) -> FinetuneCancelResult:
        """
        Cancel a finetune job.

        Stops the training job if it's still running and triggers credit finalization.

        Args:
            job_id: The job ID to cancel.

        Returns:
            FinetuneCancelResult: Confirmation of cancellation.

        Raises:
            NotFoundError: If the job is not found.
        """
        data = self._post(f"/v1/finetune/{job_id}/cancel")
        return FinetuneCancelResult.model_validate(data)
