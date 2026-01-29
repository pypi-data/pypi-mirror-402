"""Direct message action mixin for BotInstance."""

from typing import Any, Optional, TYPE_CHECKING

from ...utils.payload import build_payload

if TYPE_CHECKING:
    from ..bot_instance import BotInstance


class DirectMessagesMixin:
    """Mixin providing direct message actions for BotInstance.

    Includes: send_dm, get_dm_channel.
    """

    def send_dm(
        self: "BotInstance",
        user_id: str,
        content: str,
        embeds: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        """Send a direct message to a user.

        Args:
            user_id: Discord user ID
            content: Message content (max 2000 chars)
            embeds: Optional list of embed dicts

        Returns:
            Dict with message_id and other details
        """
        payload = build_payload(
            user_id=user_id,
            content=content,
            embeds=embeds,
        )
        result = self.execute("send_dm", **payload)
        return result.data or {"success": True}

    def get_dm_channel(
        self: "BotInstance",
        user_id: str,
    ) -> dict[str, Any]:
        """Get or create a DM channel with a user.

        Args:
            user_id: Discord user ID

        Returns:
            Dict with channel_id and other channel details
        """
        result = self.execute("get_dm_channel", user_id=user_id)
        return result.data or {}

    def send_dm_with_embed(
        self: "BotInstance",
        user_id: str,
        embed: dict[str, Any],
        content: str = "",
    ) -> dict[str, Any]:
        """Send a DM with an embed.

        Convenience method for sending an embed in a DM.

        Args:
            user_id: Discord user ID
            embed: Embed dict
            content: Optional text content

        Returns:
            Dict with message_id and other details
        """
        return self.send_dm(
            user_id=user_id,
            content=content,
            embeds=[embed],
        )
