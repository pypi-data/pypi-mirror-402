"""WebSocket API endpoints.

This module provides WebSocket endpoints for real-time updates.

Endpoints:
    WebSocket /ws/notifications/incidents - Real-time escalation incident updates
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from ..core.websocket import (
    WebSocketManager,
    WebSocketMessage,
    WebSocketMessageType,
    get_websocket_manager,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Room name for incident updates
INCIDENTS_ROOM = "incidents"


@router.websocket("/ws/notifications/incidents")
async def websocket_incidents(
    websocket: WebSocket,
    token: str | None = Query(default=None, description="Optional authentication token"),
) -> None:
    """WebSocket endpoint for real-time escalation incident updates.

    This endpoint allows clients to receive real-time updates about escalation
    incidents, including creation, state changes, and resolution.

    Query Parameters:
        token: Optional authentication token for secure connections.

    Message Types Received:
        - ping: Client heartbeat, server responds with pong
        - pong: Response to server ping

    Message Types Sent:
        - connected: Sent when connection is established
        - ping: Server heartbeat
        - pong: Response to client ping
        - incident_created: New incident created
        - incident_updated: Incident updated
        - incident_state_changed: Incident state changed
        - incident_acknowledged: Incident acknowledged
        - incident_escalated: Incident escalated to next level
        - incident_resolved: Incident resolved

    Example Client Connection (JavaScript):
        const ws = new WebSocket('ws://localhost:8765/api/v1/ws/notifications/incidents');

        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            switch (message.type) {
                case 'incident_created':
                    handleNewIncident(message.data);
                    break;
                case 'incident_state_changed':
                    handleStateChange(message.data);
                    break;
                // ... handle other message types
            }
        };

        // Send ping to keep connection alive
        setInterval(() => {
            ws.send(JSON.stringify({ type: 'ping' }));
        }, 30000);
    """
    manager = get_websocket_manager()
    connection_id = str(uuid.uuid4())

    # Optional: Validate token if provided
    # In production, implement proper authentication
    if token:
        logger.debug(f"WebSocket connection with token: {token[:8]}...")

    try:
        # Accept connection and register
        connection = await manager.connect(
            websocket=websocket,
            connection_id=connection_id,
            token=token,
        )

        # Join the incidents room for broadcast updates
        await manager.join_room(connection, INCIDENTS_ROOM)

        logger.info(
            f"Client connected to incidents WebSocket: {connection_id}"
        )

        # Handle incoming messages
        while True:
            try:
                data = await websocket.receive_json()
                await manager.handle_client_message(connection, data)
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.warning(
                    f"Error receiving message from {connection_id}: {e}"
                )
                # Send error message
                await connection.send_message(
                    WebSocketMessage(
                        type=WebSocketMessageType.ERROR,
                        data={"error": str(e)},
                    )
                )

    except WebSocketDisconnect:
        logger.info(f"Client disconnected from incidents WebSocket: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
    finally:
        await manager.disconnect(connection_id, reason="Connection closed")


async def broadcast_incident_event(
    event_type: WebSocketMessageType,
    incident_data: dict[str, Any],
) -> int:
    """Broadcast an incident event to all connected clients.

    Args:
        event_type: Type of the event.
        incident_data: Incident data to broadcast.

    Returns:
        Number of clients that received the message.
    """
    manager = get_websocket_manager()

    message = WebSocketMessage(
        type=event_type,
        data=incident_data,
    )

    return await manager.broadcast_to_room(INCIDENTS_ROOM, message)


async def notify_incident_created(
    incident_id: str,
    incident_ref: str,
    policy_id: str,
    state: str,
    current_level: int,
    context: dict[str, Any] | None = None,
) -> int:
    """Notify clients about a new incident.

    Args:
        incident_id: ID of the new incident.
        incident_ref: External reference.
        policy_id: Associated policy ID.
        state: Initial state.
        current_level: Initial escalation level.
        context: Optional incident context.

    Returns:
        Number of clients notified.
    """
    return await broadcast_incident_event(
        WebSocketMessageType.INCIDENT_CREATED,
        {
            "incident_id": incident_id,
            "incident_ref": incident_ref,
            "policy_id": policy_id,
            "state": state,
            "current_level": current_level,
            "context": context or {},
        },
    )


async def notify_incident_state_changed(
    incident_id: str,
    incident_ref: str,
    policy_id: str,
    from_state: str,
    to_state: str,
    current_level: int,
    actor: str | None = None,
    message: str | None = None,
) -> int:
    """Notify clients about an incident state change.

    Args:
        incident_id: ID of the incident.
        incident_ref: External reference.
        policy_id: Associated policy ID.
        from_state: Previous state.
        to_state: New state.
        current_level: Current escalation level.
        actor: Who triggered the change.
        message: Optional message.

    Returns:
        Number of clients notified.
    """
    # Determine specific event type based on new state
    if to_state == "acknowledged":
        event_type = WebSocketMessageType.INCIDENT_ACKNOWLEDGED
    elif to_state == "resolved":
        event_type = WebSocketMessageType.INCIDENT_RESOLVED
    elif to_state == "escalated":
        event_type = WebSocketMessageType.INCIDENT_ESCALATED
    else:
        event_type = WebSocketMessageType.INCIDENT_STATE_CHANGED

    return await broadcast_incident_event(
        event_type,
        {
            "incident_id": incident_id,
            "incident_ref": incident_ref,
            "policy_id": policy_id,
            "from_state": from_state,
            "to_state": to_state,
            "current_level": current_level,
            "actor": actor,
            "message": message,
        },
    )


async def notify_incident_updated(
    incident_id: str,
    incident_ref: str,
    policy_id: str,
    state: str,
    current_level: int,
    changes: dict[str, Any] | None = None,
) -> int:
    """Notify clients about an incident update.

    Args:
        incident_id: ID of the incident.
        incident_ref: External reference.
        policy_id: Associated policy ID.
        state: Current state.
        current_level: Current escalation level.
        changes: Optional dictionary of changed fields.

    Returns:
        Number of clients notified.
    """
    return await broadcast_incident_event(
        WebSocketMessageType.INCIDENT_UPDATED,
        {
            "incident_id": incident_id,
            "incident_ref": incident_ref,
            "policy_id": policy_id,
            "state": state,
            "current_level": current_level,
            "changes": changes or {},
        },
    )


async def notify_incident_resolved(
    incident_id: str,
    incident_ref: str,
    policy_id: str,
    resolved_by: str | None = None,
    message: str | None = None,
) -> int:
    """Notify clients about an incident resolution.

    Args:
        incident_id: ID of the incident.
        incident_ref: External reference.
        policy_id: Associated policy ID.
        resolved_by: Who resolved it.
        message: Resolution message.

    Returns:
        Number of clients notified.
    """
    return await broadcast_incident_event(
        WebSocketMessageType.INCIDENT_RESOLVED,
        {
            "incident_id": incident_id,
            "incident_ref": incident_ref,
            "policy_id": policy_id,
            "resolved_by": resolved_by,
            "message": message,
        },
    )
