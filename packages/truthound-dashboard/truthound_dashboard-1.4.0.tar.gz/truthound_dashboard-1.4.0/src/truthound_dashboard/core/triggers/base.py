"""Base classes for the trigger system.

Provides abstract base classes and common utilities for trigger implementations.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, ClassVar

logger = logging.getLogger(__name__)


@dataclass
class TriggerContext:
    """Context information passed to trigger evaluators.

    Contains all information needed to evaluate whether a trigger should fire.

    Attributes:
        schedule_id: ID of the schedule being evaluated.
        source_id: ID of the source to validate.
        last_run_at: Timestamp of last successful run.
        trigger_count: Number of times this schedule has triggered.
        current_time: Current evaluation time.
        profile_data: Latest profile data (for data change triggers).
        baseline_profile: Baseline profile for comparison.
        event_data: Event data (for event triggers).
        custom_data: Additional context data.
    """

    schedule_id: str
    source_id: str
    last_run_at: datetime | None = None
    trigger_count: int = 0
    current_time: datetime = field(default_factory=datetime.utcnow)
    profile_data: dict[str, Any] | None = None
    baseline_profile: dict[str, Any] | None = None
    event_data: dict[str, Any] | None = None
    custom_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class TriggerEvaluation:
    """Result of evaluating a trigger condition.

    Attributes:
        should_trigger: Whether the trigger condition is met.
        reason: Human-readable explanation of the result.
        next_evaluation_at: Suggested time for next evaluation.
        details: Additional details about the evaluation.
        confidence: Confidence level (0.0-1.0) for ML-based triggers.
    """

    should_trigger: bool
    reason: str
    next_evaluation_at: datetime | None = None
    details: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "should_trigger": self.should_trigger,
            "reason": self.reason,
            "next_evaluation_at": (
                self.next_evaluation_at.isoformat()
                if self.next_evaluation_at
                else None
            ),
            "details": self.details,
            "confidence": self.confidence,
            "evaluated_at": datetime.utcnow().isoformat(),
        }


class BaseTrigger(ABC):
    """Abstract base class for all trigger types.

    Implements the Strategy pattern for trigger evaluation.
    Subclasses must implement the evaluate() method.
    """

    # Class-level trigger type identifier
    trigger_type: ClassVar[str] = "base"

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize the trigger with configuration.

        Args:
            config: Trigger-specific configuration dictionary.
        """
        self.config = config
        self._validate_config()

    @abstractmethod
    def _validate_config(self) -> None:
        """Validate the trigger configuration.

        Raises:
            ValueError: If configuration is invalid.
        """
        pass

    @abstractmethod
    async def evaluate(self, context: TriggerContext) -> TriggerEvaluation:
        """Evaluate whether the trigger should fire.

        Args:
            context: Evaluation context with all necessary data.

        Returns:
            TriggerEvaluation with the result.
        """
        pass

    def get_next_evaluation_time(
        self, context: TriggerContext
    ) -> datetime | None:
        """Calculate the next time this trigger should be evaluated.

        Args:
            context: Current context.

        Returns:
            Next evaluation datetime or None if not applicable.
        """
        return None

    def get_description(self) -> str:
        """Get a human-readable description of this trigger.

        Returns:
            Description string.
        """
        return f"{self.trigger_type} trigger"

    def to_dict(self) -> dict[str, Any]:
        """Convert trigger to dictionary representation.

        Returns:
            Dictionary with trigger type and config.
        """
        return {
            "type": self.trigger_type,
            "config": self.config,
            "description": self.get_description(),
        }


class TriggerRegistry:
    """Registry for trigger type implementations.

    Allows dynamic registration and lookup of trigger classes.
    """

    _triggers: ClassVar[dict[str, type[BaseTrigger]]] = {}

    @classmethod
    def register(cls, trigger_type: str):
        """Decorator to register a trigger implementation.

        Usage:
            @TriggerRegistry.register("my_trigger")
            class MyTrigger(BaseTrigger):
                ...
        """

        def decorator(trigger_class: type[BaseTrigger]):
            cls._triggers[trigger_type] = trigger_class
            trigger_class.trigger_type = trigger_type
            return trigger_class

        return decorator

    @classmethod
    def get(cls, trigger_type: str) -> type[BaseTrigger] | None:
        """Get a trigger class by type.

        Args:
            trigger_type: Type identifier.

        Returns:
            Trigger class or None if not found.
        """
        return cls._triggers.get(trigger_type)

    @classmethod
    def create(
        cls, trigger_type: str, config: dict[str, Any]
    ) -> BaseTrigger | None:
        """Create a trigger instance.

        Args:
            trigger_type: Type identifier.
            config: Trigger configuration.

        Returns:
            Trigger instance or None if type not found.
        """
        trigger_class = cls.get(trigger_type)
        if trigger_class is None:
            logger.warning(f"Unknown trigger type: {trigger_type}")
            return None
        return trigger_class(config)

    @classmethod
    def list_types(cls) -> list[str]:
        """List all registered trigger types.

        Returns:
            List of type identifiers.
        """
        return list(cls._triggers.keys())

    @classmethod
    def get_all(cls) -> dict[str, type[BaseTrigger]]:
        """Get all registered trigger classes.

        Returns:
            Dictionary of type -> class.
        """
        return dict(cls._triggers)
