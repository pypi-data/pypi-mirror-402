"""Trigger system for advanced scheduling.

This module provides a flexible trigger system that supports:
- Cron-based triggers (traditional scheduling)
- Interval triggers (fixed time intervals)
- Data change triggers (profile-based change detection)
- Composite triggers (combine multiple triggers with AND/OR logic)
- Event triggers (respond to system events)
- Manual triggers (API-only execution)

Architecture follows the Strategy pattern for extensibility.
"""

from .base import (
    BaseTrigger,
    TriggerContext,
    TriggerEvaluation,
    TriggerRegistry,
)
from .factory import TriggerFactory
from .evaluators import (
    CronTrigger,
    IntervalTrigger,
    DataChangeTrigger,
    CompositeTrigger,
    EventTrigger,
    ManualTrigger,
)

__all__ = [
    # Base classes
    "BaseTrigger",
    "TriggerContext",
    "TriggerEvaluation",
    "TriggerRegistry",
    # Factory
    "TriggerFactory",
    # Trigger implementations
    "CronTrigger",
    "IntervalTrigger",
    "DataChangeTrigger",
    "CompositeTrigger",
    "EventTrigger",
    "ManualTrigger",
]
