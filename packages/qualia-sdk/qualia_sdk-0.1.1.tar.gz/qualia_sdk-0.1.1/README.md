# Qualia Python SDK

The official Python SDK for the [Qualia](https://app.qualiastudios.dev) VLA fine-tuning platform.

## Installation

```bash
pip install qualia-sdk
```

## Quick Start

```python
from qualia import Qualia

# Initialize the client
client = Qualia(api_key="your-api-key")

# Or use the QUALIA_API_KEY environment variable
client = Qualia()

# List available VLA models
models = client.models.list()
for model in models:
    print(f"{model.id}: {model.name}")
    print(f"  Camera slots: {model.camera_slots}")

# Create a project
project = client.projects.create(name="My Robot Project")
print(f"Created project: {project.project_id}")

# Get dataset image keys for camera mapping
image_keys = client.datasets.get_image_keys("lerobot/pusht")
print(f"Available keys: {image_keys.image_keys}")

# Start a finetune job
job = client.finetune.create(
    project_id=project.project_id,
    model_id="lerobot/smolvla_base",
    vla_type="smolvla",
    dataset_id="lerobot/pusht",
    hours=2.0,
    camera_mappings={"cam_1": "observation.images.top"},
)
print(f"Started job: {job.job_id}")

# Check job status
status = client.finetune.get(job.job_id)
print(f"Status: {status.status.status}")
print(f"Current phase: {status.status.current_phase}")

# Cancel a job if needed
result = client.finetune.cancel(job.job_id)
```

## Resources

### Credits

```python
# Get your credit balance
balance = client.credits.get()
print(f"Available credits: {balance.balance}")
```

### Datasets

```python
# Get image keys from a HuggingFace dataset
image_keys = client.datasets.get_image_keys("lerobot/pusht")
# Use these keys as values in camera_mappings
```

### Finetune

```python
# Create a finetune job
job = client.finetune.create(
    project_id="...",
    model_id="lerobot/smolvla_base",  # HuggingFace model ID
    vla_type="smolvla",                # smolvla, pi0, or pi0.5
    dataset_id="lerobot/pusht",        # HuggingFace dataset ID
    hours=2.0,                         # Training duration (max 168)
    camera_mappings={                  # Map model slots to dataset keys
        "cam_1": "observation.images.top",
    },
    # Optional parameters:
    instance_type="gpu_1x_a100",       # From client.instances.list()
    region="us-east-1",
    batch_size=32,
    name="My training run",
)

# Get job status
status = client.finetune.get(job.job_id)

# Cancel a job
result = client.finetune.cancel(job.job_id)
```

### Instances

```python
# List available GPU instances
instances = client.instances.list()
for inst in instances:
    print(f"{inst.id}: {inst.gpu_description} - {inst.credits_per_hour} credits/hr")
    print(f"  Specs: {inst.specs.gpu_count}x GPU, {inst.specs.memory_gib}GB RAM")
    print(f"  Regions: {[r.name for r in inst.regions]}")
```

### Models

```python
# List available VLA model types
models = client.models.list()
for model in models:
    print(f"{model.id}: {model.name}")
    print(f"  Base model: {model.base_model_id}")
    print(f"  Camera slots: {model.camera_slots}")
```

### Projects

```python
# Create a project
project = client.projects.create(
    name="My Project",
    description="Optional description",
)

# List all projects
projects = client.projects.list()
for p in projects:
    print(f"{p.name}: {len(p.jobs)} jobs")

# Delete a project (fails if it has active jobs)
client.projects.delete(project.project_id)
```

## Configuration

### Environment Variables

- `QUALIA_API_KEY`: Your API key (used if not passed to constructor)
- `QUALIA_BASE_URL`: Override the API base URL (default: `https://api.qualiastudios.dev`)

### Custom HTTP Client

```python
import httpx

# Use a custom httpx client for advanced configuration
custom_client = httpx.Client(
    timeout=60.0,
    limits=httpx.Limits(max_connections=10),
)

client = Qualia(api_key="...", httpx_client=custom_client)
```

### Context Manager

```python
# Automatically close the client when done
with Qualia(api_key="...") as client:
    models = client.models.list()
```

## Error Handling

```python
from qualia import (
    Qualia,
    QualiaError,
    QualiaAPIError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
)

try:
    client = Qualia(api_key="invalid-key")
    client.models.list()
except AuthenticationError as e:
    print(f"Auth failed: {e}")
except NotFoundError as e:
    print(f"Not found: {e}")
except ValidationError as e:
    print(f"Validation error: {e}")
except RateLimitError as e:
    print(f"Rate limited. Retry after: {e.retry_after}s")
except QualiaAPIError as e:
    print(f"API error [{e.status_code}]: {e.message}")
except QualiaError as e:
    print(f"SDK error: {e}")
```

## Requirements

- Python 3.10+
- httpx
- pydantic

## License

MIT
