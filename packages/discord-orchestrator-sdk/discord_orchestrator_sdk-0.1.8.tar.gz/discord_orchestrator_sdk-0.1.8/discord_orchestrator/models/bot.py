"""Bot-related data models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class BotConfig(BaseModel):
    """Bot configuration options.

    Attributes:
        auto_start: Whether to start the bot when the orchestrator starts
        auto_restart: Whether to automatically restart on crashes
    """

    auto_start: bool = False
    auto_restart: bool = True


class Bot(BaseModel):
    """Bot data model.

    Attributes:
        id: Unique bot identifier
        name: Bot name
        status: Current status (stopped, starting, running, stopping, error)
        process_pid: Process ID if running
        is_connected: Whether the bot is connected to Discord
        config: Bot configuration
        registered_actions: List of registered action names
        last_heartbeat_at: Timestamp of last heartbeat
        error_message: Error message if in error state
        owner_id: Owner ID for multi-tenant isolation (None for legacy bots)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: int
    name: str
    status: str
    process_pid: Optional[int] = None
    is_connected: bool = False
    config: dict[str, Any] = Field(default_factory=dict)
    registered_actions: list[str] = Field(default_factory=list)
    last_heartbeat_at: Optional[datetime] = None
    error_message: Optional[str] = None
    owner_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def is_running(self) -> bool:
        """Check if the bot is running."""
        return self.status == "running"

    @property
    def is_stopped(self) -> bool:
        """Check if the bot is stopped."""
        return self.status == "stopped"

    @property
    def has_error(self) -> bool:
        """Check if the bot is in an error state."""
        return self.status == "error"


class BotStatus(BaseModel):
    """Detailed bot status information.

    Attributes:
        bot_id: Bot identifier
        status: Current status
        is_connected: Whether connected to Discord
        process_pid: Process ID if running
        last_heartbeat_at: Timestamp of last heartbeat
        connection_info: Additional connection details
    """

    bot_id: int
    status: str
    is_connected: bool = False
    process_pid: Optional[int] = None
    last_heartbeat_at: Optional[datetime] = None
    connection_info: Optional[dict[str, Any]] = None


class CreateBotRequest(BaseModel):
    """Request to create a new bot.

    Attributes:
        name: Bot name
        discord_token: Discord bot token
        config: Bot configuration
    """

    name: str = Field(..., min_length=1, max_length=100)
    discord_token: str = Field(..., min_length=50)
    config: dict[str, Any] = Field(default_factory=dict)


class UpdateBotRequest(BaseModel):
    """Request to update a bot.

    Attributes:
        name: New bot name (optional)
        discord_token: New Discord bot token (optional)
        config: New bot configuration (optional)
    """

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    discord_token: Optional[str] = Field(None, min_length=50)
    config: Optional[dict[str, Any]] = None
