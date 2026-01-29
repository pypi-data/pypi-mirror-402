"""Event models for real-time events from the orchestrator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class UserInfo:
    """Information about a Discord user."""

    id: str
    username: str
    display_name: str


@dataclass
class SlashCommandEvent:
    """Event data for a slash command invocation.

    Attributes:
        interaction_id: Discord interaction ID (needed for responding)
        interaction_token: Discord interaction token (for extended responses)
        command_name: Name of the invoked command
        user: Information about the user who invoked the command
        channel_id: ID of the channel where command was invoked
        guild_id: ID of the guild (server) where command was invoked (None in DMs)
        options: Command options/arguments provided by the user
    """

    interaction_id: str
    command_name: str
    user: UserInfo
    options: dict[str, Any] = field(default_factory=dict)
    channel_id: Optional[str] = None
    guild_id: Optional[str] = None
    interaction_token: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SlashCommandEvent":
        """Create a SlashCommandEvent from a dictionary."""
        user_data = data.get("user", {})
        user = UserInfo(
            id=user_data.get("id", ""),
            username=user_data.get("username", ""),
            display_name=user_data.get("display_name", ""),
        )

        return cls(
            interaction_id=data.get("interaction_id", ""),
            interaction_token=data.get("interaction_token"),
            command_name=data.get("command_name", ""),
            user=user,
            channel_id=data.get("channel_id"),
            guild_id=data.get("guild_id"),
            options=data.get("options", {}),
        )


@dataclass
class BotEvent:
    """Generic event from a bot.

    Attributes:
        bot_id: ID of the bot that emitted the event
        event_type: Type of event (e.g., "slash_command", "message", etc.)
        data: Event data (structure depends on event_type)
    """

    bot_id: int
    event_type: str
    data: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BotEvent":
        """Create a BotEvent from a dictionary."""
        return cls(
            bot_id=data.get("bot_id", 0),
            event_type=data.get("event_type", ""),
            data=data.get("data", {}),
        )

    def as_slash_command(self) -> Optional[SlashCommandEvent]:
        """Convert to SlashCommandEvent if this is a slash_command event."""
        if self.event_type != "slash_command":
            return None
        return SlashCommandEvent.from_dict(self.data)
