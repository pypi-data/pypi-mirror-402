"""Server/Guild action mixin for BotInstance."""

from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..bots import BotInstance


class ServerMixin:
    """Mixin providing server/guild actions for BotInstance.

    Includes: guild info, invites.
    """

    def get_guild_info(
        self: "BotInstance",
        guild_id: str,
    ) -> dict[str, Any]:
        """Get detailed information about a server.

        Args:
            guild_id: Discord server ID

        Returns:
            Dict with comprehensive guild details
        """
        result = self.execute("get_guild_info", guild_id=guild_id)
        return result.data or {}

    def create_invite(
        self: "BotInstance",
        channel_id: str,
        max_age: int = 86400,
        max_uses: int = 0,
        temporary: bool = False,
        unique: bool = True,
    ) -> dict[str, Any]:
        """Create an invite link for a channel.

        Args:
            channel_id: Discord channel ID
            max_age: Invite expiration in seconds (0 = never)
            max_uses: Max uses (0 = unlimited)
            temporary: Grant temporary membership
            unique: Create unique invite

        Returns:
            Dict with invite details including code and url
        """
        result = self.execute(
            "create_invite",
            channel_id=channel_id,
            max_age=max_age,
            max_uses=max_uses,
            temporary=temporary,
            unique=unique,
        )
        return result.data or {"success": True}

    def get_invites(
        self: "BotInstance",
        guild_id: str,
    ) -> list[dict[str, Any]]:
        """Get all invites for a server.

        Args:
            guild_id: Discord server ID

        Returns:
            List of invite objects
        """
        result = self.execute("get_invites", guild_id=guild_id)
        return result.data.get("invites", []) if result.data else []

    def delete_invite(
        self: "BotInstance",
        invite_code: str,
        reason: Optional[str] = None,
    ) -> dict[str, Any]:
        """Delete an invite link.

        Args:
            invite_code: Invite code to delete
            reason: Audit log reason

        Returns:
            Dict with success status
        """
        payload: dict[str, Any] = {"invite_code": invite_code}
        if reason:
            payload["reason"] = reason
        result = self.execute("delete_invite", **payload)
        return result.data or {"success": True}
