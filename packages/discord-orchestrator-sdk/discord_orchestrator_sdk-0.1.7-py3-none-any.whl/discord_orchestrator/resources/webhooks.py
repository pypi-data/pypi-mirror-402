"""Webhooks resource."""

from __future__ import annotations

from typing import Any, Optional

from ..models.webhook import Webhook, WebhookDelivery, WebhookEvent
from .base import BaseResource


class WebhookInstance:
    """Wrapper for a single webhook with fluent interface.

    Example:
        >>> webhook = client.webhooks.get(1)
        >>> print(webhook.name, webhook.url)
        >>> webhook.test()
        >>> webhook.delete()
    """

    def __init__(self, data: Webhook, resource: "WebhooksResource"):
        """Initialize the webhook instance.

        Args:
            data: Webhook data model
            resource: Parent WebhooksResource for API calls
        """
        self._data = data
        self._resource = resource

    def __getattr__(self, name: str) -> Any:
        """Proxy attribute access to the underlying Webhook model."""
        return getattr(self._data, name)

    def __repr__(self) -> str:
        return f"WebhookInstance(id={self._data.id}, name={self._data.name!r}, url={self._data.url!r})"

    def update(
        self,
        name: Optional[str] = None,
        url: Optional[str] = None,
        events: Optional[list[str]] = None,
        headers: Optional[dict[str, str]] = None,
        is_active: Optional[bool] = None,
    ) -> "WebhookInstance":
        """Update the webhook.

        Args:
            name: New webhook name
            url: New target URL
            events: New event subscriptions
            headers: New custom headers
            is_active: Enable/disable webhook

        Returns:
            Updated WebhookInstance
        """
        return self._resource.update(
            self._data.id,
            name=name,
            url=url,
            events=events,
            headers=headers,
            is_active=is_active,
        )

    def delete(self) -> None:
        """Delete the webhook."""
        self._resource.delete(self._data.id)

    def test(self) -> dict[str, Any]:
        """Send a test event to the webhook.

        Returns:
            Test result
        """
        return self._resource.test(self._data.id)

    def regenerate_secret(self) -> "WebhookInstance":
        """Regenerate the webhook's signing secret.

        Returns:
            Updated WebhookInstance with new secret
        """
        return self._resource.regenerate_secret(self._data.id)

    def deliveries(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[WebhookDelivery]:
        """Get delivery history for this webhook.

        Args:
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of WebhookDelivery records
        """
        return self._resource.deliveries(self._data.id, limit=limit, offset=offset)

    def refresh(self) -> "WebhookInstance":
        """Refresh webhook data from the server.

        Returns:
            Updated WebhookInstance with fresh data
        """
        refreshed = self._resource.get(self._data.id)
        self._data = refreshed._data
        return self


class WebhooksResource(BaseResource):
    """Webhook management operations.

    Provides methods for creating, listing, and managing webhooks.
    """

    def list(self) -> list[WebhookInstance]:
        """List all webhooks.

        Returns:
            List of WebhookInstance objects
        """
        response = self._http.get("/webhooks")
        return [
            WebhookInstance(Webhook(**w), self)
            for w in response.get("webhooks", [])
        ]

    def get(self, webhook_id: int) -> WebhookInstance:
        """Get a webhook by ID.

        Args:
            webhook_id: Webhook identifier

        Returns:
            WebhookInstance
        """
        response = self._http.get(f"/webhooks/{webhook_id}")
        return WebhookInstance(Webhook(**response.get("webhook", response)), self)

    def create(
        self,
        name: str,
        url: str,
        events: list[str],
        headers: Optional[dict[str, str]] = None,
        bot_id: Optional[int] = None,
        user_context: Optional[str] = None,
    ) -> WebhookInstance:
        """Create a new webhook.

        Args:
            name: Webhook name
            url: Target URL
            events: List of event types to subscribe to
            headers: Custom headers to include in requests
            bot_id: Optional bot ID to filter events to a specific bot
            user_context: Optional user context for multi-tenant event filtering

        Returns:
            Created WebhookInstance (includes secret)

        Example:
            >>> webhook = client.webhooks.create(
            ...     name="My Webhook",
            ...     url="https://example.com/webhook",
            ...     events=["bot.started", "bot.stopped"]
            ... )
            >>> print(f"Secret: {webhook.secret}")

            # Filter to specific bot
            >>> webhook = client.webhooks.create(
            ...     name="Bot Events",
            ...     url="https://example.com/webhook",
            ...     events=["slash_command"],
            ...     bot_id=123
            ... )
        """
        payload: dict[str, Any] = {
            "name": name,
            "url": url,
            "events": events,
            "headers": headers or {},
        }
        if bot_id is not None:
            payload["bot_id"] = bot_id
        if user_context is not None:
            payload["user_context"] = user_context

        response = self._http.post("/webhooks", json=payload)
        return WebhookInstance(Webhook(**response.get("webhook", response)), self)

    def update(
        self,
        webhook_id: int,
        name: Optional[str] = None,
        url: Optional[str] = None,
        events: Optional[list[str]] = None,
        headers: Optional[dict[str, str]] = None,
        is_active: Optional[bool] = None,
    ) -> WebhookInstance:
        """Update a webhook.

        Args:
            webhook_id: Webhook identifier
            name: New webhook name
            url: New target URL
            events: New event subscriptions
            headers: New custom headers
            is_active: Enable/disable webhook

        Returns:
            Updated WebhookInstance
        """
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if url is not None:
            payload["url"] = url
        if events is not None:
            payload["events"] = events
        if headers is not None:
            payload["headers"] = headers
        if is_active is not None:
            payload["is_active"] = is_active

        response = self._http.put(f"/webhooks/{webhook_id}", json=payload)
        return WebhookInstance(Webhook(**response.get("webhook", response)), self)

    def delete(self, webhook_id: int) -> None:
        """Delete a webhook.

        Args:
            webhook_id: Webhook identifier
        """
        self._http.delete(f"/webhooks/{webhook_id}")

    def test(self, webhook_id: int) -> dict[str, Any]:
        """Send a test event to a webhook.

        Args:
            webhook_id: Webhook identifier

        Returns:
            Test result including success status and response
        """
        return self._http.post(f"/webhooks/{webhook_id}/test")

    def regenerate_secret(self, webhook_id: int) -> WebhookInstance:
        """Regenerate the webhook's signing secret.

        Args:
            webhook_id: Webhook identifier

        Returns:
            Updated WebhookInstance with new secret
        """
        response = self._http.post(f"/webhooks/{webhook_id}/regenerate-secret")
        return WebhookInstance(Webhook(**response.get("webhook", response)), self)

    def deliveries(
        self,
        webhook_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[WebhookDelivery]:
        """Get delivery history for a webhook.

        Args:
            webhook_id: Webhook identifier
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of WebhookDelivery records
        """
        params = {"limit": limit, "offset": offset}
        response = self._http.get(f"/webhooks/{webhook_id}/deliveries", params=params)
        return [WebhookDelivery(**d) for d in response.get("deliveries", [])]

    def events(self) -> list[WebhookEvent]:
        """Get list of available webhook event types.

        Returns:
            List of WebhookEvent definitions
        """
        response = self._http.get("/webhooks/events")
        return [WebhookEvent(**e) for e in response.get("events", [])]
