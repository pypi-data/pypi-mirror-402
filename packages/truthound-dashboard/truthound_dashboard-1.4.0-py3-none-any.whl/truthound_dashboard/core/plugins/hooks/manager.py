"""Hook Manager Implementation.

This module provides the main hook manager that coordinates
hook registration and execution.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections import defaultdict
from typing import Any

from .protocols import (
    HookContext,
    HookHandler,
    HookPriority,
    HookRegistration,
    HookResult,
    HookType,
)

logger = logging.getLogger(__name__)


class HookManager:
    """Manages hook registration and execution.

    This class provides:
    - Hook registration with priority ordering
    - Synchronous and asynchronous execution
    - Conditional execution based on context
    - Result aggregation
    - Error handling and recovery
    """

    def __init__(self) -> None:
        """Initialize the hook manager."""
        self._registrations: dict[str, HookRegistration] = {}
        self._hooks: dict[HookType, list[str]] = defaultdict(list)
        self._lock = asyncio.Lock()

    def register(
        self,
        hook_type: HookType | str,
        handler: HookHandler,
        plugin_id: str | None = None,
        priority: HookPriority | int = HookPriority.NORMAL,
        conditions: dict[str, Any] | None = None,
        handler_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Register a hook handler.

        Args:
            hook_type: Type of hook to register for.
            handler: Handler function.
            plugin_id: ID of the registering plugin.
            priority: Execution priority (lower = earlier).
            conditions: Conditions for executing the handler.
            handler_name: Optional handler name.
            metadata: Additional metadata.

        Returns:
            Registration ID for later unregistration.
        """
        if isinstance(hook_type, str):
            hook_type = HookType(hook_type)

        if isinstance(priority, int) and not isinstance(priority, HookPriority):
            # Convert int to closest priority
            for p in HookPriority:
                if priority <= p.value:
                    priority = p
                    break
            else:
                priority = HookPriority.LOWEST

        registration_id = str(uuid.uuid4())
        registration = HookRegistration(
            hook_type=hook_type,
            handler=handler,
            plugin_id=plugin_id,
            handler_name=handler_name or getattr(handler, "__name__", "unknown"),
            priority=priority,
            conditions=conditions or {},
            metadata=metadata or {},
        )

        self._registrations[registration_id] = registration
        self._hooks[hook_type].append(registration_id)

        # Sort by priority
        self._hooks[hook_type].sort(
            key=lambda rid: self._registrations[rid].priority.value
        )

        logger.debug(
            f"Registered hook handler '{registration.handler_name}' "
            f"for {hook_type.value} with priority {priority.value}"
        )

        return registration_id

    def unregister(self, registration_id: str) -> bool:
        """Unregister a hook handler.

        Args:
            registration_id: Registration ID to remove.

        Returns:
            True if successfully unregistered.
        """
        if registration_id not in self._registrations:
            return False

        registration = self._registrations[registration_id]
        hook_type = registration.hook_type

        if registration_id in self._hooks[hook_type]:
            self._hooks[hook_type].remove(registration_id)

        del self._registrations[registration_id]

        logger.debug(
            f"Unregistered hook handler '{registration.handler_name}' "
            f"from {hook_type.value}"
        )

        return True

    def unregister_plugin(self, plugin_id: str) -> int:
        """Unregister all handlers for a plugin.

        Args:
            plugin_id: Plugin ID.

        Returns:
            Number of handlers unregistered.
        """
        to_remove = [
            rid
            for rid, reg in self._registrations.items()
            if reg.plugin_id == plugin_id
        ]

        for rid in to_remove:
            self.unregister(rid)

        logger.debug(f"Unregistered {len(to_remove)} handlers for plugin {plugin_id}")

        return len(to_remove)

    def get_handlers(self, hook_type: HookType | str) -> list[HookRegistration]:
        """Get all registered handlers for a hook type.

        Args:
            hook_type: Type of hook.

        Returns:
            List of registrations, sorted by priority.
        """
        if isinstance(hook_type, str):
            hook_type = HookType(hook_type)

        return [
            self._registrations[rid]
            for rid in self._hooks.get(hook_type, [])
            if rid in self._registrations
        ]

    def execute(
        self,
        hook_type: HookType | str,
        data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        stop_on_cancel: bool = True,
        stop_on_error: bool = False,
    ) -> tuple[HookContext, list[HookResult]]:
        """Execute all handlers for a hook type synchronously.

        Args:
            hook_type: Type of hook.
            data: Data to pass to handlers.
            metadata: Additional metadata.
            stop_on_cancel: Stop if a handler cancels the operation.
            stop_on_error: Stop if a handler raises an error.

        Returns:
            Tuple of (final context, list of results).
        """
        if isinstance(hook_type, str):
            hook_type = HookType(hook_type)

        context = HookContext(
            hook_type=hook_type,
            data=data or {},
            metadata=metadata or {},
        )

        handlers = self.get_handlers(hook_type)
        results: list[HookResult] = []

        for registration in handlers:
            if not registration.enabled:
                continue

            if not registration.matches_conditions(context):
                results.append(
                    HookResult(
                        success=True,
                        plugin_id=registration.plugin_id,
                        handler_name=registration.handler_name,
                        skipped=True,
                    )
                )
                continue

            result = self._execute_handler(registration, context)
            results.append(result)
            context.results.append(result)

            if not result.success and stop_on_error:
                logger.warning(
                    f"Hook execution stopped due to error in "
                    f"'{registration.handler_name}': {result.error}"
                )
                break

            if context.cancelled and stop_on_cancel:
                logger.debug(
                    f"Hook execution cancelled by '{registration.handler_name}'"
                )
                break

        return context, results

    async def execute_async(
        self,
        hook_type: HookType | str,
        data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        stop_on_cancel: bool = True,
        stop_on_error: bool = False,
    ) -> tuple[HookContext, list[HookResult]]:
        """Execute all handlers for a hook type asynchronously.

        Args:
            hook_type: Type of hook.
            data: Data to pass to handlers.
            metadata: Additional metadata.
            stop_on_cancel: Stop if a handler cancels the operation.
            stop_on_error: Stop if a handler raises an error.

        Returns:
            Tuple of (final context, list of results).
        """
        async with self._lock:
            return self.execute(
                hook_type,
                data,
                metadata,
                stop_on_cancel,
                stop_on_error,
            )

    def _execute_handler(
        self,
        registration: HookRegistration,
        context: HookContext,
    ) -> HookResult:
        """Execute a single handler.

        Args:
            registration: Handler registration.
            context: Hook context.

        Returns:
            Handler result.
        """
        start_time = time.perf_counter()
        context.plugin_id = registration.plugin_id

        try:
            handler_result = registration.handler(context)

            execution_time = (time.perf_counter() - start_time) * 1000

            if handler_result is None:
                return HookResult(
                    success=True,
                    plugin_id=registration.plugin_id,
                    handler_name=registration.handler_name,
                    execution_time_ms=execution_time,
                )

            handler_result.execution_time_ms = execution_time
            handler_result.plugin_id = registration.plugin_id
            handler_result.handler_name = registration.handler_name

            return handler_result

        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"Error in hook handler '{registration.handler_name}': {e}",
                exc_info=True,
            )
            return HookResult(
                success=False,
                plugin_id=registration.plugin_id,
                handler_name=registration.handler_name,
                execution_time_ms=execution_time,
                error=str(e),
            )

    def create_context(
        self,
        hook_type: HookType | str,
        data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> HookContext:
        """Create a hook context.

        Args:
            hook_type: Type of hook.
            data: Context data.
            metadata: Additional metadata.

        Returns:
            New HookContext.
        """
        if isinstance(hook_type, str):
            hook_type = HookType(hook_type)

        return HookContext(
            hook_type=hook_type,
            data=data or {},
            metadata=metadata or {},
        )

    def list_hooks(self) -> dict[str, list[dict[str, Any]]]:
        """List all registered hooks.

        Returns:
            Dict mapping hook types to list of handler info.
        """
        result: dict[str, list[dict[str, Any]]] = {}

        for hook_type in HookType:
            handlers = self.get_handlers(hook_type)
            if handlers:
                result[hook_type.value] = [
                    {
                        "handler_name": h.handler_name,
                        "plugin_id": h.plugin_id,
                        "priority": h.priority.value,
                        "enabled": h.enabled,
                        "conditions": h.conditions,
                    }
                    for h in handlers
                ]

        return result

    def enable_handler(self, registration_id: str) -> bool:
        """Enable a handler.

        Args:
            registration_id: Registration ID.

        Returns:
            True if successful.
        """
        if registration_id in self._registrations:
            self._registrations[registration_id].enabled = True
            return True
        return False

    def disable_handler(self, registration_id: str) -> bool:
        """Disable a handler.

        Args:
            registration_id: Registration ID.

        Returns:
            True if successful.
        """
        if registration_id in self._registrations:
            self._registrations[registration_id].enabled = False
            return True
        return False

    def clear(self) -> None:
        """Clear all registrations."""
        self._registrations.clear()
        self._hooks.clear()


# Global hook manager instance
hook_manager = HookManager()
