"""Advanced routing engine for notification dispatch.

This module provides a flexible, rule-based routing system for directing
notifications to appropriate channels based on configurable conditions.

Features:
    - 13 built-in rule types (severity, issue count, time window, expression, jinja2, etc.)
    - Rule combinators (AllOf, AnyOf, NotRule)
    - Plugin architecture for custom rules
    - YAML/JSON configuration support
    - Priority-based route ordering
    - Safe Python expression evaluation for complex routing conditions
    - Jinja2 template-based rules for flexible matching (optional)

Example:
    from truthound_dashboard.core.notifications.routing import (
        ActionRouter,
        Route,
        RouteContext,
        SeverityRule,
        ExpressionRule,
        AllOf,
    )

    # Create rules
    critical_rule = SeverityRule(min_severity="critical")
    production_rule = TagRule(tags=["production"])
    combined_rule = AllOf(rules=[critical_rule, production_rule])

    # Python expression-based rule for complex conditions
    expr_rule = ExpressionRule(
        expression="severity == 'critical' and pass_rate < 0.8",
    )

    # Create route
    route = Route(
        name="critical_production",
        rule=combined_rule,
        actions=["channel-1", "channel-2"],
        priority=100,
    )

    # Create router and match
    router = ActionRouter(routes=[route])
    context = RouteContext(event=event, metadata={"tags": ["production"]})
    matched_routes = await router.match(context)
"""

from .combinators import AllOf, AnyOf, NotRule
from .config import RouteConfigParser
from .config_parser import (
    ConfigBuilder,
    ConfigParser,
    RouteConfig,
    RoutingConfig,
    parse_routing_config,
)
from .engine import ActionRouter, Route, RouteContext, RoutingResult
from .expression_engine import (
    ExpressionContext,
    ExpressionError,
    ExpressionRule,
    ExpressionSecurityError,
    ExpressionTimeout,
    SafeExpressionEvaluator,
)
from .rules import (
    AlwaysRule,
    BaseRule,
    DataAssetRule,
    ErrorRule,
    IssueCountRule,
    MetadataRule,
    NeverRule,
    PassRateRule,
    RuleRegistry,
    SeverityRule,
    StatusRule,
    TagRule,
    TimeWindowRule,
)
from .validator import (
    RuleValidationConfig,
    RuleValidationError,
    RuleValidationResult,
    RuleValidator,
    ValidationError,
    ValidationErrorType,
    ValidationWarning,
    validate_rule_config,
)

# Jinja2 support (optional dependency)
try:
    from .jinja2_engine import (
        JINJA2_AVAILABLE,
        Jinja2Evaluator,
        Jinja2Rule,
        Jinja2SecurityError,
        Jinja2TemplateError,
        Jinja2TimeoutError,
        TemplateNotificationFormatter,
    )
except ImportError:
    JINJA2_AVAILABLE = False
    Jinja2Evaluator = None  # type: ignore
    Jinja2Rule = None  # type: ignore
    Jinja2TemplateError = None  # type: ignore
    Jinja2TimeoutError = None  # type: ignore
    Jinja2SecurityError = None  # type: ignore
    TemplateNotificationFormatter = None  # type: ignore

__all__ = [
    # Base
    "BaseRule",
    "RuleRegistry",
    # Rules
    "SeverityRule",
    "IssueCountRule",
    "PassRateRule",
    "TimeWindowRule",
    "TagRule",
    "DataAssetRule",
    "MetadataRule",
    "StatusRule",
    "ErrorRule",
    "AlwaysRule",
    "NeverRule",
    "ExpressionRule",
    # Expression Engine
    "ExpressionContext",
    "ExpressionError",
    "ExpressionTimeout",
    "ExpressionSecurityError",
    "SafeExpressionEvaluator",
    # Combinators
    "AllOf",
    "AnyOf",
    "NotRule",
    # Engine
    "ActionRouter",
    "Route",
    "RouteContext",
    "RoutingResult",
    # Config
    "RouteConfigParser",
    "ConfigParser",
    "ConfigBuilder",
    "RouteConfig",
    "RoutingConfig",
    "parse_routing_config",
    # Validator
    "RuleValidator",
    "RuleValidationConfig",
    "RuleValidationResult",
    "RuleValidationError",
    "ValidationError",
    "ValidationErrorType",
    "ValidationWarning",
    "validate_rule_config",
    # Jinja2 (optional)
    "JINJA2_AVAILABLE",
    "Jinja2Evaluator",
    "Jinja2Rule",
    "Jinja2TemplateError",
    "Jinja2TimeoutError",
    "Jinja2SecurityError",
    "TemplateNotificationFormatter",
]
