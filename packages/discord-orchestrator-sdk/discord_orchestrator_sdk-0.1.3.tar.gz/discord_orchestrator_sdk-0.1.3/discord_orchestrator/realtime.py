"""Real-time WebSocket client for receiving bot events."""

from __future__ import annotations

import logging
import threading
from typing import Any, Callable, Optional

try:
    import socketio
except ImportError:
    socketio = None

from .config import OrchestratorConfig
from .models.event import BotEvent, SlashCommandEvent

logger = logging.getLogger(__name__)


class RealtimeClient:
    """WebSocket client for real-time events from bots.

    This client connects to the orchestrator's WebSocket endpoint and
    receives real-time events like slash command invocations.

    Example:
        >>> from discord_orchestrator import OrchestratorClient
        >>> from discord_orchestrator.realtime import RealtimeClient
        >>>
        >>> client = OrchestratorClient(base_url="http://localhost:5000", api_key="...")
        >>> realtime = RealtimeClient(client.config)
        >>>
        >>> # Connect and subscribe to bot events
        >>> realtime.connect()
        >>> realtime.subscribe(bot_id=1)
        >>>
        >>> # Handle slash commands
        >>> @realtime.on_slash_command
        ... def handle_command(event: SlashCommandEvent):
        ...     print(f"Received command: {event.command_name}")
        ...     if event.command_name == "ask":
        ...         question = event.options.get("question")
        ...         # Process and respond...
        >>>
        >>> # Run in background
        >>> realtime.wait()  # Blocks until disconnected
    """

    def __init__(self, config: OrchestratorConfig):
        """Initialize the realtime client.

        Args:
            config: Orchestrator configuration (from OrchestratorClient.config)

        Raises:
            ImportError: If python-socketio is not installed
        """
        if socketio is None:
            raise ImportError(
                "python-socketio is required for real-time features. "
                "Install it with: pip install python-socketio[client]"
            )

        self.config = config
        self._sio: Optional[socketio.Client] = None
        self._connected = False
        self._subscribed_bots: set[int] = set()

        # Event handlers
        self._slash_command_handlers: list[Callable[[SlashCommandEvent], None]] = []
        self._event_handlers: list[Callable[[BotEvent], None]] = []
        self._error_handlers: list[Callable[[dict], None]] = []

        # Thread for background waiting
        self._wait_event = threading.Event()

    @property
    def is_connected(self) -> bool:
        """Check if connected to the orchestrator."""
        return self._connected

    def connect(self) -> None:
        """Connect to the orchestrator WebSocket.

        Raises:
            Exception: If connection fails
        """
        if self._connected:
            logger.warning("Already connected to orchestrator")
            return

        self._sio = socketio.Client(
            logger=False,
            engineio_logger=False,
        )

        # Register event handlers
        self._sio.on("connect", self._on_connect)
        self._sio.on("disconnect", self._on_disconnect)
        self._sio.on("bot_event", self._on_bot_event)
        self._sio.on("subscribed_events", self._on_subscribed)
        self._sio.on("unsubscribed_events", self._on_unsubscribed)
        self._sio.on("error", self._on_error)

        # Build URL (use http for WebSocket as well)
        url = self.config.base_url
        if url.startswith("https://"):
            url = url.replace("https://", "http://", 1)

        logger.info(f"Connecting to orchestrator at {url}")

        self._sio.connect(
            url,
            transports=["polling", "websocket"],
        )

    def disconnect(self) -> None:
        """Disconnect from the orchestrator WebSocket."""
        if not self._connected or self._sio is None:
            return

        # Unsubscribe from all bots first
        for bot_id in list(self._subscribed_bots):
            try:
                self._sio.emit("unsubscribe_events", {"bot_id": bot_id})
            except Exception:
                pass

        self._sio.disconnect()
        self._connected = False
        self._subscribed_bots.clear()
        self._wait_event.set()

        logger.info("Disconnected from orchestrator")

    def subscribe(self, bot_id: int) -> None:
        """Subscribe to events for a specific bot.

        Args:
            bot_id: ID of the bot to subscribe to

        Raises:
            RuntimeError: If not connected
        """
        if not self._connected or self._sio is None:
            raise RuntimeError("Not connected to orchestrator")

        self._sio.emit("subscribe_events", {"bot_id": bot_id})
        logger.info(f"Subscribing to events for bot {bot_id}")

    def unsubscribe(self, bot_id: int) -> None:
        """Unsubscribe from events for a specific bot.

        Args:
            bot_id: ID of the bot to unsubscribe from

        Raises:
            RuntimeError: If not connected
        """
        if not self._connected or self._sio is None:
            raise RuntimeError("Not connected to orchestrator")

        self._sio.emit("unsubscribe_events", {"bot_id": bot_id})
        self._subscribed_bots.discard(bot_id)
        logger.info(f"Unsubscribing from events for bot {bot_id}")

    def on_slash_command(
        self, handler: Callable[[SlashCommandEvent], None]
    ) -> Callable[[SlashCommandEvent], None]:
        """Register a handler for slash command events.

        Can be used as a decorator:
            @realtime.on_slash_command
            def handle_command(event: SlashCommandEvent):
                print(f"Command: {event.command_name}")

        Or called directly:
            realtime.on_slash_command(my_handler)

        Args:
            handler: Function that receives SlashCommandEvent

        Returns:
            The handler function (for decorator use)
        """
        self._slash_command_handlers.append(handler)
        return handler

    def on_event(
        self, handler: Callable[[BotEvent], None]
    ) -> Callable[[BotEvent], None]:
        """Register a handler for all bot events.

        Can be used as a decorator:
            @realtime.on_event
            def handle_event(event: BotEvent):
                print(f"Event: {event.event_type}")

        Args:
            handler: Function that receives BotEvent

        Returns:
            The handler function (for decorator use)
        """
        self._event_handlers.append(handler)
        return handler

    def on_error(
        self, handler: Callable[[dict], None]
    ) -> Callable[[dict], None]:
        """Register a handler for error events.

        Args:
            handler: Function that receives error dict

        Returns:
            The handler function (for decorator use)
        """
        self._error_handlers.append(handler)
        return handler

    def wait(self, timeout: Optional[float] = None) -> bool:
        """Wait until disconnected or timeout.

        This is useful for keeping the main thread alive while
        receiving events in callbacks.

        Args:
            timeout: Maximum time to wait in seconds (None = forever)

        Returns:
            True if wait ended due to disconnect, False if timeout
        """
        self._wait_event.clear()
        return self._wait_event.wait(timeout=timeout)

    def _on_connect(self) -> None:
        """Handle connection established."""
        self._connected = True
        logger.info("Connected to orchestrator WebSocket")

    def _on_disconnect(self) -> None:
        """Handle disconnection."""
        self._connected = False
        self._subscribed_bots.clear()
        self._wait_event.set()
        logger.info("Disconnected from orchestrator WebSocket")

    def _on_bot_event(self, data: dict[str, Any]) -> None:
        """Handle incoming bot event."""
        event = BotEvent.from_dict(data)

        # Call general event handlers
        for handler in self._event_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")

        # If it's a slash command, also call slash command handlers
        if event.event_type == "slash_command":
            slash_event = event.as_slash_command()
            if slash_event:
                for handler in self._slash_command_handlers:
                    try:
                        handler(slash_event)
                    except Exception as e:
                        logger.error(f"Error in slash command handler: {e}")

    def _on_subscribed(self, data: dict[str, Any]) -> None:
        """Handle subscription confirmation."""
        bot_id = data.get("bot_id")
        if bot_id:
            self._subscribed_bots.add(bot_id)
            logger.info(f"Subscribed to events for bot {bot_id}")

    def _on_unsubscribed(self, data: dict[str, Any]) -> None:
        """Handle unsubscription confirmation."""
        bot_id = data.get("bot_id")
        if bot_id:
            self._subscribed_bots.discard(bot_id)
            logger.info(f"Unsubscribed from events for bot {bot_id}")

    def _on_error(self, data: dict[str, Any]) -> None:
        """Handle error from orchestrator."""
        logger.error(f"Orchestrator error: {data}")
        for handler in self._error_handlers:
            try:
                handler(data)
            except Exception as e:
                logger.error(f"Error in error handler: {e}")

    def __enter__(self) -> "RealtimeClient":
        """Support using as context manager."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Disconnect when exiting context."""
        self.disconnect()
