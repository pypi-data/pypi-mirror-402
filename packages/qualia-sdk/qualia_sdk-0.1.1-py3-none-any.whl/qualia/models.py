"""
Qualia SDK Models

Pydantic models for API requests and responses.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

__all__ = [
    # Enums
    "VLAType",
    "VLA_TYPES_NO_CUSTOM_MODEL",
    # Credits
    "CreditBalance",
    # Datasets
    "DatasetImageKeys",
    # Finetune
    "FinetuneJob",
    "FinetuneStatus",
    "Phase",
    "PhaseEvent",
    "FinetuneCancelResult",
    # Instances
    "Instance",
    "InstanceRegion",
    "InstanceSpecs",
    # Models
    "VLAModel",
    # Projects
    "Project",
    "ProjectJob",
    "ProjectCreateResult",
    "ProjectDeleteResult",
]


# =============================================================================
# Enums
# =============================================================================


class VLAType(str, Enum):
    """Supported VLA model types."""

    ACT = "act"
    SMOLVLA = "smolvla"
    PI0 = "pi0"
    PI0_5 = "pi05"
    GROOT_N1_5 = "gr00t_n1_5"


# VLA types that don't support custom model_id (use fixed base models)
VLA_TYPES_NO_CUSTOM_MODEL = {VLAType.ACT, VLAType.GROOT_N1_5}


# =============================================================================
# Credits
# =============================================================================


class CreditBalance(BaseModel):
    """User's credit balance."""

    balance: int = Field(..., description="Total available credits")


# =============================================================================
# Datasets
# =============================================================================


class DatasetImageKeys(BaseModel):
    """Available image keys from a HuggingFace dataset."""

    dataset_id: str = Field(..., description="HuggingFace dataset ID")
    image_keys: list[str] = Field(
        ...,
        description="Available image keys (use as values in camera_mappings)",
    )


# =============================================================================
# Finetune
# =============================================================================


class PhaseEvent(BaseModel):
    """A single event within a training phase."""

    status: str | None = Field(
        None, description="Event status: started, completed, failed"
    )
    message: str | None = Field(None, description="Event message")
    error: str | None = Field(None, description="Error details if failed")
    timestamp: datetime = Field(..., description="Event timestamp")
    retry_attempt: int = Field(0, description="Retry attempt number")


class Phase(BaseModel):
    """A training phase with its events."""

    name: str = Field(..., description="Phase name")
    status: str = Field(
        ..., description="Phase status: pending, in_progress, completed, failed"
    )
    started_at: datetime | None = Field(None, description="When phase started")
    completed_at: datetime | None = Field(None, description="When phase completed")
    events: list[PhaseEvent] = Field(
        default_factory=list, description="Events in this phase"
    )
    error: str | None = Field(None, description="Error message if phase failed")


class FinetuneJob(BaseModel):
    """Response after creating a finetune job."""

    job_id: UUID = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Current job status")
    message: str | None = Field(None, description="Status message")


class FinetuneStatus(BaseModel):
    """Detailed status of a finetune job."""

    job_id: UUID = Field(..., description="Unique job identifier")
    current_phase: str = Field(..., description="Current phase name")
    status: str = Field(
        ...,
        description="Overall job status: queued, running, completed, failed, cancelled",
    )
    phases: list[Phase] = Field(default_factory=list, description="Phase history")


class FinetuneCancelResult(BaseModel):
    """Result of cancelling a finetune job."""

    job_id: UUID = Field(..., description="Cancelled job ID")
    cancelled: bool = Field(..., description="Whether cancellation was successful")
    message: str | None = Field(None, description="Status message")


# =============================================================================
# Instances
# =============================================================================


class InstanceRegion(BaseModel):
    """A region where an instance is available."""

    name: str = Field(..., description="Region identifier")
    description: str = Field(..., description="Human-readable region name")


class InstanceSpecs(BaseModel):
    """Hardware specifications for an instance."""

    vcpus: int = Field(..., description="Number of virtual CPUs")
    memory_gib: int = Field(..., description="Memory in GiB")
    storage_gib: int = Field(..., description="Storage in GiB")
    gpu_count: int = Field(..., description="Number of GPUs")
    gpu_type: str = Field(..., description="GPU model name")


class Instance(BaseModel):
    """A GPU instance type available for training."""

    id: str = Field(
        ..., description="Instance type ID (use when creating finetune jobs)"
    )
    name: str = Field(..., description="Instance flavor name")
    description: str = Field(..., description="Instance description")
    gpu_description: str = Field(..., description="Clean GPU description")
    credits_per_hour: int = Field(..., description="Cost in credits per hour")
    specs: InstanceSpecs = Field(..., description="Hardware specifications")
    regions: list[InstanceRegion] = Field(..., description="Available regions")
    region_count: int = Field(..., description="Number of available regions")


# =============================================================================
# Models
# =============================================================================


class VLAModel(BaseModel):
    """Information about an available VLA model type."""

    id: str = Field(..., description="VLA type ID (use as vla_type in finetune jobs)")
    name: str = Field(..., description="Display name")
    description: str = Field(..., description="Model description")
    base_model_id: str | None = Field(
        None,
        description="Default HuggingFace model ID. None for models that don't support custom base models.",
    )
    camera_slots: list[str] = Field(
        ...,
        description="Camera slot names that must be mapped in finetune jobs",
    )
    supports_custom_model: bool = Field(
        True,
        description="Whether this VLA type supports passing a custom model_id",
    )


# =============================================================================
# Projects
# =============================================================================


class ProjectJob(BaseModel):
    """Job summary within a project."""

    job_id: UUID = Field(..., description="Job ID")
    name: str | None = Field(None, description="Job name/description")
    model: str | None = Field(None, description="Model being fine-tuned")
    dataset: str | None = Field(None, description="Dataset used for training")
    status: str | None = Field(None, description="Current job status")
    created_at: datetime = Field(..., description="Creation timestamp")


class Project(BaseModel):
    """A project containing finetune jobs."""

    project_id: UUID = Field(..., description="Project ID")
    name: str = Field(..., description="Project name")
    description: str | None = Field(None, description="Project description")
    created_at: datetime = Field(..., description="Creation timestamp")
    jobs: list[ProjectJob] = Field(
        default_factory=list, description="Jobs in this project"
    )


class ProjectCreateResult(BaseModel):
    """Result of creating a project."""

    created: bool = Field(..., description="Whether the project was created")
    project_id: UUID = Field(..., description="ID of the created project")


class ProjectDeleteResult(BaseModel):
    """Result of deleting a project."""

    deleted: bool = Field(..., description="Whether the project was deleted")
    project_id: UUID = Field(..., description="ID of the deleted project")
