"""Plugin Lifecycle Management.

This module provides:
- State machine for plugin lifecycle
- Hot reload capability
- File watching for auto-reload
- Graceful shutdown and rollback
"""

from __future__ import annotations

from .states import (
    PluginState,
    StateTransition,
    StateTransitionError,
)
from .machine import (
    PluginStateMachine,
    create_state_machine,
)
from .hot_reload import (
    HotReloadManager,
    FileWatcher,
    ReloadResult,
    ReloadStrategy,
)

__all__ = [
    # States
    "PluginState",
    "StateTransition",
    "StateTransitionError",
    # Machine
    "PluginStateMachine",
    "create_state_machine",
    # Hot Reload
    "HotReloadManager",
    "FileWatcher",
    "ReloadResult",
    "ReloadStrategy",
]
