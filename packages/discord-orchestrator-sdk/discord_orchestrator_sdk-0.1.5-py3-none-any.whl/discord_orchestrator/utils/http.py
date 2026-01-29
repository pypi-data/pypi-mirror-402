"""HTTP client wrapper with retry logic and error handling."""

from __future__ import annotations

from typing import Any, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..config import OrchestratorConfig
from ..exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConnectionError,
    NotFoundError,
    OrchestratorError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
)


class HTTPClient:
    """HTTP client with retry logic and error handling.

    Provides a consistent interface for making HTTP requests to the
    orchestrator API with automatic retries, authentication, and
    error handling.
    """

    def __init__(self, config: OrchestratorConfig):
        """Initialize the HTTP client.

        Args:
            config: Configuration for the client
        """
        self.config = config
        self.session = requests.Session()
        self._setup_session()
        self._setup_auth()

    def _setup_session(self) -> None:
        """Configure the session with retry logic."""
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.retry_delay,
            status_forcelist=[502, 503, 504],
            allowed_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _setup_auth(self) -> None:
        """Configure authentication headers."""
        if self.config.api_key:
            self.session.headers["Authorization"] = f"Bearer {self.config.api_key}"
        self.session.headers["Content-Type"] = "application/json"
        self.session.headers["Accept"] = "application/json"

        # Multi-tenant support: add user context header if configured
        if self.config.user_context:
            self.session.headers["X-User-Context"] = self.config.user_context

    def _build_url(self, path: str, use_api_prefix: bool = True) -> str:
        """Build the full URL for an API endpoint.

        Args:
            path: API path (should start with /)
            use_api_prefix: Whether to add /api/v1 prefix (default True)

        Returns:
            Full URL including base URL and optionally API prefix
        """
        if not path.startswith("/"):
            path = f"/{path}"
        if use_api_prefix:
            return f"{self.config.base_url}/api/v1{path}"
        return f"{self.config.base_url}{path}"

    def _handle_response(self, response: requests.Response) -> dict[str, Any]:
        """Handle the API response and raise appropriate exceptions.

        Args:
            response: The HTTP response

        Returns:
            Parsed JSON response

        Raises:
            AuthenticationError: On 401 response
            AuthorizationError: On 403 response
            NotFoundError: On 404 response
            ValidationError: On 400 response
            RateLimitError: On 429 response
            ServerError: On 5xx response
            OrchestratorError: On other errors
        """
        # Handle successful responses
        if response.status_code in (200, 201, 202):
            if response.content:
                return response.json()
            return {}

        # Handle 204 No Content
        if response.status_code == 204:
            return {}

        # Parse error response
        try:
            error_data = response.json()
            message = error_data.get("error", response.text)
            code = error_data.get("code")
            details = error_data.get("details", {})
        except (ValueError, KeyError):
            message = response.text or f"HTTP {response.status_code}"
            code = None
            details = {}

        # Map status codes to exceptions
        if response.status_code == 401:
            raise AuthenticationError(message, code, details)
        elif response.status_code == 403:
            raise AuthorizationError(message, code, details)
        elif response.status_code == 404:
            raise NotFoundError(message, code, details)
        elif response.status_code == 400:
            raise ValidationError(message, code, details)
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            retry_after_float = float(retry_after) if retry_after else None
            raise RateLimitError(message, code, details, retry_after_float)
        elif response.status_code == 504:
            raise TimeoutError(message, code, details)
        elif response.status_code >= 500:
            raise ServerError(message, code, details)
        else:
            raise OrchestratorError(message, code, details)

    def request(
        self,
        method: str,
        path: str,
        params: Optional[dict[str, Any]] = None,
        json: Optional[dict[str, Any]] = None,
        timeout: Optional[float] = None,
        use_api_prefix: bool = True,
    ) -> dict[str, Any]:
        """Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, PATCH, PUT, DELETE)
            path: API path
            params: Query parameters
            json: JSON body
            timeout: Request timeout (uses config default if not specified)
            use_api_prefix: Whether to add /api/v1 prefix (default True)

        Returns:
            Parsed JSON response

        Raises:
            ConnectionError: When connection fails
            TimeoutError: When request times out
            OrchestratorError: On other errors
        """
        url = self._build_url(path, use_api_prefix=use_api_prefix)
        timeout = timeout or self.config.timeout

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                timeout=timeout,
                verify=self.config.verify_ssl,
            )
            return self._handle_response(response)

        except requests.exceptions.Timeout as e:
            raise TimeoutError(f"Request timed out: {e}")
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(f"Connection failed: {e}")
        except requests.exceptions.RequestException as e:
            raise OrchestratorError(f"Request failed: {e}")

    def get(
        self,
        path: str,
        params: Optional[dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> dict[str, Any]:
        """Make a GET request.

        Args:
            path: API path
            params: Query parameters
            timeout: Request timeout

        Returns:
            Parsed JSON response
        """
        return self.request("GET", path, params=params, timeout=timeout)

    def post(
        self,
        path: str,
        json: Optional[dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> dict[str, Any]:
        """Make a POST request.

        Args:
            path: API path
            json: JSON body
            timeout: Request timeout

        Returns:
            Parsed JSON response
        """
        return self.request("POST", path, json=json, timeout=timeout)

    def patch(
        self,
        path: str,
        json: Optional[dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> dict[str, Any]:
        """Make a PATCH request.

        Args:
            path: API path
            json: JSON body
            timeout: Request timeout

        Returns:
            Parsed JSON response
        """
        return self.request("PATCH", path, json=json, timeout=timeout)

    def put(
        self,
        path: str,
        json: Optional[dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> dict[str, Any]:
        """Make a PUT request.

        Args:
            path: API path
            json: JSON body
            timeout: Request timeout

        Returns:
            Parsed JSON response
        """
        return self.request("PUT", path, json=json, timeout=timeout)

    def delete(
        self,
        path: str,
        timeout: Optional[float] = None,
    ) -> dict[str, Any]:
        """Make a DELETE request.

        Args:
            path: API path
            timeout: Request timeout

        Returns:
            Empty dict on success
        """
        return self.request("DELETE", path, timeout=timeout)

    def get_root(
        self,
        path: str,
        params: Optional[dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> dict[str, Any]:
        """Make a GET request to a root-level endpoint (no /api/v1 prefix).

        Args:
            path: API path (e.g., /health)
            params: Query parameters
            timeout: Request timeout

        Returns:
            Parsed JSON response
        """
        return self.request("GET", path, params=params, timeout=timeout, use_api_prefix=False)

    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()
