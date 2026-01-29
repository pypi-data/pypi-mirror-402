"""Rule combinators for complex routing logic.

This module provides combinators that compose multiple rules
into complex conditions:

- AllOf: All rules must match (AND logic)
- AnyOf: Any rule must match (OR logic)
- NotRule: Negates a rule

Example:
    # Critical severity AND production tag
    rule = AllOf(rules=[
        SeverityRule(min_severity="critical"),
        TagRule(tags=["production"]),
    ])

    # Critical OR high issue count
    rule = AnyOf(rules=[
        SeverityRule(min_severity="critical"),
        IssueCountRule(min_count=10),
    ])

    # NOT during business hours
    rule = NotRule(rule=TimeWindowRule(start_hour=9, end_hour=17))
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .rules import BaseRule, RuleRegistry

if TYPE_CHECKING:
    from .engine import RouteContext


@RuleRegistry.register("all_of")
@dataclass
class AllOf(BaseRule):
    """Combinator that requires all child rules to match.

    Implements AND logic: the combinator matches only if
    every child rule matches.

    Attributes:
        rules: List of rules that must all match.
    """

    rules: list[BaseRule] = field(default_factory=list)

    @classmethod
    def get_param_schema(cls) -> dict[str, Any]:
        return {
            "rules": {
                "type": "array",
                "required": True,
                "description": "Rules that must all match",
                "items": {"type": "object"},
            }
        }

    async def matches(self, context: "RouteContext") -> bool:
        """Check if all child rules match."""
        if not self.rules:
            return True

        for rule in self.rules:
            if not await rule.matches(context):
                return False
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.rule_type,
            "rules": [rule.to_dict() for rule in self.rules],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AllOf":
        """Create AllOf from dictionary."""
        rules_data = data.get("rules", [])
        rules = []
        for rule_data in rules_data:
            rule = BaseRule.from_dict(rule_data)
            if rule:
                rules.append(rule)
        return cls(rules=rules)


@RuleRegistry.register("any_of")
@dataclass
class AnyOf(BaseRule):
    """Combinator that requires any child rule to match.

    Implements OR logic: the combinator matches if
    at least one child rule matches.

    Attributes:
        rules: List of rules where at least one must match.
    """

    rules: list[BaseRule] = field(default_factory=list)

    @classmethod
    def get_param_schema(cls) -> dict[str, Any]:
        return {
            "rules": {
                "type": "array",
                "required": True,
                "description": "Rules where at least one must match",
                "items": {"type": "object"},
            }
        }

    async def matches(self, context: "RouteContext") -> bool:
        """Check if any child rule matches."""
        if not self.rules:
            return False

        for rule in self.rules:
            if await rule.matches(context):
                return True
        return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.rule_type,
            "rules": [rule.to_dict() for rule in self.rules],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AnyOf":
        """Create AnyOf from dictionary."""
        rules_data = data.get("rules", [])
        rules = []
        for rule_data in rules_data:
            rule = BaseRule.from_dict(rule_data)
            if rule:
                rules.append(rule)
        return cls(rules=rules)


@RuleRegistry.register("not")
@dataclass
class NotRule(BaseRule):
    """Combinator that negates a rule.

    Matches when the child rule does NOT match.

    Attributes:
        rule: The rule to negate.
    """

    rule: BaseRule | None = None

    @classmethod
    def get_param_schema(cls) -> dict[str, Any]:
        return {
            "rule": {
                "type": "object",
                "required": True,
                "description": "Rule to negate",
            }
        }

    async def matches(self, context: "RouteContext") -> bool:
        """Check if child rule does NOT match."""
        if self.rule is None:
            return False
        return not await self.rule.matches(context)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.rule_type,
            "rule": self.rule.to_dict() if self.rule else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NotRule":
        """Create NotRule from dictionary."""
        rule_data = data.get("rule")
        rule = BaseRule.from_dict(rule_data) if rule_data else None
        return cls(rule=rule)
