"""User/Member action mixin for BotInstance."""

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..bots import BotInstance


class UsersMixin:
    """Mixin providing user/member actions for BotInstance.

    Includes: get user info, get member info, list members.
    """

    def get_user_info(
        self: "BotInstance",
        user_id: str,
    ) -> dict[str, Any]:
        """Get information about a Discord user.

        Args:
            user_id: Discord user ID

        Returns:
            Dict with user profile details
        """
        result = self.execute("get_user_info", user_id=user_id)
        return result.data or {}

    def get_member_info(
        self: "BotInstance",
        guild_id: str,
        user_id: str,
    ) -> dict[str, Any]:
        """Get detailed information about a server member.

        Args:
            guild_id: Discord server ID
            user_id: User ID

        Returns:
            Dict with member details including roles, nickname, etc.
        """
        result = self.execute(
            "get_member_info",
            guild_id=guild_id,
            user_id=user_id,
        )
        return result.data or {}

    def get_members(
        self: "BotInstance",
        guild_id: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get list of members in a server.

        Args:
            guild_id: Discord server ID
            limit: Max members to retrieve

        Returns:
            List of member objects
        """
        result = self.execute("get_members", guild_id=guild_id, limit=limit)
        return result.data.get("members", []) if result.data else []
