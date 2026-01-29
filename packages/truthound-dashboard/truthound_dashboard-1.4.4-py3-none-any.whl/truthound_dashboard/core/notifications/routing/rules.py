"""Routing rule implementations.

This module provides 11 built-in rule types for matching notification
events against configurable conditions.

Rule Types:
    - SeverityRule: Match by issue severity
    - IssueCountRule: Match by issue count
    - PassRateRule: Match by validation pass rate
    - TimeWindowRule: Match by time of day/week
    - TagRule: Match by tags
    - DataAssetRule: Match by data asset pattern
    - MetadataRule: Match by metadata fields
    - StatusRule: Match by validation status
    - ErrorRule: Match by error patterns
    - AlwaysRule: Always matches
    - NeverRule: Never matches

Each rule can be serialized to/from JSON for configuration storage.
"""

from __future__ import annotations

import fnmatch
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from .engine import RouteContext


class Severity(str, Enum):
    """Issue severity levels for routing."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

    @classmethod
    def from_string(cls, value: str) -> "Severity":
        """Convert string to Severity enum."""
        try:
            return cls(value.lower())
        except ValueError:
            return cls.INFO

    def __ge__(self, other: "Severity") -> bool:
        """Compare severity levels."""
        order = [cls.INFO, cls.LOW, cls.MEDIUM, cls.HIGH, cls.CRITICAL]
        return order.index(self) >= order.index(other)

    def __gt__(self, other: "Severity") -> bool:
        """Compare severity levels."""
        order = [cls.INFO, cls.LOW, cls.MEDIUM, cls.HIGH, cls.CRITICAL]
        return order.index(self) > order.index(other)


class RuleRegistry:
    """Registry for routing rule types.

    Provides a plugin system for registering custom rule implementations.

    Usage:
        @RuleRegistry.register("custom")
        class CustomRule(BaseRule):
            ...

        rule = RuleRegistry.create("custom", params={...})
    """

    _rules: ClassVar[dict[str, type["BaseRule"]]] = {}

    @classmethod
    def register(cls, rule_type: str):
        """Decorator to register a rule type."""

        def decorator(rule_class: type["BaseRule"]) -> type["BaseRule"]:
            rule_class.rule_type = rule_type
            cls._rules[rule_type] = rule_class
            return rule_class

        return decorator

    @classmethod
    def get(cls, rule_type: str) -> type["BaseRule"] | None:
        """Get a registered rule class by type."""
        return cls._rules.get(rule_type)

    @classmethod
    def create(cls, rule_type: str, **params: Any) -> "BaseRule | None":
        """Create a rule instance by type."""
        rule_class = cls.get(rule_type)
        if rule_class is None:
            return None
        return rule_class(**params)

    @classmethod
    def list_types(cls) -> list[str]:
        """Get list of registered rule types."""
        return list(cls._rules.keys())

    @classmethod
    def get_all_schemas(cls) -> dict[str, dict[str, Any]]:
        """Get parameter schemas for all registered rules."""
        return {
            rule_type: rule_class.get_param_schema()
            for rule_type, rule_class in cls._rules.items()
        }


@dataclass
class BaseRule(ABC):
    """Abstract base class for routing rules.

    All rules must implement the `matches` method to evaluate
    whether an event context matches the rule's conditions.

    Rules can be serialized to/from JSON using `to_dict` and `from_dict`.
    """

    rule_type: ClassVar[str] = "base"

    @abstractmethod
    async def matches(self, context: "RouteContext") -> bool:
        """Check if the context matches this rule.

        Args:
            context: The routing context containing event and metadata.

        Returns:
            True if the rule matches.
        """
        ...

    @classmethod
    def get_param_schema(cls) -> dict[str, Any]:
        """Get parameter schema for this rule type.

        Returns:
            Dictionary describing the rule's parameters.
        """
        return {}

    def to_dict(self) -> dict[str, Any]:
        """Serialize rule to dictionary."""
        return {"type": self.rule_type}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaseRule | None":
        """Deserialize rule from dictionary."""
        rule_type = data.get("type")
        if rule_type is None:
            return None

        params = {k: v for k, v in data.items() if k != "type"}
        return RuleRegistry.create(rule_type, **params)


@RuleRegistry.register("severity")
@dataclass
class SeverityRule(BaseRule):
    """Match events by minimum severity level.

    Matches if the event's severity is greater than or equal to
    the specified minimum severity.

    Attributes:
        min_severity: Minimum severity to match (critical, high, medium, low, info).
    """

    min_severity: str = "high"

    @classmethod
    def get_param_schema(cls) -> dict[str, Any]:
        return {
            "min_severity": {
                "type": "string",
                "required": True,
                "description": "Minimum severity level",
                "enum": ["critical", "high", "medium", "low", "info"],
            }
        }

    async def matches(self, context: "RouteContext") -> bool:
        """Check if event severity meets minimum threshold."""
        event_severity = context.get_severity()
        if event_severity is None:
            return False

        min_sev = Severity.from_string(self.min_severity)
        actual_sev = Severity.from_string(event_severity)
        return actual_sev >= min_sev

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.rule_type, "min_severity": self.min_severity}


@RuleRegistry.register("issue_count")
@dataclass
class IssueCountRule(BaseRule):
    """Match events by minimum issue count.

    Matches if the event has at least the specified number of issues.

    Attributes:
        min_count: Minimum number of issues to match.
    """

    min_count: int = 1

    @classmethod
    def get_param_schema(cls) -> dict[str, Any]:
        return {
            "min_count": {
                "type": "integer",
                "required": True,
                "description": "Minimum issue count",
                "minimum": 0,
            }
        }

    async def matches(self, context: "RouteContext") -> bool:
        """Check if event has minimum issue count."""
        issue_count = context.get_issue_count()
        return issue_count is not None and issue_count >= self.min_count

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.rule_type, "min_count": self.min_count}


@RuleRegistry.register("pass_rate")
@dataclass
class PassRateRule(BaseRule):
    """Match events by maximum pass rate.

    Matches if the validation pass rate is below the specified threshold.

    Attributes:
        max_pass_rate: Maximum pass rate (0.0 to 1.0) to match.
    """

    max_pass_rate: float = 0.9

    @classmethod
    def get_param_schema(cls) -> dict[str, Any]:
        return {
            "max_pass_rate": {
                "type": "number",
                "required": True,
                "description": "Maximum pass rate (0.0 to 1.0)",
                "minimum": 0.0,
                "maximum": 1.0,
            }
        }

    async def matches(self, context: "RouteContext") -> bool:
        """Check if pass rate is below threshold."""
        pass_rate = context.get_pass_rate()
        return pass_rate is not None and pass_rate <= self.max_pass_rate

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.rule_type, "max_pass_rate": self.max_pass_rate}


@RuleRegistry.register("time_window")
@dataclass
class TimeWindowRule(BaseRule):
    """Match events by time of day and day of week.

    Matches if the current time falls within the specified window.
    Useful for business hours routing or off-hours escalation.

    Attributes:
        start_hour: Start hour (0-23).
        end_hour: End hour (0-23).
        weekdays: List of weekday numbers (0=Monday, 6=Sunday).
        timezone: Optional timezone name.
    """

    start_hour: int = 9
    end_hour: int = 17
    weekdays: list[int] = field(default_factory=lambda: [0, 1, 2, 3, 4])
    timezone: str | None = None

    @classmethod
    def get_param_schema(cls) -> dict[str, Any]:
        return {
            "start_hour": {
                "type": "integer",
                "required": True,
                "description": "Start hour (0-23)",
                "minimum": 0,
                "maximum": 23,
            },
            "end_hour": {
                "type": "integer",
                "required": True,
                "description": "End hour (0-23)",
                "minimum": 0,
                "maximum": 23,
            },
            "weekdays": {
                "type": "array",
                "required": False,
                "description": "Weekdays (0=Monday, 6=Sunday)",
                "items": {"type": "integer", "minimum": 0, "maximum": 6},
            },
            "timezone": {
                "type": "string",
                "required": False,
                "description": "Timezone name (e.g., 'America/New_York')",
            },
        }

    async def matches(self, context: "RouteContext") -> bool:
        """Check if current time is within window."""
        now = datetime.now()

        # Apply timezone if specified
        if self.timezone:
            try:
                import zoneinfo
                tz = zoneinfo.ZoneInfo(self.timezone)
                now = datetime.now(tz)
            except ImportError:
                pass

        # Check weekday
        if now.weekday() not in self.weekdays:
            return False

        # Check hour range
        current_hour = now.hour
        if self.start_hour <= self.end_hour:
            # Normal range (e.g., 9-17)
            return self.start_hour <= current_hour < self.end_hour
        else:
            # Overnight range (e.g., 22-6)
            return current_hour >= self.start_hour or current_hour < self.end_hour

    def to_dict(self) -> dict[str, Any]:
        data = {
            "type": self.rule_type,
            "start_hour": self.start_hour,
            "end_hour": self.end_hour,
            "weekdays": self.weekdays,
        }
        if self.timezone:
            data["timezone"] = self.timezone
        return data


@RuleRegistry.register("tag")
@dataclass
class TagRule(BaseRule):
    """Match events by tags.

    Matches if the event or context has any of the specified tags.

    Attributes:
        tags: List of tags to match.
        match_all: If True, all tags must match; if False, any tag matches.
    """

    tags: list[str] = field(default_factory=list)
    match_all: bool = False

    @classmethod
    def get_param_schema(cls) -> dict[str, Any]:
        return {
            "tags": {
                "type": "array",
                "required": True,
                "description": "Tags to match",
                "items": {"type": "string"},
            },
            "match_all": {
                "type": "boolean",
                "required": False,
                "description": "Require all tags to match",
            },
        }

    async def matches(self, context: "RouteContext") -> bool:
        """Check if context has matching tags."""
        context_tags = set(context.get_tags())

        if not self.tags:
            return True

        if self.match_all:
            return set(self.tags).issubset(context_tags)
        else:
            return bool(set(self.tags) & context_tags)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.rule_type,
            "tags": self.tags,
            "match_all": self.match_all,
        }


@RuleRegistry.register("data_asset")
@dataclass
class DataAssetRule(BaseRule):
    """Match events by data asset pattern.

    Matches if the source name or path matches a glob pattern.

    Attributes:
        pattern: Glob pattern to match (e.g., "*.parquet", "prod/*").
    """

    pattern: str = "*"

    @classmethod
    def get_param_schema(cls) -> dict[str, Any]:
        return {
            "pattern": {
                "type": "string",
                "required": True,
                "description": "Glob pattern to match data assets",
            }
        }

    async def matches(self, context: "RouteContext") -> bool:
        """Check if data asset matches pattern."""
        asset_name = context.get_data_asset()
        if asset_name is None:
            return False

        return fnmatch.fnmatch(asset_name.lower(), self.pattern.lower())

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.rule_type, "pattern": self.pattern}


@RuleRegistry.register("metadata")
@dataclass
class MetadataRule(BaseRule):
    """Match events by metadata field value.

    Matches if a metadata field equals a specific value.

    Attributes:
        key: Metadata field name.
        value: Expected value (supports string, number, boolean).
        operator: Comparison operator (eq, ne, contains, regex).
    """

    key: str = ""
    value: Any = None
    operator: str = "eq"

    @classmethod
    def get_param_schema(cls) -> dict[str, Any]:
        return {
            "key": {
                "type": "string",
                "required": True,
                "description": "Metadata field name",
            },
            "value": {
                "type": "any",
                "required": True,
                "description": "Expected value",
            },
            "operator": {
                "type": "string",
                "required": False,
                "description": "Comparison operator",
                "enum": ["eq", "ne", "contains", "regex", "gt", "lt", "gte", "lte"],
            },
        }

    async def matches(self, context: "RouteContext") -> bool:
        """Check if metadata field matches value."""
        actual = context.get_metadata(self.key)
        if actual is None:
            return False

        if self.operator == "eq":
            return actual == self.value
        elif self.operator == "ne":
            return actual != self.value
        elif self.operator == "contains":
            return str(self.value) in str(actual)
        elif self.operator == "regex":
            return bool(re.search(str(self.value), str(actual)))
        elif self.operator in ("gt", "lt", "gte", "lte"):
            try:
                a = float(actual)
                b = float(self.value)
                if self.operator == "gt":
                    return a > b
                elif self.operator == "lt":
                    return a < b
                elif self.operator == "gte":
                    return a >= b
                elif self.operator == "lte":
                    return a <= b
            except (ValueError, TypeError):
                return False

        return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.rule_type,
            "key": self.key,
            "value": self.value,
            "operator": self.operator,
        }


@RuleRegistry.register("status")
@dataclass
class StatusRule(BaseRule):
    """Match events by validation status.

    Matches if the validation status is in the specified list.

    Attributes:
        statuses: List of statuses to match (failure, error, warning, success).
    """

    statuses: list[str] = field(default_factory=lambda: ["failure", "error"])

    @classmethod
    def get_param_schema(cls) -> dict[str, Any]:
        return {
            "statuses": {
                "type": "array",
                "required": True,
                "description": "Validation statuses to match",
                "items": {
                    "type": "string",
                    "enum": ["failure", "error", "warning", "success"],
                },
            }
        }

    async def matches(self, context: "RouteContext") -> bool:
        """Check if validation status is in list."""
        status = context.get_status()
        return status is not None and status.lower() in [s.lower() for s in self.statuses]

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.rule_type, "statuses": self.statuses}


@RuleRegistry.register("error")
@dataclass
class ErrorRule(BaseRule):
    """Match events by error pattern.

    Matches if the error message contains or matches a pattern.

    Attributes:
        error_pattern: Regex pattern to match error messages.
    """

    error_pattern: str = ".*"

    @classmethod
    def get_param_schema(cls) -> dict[str, Any]:
        return {
            "error_pattern": {
                "type": "string",
                "required": True,
                "description": "Regex pattern to match errors",
            }
        }

    async def matches(self, context: "RouteContext") -> bool:
        """Check if error message matches pattern."""
        error = context.get_error_message()
        if error is None:
            return False

        return bool(re.search(self.error_pattern, error, re.IGNORECASE))

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.rule_type, "error_pattern": self.error_pattern}


@RuleRegistry.register("always")
@dataclass
class AlwaysRule(BaseRule):
    """Rule that always matches.

    Useful as a fallback or default route.
    """

    @classmethod
    def get_param_schema(cls) -> dict[str, Any]:
        return {}

    async def matches(self, context: "RouteContext") -> bool:
        """Always returns True."""
        return True


@RuleRegistry.register("never")
@dataclass
class NeverRule(BaseRule):
    """Rule that never matches.

    Useful for disabled routes without removing configuration.
    """

    @classmethod
    def get_param_schema(cls) -> dict[str, Any]:
        return {}

    async def matches(self, context: "RouteContext") -> bool:
        """Always returns False."""
        return False
