"""Input validation utilities for the SDK.

Provides validation functions for Discord tokens, URLs, IDs, and other inputs
to catch invalid data early and improve security.
"""

from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urlparse

# Discord bot token format: base64(user_id).base64(timestamp).base64(hmac)
# The token has three parts separated by dots
# - Part 1: Base64 encoded bot user ID (variable length, typically 18+ chars)
# - Part 2: Base64 encoded timestamp (6 chars)
# - Part 3: Base64 encoded HMAC (27+ chars)
DISCORD_TOKEN_PATTERN = re.compile(
    r"^[A-Za-z0-9_-]{24,}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{27,}$"
)

# Discord snowflake IDs are 17-20 digit numbers
DISCORD_SNOWFLAKE_PATTERN = re.compile(r"^\d{17,20}$")

# Maximum lengths for various inputs
MAX_BOT_NAME_LENGTH = 100
MAX_WEBHOOK_NAME_LENGTH = 100
MAX_URL_LENGTH = 2048

# Sensitive data patterns for redaction
SENSITIVE_PATTERNS = [
    # Bearer tokens
    (re.compile(r"Bearer\s+\S+", re.IGNORECASE), "Bearer [REDACTED]"),
    # Discord bot tokens
    (
        re.compile(r"[A-Za-z0-9_-]{24,}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{27,}"),
        "[TOKEN_REDACTED]",
    ),
    # API keys (common patterns)
    (
        re.compile(r"(api[_-]?key|apikey|api_secret)[=:]\s*['\"]?[\w-]+['\"]?", re.IGNORECASE),
        r"\1=[REDACTED]",
    ),
    # Authorization headers in error messages
    (
        re.compile(r"Authorization:\s*\S+", re.IGNORECASE),
        "Authorization: [REDACTED]",
    ),
]


def validate_discord_token(token: str) -> bool:
    """Validate Discord bot token format.

    This validates the token structure, not whether it's actually valid
    with Discord's API. Invalid format tokens will be rejected early.

    Args:
        token: Discord bot token to validate

    Returns:
        True if the token matches the expected format
    """
    if not token or not isinstance(token, str):
        return False
    return bool(DISCORD_TOKEN_PATTERN.match(token))


def validate_discord_snowflake(snowflake_id: str) -> bool:
    """Validate a Discord snowflake ID format.

    Discord IDs (user IDs, channel IDs, guild IDs, message IDs, etc.)
    are snowflake IDs - 64-bit integers represented as strings.

    Args:
        snowflake_id: The ID to validate

    Returns:
        True if the ID matches the expected format
    """
    if not snowflake_id or not isinstance(snowflake_id, str):
        return False
    return bool(DISCORD_SNOWFLAKE_PATTERN.match(snowflake_id))


def validate_channel_id(channel_id: str) -> bool:
    """Validate Discord channel ID format.

    Args:
        channel_id: Channel ID to validate

    Returns:
        True if valid format
    """
    return validate_discord_snowflake(channel_id)


def validate_user_id(user_id: str) -> bool:
    """Validate Discord user ID format.

    Args:
        user_id: User ID to validate

    Returns:
        True if valid format
    """
    return validate_discord_snowflake(user_id)


def validate_guild_id(guild_id: str) -> bool:
    """Validate Discord guild (server) ID format.

    Args:
        guild_id: Guild ID to validate

    Returns:
        True if valid format
    """
    return validate_discord_snowflake(guild_id)


def validate_message_id(message_id: str) -> bool:
    """Validate Discord message ID format.

    Args:
        message_id: Message ID to validate

    Returns:
        True if valid format
    """
    return validate_discord_snowflake(message_id)


def validate_url(
    url: str,
    require_https: bool = False,
    allowed_schemes: Optional[tuple[str, ...]] = None,
) -> bool:
    """Validate URL format.

    Args:
        url: URL to validate
        require_https: If True, only accept HTTPS URLs
        allowed_schemes: Tuple of allowed schemes (default: http, https)

    Returns:
        True if the URL is valid
    """
    if not url or not isinstance(url, str):
        return False

    if len(url) > MAX_URL_LENGTH:
        return False

    try:
        parsed = urlparse(url)

        # Must have scheme and netloc
        if not parsed.scheme or not parsed.netloc:
            return False

        # Check scheme
        if allowed_schemes is None:
            allowed_schemes = ("http", "https")

        if require_https:
            allowed_schemes = ("https",)

        if parsed.scheme.lower() not in allowed_schemes:
            return False

        return True
    except Exception:
        return False


def validate_bot_name(name: str, max_length: int = MAX_BOT_NAME_LENGTH) -> bool:
    """Validate bot name.

    Args:
        name: Bot name to validate
        max_length: Maximum allowed length

    Returns:
        True if the name is valid
    """
    if not name or not isinstance(name, str):
        return False

    # Strip whitespace and check length
    name = name.strip()
    if not name or len(name) > max_length:
        return False

    # Name should not be empty after stripping
    return True


def validate_webhook_name(name: str) -> bool:
    """Validate webhook name.

    Args:
        name: Webhook name to validate

    Returns:
        True if the name is valid
    """
    return validate_bot_name(name, MAX_WEBHOOK_NAME_LENGTH)


def sanitize_error_message(message: str) -> str:
    """Remove potential sensitive data from error messages.

    This helps prevent accidental exposure of tokens, API keys, or other
    sensitive information in error logs or exception messages.

    Args:
        message: Error message that may contain sensitive data

    Returns:
        Sanitized message with sensitive data redacted
    """
    if not message or not isinstance(message, str):
        return message or ""

    sanitized = message
    for pattern, replacement in SENSITIVE_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)

    return sanitized


def validate_positive_int(value: int, name: str = "value") -> int:
    """Validate that a value is a positive integer.

    Args:
        value: Value to validate
        name: Name of the value for error messages

    Returns:
        The validated value

    Raises:
        ValueError: If the value is not a positive integer
    """
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer, got {value}")
    return value


def validate_non_negative_int(value: int, name: str = "value") -> int:
    """Validate that a value is a non-negative integer.

    Args:
        value: Value to validate
        name: Name of the value for error messages

    Returns:
        The validated value

    Raises:
        ValueError: If the value is not a non-negative integer
    """
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer, got {value}")
    return value
