"""Data models for escalation system.

This module defines the core data structures for the escalation
system including policies, levels, targets, and incidents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class EscalationState(str, Enum):
    """Escalation incident states.

    State transitions:
        PENDING -> TRIGGERED -> ESCALATED -> RESOLVED
                      |             ^
                      v             |
                 ACKNOWLEDGED ------+
    """

    # Initial state, waiting for trigger
    PENDING = "pending"

    # Escalation started, first level notified
    TRIGGERED = "triggered"

    # Someone acknowledged the alert
    ACKNOWLEDGED = "acknowledged"

    # Moved to next level
    ESCALATED = "escalated"

    # Issue resolved, escalation stopped
    RESOLVED = "resolved"


class TargetType(str, Enum):
    """Types of escalation targets."""

    # Individual user
    USER = "user"

    # Group of users
    GROUP = "group"

    # On-call rotation
    ONCALL = "oncall"

    # Channel (Slack channel, email list, etc.)
    CHANNEL = "channel"


@dataclass
class EscalationTarget:
    """A target for escalation notifications.

    Attributes:
        type: Type of target (user, group, oncall, channel).
        identifier: Target identifier (username, group name, etc.).
        channel: Notification channel type to use.
        channel_id: Optional specific channel ID.
    """

    type: TargetType
    identifier: str
    channel: str
    channel_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "type": self.type.value,
            "identifier": self.identifier,
            "channel": self.channel,
            "channel_id": self.channel_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EscalationTarget":
        """Create from dictionary."""
        return cls(
            type=TargetType(data["type"]),
            identifier=data["identifier"],
            channel=data["channel"],
            channel_id=data.get("channel_id"),
        )


@dataclass
class EscalationLevel:
    """A level in the escalation policy.

    Attributes:
        level: Level number (1 = first, 2 = second, etc.).
        delay_minutes: Minutes to wait before escalating to this level.
        targets: List of targets to notify at this level.
        message_template: Optional custom message template.
    """

    level: int
    delay_minutes: int
    targets: list[EscalationTarget]
    message_template: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "level": self.level,
            "delay_minutes": self.delay_minutes,
            "targets": [t.to_dict() for t in self.targets],
            "message_template": self.message_template,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EscalationLevel":
        """Create from dictionary."""
        return cls(
            level=data["level"],
            delay_minutes=data["delay_minutes"],
            targets=[EscalationTarget.from_dict(t) for t in data.get("targets", [])],
            message_template=data.get("message_template"),
        )


@dataclass
class EscalationPolicy:
    """An escalation policy definition.

    Attributes:
        id: Unique policy identifier.
        name: Human-readable policy name.
        description: Policy description.
        levels: Ordered list of escalation levels.
        auto_resolve_on_success: Auto-resolve when validation succeeds.
        max_escalations: Maximum escalation attempts per incident.
        is_active: Whether policy is active.
    """

    name: str
    levels: list[EscalationLevel]
    id: str | None = None
    description: str = ""
    auto_resolve_on_success: bool = True
    max_escalations: int = 3
    is_active: bool = True

    def get_level(self, level_num: int) -> EscalationLevel | None:
        """Get level by number."""
        for level in self.levels:
            if level.level == level_num:
                return level
        return None

    def get_next_level(self, current_level: int) -> EscalationLevel | None:
        """Get the next escalation level."""
        for level in self.levels:
            if level.level == current_level + 1:
                return level
        return None

    @property
    def max_level(self) -> int:
        """Get highest level number."""
        if not self.levels:
            return 0
        return max(level.level for level in self.levels)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "levels": [level.to_dict() for level in self.levels],
            "auto_resolve_on_success": self.auto_resolve_on_success,
            "max_escalations": self.max_escalations,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EscalationPolicy":
        """Create from dictionary."""
        return cls(
            id=data.get("id"),
            name=data["name"],
            description=data.get("description", ""),
            levels=[EscalationLevel.from_dict(l) for l in data.get("levels", [])],
            auto_resolve_on_success=data.get("auto_resolve_on_success", True),
            max_escalations=data.get("max_escalations", 3),
            is_active=data.get("is_active", True),
        )


@dataclass
class EscalationIncident:
    """An active escalation incident.

    Attributes:
        id: Unique incident identifier.
        policy_id: ID of the escalation policy.
        incident_ref: External reference (e.g., validation_id).
        state: Current incident state.
        current_level: Current escalation level (0 = not yet triggered).
        context: Incident context data.
        acknowledged_by: Who acknowledged the incident.
        resolved_by: Who resolved the incident.
        created_at: When incident was created.
        updated_at: When incident was last updated.
        next_escalation_at: When next escalation will occur.
        escalation_count: Number of times escalated.
        events: History of state changes.
    """

    policy_id: str
    incident_ref: str
    id: str | None = None
    state: EscalationState = EscalationState.PENDING
    current_level: int = 0
    context: dict[str, Any] = field(default_factory=dict)
    acknowledged_by: str | None = None
    acknowledged_at: datetime | None = None
    resolved_by: str | None = None
    resolved_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    next_escalation_at: datetime | None = None
    escalation_count: int = 0
    events: list["EscalationEvent"] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "policy_id": self.policy_id,
            "incident_ref": self.incident_ref,
            "state": self.state.value,
            "current_level": self.current_level,
            "context": self.context,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "next_escalation_at": self.next_escalation_at.isoformat() if self.next_escalation_at else None,
            "escalation_count": self.escalation_count,
            "events": [e.to_dict() for e in self.events],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EscalationIncident":
        """Create from dictionary."""
        return cls(
            id=data.get("id"),
            policy_id=data["policy_id"],
            incident_ref=data["incident_ref"],
            state=EscalationState(data.get("state", "pending")),
            current_level=data.get("current_level", 0),
            context=data.get("context", {}),
            acknowledged_by=data.get("acknowledged_by"),
            acknowledged_at=datetime.fromisoformat(data["acknowledged_at"]) if data.get("acknowledged_at") else None,
            resolved_by=data.get("resolved_by"),
            resolved_at=datetime.fromisoformat(data["resolved_at"]) if data.get("resolved_at") else None,
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.utcnow(),
            next_escalation_at=datetime.fromisoformat(data["next_escalation_at"]) if data.get("next_escalation_at") else None,
            escalation_count=data.get("escalation_count", 0),
            events=[EscalationEvent.from_dict(e) for e in data.get("events", [])],
        )


@dataclass
class EscalationEvent:
    """A state change event in an escalation incident.

    Attributes:
        from_state: Previous state.
        to_state: New state.
        level: Escalation level at time of event.
        actor: Who/what caused the transition.
        message: Event message.
        timestamp: When event occurred.
        metadata: Additional event data.
    """

    from_state: EscalationState
    to_state: EscalationState
    level: int = 0
    actor: str | None = None
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "from_state": self.from_state.value,
            "to_state": self.to_state.value,
            "level": self.level,
            "actor": self.actor,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EscalationEvent":
        """Create from dictionary."""
        return cls(
            from_state=EscalationState(data["from_state"]),
            to_state=EscalationState(data["to_state"]),
            level=data.get("level", 0),
            actor=data.get("actor"),
            message=data.get("message", ""),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.utcnow(),
            metadata=data.get("metadata", {}),
        )


@dataclass
class StateTransition:
    """Defines a valid state transition.

    Attributes:
        from_states: Valid source states.
        to_state: Target state.
        requires_actor: Whether actor info is required.
    """

    from_states: list[EscalationState]
    to_state: EscalationState
    requires_actor: bool = False
