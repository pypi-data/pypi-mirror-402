"""Metrics-related data models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class BotMetrics(BaseModel):
    """Bot metrics data point.

    Attributes:
        timestamp: Measurement timestamp
        cpu_percent: CPU usage percentage
        memory_mb: Memory usage in megabytes
        threads: Number of threads
        guilds: Number of Discord guilds
        latency_ms: Discord API latency in milliseconds
    """

    timestamp: datetime
    cpu_percent: float
    memory_mb: float
    threads: int
    guilds: int
    latency_ms: Optional[float] = None


class MetricsSummary(BaseModel):
    """Summary of bot metrics.

    Attributes:
        bot_id: Bot identifier
        bot_name: Bot name
        status: Current bot status
        is_connected: Whether connected to Discord
        cpu_percent: Current CPU usage
        memory_mb: Current memory usage
        guilds: Current guild count
        latency_ms: Current latency
        last_update: Timestamp of last metrics update
    """

    bot_id: int
    bot_name: str
    status: str
    is_connected: bool
    cpu_percent: Optional[float] = None
    memory_mb: Optional[float] = None
    guilds: Optional[int] = None
    latency_ms: Optional[float] = None
    last_update: Optional[datetime] = None


class UptimeEvent(BaseModel):
    """Uptime event record.

    Attributes:
        event_type: Type of event (started, stopped, connected, etc.)
        timestamp: Event timestamp
        details: Additional event details
    """

    event_type: str
    timestamp: datetime
    details: Optional[dict[str, Any]] = None


class UptimeStats(BaseModel):
    """Uptime statistics for a bot.

    Attributes:
        bot_id: Bot identifier
        period: Time period for statistics
        uptime_percent: Percentage of time bot was running
        total_uptime_seconds: Total seconds running
        total_downtime_seconds: Total seconds not running
        start_count: Number of times started
        crash_count: Number of crashes
        events: Recent uptime events
    """

    bot_id: int
    period: str
    uptime_percent: float
    total_uptime_seconds: float
    total_downtime_seconds: float
    start_count: int = 0
    crash_count: int = 0
    events: list[UptimeEvent] = Field(default_factory=list)


class MetricsResponse(BaseModel):
    """Response for metrics query.

    Attributes:
        bot_id: Bot identifier
        period: Time period queried
        resolution_minutes: Data point resolution
        count: Number of data points
        metrics: List of metric data points
    """

    bot_id: int
    period: str
    resolution_minutes: int
    count: int
    metrics: list[BotMetrics]


class MetricsSummaryResponse(BaseModel):
    """Response for metrics summary query.

    Attributes:
        bots: List of bot metric summaries
        totals: Aggregate totals
    """

    bots: list[MetricsSummary]
    totals: dict[str, Any]
