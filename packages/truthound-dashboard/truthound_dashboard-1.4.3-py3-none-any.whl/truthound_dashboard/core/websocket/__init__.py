"""WebSocket support for real-time updates.

This module provides WebSocket infrastructure for broadcasting real-time
updates to connected clients.

Features:
    - Connection management (track active connections, handle disconnects)
    - Room-based broadcasting for targeted updates
    - Heartbeat/ping-pong for connection health
    - Optional token-based authentication
    - Support for multiple concurrent clients

Example:
    from truthound_dashboard.core.websocket import (
        WebSocketManager,
        get_websocket_manager,
    )

    # Get the global manager
    manager = get_websocket_manager()

    # Broadcast to all clients in a room
    await manager.broadcast_to_room(
        room="incidents",
        message={"type": "incident_updated", "data": {...}},
    )
"""

from .manager import (
    WebSocketConnection,
    WebSocketManager,
    get_websocket_manager,
    reset_websocket_manager,
)
from .messages import (
    IncidentCreatedMessage,
    IncidentResolvedMessage,
    IncidentStateChangedMessage,
    IncidentUpdatedMessage,
    WebSocketMessage,
    WebSocketMessageType,
    create_incident_message,
)

__all__ = [
    # Manager
    "WebSocketConnection",
    "WebSocketManager",
    "get_websocket_manager",
    "reset_websocket_manager",
    # Messages
    "WebSocketMessage",
    "WebSocketMessageType",
    "IncidentCreatedMessage",
    "IncidentUpdatedMessage",
    "IncidentStateChangedMessage",
    "IncidentResolvedMessage",
    "create_incident_message",
]
