"""Moderation action mixin for BotInstance."""

from typing import Any, Optional, TYPE_CHECKING

from ...constants import MAX_BANS_LIMIT
from ...models.responses import (
    BanInfo,
    BanResult,
    KickResult,
    RoleInfo,
    SuccessResult,
    TimeoutResult,
    UnbanResult,
)
from ...utils.payload import build_payload

if TYPE_CHECKING:
    from ..bot_instance import BotInstance


class ModerationMixin:
    """Mixin providing moderation actions for BotInstance.

    Includes: kick, ban, timeout, roles, nickname management.
    """

    def kick_member(
        self: "BotInstance",
        guild_id: str,
        user_id: str,
        reason: Optional[str] = None,
    ) -> KickResult:
        """Kick a member from a server.

        Args:
            guild_id: Discord server ID
            user_id: User ID to kick
            reason: Audit log reason

        Returns:
            KickResult with user_id and success status
        """
        payload = build_payload(
            guild_id=guild_id,
            user_id=user_id,
            reason=reason,
        )
        result = self.execute("kick_member", **payload)
        return result.data or {"success": True}

    def ban_member(
        self: "BotInstance",
        guild_id: str,
        user_id: str,
        reason: Optional[str] = None,
        delete_message_days: int = 0,
    ) -> BanResult:
        """Ban a user from a server.

        Args:
            guild_id: Discord server ID
            user_id: User ID to ban
            reason: Audit log reason
            delete_message_days: Days of messages to delete (0-7)

        Returns:
            BanResult with user_id and success status
        """
        payload = build_payload(
            guild_id=guild_id,
            user_id=user_id,
            delete_message_days=delete_message_days,
            reason=reason,
        )
        result = self.execute("ban_member", **payload)
        return result.data or {"success": True}

    def unban_member(
        self: "BotInstance",
        guild_id: str,
        user_id: str,
        reason: Optional[str] = None,
    ) -> UnbanResult:
        """Unban a user from a server.

        Args:
            guild_id: Discord server ID
            user_id: User ID to unban
            reason: Audit log reason

        Returns:
            UnbanResult with user_id and success status
        """
        payload = build_payload(
            guild_id=guild_id,
            user_id=user_id,
            reason=reason,
        )
        result = self.execute("unban_member", **payload)
        return result.data or {"success": True}

    def timeout_member(
        self: "BotInstance",
        guild_id: str,
        user_id: str,
        duration_minutes: int = 10,
        reason: Optional[str] = None,
    ) -> TimeoutResult:
        """Timeout (mute) a member for a specified duration.

        Args:
            guild_id: Discord server ID
            user_id: User ID to timeout
            duration_minutes: Timeout duration in minutes
            reason: Audit log reason

        Returns:
            TimeoutResult with user_id, until timestamp, and success status
        """
        payload = build_payload(
            guild_id=guild_id,
            user_id=user_id,
            duration_minutes=duration_minutes,
            reason=reason,
        )
        result = self.execute("timeout_member", **payload)
        return result.data or {"success": True}

    def remove_timeout(
        self: "BotInstance",
        guild_id: str,
        user_id: str,
        reason: Optional[str] = None,
    ) -> SuccessResult:
        """Remove timeout from a member.

        Args:
            guild_id: Discord server ID
            user_id: User ID to remove timeout from
            reason: Audit log reason

        Returns:
            SuccessResult with success status
        """
        payload = build_payload(
            guild_id=guild_id,
            user_id=user_id,
            reason=reason,
        )
        result = self.execute("remove_timeout", **payload)
        return result.data or {"success": True}

    def get_bans(
        self: "BotInstance",
        guild_id: str,
        limit: int = MAX_BANS_LIMIT,
    ) -> list[BanInfo]:
        """Get list of banned users in a server.

        Args:
            guild_id: Discord server ID
            limit: Max bans to retrieve

        Returns:
            List of BanInfo objects with user and reason
        """
        result = self.execute("get_bans", guild_id=guild_id, limit=limit)
        return result.data.get("bans", []) if result.data else []

    def add_role(
        self: "BotInstance",
        guild_id: str,
        user_id: str,
        role_id: str,
        reason: Optional[str] = None,
    ) -> SuccessResult:
        """Add a role to a member.

        Args:
            guild_id: Discord server ID
            user_id: User ID
            role_id: Role ID to add
            reason: Audit log reason

        Returns:
            SuccessResult with success status
        """
        payload = build_payload(
            guild_id=guild_id,
            user_id=user_id,
            role_id=role_id,
            reason=reason,
        )
        result = self.execute("add_role", **payload)
        return result.data or {"success": True}

    def remove_role(
        self: "BotInstance",
        guild_id: str,
        user_id: str,
        role_id: str,
        reason: Optional[str] = None,
    ) -> SuccessResult:
        """Remove a role from a member.

        Args:
            guild_id: Discord server ID
            user_id: User ID
            role_id: Role ID to remove
            reason: Audit log reason

        Returns:
            SuccessResult with success status
        """
        payload = build_payload(
            guild_id=guild_id,
            user_id=user_id,
            role_id=role_id,
            reason=reason,
        )
        result = self.execute("remove_role", **payload)
        return result.data or {"success": True}

    def create_role(
        self: "BotInstance",
        guild_id: str,
        name: str,
        color: Optional[int] = None,
        permissions: Optional[int] = None,
        hoist: bool = False,
        mentionable: bool = False,
    ) -> RoleInfo:
        """Create a new role in a server.

        Args:
            guild_id: Discord server ID
            name: Role name
            color: Role color (integer)
            permissions: Permission bitfield
            hoist: Display role separately in member list
            mentionable: Allow anyone to mention the role

        Returns:
            RoleInfo with new role details
        """
        payload = build_payload(
            guild_id=guild_id,
            name=name,
            hoist=hoist,
            mentionable=mentionable,
            color=color,
            permissions=permissions,
        )
        result = self.execute("create_role", **payload)
        return result.data or {"success": True}

    def delete_role(
        self: "BotInstance",
        guild_id: str,
        role_id: str,
        reason: Optional[str] = None,
    ) -> SuccessResult:
        """Delete a role from a server.

        Args:
            guild_id: Discord server ID
            role_id: Role ID to delete
            reason: Audit log reason

        Returns:
            SuccessResult with success status
        """
        payload = build_payload(
            guild_id=guild_id,
            role_id=role_id,
            reason=reason,
        )
        result = self.execute("delete_role", **payload)
        return result.data or {"success": True}

    def get_roles(
        self: "BotInstance",
        guild_id: str,
    ) -> list[RoleInfo]:
        """Get all roles in a server.

        Args:
            guild_id: Discord server ID

        Returns:
            List of RoleInfo objects
        """
        result = self.execute("get_roles", guild_id=guild_id)
        return result.data.get("roles", []) if result.data else []

    def change_nickname(
        self: "BotInstance",
        guild_id: str,
        user_id: str,
        nickname: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> SuccessResult:
        """Change a member's nickname.

        Args:
            guild_id: Discord server ID
            user_id: User ID
            nickname: New nickname (None to reset)
            reason: Audit log reason

        Returns:
            SuccessResult with success status
        """
        payload = build_payload(
            guild_id=guild_id,
            user_id=user_id,
            nickname=nickname,
            reason=reason,
        )
        result = self.execute("change_nickname", **payload)
        return result.data or {"success": True}
