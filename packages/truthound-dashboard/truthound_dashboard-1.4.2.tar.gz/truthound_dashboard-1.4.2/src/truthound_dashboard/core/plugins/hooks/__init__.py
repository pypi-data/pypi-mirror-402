"""Plugin Hook System.

This module provides a hook system for plugins to integrate
with the validation pipeline and other system events.

Hook Types:
- before_validation: Called before validation starts
- after_validation: Called after validation completes
- on_issue_found: Called when a validation issue is found
- before_profile: Called before profiling starts
- after_profile: Called after profiling completes
- on_report_generate: Called when a report is generated
- on_error: Called when an error occurs
- on_plugin_load: Called when a plugin is loaded
- on_plugin_unload: Called when a plugin is unloaded
"""

from __future__ import annotations

from .protocols import (
    HookType,
    HookPriority,
    HookContext,
    HookResult,
    HookHandler,
    HookRegistry,
)
from .manager import (
    HookManager,
    hook_manager,
)
from .decorators import (
    hook,
    before_validation,
    after_validation,
    on_issue_found,
    before_profile,
    after_profile,
    on_report_generate,
    on_error,
)

__all__ = [
    # Protocols
    "HookType",
    "HookPriority",
    "HookContext",
    "HookResult",
    "HookHandler",
    "HookRegistry",
    # Manager
    "HookManager",
    "hook_manager",
    # Decorators
    "hook",
    "before_validation",
    "after_validation",
    "on_issue_found",
    "before_profile",
    "after_profile",
    "on_report_generate",
    "on_error",
]
