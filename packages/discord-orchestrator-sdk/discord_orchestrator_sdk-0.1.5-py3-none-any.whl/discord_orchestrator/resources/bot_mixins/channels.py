"""Channel management action mixin for BotInstance."""

from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..bots import BotInstance


class ChannelsMixin:
    """Mixin providing channel management actions for BotInstance.

    Includes: create/edit/delete channels, threads, categories.
    """

    def create_text_channel(
        self: "BotInstance",
        guild_id: str,
        name: str,
        category_id: Optional[str] = None,
        topic: Optional[str] = None,
        slowmode_delay: int = 0,
        nsfw: bool = False,
    ) -> dict[str, Any]:
        """Create a new text channel in a server.

        Args:
            guild_id: Discord server ID
            name: Channel name
            category_id: Parent category ID
            topic: Channel topic/description
            slowmode_delay: Slowmode delay in seconds
            nsfw: Mark as NSFW

        Returns:
            Dict with new channel details
        """
        payload: dict[str, Any] = {
            "guild_id": guild_id,
            "name": name,
            "slowmode_delay": slowmode_delay,
            "nsfw": nsfw,
        }
        if category_id:
            payload["category_id"] = category_id
        if topic:
            payload["topic"] = topic
        result = self.execute("create_text_channel", **payload)
        return result.data or {"success": True}

    def create_voice_channel(
        self: "BotInstance",
        guild_id: str,
        name: str,
        category_id: Optional[str] = None,
        bitrate: int = 64000,
        user_limit: int = 0,
    ) -> dict[str, Any]:
        """Create a new voice channel in a server.

        Args:
            guild_id: Discord server ID
            name: Channel name
            category_id: Parent category ID
            bitrate: Audio bitrate (default 64000)
            user_limit: Max users (0 = unlimited)

        Returns:
            Dict with new channel details
        """
        payload: dict[str, Any] = {
            "guild_id": guild_id,
            "name": name,
            "bitrate": bitrate,
            "user_limit": user_limit,
        }
        if category_id:
            payload["category_id"] = category_id
        result = self.execute("create_voice_channel", **payload)
        return result.data or {"success": True}

    def create_category(
        self: "BotInstance",
        guild_id: str,
        name: str,
    ) -> dict[str, Any]:
        """Create a new category in a server.

        Args:
            guild_id: Discord server ID
            name: Category name

        Returns:
            Dict with new category details
        """
        result = self.execute("create_category", guild_id=guild_id, name=name)
        return result.data or {"success": True}

    def create_thread(
        self: "BotInstance",
        channel_id: str,
        name: str,
        message_id: Optional[str] = None,
        auto_archive_duration: int = 1440,
    ) -> dict[str, Any]:
        """Create a thread in a channel.

        Args:
            channel_id: Discord channel ID
            name: Thread name
            message_id: Optional message ID to create thread from
            auto_archive_duration: Auto-archive duration in minutes (60, 1440, 4320, 10080)

        Returns:
            Dict with thread_id, name, parent_id
        """
        payload: dict[str, Any] = {
            "channel_id": channel_id,
            "name": name,
            "auto_archive_duration": auto_archive_duration,
        }
        if message_id:
            payload["message_id"] = message_id

        result = self.execute("create_thread", **payload)
        return result.data or {"success": True}

    def edit_channel(
        self: "BotInstance",
        channel_id: str,
        name: Optional[str] = None,
        topic: Optional[str] = None,
        slowmode_delay: Optional[int] = None,
        nsfw: Optional[bool] = None,
    ) -> dict[str, Any]:
        """Edit a channel's settings.

        Args:
            channel_id: Discord channel ID
            name: New channel name
            topic: New channel topic
            slowmode_delay: New slowmode delay in seconds
            nsfw: NSFW flag

        Returns:
            Dict with updated channel details
        """
        payload: dict[str, Any] = {"channel_id": channel_id}
        if name is not None:
            payload["name"] = name
        if topic is not None:
            payload["topic"] = topic
        if slowmode_delay is not None:
            payload["slowmode_delay"] = slowmode_delay
        if nsfw is not None:
            payload["nsfw"] = nsfw

        result = self.execute("edit_channel", **payload)
        return result.data or {"success": True}

    def delete_channel(
        self: "BotInstance",
        channel_id: str,
        reason: Optional[str] = None,
    ) -> dict[str, Any]:
        """Delete a channel.

        Args:
            channel_id: Discord channel ID
            reason: Optional audit log reason

        Returns:
            Dict with success status
        """
        payload: dict[str, Any] = {"channel_id": channel_id}
        if reason:
            payload["reason"] = reason

        result = self.execute("delete_channel", **payload)
        return result.data or {"success": True}
