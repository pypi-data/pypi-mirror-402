# Drylab Client SDK

## Overview

`drylab_tools_sdk` is a Python SDK that enables AI-generated code running inside Drylab sandboxes to interact with the Drylab backend. It provides simple, semantic access to:

- **Vault**: File storage operations (upload, download, list)
- **Jobs**: Nextflow job management (submit, status, cancel, wait)
- **Pipelines**: Pipeline registry (list, schema, register)

> **Note**: This SDK (`drylab-tools-sdk`) is different from `drylab-runtime-sdk`:
> - `drylab-tools-sdk`: For AI-generated code to interact with backend APIs
> - `drylab-runtime-sdk`: For LangGraph agents to manage sandboxes and kernels

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DRYLAB PLATFORM                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐     1. Provision Token      ┌──────────────────────────┐  │
│  │              │ ───────────────────────────►│                          │  │
│  │  LangGraph   │                             │    Drylab Backend        │  │
│  │    Agent     │◄─────────────────────────── │                          │  │
│  │              │     JWT (drylab_sk_xxx)     │  - /api/v1/agent/*       │  │
│  └──────┬───────┘                             │  - /api/v1/ai/vault/*    │  │
│         │                                     │  - /api/v1/ai/nextflow/* │  │
│         │ 2. Inject Token                     │                          │  │
│         │    as DRYLAB_API_KEY                └──────────────────────────┘  │
│         │                                                ▲                  │
│         ▼                                                │                  │
│  ┌──────────────────────────────────────┐                │                  │
│  │            Sandbox                   │                │                  │
│  │  ┌────────────────────────────────┐  │                │                  │
│  │  │  AI-Generated Python Code      │  │                │                  │
│  │  │                                │  │                │                  │
│  │  │  from drylab_tools_sdk import │  │   3. API       │                  │
│  │  │      DrylabClient              │  │      Calls     │                  │
│  │  │                                │  │ ──────────────-┘                  │
│  │  │  client = DrylabClient()       │  │                                   │
│  │  │  files = client.vault.list()   │  │                                   │
│  │  │                                │  │                                   │
│  │  └────────────────────────────────┘  │                                   │
│  │                                      │                                   │
│  │  Environment:                        │                                   │
│  │  - DRYLAB_API_KEY=drylab_sk_xxx      │                                   │
│  │  - DRYLAB_API_BASE_URL=http://...    │                                   │
│  └──────────────────────────────────────┘                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Authentication Mechanism

### Token Types

The SDK uses **JWT (JSON Web Token)** based authentication with two modes:

| Mode | Token Format | User ID Source | Use Case |
|------|--------------|----------------|----------|
| **JWT (Preferred)** | `drylab_sk_<jwt>` | Extracted from token claims | New SDK-based authentication |
| **Legacy** | Static token | Must be in request body | Backward compatibility |

### JWT Token Structure

```json
{
  "type": "execution",
  "user_id": "uuid-of-user",
  "scopes": ["vault:*", "jobs:*", "pipelines:*"],
  "allowed_projects": null,
  "connection_key": "sandbox-connection-key",
  "environment_type": "modal",
  "iat": 1704067200,
  "exp": 1704081600,
  "jti": "unique-token-id"
}
```

### Token Claims

| Claim | Type | Description |
|-------|------|-------------|
| `type` | string | Always `"execution"` |
| `user_id` | UUID | The authenticated user |
| `scopes` | string[] | Allowed operations (e.g., `vault:*`, `jobs:submit`) |
| `allowed_projects` | UUID[] \| null | Restricted projects, or `null` for all |
| `connection_key` | string | Sandbox identifier for binding |
| `environment_type` | string | `sandbox`, `ec2`, `modal`, `local` |
| `iat` | int | Issued at (Unix timestamp) |
| `exp` | int | Expiration (Unix timestamp) |
| `jti` | string | Unique token ID for revocation |

### Scope System

Scopes control what operations the token can perform:

```
vault:*         - All vault operations
vault:read      - Read files only
vault:write     - Write files only

jobs:*          - All job operations
jobs:submit     - Submit jobs
jobs:cancel     - Cancel jobs

pipelines:*     - All pipeline operations
pipelines:read  - Read pipeline info
pipelines:write - Register pipelines

*               - Full access (legacy tokens)
```

---

## Token Lifecycle

### 1. Token Provisioning

When a LangGraph agent initializes tools, it provisions an execution token:

```python
# In tool_init.py (drylab-agents)
execution_token = provision_execution_token(
    user_id=str(user_id),
    connection_key=connection_key,
    environment_type=provider,
    ttl_hours=4,
)
```

**Backend Endpoint**: `POST /api/v1/agent/provision-token`

```json
// Request
{
  "user_id": "user-uuid",
  "scopes": ["vault:*", "jobs:*", "pipelines:*"],
  "connection_key": "sandbox-key",
  "environment_type": "modal",
  "ttl_hours": 4
}

// Response
{
  "token": "drylab_sk_eyJhbGciOiJIUzI1NiIs...",
  "token_id": "unique-token-id",
  "user_id": "user-uuid",
  "expires_in": 14400,
  "expires_at": 1704081600
}
```

### 2. Token Injection

The token is injected into the sandbox environment:

```python
# In tool_init.py
sandbox.run_code(f'''
import os
os.environ["DRYLAB_API_KEY"] = "{execution_token}"
os.environ["DRYLAB_API_BASE_URL"] = "{backend_url}"
''')
```

### 3. Token Usage

AI-generated code uses the SDK, which reads the token automatically:

```python
from drylab_tools_sdk import DrylabClient

client = DrylabClient()  # Reads DRYLAB_API_KEY from environment
# Token is sent as: Authorization: Bearer drylab_sk_xxx
```

### 4. Token Refresh

The SDK includes an auto-refresh daemon that renews tokens before expiry:

```python
# TokenManager (internal)
def _refresh(self):
    response = requests.post(
        f"{self._base_url}/api/v1/agent/refresh-token",
        headers={"Authorization": f"Bearer {self._api_key}"},
    )
    # Updates self._api_key and environment variable
```

**Backend Endpoint**: `POST /api/v1/agent/refresh-token`

- Accepts tokens up to 5 minutes past expiry
- Returns new token with same claims but fresh expiration
- Updates environment variable for child processes

### 5. Token Revocation

When a sandbox terminates, the token can be revoked:

**Backend Endpoint**: `POST /api/v1/agent/revoke-token`

```json
{
  "token_id": "unique-token-id"
}
```

Revoked tokens are stored in Redis and rejected on subsequent requests.

---

## SDK Usage

### Installation

```bash
cd /path/to/drylab_tools_sdk
pip install -e .
```

### Basic Usage

```python
from drylab_tools_sdk import DrylabClient

# Initialize (auto-reads DRYLAB_API_KEY)
client = DrylabClient()

# Or with explicit configuration
client = DrylabClient(
    api_key="drylab_sk_xxx",
    base_url="http://localhost:8000",
    auto_refresh=True,
    timeout=30,
)

# Use as context manager for cleanup
with DrylabClient() as client:
    files = client.vault.list("/MyProject/data")
```

### Vault Operations

```python
# List files in a folder
result = client.vault.list("/ProjectName/FolderPath")
for file in result.files:
    print(f"{file.filename} ({file.size} bytes)")
for folder in result.folders:
    print(f"[DIR] {folder.name}")

# Upload a file
upload = client.vault.upload(
    vault_path="/ProjectName/Output",
    filename="results.csv",
    size=1024,
)
# Use upload.presigned_url to PUT the file content

# Download a file
download = client.vault.download(vault_path="/ProjectName/data/input.fastq")
# Use download.url to GET the file content

# Download by file ID
download = client.vault.download(file_id="file-uuid")
```

### Job Operations

```python
# Submit a job
job = client.jobs.submit(
    pipeline_id="rnaseq",
    params={
        "input": "/MyProject/reads.fastq",
        "genome": "GRCh38",
    },
    compute_profile="aws-batch",
    project_id="project-uuid",  # Optional
)
print(f"Submitted job: {job.id}")

# Get job status
job = client.jobs.get(job_id="job-uuid")
print(f"Status: {job.status}, Progress: {job.progress}%")

# Wait for completion (blocking)
completed_job = client.jobs.wait_for_completion(
    job_id="job-uuid",
    poll_interval=10,  # seconds
    timeout=3600,      # max wait time
)

# Cancel a job
client.jobs.cancel(job_id="job-uuid")

# List jobs
jobs = client.jobs.list(
    status="running",   # Optional filter
    ai_only=True,       # Only AI-submitted jobs
    limit=20,
)
```

### Pipeline Operations

```python
# List available pipelines
pipelines = client.pipelines.list(
    include_public=True,
    include_user=True,
)
for p in pipelines:
    print(f"{p.id}: {p.name} ({p.source})")

# Get pipeline schema (parameters)
schema = client.pipelines.get_schema("rnaseq")
for field in schema.fields:
    print(f"  {field.name}: {field.type} (required={field.required})")

# Register custom pipeline
pipeline = client.pipelines.register(
    pipeline_zip_vault_path="/MyProject/pipelines/custom.zip",
    schema_json={"fields": [...]},
    pipeline_name="my-custom-pipeline",
    description="Custom analysis pipeline",
)
```

---

## Backend Integration

### AI-Exposed Routes

The SDK communicates with these backend endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/ai/vault/files/presigned-url` | POST | Get upload URL |
| `/api/v1/ai/vault/files/list` | POST | List files in folder |
| `/api/v1/ai/vault/files/download-url` | POST | Get download URL |
| `/api/v1/ai/vault/folders/download-zip` | POST | Download folder as zip |
| `/api/v1/ai/nextflow/jobs/submit-job` | POST | Submit job |
| `/api/v1/ai/nextflow/jobs/list` | POST | List jobs |
| `/api/v1/ai/nextflow/jobs/{id}/get` | POST | Get job details |
| `/api/v1/ai/nextflow/jobs/{id}/cancel` | POST | Cancel job |
| `/api/v1/ai/nextflow/pipelines/list` | POST | List pipelines |
| `/api/v1/ai/nextflow/pipelines/{id}/schema` | POST | Get schema |
| `/api/v1/ai/nextflow/pipelines/register` | POST | Register pipeline |

### Request Authentication

All requests include the JWT token:

```http
POST /api/v1/ai/vault/files/list HTTP/1.1
Host: api.drylab.ai
Authorization: Bearer drylab_sk_eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json

{
  "vault_path": "/MyProject/data"
}
```

Note: `user_id` is **not required** in the request body when using JWT tokens - it's extracted from the token claims.

### Backend Token Validation

The backend validates tokens in `ai_exposed_routes_helpers.py`:

```python
def validate_agent_token(authorization: str) -> TokenClaims:
    # 1. Check if JWT token (drylab_sk_ prefix or JWT format)
    if token.startswith("drylab_sk_") or _looks_like_jwt(token):
        return _validate_jwt_token(token)

    # 2. Legacy: Check against static token
    if token == settings.DRYLAB_AGENT_BACKEND_TOKEN:
        return TokenClaims(user_id=None, scopes=["*"], is_legacy=True)

    raise HTTPException(status_code=401, detail="Invalid token")
```

### Backward Compatibility

For legacy tokens (static `DRYLAB_AGENT_BACKEND_TOKEN`), `user_id` must still be provided in the request body:

```python
def get_user_id_from_request(claims: TokenClaims, request_user_id: UUID) -> UUID:
    if claims.user_id:
        return claims.user_id  # JWT token
    if claims.is_legacy and request_user_id:
        return request_user_id  # Legacy token
    raise HTTPException(status_code=400, detail="user_id required")
```

---

## Error Handling

### Exception Types

```python
from drylab_tools_sdk import (
    DrylabError,        # Base exception
    AuthenticationError, # Token invalid/expired
    ConfigurationError,  # Missing API key
    NotFoundError,       # Resource not found
    PermissionError,     # Access denied
    ValidationError,     # Invalid parameters
    RateLimitError,      # Too many requests
)
```

### Example Error Handling

```python
from drylab_tools_sdk import DrylabClient, NotFoundError, AuthenticationError

try:
    client = DrylabClient()
    job = client.jobs.get("non-existent-id")
except AuthenticationError as e:
    print(f"Token expired or invalid: {e}")
except NotFoundError as e:
    print(f"Job not found: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DRYLAB_API_KEY` | Yes | - | Execution token (JWT) |
| `DRYLAB_API_BASE_URL` | No | `https://api.drylab.ai` | Backend API URL |

### Client Options

```python
DrylabClient(
    api_key=None,        # Override DRYLAB_API_KEY
    base_url=None,       # Override DRYLAB_API_BASE_URL
    auto_refresh=True,   # Enable token auto-refresh
    timeout=30,          # HTTP timeout in seconds
)
```

---

## Security Considerations

1. **Token Scope**: Tokens are scoped to specific operations and optionally specific projects
2. **Token Expiration**: Default 4-hour TTL, auto-refresh before expiry
3. **Token Binding**: Tokens are bound to specific sandbox connections
4. **Revocation**: Tokens can be revoked when sandboxes terminate
5. **No Secrets in Code**: Token is injected via environment, not hardcoded

---

## File Structure

```
drylab_tools_sdk/
├── src/
│   └── drylab_tools_sdk/
│       ├── __init__.py          # Public API exports
│       ├── _version.py          # Version string
│       ├── client.py            # DrylabClient class
│       ├── _http.py             # HTTP client
│       ├── exceptions.py        # Exception classes
│       ├── auth/
│       │   ├── __init__.py
│       │   └── token.py         # TokenManager with auto-refresh
│       ├── resources/
│       │   ├── __init__.py
│       │   ├── base.py          # BaseResource class
│       │   ├── vault.py         # VaultResource
│       │   ├── jobs.py          # JobsResource
│       │   └── pipelines.py     # PipelinesResource
│       └── models/
│           ├── __init__.py
│           ├── vault.py         # VaultFile, UploadResult, etc.
│           ├── job.py           # Job, JobStatus
│           └── pipeline.py      # Pipeline, PipelineSchema
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Test fixtures
│   └── test_client.py           # Client tests
├── docs/
│   └── drylab_tools_sdk.md     # This documentation
├── pyproject.toml               # Package metadata
└── README.md                    # Quick start guide
```

---

## Related Components

| Component | Repository | Purpose |
|-----------|------------|---------|
| `drylab-backend` | `/drylab-backend` | FastAPI backend with AI-exposed routes |
| `drylab-agents` | `/drylab-agents` | LangGraph agents that provision tokens |
| `drylab-runtime-sdk` | - | SDK for managing sandboxes (separate from this SDK) |

### Backend Files

- `src/routers/agent_auth.py` - Token provisioning endpoints
- `src/routers/vault_ai_exposed.py` - Vault endpoints for SDK
- `src/routers/nextflow_jobs_ai_exposed.py` - Job endpoints for SDK
- `src/routers/nextflow_pipelines_ai_exposed.py` - Pipeline endpoints for SDK
- `src/services/ai_exposed_routes_helpers.py` - Token validation helpers

### Agent Files

- `services/agents/analysis/tool_init.py` - Token provisioning and injection
