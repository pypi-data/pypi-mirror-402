"""Bot instance wrapper for fluent interface."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Optional

from ..exceptions import TimeoutError
from ..models.bot import Bot, BotStatus
from ..models.command import CommandResult
from .base_instance import ResourceInstance
from .bot_mixins import (
    ChannelsMixin,
    DirectMessagesMixin,
    MessagingMixin,
    ModerationMixin,
    ServerMixin,
    UsersMixin,
)

if TYPE_CHECKING:
    from .bots import BotsResource


class BotInstance(
    ResourceInstance[Bot, "BotsResource"],
    MessagingMixin,
    DirectMessagesMixin,
    ModerationMixin,
    ChannelsMixin,
    ServerMixin,
    UsersMixin,
):
    """Wrapper for a single bot with fluent interface.

    This class provides a convenient way to interact with a bot
    without needing to pass the bot_id to every method call.

    Example:
        >>> bot = client.bots.get(1)
        >>> print(bot.name, bot.status)
        >>> bot.start()
        >>> result = bot.execute("send_message", channel_id="123", content="Hello!")
    """

    def __init__(self, data: Bot, resource: "BotsResource"):
        """Initialize the bot instance.

        Args:
            data: Bot data model
            resource: Parent BotsResource for API calls
        """
        super().__init__(data, resource)

    def __repr__(self) -> str:
        return f"BotInstance(id={self._data.id}, name={self._data.name!r}, status={self._data.status!r})"

    # --- Lifecycle operations ---

    def start(self) -> "BotInstance":
        """Start the bot. Idempotent - safe to call if already running.

        Returns:
            Updated BotInstance
        """
        if self._data.status == "running":
            return self
        return self._resource.start(self._data.id)

    def stop(self) -> "BotInstance":
        """Stop the bot. Idempotent - safe to call if already stopped.

        Returns:
            Updated BotInstance
        """
        if self._data.status == "stopped":
            return self
        return self._resource.stop(self._data.id)

    def restart(self) -> "BotInstance":
        """Restart the bot.

        Returns:
            Updated BotInstance
        """
        return self._resource.restart(self._data.id)

    def get_status(self) -> BotStatus:
        """Get detailed bot status from the API.

        Returns:
            BotStatus with detailed information

        Note:
            Use `bot.status` for the current status string,
            use `bot.get_status()` for detailed status from API.
        """
        return self._resource.status(self._data.id)

    def delete(self) -> None:
        """Delete the bot."""
        self._resource.delete(self._data.id)

    def update(
        self,
        name: Optional[str] = None,
        discord_token: Optional[str] = None,
        config: Optional[dict[str, Any]] = None,
    ) -> "BotInstance":
        """Update the bot.

        Args:
            name: New bot name
            discord_token: New Discord token
            config: New configuration

        Returns:
            Updated BotInstance
        """
        return self._resource.update(
            self._data.id,
            name=name,
            discord_token=discord_token,
            config=config,
        )

    # --- Command execution ---

    def execute(self, action: str, **payload: Any) -> CommandResult:
        """Execute a command on this bot.

        Args:
            action: Action name to execute
            **payload: Action payload as keyword arguments

        Returns:
            CommandResult with execution result
        """
        return self._resource._client.commands.execute(
            bot_id=self._data.id,
            action=action,
            payload=payload,
        )

    def execute_async(self, action: str, **payload: Any) -> str:
        """Execute a command asynchronously on this bot.

        Args:
            action: Action name to execute
            **payload: Action payload as keyword arguments

        Returns:
            Correlation ID for tracking
        """
        result = self._resource._client.commands.execute_async(
            bot_id=self._data.id,
            action=action,
            payload=payload,
        )
        return result.correlation_id

    # --- Metrics ---

    def metrics(self, period: str = "24h") -> dict[str, Any]:
        """Get metrics for this bot.

        Args:
            period: Time period (1h, 6h, 24h, 7d, 30d)

        Returns:
            Metrics data
        """
        return self._resource._client.metrics.get(self._data.id, period=period)

    def uptime(self, period: str = "7d") -> dict[str, Any]:
        """Get uptime statistics for this bot.

        Args:
            period: Time period (24h, 7d, 30d, 90d)

        Returns:
            Uptime data
        """
        return self._resource._client.metrics.uptime(self._data.id, period=period)

    # --- State management ---

    def refresh(self) -> "BotInstance":
        """Refresh bot data from the server.

        Returns:
            Updated BotInstance with fresh data
        """
        refreshed = self._resource.get(self._data.id)
        self._data = refreshed._data
        return self

    def ensure_running(self, timeout: float = 30.0) -> "BotInstance":
        """Ensure the bot is running. Idempotent - safe to call multiple times.

        - If stopped: starts the bot
        - If already running: returns immediately (no-op)
        - If starting: waits for it to be running

        Args:
            timeout: Maximum time to wait for the bot to start

        Returns:
            BotInstance in running state

        Raises:
            TimeoutError: If bot doesn't reach running state within timeout
        """
        self.refresh()

        if self._data.status == "running":
            return self

        if self._data.status in ("stopped", "error"):
            self.start()
            self.refresh()

        # Wait for running state
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._data.status == "running":
                return self
            if self._data.status in ("stopped", "error"):
                self.start()
            time.sleep(1)
            self.refresh()

        raise TimeoutError(
            f"Bot {self._data.id} did not reach running state within {timeout}s"
        )

    # --- Auto-start/restart settings ---

    def set_auto_start(self, enabled: bool) -> dict[str, Any]:
        """Set auto-start setting for this bot.

        Args:
            enabled: Whether to enable auto-start

        Returns:
            Updated auto-start status
        """
        return self._resource.set_auto_start(self._data.id, enabled)

    def set_auto_restart(self, enabled: bool) -> dict[str, Any]:
        """Set auto-restart setting for this bot.

        Args:
            enabled: Whether to enable auto-restart

        Returns:
            Updated auto-restart status
        """
        return self._resource.set_auto_restart(self._data.id, enabled)

    # --- Interactions ---

    def respond_to_command(
        self,
        interaction_id: str,
        content: Optional[str] = None,
        embeds: Optional[list[dict[str, Any]]] = None,
        ephemeral: bool = False,
    ) -> dict[str, Any]:
        """Respond to a slash command interaction.

        This sends a response to a deferred slash command interaction.
        The bot must have already deferred the interaction response.

        Args:
            interaction_id: Discord interaction ID (from SlashCommandEvent)
            content: Text content of the response (max 2000 chars)
            embeds: List of embed dicts (max 10 embeds)
            ephemeral: If True, only the invoking user sees the response

        Returns:
            InteractionResponse with success status

        Example:
            >>> @realtime.on_slash_command
            ... def handle_command(event):
            ...     question = event.options.get("question")
            ...     # Process the question with your own logic
            ...     bot.respond_to_command(
            ...         interaction_id=event.interaction_id,
            ...         content=f"You asked: {question}"
            ...     )
        """
        result = self._resource._client.interactions.respond(
            bot_id=self._data.id,
            interaction_id=interaction_id,
            content=content,
            embeds=embeds,
            ephemeral=ephemeral,
        )
        return {
            "success": result.success,
            "interaction_id": result.interaction_id,
            "message": result.message,
        }
