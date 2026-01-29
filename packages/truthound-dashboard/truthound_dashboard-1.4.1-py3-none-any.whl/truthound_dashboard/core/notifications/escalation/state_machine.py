"""State machine for escalation incident lifecycle.

This module implements the state machine that controls valid
state transitions for escalation incidents.

State Transitions:
    PENDING -> TRIGGERED (trigger)
    TRIGGERED -> ACKNOWLEDGED (acknowledge)
    TRIGGERED -> ESCALATED (escalate)
    TRIGGERED -> RESOLVED (resolve)
    ACKNOWLEDGED -> ESCALATED (escalate)
    ACKNOWLEDGED -> RESOLVED (resolve)
    ESCALATED -> ACKNOWLEDGED (acknowledge)
    ESCALATED -> ESCALATED (escalate to next level)
    ESCALATED -> RESOLVED (resolve)
"""

from __future__ import annotations

from datetime import datetime
from typing import Callable

from .models import (
    EscalationEvent,
    EscalationIncident,
    EscalationState,
    StateTransition,
)


class EscalationStateMachine:
    """State machine for escalation incident lifecycle.

    Validates and executes state transitions for incidents.
    Maintains transition history via events.

    Example:
        machine = EscalationStateMachine()

        # Trigger incident
        incident = machine.trigger(incident)

        # Acknowledge
        incident = machine.acknowledge(incident, actor="user@example.com")

        # Resolve
        incident = machine.resolve(incident, actor="user@example.com")
    """

    # Define valid state transitions
    VALID_TRANSITIONS: list[StateTransition] = [
        # PENDING -> TRIGGERED
        StateTransition(
            from_states=[EscalationState.PENDING],
            to_state=EscalationState.TRIGGERED,
        ),
        # TRIGGERED -> ACKNOWLEDGED
        StateTransition(
            from_states=[EscalationState.TRIGGERED],
            to_state=EscalationState.ACKNOWLEDGED,
            requires_actor=True,
        ),
        # TRIGGERED -> ESCALATED
        StateTransition(
            from_states=[EscalationState.TRIGGERED],
            to_state=EscalationState.ESCALATED,
        ),
        # TRIGGERED -> RESOLVED
        StateTransition(
            from_states=[EscalationState.TRIGGERED],
            to_state=EscalationState.RESOLVED,
        ),
        # ACKNOWLEDGED -> ESCALATED
        StateTransition(
            from_states=[EscalationState.ACKNOWLEDGED],
            to_state=EscalationState.ESCALATED,
        ),
        # ACKNOWLEDGED -> RESOLVED
        StateTransition(
            from_states=[EscalationState.ACKNOWLEDGED],
            to_state=EscalationState.RESOLVED,
        ),
        # ESCALATED -> ACKNOWLEDGED
        StateTransition(
            from_states=[EscalationState.ESCALATED],
            to_state=EscalationState.ACKNOWLEDGED,
            requires_actor=True,
        ),
        # ESCALATED -> ESCALATED (next level)
        StateTransition(
            from_states=[EscalationState.ESCALATED],
            to_state=EscalationState.ESCALATED,
        ),
        # ESCALATED -> RESOLVED
        StateTransition(
            from_states=[EscalationState.ESCALATED],
            to_state=EscalationState.RESOLVED,
        ),
    ]

    def __init__(
        self,
        on_transition: Callable[[EscalationIncident, EscalationEvent], None] | None = None,
    ) -> None:
        """Initialize state machine.

        Args:
            on_transition: Optional callback for transitions.
        """
        self.on_transition = on_transition

    def can_transition(
        self,
        incident: EscalationIncident,
        to_state: EscalationState,
    ) -> bool:
        """Check if transition to state is valid.

        Args:
            incident: The incident.
            to_state: Target state.

        Returns:
            True if transition is valid.
        """
        for transition in self.VALID_TRANSITIONS:
            if incident.state in transition.from_states and transition.to_state == to_state:
                return True
        return False

    def transition(
        self,
        incident: EscalationIncident,
        to_state: EscalationState,
        actor: str | None = None,
        message: str = "",
        metadata: dict | None = None,
    ) -> EscalationIncident:
        """Execute a state transition.

        Args:
            incident: The incident to transition.
            to_state: Target state.
            actor: Who/what triggered the transition.
            message: Optional transition message.
            metadata: Optional additional data.

        Returns:
            Updated incident.

        Raises:
            ValueError: If transition is invalid.
        """
        # Find valid transition
        valid_transition = None
        for transition in self.VALID_TRANSITIONS:
            if incident.state in transition.from_states and transition.to_state == to_state:
                valid_transition = transition
                break

        if valid_transition is None:
            raise ValueError(
                f"Invalid transition from {incident.state.value} to {to_state.value}"
            )

        # Check actor requirement
        if valid_transition.requires_actor and not actor:
            raise ValueError(f"Transition to {to_state.value} requires an actor")

        # Create event
        event = EscalationEvent(
            from_state=incident.state,
            to_state=to_state,
            level=incident.current_level,
            actor=actor,
            message=message,
            metadata=metadata or {},
        )

        # Update incident
        incident.state = to_state
        incident.updated_at = datetime.utcnow()
        incident.events.append(event)

        # Call callback
        if self.on_transition:
            self.on_transition(incident, event)

        return incident

    def trigger(
        self,
        incident: EscalationIncident,
        message: str = "Escalation triggered",
    ) -> EscalationIncident:
        """Trigger an escalation.

        Transitions from PENDING to TRIGGERED.

        Args:
            incident: The incident.
            message: Optional message.

        Returns:
            Updated incident.
        """
        incident.current_level = 1
        return self.transition(
            incident,
            EscalationState.TRIGGERED,
            actor="system",
            message=message,
        )

    def acknowledge(
        self,
        incident: EscalationIncident,
        actor: str,
        message: str = "",
    ) -> EscalationIncident:
        """Acknowledge an incident.

        Transitions to ACKNOWLEDGED state.

        Args:
            incident: The incident.
            actor: Who acknowledged.
            message: Optional message.

        Returns:
            Updated incident.
        """
        incident.acknowledged_by = actor
        incident.acknowledged_at = datetime.utcnow()
        return self.transition(
            incident,
            EscalationState.ACKNOWLEDGED,
            actor=actor,
            message=message or f"Acknowledged by {actor}",
        )

    def escalate(
        self,
        incident: EscalationIncident,
        to_level: int,
        message: str = "",
    ) -> EscalationIncident:
        """Escalate to the next level.

        Transitions to ESCALATED state.

        Args:
            incident: The incident.
            to_level: Target escalation level.
            message: Optional message.

        Returns:
            Updated incident.
        """
        incident.current_level = to_level
        incident.escalation_count += 1
        return self.transition(
            incident,
            EscalationState.ESCALATED,
            actor="system",
            message=message or f"Escalated to level {to_level}",
            metadata={"level": to_level},
        )

    def resolve(
        self,
        incident: EscalationIncident,
        actor: str | None = None,
        message: str = "",
        auto: bool = False,
    ) -> EscalationIncident:
        """Resolve an incident.

        Transitions to RESOLVED state.

        Args:
            incident: The incident.
            actor: Who resolved (None for auto-resolve).
            message: Optional message.
            auto: Whether this is auto-resolution.

        Returns:
            Updated incident.
        """
        incident.resolved_by = actor or ("system" if auto else None)
        incident.resolved_at = datetime.utcnow()
        incident.next_escalation_at = None

        return self.transition(
            incident,
            EscalationState.RESOLVED,
            actor=actor or "system",
            message=message or ("Auto-resolved" if auto else f"Resolved by {actor}"),
            metadata={"auto_resolved": auto},
        )

    def get_valid_transitions(
        self,
        incident: EscalationIncident,
    ) -> list[EscalationState]:
        """Get valid target states from current state.

        Args:
            incident: The incident.

        Returns:
            List of valid target states.
        """
        valid = []
        for transition in self.VALID_TRANSITIONS:
            if incident.state in transition.from_states:
                if transition.to_state not in valid:
                    valid.append(transition.to_state)
        return valid

    def is_terminal(self, incident: EscalationIncident) -> bool:
        """Check if incident is in a terminal state.

        Args:
            incident: The incident.

        Returns:
            True if no more transitions are possible.
        """
        return incident.state == EscalationState.RESOLVED
