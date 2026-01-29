"""Hook Decorators.

This module provides decorators for easily registering
hook handlers from plugin code.
"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar

from .protocols import HookContext, HookPriority, HookResult, HookType
from .manager import hook_manager

F = TypeVar("F", bound=Callable[..., Any])


def hook(
    hook_type: HookType | str,
    priority: HookPriority | int = HookPriority.NORMAL,
    conditions: dict[str, Any] | None = None,
    plugin_id: str | None = None,
    auto_register: bool = True,
) -> Callable[[F], F]:
    """Decorator to register a function as a hook handler.

    Args:
        hook_type: Type of hook to register for.
        priority: Execution priority.
        conditions: Conditions for executing.
        plugin_id: ID of the registering plugin.
        auto_register: Whether to auto-register with global manager.

    Returns:
        Decorator function.

    Example:
        @hook(HookType.BEFORE_VALIDATION)
        def my_handler(context: HookContext) -> HookResult | None:
            # Process the hook
            return HookResult(success=True)
    """
    if isinstance(hook_type, str):
        hook_type = HookType(hook_type)

    def decorator(func: F) -> F:
        # Store hook metadata on the function
        func._hook_type = hook_type  # type: ignore
        func._hook_priority = priority  # type: ignore
        func._hook_conditions = conditions or {}  # type: ignore
        func._hook_plugin_id = plugin_id  # type: ignore

        if auto_register:
            hook_manager.register(
                hook_type=hook_type,
                handler=func,
                plugin_id=plugin_id,
                priority=priority,
                conditions=conditions,
                handler_name=func.__name__,
            )

        return func

    return decorator


def before_validation(
    priority: HookPriority | int = HookPriority.NORMAL,
    conditions: dict[str, Any] | None = None,
    plugin_id: str | None = None,
) -> Callable[[F], F]:
    """Decorator for before_validation hooks.

    The handler receives:
        - context.data["source_id"]: Data source ID
        - context.data["validators"]: List of validators to run
        - context.data["config"]: Validation configuration

    The handler can:
        - Modify validators list via context.modify("validators", [...])
        - Cancel validation via context.cancel()

    Example:
        @before_validation()
        def add_custom_validator(context: HookContext) -> HookResult | None:
            validators = context.get("validators", [])
            validators.append("my_custom_validator")
            context.modify("validators", validators)
            return HookResult(success=True, data={"added": "my_custom_validator"})
    """
    return hook(
        HookType.BEFORE_VALIDATION,
        priority=priority,
        conditions=conditions,
        plugin_id=plugin_id,
    )


def after_validation(
    priority: HookPriority | int = HookPriority.NORMAL,
    conditions: dict[str, Any] | None = None,
    plugin_id: str | None = None,
) -> Callable[[F], F]:
    """Decorator for after_validation hooks.

    The handler receives:
        - context.data["source_id"]: Data source ID
        - context.data["result"]: Validation result
        - context.data["issues"]: List of validation issues
        - context.data["execution_time_ms"]: Execution time

    Example:
        @after_validation()
        def log_validation_result(context: HookContext) -> HookResult | None:
            issues = context.get("issues", [])
            if issues:
                print(f"Found {len(issues)} issues")
            return HookResult(success=True)
    """
    return hook(
        HookType.AFTER_VALIDATION,
        priority=priority,
        conditions=conditions,
        plugin_id=plugin_id,
    )


def on_issue_found(
    priority: HookPriority | int = HookPriority.NORMAL,
    conditions: dict[str, Any] | None = None,
    plugin_id: str | None = None,
) -> Callable[[F], F]:
    """Decorator for on_issue_found hooks.

    The handler receives:
        - context.data["issue"]: The validation issue
        - context.data["validator"]: The validator that found it
        - context.data["column"]: Column name (if applicable)
        - context.data["row_index"]: Row index (if applicable)

    The handler can:
        - Modify issue severity via context.modify("issue", {...})
        - Suppress issue via context.modify("suppress", True)

    Example:
        @on_issue_found()
        def filter_known_issues(context: HookContext) -> HookResult | None:
            issue = context.get("issue", {})
            if "known_pattern" in issue.get("message", ""):
                context.modify("suppress", True)
            return HookResult(success=True)
    """
    return hook(
        HookType.ON_ISSUE_FOUND,
        priority=priority,
        conditions=conditions,
        plugin_id=plugin_id,
    )


def before_profile(
    priority: HookPriority | int = HookPriority.NORMAL,
    conditions: dict[str, Any] | None = None,
    plugin_id: str | None = None,
) -> Callable[[F], F]:
    """Decorator for before_profile hooks.

    The handler receives:
        - context.data["source_id"]: Data source ID
        - context.data["config"]: Profiling configuration
        - context.data["columns"]: Columns to profile

    Example:
        @before_profile()
        def configure_profiling(context: HookContext) -> HookResult | None:
            config = context.get("config", {})
            config["sample_size"] = 10000
            context.modify("config", config)
            return HookResult(success=True)
    """
    return hook(
        HookType.BEFORE_PROFILE,
        priority=priority,
        conditions=conditions,
        plugin_id=plugin_id,
    )


def after_profile(
    priority: HookPriority | int = HookPriority.NORMAL,
    conditions: dict[str, Any] | None = None,
    plugin_id: str | None = None,
) -> Callable[[F], F]:
    """Decorator for after_profile hooks.

    The handler receives:
        - context.data["source_id"]: Data source ID
        - context.data["profile"]: Profile result
        - context.data["execution_time_ms"]: Execution time

    Example:
        @after_profile()
        def analyze_profile(context: HookContext) -> HookResult | None:
            profile = context.get("profile", {})
            # Perform additional analysis
            return HookResult(success=True, data={"analysis": {...}})
    """
    return hook(
        HookType.AFTER_PROFILE,
        priority=priority,
        conditions=conditions,
        plugin_id=plugin_id,
    )


def on_report_generate(
    priority: HookPriority | int = HookPriority.NORMAL,
    conditions: dict[str, Any] | None = None,
    plugin_id: str | None = None,
) -> Callable[[F], F]:
    """Decorator for on_report_generate hooks.

    The handler receives:
        - context.data["report"]: Report data
        - context.data["format"]: Output format (html, pdf, json, etc.)
        - context.data["config"]: Report configuration

    The handler can:
        - Add sections via context.modify("sections", [...])
        - Modify report data via context.modify("report", {...})

    Example:
        @on_report_generate()
        def add_summary(context: HookContext) -> HookResult | None:
            report = context.get("report", {})
            report["custom_summary"] = "Generated by plugin"
            context.modify("report", report)
            return HookResult(success=True)
    """
    return hook(
        HookType.ON_REPORT_GENERATE,
        priority=priority,
        conditions=conditions,
        plugin_id=plugin_id,
    )


def on_error(
    priority: HookPriority | int = HookPriority.NORMAL,
    conditions: dict[str, Any] | None = None,
    plugin_id: str | None = None,
) -> Callable[[F], F]:
    """Decorator for on_error hooks.

    The handler receives:
        - context.data["error"]: The exception
        - context.data["error_type"]: Exception type name
        - context.data["context"]: Error context (operation, source, etc.)
        - context.data["traceback"]: Traceback string

    The handler can:
        - Suppress error via context.modify("suppress", True)
        - Provide fallback via context.modify("fallback", value)
        - Request retry via context.modify("retry", True)

    Example:
        @on_error()
        def handle_connection_error(context: HookContext) -> HookResult | None:
            error_type = context.get("error_type")
            if error_type == "ConnectionError":
                context.modify("retry", True)
                return HookResult(success=True, data={"action": "retry"})
            return None
    """
    return hook(
        HookType.ON_ERROR,
        priority=priority,
        conditions=conditions,
        plugin_id=plugin_id,
    )


class HookRegistrar:
    """Helper class for registering multiple hooks from a plugin.

    Example:
        class MyPlugin:
            def __init__(self):
                self.hooks = HookRegistrar("my-plugin")

            def register_hooks(self):
                self.hooks.register(
                    HookType.BEFORE_VALIDATION,
                    self.before_validation,
                )
                self.hooks.register(
                    HookType.AFTER_VALIDATION,
                    self.after_validation,
                )

            def unregister_hooks(self):
                self.hooks.unregister_all()
    """

    def __init__(self, plugin_id: str) -> None:
        """Initialize the registrar.

        Args:
            plugin_id: Plugin ID for all registrations.
        """
        self.plugin_id = plugin_id
        self._registration_ids: list[str] = []

    def register(
        self,
        hook_type: HookType | str,
        handler: Callable[[HookContext], HookResult | None],
        priority: HookPriority | int = HookPriority.NORMAL,
        conditions: dict[str, Any] | None = None,
    ) -> str:
        """Register a hook handler.

        Args:
            hook_type: Type of hook.
            handler: Handler function.
            priority: Execution priority.
            conditions: Conditions for executing.

        Returns:
            Registration ID.
        """
        reg_id = hook_manager.register(
            hook_type=hook_type,
            handler=handler,
            plugin_id=self.plugin_id,
            priority=priority,
            conditions=conditions,
        )
        self._registration_ids.append(reg_id)
        return reg_id

    def unregister(self, registration_id: str) -> bool:
        """Unregister a specific handler.

        Args:
            registration_id: Registration ID.

        Returns:
            True if successful.
        """
        if registration_id in self._registration_ids:
            self._registration_ids.remove(registration_id)
        return hook_manager.unregister(registration_id)

    def unregister_all(self) -> int:
        """Unregister all handlers for this plugin.

        Returns:
            Number of handlers unregistered.
        """
        count = 0
        for reg_id in list(self._registration_ids):
            if hook_manager.unregister(reg_id):
                count += 1
        self._registration_ids.clear()
        return count
