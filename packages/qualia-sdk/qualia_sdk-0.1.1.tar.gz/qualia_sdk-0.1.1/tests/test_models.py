"""Tests for Pydantic models."""

from uuid import UUID

from qualia.models import (
    CreditBalance,
    DatasetImageKeys,
    FinetuneCancelResult,
    FinetuneJob,
    FinetuneStatus,
    Instance,
    Phase,
    PhaseEvent,
    Project,
    ProjectCreateResult,
    ProjectDeleteResult,
    ProjectJob,
    VLAModel,
    VLAType,
)


class TestVLAType:
    """Tests for VLAType enum."""

    def test_values(self) -> None:
        """VLAType has expected values."""
        assert VLAType.ACT.value == "act"
        assert VLAType.SMOLVLA.value == "smolvla"
        assert VLAType.PI0.value == "pi0"
        assert VLAType.PI0_5.value == "pi05"
        assert VLAType.GROOT_N1_5.value == "gr00t_n1_5"


class TestCreditBalance:
    """Tests for CreditBalance model."""

    def test_parse(self) -> None:
        """CreditBalance parses from dict."""
        data = {"balance": 1000}
        balance = CreditBalance.model_validate(data)
        assert balance.balance == 1000


class TestDatasetImageKeys:
    """Tests for DatasetImageKeys model."""

    def test_parse(self) -> None:
        """DatasetImageKeys parses from dict."""
        data = {
            "dataset_id": "lerobot/pusht",
            "image_keys": ["observation.images.top", "observation.images.side"],
        }
        keys = DatasetImageKeys.model_validate(data)
        assert keys.dataset_id == "lerobot/pusht"
        assert len(keys.image_keys) == 2


class TestPhaseEvent:
    """Tests for PhaseEvent model."""

    def test_parse_minimal(self) -> None:
        """PhaseEvent parses with minimal data."""
        data = {"timestamp": "2024-01-15T10:30:00Z"}
        event = PhaseEvent.model_validate(data)
        assert event.status is None
        assert event.message is None
        assert event.error is None
        assert event.retry_attempt == 0

    def test_parse_full(self) -> None:
        """PhaseEvent parses with all fields."""
        data = {
            "status": "completed",
            "message": "Phase finished",
            "error": None,
            "timestamp": "2024-01-15T10:30:00Z",
            "retry_attempt": 1,
        }
        event = PhaseEvent.model_validate(data)
        assert event.status == "completed"
        assert event.message == "Phase finished"
        assert event.retry_attempt == 1


class TestPhase:
    """Tests for Phase model."""

    def test_parse_minimal(self) -> None:
        """Phase parses with minimal data."""
        data = {"name": "training", "status": "pending"}
        phase = Phase.model_validate(data)
        assert phase.name == "training"
        assert phase.status == "pending"
        assert phase.events == []
        assert phase.started_at is None

    def test_parse_full(self) -> None:
        """Phase parses with all fields."""
        data = {
            "name": "training",
            "status": "completed",
            "started_at": "2024-01-15T10:00:00Z",
            "completed_at": "2024-01-15T12:00:00Z",
            "events": [{"timestamp": "2024-01-15T10:00:00Z", "status": "started"}],
            "error": None,
        }
        phase = Phase.model_validate(data)
        assert phase.completed_at is not None
        assert len(phase.events) == 1


class TestFinetuneJob:
    """Tests for FinetuneJob model."""

    def test_parse(self) -> None:
        """FinetuneJob parses from dict."""
        job_id = "550e8400-e29b-41d4-a716-446655440000"
        data = {"job_id": job_id, "status": "queued", "message": "Job created"}
        job = FinetuneJob.model_validate(data)
        assert job.job_id == UUID(job_id)
        assert job.status == "queued"
        assert job.message == "Job created"


class TestFinetuneStatus:
    """Tests for FinetuneStatus model."""

    def test_parse(self) -> None:
        """FinetuneStatus parses flat API response."""
        job_id = "550e8400-e29b-41d4-a716-446655440000"
        # API returns flat response
        data = {
            "job_id": job_id,
            "current_phase": "training",
            "status": "running",
            "phases": [],
        }
        status = FinetuneStatus.model_validate(data)
        assert status.job_id == UUID(job_id)
        assert status.status == "running"
        assert status.current_phase == "training"
        assert status.phases == []


