"""Configuration classes for the Discord Bot Orchestrator SDK."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class OrchestratorConfig:
    """Configuration for the Orchestrator client.

    Attributes:
        base_url: Base URL of the orchestrator API (default: http://localhost:5000)
        api_key: API key for authentication (optional)
        timeout: Request timeout in seconds (default: 30.0)
        verify_ssl: Whether to verify SSL certificates (default: True)
        max_retries: Maximum number of retry attempts (default: 3)
        retry_delay: Base delay between retries in seconds (default: 1.0)
        user_context: User context for multi-tenant isolation (optional).
            When set, requests include an X-User-Context header that filters
            bot visibility to only bots owned by this user.
    """

    base_url: str = "http://localhost:5000"
    api_key: Optional[str] = None
    timeout: float = 30.0
    verify_ssl: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0
    user_context: Optional[str] = None

    def __post_init__(self):
        """Validate and normalize configuration."""
        # Remove trailing slash from base_url
        self.base_url = self.base_url.rstrip("/")

        # Validate timeout
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")

        # Validate max_retries
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")

        # Validate retry_delay
        if self.retry_delay < 0:
            raise ValueError("retry_delay must be non-negative")
