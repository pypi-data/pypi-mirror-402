"""Payload building utilities for the SDK.

Provides helper functions for constructing API payloads with consistent
handling of optional values.
"""

from __future__ import annotations

from typing import Any


def build_payload(**kwargs: Any) -> dict[str, Any]:
    """Build a payload dict, excluding None values.

    This is a convenience function for building API payloads where None
    values should be omitted rather than sent as null.

    Args:
        **kwargs: Key-value pairs for the payload

    Returns:
        Dict containing only non-None values

    Example:
        >>> build_payload(name="test", description=None, count=5)
        {'name': 'test', 'count': 5}
    """
    return {k: v for k, v in kwargs.items() if v is not None}


def build_payload_with_required(
    required: dict[str, Any],
    **optional: Any,
) -> dict[str, Any]:
    """Build a payload with required and optional fields.

    Required fields are always included (even if None).
    Optional fields are only included if not None.

    Args:
        required: Required fields to always include
        **optional: Optional fields to include if not None

    Returns:
        Combined payload dict

    Example:
        >>> build_payload_with_required(
        ...     {"channel_id": "123", "content": "hello"},
        ...     embeds=None,
        ...     reply_to="456"
        ... )
        {'channel_id': '123', 'content': 'hello', 'reply_to': '456'}
    """
    payload = dict(required)
    for k, v in optional.items():
        if v is not None:
            payload[k] = v
    return payload


def merge_payloads(*payloads: dict[str, Any]) -> dict[str, Any]:
    """Merge multiple payloads, excluding None values from all.

    Later payloads override earlier ones for duplicate keys.
    None values are excluded from all payloads.

    Args:
        *payloads: Payload dicts to merge

    Returns:
        Merged payload with no None values

    Example:
        >>> merge_payloads(
        ...     {"a": 1, "b": None},
        ...     {"b": 2, "c": 3}
        ... )
        {'a': 1, 'b': 2, 'c': 3}
    """
    result: dict[str, Any] = {}
    for payload in payloads:
        for k, v in payload.items():
            if v is not None:
                result[k] = v
    return result


def extract_result_data(
    result: Any,
    key: str,
    default: Any = None,
) -> Any:
    """Extract data from a command result.

    Safely extracts nested data from command results with proper
    handling of None and missing keys.

    Args:
        result: Command result object (with .data attribute) or dict
        key: Key to extract from result data
        default: Default value if key not found

    Returns:
        Extracted value or default

    Example:
        >>> extract_result_data(result, "messages", [])
        [...]
    """
    if result is None:
        return default

    # Handle CommandResult objects with .data attribute
    if hasattr(result, "data"):
        data = result.data
    else:
        data = result

    if data is None:
        return default

    if isinstance(data, dict):
        return data.get(key, default)

    return default
