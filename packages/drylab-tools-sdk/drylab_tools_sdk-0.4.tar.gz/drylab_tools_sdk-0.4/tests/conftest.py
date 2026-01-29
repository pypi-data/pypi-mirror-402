"""Pytest configuration and fixtures."""

import base64
import json
import time
import pytest


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (requires backend)"
    )


def create_test_token(
    user_id: str = "test-user-123",
    scopes: list = None,
    exp_hours: int = 4,
) -> str:
    """Create a test JWT token."""
    if scopes is None:
        scopes = ["vault:*", "jobs:*", "pipelines:*"]

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "type": "execution",
        "user_id": user_id,
        "scopes": scopes,
        "iat": int(time.time()),
        "exp": int(time.time()) + (exp_hours * 3600),
        "jti": "test-token-id",
    }

    # Create unsigned token (signature doesn't matter for client-side tests)
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signature = "test_signature"

    return f"drylab_sk_{header_b64}.{payload_b64}.{signature}"


@pytest.fixture
def test_token():
    """Fixture providing a test token."""
    return create_test_token()


@pytest.fixture
def expired_token():
    """Fixture providing an expired token."""
    return create_test_token(exp_hours=-1)
