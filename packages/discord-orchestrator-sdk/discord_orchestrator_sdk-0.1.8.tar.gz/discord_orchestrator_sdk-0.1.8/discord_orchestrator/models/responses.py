"""Typed response definitions for API responses.

This module provides TypedDict classes for better type hints on API responses,
improving IDE support and catching type errors at development time.
"""

from __future__ import annotations

from typing import Optional
from typing_extensions import NotRequired, TypedDict


# ==============================================================================
# Message-related responses
# ==============================================================================


class MessageResult(TypedDict):
    """Result of sending a message."""

    message_id: str
    channel_id: str
    success: bool


class EditMessageResult(TypedDict):
    """Result of editing a message."""

    message_id: str
    channel_id: str
    content: NotRequired[str]
    success: bool


class DeleteMessageResult(TypedDict):
    """Result of deleting a message."""

    success: bool


class BulkDeleteResult(TypedDict):
    """Result of bulk deleting messages."""

    deleted_count: int
    success: bool


# ==============================================================================
# Channel-related responses
# ==============================================================================


class ChannelInfo(TypedDict):
    """Discord channel information."""

    id: str
    name: str
    type: int
    guild_id: NotRequired[str]
    position: NotRequired[int]
    parent_id: NotRequired[str]
    topic: NotRequired[str]
    nsfw: NotRequired[bool]


class ThreadInfo(TypedDict):
    """Discord thread information."""

    id: str
    name: str
    parent_id: str
    guild_id: str
    owner_id: NotRequired[str]
    message_count: NotRequired[int]
    member_count: NotRequired[int]
    archived: NotRequired[bool]
    locked: NotRequired[bool]


class CreateChannelResult(TypedDict):
    """Result of creating a channel."""

    channel: ChannelInfo
    success: bool


# ==============================================================================
# Guild/Server-related responses
# ==============================================================================


class GuildInfo(TypedDict):
    """Discord guild (server) information."""

    id: str
    name: str
    icon: NotRequired[str]
    owner_id: NotRequired[str]
    member_count: NotRequired[int]
    description: NotRequired[str]


class RoleInfo(TypedDict):
    """Discord role information."""

    id: str
    name: str
    color: int
    permissions: int
    position: NotRequired[int]
    hoist: NotRequired[bool]
    mentionable: NotRequired[bool]


# ==============================================================================
# User-related responses
# ==============================================================================


class UserInfo(TypedDict):
    """Discord user information."""

    id: str
    username: str
    discriminator: NotRequired[str]
    display_name: NotRequired[str]
    avatar: NotRequired[str]
    bot: NotRequired[bool]


class MemberInfo(TypedDict):
    """Discord guild member information."""

    user: UserInfo
    nick: NotRequired[str]
    roles: list[str]
    joined_at: NotRequired[str]
    premium_since: NotRequired[str]


class BanInfo(TypedDict):
    """Discord ban information."""

    user: UserInfo
    reason: NotRequired[str]


# ==============================================================================
# Moderation-related responses
# ==============================================================================


class KickResult(TypedDict):
    """Result of kicking a member."""

    user_id: str
    success: bool


class BanResult(TypedDict):
    """Result of banning a member."""

    user_id: str
    success: bool


class UnbanResult(TypedDict):
    """Result of unbanning a user."""

    user_id: str
    success: bool


class TimeoutResult(TypedDict):
    """Result of timing out a member."""

    user_id: str
    until: NotRequired[str]
    success: bool


# ==============================================================================
# Reaction-related responses
# ==============================================================================


class ReactionResult(TypedDict):
    """Result of adding/removing a reaction."""

    success: bool


class ClearReactionsResult(TypedDict):
    """Result of clearing reactions."""

    success: bool


# ==============================================================================
# Pin-related responses
# ==============================================================================


class PinResult(TypedDict):
    """Result of pinning/unpinning a message."""

    success: bool


class PinnedMessage(TypedDict):
    """A pinned message."""

    id: str
    channel_id: str
    content: str
    author: UserInfo
    pinned_at: NotRequired[str]


# ==============================================================================
# File-related responses
# ==============================================================================


class SendFileResult(TypedDict):
    """Result of sending a file."""

    message_id: str
    channel_id: str
    success: bool


# ==============================================================================
# DM-related responses
# ==============================================================================


class SendDMResult(TypedDict):
    """Result of sending a DM."""

    message_id: str
    channel_id: str
    success: bool


class DMChannelInfo(TypedDict):
    """DM channel information."""

    id: str
    type: int
    recipient: NotRequired[UserInfo]


# ==============================================================================
# Generic success response
# ==============================================================================


class SuccessResult(TypedDict):
    """Generic success response."""

    success: bool
    message: NotRequired[str]


class ErrorResult(TypedDict):
    """Error response."""

    success: bool
    error: str
    code: NotRequired[str]
    details: NotRequired[dict]
