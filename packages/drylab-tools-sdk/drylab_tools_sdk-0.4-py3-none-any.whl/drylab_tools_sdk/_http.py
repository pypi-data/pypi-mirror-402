"""Internal HTTP client with error handling and retries."""

import logging
from typing import Optional, Dict, Any, TYPE_CHECKING

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from drylab_tools_sdk.exceptions import (
    DrylabError,
    AuthenticationError,
    PermissionError,
    NotFoundError,
    ValidationError,
    RateLimitError,
)

if TYPE_CHECKING:
    from drylab_tools_sdk.auth.token import TokenManager

logger = logging.getLogger(__name__)


class HttpClient:
    """HTTP client with authentication and error handling."""

    def __init__(
        self,
        base_url: str,
        token_manager: "TokenManager",
        timeout: int = 30,
        max_retries: int = 3,
    ):
        self.base_url = base_url.rstrip("/")
        self.token_manager = token_manager
        self.timeout = timeout

        # Configure session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Make an authenticated HTTP request."""

        url = f"{self.base_url}{path}"

        request_headers = {
            "Authorization": f"Bearer {self.token_manager.get_valid_token()}",
            "Content-Type": "application/json",
            "User-Agent": "drylab-tools-sdk/0.1.0",
        }
        if headers:
            request_headers.update(headers)

        try:
            # Allow timeout to be overridden via kwargs (e.g., for long-running Pokemon jobs)
            timeout = kwargs.pop("timeout", self.timeout)
            response = self.session.request(
                method=method,
                url=url,
                json=json,
                params=params,
                headers=request_headers,
                timeout=timeout,
                **kwargs,
            )
        except requests.exceptions.Timeout:
            raise DrylabError(f"Request timed out: {method} {path}")
        except requests.exceptions.ConnectionError as e:
            raise DrylabError(f"Connection error: {e}")

        return self._handle_response(response, path)

    def _handle_response(self, response: requests.Response, path: str) -> Dict[str, Any]:
        """Parse response and raise appropriate exceptions."""

        # Try to parse JSON body
        try:
            body = response.json()
        except ValueError:
            body = {"detail": response.text}

        # Success
        if response.ok:
            return body

        # Error handling
        message = body.get("detail", body.get("message", "Unknown error"))
        if isinstance(message, dict):
            message = message.get("message", str(message))

        if response.status_code == 401:
            raise AuthenticationError(
                message=message,
                status_code=401,
                response_body=body,
            )

        if response.status_code == 403:
            raise PermissionError(
                message=message,
                status_code=403,
                response_body=body,
            )

        if response.status_code == 404:
            raise NotFoundError(
                message=message,
                status_code=404,
                response_body=body,
            )

        if response.status_code == 422:
            raise ValidationError(
                message=message,
                errors=body.get("errors", body.get("detail", [])),
                status_code=422,
                response_body=body,
            )

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                message=message,
                retry_after=int(retry_after) if retry_after else None,
                status_code=429,
                response_body=body,
            )

        # Generic error
        raise DrylabError(
            message=f"{path}: {message}",
            status_code=response.status_code,
            response_body=body,
        )

    def get(self, path: str, **kwargs: Any) -> Dict[str, Any]:
        """Make a GET request."""
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> Dict[str, Any]:
        """Make a POST request."""
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> Dict[str, Any]:
        """Make a PUT request."""
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> Dict[str, Any]:
        """Make a DELETE request."""
        return self.request("DELETE", path, **kwargs)
