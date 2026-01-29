"""Base resource class for API resources."""

from __future__ import annotations

from typing import TYPE_CHECKING

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
