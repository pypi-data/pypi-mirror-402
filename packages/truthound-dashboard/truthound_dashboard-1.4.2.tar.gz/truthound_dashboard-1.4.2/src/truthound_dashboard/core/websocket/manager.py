"""WebSocket connection manager.

This module provides a manager class for handling WebSocket connections,
including connection tracking, room-based broadcasting, and health checks.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from .messages import WebSocketMessage, WebSocketMessageType

logger = logging.getLogger(__name__)


@dataclass
class WebSocketConnection:
    """Represents a WebSocket connection with metadata."""

    websocket: WebSocket
    connection_id: str
    connected_at: datetime = field(default_factory=datetime.utcnow)
    rooms: set[str] = field(default_factory=set)
    last_ping: datetime | None = None
    client_info: dict[str, Any] = field(default_factory=dict)
    token: str | None = None

    async def send_json(self, data: dict[str, Any]) -> bool:
        """Send JSON data to the client.

        Args:
            data: Data to send.

        Returns:
            True if sent successfully, False otherwise.
        """
        try:
            await self.websocket.send_json(data)
            return True
        except Exception as e:
            logger.warning(
                f"Failed to send message to connection {self.connection_id}: {e}"
            )
            return False

    async def send_message(self, message: WebSocketMessage) -> bool:
        """Send a WebSocket message to the client.

        Args:
            message: Message to send.

        Returns:
            True if sent successfully, False otherwise.
        """
        return await self.send_json(message.to_json())


class WebSocketManager:
    """Manager for WebSocket connections.

    Features:
        - Connection tracking
        - Room-based broadcasting
        - Heartbeat/ping-pong
        - Graceful disconnection handling
        - Thread-safe operations

    Example:
        manager = WebSocketManager()

        # Accept a new connection
        conn = await manager.connect(websocket, connection_id)

        # Join a room
        await manager.join_room(conn, "incidents")

        # Broadcast to room
        await manager.broadcast_to_room(
            room="incidents",
            message={"type": "update", "data": {...}},
        )

        # Disconnect
        await manager.disconnect(connection_id)
    """

    def __init__(
        self,
        ping_interval: float = 30.0,
        ping_timeout: float = 10.0,
    ) -> None:
        """Initialize the WebSocket manager.

        Args:
            ping_interval: Interval between heartbeat pings (seconds).
            ping_timeout: Timeout for ping response (seconds).
        """
        self._connections: dict[str, WebSocketConnection] = {}
        self._rooms: dict[str, set[str]] = {}
        self._lock = asyncio.Lock()
        self._ping_interval = ping_interval
        self._ping_timeout = ping_timeout
        self._heartbeat_task: asyncio.Task | None = None
        self._running = False

    @property
    def connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self._connections)

    @property
    def room_count(self) -> int:
        """Get the number of active rooms."""
        return len(self._rooms)

    async def start(self) -> None:
        """Start the manager and heartbeat task."""
        if self._running:
            return

        self._running = True
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info("WebSocket manager started")

    async def stop(self) -> None:
        """Stop the manager and disconnect all clients."""
        if not self._running:
            return

        self._running = False

        # Cancel heartbeat task
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None

        # Disconnect all clients
        connection_ids = list(self._connections.keys())
        for conn_id in connection_ids:
            await self.disconnect(conn_id, reason="Server shutting down")

        logger.info("WebSocket manager stopped")

    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str,
        token: str | None = None,
    ) -> WebSocketConnection:
        """Accept and register a new WebSocket connection.

        Args:
            websocket: The WebSocket instance.
            connection_id: Unique identifier for this connection.
            token: Optional authentication token.

        Returns:
            The registered connection object.
        """
        await websocket.accept()

        connection = WebSocketConnection(
            websocket=websocket,
            connection_id=connection_id,
            token=token,
        )

        async with self._lock:
            self._connections[connection_id] = connection

        logger.info(f"WebSocket connected: {connection_id}")

        # Send connected message
        await connection.send_message(
            WebSocketMessage(
                type=WebSocketMessageType.CONNECTED,
                data={
                    "connection_id": connection_id,
                    "message": "Connected successfully",
                },
            )
        )

        return connection

    async def disconnect(
        self,
        connection_id: str,
        reason: str = "Client disconnected",
    ) -> None:
        """Disconnect and unregister a WebSocket connection.

        Args:
            connection_id: ID of the connection to disconnect.
            reason: Reason for disconnection.
        """
        async with self._lock:
            connection = self._connections.pop(connection_id, None)
            if not connection:
                return

            # Remove from all rooms
            for room in list(connection.rooms):
                if room in self._rooms:
                    self._rooms[room].discard(connection_id)
                    if not self._rooms[room]:
                        del self._rooms[room]

        # Try to close gracefully
        try:
            await connection.websocket.close()
        except Exception:
            pass

        logger.info(f"WebSocket disconnected: {connection_id} ({reason})")

    async def join_room(
        self,
        connection: WebSocketConnection,
        room: str,
    ) -> None:
        """Add a connection to a room.

        Args:
            connection: The connection to add.
            room: Room name.
        """
        async with self._lock:
            if room not in self._rooms:
                self._rooms[room] = set()
            self._rooms[room].add(connection.connection_id)
            connection.rooms.add(room)

        logger.debug(f"Connection {connection.connection_id} joined room: {room}")

    async def leave_room(
        self,
        connection: WebSocketConnection,
        room: str,
    ) -> None:
        """Remove a connection from a room.

        Args:
            connection: The connection to remove.
            room: Room name.
        """
        async with self._lock:
            if room in self._rooms:
                self._rooms[room].discard(connection.connection_id)
                if not self._rooms[room]:
                    del self._rooms[room]
            connection.rooms.discard(room)

        logger.debug(f"Connection {connection.connection_id} left room: {room}")

    async def broadcast(
        self,
        message: WebSocketMessage | dict[str, Any],
        exclude: set[str] | None = None,
    ) -> int:
        """Broadcast a message to all connected clients.

        Args:
            message: Message to broadcast.
            exclude: Set of connection IDs to exclude.

        Returns:
            Number of clients that received the message.
        """
        exclude = exclude or set()

        if isinstance(message, WebSocketMessage):
            data = message.to_json()
        else:
            data = message

        sent_count = 0
        failed_connections: list[str] = []

        async with self._lock:
            connections = list(self._connections.items())

        for conn_id, connection in connections:
            if conn_id in exclude:
                continue

            success = await connection.send_json(data)
            if success:
                sent_count += 1
            else:
                failed_connections.append(conn_id)

        # Clean up failed connections
        for conn_id in failed_connections:
            await self.disconnect(conn_id, reason="Send failed")

        return sent_count

    async def broadcast_to_room(
        self,
        room: str,
        message: WebSocketMessage | dict[str, Any],
        exclude: set[str] | None = None,
    ) -> int:
        """Broadcast a message to all clients in a room.

        Args:
            room: Room name.
            message: Message to broadcast.
            exclude: Set of connection IDs to exclude.

        Returns:
            Number of clients that received the message.
        """
        exclude = exclude or set()

        if isinstance(message, WebSocketMessage):
            data = message.to_json()
        else:
            data = message

        async with self._lock:
            connection_ids = self._rooms.get(room, set()).copy()

        sent_count = 0
        failed_connections: list[str] = []

        for conn_id in connection_ids:
            if conn_id in exclude:
                continue

            async with self._lock:
                connection = self._connections.get(conn_id)

            if not connection:
                continue

            success = await connection.send_json(data)
            if success:
                sent_count += 1
            else:
                failed_connections.append(conn_id)

        # Clean up failed connections
        for conn_id in failed_connections:
            await self.disconnect(conn_id, reason="Send failed")

        return sent_count

    async def send_to_connection(
        self,
        connection_id: str,
        message: WebSocketMessage | dict[str, Any],
    ) -> bool:
        """Send a message to a specific connection.

        Args:
            connection_id: Target connection ID.
            message: Message to send.

        Returns:
            True if sent successfully, False otherwise.
        """
        async with self._lock:
            connection = self._connections.get(connection_id)

        if not connection:
            return False

        if isinstance(message, WebSocketMessage):
            data = message.to_json()
        else:
            data = message

        success = await connection.send_json(data)
        if not success:
            await self.disconnect(connection_id, reason="Send failed")

        return success

    async def _heartbeat_loop(self) -> None:
        """Background task for sending heartbeat pings."""
        while self._running:
            try:
                await asyncio.sleep(self._ping_interval)

                if not self._running:
                    break

                # Send ping to all connections
                async with self._lock:
                    connections = list(self._connections.values())

                ping_message = WebSocketMessage(
                    type=WebSocketMessageType.PING,
                    data={"server_time": datetime.utcnow().isoformat()},
                )

                for connection in connections:
                    connection.last_ping = datetime.utcnow()
                    await connection.send_message(ping_message)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")

    async def handle_client_message(
        self,
        connection: WebSocketConnection,
        data: dict[str, Any],
    ) -> None:
        """Handle an incoming message from a client.

        Args:
            connection: The connection that sent the message.
            data: The message data.
        """
        message_type = data.get("type", "")

        if message_type == WebSocketMessageType.PONG.value:
            # Client responded to ping
            logger.debug(f"Received pong from {connection.connection_id}")
        elif message_type == WebSocketMessageType.PING.value:
            # Client sending ping, respond with pong
            await connection.send_message(
                WebSocketMessage(
                    type=WebSocketMessageType.PONG,
                    data={"server_time": datetime.utcnow().isoformat()},
                )
            )
        else:
            logger.debug(
                f"Received message from {connection.connection_id}: {message_type}"
            )

    def get_connection(self, connection_id: str) -> WebSocketConnection | None:
        """Get a connection by ID.

        Args:
            connection_id: Connection ID.

        Returns:
            The connection or None if not found.
        """
        return self._connections.get(connection_id)

    def get_room_connections(self, room: str) -> list[WebSocketConnection]:
        """Get all connections in a room.

        Args:
            room: Room name.

        Returns:
            List of connections in the room.
        """
        connection_ids = self._rooms.get(room, set())
        return [
            self._connections[conn_id]
            for conn_id in connection_ids
            if conn_id in self._connections
        ]

    def get_status(self) -> dict[str, Any]:
        """Get manager status.

        Returns:
            Dictionary with status information.
        """
        return {
            "running": self._running,
            "connection_count": self.connection_count,
            "room_count": self.room_count,
            "rooms": {room: len(conns) for room, conns in self._rooms.items()},
            "ping_interval": self._ping_interval,
            "ping_timeout": self._ping_timeout,
        }


# Global WebSocket manager instance
_websocket_manager: WebSocketManager | None = None


def get_websocket_manager() -> WebSocketManager:
    """Get the global WebSocket manager instance.

    Returns:
        The WebSocket manager singleton.
    """
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    return _websocket_manager


def reset_websocket_manager() -> None:
    """Reset the global WebSocket manager instance.

    Used for testing.
    """
    global _websocket_manager
    _websocket_manager = None
