"""Jinja2 template engine for routing rules.

This module provides Jinja2-based rule evaluation for flexible, template-driven
notification routing. It supports secure sandboxed execution and custom filters
for common data quality operations.

Features:
    - SandboxedEnvironment for security
    - Custom filters: severity_level, is_critical, format_issues
    - Template-based condition evaluation
    - Notification message formatting

Example:
    from truthound_dashboard.core.notifications.routing.jinja2_engine import (
        Jinja2Evaluator,
        Jinja2Rule,
        TemplateNotificationFormatter,
    )

    # Template-based rule
    rule = Jinja2Rule(
        template="{{ severity == 'critical' and issue_count > 5 }}",
        expected_result="True",
    )
    matched = await rule.matches(context)

    # Message formatting
    formatter = TemplateNotificationFormatter()
    message = formatter.format_message(
        "Alert: {{ source_name }} has {{ issue_count }} issues",
        event_dict,
    )

Security:
    - Uses jinja2.sandbox.SandboxedEnvironment
    - Blocks filesystem and subprocess access
    - Limited function calls
    - Timeout protection via template complexity limits
"""

from __future__ import annotations

import signal
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar

try:
    from jinja2 import TemplateSyntaxError, UndefinedError
    from jinja2.sandbox import SandboxedEnvironment

    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    SandboxedEnvironment = None  # type: ignore
    TemplateSyntaxError = Exception  # type: ignore
    UndefinedError = Exception  # type: ignore

from .rules import BaseRule, RuleRegistry, Severity

if TYPE_CHECKING:
    from .engine import RouteContext


class Jinja2TemplateError(Exception):
    """Exception raised for Jinja2 template errors."""

    pass


class Jinja2TimeoutError(Exception):
    """Exception raised when template evaluation times out."""

    pass


class Jinja2SecurityError(Exception):
    """Exception raised for security violations in templates."""

    pass


@contextmanager
def timeout_handler(seconds: int):
    """Context manager for timeout protection on Unix systems.

    On non-Unix systems (Windows), this is a no-op as SIGALRM is not available.

    Args:
        seconds: Maximum execution time in seconds.

    Raises:
        Jinja2TimeoutError: If execution exceeds timeout.
    """

    def _timeout_handler(signum: int, frame: Any) -> None:
        raise Jinja2TimeoutError(f"Template evaluation timed out after {seconds} seconds")

    # Check if SIGALRM is available (Unix only)
    if hasattr(signal, "SIGALRM"):
        old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    else:
        # On Windows, just yield without timeout protection
        yield


# Custom Jinja2 filters
def severity_level(value: str) -> int:
    """Convert severity string to numeric level.

    Args:
        value: Severity string (critical, high, medium, low, info).

    Returns:
        Numeric level (5=critical, 4=high, 3=medium, 2=low, 1=info, 0=unknown).

    Example:
        {{ severity | severity_level > 3 }}  # critical or high
    """
    levels = {
        "critical": 5,
        "high": 4,
        "medium": 3,
        "low": 2,
        "info": 1,
    }
    return levels.get(str(value).lower(), 0)


def is_critical(value: str) -> bool:
    """Check if severity is critical.

    Args:
        value: Severity string.

    Returns:
        True if severity is critical.

    Example:
        {{ severity | is_critical }}
    """
    return str(value).lower() == "critical"


def is_high_or_critical(value: str) -> bool:
    """Check if severity is high or critical.

    Args:
        value: Severity string.

    Returns:
        True if severity is high or critical.

    Example:
        {{ severity | is_high_or_critical }}
    """
    return str(value).lower() in ("critical", "high")


def format_issues(issues: list[dict[str, Any]], max_items: int = 5) -> str:
    """Format a list of issues for display.

    Args:
        issues: List of issue dictionaries.
        max_items: Maximum number of issues to include.

    Returns:
        Formatted string of issues.

    Example:
        {{ issues | format_issues(3) }}
    """
    if not issues:
        return "No issues"

    formatted = []
    for issue in issues[:max_items]:
        validator = issue.get("validator", "Unknown")
        column = issue.get("column", "")
        message = issue.get("message", issue.get("description", ""))
        severity = issue.get("severity", "")

        if column:
            formatted.append(f"- [{severity}] {validator} ({column}): {message}")
        else:
            formatted.append(f"- [{severity}] {validator}: {message}")

    if len(issues) > max_items:
        formatted.append(f"  ... and {len(issues) - max_items} more")

    return "\n".join(formatted)


