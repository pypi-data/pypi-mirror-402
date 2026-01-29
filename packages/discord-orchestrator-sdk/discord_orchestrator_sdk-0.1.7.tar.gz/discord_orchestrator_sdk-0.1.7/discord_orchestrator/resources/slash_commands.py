"""Slash command management resource."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .base import BaseResource


@dataclass
class SlashCommandOption:
    """A slash command option/argument definition."""

    name: str
    description: str
    type: int  # Discord option types: 3=string, 4=int, 5=bool, 6=user, etc.
    required: bool = False
    choices: Optional[list[dict[str, Any]]] = None


@dataclass
class SlashCommand:
    """A registered slash command."""

    id: int
    bot_id: int
    name: str
    description: str
    options: list[dict[str, Any]] = field(default_factory=list)
    enabled: bool = True
    discord_command_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SlashCommand":
        """Create from API response dict."""
        return cls(
            id=data.get("id", 0),
            bot_id=data.get("bot_id", 0),
            name=data.get("name", ""),
            description=data.get("description", ""),
            options=data.get("options", []),
            enabled=data.get("enabled", True),
            discord_command_id=data.get("discord_command_id"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


@dataclass
class SlashCommandSyncResult:
    """Result of syncing slash commands to Discord."""

    message: str
    synced_count: int
    commands: list[SlashCommand]


class SlashCommandsResource(BaseResource):
    """Resource for managing slash commands for bots.

    Example:
        >>> # Create a slash command
        >>> cmd = client.slash_commands.create(
        ...     bot_id=1,
        ...     name="ask",
        ...     description="Ask a question",
        ...     options=[
        ...         {"name": "question", "description": "Your question", "type": 3, "required": True}
        ...     ]
        ... )
        >>> print(f"Created command: {cmd.name}")
        >>>
        >>> # Sync commands to Discord
        >>> result = client.slash_commands.sync(bot_id=1)
        >>> print(f"Synced {result.synced_count} commands")
    """

    def list(self, bot_id: int) -> list[SlashCommand]:
        """List all slash commands for a bot.

        Args:
            bot_id: Bot ID

        Returns:
            List of SlashCommand objects
        """
        response = self._http.get(f"/bots/{bot_id}/slash-commands")
        commands = response.get("commands", [])
        return [SlashCommand.from_dict(c) for c in commands]

    def create(
        self,
        bot_id: int,
        name: str,
        description: str,
        options: Optional[list[dict[str, Any]]] = None,
    ) -> SlashCommand:
        """Create a new slash command for a bot.

        Args:
            bot_id: Bot ID
            name: Command name (1-32 chars, lowercase, no spaces)
            description: Command description (1-100 chars)
            options: List of option definitions (optional)

        Returns:
            Created SlashCommand object
        """
        response = self._http.post(
            f"/bots/{bot_id}/slash-commands",
            json={
                "name": name,
                "description": description,
                "options": options or [],
            },
        )
        return SlashCommand.from_dict(response)

    def get(self, bot_id: int, command_id: int) -> SlashCommand:
        """Get a specific slash command.

        Args:
            bot_id: Bot ID
            command_id: Command ID

        Returns:
            SlashCommand object
        """
        response = self._http.get(f"/bots/{bot_id}/slash-commands/{command_id}")
        return SlashCommand.from_dict(response)

    def update(
        self,
        bot_id: int,
        command_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        options: Optional[list[dict[str, Any]]] = None,
        enabled: Optional[bool] = None,
    ) -> SlashCommand:
        """Update a slash command.

        Args:
            bot_id: Bot ID
            command_id: Command ID
            name: New command name
            description: New description
            options: New options list
            enabled: Whether command is enabled

        Returns:
            Updated SlashCommand object
        """
        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if options is not None:
            data["options"] = options
        if enabled is not None:
            data["enabled"] = enabled

        response = self._http.patch(
            f"/bots/{bot_id}/slash-commands/{command_id}",
            json=data,
        )
        return SlashCommand.from_dict(response)

    def delete(self, bot_id: int, command_id: int) -> None:
        """Delete a slash command.

        Args:
            bot_id: Bot ID
            command_id: Command ID
        """
        self._http.delete(f"/bots/{bot_id}/slash-commands/{command_id}")

    def sync(self, bot_id: int) -> SlashCommandSyncResult:
        """Sync all enabled slash commands to Discord.

        This registers/updates all enabled slash commands with Discord's API.
        The bot must be running and connected.

        Args:
            bot_id: Bot ID

        Returns:
            SlashCommandSyncResult with synced commands

        Raises:
            RuntimeError: If bot is not connected
        """
        response = self._http.post(f"/bots/{bot_id}/slash-commands/sync")
        commands = [SlashCommand.from_dict(c) for c in response.get("commands", [])]
        return SlashCommandSyncResult(
            message=response.get("message", ""),
            synced_count=response.get("synced_count", 0),
            commands=commands,
        )

    # --- Idempotent helpers for automation workflows ---

    def find_by_name(self, bot_id: int, name: str) -> Optional[SlashCommand]:
        """Find a slash command by name.

        Args:
            bot_id: Bot ID
            name: Command name to search for

        Returns:
            SlashCommand if found, None otherwise
        """
        commands = self.list(bot_id)
        for cmd in commands:
            if cmd.name == name:
                return cmd
        return None

    def get_or_create(
        self,
        bot_id: int,
        name: str,
        description: str,
        options: Optional[list[dict[str, Any]]] = None,
    ) -> SlashCommand:
        """Get existing slash command by name, or create if it doesn't exist.

        This is idempotent - safe to call multiple times in automation workflows.
        If the command exists, returns it without modification.

        Args:
            bot_id: Bot ID
            name: Command name
            description: Command description (only used for creation)
            options: Command options (only used for creation)

        Returns:
            SlashCommand (existing or newly created)
        """
        existing = self.find_by_name(bot_id, name)
        if existing:
            return existing
        return self.create(bot_id, name, description, options)

    def ensure(
        self,
        bot_id: int,
        name: str,
        description: str,
        options: Optional[list[dict[str, Any]]] = None,
    ) -> SlashCommand:
        """Ensure a slash command exists with the specified definition.

        This is idempotent - safe to call multiple times. If the command exists,
        it will be updated to match the provided definition. If it doesn't exist,
        it will be created.

        Args:
            bot_id: Bot ID
            name: Command name
            description: Command description
            options: Command options

        Returns:
            SlashCommand (created or updated to match definition)
        """
        existing = self.find_by_name(bot_id, name)
        if existing:
            # Update to match the provided definition
            return self.update(
                bot_id=bot_id,
                command_id=existing.id,
                description=description,
                options=options,
            )
        return self.create(bot_id, name, description, options)
