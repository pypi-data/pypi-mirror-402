"""Bot management resource."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from ..exceptions import NotFoundError, ValidationError
from ..models.bot import Bot, BotStatus
from ..utils.payload import build_payload
from ..utils.validation import validate_bot_name, validate_discord_token
from .base import BaseResource
from .bot_instance import BotInstance

if TYPE_CHECKING:
    from ..client import OrchestratorClient

# Re-export BotInstance for backwards compatibility
__all__ = ["BotInstance", "BotsResource"]


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
            name: Bot name (1-100 characters)
            discord_token: Discord bot token (must be valid format)
            config: Bot configuration

        Returns:
            Created BotInstance

        Raises:
            ValidationError: If name or discord_token is invalid
        """
        # Validate inputs before making API call
        if not validate_bot_name(name):
            raise ValidationError(
                f"Invalid bot name: must be 1-100 non-empty characters, got {len(name) if name else 0}"
            )
        if not validate_discord_token(discord_token):
            raise ValidationError(
                "Invalid Discord token format. Token should match the pattern: "
                "base64.base64.base64 (e.g., MTIz...AbC...xyz)"
            )

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
        payload = build_payload(
            name=name,
            discord_token=discord_token,
            config=config,
        )
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
