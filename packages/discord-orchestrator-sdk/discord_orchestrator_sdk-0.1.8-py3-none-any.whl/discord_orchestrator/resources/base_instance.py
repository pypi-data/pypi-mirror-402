"""Base class for resource instance wrappers.

Provides common functionality for BotInstance, WebhookInstance, etc.
"""

from __future__ import annotations

from abc import ABC
from typing import Any, Generic, TypeVar

# Type vars for data model and resource types
TData = TypeVar("TData")
TResource = TypeVar("TResource")


class ResourceInstance(ABC, Generic[TData, TResource]):
    """Base class for resource instance wrappers.

    Resource instances wrap API data models and provide fluent interfaces
    for interacting with individual resources.

    Type Parameters:
        TData: The data model type (e.g., Bot, Webhook)
        TResource: The resource class type (e.g., BotsResource, WebhooksResource)

    Attributes:
        _data: The underlying data model
        _resource: Parent resource class for API calls

    Example:
        >>> class BotInstance(ResourceInstance[Bot, "BotsResource"]):
        ...     def start(self) -> "BotInstance":
        ...         return self._resource.start(self._data.id)
    """

    def __init__(self, data: TData, resource: TResource):
        """Initialize the resource instance.

        Args:
            data: The underlying data model
            resource: Parent resource class for API calls
        """
        self._data = data
        self._resource = resource

    def __getattr__(self, name: str) -> Any:
        """Proxy attribute access to the underlying data model.

        This allows accessing data model attributes directly on the instance.

        Args:
            name: Attribute name to access

        Returns:
            Value from the underlying data model

        Raises:
            AttributeError: If attribute doesn't exist on data model
        """
        return getattr(self._data, name)

    @property
    def id(self) -> int:
        """Get the resource ID.

        Returns:
            The resource's unique identifier
        """
        return self._data.id  # type: ignore[attr-defined]

    def _refresh_data(self, new_data: TData) -> None:
        """Update the internal data model.

        Args:
            new_data: New data model to use
        """
        self._data = new_data

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance data to a dictionary.

        Returns:
            Dict representation of the data model
        """
        if hasattr(self._data, "model_dump"):
            # Pydantic v2
            return self._data.model_dump()  # type: ignore[attr-defined]
        elif hasattr(self._data, "dict"):
            # Pydantic v1
            return self._data.dict()  # type: ignore[attr-defined]
        elif hasattr(self._data, "__dict__"):
            return dict(self._data.__dict__)
        return {}
