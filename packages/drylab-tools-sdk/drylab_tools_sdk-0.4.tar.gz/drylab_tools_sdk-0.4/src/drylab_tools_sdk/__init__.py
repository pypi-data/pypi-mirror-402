"""
Drylab Client SDK - Python client for Drylab Backend API.

This SDK is designed for AI-generated code running inside Drylab sandboxes.
It provides simple, semantic access to vault files, Nextflow jobs, and pipelines.

Note: This SDK (drylab-tools-sdk) is different from drylab-runtime-sdk:
- drylab-tools-sdk: For AI code to interact with backend (vault, jobs, pipelines)
- drylab-runtime-sdk: For LangGraph agents to manage sandboxes and kernels

Usage:
    from drylab_tools_sdk import DrylabClient

    client = DrylabClient()  # Auto-configures from DRYLAB_API_KEY

    # Vault operations
    files = client.vault.list("/MyProject/data")
    upload = client.vault.upload("/MyProject/output", "result.csv", size=1024)

    # Job operations
    job = client.jobs.submit("rnaseq", params={"input": "..."})
    status = client.jobs.get(job.id)

    # Pipeline operations
    pipelines = client.pipelines.list()
    schema = client.pipelines.get_schema("rnaseq")
"""

from drylab_tools_sdk._version import __version__
from drylab_tools_sdk.client import DrylabClient
from drylab_tools_sdk.exceptions import (
    DrylabError,
    AuthenticationError,
    ConfigurationError,
    NotFoundError,
    PermissionError,
    ValidationError,
    RateLimitError,
)
from drylab_tools_sdk.models import (
    # Vault
    VaultFile,
    VaultFolder,
    UploadResult,
    DownloadResult,
    ListFilesResult,
    # Jobs
    Job,
    JobStatus,
    # Pipelines
    Pipeline,
    PipelineSchema,
    SchemaField,
)

__all__ = [
    # Version
    "__version__",
    # Main client
    "DrylabClient",
    # Exceptions
    "DrylabError",
    "AuthenticationError",
    "ConfigurationError",
    "NotFoundError",
    "PermissionError",
    "ValidationError",
    "RateLimitError",
    # Models - Vault
    "VaultFile",
    "VaultFolder",
    "UploadResult",
    "DownloadResult",
    "ListFilesResult",
    # Models - Jobs
    "Job",
    "JobStatus",
    # Models - Pipelines
    "Pipeline",
    "PipelineSchema",
    "SchemaField",
]
