"""Rule configuration validator with circular reference detection.

This module provides comprehensive validation for routing rule configurations,
including:
- Circular reference detection (direct and indirect)
- Maximum nesting depth limits
- Maximum rules per combinator limits
- Reserved field name validation
- Rule type validation against RuleRegistry

Example:
    from truthound_dashboard.core.notifications.routing.validator import (
        RuleValidator,
        RuleValidationConfig,
        RuleValidationError,
    )

    validator = RuleValidator()
    result = validator.validate(rule_config)

    if not result.valid:
        for error in result.errors:
            print(f"Error: {error.message} at {error.path}")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ValidationErrorType(str, Enum):
    """Types of validation errors."""

    UNKNOWN_RULE_TYPE = "unknown_rule_type"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    INVALID_FIELD_VALUE = "invalid_field_value"
    CIRCULAR_REFERENCE = "circular_reference"
    MAX_DEPTH_EXCEEDED = "max_depth_exceeded"
    MAX_RULES_EXCEEDED = "max_rules_exceeded"
    RESERVED_FIELD_NAME = "reserved_field_name"
    EMPTY_COMBINATOR = "empty_combinator"
    INVALID_STRUCTURE = "invalid_structure"


@dataclass
class ValidationError:
    """A single validation error with context.

    Attributes:
        type: The type of validation error.
        message: Human-readable error message.
        path: JSON path to the error location (e.g., "rules[0].rules[1]").
        context: Additional context about the error.
    """

    type: ValidationErrorType
    message: str
    path: str = ""
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "type": self.type.value,
            "message": self.message,
            "path": self.path,
            "context": self.context,
        }


@dataclass
class ValidationWarning:
    """A single validation warning.

    Attributes:
        message: Human-readable warning message.
        path: JSON path to the warning location.
    """

    message: str
    path: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "message": self.message,
            "path": self.path,
        }


@dataclass
class RuleValidationConfig:
    """Configuration for rule validation.

    Attributes:
        max_depth: Maximum allowed nesting depth (default: 10).
        max_rules_per_combinator: Maximum rules in a single combinator (default: 50).
        max_total_rules: Maximum total rules in the configuration (default: 500).
        reserved_field_names: Set of reserved field names that cannot be used.
        check_circular_refs: Whether to check for circular references (default: True).
        strict_mode: If True, warnings are treated as errors (default: False).
    """

    max_depth: int = 10
    max_rules_per_combinator: int = 50
    max_total_rules: int = 500
    reserved_field_names: set[str] = field(
        default_factory=lambda: {
            "__proto__",
            "constructor",
            "prototype",
            "__class__",
            "__bases__",
            "__mro__",
            "__subclasses__",
            "__init__",
            "__new__",
            "__del__",
            "__call__",
            "__getattr__",
            "__setattr__",
            "__delattr__",
            "__dict__",
            "__slots__",
            "__module__",
            "__name__",
            "__qualname__",
            "__globals__",
            "__code__",
            "__builtins__",
            "__import__",
            "eval",
            "exec",
            "compile",
        }
    )
    check_circular_refs: bool = True
    strict_mode: bool = False


@dataclass
class RuleValidationResult:
    """Result of rule configuration validation.

    Attributes:
        valid: Whether the configuration is valid.
        errors: List of validation errors.
        warnings: List of validation warnings.
        rule_count: Total number of rules (including nested).
        max_depth: Maximum nesting depth found.
        circular_paths: Paths of detected circular references.
    """

    valid: bool = True
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationWarning] = field(default_factory=list)
    rule_count: int = 0
    max_depth: int = 0
    circular_paths: list[str] = field(default_factory=list)

    def add_error(
        self,
        error_type: ValidationErrorType,
        message: str,
        path: str = "",
        context: dict[str, Any] | None = None,
    ) -> None:
        """Add a validation error."""
        self.valid = False
        self.errors.append(
            ValidationError(
                type=error_type,
                message=message,
                path=path,
                context=context or {},
            )
        )

    def add_warning(self, message: str, path: str = "") -> None:
        """Add a validation warning."""
        self.warnings.append(ValidationWarning(message=message, path=path))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "valid": self.valid,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "rule_count": self.rule_count,
            "max_depth": self.max_depth,
            "circular_paths": self.circular_paths,
        }

    def error_messages(self) -> list[str]:
        """Get list of error messages for backward compatibility."""
        return [e.message for e in self.errors]

    def warning_messages(self) -> list[str]:
        """Get list of warning messages for backward compatibility."""
        return [w.message for w in self.warnings]


class RuleValidationError(Exception):
    """Exception raised for critical validation failures.

    Attributes:
        result: The validation result with error details.
    """

    def __init__(self, message: str, result: RuleValidationResult):
        super().__init__(message)
        self.result = result


class RuleValidator:
    """Comprehensive validator for routing rule configurations.

    Provides validation including:
    - Rule type existence (via RuleRegistry)
    - Required parameter validation
    - Circular reference detection (direct and indirect)
    - Maximum nesting depth enforcement
    - Maximum rules per combinator enforcement
    - Reserved field name checking

    Example:
        validator = RuleValidator()
        result = validator.validate({
            "type": "all_of",
            "rules": [
                {"type": "severity", "params": {"min_severity": "critical"}},
                {"type": "tag", "params": {"tags": ["production"]}},
            ]
        })

        if result.valid:
            print("Configuration is valid")
        else:
            for error in result.errors:
                print(f"Error: {error.message}")
    """

    # Combinator types that can contain nested rules
    COMBINATOR_TYPES = {"all_of", "any_of", "not"}

    def __init__(self, config: RuleValidationConfig | None = None):
        """Initialize the validator.

        Args:
            config: Validation configuration. Uses defaults if not provided.
        """
        self.config = config or RuleValidationConfig()

    def validate(
        self,
        rule_config: dict[str, Any],
        config_override: RuleValidationConfig | None = None,
    ) -> RuleValidationResult:
        """Validate a rule configuration.

        Args:
            rule_config: The rule configuration dictionary to validate.
            config_override: Optional configuration override for this validation.

        Returns:
            RuleValidationResult with validation details.
        """
        config = config_override or self.config
        result = RuleValidationResult()

        # Track visited nodes for circular reference detection
        # Using a path-based approach for accurate cycle detection
        visited_paths: set[str] = set()

        # Perform recursive validation
        self._validate_rule_recursive(
            rule_config=rule_config,
            result=result,
            config=config,
            depth=0,
            path="",
            visited_paths=visited_paths,
            parent_chain=[],
        )

        # Apply strict mode if configured
        if config.strict_mode and result.warnings:
            for warning in result.warnings:
                result.add_error(
                    ValidationErrorType.INVALID_FIELD_VALUE,
                    f"Strict mode: {warning.message}",
                    warning.path,
                )

        return result

    def _validate_rule_recursive(
        self,
        rule_config: dict[str, Any],
        result: RuleValidationResult,
        config: RuleValidationConfig,
        depth: int,
        path: str,
        visited_paths: set[str],
        parent_chain: list[str],
    ) -> None:
        """Recursively validate a rule configuration.

        Uses DFS with visited set for efficient cycle detection.

        Args:
            rule_config: The rule configuration to validate.
            result: Validation result to update.
            config: Validation configuration.
            depth: Current nesting depth.
            path: Current JSON path for error reporting.
            visited_paths: Set of visited paths for cycle detection.
            parent_chain: Chain of parent rule IDs for cycle path reporting.
        """
        from .rules import RuleRegistry

        result.rule_count += 1
        result.max_depth = max(result.max_depth, depth)

        # Check total rules limit
        if result.rule_count > config.max_total_rules:
            result.add_error(
                ValidationErrorType.MAX_RULES_EXCEEDED,
                f"Total rule count ({result.rule_count}) exceeds maximum ({config.max_total_rules})",
                path,
                {"max_total_rules": config.max_total_rules, "current_count": result.rule_count},
            )
            return

        # Validate structure
        if not isinstance(rule_config, dict):
            result.add_error(
                ValidationErrorType.INVALID_STRUCTURE,
                "Rule configuration must be a dictionary/object",
                path,
            )
            return

        # Get rule type
        rule_type = rule_config.get("type")
        if not rule_type:
            result.add_error(
                ValidationErrorType.MISSING_REQUIRED_FIELD,
                "Rule missing required field 'type'",
                path,
            )
            return

        # Validate rule type string
        if not isinstance(rule_type, str):
            result.add_error(
                ValidationErrorType.INVALID_FIELD_VALUE,
                f"Rule 'type' must be a string, got {type(rule_type).__name__}",
                path,
            )
            return

        # Check for reserved field names in params
        params = rule_config.get("params", {})
        if isinstance(params, dict):
            self._check_reserved_fields(params, result, config, f"{path}.params")

        # Check nesting depth
        if depth > config.max_depth:
            result.add_error(
                ValidationErrorType.MAX_DEPTH_EXCEEDED,
                f"Maximum nesting depth ({config.max_depth}) exceeded at depth {depth}",
                path,
                {"max_depth": config.max_depth, "current_depth": depth},
            )
            return

        # Create a unique identifier for this rule node
        rule_id = self._generate_rule_id(rule_config, path)

        # Circular reference detection using path-based tracking
        if config.check_circular_refs:
            if rule_id in visited_paths:
                # Found a circular reference
                cycle_path = self._format_cycle_path(parent_chain, rule_id)
                result.add_error(
                    ValidationErrorType.CIRCULAR_REFERENCE,
                    f"Circular reference detected: {cycle_path}",
                    path,
                    {"cycle_path": cycle_path, "rule_id": rule_id},
                )
                result.circular_paths.append(cycle_path)
                return

        # Mark as visited
        visited_paths.add(rule_id)
        current_chain = parent_chain + [rule_id]

        try:
            # Validate based on rule type
            if rule_type in self.COMBINATOR_TYPES:
                self._validate_combinator(
                    rule_config=rule_config,
                    rule_type=rule_type,
                    result=result,
                    config=config,
                    depth=depth,
                    path=path,
                    visited_paths=visited_paths,
                    parent_chain=current_chain,
                )
            else:
                self._validate_simple_rule(
                    rule_config=rule_config,
                    rule_type=rule_type,
                    result=result,
                    path=path,
                )
        finally:
            # Unmark as visited (for DFS backtracking)
            # This allows the same rule pattern to appear in different branches
            visited_paths.discard(rule_id)

    def _validate_combinator(
        self,
        rule_config: dict[str, Any],
        rule_type: str,
        result: RuleValidationResult,
        config: RuleValidationConfig,
        depth: int,
        path: str,
        visited_paths: set[str],
        parent_chain: list[str],
    ) -> None:
        """Validate a combinator rule (all_of, any_of, not).

        Args:
            rule_config: The combinator rule configuration.
            rule_type: The combinator type.
            result: Validation result to update.
            config: Validation configuration.
            depth: Current nesting depth.
            path: Current JSON path.
            visited_paths: Set of visited paths.
            parent_chain: Chain of parent rule IDs.
        """
        if rule_type == "not":
            # NOT combinator requires a single 'rule' field
            nested_rule = rule_config.get("rule") or rule_config.get("params", {}).get("rule")

            if not nested_rule:
                result.add_error(
                    ValidationErrorType.EMPTY_COMBINATOR,
                    "'not' combinator requires a 'rule' field",
                    path,
                )
                return

            if not isinstance(nested_rule, dict):
                result.add_error(
                    ValidationErrorType.INVALID_STRUCTURE,
                    "'not' combinator 'rule' must be an object",
                    path,
                )
                return

            # Recursively validate the nested rule
            self._validate_rule_recursive(
                rule_config=nested_rule,
                result=result,
                config=config,
                depth=depth + 1,
                path=f"{path}.rule" if path else "rule",
                visited_paths=visited_paths,
                parent_chain=parent_chain,
            )

        else:
            # ALL_OF or ANY_OF combinator requires a 'rules' array
            nested_rules = rule_config.get("rules") or rule_config.get("params", {}).get("rules", [])

            if not nested_rules:
                result.add_error(
                    ValidationErrorType.EMPTY_COMBINATOR,
                    f"'{rule_type}' combinator requires a non-empty 'rules' array",
                    path,
                )
                return

            if not isinstance(nested_rules, list):
                result.add_error(
                    ValidationErrorType.INVALID_STRUCTURE,
                    f"'{rule_type}' combinator 'rules' must be an array",
                    path,
                )
                return

            # Check max rules per combinator
            if len(nested_rules) > config.max_rules_per_combinator:
                result.add_error(
                    ValidationErrorType.MAX_RULES_EXCEEDED,
                    f"Combinator has {len(nested_rules)} rules, exceeds maximum of {config.max_rules_per_combinator}",
                    path,
                    {
                        "max_rules_per_combinator": config.max_rules_per_combinator,
                        "current_count": len(nested_rules),
                    },
                )
                return

            # Warn about single-rule combinators
            if len(nested_rules) == 1:
                result.add_warning(
                    f"'{rule_type}' combinator with only 1 rule is redundant",
                    path,
                )

            # Recursively validate each nested rule
            for idx, nested_rule in enumerate(nested_rules):
                nested_path = f"{path}.rules[{idx}]" if path else f"rules[{idx}]"
                self._validate_rule_recursive(
                    rule_config=nested_rule,
                    result=result,
                    config=config,
                    depth=depth + 1,
                    path=nested_path,
                    visited_paths=visited_paths,
                    parent_chain=parent_chain,
                )

    def _validate_simple_rule(
        self,
        rule_config: dict[str, Any],
        rule_type: str,
        result: RuleValidationResult,
        path: str,
    ) -> None:
        """Validate a simple (non-combinator) rule.

        Args:
            rule_config: The rule configuration.
            rule_type: The rule type.
            result: Validation result to update.
            path: Current JSON path.
        """
        from .rules import RuleRegistry

        # Check if rule type is registered
        rule_class = RuleRegistry.get(rule_type)
        if rule_class is None:
            available_types = RuleRegistry.list_types()
            result.add_error(
                ValidationErrorType.UNKNOWN_RULE_TYPE,
                f"Unknown rule type '{rule_type}'. Available types: {available_types}",
                path,
                {"rule_type": rule_type, "available_types": available_types},
            )
            return

        # Get params (support both top-level and nested params format)
        params = {}
        nested_params = rule_config.get("params", {})
        if isinstance(nested_params, dict):
            params.update(nested_params)

        # Also support top-level params (e.g., {"type": "severity", "min_severity": "critical"})
        for key, value in rule_config.items():
            if key not in ("type", "params", "rules", "rule"):
                params[key] = value

        # Validate required parameters
        param_schema = rule_class.get_param_schema()
        for param_name, param_spec in param_schema.items():
            if param_spec.get("required", False) and param_name not in params:
                result.add_error(
                    ValidationErrorType.MISSING_REQUIRED_FIELD,
                    f"Missing required parameter '{param_name}' for rule type '{rule_type}'",
                    f"{path}.params.{param_name}" if path else f"params.{param_name}",
                    {"rule_type": rule_type, "parameter": param_name},
                )

    def _check_reserved_fields(
        self,
        data: dict[str, Any],
        result: RuleValidationResult,
        config: RuleValidationConfig,
        path: str,
    ) -> None:
        """Check for reserved field names in data.

        Args:
            data: Dictionary to check.
            result: Validation result to update.
            config: Validation configuration.
            path: Current JSON path.
        """
        for key in data.keys():
            if key.lower() in {rf.lower() for rf in config.reserved_field_names}:
                result.add_error(
                    ValidationErrorType.RESERVED_FIELD_NAME,
                    f"Reserved field name '{key}' cannot be used",
                    f"{path}.{key}" if path else key,
                    {"field_name": key},
                )

    def _generate_rule_id(self, rule_config: dict[str, Any], path: str) -> str:
        """Generate a unique identifier for a rule node.

        For circular reference detection, we create an ID based on
        the rule's structural properties.

        Args:
            rule_config: The rule configuration.
            path: The current path (used for position context).

        Returns:
            A unique identifier string for this rule.
        """
        rule_type = rule_config.get("type", "unknown")

        # For simple rules, include type and key params
        if rule_type not in self.COMBINATOR_TYPES:
            params = rule_config.get("params", {})
            # Create a deterministic string from key parameters
            param_str = str(sorted(params.items())) if params else ""
            return f"{rule_type}:{param_str}"

        # For combinators, use type and path to distinguish branches
        return f"{rule_type}@{path}"

    def _format_cycle_path(self, parent_chain: list[str], current_id: str) -> str:
        """Format a cycle path for error reporting.

        Args:
            parent_chain: List of parent rule IDs.
            current_id: The current rule ID that creates the cycle.

        Returns:
            Formatted cycle path string (e.g., "A -> B -> C -> A").
        """
        if current_id in parent_chain:
            # Find where the cycle starts
            cycle_start = parent_chain.index(current_id)
            cycle_nodes = parent_chain[cycle_start:] + [current_id]
            return " -> ".join(cycle_nodes)
        return f"... -> {current_id}"


# Convenience function for quick validation
def validate_rule_config(
    rule_config: dict[str, Any],
    max_depth: int = 10,
    max_rules_per_combinator: int = 50,
    check_circular_refs: bool = True,
) -> RuleValidationResult:
    """Validate a rule configuration with custom settings.

    This is a convenience function for one-off validations.
    For repeated validations, create a RuleValidator instance.

    Args:
        rule_config: The rule configuration to validate.
        max_depth: Maximum nesting depth allowed.
        max_rules_per_combinator: Maximum rules in a single combinator.
        check_circular_refs: Whether to check for circular references.

    Returns:
        RuleValidationResult with validation details.
    """
    config = RuleValidationConfig(
        max_depth=max_depth,
        max_rules_per_combinator=max_rules_per_combinator,
        check_circular_refs=check_circular_refs,
    )
    validator = RuleValidator(config)
    return validator.validate(rule_config)
