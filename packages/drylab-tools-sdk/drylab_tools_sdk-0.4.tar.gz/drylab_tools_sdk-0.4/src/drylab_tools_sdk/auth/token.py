"""Token decoding and management."""

import base64
import json
import logging
import os
import threading
import time
from typing import Optional, Dict, Any

from drylab_tools_sdk.exceptions import AuthenticationError, ConfigurationError

logger = logging.getLogger(__name__)


class TokenManager:
    """
    Manages API token lifecycle including decoding and auto-refresh.

    The token is a JWT that contains:
    - user_id: The authenticated user
    - scopes: Allowed operations
    - exp: Expiration timestamp
    - jti: Unique token ID
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        auto_refresh: bool = True,
        refresh_threshold_seconds: int = 300,
    ):
        self._api_key = api_key
        self._base_url = base_url
        self._refresh_threshold = refresh_threshold_seconds
        self._refresh_lock = threading.Lock()
        self._stop_refresh = False

        # Decode token to extract claims
        self._claims = self._decode_token(api_key)

        # Validate token is not already expired
        if self.is_expired:
            raise AuthenticationError("API key has expired. Please obtain a new token.")

        # Start auto-refresh daemon
        if auto_refresh and not self.is_expired:
            self._start_refresh_daemon()

    @property
    def claims(self) -> Dict[str, Any]:
        """Get decoded token claims."""
        return self._claims

    @property
    def user_id(self) -> str:
        """Get user ID from token."""
        return self._claims.get("user_id", "")

    @property
    def scopes(self) -> list:
        """Get allowed scopes from token."""
        return self._claims.get("scopes", [])

    @property
    def expires_at(self) -> int:
        """Get expiration timestamp."""
        return self._claims.get("exp", 0)

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return time.time() >= self.expires_at

    @property
    def is_expiring_soon(self) -> bool:
        """Check if token is within refresh threshold."""
        return time.time() >= (self.expires_at - self._refresh_threshold) and time.time() < self.expires_at

    @property
    def time_until_expiry(self) -> float:
        """Seconds until token expires."""
        return max(0, self.expires_at - time.time())

    def get_valid_token(self) -> str:
        """Get a valid token, refreshing if necessary."""
        if self.is_expired:
            raise AuthenticationError("API key has expired and could not be refreshed.")

        if self.is_expiring_soon:
            try:
                self._refresh()
            except Exception as e:
                # If refresh fails but token still valid, continue
                if not self.is_expired:
                    logger.warning(f"Token refresh failed, but token still valid: {e}")
                else:
                    raise

        return self._api_key

    def _decode_token(self, token: str) -> Dict[str, Any]:
        """Decode JWT token without cryptographic verification.

        We don't verify the signature client-side because:
        1. The backend will verify it on every request
        2. We just need to read claims for user_id and expiry
        """
        # Strip prefix
        if token.startswith("drylab_sk_"):
            token = token[10:]

        # JWT format: header.payload.signature
        parts = token.split(".")
        if len(parts) != 3:
            raise ConfigurationError("Invalid API key format. Expected JWT token.")

        # Decode payload (base64url)
        payload = parts[1]

        # Add padding if needed (base64url may omit padding)
        padding_needed = 4 - (len(payload) % 4)
        if padding_needed != 4:
            payload += "=" * padding_needed

        try:
            decoded_bytes = base64.urlsafe_b64decode(payload)
            return json.loads(decoded_bytes)
        except (ValueError, json.JSONDecodeError) as e:
            raise ConfigurationError(f"Failed to decode API key: {e}")

    def _refresh(self) -> None:
        """Refresh the token via backend API."""
        with self._refresh_lock:
            # Double-check after acquiring lock
            if not self.is_expiring_soon:
                return

            import requests

            try:
                response = requests.post(
                    f"{self._base_url}/api/v1/ai/auth/refresh-token",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    timeout=30,
                )

                if response.ok:
                    data = response.json()
                    new_token = data.get("token", data.get("execution_token"))

                    if new_token:
                        self._api_key = new_token
                        self._claims = self._decode_token(new_token)

                        # Update environment variable for child processes
                        os.environ["DRYLAB_API_KEY"] = new_token
                        logger.info("Token refreshed successfully")

                elif response.status_code == 401:
                    logger.warning("Token refresh failed: unauthorized")
                else:
                    logger.warning(f"Token refresh failed: {response.status_code}")

            except requests.exceptions.RequestException as e:
                logger.warning(f"Token refresh request failed: {e}")

    def _start_refresh_daemon(self) -> None:
        """Start background thread for automatic token refresh."""

        def refresh_loop():
            while not self._stop_refresh:
                try:
                    # Calculate sleep time
                    sleep_time = max(
                        30,  # Minimum 30 seconds
                        min(
                            300,  # Maximum 5 minutes
                            self.time_until_expiry - self._refresh_threshold - 60,
                        ),
                    )

                    # Sleep in small increments to allow clean shutdown
                    for _ in range(int(sleep_time)):
                        if self._stop_refresh:
                            return
                        time.sleep(1)

                    if self.is_expiring_soon and not self.is_expired:
                        self._refresh()

                except Exception as e:
                    logger.warning(f"Token refresh daemon error: {e}")
                    time.sleep(60)

        thread = threading.Thread(target=refresh_loop, daemon=True, name="drylab-token-refresh")
        thread.start()

    def stop(self) -> None:
        """Stop the refresh daemon."""
        self._stop_refresh = True
