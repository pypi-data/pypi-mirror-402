"""Messaging action mixin for BotInstance."""

from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..bots import BotInstance


class MessagingMixin:
    """Mixin providing messaging actions for BotInstance.

    Includes: send_message, edit_message, delete_message, reactions,
    pins, message history, send_file, send_dm, get_channels, get_guilds.
    """

    def send_message(
        self: "BotInstance",
        channel_id: str,
        content: str,
        embeds: Optional[list[dict[str, Any]]] = None,
        reply_to: Optional[str] = None,
    ) -> dict[str, Any]:
        """Send a message to a channel.

        Args:
            channel_id: Discord channel ID
            content: Message content (max 2000 chars)
            embeds: Optional list of embed dicts
            reply_to: Optional message ID to reply to

        Returns:
            Dict with message_id and other details
        """
        payload: dict[str, Any] = {
            "channel_id": channel_id,
            "content": content,
        }
        if embeds:
            payload["embeds"] = embeds
        if reply_to:
            payload["reply_to"] = reply_to

        result = self.execute("send_message", **payload)
        return result.data or {"success": True}

    def edit_message(
        self: "BotInstance",
        channel_id: str,
        message_id: str,
        content: Optional[str] = None,
        embed: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Edit an existing message.

        Args:
            channel_id: Discord channel ID
            message_id: Message ID to edit
            content: New message content
            embed: New embed object

        Returns:
            Dict with updated message details
        """
        payload: dict[str, Any] = {
            "channel_id": channel_id,
            "message_id": message_id,
        }
        if content is not None:
            payload["content"] = content
        if embed is not None:
            payload["embed"] = embed
        result = self.execute("edit_message", **payload)
        return result.data or {"success": True}

    def delete_message(
        self: "BotInstance",
        channel_id: str,
        message_id: str,
    ) -> dict[str, Any]:
        """Delete a message.

        Args:
            channel_id: Discord channel ID
            message_id: Message ID to delete

        Returns:
            Dict with success status
        """
        result = self.execute(
            "delete_message",
            channel_id=channel_id,
            message_id=message_id,
        )
        return result.data or {"success": True}

    def bulk_delete_messages(
        self: "BotInstance",
        channel_id: str,
        message_ids: list[str],
    ) -> dict[str, Any]:
        """Delete multiple messages at once (max 100, must be < 14 days old).

        Args:
            channel_id: Discord channel ID
            message_ids: List of message IDs to delete

        Returns:
            Dict with deletion summary
        """
        result = self.execute(
            "bulk_delete_messages",
            channel_id=channel_id,
            message_ids=message_ids,
        )
        return result.data or {"success": True}

    def add_reaction(
        self: "BotInstance",
        channel_id: str,
        message_id: str,
        emoji: str,
    ) -> dict[str, Any]:
        """Add a reaction to a message.

        Args:
            channel_id: Discord channel ID
            message_id: Message ID to react to
            emoji: Emoji to add (unicode or custom format)

        Returns:
            Dict with success status
        """
        result = self.execute(
            "add_reaction",
            channel_id=channel_id,
            message_id=message_id,
            emoji=emoji,
        )
        return result.data or {"success": True}

    def remove_reaction(
        self: "BotInstance",
        channel_id: str,
        message_id: str,
        emoji: str,
        user_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Remove a reaction from a message.

        Args:
            channel_id: Discord channel ID
            message_id: Message ID
            emoji: Emoji to remove
            user_id: User ID to remove reaction from (None = bot's own reaction)

        Returns:
            Dict with success status
        """
        payload: dict[str, Any] = {
            "channel_id": channel_id,
            "message_id": message_id,
            "emoji": emoji,
        }
        if user_id:
            payload["user_id"] = user_id
        result = self.execute("remove_reaction", **payload)
        return result.data or {"success": True}

    def clear_reactions(
        self: "BotInstance",
        channel_id: str,
        message_id: str,
        emoji: Optional[str] = None,
    ) -> dict[str, Any]:
        """Clear reactions from a message.

        Args:
            channel_id: Discord channel ID
            message_id: Message ID
            emoji: Specific emoji to clear (None = clear all reactions)

        Returns:
            Dict with success status
        """
        payload: dict[str, Any] = {
            "channel_id": channel_id,
            "message_id": message_id,
        }
        if emoji:
            payload["emoji"] = emoji
        result = self.execute("clear_reactions", **payload)
        return result.data or {"success": True}

    def pin_message(
        self: "BotInstance",
        channel_id: str,
        message_id: str,
    ) -> dict[str, Any]:
        """Pin a message to a channel.

        Args:
            channel_id: Discord channel ID
            message_id: Message ID to pin

        Returns:
            Dict with success status
        """
        result = self.execute(
            "pin_message",
            channel_id=channel_id,
            message_id=message_id,
        )
        return result.data or {"success": True}

    def unpin_message(
        self: "BotInstance",
        channel_id: str,
        message_id: str,
    ) -> dict[str, Any]:
        """Unpin a message from a channel.

        Args:
            channel_id: Discord channel ID
            message_id: Message ID to unpin

        Returns:
            Dict with success status
        """
        result = self.execute(
            "unpin_message",
            channel_id=channel_id,
            message_id=message_id,
        )
        return result.data or {"success": True}

    def get_pinned_messages(
        self: "BotInstance",
        channel_id: str,
    ) -> list[dict[str, Any]]:
        """Get all pinned messages in a channel.

        Args:
            channel_id: Discord channel ID

        Returns:
            List of pinned message objects
        """
        result = self.execute("get_pinned_messages", channel_id=channel_id)
        return result.data.get("pinned_messages", []) if result.data else []

    def get_message_history(
        self: "BotInstance",
        channel_id: str,
        limit: int = 100,
        before_id: Optional[str] = None,
        after_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Get message history from a channel.

        Args:
            channel_id: Discord channel ID
            limit: Max messages to retrieve (1-100)
            before_id: Get messages before this message ID
            after_id: Get messages after this message ID

        Returns:
            List of message objects
        """
        payload: dict[str, Any] = {
            "channel_id": channel_id,
            "limit": limit,
        }
        if before_id:
            payload["before_id"] = before_id
        if after_id:
            payload["after_id"] = after_id
        result = self.execute("get_message_history", **payload)
        return result.data.get("messages", []) if result.data else []

    def send_file(
        self: "BotInstance",
        channel_id: str,
        file_url: str,
        filename: str,
        content: str = "",
    ) -> dict[str, Any]:
        """Send a file to a channel from a URL.

        Args:
            channel_id: Discord channel ID
            file_url: URL of the file to send
            filename: Filename for the attachment
            content: Optional message text with the file

        Returns:
            Dict with message details
        """
        result = self.execute(
            "send_file",
            channel_id=channel_id,
            file_url=file_url,
            filename=filename,
            content=content,
        )
        return result.data or {"success": True}

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
        payload: dict[str, Any] = {
            "user_id": user_id,
            "content": content,
        }
        if embeds:
            payload["embeds"] = embeds

        result = self.execute("send_dm", **payload)
        return result.data or {"success": True}

    def get_channels(
        self: "BotInstance",
        guild_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Get list of channels the bot can see.

        Args:
            guild_id: Filter by specific server ID (optional)

        Returns:
            List of channel objects
        """
        payload: dict[str, Any] = {}
        if guild_id:
            payload["guild_id"] = guild_id
        result = self.execute("get_channels", **payload)
        return result.data.get("channels", []) if result.data else []

    def get_guilds(self: "BotInstance") -> list[dict[str, Any]]:
        """Get list of guilds (servers) the bot is in.

        Returns:
            List of guild objects
        """
        result = self.execute("get_guilds")
        return result.data.get("guilds", []) if result.data else []
