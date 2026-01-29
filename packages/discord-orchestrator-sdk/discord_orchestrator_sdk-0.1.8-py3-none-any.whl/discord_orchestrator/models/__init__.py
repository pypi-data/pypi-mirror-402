"""Data models for the Discord Bot Orchestrator SDK."""

from .bot import Bot, BotConfig, BotStatus, CreateBotRequest, UpdateBotRequest
from .command import AsyncCommandResult, CommandHistory, CommandResult
from .event import BotEvent, SlashCommandEvent, UserInfo
from .metrics import BotMetrics, MetricsSummary, UptimeStats
from .responses import (
    BanInfo,
    BanResult,
    BulkDeleteResult,
    ChannelInfo,
    ClearReactionsResult,
    CreateChannelResult,
    DeleteMessageResult,
    DMChannelInfo,
    EditMessageResult,
    ErrorResult,
    GuildInfo,
    KickResult,
    MemberInfo,
    MessageResult,
    PinnedMessage,
    PinResult,
    ReactionResult,
    RoleInfo,
    SendDMResult,
    SendFileResult,
    SuccessResult,
    ThreadInfo,
    TimeoutResult,
    UnbanResult,
    UserInfo as UserInfoResponse,
)
from .webhook import Webhook, WebhookDelivery, WebhookEvent

__all__ = [
    # Bot models
    "Bot",
    "BotConfig",
    "BotStatus",
    "CreateBotRequest",
    "UpdateBotRequest",
    # Command models
    "CommandResult",
    "AsyncCommandResult",
    "CommandHistory",
    # Event models
    "BotEvent",
    "SlashCommandEvent",
    "UserInfo",
    # Metrics models
    "BotMetrics",
    "MetricsSummary",
    "UptimeStats",
    # Response types (TypedDict)
    "BanInfo",
    "BanResult",
    "BulkDeleteResult",
    "ChannelInfo",
    "ClearReactionsResult",
    "CreateChannelResult",
    "DeleteMessageResult",
    "DMChannelInfo",
    "EditMessageResult",
    "ErrorResult",
    "GuildInfo",
    "KickResult",
    "MemberInfo",
    "MessageResult",
    "PinnedMessage",
    "PinResult",
    "ReactionResult",
    "RoleInfo",
    "SendDMResult",
    "SendFileResult",
    "SuccessResult",
    "ThreadInfo",
    "TimeoutResult",
    "UnbanResult",
    "UserInfoResponse",
    # Webhook models
    "Webhook",
    "WebhookDelivery",
    "WebhookEvent",
]
