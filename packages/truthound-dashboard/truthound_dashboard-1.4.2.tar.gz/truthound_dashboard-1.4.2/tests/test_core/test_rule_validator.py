"""Tests for rule configuration validator with circular reference detection.

Tests cover:
- Basic rule validation
- Circular reference detection (direct and indirect)
- Maximum nesting depth limits
- Maximum rules per combinator limits
- Reserved field name validation
- Combinator validation (all_of, any_of, not)
"""

import pytest

from truthound_dashboard.core.notifications.routing.validator import (
    RuleValidationConfig,
    RuleValidator,
    ValidationErrorType,
    validate_rule_config,
)


class TestBasicValidation:
    """Test basic rule validation functionality."""

    def test_valid_simple_rule(self):
        """Test that a valid simple rule passes validation."""
        rule = {
            "type": "severity",
            "params": {"min_severity": "critical"},
        }
        result = validate_rule_config(rule)

        assert result.valid is True
        assert len(result.errors) == 0
        assert result.rule_count == 1
        assert result.max_depth == 0

    def test_valid_simple_rule_flat_params(self):
        """Test that a valid simple rule with flat params passes validation."""
        rule = {
            "type": "severity",
            "min_severity": "critical",
        }
        result = validate_rule_config(rule)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_unknown_rule_type(self):
        """Test that an unknown rule type fails validation."""
        rule = {
            "type": "nonexistent_rule_type",
        }
        result = validate_rule_config(rule)

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].type == ValidationErrorType.UNKNOWN_RULE_TYPE
        assert "nonexistent_rule_type" in result.errors[0].message

    def test_missing_type_field(self):
        """Test that a rule without type field fails validation."""
        rule = {
            "params": {"min_severity": "critical"},
        }
        result = validate_rule_config(rule)

        assert result.valid is False
        assert any(e.type == ValidationErrorType.MISSING_REQUIRED_FIELD for e in result.errors)

    def test_missing_required_parameter(self):
        """Test that missing required parameters are detected."""
        rule = {
            "type": "severity",
            # Missing required 'min_severity' param
        }
        result = validate_rule_config(rule)

        assert result.valid is False
        assert any(e.type == ValidationErrorType.MISSING_REQUIRED_FIELD for e in result.errors)
        assert any("min_severity" in e.message for e in result.errors)


class TestCombinatorValidation:
    """Test combinator rule validation."""

    def test_valid_all_of_combinator(self):
        """Test that a valid all_of combinator passes validation."""
        rule = {
            "type": "all_of",
            "rules": [
                {"type": "severity", "params": {"min_severity": "critical"}},
                {"type": "tag", "params": {"tags": ["production"]}},
            ],
        }
        result = validate_rule_config(rule)

        assert result.valid is True
        assert result.rule_count == 3  # all_of + 2 nested rules
        assert result.max_depth == 1

    def test_valid_any_of_combinator(self):
        """Test that a valid any_of combinator passes validation."""
        rule = {
            "type": "any_of",
            "rules": [
                {"type": "severity", "params": {"min_severity": "critical"}},
                {"type": "issue_count", "params": {"min_count": 10}},
            ],
        }
        result = validate_rule_config(rule)

        assert result.valid is True
        assert result.rule_count == 3

    def test_valid_not_combinator(self):
        """Test that a valid not combinator passes validation."""
        rule = {
            "type": "not",
            "rule": {"type": "severity", "params": {"min_severity": "low"}},
        }
        result = validate_rule_config(rule)

        assert result.valid is True
        assert result.rule_count == 2

    def test_empty_all_of_combinator(self):
        """Test that an empty all_of combinator fails validation."""
        rule = {
            "type": "all_of",
            "rules": [],
        }
        result = validate_rule_config(rule)

        assert result.valid is False
        assert any(e.type == ValidationErrorType.EMPTY_COMBINATOR for e in result.errors)

    def test_empty_any_of_combinator(self):
        """Test that an empty any_of combinator fails validation."""
        rule = {
            "type": "any_of",
            "rules": [],
        }
        result = validate_rule_config(rule)

        assert result.valid is False
        assert any(e.type == ValidationErrorType.EMPTY_COMBINATOR for e in result.errors)

    def test_not_combinator_without_rule(self):
        """Test that a not combinator without rule fails validation."""
        rule = {
            "type": "not",
        }
        result = validate_rule_config(rule)

        assert result.valid is False
        assert any(e.type == ValidationErrorType.EMPTY_COMBINATOR for e in result.errors)

    def test_single_rule_combinator_warning(self):
        """Test that a combinator with single rule produces warning."""
        rule = {
            "type": "all_of",
            "rules": [
                {"type": "severity", "params": {"min_severity": "critical"}},
            ],
        }
        result = validate_rule_config(rule)

        assert result.valid is True  # Still valid, just a warning
        assert len(result.warnings) == 1
        assert "redundant" in result.warnings[0].message.lower()


