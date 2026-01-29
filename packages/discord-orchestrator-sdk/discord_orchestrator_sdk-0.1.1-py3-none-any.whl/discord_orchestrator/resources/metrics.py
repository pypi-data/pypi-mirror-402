"""Metrics resource."""

from typing import Any, Optional

from .base import BaseResource


class MetricsResource(BaseResource):
    """Metrics query operations.

    Provides methods for querying bot metrics, uptime statistics,
    and system-wide metrics summaries.
    """

    def get(
        self,
        bot_id: int,
        period: str = "24h",
        resolution: Optional[int] = None,
    ) -> dict[str, Any]:
        """Get historical metrics for a bot.

        Args:
            bot_id: Bot identifier
            period: Time period (1h, 6h, 24h, 7d, 30d)
            resolution: Data point interval in minutes (auto-calculated if not specified)

        Returns:
            Metrics data including:
            - bot_id: Bot identifier
            - period: Time period queried
            - resolution_minutes: Data point resolution
            - count: Number of data points
            - metrics: List of metric data points

        Example:
            >>> metrics = client.metrics.get(bot_id=1, period="24h")
            >>> for point in metrics["metrics"]:
            ...     print(f"{point['timestamp']}: CPU {point['cpu_percent']}%")
        """
        params: dict[str, Any] = {"period": period}
        if resolution is not None:
            params["resolution"] = resolution

        return self._http.get(f"/bots/{bot_id}/metrics", params=params)

    def latest(self, bot_id: int) -> dict[str, Any]:
        """Get the most recent metrics for a bot.

        Args:
            bot_id: Bot identifier

        Returns:
            Latest metrics data including:
            - bot_id: Bot identifier
            - metrics: Most recent metrics (or None if no metrics)
        """
        return self._http.get(f"/bots/{bot_id}/metrics/latest")

    def uptime(self, bot_id: int, period: str = "7d") -> dict[str, Any]:
        """Get uptime statistics for a bot.

        Args:
            bot_id: Bot identifier
            period: Time period (24h, 7d, 30d, 90d)

        Returns:
            Uptime data including:
            - bot_id: Bot identifier
            - period: Time period queried
            - stats: Uptime statistics
            - events: List of uptime events

        Example:
            >>> uptime = client.metrics.uptime(bot_id=1, period="7d")
            >>> print(f"Uptime: {uptime['stats']['uptime_percent']}%")
        """
        params = {"period": period}
        return self._http.get(f"/bots/{bot_id}/uptime", params=params)

    def summary(self) -> dict[str, Any]:
        """Get aggregate metrics across all bots.

        Returns:
            Summary data including:
            - bots: List of per-bot metric summaries
            - totals: Aggregate totals (cpu, memory, guilds, etc.)

        Example:
            >>> summary = client.metrics.summary()
            >>> print(f"Total bots: {summary['totals']['total_bots']}")
            >>> print(f"Running: {summary['totals']['running_bots']}")
        """
        return self._http.get("/metrics/summary")
