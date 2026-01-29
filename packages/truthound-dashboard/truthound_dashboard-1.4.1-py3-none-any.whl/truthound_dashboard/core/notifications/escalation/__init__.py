"""Escalation engine for notification management.

This module provides a multi-level escalation system for managing
alerts that require attention at different organizational levels.

Features:
    - Multi-level escalation policies
    - State machine for incident tracking
    - Configurable delay between escalation levels
    - Support for user, group, and on-call targets
    - Auto-resolution on success

State Machine:
    PENDING -> TRIGGERED -> ESCALATED -> RESOLVED
                  |             ^
                  v             |
             ACKNOWLEDGED ------+

Example:
    from truthound_dashboard.core.notifications.escalation import (
        EscalationEngine,
        EscalationPolicy,
        EscalationLevel,
        EscalationTarget,
        TargetType,
    )

    policy = EscalationPolicy(
        name="critical_alerts",
        levels=[
            EscalationLevel(
                level=1,
                delay_minutes=0,
                targets=[
                    EscalationTarget(type=TargetType.USER, identifier="team-lead", channel="slack")
                ],
            ),
            EscalationLevel(
                level=2,
                delay_minutes=15,
                targets=[
                    EscalationTarget(type=TargetType.GROUP, identifier="managers", channel="pagerduty")
                ],
            ),
        ],
    )

    engine = EscalationEngine(policy=policy)
    await engine.trigger("incident-123", context={"severity": "critical"})
"""

from .engine import EscalationEngine, EscalationEngineConfig
from .models import (
    EscalationEvent,
    EscalationIncident,
    EscalationLevel,
    EscalationPolicy,
    EscalationState,
    EscalationTarget,
    StateTransition,
    TargetType,
)
from .backends import (
    BackendType,
    InMemorySchedulerBackend,
    JobData,
    JobExecutionResult,
    JobState,
    MisfirePolicy,
    SchedulerBackend,
    SchedulerBackendConfig,
    SQLAlchemySchedulerBackend,
    create_scheduler_backend,
)
from .scheduler import (
    DefaultEscalationHandler,
    EscalationHandler,
    EscalationResult,
    EscalationSchedulerConfig,
    EscalationSchedulerService,
    EscalationStrategy,
    ImmediateEscalationStrategy,
    LoggingEscalationHandler,
    TimeBasedEscalationStrategy,
    get_escalation_scheduler,
    reset_escalation_scheduler,
    start_escalation_scheduler,
    stop_escalation_scheduler,
)
from .state_machine import EscalationStateMachine
from .stores import (
    BaseEscalationStore,
    EscalationMetrics,
    EscalationStoreType,
    InMemoryEscalationStore,
    RedisEscalationStore,
    SQLiteEscalationStore,
    create_escalation_store,
)

__all__ = [
    # Models
    "EscalationState",
    "TargetType",
    "EscalationTarget",
    "EscalationLevel",
    "EscalationPolicy",
    "EscalationIncident",
    "EscalationEvent",
    "StateTransition",
    # State Machine
    "EscalationStateMachine",
    # Stores
    "BaseEscalationStore",
    "EscalationMetrics",
    "EscalationStoreType",
    "InMemoryEscalationStore",
    "RedisEscalationStore",
    "SQLiteEscalationStore",
    "create_escalation_store",
    # Engine
    "EscalationEngine",
    "EscalationEngineConfig",
    # Scheduler Backends
    "BackendType",
    "JobState",
    "MisfirePolicy",
    "SchedulerBackendConfig",
    "JobData",
    "JobExecutionResult",
    "SchedulerBackend",
    "InMemorySchedulerBackend",
    "SQLAlchemySchedulerBackend",
    "create_scheduler_backend",
    # Scheduler
    "EscalationSchedulerService",
    "EscalationSchedulerConfig",
    "EscalationHandler",
    "EscalationResult",
    "EscalationStrategy",
    "DefaultEscalationHandler",
    "LoggingEscalationHandler",
    "TimeBasedEscalationStrategy",
    "ImmediateEscalationStrategy",
    "get_escalation_scheduler",
    "reset_escalation_scheduler",
    "start_escalation_scheduler",
    "stop_escalation_scheduler",
]
