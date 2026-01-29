"""Escalation engine for managing alert escalations.

This module provides the main EscalationEngine that orchestrates
the escalation lifecycle including triggering, escalating,
acknowledging, and resolving incidents.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable

from .models import (
    EscalationIncident,
    EscalationLevel,
    EscalationPolicy,
    EscalationState,
    EscalationTarget,
)
from .state_machine import EscalationStateMachine
from .stores import BaseEscalationStore, InMemoryEscalationStore

logger = logging.getLogger(__name__)


@dataclass
class EscalationEngineConfig:
    """Configuration for the escalation engine.

    Attributes:
        check_interval_seconds: How often to check for pending escalations.
        max_retries: Maximum notification retries per level.
        default_delay_minutes: Default delay between levels if not specified.
    """

    check_interval_seconds: int = 60
    max_retries: int = 3
    default_delay_minutes: int = 15


class EscalationEngine:
    """Main escalation engine.

    Orchestrates the complete escalation lifecycle:
    1. Triggering new incidents
    2. Escalating to next levels based on time
    3. Acknowledging incidents
    4. Resolving incidents
    5. Auto-resolving on success

    The engine can be used standalone or integrated with
    APScheduler for periodic escalation checks.

    Example:
        engine = EscalationEngine(
            store=SQLiteEscalationStore("escalation.db"),
            on_notify=send_notification,
        )

        # Trigger escalation
        await engine.trigger(
            policy_id="critical-policy",
            incident_ref="validation-123",
            context={"severity": "critical"},
        )

        # Acknowledge
        await engine.acknowledge("incident-id", actor="user@example.com")

        # Resolve
        await engine.resolve("incident-id", actor="user@example.com")
    """

    def __init__(
        self,
        store: BaseEscalationStore | None = None,
        config: EscalationEngineConfig | None = None,
        on_notify: Callable[[EscalationIncident, EscalationLevel, EscalationTarget], Any] | None = None,
    ) -> None:
        """Initialize escalation engine.

        Args:
            store: Storage backend.
            config: Engine configuration.
            on_notify: Callback for sending notifications.
        """
        self.store = store or InMemoryEscalationStore()
        self.config = config or EscalationEngineConfig()
        self.on_notify = on_notify
        self.state_machine = EscalationStateMachine()

    async def trigger(
        self,
        policy_id: str,
        incident_ref: str,
        context: dict[str, Any] | None = None,
    ) -> EscalationIncident:
        """Trigger a new escalation incident.

        Creates a new incident and starts the escalation process.
        If an incident with the same ref already exists and is not
        resolved, returns the existing incident.

        Args:
            policy_id: ID of the escalation policy.
            incident_ref: External reference (e.g., validation ID).
            context: Context data for the incident.

        Returns:
            The created or existing incident.

        Raises:
            ValueError: If policy not found.
        """
        # Check for existing unresolved incident
        existing = self.store.get_incident_by_ref(incident_ref)
        if existing and existing.state != EscalationState.RESOLVED:
            logger.debug(f"Incident {incident_ref} already exists in state {existing.state}")
            return existing

        # Get policy
        policy = self.store.get_policy(policy_id)
        if not policy:
            raise ValueError(f"Escalation policy not found: {policy_id}")

        if not policy.is_active:
            raise ValueError(f"Escalation policy is not active: {policy_id}")

        # Create incident
        incident = EscalationIncident(
            policy_id=policy_id,
            incident_ref=incident_ref,
            context=context or {},
        )

        # Trigger state transition
        incident = self.state_machine.trigger(incident)

        # Set next escalation time
        first_level = policy.get_level(1)
        if first_level:
            delay = first_level.delay_minutes
            if delay > 0:
                incident.next_escalation_at = datetime.utcnow() + timedelta(minutes=delay)
            else:
                incident.next_escalation_at = datetime.utcnow()

        # Save incident
        self.store.save_incident(incident)

        # Notify first level
        await self._notify_level(incident, policy, first_level)

        logger.info(f"Triggered escalation for {incident_ref}")
        return incident

    async def escalate(self, incident_id: str) -> EscalationIncident:
        """Escalate incident to the next level.

        Args:
            incident_id: ID of the incident.

        Returns:
            Updated incident.

        Raises:
            ValueError: If incident not found or can't escalate.
        """
        incident = self.store.get_incident(incident_id)
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")

        if incident.state == EscalationState.RESOLVED:
            raise ValueError("Cannot escalate resolved incident")

        policy = self.store.get_policy(incident.policy_id)
        if not policy:
            raise ValueError(f"Policy not found: {incident.policy_id}")

        # Check max escalations
        if incident.escalation_count >= policy.max_escalations:
            logger.warning(f"Incident {incident_id} reached max escalations")
            return incident

        # Get next level
        next_level = policy.get_next_level(incident.current_level)
        if not next_level:
            logger.info(f"Incident {incident_id} at max level {incident.current_level}")
            return incident

        # Escalate
        incident = self.state_machine.escalate(
            incident,
            to_level=next_level.level,
            message=f"Escalating to level {next_level.level}",
        )

        # Set next escalation time
        further_level = policy.get_next_level(next_level.level)
        if further_level:
            delay = further_level.delay_minutes
            incident.next_escalation_at = datetime.utcnow() + timedelta(minutes=delay)
        else:
            incident.next_escalation_at = None

        # Save
        self.store.save_incident(incident)

        # Notify
        await self._notify_level(incident, policy, next_level)

        logger.info(f"Escalated {incident_id} to level {next_level.level}")
        return incident

    async def acknowledge(
        self,
        incident_id: str,
        actor: str,
        message: str = "",
    ) -> EscalationIncident:
        """Acknowledge an incident.

        Pauses further escalation until either resolved or
        escalation time is reached.

        Args:
            incident_id: ID of the incident.
            actor: Who is acknowledging.
            message: Optional acknowledgement message.

        Returns:
            Updated incident.

        Raises:
            ValueError: If incident not found or can't acknowledge.
        """
        incident = self.store.get_incident(incident_id)
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")

        # Check if can acknowledge
        if not self.state_machine.can_transition(incident, EscalationState.ACKNOWLEDGED):
            raise ValueError(f"Cannot acknowledge incident in state {incident.state}")

        # Acknowledge
        incident = self.state_machine.acknowledge(
            incident,
            actor=actor,
            message=message or f"Acknowledged by {actor}",
        )

        # Save
        self.store.save_incident(incident)

        logger.info(f"Incident {incident_id} acknowledged by {actor}")
        return incident

    async def resolve(
        self,
        incident_id: str,
        actor: str | None = None,
        message: str = "",
        auto: bool = False,
    ) -> EscalationIncident:
        """Resolve an incident.

        Args:
            incident_id: ID of the incident.
            actor: Who is resolving (None for auto-resolve).
            message: Optional resolution message.
            auto: Whether this is auto-resolution.

        Returns:
            Updated incident.

        Raises:
            ValueError: If incident not found or can't resolve.
        """
        incident = self.store.get_incident(incident_id)
        if not incident:
            raise ValueError(f"Incident not found: {incident_id}")

        # Check if can resolve
        if not self.state_machine.can_transition(incident, EscalationState.RESOLVED):
            raise ValueError(f"Cannot resolve incident in state {incident.state}")

        # Resolve
        incident = self.state_machine.resolve(
            incident,
            actor=actor,
            message=message,
            auto=auto,
        )

        # Save
        self.store.save_incident(incident)

        log_msg = f"Incident {incident_id} resolved"
        if auto:
            log_msg += " (auto)"
        elif actor:
            log_msg += f" by {actor}"
        logger.info(log_msg)

        return incident

    async def auto_resolve_by_ref(
        self,
        incident_ref: str,
        message: str = "Auto-resolved - validation passed",
    ) -> EscalationIncident | None:
        """Auto-resolve an incident by reference.

        Called when validation passes to auto-resolve associated
        incidents (if policy allows).

        Args:
            incident_ref: External reference.
            message: Resolution message.

        Returns:
            Resolved incident or None if not found/not eligible.
        """
        incident = self.store.get_incident_by_ref(incident_ref)
        if not incident:
            return None

        if incident.state == EscalationState.RESOLVED:
            return incident

        # Check policy allows auto-resolve
        policy = self.store.get_policy(incident.policy_id)
        if not policy or not policy.auto_resolve_on_success:
            return None

        return await self.resolve(
            incident.id,
            message=message,
            auto=True,
        )

    async def check_and_escalate(self) -> int:
        """Check for and process pending escalations.

        This method should be called periodically (e.g., by APScheduler)
        to process escalations that are due.

        Returns:
            Number of incidents escalated.
        """
        pending = self.store.get_pending_escalations()
        escalated = 0

        for incident in pending:
            try:
                await self.escalate(incident.id)
                escalated += 1
            except Exception as e:
                logger.error(f"Failed to escalate {incident.id}: {e}")

        return escalated

    async def _notify_level(
        self,
        incident: EscalationIncident,
        policy: EscalationPolicy,
        level: EscalationLevel | None,
    ) -> None:
        """Send notifications for an escalation level.

        Args:
            incident: The incident.
            policy: The policy.
            level: The level to notify.
        """
        if not level or not self.on_notify:
            return

        for target in level.targets:
            try:
                await self.on_notify(incident, level, target)
            except Exception as e:
                logger.error(
                    f"Failed to notify {target.identifier} for incident {incident.id}: {e}"
                )

    def get_incident(self, incident_id: str) -> EscalationIncident | None:
        """Get incident by ID."""
        return self.store.get_incident(incident_id)

    def get_incident_by_ref(self, incident_ref: str) -> EscalationIncident | None:
        """Get incident by reference."""
        return self.store.get_incident_by_ref(incident_ref)

    def list_active_incidents(self) -> list[EscalationIncident]:
        """List all active (non-resolved) incidents."""
        return self.store.list_incidents(
            states=[
                EscalationState.PENDING,
                EscalationState.TRIGGERED,
                EscalationState.ACKNOWLEDGED,
                EscalationState.ESCALATED,
            ]
        )

    def get_stats(self) -> dict[str, Any]:
        """Get escalation statistics.

        Returns:
            Dictionary with stats.
        """
        all_incidents = self.store.list_incidents()

        by_state: dict[str, int] = {}
        for incident in all_incidents:
            state = incident.state.value
            by_state[state] = by_state.get(state, 0) + 1

        return {
            "total_incidents": len(all_incidents),
            "by_state": by_state,
            "active_count": sum(
                1 for i in all_incidents
                if i.state != EscalationState.RESOLVED
            ),
            "total_policies": len(self.store.list_policies(active_only=False)),
        }
