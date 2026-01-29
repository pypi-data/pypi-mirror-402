"""Health check resource."""

from __future__ import annotations

from typing import Any

from .base import BaseResource


class HealthStatus:
    """Health check result.

    Attributes:
        status: Overall health status (healthy, degraded)
        version: Orchestrator version
        database: Database status
        websocket: WebSocket status
        bots_total: Total number of bots
        bots_running: Number of running bots
        bots_connected: Number of connected bots
    """

    def __init__(self, data: dict[str, Any]):
        self.status = data.get("status", "unknown")
        self.version = data.get("version", "unknown")
        self.database = data.get("database", "unknown")
        self.websocket = data.get("websocket", "unknown")
        self.bots_total = data.get("bots_total", 0)
        self.bots_running = data.get("bots_running", 0)
        self.bots_connected = data.get("bots_connected", 0)

    @property
    def is_healthy(self) -> bool:
        """Check if the system is healthy."""
        return self.status == "healthy"

    @property
    def is_degraded(self) -> bool:
        """Check if the system is degraded."""
        return self.status == "degraded"

    def __repr__(self) -> str:
        return (
            f"HealthStatus(status={self.status!r}, version={self.version!r}, "
            f"bots_running={self.bots_running}/{self.bots_total})"
        )


class HealthResource(BaseResource):
    """Health check operations."""

    def check(self) -> HealthStatus:
        """Check the health of the orchestrator.

        Returns:
            HealthStatus object with system health information

        Example:
            >>> health = client.health.check()
            >>> print(f"Status: {health.status}")
            >>> if health.is_healthy:
            ...     print("All systems operational")
        """
        response = self._http.get_root("/health")
        return HealthStatus(response)

    def ready(self) -> bool:
        """Check if the orchestrator is ready to accept requests.

        Returns:
            True if ready, False otherwise
        """
        try:
            response = self._http.get_root("/ready")
            return response.get("ready", False)
        except Exception:
            return False

    def live(self) -> bool:
        """Check if the orchestrator is alive.

        Returns:
            True if alive, False otherwise
        """
        try:
            response = self._http.get_root("/live")
            return response.get("alive", False)
        except Exception:
            return False
