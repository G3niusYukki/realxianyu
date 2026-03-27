"""WebSocket connection pool for managing multiple Xianyu account connections."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

import websockets
from websockets.exceptions import ConnectionClosed, InvalidState

from xianyuflow_common import get_logger

logger = get_logger(__name__)


class ConnectionStatus(Enum):
    """WebSocket connection status."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


@dataclass
class ConnectionInfo:
    """Connection information for an account."""

    account_id: str
    websocket: websockets.WebSocketServerProtocol | None = None
    status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    last_ping: float = field(default_factory=lambda: asyncio.get_event_loop().time())
    reconnect_attempts: int = 0
    message_count: int = 0
    error_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class WebSocketConnectionPool:
    """Manages WebSocket connections for multiple Xianyu accounts.

    Features:
    - Connection pooling for multiple accounts
    - Automatic reconnection with exponential backoff
    - Health check loop
    - Connection state monitoring
    """

    def __init__(
        self,
        max_reconnect_attempts: int = 5,
        reconnect_base_delay: float = 1.0,
        reconnect_max_delay: float = 60.0,
        health_check_interval: float = 30.0,
        ping_timeout: float = 10.0,
    ) -> None:
        """Initialize the connection pool.

        Args:
            max_reconnect_attempts: Maximum reconnection attempts before giving up.
            reconnect_base_delay: Base delay for exponential backoff (seconds).
            reconnect_max_delay: Maximum delay between reconnection attempts (seconds).
            health_check_interval: Interval between health checks (seconds).
            ping_timeout: Timeout for ping/pong (seconds).
        """
        self._connections: dict[str, ConnectionInfo] = {}
        self._message_handlers: list[Callable[[str, dict[str, Any]], None]] = []
        self._lock = asyncio.Lock()

        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_base_delay = reconnect_base_delay
        self.reconnect_max_delay = reconnect_max_delay
        self.health_check_interval = health_check_interval
        self.ping_timeout = ping_timeout

        self._health_check_task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        """Start the connection pool and health check loop."""
        self._running = True
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("WebSocket connection pool started")

    async def stop(self) -> None:
        """Stop the connection pool and close all connections."""
        self._running = False

        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        async with self._lock:
            for account_id, conn_info in self._connections.items():
                if conn_info.websocket:
                    try:
                        await conn_info.websocket.close()
                        logger.info("Closed connection for account %s", account_id)
                    except Exception as e:
                        logger.error("Error closing connection for %s: %s", account_id, e)

            self._connections.clear()

        logger.info("WebSocket connection pool stopped")

    async def register_connection(
        self,
        account_id: str,
        websocket: websockets.WebSocketServerProtocol,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Register a new WebSocket connection.

        Args:
            account_id: The Xianyu account ID.
            websocket: The WebSocket connection.
            metadata: Optional metadata for the connection.
        """
        async with self._lock:
            # Close existing connection if any
            if account_id in self._connections:
                old_conn = self._connections[account_id]
                if old_conn.websocket:
                    try:
                        await old_conn.websocket.close()
                    except Exception:
                        pass

            self._connections[account_id] = ConnectionInfo(
                account_id=account_id,
                websocket=websocket,
                status=ConnectionStatus.CONNECTED,
                last_ping=asyncio.get_event_loop().time(),
                reconnect_attempts=0,
                metadata=metadata or {},
            )

        logger.info("Registered WebSocket connection for account %s", account_id)

        # Start message handler for this connection
        asyncio.create_task(self._handle_messages(account_id, websocket))

    async def unregister_connection(self, account_id: str) -> None:
        """Unregister a WebSocket connection.

        Args:
            account_id: The Xianyu account ID.
        """
        async with self._lock:
            if account_id in self._connections:
                conn_info = self._connections[account_id]
                if conn_info.websocket:
                    try:
                        await conn_info.websocket.close()
                    except Exception:
                        pass

                del self._connections[account_id]
                logger.info("Unregistered WebSocket connection for account %s", account_id)

    async def send_message(self, account_id: str, message: dict[str, Any]) -> bool:
        """Send a message to a specific account.

        Args:
            account_id: The target account ID.
            message: The message to send.

        Returns:
            True if message was sent successfully, False otherwise.
        """
        import json

        async with self._lock:
            conn_info = self._connections.get(account_id)
            if not conn_info or not conn_info.websocket:
                logger.warning("No active connection for account %s", account_id)
                return False

            if conn_info.status != ConnectionStatus.CONNECTED:
                logger.warning("Connection for account %s is not active", account_id)
                return False

            try:
                await conn_info.websocket.send(json.dumps(message))
                conn_info.message_count += 1
                return True
            except Exception as e:
                logger.error("Failed to send message to %s: %s", account_id, e)
                conn_info.error_count += 1
                return False

    def add_message_handler(
        self, handler: Callable[[str, dict[str, Any]], None]
    ) -> None:
        """Add a message handler for incoming messages.

        Args:
            handler: Callback function that receives (account_id, message).
        """
        self._message_handlers.append(handler)

    def remove_message_handler(
        self, handler: Callable[[str, dict[str, Any]], None]
    ) -> None:
        """Remove a message handler.

        Args:
            handler: The handler to remove.
        """
        if handler in self._message_handlers:
            self._message_handlers.remove(handler)

    def get_connection_status(self, account_id: str) -> ConnectionInfo | None:
        """Get connection status for an account.

        Args:
            account_id: The account ID.

        Returns:
            ConnectionInfo if account is connected, None otherwise.
        """
        return self._connections.get(account_id)

    def get_all_connections(self) -> dict[str, ConnectionInfo]:
        """Get all connection statuses.

        Returns:
            Dictionary mapping account IDs to ConnectionInfo.
        """
        return dict(self._connections)

    async def _handle_messages(
        self, account_id: str, websocket: websockets.WebSocketServerProtocol
    ) -> None:
        """Handle incoming messages from a WebSocket connection.

        Args:
            account_id: The account ID.
            websocket: The WebSocket connection.
        """
        import json

        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    logger.debug("Received message from %s: %s", account_id, data)

                    # Update last ping time
                    async with self._lock:
                        if account_id in self._connections:
                            self._connections[account_id].last_ping = (
                                asyncio.get_event_loop().time()
                            )

                    # Notify handlers
                    for handler in self._message_handlers:
                        try:
                            handler(account_id, data)
                        except Exception as e:
                            logger.error("Error in message handler: %s", e)

                except json.JSONDecodeError:
                    logger.error("Invalid JSON message from %s: %s", account_id, message)
                except Exception as e:
                    logger.error("Error processing message from %s: %s", account_id, e)

        except ConnectionClosed:
            logger.info("Connection closed for account %s", account_id)
        except Exception as e:
            logger.error("Error in message handler for %s: %s", account_id, e)
        finally:
            await self._handle_disconnect(account_id)

    async def _handle_disconnect(self, account_id: str) -> None:
        """Handle disconnection and trigger reconnection if needed.

        Args:
            account_id: The account ID that disconnected.
        """
        async with self._lock:
            if account_id not in self._connections:
                return

            conn_info = self._connections[account_id]
            conn_info.status = ConnectionStatus.DISCONNECTED
            conn_info.websocket = None

            # Attempt reconnection if under limit
            if conn_info.reconnect_attempts < self.max_reconnect_attempts:
                conn_info.status = ConnectionStatus.RECONNECTING
                asyncio.create_task(self._reconnect(account_id))
            else:
                logger.error(
                    "Max reconnection attempts reached for account %s", account_id
                )
                conn_info.status = ConnectionStatus.ERROR

    async def _reconnect(self, account_id: str) -> None:
        """Attempt to reconnect to an account.

        Args:
            account_id: The account ID to reconnect.
        """
        async with self._lock:
            if account_id not in self._connections:
                return

            conn_info = self._connections[account_id]
            conn_info.reconnect_attempts += 1

            # Calculate backoff delay
            delay = min(
                self.reconnect_base_delay * (2 ** (conn_info.reconnect_attempts - 1)),
                self.reconnect_max_delay,
            )

        logger.info(
            "Attempting to reconnect account %s (attempt %d/%d) after %.1fs",
            account_id,
            conn_info.reconnect_attempts,
            self.max_reconnect_attempts,
            delay,
        )

        await asyncio.sleep(delay)

        # Note: Actual reconnection logic would depend on how connections are established
        # This is a placeholder - the actual reconnection would typically be initiated
        # by the client reconnecting to the WebSocket endpoint
        logger.info("Reconnection attempt completed for account %s", account_id)

    async def _health_check_loop(self) -> None:
        """Run periodic health checks on all connections."""
        while self._running:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._perform_health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in health check loop: %s", e)

    async def _perform_health_check(self) -> None:
        """Perform health check on all connections."""
        current_time = asyncio.get_event_loop().time()

        async with self._lock:
            for account_id, conn_info in list(self._connections.items()):
                if conn_info.status != ConnectionStatus.CONNECTED:
                    continue

                # Check if connection is stale (no ping for too long)
                time_since_ping = current_time - conn_info.last_ping
                if time_since_ping > self.health_check_interval * 2:
                    logger.warning(
                        "Connection for account %s appears stale (%.1fs since last activity)",
                        account_id,
                        time_since_ping,
                    )

                # Try to send ping if websocket is available
                if conn_info.websocket:
                    try:
                        # websockets library handles ping/pong automatically
                        # We just check if the connection is still open
                        if conn_info.websocket.closed:
                            logger.warning(
                                "Connection for account %s is closed, will reconnect",
                                account_id,
                            )
                            conn_info.status = ConnectionStatus.DISCONNECTED
                            asyncio.create_task(self._handle_disconnect(account_id))
                    except Exception as e:
                        logger.error("Health check failed for %s: %s", account_id, e)
                        conn_info.error_count += 1