def format_percentage(value: float | int, decimals: int = 1) -> str:
    """Format a number as a percentage.

    Args:
        value: Number to format (0-1 for rate, or 0-100).
        decimals: Number of decimal places.

    Returns:
        Formatted percentage string.

    Example:
        {{ pass_rate | format_percentage }}  # "95.5%"
    """
    if value is None:
        return "N/A"

    # Assume values <= 1 are rates (0-1), otherwise treat as percentage
    if abs(value) <= 1:
        value = value * 100

    return f"{value:.{decimals}f}%"


def truncate_text(value: str, length: int = 100, suffix: str = "...") -> str:
    """Truncate text to a maximum length.

    Args:
        value: Text to truncate.
        length: Maximum length.
        suffix: Suffix to append if truncated.

    Returns:
        Truncated text.

    Example:
        {{ message | truncate_text(50) }}
    """
    if not value:
        return ""

    text = str(value)
    if len(text) <= length:
        return text

    return text[: length - len(suffix)] + suffix


def pluralize(count: int, singular: str, plural: str | None = None) -> str:
    """Return singular or plural form based on count.

    Args:
        count: The count.
        singular: Singular form.
        plural: Plural form (default: singular + 's').

    Returns:
        Appropriate form for the count.

    Example:
        {{ issue_count }} {{ issue_count | pluralize('issue') }}
    """
    if plural is None:
        plural = singular + "s"

    return singular if count == 1 else plural


