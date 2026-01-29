"""Webhook-related data models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class WebhookEvent(BaseModel):
    """Webhook event type definition.

    Attributes:
        type: Event type identifier
        description: Human-readable description
    """

    type: str
    description: str


class Webhook(BaseModel):
    """Webhook configuration.

    Attributes:
        id: Webhook identifier
        name: Webhook name
        url: Target URL
        events: List of subscribed event types
        headers: Custom headers to send
        bot_id: Optional bot ID to filter events
        user_context: Optional user context for multi-tenant filtering
        is_active: Whether the webhook is enabled
        secret: Signing secret (only included on creation)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: int
    name: str
    url: str
    events: list[str] = Field(default_factory=list)
    headers: dict[str, str] = Field(default_factory=dict)
    bot_id: Optional[int] = None
    user_context: Optional[str] = None
    is_active: bool = True
    secret: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class WebhookDelivery(BaseModel):
    """Webhook delivery record.

    Attributes:
        id: Delivery identifier
        webhook_id: Parent webhook ID
        event_type: Type of event delivered
        payload: Event payload
        response_code: HTTP response code
        response_body: Response body (truncated)
        success: Whether delivery succeeded
        delivered_at: Delivery timestamp
        duration_ms: Request duration in milliseconds
    """

    id: int
    webhook_id: int
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    success: bool = False
    delivered_at: datetime
    duration_ms: Optional[float] = None


class CreateWebhookRequest(BaseModel):
    """Request to create a new webhook.

    Attributes:
        name: Webhook name
        url: Target URL
        events: List of event types to subscribe to
        headers: Custom headers to include
        bot_id: Optional bot ID to filter events
        user_context: Optional user context for multi-tenant filtering
    """

    name: str = Field(..., min_length=1, max_length=100)
    url: str = Field(..., min_length=1)
    events: list[str] = Field(..., min_length=1)
    headers: dict[str, str] = Field(default_factory=dict)
    bot_id: Optional[int] = None
    user_context: Optional[str] = None


class UpdateWebhookRequest(BaseModel):
    """Request to update a webhook.

    Attributes:
        name: New webhook name (optional)
        url: New target URL (optional)
        events: New event subscriptions (optional)
        headers: New custom headers (optional)
        is_active: Enable/disable webhook (optional)
    """

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    url: Optional[str] = Field(None, min_length=1)
    events: Optional[list[str]] = None
    headers: Optional[dict[str, str]] = None
    is_active: Optional[bool] = None
