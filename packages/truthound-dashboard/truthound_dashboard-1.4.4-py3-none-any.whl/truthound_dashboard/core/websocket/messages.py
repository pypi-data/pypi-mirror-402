"""WebSocket message types and schemas.

This module defines the message types used for WebSocket communication.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class WebSocketMessageType(str, Enum):
    """WebSocket message types for escalation incidents."""

    # Connection lifecycle
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"

    # Incident events
    INCIDENT_CREATED = "incident_created"
    INCIDENT_UPDATED = "incident_updated"
    INCIDENT_STATE_CHANGED = "incident_state_changed"
    INCIDENT_RESOLVED = "incident_resolved"
    INCIDENT_ACKNOWLEDGED = "incident_acknowledged"
    INCIDENT_ESCALATED = "incident_escalated"


class WebSocketMessage(BaseModel):
    """Base WebSocket message schema."""

    type: WebSocketMessageType = Field(..., description="Message type")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Message timestamp (ISO format)",
    )
    data: dict[str, Any] = Field(default_factory=dict, description="Message payload")

    def to_json(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return self.model_dump()


class IncidentCreatedMessage(WebSocketMessage):
    """Message for incident creation."""

    type: WebSocketMessageType = WebSocketMessageType.INCIDENT_CREATED


class IncidentUpdatedMessage(WebSocketMessage):
    """Message for incident updates."""

    type: WebSocketMessageType = WebSocketMessageType.INCIDENT_UPDATED


class IncidentStateChangedMessage(WebSocketMessage):
    """Message for incident state changes.

    Includes from_state and to_state in the data payload.
    """

    type: WebSocketMessageType = WebSocketMessageType.INCIDENT_STATE_CHANGED


class IncidentResolvedMessage(WebSocketMessage):
    """Message for incident resolution."""

    type: WebSocketMessageType = WebSocketMessageType.INCIDENT_RESOLVED


class IncidentAcknowledgedMessage(WebSocketMessage):
    """Message for incident acknowledgement."""

    type: WebSocketMessageType = WebSocketMessageType.INCIDENT_ACKNOWLEDGED


class IncidentEscalatedMessage(WebSocketMessage):
    """Message for incident escalation."""

    type: WebSocketMessageType = WebSocketMessageType.INCIDENT_ESCALATED


def create_incident_message(
    message_type: WebSocketMessageType,
    incident_id: str,
    incident_ref: str,
    policy_id: str,
    state: str,
    current_level: int,
    **extra_data: Any,
) -> WebSocketMessage:
    """Create an incident-related WebSocket message.

    Args:
        message_type: Type of the message.
        incident_id: ID of the incident.
        incident_ref: External reference of the incident.
        policy_id: ID of the escalation policy.
        state: Current state of the incident.
        current_level: Current escalation level.
        **extra_data: Additional data to include.

    Returns:
        WebSocketMessage with the incident data.
    """
    data = {
        "incident_id": incident_id,
        "incident_ref": incident_ref,
        "policy_id": policy_id,
        "state": state,
        "current_level": current_level,
        **extra_data,
    }

    message_classes = {
        WebSocketMessageType.INCIDENT_CREATED: IncidentCreatedMessage,
        WebSocketMessageType.INCIDENT_UPDATED: IncidentUpdatedMessage,
        WebSocketMessageType.INCIDENT_STATE_CHANGED: IncidentStateChangedMessage,
        WebSocketMessageType.INCIDENT_RESOLVED: IncidentResolvedMessage,
        WebSocketMessageType.INCIDENT_ACKNOWLEDGED: IncidentAcknowledgedMessage,
        WebSocketMessageType.INCIDENT_ESCALATED: IncidentEscalatedMessage,
    }

    message_class = message_classes.get(message_type, WebSocketMessage)
    return message_class(type=message_type, data=data)
