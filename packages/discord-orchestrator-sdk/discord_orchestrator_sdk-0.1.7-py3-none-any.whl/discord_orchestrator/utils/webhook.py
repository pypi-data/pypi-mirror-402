"""Webhook signature verification utilities."""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Optional, Union

from ..constants import MAX_WEBHOOK_AGE_SECONDS, WEBHOOK_CLOCK_SKEW_TOLERANCE


class WebhookSignatureError(Exception):
    """Raised when webhook signature verification fails."""

    pass


def verify_webhook_signature(
    payload: Union[str, bytes],
    signature_header: str,
    secret: str,
    timestamp_header: Optional[str] = None,
    max_age_seconds: int = MAX_WEBHOOK_AGE_SECONDS,
) -> bool:
    """Verify the signature of a webhook payload.

    This validates that the webhook payload was sent by the orchestrator
    and has not been tampered with.

    Args:
        payload: The raw request body (JSON string or bytes)
        signature_header: The X-Webhook-Signature header value (e.g., "sha256=abc123...")
        secret: The webhook secret (returned when webhook was created)
        timestamp_header: Optional X-Webhook-Timestamp header for replay protection
        max_age_seconds: Maximum age of webhook in seconds (default: 300 = 5 minutes)

    Returns:
        True if signature is valid

    Raises:
        WebhookSignatureError: If signature is invalid, missing, or payload is too old

    Example:
        >>> from flask import request
        >>> from discord_orchestrator.utils.webhook import verify_webhook_signature
        >>>
        >>> @app.route("/webhook", methods=["POST"])
        >>> def handle_webhook():
        ...     try:
        ...         verify_webhook_signature(
        ...             payload=request.data,
        ...             signature_header=request.headers.get("X-Webhook-Signature", ""),
        ...             secret=WEBHOOK_SECRET,
        ...             timestamp_header=request.headers.get("X-Webhook-Timestamp"),
        ...         )
        ...     except WebhookSignatureError as e:
        ...         return {"error": str(e)}, 401
        ...
        ...     # Process the webhook
        ...     data = request.json
        ...     ...
    """
    # Validate signature header format
    if not signature_header:
        raise WebhookSignatureError("Missing signature header")

    if not signature_header.startswith("sha256="):
        raise WebhookSignatureError("Invalid signature format (expected 'sha256=...')")

    provided_signature = signature_header[7:]  # Remove "sha256=" prefix

    # Convert payload to bytes if string
    if isinstance(payload, str):
        payload_bytes = payload.encode("utf-8")
    else:
        payload_bytes = payload

    # Compute expected signature
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()

    # Use constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(provided_signature, expected_signature):
        raise WebhookSignatureError("Invalid signature")

    # Verify timestamp if provided (replay protection)
    if timestamp_header:
        try:
            timestamp = int(timestamp_header)
            current_time = int(time.time())
            age = current_time - timestamp

            if age > max_age_seconds:
                raise WebhookSignatureError(
                    f"Webhook too old ({age}s > {max_age_seconds}s max)"
                )

            if age < -WEBHOOK_CLOCK_SKEW_TOLERANCE:
                raise WebhookSignatureError("Webhook timestamp is in the future")

        except ValueError:
            raise WebhookSignatureError("Invalid timestamp format")

    return True


def compute_webhook_signature(payload: Union[str, bytes], secret: str) -> str:
    """Compute the HMAC-SHA256 signature for a webhook payload.

    This is useful for testing webhook handlers.

    Args:
        payload: The JSON payload to sign
        secret: The webhook secret

    Returns:
        Signature string in format "sha256=..."

    Example:
        >>> signature = compute_webhook_signature('{"event": "test"}', "my-secret")
        >>> print(signature)
        sha256=abc123...
    """
    if isinstance(payload, str):
        payload_bytes = payload.encode("utf-8")
    else:
        payload_bytes = payload

    signature = hmac.new(
        secret.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()

    return f"sha256={signature}"
