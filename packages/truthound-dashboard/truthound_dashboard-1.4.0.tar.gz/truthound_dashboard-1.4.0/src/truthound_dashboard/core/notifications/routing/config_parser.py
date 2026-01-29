"""YAML/JSON configuration parser for routing rules.

This module provides comprehensive configuration parsing for creating
routes and rules from YAML/JSON files or programmatic builders.

Features:
    - RouteConfig and RoutingConfig dataclasses for structured configuration
    - ConfigParser for parsing YAML/JSON configurations
    - ConfigBuilder for programmatic configuration creation
    - Nested rule support with combinators (all_of, any_of, not)
    - Validation against RuleRegistry

Example YAML config:
    version: "1.0"
    defaults:
      priority: 0
      stop_on_match: false
    routes:
      - name: critical_alerts
        rules:
          - type: any_of
            rules:
              - type: severity
                params:
                  min_level: critical
              - type: all_of
                rules:
                  - type: issue_count
                    params:
                      min_count: 10
                  - type: tag
                    params:
                      tags: ["production"]
        actions: ["pagerduty", "slack-critical"]
        priority: 100

Example usage:
    # Parse from file
    config = ConfigParser.parse_file(Path("routes.yaml"))

    # Build programmatically
    config = (
        ConfigBuilder()
        .with_defaults(priority=0)
        .add_route(
            name="critical",
            rules=[{"type": "severity", "params": {"min_severity": "critical"}}],
            actions=["pagerduty"],
            priority=100,
        )
        .build()
    )

    # Export to YAML/JSON
    yaml_str = ConfigParser.to_yaml(config)
    json_str = ConfigParser.to_json(config)

    # Validate configuration
    errors = ConfigParser.validate(config)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from .engine import ActionRouter


@dataclass
class RouteConfig:
    """Configuration for a single routing rule.

    Attributes:
        name: Unique route identifier.
        rules: List of rule configurations (can be nested for combinators).
        actions: List of action/channel identifiers to trigger on match.
        priority: Route evaluation priority (higher = evaluated first).
        stop_on_match: If True, stop evaluating lower priority routes on match.
        metadata: Additional route metadata.
    """

    name: str
    rules: list[dict[str, Any]]
    actions: list[str]
    priority: int = 0
    stop_on_match: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize route configuration to dictionary."""
        return {
            "name": self.name,
            "rules": self.rules,
            "actions": self.actions,
            "priority": self.priority,
            "stop_on_match": self.stop_on_match,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], defaults: dict[str, Any] | None = None) -> RouteConfig:
        """Create RouteConfig from dictionary.

        Args:
            data: Route configuration dictionary.
            defaults: Optional default values to apply.

        Returns:
            RouteConfig instance.
        """
        defaults = defaults or {}

        # Handle single rule vs rules list
        rules = data.get("rules", [])
        if "rule" in data and not rules:
            # Support single rule format for backward compatibility
            rules = [data["rule"]]

        return cls(
            name=data.get("name", "unnamed"),
            rules=rules,
            actions=data.get("actions", []),
            priority=data.get("priority", defaults.get("priority", 0)),
            stop_on_match=data.get("stop_on_match", defaults.get("stop_on_match", False)),
            metadata=data.get("metadata", defaults.get("metadata", {})),
        )


