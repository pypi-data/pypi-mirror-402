"""Bot management resource."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Optional

from ..exceptions import NotFoundError, TimeoutError
from ..models.bot import Bot, BotStatus
from ..models.command import CommandResult
from .base import BaseResource
from .bot_mixins import (
    MessagingMixin,
    ModerationMixin,
    ChannelsMixin,
    ServerMixin,
    UsersMixin,
)

if TYPE_CHECKING:
    from ..client import OrchestratorClient


class BotInstance(
    MessagingMixin,
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
        self._data = data
        self._resource = resource

    def __getattr__(self, name: str) -> Any:
        """Proxy attribute access to the underlying Bot model."""
        return getattr(self._data, name)

    def __repr__(self) -> str:
        return f"BotInstance(id={self._data.id}, name={self._data.name!r}, status={self._data.status!r})"

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


class BotsResource(BaseResource):
    """Bot management operations.

    Provides methods for creating, listing, managing, and controlling bots.
    """

    def __init__(self, http: Any, client: "OrchestratorClient"):
        """Initialize the bots resource.

        Args:
            http: HTTP client
            client: Parent OrchestratorClient
        """
        super().__init__(http)
        self._client = client

    def list(self) -> list[BotInstance]:
        """List all bots.

        Returns:
            List of BotInstance objects
        """
        response = self._http.get("/bots")
        return [BotInstance(Bot(**b), self) for b in response.get("bots", [])]

    def get(self, bot_id: int) -> BotInstance:
        """Get a bot by ID.

        Args:
            bot_id: Bot identifier

        Returns:
            BotInstance

        Raises:
            NotFoundError: If bot not found
        """
        response = self._http.get(f"/bots/{bot_id}")
        return BotInstance(Bot(**response), self)

    def create(
        self,
        name: str,
        discord_token: str,
        config: Optional[dict[str, Any]] = None,
    ) -> BotInstance:
        """Create a new bot.

        Args:
            name: Bot name
            discord_token: Discord bot token
            config: Bot configuration

        Returns:
            Created BotInstance
        """
        payload = {
            "name": name,
            "discord_token": discord_token,
            "config": config or {},
        }
        response = self._http.post("/bots", json=payload)
        return BotInstance(Bot(**response), self)

    def update(
        self,
        bot_id: int,
        name: Optional[str] = None,
        discord_token: Optional[str] = None,
        config: Optional[dict[str, Any]] = None,
    ) -> BotInstance:
        """Update a bot.

        Args:
            bot_id: Bot identifier
            name: New bot name
            discord_token: New Discord token
            config: New configuration

        Returns:
            Updated BotInstance
        """
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if discord_token is not None:
            payload["discord_token"] = discord_token
        if config is not None:
            payload["config"] = config

        response = self._http.patch(f"/bots/{bot_id}", json=payload)
        return BotInstance(Bot(**response), self)

    def delete(self, bot_id: int) -> None:
        """Delete a bot.

        Args:
            bot_id: Bot identifier
        """
        self._http.delete(f"/bots/{bot_id}")

    def start(self, bot_id: int) -> BotInstance:
        """Start a bot.

        Args:
            bot_id: Bot identifier

        Returns:
            Updated BotInstance
        """
        response = self._http.post(f"/bots/{bot_id}/start")
        return BotInstance(Bot(**response), self)

    def stop(self, bot_id: int) -> BotInstance:
        """Stop a bot.

        Args:
            bot_id: Bot identifier

        Returns:
            Updated BotInstance
        """
        response = self._http.post(f"/bots/{bot_id}/stop")
        return BotInstance(Bot(**response), self)

    def restart(self, bot_id: int) -> BotInstance:
        """Restart a bot.

        Args:
            bot_id: Bot identifier

        Returns:
            Updated BotInstance
        """
        response = self._http.post(f"/bots/{bot_id}/restart")
        return BotInstance(Bot(**response), self)

    def status(self, bot_id: int) -> BotStatus:
        """Get detailed bot status.

        Args:
            bot_id: Bot identifier

        Returns:
            BotStatus with detailed information
        """
        response = self._http.get(f"/bots/{bot_id}/status")
        return BotStatus(**response)

    # --- Idempotent helpers for repeated runs ---

    def find_by_name(self, name: str) -> Optional[BotInstance]:
        """Find a bot by name.

        Uses efficient API lookup. When user_context is set, only searches
        within that user's bots.

        Args:
            name: Bot name to search for

        Returns:
            BotInstance if found, None otherwise
        """
        try:
            return self.get_by_name(name)
        except NotFoundError:
            return None

    def get_by_name(self, name: str) -> BotInstance:
        """Get a bot by name.

        Uses efficient API lookup. When user_context is set, only searches
        within that user's bots.

        Args:
            name: Bot name to search for

        Returns:
            BotInstance

        Raises:
            NotFoundError: If bot not found
        """
        response = self._http.get(f"/bots/by-name/{name}")
        return BotInstance(Bot(**response), self)

    def exists(
        self,
        name: Optional[str] = None,
        bot_id: Optional[int] = None,
    ) -> bool:
        """Check if a bot exists.

        Args:
            name: Bot name to check
            bot_id: Bot ID to check

        Returns:
            True if bot exists, False otherwise

        Raises:
            ValueError: If neither name nor bot_id is provided
        """
        if name:
            return self.find_by_name(name) is not None
        if bot_id:
            try:
                self.get(bot_id)
                return True
            except NotFoundError:
                return False
        raise ValueError("Must provide either name or bot_id")

    def get_or_create(
        self,
        name: str,
        discord_token: Optional[str] = None,
        config: Optional[dict[str, Any]] = None,
    ) -> BotInstance:
        """Get existing bot by name, or create if it doesn't exist.

        This is idempotent - safe to call multiple times in automation workflows.
        The discord_token is only used if creating a new bot.

        Args:
            name: Bot name
            discord_token: Discord token (only required if bot doesn't exist)
            config: Bot configuration (only used for creation)

        Returns:
            BotInstance (existing or newly created)

        Raises:
            ValueError: If bot doesn't exist and no discord_token provided
        """
        existing = self.find_by_name(name)
        if existing:
            return existing
        if not discord_token:
            raise ValueError(
                f"Bot '{name}' not found and no discord_token provided to create it"
            )
        return self.create(name=name, discord_token=discord_token, config=config)

    # --- Auto-start/restart settings ---

    def get_auto_start(self, bot_id: int) -> dict[str, Any]:
        """Get auto-start status for a bot.

        Args:
            bot_id: Bot identifier

        Returns:
            Auto-start status
        """
        return self._http.get(f"/bots/{bot_id}/auto-start")

    def set_auto_start(self, bot_id: int, enabled: bool) -> dict[str, Any]:
        """Set auto-start setting for a bot.

        Args:
            bot_id: Bot identifier
            enabled: Whether to enable auto-start

        Returns:
            Updated auto-start status
        """
        return self._http.put(f"/bots/{bot_id}/auto-start", json={"enabled": enabled})

    def get_auto_restart(self, bot_id: int) -> dict[str, Any]:
        """Get auto-restart status for a bot.

        Args:
            bot_id: Bot identifier

        Returns:
            Auto-restart status
        """
        return self._http.get(f"/bots/{bot_id}/auto-restart")

    def set_auto_restart(self, bot_id: int, enabled: bool) -> dict[str, Any]:
        """Set auto-restart setting for a bot.

        Args:
            bot_id: Bot identifier
            enabled: Whether to enable auto-restart

        Returns:
            Updated auto-restart status
        """
        return self._http.put(f"/bots/{bot_id}/auto-restart", json={"enabled": enabled})

    def reset_auto_restart(self, bot_id: int) -> dict[str, Any]:
        """Reset auto-restart state for a bot.

        Clears the restart attempt counter.

        Args:
            bot_id: Bot identifier

        Returns:
            Reset confirmation
        """
        return self._http.post(f"/bots/{bot_id}/auto-restart/reset")