class TestNestedValidation:
    """Test nested rule validation."""

    def test_deeply_nested_rules(self):
        """Test that deeply nested rules are properly counted."""
        rule = {
            "type": "all_of",
            "rules": [
                {
                    "type": "any_of",
                    "rules": [
                        {
                            "type": "all_of",
                            "rules": [
                                {"type": "severity", "params": {"min_severity": "critical"}},
                                {"type": "tag", "params": {"tags": ["prod"]}},
                            ],
                        },
                    ],
                },
            ],
        }
        result = validate_rule_config(rule)

        assert result.valid is True
        assert result.rule_count == 5
        assert result.max_depth == 3


class TestMaxDepthLimit:
    """Test maximum nesting depth limits."""

    def test_max_depth_exceeded(self):
        """Test that exceeding max depth fails validation."""
        # Create a rule with depth exceeding limit
        rule: dict = {"type": "severity", "params": {"min_severity": "critical"}}

        # Wrap in nested not combinators to exceed depth
        for _ in range(15):  # Default max is 10
            rule = {"type": "not", "rule": rule}

        result = validate_rule_config(rule, max_depth=10)

        assert result.valid is False
        assert any(e.type == ValidationErrorType.MAX_DEPTH_EXCEEDED for e in result.errors)

    def test_custom_max_depth(self):
        """Test that custom max depth is respected."""
        # Create 3-level nesting
        rule = {
            "type": "not",
            "rule": {
                "type": "not",
                "rule": {
                    "type": "not",
                    "rule": {"type": "always"},
                },
            },
        }

        # Should pass with default depth (10)
        result1 = validate_rule_config(rule, max_depth=10)
        assert result1.valid is True

        # Should fail with small max depth
        result2 = validate_rule_config(rule, max_depth=2)
        assert result2.valid is False
        assert any(e.type == ValidationErrorType.MAX_DEPTH_EXCEEDED for e in result2.errors)


class TestMaxRulesPerCombinator:
    """Test maximum rules per combinator limits."""

    def test_max_rules_per_combinator_exceeded(self):
        """Test that exceeding max rules per combinator fails validation."""
        # Create a combinator with many rules
        rules = [{"type": "always"} for _ in range(60)]
        rule = {"type": "all_of", "rules": rules}

        result = validate_rule_config(rule, max_rules_per_combinator=50)

        assert result.valid is False
        assert any(e.type == ValidationErrorType.MAX_RULES_EXCEEDED for e in result.errors)

    def test_within_max_rules_limit(self):
        """Test that staying within max rules limit passes validation."""
        rules = [{"type": "always"} for _ in range(10)]
        rule = {"type": "all_of", "rules": rules}

        result = validate_rule_config(rule, max_rules_per_combinator=50)

        assert result.valid is True


class TestCircularReferenceDetection:
    """Test circular reference detection."""

    def test_no_circular_reference(self):
        """Test that non-circular rules pass validation."""
        rule = {
            "type": "all_of",
            "rules": [
                {"type": "severity", "params": {"min_severity": "critical"}},
                {
                    "type": "any_of",
                    "rules": [
                        {"type": "tag", "params": {"tags": ["prod"]}},
                        {"type": "tag", "params": {"tags": ["staging"]}},
                    ],
                },
            ],
        }
        result = validate_rule_config(rule, check_circular_refs=True)

        assert result.valid is True
        assert len(result.circular_paths) == 0

    def test_same_rule_different_branches(self):
        """Test that same rule pattern in different branches is allowed."""
        # Same rule appears in different branches - this is OK
        rule = {
            "type": "any_of",
            "rules": [
                {
                    "type": "all_of",
                    "rules": [
                        {"type": "severity", "params": {"min_severity": "critical"}},
                        {"type": "tag", "params": {"tags": ["prod"]}},
                    ],
                },
                {
                    "type": "all_of",
                    "rules": [
                        {"type": "severity", "params": {"min_severity": "high"}},
                        {"type": "tag", "params": {"tags": ["staging"]}},
                    ],
                },
            ],
        }
        result = validate_rule_config(rule, check_circular_refs=True)

        assert result.valid is True

    def test_circular_reference_detection_can_be_disabled(self):
        """Test that circular reference detection can be disabled."""
        rule = {
            "type": "all_of",
            "rules": [
                {"type": "severity", "params": {"min_severity": "critical"}},
            ],
        }
        result = validate_rule_config(rule, check_circular_refs=False)

        assert result.valid is True


