"""Command-related data models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class CommandResult(BaseModel):
    """Result of a synchronous command execution.

    Attributes:
        status: Execution status (success, error)
        data: Result data from the bot
        correlation_id: Unique identifier for tracking
    """

    status: str
    data: Optional[dict[str, Any]] = None
    correlation_id: str


class AsyncCommandResult(BaseModel):
    """Result of an asynchronous command submission.

    Attributes:
        correlation_id: Unique identifier for tracking
        message: Confirmation message
    """

    correlation_id: str
    message: str = "Command sent asynchronously"


class CommandHistory(BaseModel):
    """Historical command execution record.

    Attributes:
        id: Record identifier
        bot_id: Bot that executed the command
        action: Action name
        payload: Command payload
        status: Execution status
        result_data: Result data from execution
        executed_at: Execution timestamp
        correlation_id: Unique tracking identifier
    """

    id: int
    bot_id: int
    action: str
    payload: dict[str, Any] = Field(default_factory=dict)
    status: str
    result_data: Optional[dict[str, Any]] = None
    executed_at: datetime
    correlation_id: str


class ExecuteCommandRequest(BaseModel):
    """Request to execute a command on a bot.

    Attributes:
        bot_id: Target bot ID
        action: Action to execute
        payload: Action payload
        timeout: Execution timeout in seconds
        async_mode: Whether to execute asynchronously
    """

    bot_id: int = Field(..., gt=0)
    action: str = Field(..., min_length=1, max_length=100)
    payload: dict[str, Any] = Field(default_factory=dict)
    timeout: float = Field(default=30.0, ge=1.0, le=300.0)
    async_mode: bool = False