class Jinja2Evaluator:
    """Jinja2 template evaluator with sandbox security.

    Provides secure template evaluation using Jinja2's SandboxedEnvironment.
    Includes custom filters for data quality operations.

    Attributes:
        env: The Jinja2 sandboxed environment.
        timeout: Maximum evaluation time in seconds.

    Example:
        evaluator = Jinja2Evaluator(sandbox=True)
        result = evaluator.evaluate(
            "{{ source_name }}: {{ issue_count }} issues",
            {"source_name": "users.csv", "issue_count": 5}
        )
        # Result: "users.csv: 5 issues"

        is_match = evaluator.evaluate_condition(
            "{{ severity == 'critical' and issue_count > 3 }}",
            {"severity": "critical", "issue_count": 5}
        )
        # Result: True
    """

    # Default timeout for template evaluation (seconds)
    DEFAULT_TIMEOUT: ClassVar[int] = 5

    # Maximum template length to prevent DoS
    MAX_TEMPLATE_LENGTH: ClassVar[int] = 10000

    def __init__(self, sandbox: bool = True, timeout: int | None = None) -> None:
        """Initialize the Jinja2 evaluator.

        Args:
            sandbox: If True, use SandboxedEnvironment for security.
            timeout: Maximum evaluation time in seconds.

        Raises:
            ImportError: If jinja2 is not installed.
        """
        if not JINJA2_AVAILABLE:
            raise ImportError(
                "jinja2 is required for Jinja2 template support. "
                "Install it with: pip install jinja2"
            )

        self.timeout = timeout or self.DEFAULT_TIMEOUT

        if sandbox:
            self.env = SandboxedEnvironment(
                autoescape=False,  # We handle escaping as needed
                cache_size=100,  # Cache compiled templates
            )
        else:
            # Non-sandboxed environment - use with caution
            from jinja2 import Environment

            self.env = Environment(
                autoescape=False,
                cache_size=100,
            )

        # Register custom filters
        self._register_filters()

    def _register_filters(self) -> None:
        """Register custom filters in the environment."""
        self.env.filters["severity_level"] = severity_level
        self.env.filters["is_critical"] = is_critical
        self.env.filters["is_high_or_critical"] = is_high_or_critical
        self.env.filters["format_issues"] = format_issues
        self.env.filters["format_percentage"] = format_percentage
        self.env.filters["truncate_text"] = truncate_text
        self.env.filters["pluralize"] = pluralize

    def _validate_template(self, template: str) -> None:
        """Validate template for security and sanity.

        Args:
            template: Template string to validate.

        Raises:
            Jinja2SecurityError: If template contains dangerous patterns.
            Jinja2TemplateError: If template is too long.
        """
        if len(template) > self.MAX_TEMPLATE_LENGTH:
            raise Jinja2TemplateError(
                f"Template exceeds maximum length of {self.MAX_TEMPLATE_LENGTH} characters"
            )

        # Check for potentially dangerous patterns
        dangerous_patterns = [
            "__class__",
            "__mro__",
            "__subclasses__",
            "__globals__",
            "__builtins__",
            "__import__",
            "subprocess",
            "popen",
            "system",
            "eval(",
            "exec(",
            "compile(",
            "open(",
            "file(",
        ]

        template_lower = template.lower()
        for pattern in dangerous_patterns:
            if pattern.lower() in template_lower:
                raise Jinja2SecurityError(
                    f"Template contains potentially dangerous pattern: {pattern}"
                )

    def evaluate(self, template: str, context: dict[str, Any]) -> str:
        """Render a Jinja2 template with the given context.

        Args:
            template: Jinja2 template string.
            context: Dictionary of variables available in template.

        Returns:
            Rendered template string.

        Raises:
            Jinja2TemplateError: If template is invalid.
            Jinja2SecurityError: If template contains dangerous patterns.
            Jinja2TimeoutError: If evaluation times out.

        Example:
            result = evaluator.evaluate(
                "Source: {{ name }}, Issues: {{ count }}",
                {"name": "users.csv", "count": 5}
            )
        """
        self._validate_template(template)

        try:
            with timeout_handler(self.timeout):
                compiled = self.env.from_string(template)
                return compiled.render(**context)
        except TemplateSyntaxError as e:
            raise Jinja2TemplateError(f"Template syntax error: {e}") from e
        except UndefinedError as e:
            raise Jinja2TemplateError(f"Undefined variable in template: {e}") from e
        except Jinja2TimeoutError:
            raise
        except Exception as e:
            raise Jinja2TemplateError(f"Template evaluation error: {e}") from e

    def evaluate_condition(self, template: str, context: dict[str, Any]) -> bool:
        """Evaluate a template as a boolean condition.

        The template should render to a value that can be interpreted as
        boolean. Strings like "true", "True", "1", "yes" are True.
        Strings like "false", "False", "0", "no", "" are False.

        Args:
            template: Jinja2 template that evaluates to a boolean-like value.
            context: Dictionary of variables available in template.

        Returns:
            Boolean result of condition evaluation.

        Raises:
            Jinja2TemplateError: If template is invalid.

        Example:
            is_match = evaluator.evaluate_condition(
                "{{ severity == 'critical' }}",
                {"severity": "critical"}
            )  # Returns True
        """
        result = self.evaluate(template, context)

        # Normalize result to boolean
        result_lower = result.strip().lower()

        # Python boolean repr
        if result_lower in ("true", "1", "yes", "on"):
            return True
        if result_lower in ("false", "0", "no", "off", "none", ""):
            return False

        # Non-empty string is truthy
        return bool(result.strip())


