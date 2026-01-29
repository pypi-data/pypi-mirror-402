"""Main client for the Discord Bot Orchestrator SDK."""

from __future__ import annotations

from typing import Optional

from .config import OrchestratorConfig
from .resources.bots import BotsResource
from .resources.commands import CommandsResource
from .resources.health import HealthResource
from .resources.interactions import InteractionsResource
from .resources.metrics import MetricsResource
from .resources.slash_commands import SlashCommandsResource
from .resources.webhooks import WebhooksResource
from .utils.http import HTTPClient


class OrchestratorClient:
    """Main client for the Discord Bot Orchestrator API.

    This client provides access to all orchestrator resources through
    intuitive, resource-based interfaces.

    Example:
        >>> from discord_orchestrator import OrchestratorClient
        >>>
        >>> # Initialize client
        >>> client = OrchestratorClient(
        ...     base_url="http://localhost:8000",
        ...     api_key="orc_your_api_key_here"
        ... )
        >>>
        >>> # Check health
        >>> health = client.health.check()
        >>> print(f"Status: {health.status}")
        >>>
        >>> # List bots
        >>> bots = client.bots.list()
        >>> for bot in bots:
        ...     print(f"{bot.name}: {bot.status}")
        >>>
        >>> # Create and start a bot
        >>> bot = client.bots.create(name="MyBot", discord_token="...")
        >>> bot.start()
        >>>
        >>> # Execute a command
        >>> result = bot.execute("send_message", channel_id="123", content="Hello!")
        >>>
        >>> # Clean up
        >>> client.close()

    Attributes:
        bots: Bot management operations
        commands: Command execution operations
        interactions: Interaction response operations (for slash commands)
        metrics: Metrics query operations
        slash_commands: Slash command CRUD operations
        webhooks: Webhook management operations
        health: Health check operations
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        verify_ssl: bool = True,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        user_context: Optional[str] = None,
    ):
        """Initialize the orchestrator client.

        Args:
            base_url: Base URL of the orchestrator API
            api_key: API key for authentication
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries in seconds
            user_context: User context for multi-tenant isolation.
                When set, only bots owned by this user are visible,
                and new bots are automatically assigned to this user.
        """
        self._config = OrchestratorConfig(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            verify_ssl=verify_ssl,
            max_retries=max_retries,
            retry_delay=retry_delay,
            user_context=user_context,
        )
        self._http = HTTPClient(self._config)

        # Initialize resources
        self.bots = BotsResource(self._http, self)
        self.commands = CommandsResource(self._http)
        self.interactions = InteractionsResource(self._http)
        self.metrics = MetricsResource(self._http)
        self.slash_commands = SlashCommandsResource(self._http)
        self.webhooks = WebhooksResource(self._http)
        self.health = HealthResource(self._http)

    @property
    def config(self) -> OrchestratorConfig:
        """Get the client configuration."""
        return self._config

    def close(self) -> None:
        """Close the HTTP session.

        Should be called when done using the client to free resources.
        """
        self._http.close()

    def __enter__(self) -> "OrchestratorClient":
        """Support using client as context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close client when exiting context."""
        self.close()

    def __repr__(self) -> str:
        return f"OrchestratorClient(base_url={self._config.base_url!r})"
