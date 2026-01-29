"""
Integration tests for DrylabClient.

These tests require a running backend and valid credentials.
Run with: pytest tests/test_integration.py -v -m integration

To set up:
1. Start the backend: cd drylab-backend && python -m uvicorn app:app --port 8000
2. Set environment variables:
   export DRYLAB_TEST_USER_ID="your-user-uuid"
   export DRYLAB_AGENT_BACKEND_TOKEN="your-agent-token"
   export DRYLAB_API_BASE_URL="http://localhost:8000"
3. Run tests: pytest tests/test_integration.py -v -m integration
"""

import os
import pytest
import requests

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def backend_url():
    """Get backend URL from environment."""
    return os.environ.get("DRYLAB_API_BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="module")
def agent_token():
    """Get agent backend token for provisioning."""
    token = os.environ.get("DRYLAB_AGENT_BACKEND_TOKEN")
    if not token:
        pytest.skip("DRYLAB_AGENT_BACKEND_TOKEN not set")
    return token


@pytest.fixture(scope="module")
def test_user_id():
    """Get test user ID."""
    user_id = os.environ.get("DRYLAB_TEST_USER_ID")
    if not user_id:
        pytest.skip("DRYLAB_TEST_USER_ID not set")
    return user_id


@pytest.fixture(scope="module")
def execution_token(backend_url, agent_token, test_user_id):
    """Provision an execution token for testing."""
    response = requests.post(
        f"{backend_url}/api/v1/agent/provision-token",
        json={
            "user_id": test_user_id,
            "scopes": ["vault:*", "jobs:*", "pipelines:*"],
            "ttl_hours": 1,
        },
        headers={"Authorization": f"Bearer {agent_token}"},
        timeout=10,
    )

    if response.status_code != 200:
        pytest.skip(f"Failed to provision token: {response.status_code} - {response.text}")

    return response.json()["token"]


@pytest.fixture
def client(execution_token, backend_url):
    """Create a DrylabClient with test credentials."""
    from drylab_tools_sdk import DrylabClient

    return DrylabClient(
        api_key=execution_token,
        base_url=backend_url,
        auto_refresh=False,
    )


class TestVaultIntegration:
    """Integration tests for Vault operations."""

    def test_list_files_requires_valid_path(self, client):
        """Test listing files with invalid path returns error."""
        from drylab_tools_sdk import NotFoundError

        with pytest.raises(NotFoundError):
            client.vault.list("/NonExistentProject/data")

    def test_client_has_user_id(self, client, test_user_id):
        """Test that client extracts user_id from token."""
        assert client.user_id == test_user_id


class TestJobsIntegration:
    """Integration tests for Jobs operations."""

    def test_list_jobs(self, client):
        """Test listing jobs."""
        jobs = client.jobs.list(limit=5)
        # Should return a list (may be empty)
        assert isinstance(jobs, list)


class TestPipelinesIntegration:
    """Integration tests for Pipelines operations."""

    def test_list_pipelines(self, client):
        """Test listing pipelines."""
        pipelines = client.pipelines.list()
        # Should return a list with at least public pipelines
        assert isinstance(pipelines, list)


class TestTokenInfo:
    """Test token information endpoint."""

    def test_token_info(self, execution_token, backend_url):
        """Test getting token info."""
        response = requests.get(
            f"{backend_url}/api/v1/agent/token-info",
            headers={"Authorization": f"Bearer {execution_token}"},
            timeout=10,
        )

        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "scopes" in data
        assert data["is_expired"] is False
