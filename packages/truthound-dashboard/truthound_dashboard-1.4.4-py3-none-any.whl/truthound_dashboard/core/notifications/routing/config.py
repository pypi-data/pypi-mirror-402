"""Configuration parser for routing rules.

This module provides YAML/JSON configuration parsing for
creating routes and rules from configuration files.

Example YAML config:
    routes:
      - name: critical_pagerduty
        rule:
          type: severity
          min_severity: critical
        actions:
          - pagerduty-channel
        priority: 100

      - name: production_alerts
        rule:
          type: all_of
          rules:
            - type: tag
              tags: ["production"]
            - type: severity
              min_severity: high
        actions:
          - slack-alerts
        priority: 50

      - name: default
        rule:
          type: always
        actions:
          - slack-general
        priority: 0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .engine import ActionRouter, Route
from .rules import BaseRule


class RouteConfigParser:
    """Parser for routing configuration files.

    Supports both YAML and JSON configuration formats.

    Example usage:
        # Parse from file
        router = RouteConfigParser.from_file("routes.yaml")

        # Parse from dict
        router = RouteConfigParser.from_dict(config)

        # Parse from YAML string
        router = RouteConfigParser.from_yaml(yaml_string)
    """

    @classmethod
    def from_file(cls, path: str | Path) -> ActionRouter:
        """Load routing configuration from file.

        Args:
            path: Path to configuration file (.yaml, .yml, or .json).

        Returns:
            Configured ActionRouter.

        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If file format is unsupported.
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        content = path.read_text()

        if path.suffix in (".yaml", ".yml"):
            return cls.from_yaml(content)
        elif path.suffix == ".json":
            return cls.from_json(content)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")

    @classmethod
    def from_yaml(cls, content: str) -> ActionRouter:
        """Parse routing configuration from YAML string.

        Args:
            content: YAML configuration string.

        Returns:
            Configured ActionRouter.
        """
        try:
            import yaml
        except ImportError:
            raise ImportError(
                "PyYAML is required for YAML config parsing. "
                "Install with: pip install pyyaml"
            )

        data = yaml.safe_load(content)
        return cls.from_dict(data)

    @classmethod
    def from_json(cls, content: str) -> ActionRouter:
        """Parse routing configuration from JSON string.

        Args:
            content: JSON configuration string.

        Returns:
            Configured ActionRouter.
        """
        import json

        data = json.loads(content)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ActionRouter:
        """Parse routing configuration from dictionary.

        Args:
            data: Configuration dictionary.

        Returns:
            Configured ActionRouter.
        """
        routes: list[Route] = []
        default_route: Route | None = None

        # Parse routes
        routes_data = data.get("routes", data.get("routing", {}).get("routes", []))
        for route_data in routes_data:
            route = cls._parse_route(route_data)
            if route:
                routes.append(route)

        # Parse default route
        default_data = data.get("default_route") or data.get("routing", {}).get("default_route")
        if default_data:
            default_route = cls._parse_route(default_data)

        return ActionRouter(routes=routes, default_route=default_route)

    @classmethod
    def _parse_route(cls, data: dict[str, Any]) -> Route | None:
        """Parse a single route from configuration.

        Args:
            data: Route configuration dictionary.

        Returns:
            Parsed Route or None if invalid.
        """
        rule_data = data.get("rule")
        if not rule_data:
            return None

        rule = cls._parse_rule(rule_data)
        if rule is None:
            return None

        return Route(
            name=data.get("name", "unnamed"),
            rule=rule,
            actions=data.get("actions", []),
            priority=data.get("priority", 0),
            is_active=data.get("is_active", True),
            escalation_policy_id=data.get("escalation_policy_id"),
            stop_on_match=data.get("stop_on_match", False),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def _parse_rule(cls, data: dict[str, Any]) -> BaseRule | None:
        """Parse a rule from configuration.

        Handles nested rules for combinators.

        Args:
            data: Rule configuration dictionary.

        Returns:
            Parsed rule or None if invalid.
        """
        rule_type = data.get("type")
        if not rule_type:
            return None

        # Handle combinator rules with nested rules
        if rule_type in ("all_of", "any_of"):
            nested_rules = []
            for nested_data in data.get("rules", []):
                nested_rule = cls._parse_rule(nested_data)
                if nested_rule:
                    nested_rules.append(nested_rule)

            from .combinators import AllOf, AnyOf

            if rule_type == "all_of":
                return AllOf(rules=nested_rules)
            else:
                return AnyOf(rules=nested_rules)

        elif rule_type == "not":
            nested_data = data.get("rule")
            if nested_data:
                nested_rule = cls._parse_rule(nested_data)
                if nested_rule:
                    from .combinators import NotRule

                    return NotRule(rule=nested_rule)
            return None

        # Use registry for simple rules
        return BaseRule.from_dict(data)

    @classmethod
    def to_yaml(cls, router: ActionRouter) -> str:
        """Export router configuration to YAML string.

        Args:
            router: ActionRouter to export.

        Returns:
            YAML configuration string.
        """
        try:
            import yaml
        except ImportError:
            raise ImportError(
                "PyYAML is required for YAML config export. "
                "Install with: pip install pyyaml"
            )

        data = cls.to_dict(router)
        return yaml.dump(data, default_flow_style=False, sort_keys=False)

    @classmethod
    def to_json(cls, router: ActionRouter, indent: int = 2) -> str:
        """Export router configuration to JSON string.

        Args:
            router: ActionRouter to export.
            indent: JSON indentation level.

        Returns:
            JSON configuration string.
        """
        import json

        data = cls.to_dict(router)
        return json.dumps(data, indent=indent)

    @classmethod
    def to_dict(cls, router: ActionRouter) -> dict[str, Any]:
        """Export router configuration to dictionary.

        Args:
            router: ActionRouter to export.

        Returns:
            Configuration dictionary.
        """
        return {
            "routes": [route.to_dict() for route in router.routes],
            "default_route": router.default_route.to_dict() if router.default_route else None,
        }

    @classmethod
    def validate(cls, data: dict[str, Any]) -> list[str]:
        """Validate routing configuration.

        Args:
            data: Configuration dictionary to validate.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors: list[str] = []

        routes_data = data.get("routes", [])
        if not isinstance(routes_data, list):
            errors.append("'routes' must be a list")
            return errors

        route_names = set()
        for i, route_data in enumerate(routes_data):
            route_errors = cls._validate_route(route_data, i)
            errors.extend(route_errors)

            # Check for duplicate names
            name = route_data.get("name")
            if name:
                if name in route_names:
                    errors.append(f"Route {i}: Duplicate route name '{name}'")
                route_names.add(name)

        return errors

    @classmethod
    def _validate_route(cls, data: dict[str, Any], index: int) -> list[str]:
        """Validate a single route configuration."""
        errors: list[str] = []
        prefix = f"Route {index}"

        if not isinstance(data, dict):
            errors.append(f"{prefix}: Must be an object")
            return errors

        # Required fields
        if "rule" not in data:
            errors.append(f"{prefix}: Missing required field 'rule'")

        if "actions" not in data:
            errors.append(f"{prefix}: Missing required field 'actions'")
        elif not isinstance(data["actions"], list):
            errors.append(f"{prefix}: 'actions' must be a list")
        elif not data["actions"]:
            errors.append(f"{prefix}: 'actions' must not be empty")

        # Validate rule
        rule_data = data.get("rule", {})
        rule_errors = cls._validate_rule(rule_data, prefix)
        errors.extend(rule_errors)

        return errors

    @classmethod
    def _validate_rule(cls, data: dict[str, Any], prefix: str) -> list[str]:
        """Validate a rule configuration."""
        from .rules import RuleRegistry

        errors: list[str] = []

        if not isinstance(data, dict):
            errors.append(f"{prefix}: Rule must be an object")
            return errors

        rule_type = data.get("type")
        if not rule_type:
            errors.append(f"{prefix}: Rule missing required field 'type'")
            return errors

        # Check if rule type exists
        if rule_type not in RuleRegistry.list_types():
            errors.append(f"{prefix}: Unknown rule type '{rule_type}'")
            return errors

        # Validate nested rules for combinators
        if rule_type in ("all_of", "any_of"):
            nested_rules = data.get("rules", [])
            if not isinstance(nested_rules, list):
                errors.append(f"{prefix}: '{rule_type}' rules must be a list")
            else:
                for i, nested_data in enumerate(nested_rules):
                    nested_errors = cls._validate_rule(nested_data, f"{prefix}/{rule_type}[{i}]")
                    errors.extend(nested_errors)

        elif rule_type == "not":
            nested_data = data.get("rule")
            if not nested_data:
                errors.append(f"{prefix}: 'not' rule missing nested 'rule'")
            else:
                nested_errors = cls._validate_rule(nested_data, f"{prefix}/not")
                errors.extend(nested_errors)

        return errors
