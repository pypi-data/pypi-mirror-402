"""Plugin Lifecycle States.

This module defines the state machine states and transitions
for plugin lifecycle management.

State Diagram:
    DISCOVERED --> LOADING --> LOADED --> ACTIVATING --> ACTIVE
         |           |           |            |            |
         v           v           v            v            v
       FAILED     FAILED     FAILED       FAILED    DEACTIVATING
                                                         |
                                                         v
                                                    UNLOADING --> UNLOADED
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class PluginState(str, Enum):
    """Plugin lifecycle states."""

    # Initial state when plugin is found
    DISCOVERED = "discovered"

    # Plugin is being loaded (reading files, parsing)
    LOADING = "loading"

    # Plugin code is loaded but not active
    LOADED = "loaded"

    # Plugin is being activated (initializing)
    ACTIVATING = "activating"

    # Plugin is active and running
    ACTIVE = "active"

    # Plugin is being deactivated
    DEACTIVATING = "deactivating"

    # Plugin is being unloaded
    UNLOADING = "unloading"

    # Plugin has been unloaded
    UNLOADED = "unloaded"

    # Plugin failed to load or activate
    FAILED = "failed"

    # Plugin is being reloaded (hot reload)
    RELOADING = "reloading"

    # Plugin is being upgraded to new version
    UPGRADING = "upgrading"


class StateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""

    def __init__(
        self,
        current_state: PluginState,
        target_state: PluginState,
        message: str | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            current_state: Current plugin state.
            target_state: Attempted target state.
            message: Optional error message.
        """
        self.current_state = current_state
        self.target_state = target_state
        msg = message or f"Cannot transition from {current_state.value} to {target_state.value}"
        super().__init__(msg)


@dataclass
class StateTransition:
    """Represents a state transition event.

    Attributes:
        from_state: Previous state.
        to_state: New state.
        timestamp: When the transition occurred.
        trigger: What triggered the transition.
        duration_ms: Time spent in previous state.
        metadata: Additional transition metadata.
        error: Error message if transition failed.
    """

    from_state: PluginState
    to_state: PluginState
    timestamp: datetime = field(default_factory=datetime.utcnow)
    trigger: str = ""
    duration_ms: float = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "from_state": self.from_state.value,
            "to_state": self.to_state.value,
            "timestamp": self.timestamp.isoformat(),
            "trigger": self.trigger,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
            "error": self.error,
        }


# Valid state transitions
VALID_TRANSITIONS: dict[PluginState, set[PluginState]] = {
    PluginState.DISCOVERED: {
        PluginState.LOADING,
        PluginState.FAILED,
        PluginState.UNLOADED,
    },
    PluginState.LOADING: {
        PluginState.LOADED,
        PluginState.FAILED,
    },
    PluginState.LOADED: {
        PluginState.ACTIVATING,
        PluginState.UNLOADING,
        PluginState.FAILED,
    },
    PluginState.ACTIVATING: {
        PluginState.ACTIVE,
        PluginState.FAILED,
        PluginState.LOADED,  # Rollback on failure
    },
    PluginState.ACTIVE: {
        PluginState.DEACTIVATING,
        PluginState.RELOADING,
        PluginState.UPGRADING,
        PluginState.FAILED,
    },
    PluginState.DEACTIVATING: {
        PluginState.LOADED,
        PluginState.UNLOADING,
        PluginState.FAILED,
    },
    PluginState.UNLOADING: {
        PluginState.UNLOADED,
        PluginState.FAILED,
    },
    PluginState.UNLOADED: {
        PluginState.DISCOVERED,  # Re-install
        PluginState.LOADING,     # Re-load
    },
    PluginState.FAILED: {
        PluginState.DISCOVERED,  # Retry discovery
        PluginState.LOADING,     # Retry load
        PluginState.UNLOADING,   # Unload failed plugin
    },
    PluginState.RELOADING: {
        PluginState.ACTIVE,
        PluginState.FAILED,
        PluginState.LOADED,  # Rollback
    },
    PluginState.UPGRADING: {
        PluginState.ACTIVE,
        PluginState.FAILED,
        PluginState.LOADED,  # Rollback
    },
}


def is_valid_transition(from_state: PluginState, to_state: PluginState) -> bool:
    """Check if a state transition is valid.

    Args:
        from_state: Current state.
        to_state: Target state.

    Returns:
        True if transition is valid.
    """
    valid_targets = VALID_TRANSITIONS.get(from_state, set())
    return to_state in valid_targets


def get_valid_transitions(state: PluginState) -> list[PluginState]:
    """Get valid target states from a given state.

    Args:
        state: Current state.

    Returns:
        List of valid target states.
    """
    return list(VALID_TRANSITIONS.get(state, []))


def can_activate(state: PluginState) -> bool:
    """Check if plugin can be activated from current state.

    Args:
        state: Current state.

    Returns:
        True if activation is possible.
    """
    return state in {PluginState.LOADED, PluginState.FAILED}


def can_deactivate(state: PluginState) -> bool:
    """Check if plugin can be deactivated from current state.

    Args:
        state: Current state.

    Returns:
        True if deactivation is possible.
    """
    return state == PluginState.ACTIVE


def is_running(state: PluginState) -> bool:
    """Check if plugin is in a running state.

    Args:
        state: Current state.

    Returns:
        True if plugin is running.
    """
    return state == PluginState.ACTIVE


def is_transitioning(state: PluginState) -> bool:
    """Check if plugin is in a transitional state.

    Args:
        state: Current state.

    Returns:
        True if plugin is transitioning.
    """
    return state in {
        PluginState.LOADING,
        PluginState.ACTIVATING,
        PluginState.DEACTIVATING,
        PluginState.UNLOADING,
        PluginState.RELOADING,
        PluginState.UPGRADING,
    }


def is_terminal(state: PluginState) -> bool:
    """Check if plugin is in a terminal state.

    Args:
        state: Current state.

    Returns:
        True if plugin is in terminal state.
    """
    return state in {PluginState.UNLOADED, PluginState.FAILED}
