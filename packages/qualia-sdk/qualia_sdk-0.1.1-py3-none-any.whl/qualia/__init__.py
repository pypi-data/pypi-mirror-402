"""
Qualia SDK

Python SDK for the Qualia Studios VLA fine-tuning platform.

Usage:
    ```python
    from qualia import Qualia

    client = Qualia(api_key="your-api-key")

    # List available models
    models = client.models.list()

    # Create a project
    project = client.projects.create(name="My Robot Project")

    # Get dataset image keys for camera mapping
    image_keys = client.datasets.get_image_keys("lerobot/pusht")

    # Start a finetune job
    job = client.finetune.create(
        project_id=project.project_id,
        model_id="lerobot/smolvla_base",
        vla_type="smolvla",
        dataset_id="lerobot/pusht",
        hours=2.0,
        camera_mappings={"cam_1": "observation.images.top"},
    )

    # Check status
    status = client.finetune.get(job.job_id)
    print(f"Status: {status.status}")
    ```
"""

from .client import Qualia
from .exceptions import (
    AuthenticationError,
    NotFoundError,
    QualiaAPIError,
    QualiaError,
    RateLimitError,
    ValidationError,
)
from .models import (
    CreditBalance,
    DatasetImageKeys,
    FinetuneCancelResult,
    FinetuneJob,
    FinetuneStatus,
    Instance,
    InstanceRegion,
    InstanceSpecs,
    Phase,
    PhaseEvent,
    Project,
    ProjectCreateResult,
    ProjectDeleteResult,
    ProjectJob,
    VLAModel,
    VLAType,
)

__version__ = "0.1.1"

__all__ = [
    # Client
    "Qualia",
    # Exceptions
    "QualiaError",
    "QualiaAPIError",
    "AuthenticationError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    # Models
    "VLAType",
    "CreditBalance",
    "DatasetImageKeys",
    "FinetuneJob",
    "FinetuneStatus",
    "Phase",
    "PhaseEvent",
    "FinetuneCancelResult",
    "Instance",
    "InstanceRegion",
    "InstanceSpecs",
    "VLAModel",
    "Project",
    "ProjectJob",
    "ProjectCreateResult",
    "ProjectDeleteResult",
]
