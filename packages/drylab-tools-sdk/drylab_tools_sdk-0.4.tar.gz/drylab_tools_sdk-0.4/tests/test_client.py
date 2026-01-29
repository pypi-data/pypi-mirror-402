"""Tests for DrylabClient."""

import os
import pytest

from drylab_tools_sdk import DrylabClient
from drylab_tools_sdk.exceptions import ConfigurationError, AuthenticationError


class TestDrylabClient:
    """Tests for DrylabClient initialization."""

    def test_init_with_api_key(self, test_token):
        """Test client initialization with explicit API key."""
        client = DrylabClient(api_key=test_token, auto_refresh=False)
        assert client.user_id == "test-user-123"

    def test_init_from_env(self, test_token, monkeypatch):
        """Test client initialization from environment variable."""
        monkeypatch.setenv("DRYLAB_API_KEY", test_token)
        client = DrylabClient(auto_refresh=False)
        assert client.user_id == "test-user-123"

    def test_init_missing_key_raises(self, monkeypatch):
        """Test that missing API key raises ConfigurationError."""
        monkeypatch.delenv("DRYLAB_API_KEY", raising=False)
        with pytest.raises(ConfigurationError, match="No API key provided"):
            DrylabClient()

    def test_init_expired_token_raises(self, expired_token):
        """Test that expired token raises AuthenticationError."""
        with pytest.raises(AuthenticationError, match="expired"):
            DrylabClient(api_key=expired_token, auto_refresh=False)

    def test_resources_available(self, test_token):
        """Test that all resources are available."""
        client = DrylabClient(api_key=test_token, auto_refresh=False)
        assert hasattr(client, "vault")
        assert hasattr(client, "jobs")
        assert hasattr(client, "pipelines")

    def test_context_manager(self, test_token):
        """Test client works as context manager."""
        with DrylabClient(api_key=test_token, auto_refresh=False) as client:
            assert client.user_id == "test-user-123"
