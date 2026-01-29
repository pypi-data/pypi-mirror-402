"""Exception classes for drylab_tools_sdk."""

from typing import Optional, Dict, Any, List


class DrylabError(Exception):
    """Base exception for all Drylab SDK errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_body = response_body

    def __str__(self) -> str:
        if self.status_code:
            return f"Error {self.status_code}: {self.message}"
        return self.message


class ConfigurationError(DrylabError):
    """Raised when SDK is misconfigured (missing API key, invalid URL, etc.)."""

    pass


class AuthenticationError(DrylabError):
    """Raised when authentication fails (invalid/expired token)."""

    pass


class PermissionError(DrylabError):
    """Raised when user lacks permission for the requested operation."""

    pass


class NotFoundError(DrylabError):
    """Raised when requested resource is not found."""

    pass


class ValidationError(DrylabError):
    """Raised when request validation fails."""

    def __init__(
        self,
        message: str,
        errors: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ):
        super().__init__(message, **kwargs)
        self.errors = errors or []


class RateLimitError(DrylabError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        **kwargs: Any,
    ):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after
