"""Utility modules for the Discord Bot Orchestrator SDK."""

from .http import HTTPClient
from .pagination import (
    paginate_results,
    Paginator,
    PaginationParams,
)
from .payload import (
    build_payload,
    build_payload_with_required,
    extract_result_data,
    merge_payloads,
)
from .validation import (
    sanitize_error_message,
    validate_bot_name,
    validate_channel_id,
    validate_discord_snowflake,
    validate_discord_token,
    validate_guild_id,
    validate_message_id,
    validate_non_negative_int,
    validate_positive_int,
    validate_url,
    validate_user_id,
    validate_webhook_name,
)
from .webhook import (
    WebhookSignatureError,
    verify_webhook_signature,
    compute_webhook_signature,
)

__all__ = [
    "HTTPClient",
    # Pagination utilities
    "paginate_results",
    "Paginator",
    "PaginationParams",
    # Payload utilities
    "build_payload",
    "build_payload_with_required",
    "extract_result_data",
    "merge_payloads",
    # Validation utilities
    "sanitize_error_message",
    "validate_bot_name",
    "validate_channel_id",
    "validate_discord_snowflake",
    "validate_discord_token",
    "validate_guild_id",
    "validate_message_id",
    "validate_non_negative_int",
    "validate_positive_int",
    "validate_url",
    "validate_user_id",
    "validate_webhook_name",
    # Webhook utilities
    "WebhookSignatureError",
    "verify_webhook_signature",
    "compute_webhook_signature",
]
