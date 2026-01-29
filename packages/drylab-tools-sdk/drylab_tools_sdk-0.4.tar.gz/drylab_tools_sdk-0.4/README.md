# drylab-tools-sdk

Python SDK for the Drylab API. Provides simple access to vault files, Nextflow jobs, and pipelines.

> **Note**: This SDK (`drylab-tools-sdk`) is for AI-generated code running inside sandboxes.

## Installation

```bash
pip install drylab-tools-sdk
```

## Quick Start

```python
from drylab_tools_sdk import DrylabClient

# Initialize client (reads DRYLAB_API_KEY from environment)
client = DrylabClient()

# List files in a project folder
result = client.vault.list("/MyProject/data")
for file in result.files:
    print(f"{file.filename} ({file.size} bytes)")

# Upload a file
upload = client.vault.upload("/MyProject/output", "results.csv", size=1024)
import requests
with open("results.csv", "rb") as f:
    requests.put(upload.presigned_url, data=f)

# Submit a Nextflow job
job = client.jobs.submit(
    pipeline_id="rnaseq",
    params={
        "input": "/MyProject/data/samplesheet.csv",
        "outdir": "/MyProject/results",
        "genome": "GRCh38"
    },
    compute_profile="aws-batch"
)
print(f"Submitted job: {job.id}")

# Check job status
job = client.jobs.get(job.id)
print(f"Status: {job.status}, Complete: {job.is_complete}")

# List available pipelines
pipelines = client.pipelines.list()
for p in pipelines:
    print(f"{p.id}: {p.name}")

# Get pipeline parameter schema
schema = client.pipelines.get_schema("rnaseq")
for field in schema.required_fields:
    print(f"Required: {field.name} ({field.type})")
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DRYLAB_API_KEY` | Yes | Execution token (injected by sandbox) |
| `DRYLAB_API_BASE_URL` | No | Backend URL (default: https://api.drylab.ai) |

## Documentation

For comprehensive documentation including:
- Authentication mechanism and token lifecycle
- Backend integration details
- Security considerations
- Error handling

See **[docs/drylab_tools_sdk.md](docs/drylab_tools_sdk.md)**

## API Reference

### Vault Operations

```python
# List files
result = client.vault.list("/Project/folder")

# Upload (get presigned URL)
upload = client.vault.upload("/Project/folder", "file.csv", size=1024)

# Upload file directly (convenience)
client.vault.upload_file("/Project/folder", "/local/path/file.csv")

# Download (get presigned URL)
download = client.vault.download("/Project/folder/file.csv")

# Download file directly (convenience)
client.vault.download_file("/local/path", vault_path="/Project/folder/file.csv")

# Download folder as zip
download = client.vault.download_folder("/Project/results")
```

### Job Operations

```python
# Submit job
job = client.jobs.submit("rnaseq", params={...}, compute_profile="aws-batch")

# Get job status
job = client.jobs.get(job.id)

# List jobs
jobs = client.jobs.list(status="running", limit=10)

# Cancel job
client.jobs.cancel(job.id)

# Wait for completion
job = client.jobs.wait_for_completion(job.id, timeout=3600)
```

### Pipeline Operations

```python
# List pipelines
pipelines = client.pipelines.list()

# Get pipeline details
pipeline = client.pipelines.get("rnaseq")

# Get parameter schema
schema = client.pipelines.get_schema("rnaseq")

# Register custom pipeline
pipeline = client.pipelines.register(
    name="my-pipeline",
    pipeline_zip_path="/Project/pipelines/my-pipeline.zip",
    schema={"fields": [...]}
)
```

## License

MIT
