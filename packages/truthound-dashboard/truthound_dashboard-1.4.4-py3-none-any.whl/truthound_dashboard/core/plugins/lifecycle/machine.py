"""Plugin State Machine.

This module provides the state machine implementation
for plugin lifecycle management.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Awaitable

from .states import (
    PluginState,
    StateTransition,
    StateTransitionError,
    is_valid_transition,
    get_valid_transitions,
)

logger = logging.getLogger(__name__)


# Callback types
SyncCallback = Callable[["PluginStateMachine", StateTransition], None]
AsyncCallback = Callable[["PluginStateMachine", StateTransition], Awaitable[None]]
TransitionCallback = SyncCallback | AsyncCallback


@dataclass
class PluginContext:
    """Context for plugin state machine.

    Attributes:
        plugin_id: Plugin identifier.
        version: Plugin version.
        path: Plugin installation path.
        config: Plugin configuration.
        state_data: State-specific data.
        error: Last error message.
        last_error_at: When last error occurred.
        retry_count: Number of retry attempts.
    """

    plugin_id: str
    version: str = ""
    path: str = ""
    config: dict[str, Any] = field(default_factory=dict)
    state_data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    last_error_at: datetime | None = None
    retry_count: int = 0


class PluginStateMachine:
    """State machine for managing plugin lifecycle.

    This class provides:
    - State transition management
    - Transition callbacks (before/after)
    - State history tracking
    - Error recovery and rollback
    """

    def __init__(
        self,
        plugin_id: str,
        initial_state: PluginState = PluginState.DISCOVERED,
        context: PluginContext | None = None,
    ) -> None:
        """Initialize the state machine.

        Args:
            plugin_id: Plugin identifier.
            initial_state: Initial state.
            context: Optional plugin context.
        """
        self.plugin_id = plugin_id
        self._state = initial_state
        self._previous_state: PluginState | None = None
        self._state_entered_at = datetime.utcnow()
        self._history: list[StateTransition] = []
        self._context = context or PluginContext(plugin_id=plugin_id)

        # Callbacks
        self._before_callbacks: dict[PluginState, list[TransitionCallback]] = {}
        self._after_callbacks: dict[PluginState, list[TransitionCallback]] = {}
        self._on_any_transition: list[TransitionCallback] = []

        # Locking
        self._lock = asyncio.Lock()

    @property
    def state(self) -> PluginState:
        """Get current state."""
        return self._state

    @property
    def previous_state(self) -> PluginState | None:
        """Get previous state."""
        return self._previous_state

    @property
    def context(self) -> PluginContext:
        """Get plugin context."""
        return self._context

    @property
    def history(self) -> list[StateTransition]:
        """Get state transition history."""
        return self._history.copy()

    def can_transition_to(self, target_state: PluginState) -> bool:
        """Check if transition to target state is possible.

        Args:
            target_state: Target state.

        Returns:
            True if transition is valid.
        """
        return is_valid_transition(self._state, target_state)

    def get_available_transitions(self) -> list[PluginState]:
        """Get states that can be transitioned to from current state.

        Returns:
            List of valid target states.
        """
        return get_valid_transitions(self._state)

    def transition(
        self,
        target_state: PluginState,
        trigger: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> StateTransition:
        """Transition to a new state synchronously.

        Args:
            target_state: Target state.
            trigger: What triggered the transition.
            metadata: Additional metadata.

        Returns:
            StateTransition record.

        Raises:
            StateTransitionError: If transition is invalid.
        """
        if not is_valid_transition(self._state, target_state):
            raise StateTransitionError(self._state, target_state)

        # Calculate time in previous state
        now = datetime.utcnow()
        duration_ms = (now - self._state_entered_at).total_seconds() * 1000

        # Create transition record
        transition = StateTransition(
            from_state=self._state,
            to_state=target_state,
            timestamp=now,
            trigger=trigger,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )

        # Execute before callbacks
        self._execute_before_callbacks(transition)

        # Perform transition
        self._previous_state = self._state
        self._state = target_state
        self._state_entered_at = now
        self._history.append(transition)

        # Execute after callbacks
        self._execute_after_callbacks(transition)

        logger.info(
            f"Plugin {self.plugin_id}: {transition.from_state.value} -> "
            f"{transition.to_state.value} (trigger: {trigger})"
        )

        return transition

    async def transition_async(
        self,
        target_state: PluginState,
        trigger: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> StateTransition:
        """Transition to a new state asynchronously.

        Args:
            target_state: Target state.
            trigger: What triggered the transition.
            metadata: Additional metadata.

        Returns:
            StateTransition record.

        Raises:
            StateTransitionError: If transition is invalid.
        """
        async with self._lock:
            if not is_valid_transition(self._state, target_state):
                raise StateTransitionError(self._state, target_state)

            # Calculate time in previous state
            now = datetime.utcnow()
            duration_ms = (now - self._state_entered_at).total_seconds() * 1000

            # Create transition record
            transition = StateTransition(
                from_state=self._state,
                to_state=target_state,
                timestamp=now,
                trigger=trigger,
                duration_ms=duration_ms,
                metadata=metadata or {},
            )

            # Execute before callbacks
            await self._execute_before_callbacks_async(transition)

            # Perform transition
            self._previous_state = self._state
            self._state = target_state
            self._state_entered_at = now
            self._history.append(transition)

            # Execute after callbacks
            await self._execute_after_callbacks_async(transition)

            logger.info(
                f"Plugin {self.plugin_id}: {transition.from_state.value} -> "
                f"{transition.to_state.value} (trigger: {trigger})"
            )

            return transition

    def fail(self, error: str, trigger: str = "error") -> StateTransition:
        """Transition to FAILED state.

        Args:
            error: Error message.
            trigger: What triggered the failure.

        Returns:
            StateTransition record.
        """
        self._context.error = error
        self._context.last_error_at = datetime.utcnow()

        return self.transition(
            PluginState.FAILED,
            trigger=trigger,
            metadata={"error": error},
        )

    def rollback(self, trigger: str = "rollback") -> StateTransition | None:
        """Rollback to previous state if possible.

        Args:
            trigger: What triggered the rollback.

        Returns:
            StateTransition record, or None if rollback not possible.
        """
        if self._previous_state is None:
            return None

        if not is_valid_transition(self._state, self._previous_state):
            return None

        return self.transition(
            self._previous_state,
            trigger=trigger,
            metadata={"rollback": True},
        )

    def on_before(
        self,
        state: PluginState,
        callback: TransitionCallback,
    ) -> None:
        """Register a callback to run before entering a state.

        Args:
            state: Target state.
            callback: Callback function.
        """
        if state not in self._before_callbacks:
            self._before_callbacks[state] = []
        self._before_callbacks[state].append(callback)

    def on_after(
        self,
        state: PluginState,
        callback: TransitionCallback,
    ) -> None:
        """Register a callback to run after entering a state.

        Args:
            state: Target state.
            callback: Callback function.
        """
        if state not in self._after_callbacks:
            self._after_callbacks[state] = []
        self._after_callbacks[state].append(callback)

    def on_transition(self, callback: TransitionCallback) -> None:
        """Register a callback for any transition.

        Args:
            callback: Callback function.
        """
        self._on_any_transition.append(callback)

    def _execute_before_callbacks(self, transition: StateTransition) -> None:
        """Execute before callbacks synchronously."""
        callbacks = self._before_callbacks.get(transition.to_state, [])
        for callback in callbacks:
            try:
                result = callback(self, transition)
                if asyncio.iscoroutine(result):
                    # Run async callback synchronously
                    asyncio.get_event_loop().run_until_complete(result)
            except Exception as e:
                logger.error(f"Before callback error: {e}")

    def _execute_after_callbacks(self, transition: StateTransition) -> None:
        """Execute after callbacks synchronously."""
        callbacks = self._after_callbacks.get(transition.to_state, [])
        callbacks.extend(self._on_any_transition)
        for callback in callbacks:
            try:
                result = callback(self, transition)
                if asyncio.iscoroutine(result):
                    asyncio.get_event_loop().run_until_complete(result)
            except Exception as e:
                logger.error(f"After callback error: {e}")

    async def _execute_before_callbacks_async(
        self, transition: StateTransition
    ) -> None:
        """Execute before callbacks asynchronously."""
        callbacks = self._before_callbacks.get(transition.to_state, [])
        for callback in callbacks:
            try:
                result = callback(self, transition)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Before callback error: {e}")

    async def _execute_after_callbacks_async(
        self, transition: StateTransition
    ) -> None:
        """Execute after callbacks asynchronously."""
        callbacks = self._after_callbacks.get(transition.to_state, [])
        callbacks.extend(self._on_any_transition)
        for callback in callbacks:
            try:
                result = callback(self, transition)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"After callback error: {e}")

    def get_state_info(self) -> dict[str, Any]:
        """Get information about current state.

        Returns:
            State information dictionary.
        """
        return {
            "plugin_id": self.plugin_id,
            "state": self._state.value,
            "previous_state": self._previous_state.value if self._previous_state else None,
            "state_entered_at": self._state_entered_at.isoformat(),
            "available_transitions": [s.value for s in self.get_available_transitions()],
            "history_length": len(self._history),
            "context": {
                "version": self._context.version,
                "error": self._context.error,
                "retry_count": self._context.retry_count,
            },
        }


def create_state_machine(
    plugin_id: str,
    version: str = "",
    initial_state: PluginState = PluginState.DISCOVERED,
) -> PluginStateMachine:
    """Create a new plugin state machine.

    Args:
        plugin_id: Plugin identifier.
        version: Plugin version.
        initial_state: Initial state.

    Returns:
        Configured PluginStateMachine.
    """
    context = PluginContext(
        plugin_id=plugin_id,
        version=version,
    )
    return PluginStateMachine(
        plugin_id=plugin_id,
        initial_state=initial_state,
        context=context,
    )
