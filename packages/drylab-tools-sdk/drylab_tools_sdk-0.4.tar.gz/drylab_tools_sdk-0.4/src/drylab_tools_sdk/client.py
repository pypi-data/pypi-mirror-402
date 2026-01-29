"""Main DrylabClient class."""

import logging
import os
from typing import Optional

from drylab_tools_sdk.auth.token import TokenManager
from drylab_tools_sdk._http import HttpClient
from drylab_tools_sdk.resources.vault import VaultResource
from drylab_tools_sdk.resources.jobs import JobsResource
from drylab_tools_sdk.resources.pipelines import PipelinesResource
from drylab_tools_sdk.resources.pokemon import PokemonResource
from drylab_tools_sdk.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class DrylabClient:
    """
    Drylab Client SDK - Python client for Drylab Backend API.

    This client provides access to:
    - vault: File storage operations (upload, download, list)
    - jobs: Nextflow job management (submit, status, cancel)
    - pipelines: Pipeline registry (list, schema, register)
    - pokemon: Protein structure prediction tools (ProteinX, Chai1, ProteinMPNN, Boltz2)

    The client automatically reads the API key from the DRYLAB_API_KEY
    environment variable, which is injected when the sandbox is provisioned.

    Usage:
        from drylab_tools_sdk import DrylabClient

        client = DrylabClient()

        # List files
        result = client.vault.list("/MyProject/data")
        for file in result.files:
            print(f"{file.filename} ({file.size} bytes)")

        # Submit a job
        job = client.jobs.submit(
            pipeline_id="rnaseq",
            params={"input": "/MyProject/data/reads.fastq"},
            compute_profile="aws-batch"
        )
        print(f"Job submitted: {job.id}")

        # Check job status
        job = client.jobs.get(job.id)
        print(f"Status: {job.status}")

    Environment Variables:
        DRYLAB_API_KEY: Required. The execution token (injected by LangGraph).
        DRYLAB_API_BASE_URL: Optional. Backend URL (default: https://api.drylab.ai).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        auto_refresh: bool = True,
        timeout: int = 30,
    ):
        """
        Initialize the Drylab client.

        Args:
            api_key: API key (execution token). Default: DRYLAB_API_KEY env var.
            base_url: Backend API URL. Default: DRYLAB_API_BASE_URL env var or https://api.drylab.ai.
            auto_refresh: Enable automatic token refresh before expiry. Default: True.
            timeout: HTTP request timeout in seconds. Default: 30.
        """
        # Get configuration
        self._api_key = api_key or os.environ.get("DRYLAB_API_KEY")
        self._base_url = (
            base_url
            or os.environ.get("DRYLAB_API_BASE_URL")
            or os.environ.get("DRYLAB_API_URL")  # Backward compat
            or "https://api.drylab.ai"
        ).rstrip("/")

        # Validate configuration
        if not self._api_key:
            raise ConfigurationError(
                "No API key provided. "
                "Set the DRYLAB_API_KEY environment variable or pass api_key parameter. "
                "This is typically done automatically when the sandbox is provisioned."
            )

        # Initialize token manager
        self._token_manager = TokenManager(
            api_key=self._api_key,
            base_url=self._base_url,
            auto_refresh=auto_refresh,
        )

        # Initialize HTTP client
        self._http = HttpClient(
            base_url=self._base_url,
            token_manager=self._token_manager,
            timeout=timeout,
        )

        # Initialize resource clients
        self.vault = VaultResource(self._http, self._token_manager)
        self.jobs = JobsResource(self._http, self._token_manager)
        self.pipelines = PipelinesResource(self._http, self._token_manager)
        self.pokemon = PokemonResource(self._http, self._token_manager)

        logger.debug(f"DrylabClient initialized for user {self.user_id}")

    @property
    def user_id(self) -> str:
        """Get the authenticated user ID from the token."""
        return self._token_manager.user_id

    @property
    def token_expires_in(self) -> float:
        """Get seconds until token expires."""
        return self._token_manager.time_until_expiry

    def close(self) -> None:
        """Close the client and stop background threads."""
        self._token_manager.stop()

    def __enter__(self) -> "DrylabClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"DrylabClient(user_id={self.user_id!r}, base_url={self._base_url!r})"