class TestReservedFieldNames:
    """Test reserved field name validation."""

    def test_reserved_field_in_params(self):
        """Test that reserved field names in params are detected."""
        rule = {
            "type": "metadata",
            "params": {
                "key": "test",
                "value": "test",
                "__proto__": "malicious",  # Reserved field
            },
        }
        result = validate_rule_config(rule)

        assert result.valid is False
        assert any(e.type == ValidationErrorType.RESERVED_FIELD_NAME for e in result.errors)

    def test_constructor_reserved_field(self):
        """Test that constructor field name is reserved."""
        rule = {
            "type": "metadata",
            "params": {
                "key": "test",
                "value": "test",
                "constructor": "Object",  # Reserved field
            },
        }
        result = validate_rule_config(rule)

        assert result.valid is False
        assert any(e.type == ValidationErrorType.RESERVED_FIELD_NAME for e in result.errors)


class TestValidatorConfiguration:
    """Test RuleValidator configuration."""

    def test_custom_config(self):
        """Test that custom configuration is respected."""
        config = RuleValidationConfig(
            max_depth=5,
            max_rules_per_combinator=10,
            check_circular_refs=False,
        )
        validator = RuleValidator(config)

        # Create rule that exceeds custom limits
        rules = [{"type": "always"} for _ in range(15)]
        rule = {"type": "all_of", "rules": rules}

        result = validator.validate(rule)

        assert result.valid is False
        assert any(e.type == ValidationErrorType.MAX_RULES_EXCEEDED for e in result.errors)

    def test_strict_mode(self):
        """Test that strict mode converts warnings to errors."""
        config = RuleValidationConfig(strict_mode=True)
        validator = RuleValidator(config)

        # Single-rule combinator produces warning
        rule = {
            "type": "all_of",
            "rules": [{"type": "always"}],
        }

        result = validator.validate(rule)

        # In strict mode, warning should become error
        assert result.valid is False

    def test_config_override(self):
        """Test that config override works."""
        default_config = RuleValidationConfig(max_depth=5)
        override_config = RuleValidationConfig(max_depth=20)
        validator = RuleValidator(default_config)

        # Create deep nesting
        rule: dict = {"type": "always"}
        for _ in range(10):
            rule = {"type": "not", "rule": rule}

        # Should fail with default config
        result1 = validator.validate(rule)
        assert result1.valid is False

        # Should pass with override config
        result2 = validator.validate(rule, config_override=override_config)
        assert result2.valid is True


class TestValidationResult:
    """Test validation result methods."""

    def test_error_messages(self):
        """Test that error_messages returns list of strings."""
        rule = {"type": "nonexistent"}
        result = validate_rule_config(rule)

        messages = result.error_messages()

        assert isinstance(messages, list)
        assert all(isinstance(m, str) for m in messages)
        assert len(messages) > 0

    def test_warning_messages(self):
        """Test that warning_messages returns list of strings."""
        rule = {
            "type": "all_of",
            "rules": [{"type": "always"}],
        }
        result = validate_rule_config(rule)

        messages = result.warning_messages()

        assert isinstance(messages, list)
        assert all(isinstance(m, str) for m in messages)
        assert len(messages) > 0

    def test_to_dict(self):
        """Test that to_dict returns proper dictionary."""
        rule = {"type": "always"}
        result = validate_rule_config(rule)

        data = result.to_dict()

        assert isinstance(data, dict)
        assert "valid" in data
        assert "errors" in data
        assert "warnings" in data
        assert "rule_count" in data
        assert "max_depth" in data
        assert "circular_paths" in data


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_rule_dict(self):
        """Test that empty rule dict fails gracefully."""
        rule: dict = {}
        result = validate_rule_config(rule)

        assert result.valid is False

    def test_invalid_type_for_rules(self):
        """Test that invalid type for rules field is detected."""
        rule = {
            "type": "all_of",
            "rules": "not_a_list",  # Invalid
        }
        result = validate_rule_config(rule)

        assert result.valid is False

    def test_invalid_type_for_rule(self):
        """Test that invalid type for rule field is detected."""
        rule = {
            "type": "not",
            "rule": "not_a_dict",  # Invalid
        }
        result = validate_rule_config(rule)

        assert result.valid is False

    def test_none_rule_config(self):
        """Test that None values are handled."""
        rule = {
            "type": "all_of",
            "rules": None,  # None instead of list
        }
        result = validate_rule_config(rule)

        assert result.valid is False

    def test_always_rule_no_params(self):
        """Test that always rule with no params passes."""
        rule = {"type": "always"}
        result = validate_rule_config(rule)

        assert result.valid is True

    def test_never_rule_no_params(self):
        """Test that never rule with no params passes."""
        rule = {"type": "never"}
        result = validate_rule_config(rule)

        assert result.valid is True
