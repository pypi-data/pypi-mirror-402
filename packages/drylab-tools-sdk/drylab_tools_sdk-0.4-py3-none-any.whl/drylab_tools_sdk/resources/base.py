"""Base class for API resources."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from drylab_tools_sdk._http import HttpClient
    from drylab_tools_sdk.auth.token import TokenManager


class BaseResource:
    """Base class for API resource clients."""

    def __init__(self, http: "HttpClient", token_manager: "TokenManager"):
        self._http = http
        self._token_manager = token_manager

    @property
    def _user_id(self) -> str:
        """Get user ID from token (for internal use if needed)."""
        return self._token_manager.user_id