@RuleRegistry.register("jinja2")
@dataclass
class Jinja2Rule(BaseRule):
    """Rule that evaluates Jinja2 templates for matching.

    Uses Jinja2 templates to create flexible, expression-based routing rules.
    The template should evaluate to a boolean-like value.

    Attributes:
        template: Jinja2 template expression.
        expected_result: Expected result for match (default "true").

    Example templates:
        - "{{ severity == 'critical' }}"
        - "{{ severity | is_critical and issue_count > 5 }}"
        - "{{ pass_rate < 0.9 and 'production' in tags }}"
        - "{{ severity | severity_level >= 4 }}"

    Available context variables:
        - severity: Issue severity level
        - issue_count: Number of issues
        - pass_rate: Validation pass rate
        - tags: List of context tags
        - data_asset: Data asset name/path
        - status: Validation status
        - error_message: Error message if any
        - metadata: Additional metadata dictionary
        - event: Full event dictionary

    Available filters:
        - severity_level: Convert severity to numeric (5=critical to 1=info)
        - is_critical: Check if severity is critical
        - is_high_or_critical: Check if severity is high or critical
        - format_issues: Format issue list for display
        - format_percentage: Format number as percentage
        - truncate_text: Truncate text with ellipsis
        - pluralize: Singular/plural form based on count
    """

    template: str = "{{ true }}"
    expected_result: str = "true"

    # Class-level evaluator for reuse
    _evaluator: ClassVar[Jinja2Evaluator | None] = None

    @classmethod
    def _get_evaluator(cls) -> Jinja2Evaluator:
        """Get or create the Jinja2 evaluator."""
        if cls._evaluator is None:
            cls._evaluator = Jinja2Evaluator(sandbox=True)
        return cls._evaluator

    @classmethod
    def get_param_schema(cls) -> dict[str, Any]:
        """Get parameter schema for this rule type."""
        return {
            "template": {
                "type": "string",
                "required": True,
                "description": "Jinja2 template expression (e.g., '{{ severity == \"critical\" }}')",
            },
            "expected_result": {
                "type": "string",
                "required": False,
                "description": "Expected result for match (default: 'true')",
                "default": "true",
            },
        }

    def _build_context(self, context: "RouteContext") -> dict[str, Any]:
        """Build template context from RouteContext.

        Args:
            context: The routing context.

        Returns:
            Dictionary suitable for template evaluation.
        """
        # Get event as dict if available
        event_dict = {}
        if hasattr(context.event, "to_dict"):
            event_dict = context.event.to_dict()
        elif hasattr(context.event, "__dict__"):
            event_dict = {
                k: v for k, v in context.event.__dict__.items() if not k.startswith("_")
            }

        return {
            # Direct accessors
            "severity": context.get_severity() or "",
            "issue_count": context.get_issue_count() or 0,
            "pass_rate": context.get_pass_rate() or 0.0,
            "tags": context.get_tags(),
            "data_asset": context.get_data_asset() or "",
            "status": context.get_status() or "",
            "error_message": context.get_error_message() or "",
            # Full access
            "metadata": context.metadata,
            "event": event_dict,
            # Timestamp
            "timestamp": context.timestamp,
            # Source info
            "source_name": context.event.source_name if context.event else "",
            "source_id": context.event.source_id if context.event else "",
            # Helper values
            "has_issues": (context.get_issue_count() or 0) > 0,
            "is_failure": context.get_status() in ("failure", "error"),
        }

    async def matches(self, context: "RouteContext") -> bool:
        """Check if the context matches this rule.

        Args:
            context: The routing context containing event and metadata.

        Returns:
            True if the template evaluates to the expected result.
        """
        try:
            evaluator = self._get_evaluator()
            template_context = self._build_context(context)

            if self.expected_result.lower() == "true":
                # Direct boolean evaluation
                return evaluator.evaluate_condition(self.template, template_context)
            else:
                # String comparison
                result = evaluator.evaluate(self.template, template_context)
                return result.strip().lower() == self.expected_result.lower()

        except (Jinja2TemplateError, Jinja2SecurityError, Jinja2TimeoutError):
            # Template errors should not match
            return False
        except Exception:
            # Any unexpected error should not match
            return False

    def to_dict(self) -> dict[str, Any]:
        """Serialize rule to dictionary."""
        return {
            "type": self.rule_type,
            "template": self.template,
            "expected_result": self.expected_result,
        }


