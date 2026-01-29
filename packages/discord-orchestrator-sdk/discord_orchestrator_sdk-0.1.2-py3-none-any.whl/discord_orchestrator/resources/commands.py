"""Command execution resource."""

from __future__ import annotations

from typing import Any, Optional

from ..models.command import AsyncCommandResult, CommandHistory, CommandResult
from .base import BaseResource


class CommandsResource(BaseResource):
    """Command execution operations.

    Provides methods for executing commands on bots and querying
    command history.
    """

    def execute(
        self,
        bot_id: int,
        action: str,
        payload: Optional[dict[str, Any]] = None,
        timeout: float = 30.0,
    ) -> CommandResult:
        """Execute a command on a bot and wait for the result.

        Args:
            bot_id: Target bot ID
            action: Action name to execute
            payload: Action payload
            timeout: Execution timeout in seconds (1-300)

        Returns:
            CommandResult with execution result

        Example:
            >>> result = client.commands.execute(
            ...     bot_id=1,
            ...     action="send_message",
            ...     payload={"channel_id": "123", "content": "Hello!"}
            ... )
            >>> print(result.status, result.data)
        """
        request = {
            "bot_id": bot_id,
            "action": action,
            "payload": payload or {},
            "timeout": timeout,
            "async_mode": False,
        }
        response = self._http.post("/commands", json=request, timeout=timeout + 5)
        return CommandResult(**response)

    def execute_async(
        self,
        bot_id: int,
        action: str,
        payload: Optional[dict[str, Any]] = None,
    ) -> AsyncCommandResult:
        """Execute a command asynchronously without waiting for result.

        Args:
            bot_id: Target bot ID
            action: Action name to execute
            payload: Action payload

        Returns:
            AsyncCommandResult with correlation ID for tracking

        Example:
            >>> result = client.commands.execute_async(
            ...     bot_id=1,
            ...     action="long_running_task",
            ...     payload={"param": "value"}
            ... )
            >>> print(f"Task submitted: {result.correlation_id}")
        """
        request = {
            "bot_id": bot_id,
            "action": action,
            "payload": payload or {},
            "async_mode": True,
        }
        response = self._http.post("/commands", json=request)
        return AsyncCommandResult(**response)

    def history(
        self,
        bot_id: Optional[int] = None,
        action: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CommandHistory]:
        """Get command execution history.

        Args:
            bot_id: Filter by bot ID
            action: Filter by action name
            status: Filter by status
            limit: Maximum results (default 50, max 500)
            offset: Pagination offset

        Returns:
            List of CommandHistory records
        """
        params: dict[str, Any] = {"limit": min(limit, 500), "offset": offset}
        if bot_id is not None:
            params["bot_id"] = bot_id
        if action is not None:
            params["action"] = action
        if status is not None:
            params["status"] = status

        response = self._http.get("/commands/history", params=params)
        return [CommandHistory(**h) for h in response.get("history", [])]

    def history_for_bot(
        self,
        bot_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CommandHistory]:
        """Get command history for a specific bot.

        Args:
            bot_id: Bot identifier
            limit: Maximum results (default 50, max 500)
            offset: Pagination offset

        Returns:
            List of CommandHistory records for the bot
        """
        params: dict[str, Any] = {"limit": min(limit, 500), "offset": offset}
        response = self._http.get(f"/bots/{bot_id}/history", params=params)
        return [CommandHistory(**h) for h in response.get("history", [])]

    def get_history_detail(self, history_id: int) -> CommandHistory:
        """Get details of a specific command execution.

        Args:
            history_id: Command history record ID

        Returns:
            CommandHistory with full details
        """
        response = self._http.get(f"/commands/history/{history_id}")
        return CommandHistory(**response)