class TestFinetuneCancelResult:
    """Tests for FinetuneCancelResult model."""

    def test_parse(self) -> None:
        """FinetuneCancelResult parses from dict."""
        job_id = "550e8400-e29b-41d4-a716-446655440000"
        data = {"job_id": job_id, "cancelled": True, "message": "Job cancelled"}
        result = FinetuneCancelResult.model_validate(data)
        assert result.job_id == UUID(job_id)
        assert result.cancelled is True


class TestInstance:
    """Tests for Instance model."""

    def test_parse(self) -> None:
        """Instance parses from dict."""
        data = {
            "id": "n3-A100x1",
            "name": "n3-A100x1",
            "description": "NVIDIA A100 80GB x1",
            "gpu_description": "NVIDIA A100 80GB",
            "credits_per_hour": 250,
            "specs": {
                "vcpus": 12,
                "memory_gib": 85,
                "storage_gib": 500,
                "gpu_count": 1,
                "gpu_type": "NVIDIA A100 80GB",
            },
            "regions": [
                {"name": "CANADA-1", "description": "Canada"},
                {"name": "NORWAY-1", "description": "Norway"},
            ],
            "region_count": 2,
        }
        instance = Instance.model_validate(data)
        assert instance.id == "n3-A100x1"
        assert instance.specs.gpu_count == 1
        assert instance.credits_per_hour == 250
        assert len(instance.regions) == 2
        assert instance.regions[0].name == "CANADA-1"


class TestVLAModel:
    """Tests for VLAModel model."""

    def test_parse(self) -> None:
        """VLAModel parses from dict."""
        data = {
            "id": "smolvla",
            "name": "SmolVLA",
            "description": "Small VLA model",
            "base_model_id": "lerobot/smolvla_base",
            "camera_slots": ["cam_1", "cam_2"],
        }
        model = VLAModel.model_validate(data)
        assert model.id == "smolvla"
        assert len(model.camera_slots) == 2


class TestProjectJob:
    """Tests for ProjectJob model."""

    def test_parse_minimal(self) -> None:
        """ProjectJob parses with minimal data."""
        job_id = "550e8400-e29b-41d4-a716-446655440000"
        data = {"job_id": job_id, "created_at": "2024-01-15T10:00:00Z"}
        job = ProjectJob.model_validate(data)
        assert job.job_id == UUID(job_id)
        assert job.name is None

    def test_parse_full(self) -> None:
        """ProjectJob parses with all fields."""
        job_id = "550e8400-e29b-41d4-a716-446655440000"
        data = {
            "job_id": job_id,
            "name": "Test Job",
            "model": "smolvla",
            "dataset": "lerobot/pusht",
            "status": "running",
            "created_at": "2024-01-15T10:00:00Z",
        }
        job = ProjectJob.model_validate(data)
        assert job.name == "Test Job"
        assert job.status == "running"


class TestProject:
    """Tests for Project model."""

    def test_parse(self) -> None:
        """Project parses from dict."""
        project_id = "550e8400-e29b-41d4-a716-446655440000"
        data = {
            "project_id": project_id,
            "name": "My Project",
            "description": "Test project",
            "created_at": "2024-01-15T10:00:00Z",
            "jobs": [],
        }
        project = Project.model_validate(data)
        assert project.project_id == UUID(project_id)
        assert project.name == "My Project"
        assert project.jobs == []


class TestProjectCreateResult:
    """Tests for ProjectCreateResult model."""

    def test_parse(self) -> None:
        """ProjectCreateResult parses from dict."""
        project_id = "550e8400-e29b-41d4-a716-446655440000"
        data = {"created": True, "project_id": project_id}
        result = ProjectCreateResult.model_validate(data)
        assert result.created is True
        assert result.project_id == UUID(project_id)


class TestProjectDeleteResult:
    """Tests for ProjectDeleteResult model."""

    def test_parse(self) -> None:
        """ProjectDeleteResult parses from dict."""
        project_id = "550e8400-e29b-41d4-a716-446655440000"
        data = {"deleted": True, "project_id": project_id}
        result = ProjectDeleteResult.model_validate(data)
        assert result.deleted is True
        assert result.project_id == UUID(project_id)