class TemplateNotificationFormatter:
    """Format notification messages using Jinja2 templates.

    Provides a simple interface for creating dynamic notification messages
    based on event data.

    Example:
        formatter = TemplateNotificationFormatter()

        message = formatter.format_message(
            "Validation failed for {{ source_name }}: "
            "{{ issue_count }} {{ issue_count | pluralize('issue') }} found",
            {"source_name": "users.csv", "issue_count": 5}
        )
        # Result: "Validation failed for users.csv: 5 issues found"

    Default templates:
        The formatter includes built-in templates for common notification types.
    """

    # Built-in notification templates
    DEFAULT_TEMPLATES: ClassVar[dict[str, str]] = {
        "validation_failed": (
            "Validation Failed: {{ source_name }}\n"
            "Severity: {{ severity }}\n"
            "Issues: {{ issue_count }}\n"
            "{% if pass_rate %}Pass Rate: {{ pass_rate | format_percentage }}{% endif %}\n"
            "{% if issues %}{{ issues | format_issues(5) }}{% endif %}"
        ),
        "drift_detected": (
            "Drift Detected\n"
            "Baseline: {{ baseline_source_name }}\n"
            "Current: {{ current_source_name }}\n"
            "Drifted Columns: {{ drifted_columns }}/{{ total_columns }} "
            "({{ (drifted_columns / total_columns * 100) | round(1) }}%)"
        ),
        "schedule_failed": (
            "Scheduled Validation Failed\n"
            "Schedule: {{ schedule_name }}\n"
            "{% if error_message %}Error: {{ error_message | truncate_text(200) }}{% endif %}"
        ),
        "schema_changed": (
            "Schema Changed: {{ source_name }}\n"
            "Version: {{ from_version or 'N/A' }} -> {{ to_version }}\n"
            "Changes: {{ total_changes }} ({{ breaking_changes }} breaking)"
        ),
        "generic": (
            "{{ event_type | title }}\n"
            "Source: {{ source_name }}\n"
            "Time: {{ timestamp }}"
        ),
    }

    def __init__(self, evaluator: Jinja2Evaluator | None = None) -> None:
        """Initialize the formatter.

        Args:
            evaluator: Optional Jinja2Evaluator instance. If not provided,
                      creates a new sandboxed evaluator.
        """
        self._evaluator = evaluator or Jinja2Evaluator(sandbox=True)

    def format_message(
        self,
        template: str,
        event: dict[str, Any],
        extra_context: dict[str, Any] | None = None,
    ) -> str:
        """Format a notification message using a template.

        Args:
            template: Jinja2 template string.
            event: Event dictionary with data for template.
            extra_context: Additional context variables.

        Returns:
            Formatted message string.

        Raises:
            Jinja2TemplateError: If template is invalid.

        Example:
            message = formatter.format_message(
                "Alert: {{ source_name }} - {{ severity }}",
                {"source_name": "users.csv", "severity": "critical"}
            )
        """
        context = {**event}
        if extra_context:
            context.update(extra_context)

        return self._evaluator.evaluate(template, context)

    def format_with_default(
        self,
        event_type: str,
        event: dict[str, Any],
        custom_template: str | None = None,
    ) -> str:
        """Format a message using default or custom template.

        Args:
            event_type: Type of event (validation_failed, drift_detected, etc.).
            event: Event dictionary.
            custom_template: Optional custom template to use instead of default.

        Returns:
            Formatted message string.

        Example:
            message = formatter.format_with_default(
                "validation_failed",
                event_dict
            )
        """
        template = custom_template or self.DEFAULT_TEMPLATES.get(
            event_type, self.DEFAULT_TEMPLATES["generic"]
        )

        # Add event_type to context if not present
        if "event_type" not in event:
            event = {**event, "event_type": event_type}

        return self.format_message(template, event)

    def validate_template(self, template: str) -> tuple[bool, str | None]:
        """Validate a template without rendering.

        Args:
            template: Template string to validate.

        Returns:
            Tuple of (is_valid, error_message).

        Example:
            is_valid, error = formatter.validate_template("{{ invalid }")
            if not is_valid:
                print(f"Template error: {error}")
        """
        try:
            self._evaluator._validate_template(template)
            # Try to compile the template
            self._evaluator.env.from_string(template)
            return True, None
        except Jinja2SecurityError as e:
            return False, f"Security error: {e}"
        except Jinja2TemplateError as e:
            return False, str(e)
        except TemplateSyntaxError as e:
            return False, f"Syntax error: {e}"
        except Exception as e:
            return False, f"Validation error: {e}"


# Export all public classes and exceptions
__all__ = [
    "Jinja2Evaluator",
    "Jinja2Rule",
    "TemplateNotificationFormatter",
    "Jinja2TemplateError",
    "Jinja2TimeoutError",
    "Jinja2SecurityError",
    "JINJA2_AVAILABLE",
    # Custom filters (for external use)
    "severity_level",
    "is_critical",
    "is_high_or_critical",
    "format_issues",
    "format_percentage",
    "truncate_text",
    "pluralize",
]
