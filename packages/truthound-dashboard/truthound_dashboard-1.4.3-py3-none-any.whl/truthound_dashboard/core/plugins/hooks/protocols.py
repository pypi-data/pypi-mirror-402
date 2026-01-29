"""Hook System Protocol Definitions.

This module defines the core protocols and data types for the
plugin hook system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Protocol


class HookType(str, Enum):
    """Types of hooks available in the system."""

    # Validation hooks
    BEFORE_VALIDATION = "before_validation"
    AFTER_VALIDATION = "after_validation"
    ON_ISSUE_FOUND = "on_issue_found"

    # Profiling hooks
    BEFORE_PROFILE = "before_profile"
    AFTER_PROFILE = "after_profile"

    # Report hooks
    ON_REPORT_GENERATE = "on_report_generate"
    BEFORE_REPORT_SEND = "before_report_send"
    AFTER_REPORT_SEND = "after_report_send"

    # Error hooks
    ON_ERROR = "on_error"
    ON_RETRY = "on_retry"

    # Plugin lifecycle hooks
    ON_PLUGIN_LOAD = "on_plugin_load"
    ON_PLUGIN_UNLOAD = "on_plugin_unload"
    ON_PLUGIN_ENABLE = "on_plugin_enable"
    ON_PLUGIN_DISABLE = "on_plugin_disable"

    # Data source hooks
    ON_SOURCE_CONNECT = "on_source_connect"
    ON_SOURCE_DISCONNECT = "on_source_disconnect"

    # Schema hooks
    ON_SCHEMA_CHANGE = "on_schema_change"
    ON_SCHEMA_DRIFT = "on_schema_drift"


class HookPriority(int, Enum):
    """Hook execution priority (lower = earlier)."""

    HIGHEST = 0
    HIGH = 25
    NORMAL = 50
    LOW = 75
    LOWEST = 100


@dataclass
class HookContext:
    """Context passed to hook handlers.

    Attributes:
        hook_type: Type of hook being executed.
        plugin_id: ID of the plugin that registered this hook.
        timestamp: When the hook was triggered.
        data: Hook-specific data.
        metadata: Additional metadata.
        results: Results from previous handlers in the chain.
        cancelled: Whether the operation should be cancelled.
        modified_data: Data modified by handlers.
    """

    hook_type: HookType
    plugin_id: str | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    results: list["HookResult"] = field(default_factory=list)
    cancelled: bool = False
    modified_data: dict[str, Any] = field(default_factory=dict)

    def cancel(self) -> None:
        """Cancel the current operation."""
        self.cancelled = True

    def modify(self, key: str, value: Any) -> None:
        """Modify data that will be passed to the next handler.

        Args:
            key: Data key to modify.
            value: New value.
        """
        self.modified_data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get data from context, preferring modified data.

        Args:
            key: Data key.
            default: Default value if not found.

        Returns:
            Value from modified_data or data.
        """
        if key in self.modified_data:
            return self.modified_data[key]
        return self.data.get(key, default)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "hook_type": self.hook_type.value,
            "plugin_id": self.plugin_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "metadata": self.metadata,
            "cancelled": self.cancelled,
        }


@dataclass
class HookResult:
    """Result from a hook handler.

    Attributes:
        success: Whether the handler executed successfully.
        plugin_id: ID of the plugin that handled this hook.
        handler_name: Name of the handler function.
        execution_time_ms: Execution time in milliseconds.
        data: Data returned by the handler.
        error: Error message if failed.
        skipped: Whether the handler was skipped.
        modified_keys: Keys that were modified by this handler.
    """

    success: bool
    plugin_id: str | None = None
    handler_name: str = ""
    execution_time_ms: float = 0
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    skipped: bool = False
    modified_keys: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "plugin_id": self.plugin_id,
            "handler_name": self.handler_name,
            "execution_time_ms": self.execution_time_ms,
            "data": self.data,
            "error": self.error,
            "skipped": self.skipped,
            "modified_keys": self.modified_keys,
        }


# Type alias for hook handlers
HookHandler = Callable[[HookContext], HookResult | None]


@dataclass
class HookRegistration:
    """Registration information for a hook handler.

    Attributes:
        hook_type: Type of hook.
        handler: Handler function.
        plugin_id: ID of the registering plugin.
        handler_name: Name of the handler.
        priority: Execution priority.
        enabled: Whether the handler is enabled.
        conditions: Conditions for executing the handler.
        metadata: Additional metadata.
    """

    hook_type: HookType
    handler: HookHandler
    plugin_id: str | None = None
    handler_name: str = ""
    priority: HookPriority = HookPriority.NORMAL
    enabled: bool = True
    conditions: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Extract handler name if not provided."""
        if not self.handler_name and hasattr(self.handler, "__name__"):
            self.handler_name = self.handler.__name__

    def matches_conditions(self, context: HookContext) -> bool:
        """Check if conditions match the context.

        Args:
            context: Hook context to check against.

        Returns:
            True if all conditions are satisfied.
        """
        if not self.conditions:
            return True

        for key, expected in self.conditions.items():
            actual = context.data.get(key) or context.metadata.get(key)
            if actual != expected:
                return False

        return True


class HookRegistry(Protocol):
    """Protocol for hook registries."""

    def register(
        self,
        hook_type: HookType,
        handler: HookHandler,
        plugin_id: str | None = None,
        priority: HookPriority = HookPriority.NORMAL,
        conditions: dict[str, Any] | None = None,
    ) -> str:
        """Register a hook handler.

        Args:
            hook_type: Type of hook.
            handler: Handler function.
            plugin_id: ID of the registering plugin.
            priority: Execution priority.
            conditions: Conditions for executing.

        Returns:
            Registration ID.
        """
        ...

    def unregister(self, registration_id: str) -> bool:
        """Unregister a hook handler.

        Args:
            registration_id: Registration ID.

        Returns:
            True if successfully unregistered.
        """
        ...

    def execute(
        self,
        hook_type: HookType,
        context: HookContext,
    ) -> list[HookResult]:
        """Execute all handlers for a hook type.

        Args:
            hook_type: Type of hook.
            context: Hook context.

        Returns:
            List of results from handlers.
        """
        ...
