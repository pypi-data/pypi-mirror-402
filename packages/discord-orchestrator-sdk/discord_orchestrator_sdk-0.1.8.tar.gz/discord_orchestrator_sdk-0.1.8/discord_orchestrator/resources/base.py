"""Base resource class for API resources."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ..utils.http import HTTPClient


class BaseResource:
    """Base class for API resource classes.

    Provides common functionality and HTTP client access for all
    resource classes.
    """

    def __init__(self, http: "HTTPClient"):
        """Initialize the resource.

        Args:
            http: HTTP client for making API requests
        """
        self._http = http

    def _build_url(self, *parts: str | int) -> str:
        """Build URL path from parts.

        Args:
            *parts: URL path segments

        Returns:
            Combined URL path starting with /

        Example:
            >>> self._build_url("bots", 123, "start")
            "/bots/123/start"
        """
        path = "/".join(str(p) for p in parts)
        if not path.startswith("/"):
            path = f"/{path}"
        return path

    def _wrap_response(
        self,
        response: dict[str, Any],
        key: Optional[str] = None,
        default: Any = None,
    ) -> Any:
        """Extract data from response with optional key extraction.

        Handles both wrapped and unwrapped API responses consistently.

        Args:
            response: API response dict
            key: Optional key to extract from response
            default: Default value if key not found

        Returns:
            Extracted data or full response if no key specified

        Example:
            >>> # Response: {"bot": {...}}
            >>> self._wrap_response(response, "bot")
            {...}
            >>> # Response: {...}
            >>> self._wrap_response(response, "bot")
            {...}  # Falls back to full response
        """
        if key is None:
            return response
        return response.get(key, response) if isinstance(response, dict) else default

    def _extract_list(
        self,
        response: dict[str, Any],
        key: str,
    ) -> list[Any]:
        """Extract a list from response.

        Args:
            response: API response dict
            key: Key containing the list

        Returns:
            List from response, or empty list if not found

        Example:
            >>> # Response: {"bots": [...]}
            >>> self._extract_list(response, "bots")
            [...]
        """
        if isinstance(response, dict):
            return response.get(key, [])
        return []
