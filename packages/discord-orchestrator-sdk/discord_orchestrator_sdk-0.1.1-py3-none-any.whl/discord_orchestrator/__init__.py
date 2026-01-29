"""Discord Bot Orchestrator SDK.

A Python SDK for interacting with the Discord Bot Orchestrator API.

Example:
    >>> from discord_orchestrator import OrchestratorClient
    >>>
    >>> client = OrchestratorClient(
    ...     base_url="http://localhost:8000",
    ...     api_key="orc_your_api_key"
    ... )
    >>>
    >>> # List all bots
    >>> bots = client.bots.list()
    >>>
    >>> # Create and start a bot
    >>> bot = client.bots.create(name="MyBot", discord_token="...")
    >>> bot.start()
    >>>
    >>> # Execute a command
    >>> result = bot.execute("send_message", channel_id="123", content="Hello!")
"""

__version__ = "0.1.0"

from .client import OrchestratorClient
from .config import OrchestratorConfig
from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConnectionError,
    NotFoundError,
    OrchestratorError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
)
from .models.bot import Bot, BotConfig, BotStatus
from .models.command import AsyncCommandResult, CommandHistory, CommandResult
from .models.event import BotEvent, SlashCommandEvent, UserInfo
from .models.metrics import BotMetrics, MetricsSummary, UptimeStats
from .models.webhook import Webhook, WebhookDelivery, WebhookEvent
from .realtime import RealtimeClient
from .resources.bots import BotInstance
from .resources.health import HealthStatus
from .resources.interactions import InteractionResponse
from .resources.slash_commands import SlashCommand, SlashCommandSyncResult
from .resources.webhooks import WebhookInstance

__all__ = [
    # Version
    "__version__",
    # Main client
    "OrchestratorClient",
    "OrchestratorConfig",
    # Exceptions
    "OrchestratorError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "TimeoutError",
    "ServerError",
    "ConnectionError",
    # Bot models
    "Bot",
    "BotConfig",
    "BotStatus",
    "BotInstance",
    # Command models
    "CommandResult",
    "AsyncCommandResult",
    "CommandHistory",
    # Event models
    "BotEvent",
    "SlashCommandEvent",
    "UserInfo",
    # Realtime client
    "RealtimeClient",
    # Metrics models
    "BotMetrics",
    "MetricsSummary",
    "UptimeStats",
    # Webhook models
    "Webhook",
    "WebhookDelivery",
    "WebhookEvent",
    "WebhookInstance",
    # Health
    "HealthStatus",
    # Interaction resources
    "InteractionResponse",
    # Slash command resources
    "SlashCommand",
    "SlashCommandSyncResult",
]