@dataclass
class RoutingConfig:
    """Full routing configuration.

    Attributes:
        version: Configuration version string.
        routes: List of route configurations.
        defaults: Default values applied to routes.
    """

    version: str = "1.0"
    routes: list[RouteConfig] = field(default_factory=list)
    defaults: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize routing configuration to dictionary."""
        return {
            "version": self.version,
            "defaults": self.defaults,
            "routes": [route.to_dict() for route in self.routes],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RoutingConfig:
        """Create RoutingConfig from dictionary.

        Args:
            data: Configuration dictionary.

        Returns:
            RoutingConfig instance.
        """
        version = data.get("version", "1.0")
        defaults = data.get("defaults", {})
        routes_data = data.get("routes", [])

        routes = [RouteConfig.from_dict(route_data, defaults) for route_data in routes_data]

        return cls(
            version=version,
            routes=routes,
            defaults=defaults,
        )


class ConfigParser:
    """Parser for YAML/JSON routing configurations.

    Provides methods for parsing, serializing, and validating
    routing configurations from various formats.

    Example:
        # Parse from YAML string
        config = ConfigParser.parse_yaml(yaml_content)

        # Parse from JSON string
        config = ConfigParser.parse_json(json_content)

        # Parse from file (auto-detect format)
        config = ConfigParser.parse_file(Path("routes.yaml"))

        # Export to YAML
        yaml_str = ConfigParser.to_yaml(config)

        # Validate configuration
        errors = ConfigParser.validate(config)
    """

    @classmethod
    def parse_yaml(cls, yaml_content: str) -> RoutingConfig:
        """Parse routing configuration from YAML string.

        Args:
            yaml_content: YAML configuration string.

        Returns:
            Parsed RoutingConfig.

        Raises:
            ImportError: If PyYAML is not installed.
            ValueError: If YAML is invalid.
        """
        try:
            import yaml
        except ImportError as err:
            raise ImportError(
                "PyYAML is required for YAML config parsing. "
                "Install with: pip install pyyaml"
            ) from err

        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {e}") from e

        if not isinstance(data, dict):
            raise ValueError("YAML content must be a mapping")

        return RoutingConfig.from_dict(data)

    @classmethod
    def parse_json(cls, json_content: str) -> RoutingConfig:
        """Parse routing configuration from JSON string.

        Args:
            json_content: JSON configuration string.

        Returns:
            Parsed RoutingConfig.

        Raises:
            ValueError: If JSON is invalid.
        """
        try:
            data = json.loads(json_content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}") from e

        if not isinstance(data, dict):
            raise ValueError("JSON content must be an object")

        return RoutingConfig.from_dict(data)

    @classmethod
    def parse_file(cls, file_path: Path | str) -> RoutingConfig:
        """Parse routing configuration from file.

        Automatically detects format based on file extension.

        Args:
            file_path: Path to configuration file (.yaml, .yml, or .json).

        Returns:
            Parsed RoutingConfig.

        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If file format is unsupported.
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        content = path.read_text(encoding="utf-8")

        if path.suffix in (".yaml", ".yml"):
            return cls.parse_yaml(content)
        elif path.suffix == ".json":
            return cls.parse_json(content)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")

    @classmethod
    def to_yaml(cls, config: RoutingConfig) -> str:
        """Export routing configuration to YAML string.

        Args:
            config: RoutingConfig to export.

        Returns:
            YAML configuration string.

        Raises:
            ImportError: If PyYAML is not installed.
        """
        try:
            import yaml
        except ImportError as err:
            raise ImportError(
                "PyYAML is required for YAML config export. "
                "Install with: pip install pyyaml"
            ) from err

        data = config.to_dict()
        return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)

    @classmethod
    def to_json(cls, config: RoutingConfig, indent: int = 2) -> str:
        """Export routing configuration to JSON string.

        Args:
            config: RoutingConfig to export.
            indent: JSON indentation level.

        Returns:
            JSON configuration string.
        """
        data = config.to_dict()
        return json.dumps(data, indent=indent, ensure_ascii=False)

    @classmethod
    def validate(
        cls,
        config: RoutingConfig,
        max_depth: int = 10,
        max_rules_per_combinator: int = 50,
        check_circular_refs: bool = True,
    ) -> list[str]:
        """Validate routing configuration.

        Checks:
        - Route names are unique
        - Rule types exist in RuleRegistry
        - Required fields are present
        - Actions are not empty
        - Circular references in rules
        - Maximum nesting depth
        - Maximum rules per combinator
        - Reserved field names

        Args:
            config: RoutingConfig to validate.
            max_depth: Maximum nesting depth for rules (default: 10).
            max_rules_per_combinator: Maximum rules per combinator (default: 50).
            check_circular_refs: Whether to check for circular references (default: True).

        Returns:
            List of validation error messages (empty if valid).
        """
        from .rules import RuleRegistry
        from .validator import RuleValidationConfig, RuleValidator

        errors: list[str] = []

        # Check version
        if not config.version:
            errors.append("Missing 'version' field")

        # Check for duplicate route names
        route_names: set[str] = set()
        for i, route in enumerate(config.routes):
            if route.name in route_names:
                errors.append(f"Route {i}: Duplicate route name '{route.name}'")
            route_names.add(route.name)

            # Validate each route structure
            route_errors = cls._validate_route(route, i, RuleRegistry)
            errors.extend(route_errors)

            # Use RuleValidator for comprehensive validation of each rule
            if route.rules:
                validation_config = RuleValidationConfig(
                    max_depth=max_depth,
                    max_rules_per_combinator=max_rules_per_combinator,
                    check_circular_refs=check_circular_refs,
                )
                validator = RuleValidator(validation_config)

                for j, rule_data in enumerate(route.rules):
                    result = validator.validate(rule_data)
                    if not result.valid:
                        for error in result.errors:
                            path_prefix = f"Route {i} ('{route.name}')/rules[{j}]"
                            if error.path:
                                errors.append(f"{path_prefix}/{error.path}: {error.message}")
                            else:
                                errors.append(f"{path_prefix}: {error.message}")

        return errors

    @classmethod
    def _validate_route(cls, route: RouteConfig, index: int, registry: type) -> list[str]:
        """Validate a single route configuration.

        Args:
            route: RouteConfig to validate.
            index: Route index for error messages.
            registry: RuleRegistry class for rule type validation.

        Returns:
            List of validation errors.
        """
        errors: list[str] = []
        prefix = f"Route {index} ('{route.name}')"

        # Check required fields
        if not route.name:
            errors.append(f"{prefix}: Missing required field 'name'")

        if not route.rules:
            errors.append(f"{prefix}: Missing required field 'rules'")
        else:
            # Validate each rule in the rules list
            for rule_idx, rule_data in enumerate(route.rules):
                rule_errors = cls._validate_rule(rule_data, f"{prefix}/rules[{rule_idx}]", registry)
                errors.extend(rule_errors)

        if not route.actions:
            errors.append(f"{prefix}: Missing required field 'actions'")
        elif not isinstance(route.actions, list):
            errors.append(f"{prefix}: 'actions' must be a list")

        return errors

    @classmethod
    def _validate_rule(cls, data: dict[str, Any], prefix: str, registry: type) -> list[str]:
        """Validate a rule configuration recursively.

        Handles nested rules for combinators (all_of, any_of, not).

        Args:
            data: Rule configuration dictionary.
            prefix: Error message prefix.
            registry: RuleRegistry class.

        Returns:
            List of validation errors.
        """
        errors: list[str] = []

        if not isinstance(data, dict):
            errors.append(f"{prefix}: Rule must be an object")
            return errors

        rule_type = data.get("type")
        if not rule_type:
            errors.append(f"{prefix}: Rule missing required field 'type'")
            return errors

        # Check if rule type exists in registry
        registered_types = registry.list_types()
        if rule_type not in registered_types:
            errors.append(f"{prefix}: Unknown rule type '{rule_type}'. Available: {registered_types}")
            return errors

        # Validate params if present
        params = data.get("params", {})
        if params and not isinstance(params, dict):
            errors.append(f"{prefix}: 'params' must be an object")

        # Validate nested rules for combinators
        if rule_type in ("all_of", "any_of"):
            nested_rules = data.get("rules", params.get("rules", []))
            if not isinstance(nested_rules, list):
                errors.append(f"{prefix}: '{rule_type}' requires 'rules' to be a list")
            else:
                for i, nested_data in enumerate(nested_rules):
                    nested_errors = cls._validate_rule(nested_data, f"{prefix}/{rule_type}[{i}]", registry)
                    errors.extend(nested_errors)

        elif rule_type == "not":
            nested_rule = data.get("rule", params.get("rule"))
            if not nested_rule:
                errors.append(f"{prefix}: 'not' rule requires nested 'rule' field")
            elif isinstance(nested_rule, dict):
                nested_errors = cls._validate_rule(nested_rule, f"{prefix}/not", registry)
                errors.extend(nested_errors)

        return errors

    @classmethod
    def to_action_router(cls, config: RoutingConfig) -> "ActionRouter":
        """Convert RoutingConfig to ActionRouter.

        Converts the parsed configuration into an ActionRouter
        instance ready for event matching.

        Args:
            config: RoutingConfig to convert.

        Returns:
            Configured ActionRouter.
        """
        from .combinators import AllOf, AnyOf, NotRule
        from .engine import ActionRouter, Route
        from .rules import BaseRule, RuleRegistry

        routes: list[Route] = []

        for route_config in config.routes:
            # Build the rule from rules list
            rule = cls._build_rule_from_list(route_config.rules)
            if rule is None:
                continue

            route = Route(
                name=route_config.name,
                rule=rule,
                actions=route_config.actions,
                priority=route_config.priority,
                is_active=True,
                stop_on_match=route_config.stop_on_match,
                metadata=route_config.metadata,
            )
            routes.append(route)

        return ActionRouter(routes=routes)

    @classmethod
    def _build_rule_from_list(cls, rules_list: list[dict[str, Any]]) -> "BaseRule | None":
        """Build a rule from a list of rule configurations.

        If multiple rules, wraps them in AllOf combinator.

        Args:
            rules_list: List of rule configurations.

        Returns:
            BaseRule instance or None if empty/invalid.
        """
        from .combinators import AllOf

        if not rules_list:
            return None

        if len(rules_list) == 1:
            return cls._build_rule(rules_list[0])

        # Multiple rules -> combine with AllOf
        rules = []
        for rule_data in rules_list:
            rule = cls._build_rule(rule_data)
            if rule:
                rules.append(rule)

        if not rules:
            return None

        return AllOf(rules=rules)

    @classmethod
    def _build_rule(cls, data: dict[str, Any]) -> "BaseRule | None":
        """Build a single rule from configuration.

        Handles nested rules for combinators.

        Args:
            data: Rule configuration dictionary.

        Returns:
            BaseRule instance or None if invalid.
        """
        from .combinators import AllOf, AnyOf, NotRule
        from .rules import BaseRule, RuleRegistry

        rule_type = data.get("type")
        if not rule_type:
            return None

        # Get params (support both top-level and nested params)
        params = data.get("params", {})

        # Handle combinator rules with nested rules
        if rule_type == "all_of":
            nested_rules_data = data.get("rules", params.get("rules", []))
            nested_rules = []
            for nested_data in nested_rules_data:
                nested_rule = cls._build_rule(nested_data)
                if nested_rule:
                    nested_rules.append(nested_rule)
            return AllOf(rules=nested_rules)

        elif rule_type == "any_of":
            nested_rules_data = data.get("rules", params.get("rules", []))
            nested_rules = []
            for nested_data in nested_rules_data:
                nested_rule = cls._build_rule(nested_data)
                if nested_rule:
                    nested_rules.append(nested_rule)
            return AnyOf(rules=nested_rules)

        elif rule_type == "not":
            nested_data = data.get("rule", params.get("rule"))
            if nested_data:
                nested_rule = cls._build_rule(nested_data)
                if nested_rule:
                    return NotRule(rule=nested_rule)
            return None

        # Simple rules - merge top-level params with nested params
        # Support both formats:
        # 1. { type: "severity", min_severity: "critical" }
        # 2. { type: "severity", params: { min_severity: "critical" } }
        merged_params = {k: v for k, v in data.items() if k not in ("type", "params")}
        merged_params.update(params)

        return RuleRegistry.create(rule_type, **merged_params)


class ConfigBuilder:
    """Builder for programmatically creating routing configurations.

    Provides a fluent interface for constructing RoutingConfig
    instances without manual dictionary manipulation.

    Example:
        config = (
            ConfigBuilder()
            .with_version("1.0")
            .with_defaults(priority=0, stop_on_match=False)
            .add_route(
                name="critical_alerts",
                rules=[
                    {"type": "severity", "params": {"min_severity": "critical"}}
                ],
                actions=["pagerduty"],
                priority=100,
            )
            .add_route(
                name="production_errors",
                rules=[
                    {
                        "type": "all_of",
                        "rules": [
                            {"type": "tag", "params": {"tags": ["production"]}},
                            {"type": "status", "params": {"statuses": ["error"]}},
                        ],
                    }
                ],
                actions=["slack-alerts"],
                priority=50,
            )
            .build()
        )
    """

    def __init__(self) -> None:
        """Initialize the builder."""
        self._version: str = "1.0"
        self._defaults: dict[str, Any] = {}
        self._routes: list[RouteConfig] = []

    def with_version(self, version: str) -> Self:
        """Set the configuration version.

        Args:
            version: Version string.

        Returns:
            Self for method chaining.
        """
        self._version = version
        return self

    def with_defaults(self, **kwargs: Any) -> Self:
        """Set default values for routes.

        Supported defaults:
        - priority: Default route priority
        - stop_on_match: Default stop_on_match behavior
        - metadata: Default metadata to apply

        Args:
            **kwargs: Default values.

        Returns:
            Self for method chaining.
        """
        self._defaults.update(kwargs)
        return self

    def add_route(
        self,
        name: str,
        rules: list[dict[str, Any]],
        actions: list[str],
        priority: int | None = None,
        stop_on_match: bool | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Self:
        """Add a route to the configuration.

        Args:
            name: Unique route name.
            rules: List of rule configurations.
            actions: List of action/channel identifiers.
            priority: Route priority (uses default if None).
            stop_on_match: Stop on match behavior (uses default if None).
            metadata: Route metadata (uses default if None).

        Returns:
            Self for method chaining.
        """
        route = RouteConfig(
            name=name,
            rules=rules,
            actions=actions,
            priority=priority if priority is not None else self._defaults.get("priority", 0),
            stop_on_match=(
                stop_on_match if stop_on_match is not None else self._defaults.get("stop_on_match", False)
            ),
            metadata=metadata if metadata is not None else dict(self._defaults.get("metadata", {})),
        )
        self._routes.append(route)
        return self

    def add_simple_route(
        self,
        name: str,
        rule_type: str,
        rule_params: dict[str, Any],
        actions: list[str],
        priority: int | None = None,
        stop_on_match: bool | None = None,
    ) -> Self:
        """Add a simple route with a single rule.

        Convenience method for routes with a single rule.

        Args:
            name: Unique route name.
            rule_type: Rule type (e.g., "severity", "tag").
            rule_params: Rule parameters.
            actions: List of action/channel identifiers.
            priority: Route priority.
            stop_on_match: Stop on match behavior.

        Returns:
            Self for method chaining.
        """
        rules = [{"type": rule_type, "params": rule_params}]
        return self.add_route(
            name=name,
            rules=rules,
            actions=actions,
            priority=priority,
            stop_on_match=stop_on_match,
        )

    def add_combined_route(
        self,
        name: str,
        combinator: str,
        rule_configs: list[tuple[str, dict[str, Any]]],
        actions: list[str],
        priority: int | None = None,
        stop_on_match: bool | None = None,
    ) -> Self:
        """Add a route with combined rules.

        Convenience method for routes with multiple rules combined
        by a combinator (all_of, any_of).

        Args:
            name: Unique route name.
            combinator: Combinator type ("all_of" or "any_of").
            rule_configs: List of (rule_type, params) tuples.
            actions: List of action/channel identifiers.
            priority: Route priority.
            stop_on_match: Stop on match behavior.

        Returns:
            Self for method chaining.
        """
        nested_rules = [{"type": rtype, "params": params} for rtype, params in rule_configs]
        rules = [{"type": combinator, "rules": nested_rules}]
        return self.add_route(
            name=name,
            rules=rules,
            actions=actions,
            priority=priority,
            stop_on_match=stop_on_match,
        )

    def clear_routes(self) -> Self:
        """Clear all routes from the builder.

        Returns:
            Self for method chaining.
        """
        self._routes.clear()
        return self

    def remove_route(self, name: str) -> Self:
        """Remove a route by name.

        Args:
            name: Route name to remove.

        Returns:
            Self for method chaining.
        """
        self._routes = [r for r in self._routes if r.name != name]
        return self

    def build(self) -> RoutingConfig:
        """Build the RoutingConfig.

        Returns:
            Configured RoutingConfig instance.
        """
        return RoutingConfig(
            version=self._version,
            routes=list(self._routes),
            defaults=dict(self._defaults),
        )

    def build_router(self) -> "ActionRouter":
        """Build and convert to ActionRouter.

        Convenience method that builds the config and
        converts it to an ActionRouter in one step.

        Returns:
            Configured ActionRouter instance.
        """
        config = self.build()
        return ConfigParser.to_action_router(config)


# Convenience function for quick parsing
def parse_routing_config(source: str | Path | dict[str, Any]) -> RoutingConfig:
    """Parse routing configuration from various sources.

    Args:
        source: Configuration source - can be:
            - Path to a file
            - YAML or JSON string
            - Dictionary

    Returns:
        Parsed RoutingConfig.

    Raises:
        ValueError: If source format cannot be determined.
    """
    if isinstance(source, Path):
        return ConfigParser.parse_file(source)
    elif isinstance(source, str):
        # Check if it's a file path
        path = Path(source)
        if path.exists():
            return ConfigParser.parse_file(path)

        # Try parsing as YAML/JSON
        source = source.strip()
        if source.startswith("{"):
            return ConfigParser.parse_json(source)
        else:
            return ConfigParser.parse_yaml(source)
    elif isinstance(source, dict):
        return RoutingConfig.from_dict(source)
    else:
        raise ValueError(f"Unsupported source type: {type(source)}")
