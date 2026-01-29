"""Rule generation service.

This module provides functionality for automatically generating
validation rules based on profile data analysis.

Features:
    - Multiple strictness levels (loose, medium, strict)
    - Preset templates for different use cases
    - Category-based filtering
    - Multiple export formats (YAML, JSON, Python, TOML)
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

import yaml
from sqlalchemy.ext.asyncio import AsyncSession

from truthound_dashboard.db import Profile, Rule, Schema, Source
from truthound_dashboard.core.services import ProfileRepository, RuleRepository
from truthound_dashboard.schemas.rule_suggestion import (
    ApplyRulesResponse,
    CrossColumnRuleSuggestion,
    CrossColumnRuleType,
    ExportRulesResponse,
    PresetInfo,
    PresetsResponse,
    RuleCategory,
    RuleExportFormat,
    RulePreset,
    RuleSuggestionResponse,
    StrictnessLevel,
    SuggestedRule,
)


# Common email pattern
EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
)

# Common date patterns
DATE_PATTERNS = [
    r"\d{4}-\d{2}-\d{2}",  # YYYY-MM-DD
    r"\d{2}/\d{2}/\d{4}",  # MM/DD/YYYY
    r"\d{2}-\d{2}-\d{4}",  # DD-MM-YYYY
]


# =============================================================================
# Statistical Confidence Calculation Helpers
# =============================================================================


def calculate_pattern_confidence(
    match_rate: float,
    sample_size: int,
    min_sample: int = 100,
    base_confidence: float = 0.5,
) -> float:
    """Calculate confidence score based on pattern matching and sample size.

    Uses a statistical approach to compute confidence:
    - Higher match rates increase confidence
    - Larger sample sizes increase confidence
    - Small samples (<min_sample) are penalized

    Args:
        match_rate: Rate of pattern matches (0.0 to 1.0).
        sample_size: Number of samples analyzed.
        min_sample: Minimum sample size for full confidence.
        base_confidence: Starting confidence level.

    Returns:
        Confidence score between 0.0 and 1.0.
    """
    if sample_size == 0:
        return base_confidence

    # Sample size factor: penalize small samples
    size_factor = min(1.0, sample_size / min_sample)

    # Match rate contribution (higher is better)
    rate_contribution = match_rate * 0.4

    # Size contribution (larger samples = more reliable)
    size_contribution = size_factor * 0.1

    # Base contribution
    confidence = base_confidence + rate_contribution + size_contribution

    # Clamp to valid range
    return max(0.0, min(1.0, confidence))


def calculate_uniqueness_confidence(
    unique_ratio: float,
    total_count: int,
    cardinality: int,
) -> float:
    """Calculate confidence for uniqueness-based rules.

    Args:
        unique_ratio: Ratio of unique values.
        total_count: Total number of rows.
        cardinality: Number of distinct values.

    Returns:
        Confidence score.
    """
    if total_count == 0:
        return 0.5

    # High uniqueness = likely primary key
    if unique_ratio >= 0.99:
        base = 0.85
    elif unique_ratio >= 0.95:
        base = 0.75
    elif unique_ratio >= 0.8:
        base = 0.65
    else:
        base = 0.5

    # Bonus for larger datasets (more statistically significant)
    size_bonus = min(0.1, total_count / 10000 * 0.1)

    return min(1.0, base + size_bonus)


def calculate_correlation_confidence(
    pattern_strength: str,
    column_count: int = 2,
) -> float:
    """Calculate confidence for correlation-based rules.

    Args:
        pattern_strength: 'strong', 'medium', 'weak'.
        column_count: Number of columns involved.

    Returns:
        Confidence score.
    """
    strength_scores = {
        "strong": 0.85,
        "medium": 0.7,
        "weak": 0.55,
    }
    base = strength_scores.get(pattern_strength, 0.6)

    # Penalize for more columns (harder to maintain relationship)
    column_penalty = max(0, (column_count - 2) * 0.05)

    return max(0.5, base - column_penalty)


def extract_sample_violations(
    profile_data: dict[str, Any],
    columns: list[str],
    rule_type: str,
    max_samples: int = 5,
) -> list[dict[str, Any]]:
    """Extract sample violations from profile data.

    This function attempts to find potential violations based on the
    profile statistics. In production, this would query actual data.

    Args:
        profile_data: Profile statistics for columns.
        columns: Column names involved in the rule.
        rule_type: Type of cross-column rule.
        max_samples: Maximum number of sample violations to return.

    Returns:
        List of sample violation records.
    """
    violations: list[dict[str, Any]] = []

    # Check if profile has outlier or anomaly data
    for col in columns:
        col_data = profile_data.get(col, {})

        # Check for outliers that might indicate violations
        outliers = col_data.get("outliers", [])
        if outliers:
            for outlier in outliers[:max_samples]:
                violations.append({
                    "row_index": outlier.get("row", 0),
                    "column": col,
                    "value": outlier.get("value"),
                    "reason": f"Outlier detected in {col}",
                })

        # Check for null/missing values that might cause violations
        null_count = col_data.get("null_count", 0)
        if null_count > 0 and rule_type in ("column_coexistence", "column_dependency"):
            violations.append({
                "row_index": "multiple",
                "column": col,
                "value": None,
                "reason": f"{null_count} null values in {col}",
            })

    return violations[:max_samples]


# =============================================================================
# Preset Definitions
# =============================================================================


PRESET_DEFINITIONS: dict[RulePreset, PresetInfo] = {
    RulePreset.DEFAULT: PresetInfo(
        name=RulePreset.DEFAULT,
        display_name="Default",
        description="General purpose validation rules. Balanced coverage and thresholds.",
        strictness=StrictnessLevel.MEDIUM,
        categories=[
            RuleCategory.SCHEMA,
            RuleCategory.COMPLETENESS,
            RuleCategory.UNIQUENESS,
            RuleCategory.STATISTICS,
        ],
        recommended_for="Most data validation scenarios",
    ),
    RulePreset.STRICT: PresetInfo(
        name=RulePreset.STRICT,
        display_name="Strict",
        description="Tight thresholds for production data. High confidence rules only.",
        strictness=StrictnessLevel.STRICT,
        categories=[
            RuleCategory.SCHEMA,
            RuleCategory.COMPLETENESS,
            RuleCategory.UNIQUENESS,
            RuleCategory.STATISTICS,
            RuleCategory.PATTERN,
        ],
        recommended_for="Production data pipelines, data quality gates",
    ),
    RulePreset.LOOSE: PresetInfo(
        name=RulePreset.LOOSE,
        display_name="Loose",
        description="Permissive thresholds for development/testing.",
        strictness=StrictnessLevel.LOOSE,
        categories=[
            RuleCategory.SCHEMA,
            RuleCategory.COMPLETENESS,
        ],
        recommended_for="Development, testing, exploratory analysis",
    ),
    RulePreset.MINIMAL: PresetInfo(
        name=RulePreset.MINIMAL,
        display_name="Minimal",
        description="Essential rules only. Focus on critical data integrity.",
        strictness=StrictnessLevel.MEDIUM,
        categories=[
            RuleCategory.SCHEMA,
            RuleCategory.COMPLETENESS,
        ],
        recommended_for="Quick validation, minimal overhead",
    ),
    RulePreset.COMPREHENSIVE: PresetInfo(
        name=RulePreset.COMPREHENSIVE,
        display_name="Comprehensive",
        description="All available rules. Maximum validation coverage.",
        strictness=StrictnessLevel.MEDIUM,
        categories=[
            RuleCategory.SCHEMA,
            RuleCategory.COMPLETENESS,
            RuleCategory.UNIQUENESS,
            RuleCategory.STATISTICS,
            RuleCategory.PATTERN,
            RuleCategory.DISTRIBUTION,
        ],
        recommended_for="Full data audit, compliance checks",
    ),
    RulePreset.CI_CD: PresetInfo(
        name=RulePreset.CI_CD,
        display_name="CI/CD",
        description="Optimized for continuous integration. Fast execution, clear failures.",
        strictness=StrictnessLevel.STRICT,
        categories=[
            RuleCategory.SCHEMA,
            RuleCategory.COMPLETENESS,
            RuleCategory.UNIQUENESS,
        ],
        recommended_for="CI/CD pipelines, automated testing",
    ),
    RulePreset.SCHEMA_ONLY: PresetInfo(
        name=RulePreset.SCHEMA_ONLY,
        display_name="Schema Only",
        description="Structure validation only. No statistical checks.",
        strictness=StrictnessLevel.MEDIUM,
        categories=[RuleCategory.SCHEMA],
        recommended_for="Schema drift detection, structure validation",
    ),
    RulePreset.FORMAT_ONLY: PresetInfo(
        name=RulePreset.FORMAT_ONLY,
        display_name="Format Only",
        description="Format and pattern rules only.",
        strictness=StrictnessLevel.MEDIUM,
        categories=[RuleCategory.PATTERN],
        recommended_for="Data format validation, PII detection",
    ),
    RulePreset.CROSS_COLUMN: PresetInfo(
        name=RulePreset.CROSS_COLUMN,
        display_name="Cross-Column",
        description="Focus on cross-column relationships and constraints.",
        strictness=StrictnessLevel.MEDIUM,
        categories=[
            RuleCategory.RELATIONSHIP,
            RuleCategory.MULTI_COLUMN,
            RuleCategory.UNIQUENESS,
        ],
        recommended_for="Data integrity, referential constraints, composite keys",
    ),
    RulePreset.DATA_INTEGRITY: PresetInfo(
        name=RulePreset.DATA_INTEGRITY,
        display_name="Data Integrity",
        description="Comprehensive data integrity validation including cross-column rules.",
        strictness=StrictnessLevel.STRICT,
        categories=[
            RuleCategory.SCHEMA,
            RuleCategory.COMPLETENESS,
            RuleCategory.UNIQUENESS,
            RuleCategory.RELATIONSHIP,
            RuleCategory.MULTI_COLUMN,
        ],
        recommended_for="Database migrations, data warehouse validation",
    ),
}


# Strictness thresholds
STRICTNESS_THRESHOLDS = {
    StrictnessLevel.LOOSE: {
        "min_confidence": 0.3,
        "null_threshold": 10.0,
        "unique_threshold": 90.0,
        "range_buffer": 0.2,  # 20% buffer on ranges
    },
    StrictnessLevel.MEDIUM: {
        "min_confidence": 0.5,
        "null_threshold": 5.0,
        "unique_threshold": 95.0,
        "range_buffer": 0.1,  # 10% buffer
    },
    StrictnessLevel.STRICT: {
        "min_confidence": 0.7,
        "null_threshold": 1.0,
        "unique_threshold": 99.0,
        "range_buffer": 0.0,  # No buffer
    },
}


def _parse_percentage(value: str | None) -> float:
    """Parse percentage string to float.

    Args:
        value: Percentage string like "25.5%".

    Returns:
        Float value (0.0-100.0).
    """
    if not value:
        return 0.0
    try:
        return float(value.replace("%", ""))
    except (ValueError, AttributeError):
        return 0.0


class RuleGeneratorService:
    """Service for generating validation rules from profile data."""

    def __init__(self, session: AsyncSession):
        """Initialize service.

        Args:
            session: Database session.
        """
        self.session = session
        self.profile_repo = ProfileRepository(session)
        self.rule_repo = RuleRepository(session)

    def _suggest_null_rules(
        self,
        column: dict[str, Any],
        strictness: StrictnessLevel = StrictnessLevel.MEDIUM,
    ) -> list[SuggestedRule]:
        """Suggest null-related validators based on null percentage.

        Args:
            column: Column profile data.
            strictness: Strictness level for thresholds.

        Returns:
            List of suggested rules.
        """
        suggestions = []
        col_name = column.get("name", "")
        null_pct = _parse_percentage(column.get("null_pct"))
        thresholds = STRICTNESS_THRESHOLDS[strictness]
        null_threshold = thresholds["null_threshold"]

        if null_pct == 0.0:
            # Column has no nulls - suggest NotNull
            suggestions.append(
                SuggestedRule(
                    column=col_name,
                    validator_name="NotNull",
                    params={},
                    confidence=0.95,
                    reason="Column has 0% null values",
                    severity_suggestion="high",
                    category=RuleCategory.COMPLETENESS,
                )
            )
        elif null_pct < 1.0:
            # Very few nulls - suggest Null with mostly
            mostly = 0.99 if strictness == StrictnessLevel.STRICT else 0.98
            suggestions.append(
                SuggestedRule(
                    column=col_name,
                    validator_name="Null",
                    params={"mostly": mostly},
                    confidence=0.85,
                    reason=f"Column has only {null_pct}% null values",
                    severity_suggestion="medium",
                    category=RuleCategory.COMPLETENESS,
                )
            )
        elif null_pct < null_threshold:
            # Some nulls - suggest Null with lower threshold
            mostly = 1 - (null_pct / 100) - 0.01
            suggestions.append(
                SuggestedRule(
                    column=col_name,
                    validator_name="Null",
                    params={"mostly": round(mostly, 2)},
                    confidence=0.7,
                    reason=f"Column has {null_pct}% null values",
                    severity_suggestion="low",
                    category=RuleCategory.COMPLETENESS,
                )
            )

        return suggestions

    def _suggest_uniqueness_rules(
        self,
        column: dict[str, Any],
        strictness: StrictnessLevel = StrictnessLevel.MEDIUM,
    ) -> list[SuggestedRule]:
        """Suggest uniqueness validators based on unique percentage.

        Args:
            column: Column profile data.
            strictness: Strictness level for thresholds.

        Returns:
            List of suggested rules.
        """
        suggestions = []
        col_name = column.get("name", "")
        unique_pct = _parse_percentage(column.get("unique_pct"))
        distinct_count = column.get("distinct_count")
        thresholds = STRICTNESS_THRESHOLDS[strictness]
        unique_threshold = thresholds["unique_threshold"]

        if unique_pct >= 99.9:
            # Nearly unique - suggest Unique
            suggestions.append(
                SuggestedRule(
                    column=col_name,
                    validator_name="Unique",
                    params={},
                    confidence=0.95,
                    reason=f"Column has {unique_pct}% unique values (likely primary key)",
                    severity_suggestion="high",
                    category=RuleCategory.UNIQUENESS,
                )
            )
        elif unique_pct >= unique_threshold:
            # High uniqueness - suggest Unique with tolerance
            mostly = unique_pct / 100
            suggestions.append(
                SuggestedRule(
                    column=col_name,
                    validator_name="Unique",
                    params={"mostly": round(mostly, 2)},
                    confidence=0.8,
                    reason=f"Column has {unique_pct}% unique values",
                    severity_suggestion="medium",
                    category=RuleCategory.UNIQUENESS,
                )
            )
        elif unique_pct < 10.0 and distinct_count and distinct_count < 50:
            # Low cardinality - suggest DistinctSet
            buffer = 10 if strictness == StrictnessLevel.LOOSE else 5
            suggestions.append(
                SuggestedRule(
                    column=col_name,
                    validator_name="DistinctSet",
                    params={"max_distinct": distinct_count + buffer},
                    confidence=0.75,
                    reason=f"Column has low cardinality ({distinct_count} distinct values)",
                    severity_suggestion="low",
                    category=RuleCategory.DISTRIBUTION,
                )
            )

        return suggestions

    def _suggest_range_rules(
        self,
        column: dict[str, Any],
        strictness: StrictnessLevel = StrictnessLevel.MEDIUM,
    ) -> list[SuggestedRule]:
        """Suggest range validators based on min/max values.

        Args:
            column: Column profile data.
            strictness: Strictness level for thresholds.

        Returns:
            List of suggested rules.
        """
        suggestions = []
        col_name = column.get("name", "")
        dtype = column.get("dtype", "").lower()
        min_val = column.get("min")
        max_val = column.get("max")
        thresholds = STRICTNESS_THRESHOLDS[strictness]
        buffer = thresholds["range_buffer"]

        # Only suggest for numeric types
        if dtype not in ("int64", "int32", "float64", "float32", "number", "integer"):
            return suggestions

        if min_val is not None and max_val is not None:
            try:
                min_num = float(min_val)
                max_num = float(max_val)

                # Only suggest if range seems reasonable
                if max_num > min_num:
                    # Apply buffer to range
                    range_size = max_num - min_num
                    buffered_min = min_num - (range_size * buffer)
                    buffered_max = max_num + (range_size * buffer)

                    suggestions.append(
                        SuggestedRule(
                            column=col_name,
                            validator_name="Range",
                            params={
                                "min_value": round(buffered_min, 2),
                                "max_value": round(buffered_max, 2),
                            },
                            confidence=0.7,
                            reason=f"Column values range from {min_num} to {max_num}",
                            severity_suggestion="medium",
                            category=RuleCategory.STATISTICS,
                        )
                    )
            except (ValueError, TypeError):
                pass

        return suggestions

    def _suggest_type_rules(
        self,
        column: dict[str, Any],
        schema_column: dict[str, Any] | None = None,
        strictness: StrictnessLevel = StrictnessLevel.MEDIUM,
    ) -> list[SuggestedRule]:
        """Suggest type and pattern validators based on data type.

        Args:
            column: Column profile data.
            schema_column: Optional schema column definition.
            strictness: Strictness level.

        Returns:
            List of suggested rules.
        """
        suggestions = []
        col_name = column.get("name", "").lower()
        original_name = column.get("name", "")
        dtype = column.get("dtype", "").lower()

        # Email detection by column name
        if any(hint in col_name for hint in ("email", "e_mail", "mail")):
            suggestions.append(
                SuggestedRule(
                    column=original_name,
                    validator_name="Email",
                    params={},
                    confidence=0.85,
                    reason="Column name suggests email content",
                    severity_suggestion="medium",
                    category=RuleCategory.PATTERN,
                )
            )

        # Phone detection by column name
        if any(hint in col_name for hint in ("phone", "tel", "mobile", "cell")):
            suggestions.append(
                SuggestedRule(
                    column=original_name,
                    validator_name="Phone",
                    params={},
                    confidence=0.75,
                    reason="Column name suggests phone number",
                    severity_suggestion="low",
                    category=RuleCategory.PATTERN,
                )
            )

        # URL detection by column name
        if any(hint in col_name for hint in ("url", "link", "website", "href")):
            suggestions.append(
                SuggestedRule(
                    column=original_name,
                    validator_name="URL",
                    params={},
                    confidence=0.8,
                    reason="Column name suggests URL content",
                    severity_suggestion="low",
                    category=RuleCategory.PATTERN,
                )
            )

        # Date/datetime type detection
        if dtype in ("datetime64", "date", "timestamp"):
            suggestions.append(
                SuggestedRule(
                    column=original_name,
                    validator_name="DateParseable",
                    params={},
                    confidence=0.9,
                    reason=f"Column has {dtype} data type",
                    severity_suggestion="medium",
                    category=RuleCategory.SCHEMA,
                )
            )

        # Positive number detection for common column names
        if dtype in ("int64", "int32", "float64", "float32"):
            positive_hints = ("id", "count", "quantity", "amount", "price", "age")
            if any(col_name.endswith(hint) or col_name == hint for hint in positive_hints):
                min_val = column.get("min")
                if min_val is not None:
                    try:
                        if float(min_val) >= 0:
                            suggestions.append(
                                SuggestedRule(
                                    column=original_name,
                                    validator_name="Positive",
                                    params={},
                                    confidence=0.75,
                                    reason=f"Column name suggests positive values (min={min_val})",
                                    severity_suggestion="low",
                                    category=RuleCategory.STATISTICS,
                                )
                            )
                    except (ValueError, TypeError):
                        pass

        return suggestions

    def _suggest_statistical_rules(
        self,
        column: dict[str, Any],
        strictness: StrictnessLevel = StrictnessLevel.MEDIUM,
    ) -> list[SuggestedRule]:
        """Suggest statistical validators based on distribution.

        Args:
            column: Column profile data.
            strictness: Strictness level.

        Returns:
            List of suggested rules.
        """
        suggestions = []
        col_name = column.get("name", "")
        mean = column.get("mean")
        std = column.get("std")

        # Suggest Z-score based outlier detection if we have distribution data
        if mean is not None and std is not None and std > 0:
            # Adjust threshold based on strictness
            threshold = {
                StrictnessLevel.LOOSE: 4.0,
                StrictnessLevel.MEDIUM: 3.0,
                StrictnessLevel.STRICT: 2.5,
            }[strictness]

            suggestions.append(
                SuggestedRule(
                    column=col_name,
                    validator_name="ZScore",
                    params={"threshold": threshold},
                    confidence=0.6,
                    reason=f"Column has mean={mean:.2f}, std={std:.2f}",
                    severity_suggestion="low",
                    category=RuleCategory.STATISTICS,
                )
            )

        return suggestions

    # =============================================================================
    # Cross-Column Rule Suggestion Methods
    # =============================================================================

    def _suggest_composite_key_rules(
        self,
        columns: list[dict[str, Any]],
        strictness: StrictnessLevel = StrictnessLevel.MEDIUM,
    ) -> list[CrossColumnRuleSuggestion]:
        """Suggest composite key (multi-column uniqueness) rules.

        Analyzes column combinations to detect potential composite keys
        based on uniqueness patterns.

        Args:
            columns: List of column profile data.
            strictness: Strictness level.

        Returns:
            List of cross-column suggestions.
        """
        suggestions = []

        # Find columns that might form composite keys
        # Look for ID-like columns or columns with moderate cardinality
        id_columns = []
        categorical_columns = []

        for col in columns:
            col_name = col.get("name", "")
            unique_pct = _parse_percentage(col.get("unique_pct"))
            distinct_count = col.get("distinct_count", 0)

            # ID-like columns (high but not 100% uniqueness)
            if 50 <= unique_pct < 99.9 and any(
                hint in col_name.lower()
                for hint in ("id", "key", "code", "num", "ref")
            ):
                id_columns.append(col_name)

            # Categorical columns with moderate cardinality
            elif distinct_count and 2 < distinct_count < 100:
                categorical_columns.append(col_name)

        # Suggest composite keys from ID column pairs
        if len(id_columns) >= 2:
            for i in range(len(id_columns)):
                for j in range(i + 1, min(i + 3, len(id_columns))):
                    cols = [id_columns[i], id_columns[j]]
                    suggestions.append(
                        CrossColumnRuleSuggestion(
                            rule_type=CrossColumnRuleType.COMPOSITE_KEY,
                            columns=cols,
                            validator_name="MultiColumnUnique",
                            params={"columns": cols},
                            confidence=0.75,
                            reason=f"Columns {cols[0]} and {cols[1]} may form a composite key",
                            severity_suggestion="high",
                            evidence={
                                "pattern": "id_column_combination",
                                "columns": cols,
                            },
                        )
                    )

        # Suggest composite keys from ID + categorical combinations
        for id_col in id_columns[:2]:  # Limit to avoid explosion
            for cat_col in categorical_columns[:3]:
                suggestions.append(
                    CrossColumnRuleSuggestion(
                        rule_type=CrossColumnRuleType.COMPOSITE_KEY,
                        columns=[id_col, cat_col],
                        validator_name="MultiColumnUnique",
                        params={"columns": [id_col, cat_col]},
                        confidence=0.65,
                        reason=f"{id_col} combined with {cat_col} may form a natural key",
                        severity_suggestion="medium",
                        evidence={
                            "pattern": "id_categorical_combination",
                        },
                    )
                )

        return suggestions

    def _suggest_comparison_rules(
        self,
        columns: list[dict[str, Any]],
        strictness: StrictnessLevel = StrictnessLevel.MEDIUM,
    ) -> list[CrossColumnRuleSuggestion]:
        """Suggest column comparison rules (e.g., end_date > start_date).

        Args:
            columns: List of column profile data.
            strictness: Strictness level.

        Returns:
            List of cross-column suggestions.
        """
        suggestions = []
        col_map = {col.get("name", ""): col for col in columns}

        # Common comparison patterns
        date_pairs = [
            ("start_date", "end_date", ">"),
            ("created_at", "updated_at", "<="),
            ("birth_date", "death_date", "<="),
            ("hire_date", "termination_date", "<="),
            ("order_date", "ship_date", "<="),
            ("start_time", "end_time", "<"),
        ]

        numeric_pairs = [
            ("min_value", "max_value", "<="),
            ("min_price", "max_price", "<="),
            ("min_quantity", "max_quantity", "<="),
            ("low", "high", "<="),
            ("floor", "ceiling", "<="),
            ("cost", "price", "<="),
        ]

        # Check date comparison patterns
        for start_hint, end_hint, operator in date_pairs:
            start_cols = [
                c for c in col_map
                if start_hint in c.lower() or c.lower().endswith("_start")
            ]
            end_cols = [
                c for c in col_map
                if end_hint in c.lower() or c.lower().endswith("_end")
            ]

            for start_col in start_cols:
                for end_col in end_cols:
                    # Avoid matching same column
                    if start_col == end_col:
                        continue
                    # Check if they share a common prefix/suffix
                    start_base = start_col.replace("_start", "").replace("start_", "")
                    end_base = end_col.replace("_end", "").replace("end_", "")
                    base_match = (
                        start_base.lower() == end_base.lower()
                        or start_base.lower().replace("date", "") == end_base.lower().replace("date", "")
                    )

                    confidence = 0.85 if base_match else 0.7

                    suggestions.append(
                        CrossColumnRuleSuggestion(
                            rule_type=CrossColumnRuleType.COLUMN_COMPARISON,
                            columns=[end_col, start_col],
                            validator_name="ColumnComparison",
                            params={
                                "column_a": end_col,
                                "column_b": start_col,
                                "operator": operator,
                            },
                            confidence=confidence,
                            reason=f"{end_col} should be {operator} {start_col}",
                            severity_suggestion="high" if confidence >= 0.8 else "medium",
                            evidence={
                                "pattern": "date_range",
                                "base_match": base_match,
                            },
                        )
                    )

        # Check numeric comparison patterns
        for min_hint, max_hint, operator in numeric_pairs:
            min_cols = [c for c in col_map if min_hint in c.lower()]
            max_cols = [c for c in col_map if max_hint in c.lower()]

            for min_col in min_cols:
                for max_col in max_cols:
                    if min_col == max_col:
                        continue

                    suggestions.append(
                        CrossColumnRuleSuggestion(
                            rule_type=CrossColumnRuleType.COLUMN_COMPARISON,
                            columns=[max_col, min_col],
                            validator_name="ColumnComparison",
                            params={
                                "column_a": max_col,
                                "column_b": min_col,
                                "operator": ">=",
                            },
                            confidence=0.8,
                            reason=f"{max_col} should be >= {min_col}",
                            severity_suggestion="high",
                            evidence={
                                "pattern": "numeric_range",
                            },
                        )
                    )

        return suggestions

    def _suggest_arithmetic_rules(
        self,
        columns: list[dict[str, Any]],
        strictness: StrictnessLevel = StrictnessLevel.MEDIUM,
    ) -> list[CrossColumnRuleSuggestion]:
        """Suggest arithmetic relationship rules (sum, product, etc.).

        Args:
            columns: List of column profile data.
            strictness: Strictness level.

        Returns:
            List of cross-column suggestions.
        """
        suggestions = []
        col_map = {col.get("name", "").lower(): col.get("name", "") for col in columns}
        numeric_cols = [
            col.get("name", "") for col in columns
            if col.get("dtype", "").lower() in ("int64", "int32", "float64", "float32", "number", "integer")
        ]

        # Common sum patterns: subtotal + tax + shipping = total
        sum_patterns = [
            (["subtotal", "tax", "shipping"], "total", "Order total calculation"),
            (["subtotal", "tax"], "total", "Subtotal + tax = total"),
            (["quantity", "unit_price"], None, "Quantity * unit_price"),  # Product
            (["hours", "rate"], None, "Hours * rate"),  # Product
            (["principal", "interest"], "total_amount", "Principal + interest"),
            (["base_salary", "bonus"], "total_compensation", "Salary + bonus"),
        ]

        for pattern_cols, result_col, description in sum_patterns:
            matched_cols = []
            for p in pattern_cols:
                for col_lower, col_name in col_map.items():
                    if p in col_lower:
                        matched_cols.append(col_name)
                        break

            if len(matched_cols) >= 2:
                # Check for result column
                result_found = None
                if result_col:
                    for col_lower, col_name in col_map.items():
                        if result_col in col_lower:
                            result_found = col_name
                            break

                if result_found:
                    suggestions.append(
                        CrossColumnRuleSuggestion(
                            rule_type=CrossColumnRuleType.COLUMN_SUM,
                            columns=[*matched_cols, result_found],
                            validator_name="ColumnSum",
                            params={
                                "columns": matched_cols,
                                "target_column": result_found,
                                "tolerance": 0.01,
                            },
                            confidence=0.75,
                            reason=f"Sum of {', '.join(matched_cols)} should equal {result_found}",
                            severity_suggestion="high",
                            evidence={
                                "pattern": "arithmetic_sum",
                                "description": description,
                            },
                        )
                    )

        # Percentage/ratio patterns
        percentage_patterns = [
            ("percentage", "total", "part", "Percentage calculation"),
            ("rate", "amount", "base", "Rate calculation"),
            ("discount_pct", "discount", "subtotal", "Discount percentage"),
        ]

        return suggestions

    def _suggest_correlation_rules(
        self,
        columns: list[dict[str, Any]],
        strictness: StrictnessLevel = StrictnessLevel.MEDIUM,
    ) -> list[CrossColumnRuleSuggestion]:
        """Suggest column correlation rules for numeric columns.

        Analyzes profile data to identify potentially correlated numeric columns
        based on naming patterns and statistical properties.

        Args:
            columns: List of column profile data.
            strictness: Strictness level.

        Returns:
            List of cross-column suggestions.
        """
        suggestions = []

        # Filter numeric columns only
        numeric_cols = [
            col for col in columns
            if col.get("dtype", "").lower() in (
                "int64", "int32", "float64", "float32", "number", "integer", "float"
            )
        ]

        if len(numeric_cols) < 2:
            return suggestions

        # Common correlation patterns based on naming conventions
        correlation_patterns = [
            # High positive correlation expected
            (["price", "cost"], "positive", 0.7, "Price/cost related columns"),
            (["quantity", "total"], "positive", 0.5, "Quantity affects total"),
            (["height", "weight"], "positive", 0.3, "Physical measurements"),
            (["income", "expenditure"], "positive", 0.4, "Financial metrics"),
            (["age", "experience"], "positive", 0.5, "Age correlates with experience"),
            (["views", "clicks"], "positive", 0.6, "Engagement metrics"),
            (["revenue", "profit"], "positive", 0.6, "Revenue correlates with profit"),
            # Negative correlation expected
            (["discount", "price"], "negative", -0.3, "Discount inversely affects price"),
            (["errors", "quality"], "negative", -0.5, "Errors reduce quality score"),
        ]

        col_name_map = {col.get("name", "").lower(): col.get("name", "") for col in numeric_cols}

        for hints, direction, expected_correlation, description in correlation_patterns:
            matched_cols = []
            for hint in hints:
                for col_lower, col_name in col_name_map.items():
                    if hint in col_lower and col_name not in matched_cols:
                        matched_cols.append(col_name)
                        break

            if len(matched_cols) >= 2:
                # Suggest correlation check for the first pair found
                col_a, col_b = matched_cols[0], matched_cols[1]
                if direction == "positive":
                    min_corr = expected_correlation
                    max_corr = 1.0
                else:
                    min_corr = -1.0
                    max_corr = expected_correlation

                suggestions.append(
                    CrossColumnRuleSuggestion(
                        rule_type=CrossColumnRuleType.COLUMN_CORRELATION,
                        columns=[col_a, col_b],
                        validator_name="ColumnCorrelation",
                        params={
                            "column_a": col_a,
                            "column_b": col_b,
                            "min_correlation": min_corr,
                            "max_correlation": max_corr,
                        },
                        confidence=0.65,
                        reason=f"{description}: {col_a} and {col_b} may be correlated",
                        severity_suggestion="medium",
                        evidence={
                            "pattern": "correlation_pattern",
                            "direction": direction,
                            "expected_correlation": expected_correlation,
                        },
                    )
                )

        # Also suggest correlation check for columns with similar names (e.g., metric_v1, metric_v2)
        for i, col1 in enumerate(numeric_cols):
            for col2 in numeric_cols[i + 1:]:
                name1 = col1.get("name", "")
                name2 = col2.get("name", "")

                # Check for versioned or indexed columns
                base1 = re.sub(r"[_\-]?(v?\d+|old|new|prev|next)$", "", name1.lower())
                base2 = re.sub(r"[_\-]?(v?\d+|old|new|prev|next)$", "", name2.lower())

                if base1 and base1 == base2 and name1 != name2:
                    suggestions.append(
                        CrossColumnRuleSuggestion(
                            rule_type=CrossColumnRuleType.COLUMN_CORRELATION,
                            columns=[name1, name2],
                            validator_name="ColumnCorrelation",
                            params={
                                "column_a": name1,
                                "column_b": name2,
                                "min_correlation": 0.5,
                                "max_correlation": 1.0,
                            },
                            confidence=0.7,
                            reason=f"Versioned columns {name1} and {name2} should be correlated",
                            severity_suggestion="low",
                            evidence={
                                "pattern": "versioned_columns",
                                "base_name": base1,
                            },
                        )
                    )

        return suggestions

    def _suggest_chain_comparison_rules(
        self,
        columns: list[dict[str, Any]],
        strictness: StrictnessLevel = StrictnessLevel.MEDIUM,
    ) -> list[CrossColumnRuleSuggestion]:
        """Suggest chain comparison rules (a < b < c).

        Args:
            columns: List of column profile data.
            strictness: Strictness level.

        Returns:
            List of cross-column suggestions.
        """
        suggestions = []
        col_map = {col.get("name", "").lower(): col.get("name", "") for col in columns}

        # Common chain comparison patterns
        chain_patterns = [
            # Date chains
            (["created", "updated", "deleted"], "<=", "Lifecycle date ordering"),
            (["start_date", "mid_date", "end_date"], "<=", "Date range ordering"),
            (["ordered", "shipped", "delivered"], "<=", "Order timeline"),
            (["submitted", "approved", "completed"], "<=", "Workflow dates"),
            # Numeric chains
            (["min", "avg", "max"], "<=", "Statistical ordering"),
            (["low", "mid", "high"], "<=", "Range tier ordering"),
            (["bronze", "silver", "gold"], "<=", "Tier value ordering"),
            (["small", "medium", "large"], "<=", "Size value ordering"),
            (["floor_price", "price", "ceiling_price"], "<=", "Price bounds ordering"),
            (["cost", "price", "msrp"], "<=", "Pricing chain"),
        ]

        for hints, operator, description in chain_patterns:
            matched_cols = []
            for hint in hints:
                for col_lower, col_name in col_map.items():
                    if hint in col_lower and col_name not in matched_cols:
                        matched_cols.append(col_name)
                        break

            if len(matched_cols) >= 3:
                suggestions.append(
                    CrossColumnRuleSuggestion(
                        rule_type=CrossColumnRuleType.COLUMN_CHAIN_COMPARISON,
                        columns=matched_cols[:3],  # Limit to 3 columns
                        validator_name="ColumnChainComparison",
                        params={
                            "columns": matched_cols[:3],
                            "operator": operator,
                        },
                        confidence=0.75,
                        reason=f"{description}: {' {0} '.format(operator).join(matched_cols[:3])}",
                        severity_suggestion="medium",
                        evidence={
                            "pattern": "chain_comparison",
                            "operator": operator,
                        },
                    )
                )

        return suggestions

    def _suggest_advanced_arithmetic_rules(
        self,
        columns: list[dict[str, Any]],
        strictness: StrictnessLevel = StrictnessLevel.MEDIUM,
    ) -> list[CrossColumnRuleSuggestion]:
        """Suggest advanced arithmetic relationship rules (product, ratio, percentage).

        Args:
            columns: List of column profile data.
            strictness: Strictness level.

        Returns:
            List of cross-column suggestions.
        """
        suggestions = []
        col_map = {col.get("name", "").lower(): col.get("name", "") for col in columns}
        numeric_cols = [
            col.get("name", "") for col in columns
            if col.get("dtype", "").lower() in (
                "int64", "int32", "float64", "float32", "number", "integer", "float"
            )
        ]

        # Product patterns (a * b = c)
        product_patterns = [
            (["quantity", "unit_price"], "total", "Line item total"),
            (["quantity", "price"], "amount", "Order amount"),
            (["hours", "rate"], "cost", "Labor cost"),
            (["hours", "hourly_rate"], "total_cost", "Total labor cost"),
            (["length", "width"], "area", "Area calculation"),
            (["principal", "rate"], "interest", "Interest calculation"),
        ]

        for factors, result_hint, description in product_patterns:
            factor_cols = []
            for factor in factors:
                for col_lower, col_name in col_map.items():
                    if factor in col_lower and col_name not in factor_cols:
                        factor_cols.append(col_name)
                        break

            if len(factor_cols) >= 2:
                # Find result column
                result_col = None
                for col_lower, col_name in col_map.items():
                    if result_hint in col_lower and col_name not in factor_cols:
                        result_col = col_name
                        break

                if result_col:
                    suggestions.append(
                        CrossColumnRuleSuggestion(
                            rule_type=CrossColumnRuleType.COLUMN_PRODUCT,
                            columns=[*factor_cols, result_col],
                            validator_name="ColumnProduct",
                            params={
                                "columns": factor_cols,
                                "target_column": result_col,
                                "tolerance": 0.01,
                            },
                            confidence=0.75,
                            reason=f"{description}: {' × '.join(factor_cols)} = {result_col}",
                            severity_suggestion="high",
                            evidence={
                                "pattern": "arithmetic_product",
                                "description": description,
                            },
                        )
                    )

        # Ratio patterns (a / b = expected ratio or a / b ≈ c)
        ratio_patterns = [
            ("profit", "revenue", "margin", "Profit margin"),
            ("tax", "subtotal", "tax_rate", "Tax rate"),
            ("discount", "price", "discount_rate", "Discount rate"),
            ("part", "total", "ratio", "Part to total ratio"),
            ("completed", "total", "completion_rate", "Completion rate"),
        ]

        for numerator_hint, denominator_hint, result_hint, description in ratio_patterns:
            numerator_col = None
            denominator_col = None
            result_col = None

            for col_lower, col_name in col_map.items():
                if numerator_hint in col_lower and not numerator_col:
                    numerator_col = col_name
                elif denominator_hint in col_lower and not denominator_col:
                    denominator_col = col_name
                elif result_hint in col_lower and not result_col:
                    result_col = col_name

            if numerator_col and denominator_col:
                if result_col:
                    # Ratio with result column
                    suggestions.append(
                        CrossColumnRuleSuggestion(
                            rule_type=CrossColumnRuleType.COLUMN_RATIO,
                            columns=[numerator_col, denominator_col, result_col],
                            validator_name="ColumnRatio",
                            params={
                                "numerator_column": numerator_col,
                                "denominator_column": denominator_col,
                                "result_column": result_col,
                                "tolerance": 0.01,
                            },
                            confidence=0.7,
                            reason=f"{description}: {numerator_col} / {denominator_col} = {result_col}",
                            severity_suggestion="medium",
                            evidence={
                                "pattern": "arithmetic_ratio",
                                "description": description,
                            },
                        )
                    )

        # Percentage patterns
        percentage_patterns = [
            ("discount_pct", "subtotal", "discount", "Discount percentage"),
            ("tax_pct", "subtotal", "tax", "Tax percentage"),
            ("commission_pct", "sales", "commission", "Commission percentage"),
            ("margin_pct", "revenue", "profit", "Margin percentage"),
        ]

        for pct_hint, base_hint, result_hint, description in percentage_patterns:
            pct_col = None
            base_col = None
            result_col = None

            for col_lower, col_name in col_map.items():
                if pct_hint in col_lower and not pct_col:
                    pct_col = col_name
                elif base_hint in col_lower and not base_col:
                    base_col = col_name
                elif result_hint in col_lower and not result_col:
                    result_col = col_name

            if pct_col and base_col and result_col:
                suggestions.append(
                    CrossColumnRuleSuggestion(
                        rule_type=CrossColumnRuleType.COLUMN_PERCENTAGE,
                        columns=[pct_col, base_col, result_col],
                        validator_name="ColumnPercentage",
                        params={
                            "percentage_column": pct_col,
                            "base_column": base_col,
                            "result_column": result_col,
                            "tolerance": 0.01,
                        },
                        confidence=0.7,
                        reason=f"{description}: {base_col} × {pct_col}% = {result_col}",
                        severity_suggestion="medium",
                        evidence={
                            "pattern": "arithmetic_percentage",
                            "description": description,
                        },
                    )
                )

        # Difference patterns (a - b = c)
        difference_patterns = [
            ("gross", "deductions", "net", "Net calculation"),
            ("revenue", "cost", "profit", "Profit calculation"),
            ("end_value", "start_value", "change", "Change calculation"),
            ("current", "previous", "delta", "Delta calculation"),
        ]

        for minuend_hint, subtrahend_hint, result_hint, description in difference_patterns:
            minuend_col = None
            subtrahend_col = None
            result_col = None

            for col_lower, col_name in col_map.items():
                if minuend_hint in col_lower and not minuend_col:
                    minuend_col = col_name
                elif subtrahend_hint in col_lower and not subtrahend_col:
                    subtrahend_col = col_name
                elif result_hint in col_lower and not result_col:
                    result_col = col_name

            if minuend_col and subtrahend_col and result_col:
                suggestions.append(
                    CrossColumnRuleSuggestion(
                        rule_type=CrossColumnRuleType.COLUMN_DIFFERENCE,
                        columns=[minuend_col, subtrahend_col, result_col],
                        validator_name="ColumnDifference",
                        params={
                            "minuend_column": minuend_col,
                            "subtrahend_column": subtrahend_col,
                            "result_column": result_col,
                            "tolerance": 0.01,
                        },
                        confidence=0.75,
                        reason=f"{description}: {minuend_col} - {subtrahend_col} = {result_col}",
                        severity_suggestion="high",
                        evidence={
                            "pattern": "arithmetic_difference",
                            "description": description,
                        },
                    )
                )

        return suggestions

    def _suggest_dependency_rules(
        self,
        columns: list[dict[str, Any]],
        strictness: StrictnessLevel = StrictnessLevel.MEDIUM,
    ) -> list[CrossColumnRuleSuggestion]:
        """Suggest functional dependency and implication rules.

        Args:
            columns: List of column profile data.
            strictness: Strictness level.

        Returns:
            List of cross-column suggestions.
        """
        suggestions = []
        col_map = {col.get("name", ""): col for col in columns}

        # Common dependency patterns
        dependency_patterns = [
            # If status is 'active', email must not be null
            ("status", "email", "active", "If status is active, email is required"),
            ("status", "phone", "active", "If status is active, phone is required"),
            # If is_premium, subscription_tier must be set
            ("is_premium", "subscription_tier", True, "Premium users must have subscription tier"),
            # Country determines currency
            ("country", "currency", None, "Country determines currency"),
            ("country_code", "currency_code", None, "Country code determines currency code"),
        ]

        for det_hint, dep_hint, condition, description in dependency_patterns:
            det_col = None
            dep_col = None

            for col_name in col_map:
                if det_hint in col_name.lower():
                    det_col = col_name
                if dep_hint in col_name.lower():
                    dep_col = col_name

            if det_col and dep_col and det_col != dep_col:
                if condition is not None:
                    # Implication rule: if condition then dependent not null
                    suggestions.append(
                        CrossColumnRuleSuggestion(
                            rule_type=CrossColumnRuleType.COLUMN_IMPLICATION,
                            columns=[det_col, dep_col],
                            validator_name="ColumnImplication",
                            params={
                                "determinant_column": det_col,
                                "dependent_column": dep_col,
                                "condition_value": condition,
                            },
                            confidence=0.7,
                            reason=description,
                            severity_suggestion="medium",
                            evidence={
                                "pattern": "conditional_dependency",
                            },
                        )
                    )
                else:
                    # Functional dependency
                    suggestions.append(
                        CrossColumnRuleSuggestion(
                            rule_type=CrossColumnRuleType.COLUMN_DEPENDENCY,
                            columns=[det_col, dep_col],
                            validator_name="ColumnDependency",
                            params={
                                "determinant_column": det_col,
                                "dependent_column": dep_col,
                            },
                            confidence=0.65,
                            reason=description,
                            severity_suggestion="medium",
                            evidence={
                                "pattern": "functional_dependency",
                            },
                        )
                    )

        # Coexistence patterns (all null or all non-null)
        coexistence_groups = [
            (["address_line1", "city", "postal_code"], "Address fields should coexist"),
            (["latitude", "longitude"], "Coordinates should coexist"),
            (["first_name", "last_name"], "Name fields should coexist"),
            (["start_date", "end_date"], "Date range fields should coexist"),
        ]

        for hints, description in coexistence_groups:
            found_cols = []
            for hint in hints:
                for col_name in col_map:
                    if hint in col_name.lower():
                        found_cols.append(col_name)
                        break

            if len(found_cols) >= 2:
                suggestions.append(
                    CrossColumnRuleSuggestion(
                        rule_type=CrossColumnRuleType.COLUMN_COEXISTENCE,
                        columns=found_cols,
                        validator_name="ColumnCoexistence",
                        params={"columns": found_cols},
                        confidence=0.7,
                        reason=description,
                        severity_suggestion="medium",
                        evidence={
                            "pattern": "coexistence",
                            "matched_hints": hints[:len(found_cols)],
                        },
                    )
                )

        # Mutual exclusivity patterns
        mutex_groups = [
            (["phone_home", "phone_work", "phone_mobile"], "At most one phone type"),
            (["payment_card", "payment_bank", "payment_crypto"], "One payment method"),
        ]

        for hints, description in mutex_groups:
            found_cols = []
            for hint in hints:
                for col_name in col_map:
                    if hint in col_name.lower():
                        found_cols.append(col_name)
                        break

            if len(found_cols) >= 2:
                suggestions.append(
                    CrossColumnRuleSuggestion(
                        rule_type=CrossColumnRuleType.COLUMN_MUTUAL_EXCLUSIVITY,
                        columns=found_cols,
                        validator_name="ColumnMutualExclusivity",
                        params={"columns": found_cols},
                        confidence=0.6,
                        reason=description,
                        severity_suggestion="low",
                        evidence={
                            "pattern": "mutual_exclusivity",
                        },
                    )
                )

        return suggestions

    def _generate_cross_column_suggestions(
        self,
        columns: list[dict[str, Any]],
        strictness: StrictnessLevel = StrictnessLevel.MEDIUM,
        include_types: list[CrossColumnRuleType] | None = None,
        exclude_types: list[CrossColumnRuleType] | None = None,
    ) -> list[CrossColumnRuleSuggestion]:
        """Generate all cross-column rule suggestions.

        Args:
            columns: List of column profile data.
            strictness: Strictness level.
            include_types: Only include these cross-column rule types.
            exclude_types: Exclude these cross-column rule types.

        Returns:
            List of cross-column suggestions.
        """
        all_suggestions: list[CrossColumnRuleSuggestion] = []

        # Generate suggestions by type
        # Each generator method may produce multiple rule types
        type_generators = {
            CrossColumnRuleType.COMPOSITE_KEY: self._suggest_composite_key_rules,
            CrossColumnRuleType.COLUMN_COMPARISON: self._suggest_comparison_rules,
            CrossColumnRuleType.COLUMN_SUM: self._suggest_arithmetic_rules,
            CrossColumnRuleType.COLUMN_DEPENDENCY: self._suggest_dependency_rules,
            CrossColumnRuleType.COLUMN_IMPLICATION: self._suggest_dependency_rules,
            CrossColumnRuleType.COLUMN_COEXISTENCE: self._suggest_dependency_rules,
            CrossColumnRuleType.COLUMN_MUTUAL_EXCLUSIVITY: self._suggest_dependency_rules,
            # New generators for comprehensive cross-column support
            CrossColumnRuleType.COLUMN_CORRELATION: self._suggest_correlation_rules,
            CrossColumnRuleType.COLUMN_CHAIN_COMPARISON: self._suggest_chain_comparison_rules,
            CrossColumnRuleType.COLUMN_PRODUCT: self._suggest_advanced_arithmetic_rules,
            CrossColumnRuleType.COLUMN_RATIO: self._suggest_advanced_arithmetic_rules,
            CrossColumnRuleType.COLUMN_PERCENTAGE: self._suggest_advanced_arithmetic_rules,
            CrossColumnRuleType.COLUMN_DIFFERENCE: self._suggest_advanced_arithmetic_rules,
        }

        # Determine which types to generate
        types_to_generate = set(type_generators.keys())

        if include_types:
            types_to_generate &= set(include_types)

        if exclude_types:
            types_to_generate -= set(exclude_types)

        # Generate suggestions
        generated_methods = set()
        for rule_type in types_to_generate:
            generator = type_generators.get(rule_type)
            if generator and generator not in generated_methods:
                generated_methods.add(generator)
                suggestions = generator(columns, strictness)
                all_suggestions.extend(suggestions)

        # Filter by min confidence based on strictness
        thresholds = STRICTNESS_THRESHOLDS[strictness]
        min_confidence = thresholds["min_confidence"]
        all_suggestions = [s for s in all_suggestions if s.confidence >= min_confidence]

        # Deduplicate and sort by confidence
        seen = set()
        unique_suggestions = []
        for s in all_suggestions:
            key = (s.rule_type.value, tuple(sorted(s.columns)))
            if key not in seen:
                seen.add(key)
                unique_suggestions.append(s)

        unique_suggestions.sort(key=lambda s: s.confidence, reverse=True)

        # Assign unique IDs
        import uuid
        for s in unique_suggestions:
            s.id = str(uuid.uuid4())[:8]

        return unique_suggestions

    def _get_categories_for_preset(
        self, preset: RulePreset | None
    ) -> list[RuleCategory] | None:
        """Get categories for a preset.

        Args:
            preset: Preset name.

        Returns:
            List of categories or None for all.
        """
        if preset is None:
            return None
        preset_info = PRESET_DEFINITIONS.get(preset)
        if preset_info:
            return preset_info.categories
        return None

    def _filter_by_category(
        self,
        suggestions: list[SuggestedRule],
        include_categories: list[RuleCategory] | None,
        exclude_categories: list[RuleCategory] | None,
    ) -> list[SuggestedRule]:
        """Filter suggestions by category.

        Args:
            suggestions: List of suggestions.
            include_categories: Categories to include (None = all).
            exclude_categories: Categories to exclude.

        Returns:
            Filtered list.
        """
        result = suggestions

        if include_categories:
            include_set = set(c.value if isinstance(c, RuleCategory) else c for c in include_categories)
            result = [
                s for s in result
                if (s.category.value if isinstance(s.category, RuleCategory) else s.category) in include_set
            ]

        if exclude_categories:
            exclude_set = set(c.value if isinstance(c, RuleCategory) else c for c in exclude_categories)
            result = [
                s for s in result
                if (s.category.value if isinstance(s.category, RuleCategory) else s.category) not in exclude_set
            ]

        return result

    async def generate_suggestions(
        self,
        source: Source,
        profile: Profile,
        schema: Schema | None = None,
        *,
        min_confidence: float = 0.5,
        strictness: StrictnessLevel = StrictnessLevel.MEDIUM,
        preset: RulePreset | None = None,
        include_categories: list[RuleCategory] | None = None,
        exclude_categories: list[RuleCategory] | None = None,
        enable_cross_column: bool = True,
        include_cross_column_types: list[CrossColumnRuleType] | None = None,
        exclude_cross_column_types: list[CrossColumnRuleType] | None = None,
    ) -> RuleSuggestionResponse:
        """Generate rule suggestions based on profile data.

        Args:
            source: Source record.
            profile: Profile record.
            schema: Optional schema for additional context.
            min_confidence: Minimum confidence threshold.
            strictness: Strictness level for rule thresholds.
            preset: Preset template to use.
            include_categories: Categories to include.
            exclude_categories: Categories to exclude.
            enable_cross_column: Whether to generate cross-column rules.
            include_cross_column_types: Cross-column types to include.
            exclude_cross_column_types: Cross-column types to exclude.

        Returns:
            Rule suggestion response.
        """
        suggestions: list[SuggestedRule] = []
        cross_column_suggestions: list[CrossColumnRuleSuggestion] = []

        # Apply preset settings if specified
        if preset:
            preset_info = PRESET_DEFINITIONS.get(preset)
            if preset_info:
                strictness = preset_info.strictness
                include_categories = preset_info.categories

        # Adjust min_confidence based on strictness
        thresholds = STRICTNESS_THRESHOLDS[strictness]
        effective_min_confidence = max(min_confidence, thresholds["min_confidence"])

        # Get columns from profile
        columns = profile.columns if hasattr(profile, "columns") else []
        if not columns and profile.profile_json:
            columns = profile.profile_json.get("columns", [])

        # Get schema columns for additional context
        schema_columns = {}
        if schema and schema.schema_json:
            schema_columns = schema.schema_json.get("columns", {})

        # Generate single-column suggestions for each column
        for column in columns:
            col_name = column.get("name", "")
            schema_col = schema_columns.get(col_name)

            # Collect all suggestions for this column with strictness
            suggestions.extend(self._suggest_null_rules(column, strictness))
            suggestions.extend(self._suggest_uniqueness_rules(column, strictness))
            suggestions.extend(self._suggest_range_rules(column, strictness))
            suggestions.extend(self._suggest_type_rules(column, schema_col, strictness))
            suggestions.extend(self._suggest_statistical_rules(column, strictness))

        # Filter by category
        suggestions = self._filter_by_category(
            suggestions, include_categories, exclude_categories
        )

        # Filter by confidence threshold
        suggestions = [s for s in suggestions if s.confidence >= effective_min_confidence]

        # Sort by confidence (highest first)
        suggestions.sort(key=lambda s: s.confidence, reverse=True)

        # Generate cross-column suggestions if enabled
        if enable_cross_column and columns:
            cross_column_suggestions = self._generate_cross_column_suggestions(
                columns,
                strictness,
                include_cross_column_types,
                exclude_cross_column_types,
            )
            # Filter by min confidence
            cross_column_suggestions = [
                s for s in cross_column_suggestions
                if s.confidence >= effective_min_confidence
            ]

        # Count high confidence suggestions (single + cross-column)
        high_confidence = sum(1 for s in suggestions if s.confidence >= 0.8)
        high_confidence += sum(1 for s in cross_column_suggestions if s.confidence >= 0.8)

        # Count by category
        by_category: dict[str, int] = {}
        for s in suggestions:
            cat_value = s.category.value if isinstance(s.category, RuleCategory) else str(s.category)
            by_category[cat_value] = by_category.get(cat_value, 0) + 1

        # Add cross-column categories
        if cross_column_suggestions:
            by_category["relationship"] = len([
                s for s in cross_column_suggestions
                if s.rule_type in (
                    CrossColumnRuleType.COLUMN_COMPARISON,
                    CrossColumnRuleType.COLUMN_DEPENDENCY,
                    CrossColumnRuleType.COLUMN_IMPLICATION,
                )
            ])
            by_category["multi_column"] = len([
                s for s in cross_column_suggestions
                if s.rule_type in (
                    CrossColumnRuleType.COMPOSITE_KEY,
                    CrossColumnRuleType.COLUMN_SUM,
                    CrossColumnRuleType.COLUMN_COEXISTENCE,
                    CrossColumnRuleType.COLUMN_MUTUAL_EXCLUSIVITY,
                )
            ])

        # Count by cross-column type
        by_cross_column_type: dict[str, int] = {}
        for s in cross_column_suggestions:
            type_value = s.rule_type.value
            by_cross_column_type[type_value] = by_cross_column_type.get(type_value, 0) + 1

        # Collect unique categories
        categories_included = list(set(
            s.category if isinstance(s.category, RuleCategory) else RuleCategory(s.category)
            for s in suggestions
        ))
        if cross_column_suggestions:
            if RuleCategory.RELATIONSHIP not in categories_included:
                categories_included.append(RuleCategory.RELATIONSHIP)
            if RuleCategory.MULTI_COLUMN not in categories_included:
                categories_included.append(RuleCategory.MULTI_COLUMN)

        # Total suggestions count
        total_suggestions = len(suggestions) + len(cross_column_suggestions)

        return RuleSuggestionResponse(
            source_id=source.id,
            source_name=source.name,
            profile_id=profile.id,
            suggestions=suggestions,
            cross_column_suggestions=cross_column_suggestions,
            total_suggestions=total_suggestions,
            high_confidence_count=high_confidence,
            cross_column_count=len(cross_column_suggestions),
            generated_at=datetime.utcnow(),
            strictness=strictness,
            preset=preset,
            categories_included=categories_included,
            by_category=by_category,
            by_cross_column_type=by_cross_column_type,
        )

    def _build_rules_dict(
        self, suggestions: list[SuggestedRule]
    ) -> tuple[dict[str, Any], list[str]]:
        """Build rules dictionary from suggestions.

        Args:
            suggestions: List of suggestions.

        Returns:
            Tuple of (rules dict, validator names).
        """
        rules_dict: dict[str, Any] = {"columns": {}}
        validators_applied = []

        for suggestion in suggestions:
            col_name = suggestion.column
            validator_name = suggestion.validator_name

            if col_name not in rules_dict["columns"]:
                rules_dict["columns"][col_name] = {}

            # Add validator with params
            if suggestion.params:
                rules_dict["columns"][col_name][validator_name.lower()] = suggestion.params
            else:
                rules_dict["columns"][col_name][validator_name.lower()] = True

            validators_applied.append(validator_name)

        return rules_dict, validators_applied

    async def apply_suggestions(
        self,
        source: Source,
        suggestions: list[SuggestedRule],
        *,
        rule_name: str | None = None,
        rule_description: str | None = None,
    ) -> ApplyRulesResponse:
        """Apply selected rule suggestions to create validation rules.

        Args:
            source: Source record.
            suggestions: Selected suggestions to apply.
            rule_name: Optional name for the rule set.
            rule_description: Optional description.

        Returns:
            Apply rules response.
        """
        # Build rules from suggestions
        rules_dict, validators_applied = self._build_rules_dict(suggestions)

        # Create YAML string
        rules_yaml = yaml.dump(rules_dict, default_flow_style=False)

        # Create rule record
        final_name = rule_name or f"Auto-generated rules for {source.name}"
        final_description = rule_description or (
            f"Automatically generated from profile analysis. "
            f"Includes {len(suggestions)} validators."
        )

        # Deactivate existing rules
        existing_rules = await self.rule_repo.get_for_source(
            source.id, active_only=True
        )
        for rule in existing_rules:
            rule.is_active = False

        # Create new rule
        rule = await self.rule_repo.create(
            source_id=source.id,
            name=final_name,
            description=final_description,
            rules_yaml=rules_yaml,
            rules_json=rules_dict,
            is_active=True,
        )

        await self.session.commit()

        return ApplyRulesResponse(
            source_id=source.id,
            rule_id=rule.id,
            rule_name=rule.name,
            applied_count=len(suggestions),
            validators=list(set(validators_applied)),
            created_at=rule.created_at,
        )

    def export_rules(
        self,
        suggestions: list[SuggestedRule],
        format: RuleExportFormat = RuleExportFormat.YAML,
        *,
        rule_name: str = "auto_generated_rules",
        description: str | None = None,
        include_metadata: bool = True,
    ) -> ExportRulesResponse:
        """Export rules in various formats.

        Args:
            suggestions: Rules to export.
            format: Export format.
            rule_name: Name for the rule set.
            description: Optional description.
            include_metadata: Include generation metadata.

        Returns:
            Export response with content.
        """
        rules_dict, validators = self._build_rules_dict(suggestions)

        # Add metadata if requested
        if include_metadata:
            rules_dict["_metadata"] = {
                "name": rule_name,
                "description": description or f"Auto-generated rules ({len(suggestions)} validators)",
                "generated_at": datetime.utcnow().isoformat(),
                "rule_count": len(suggestions),
                "validators": list(set(validators)),
            }

        # Generate content based on format
        if format == RuleExportFormat.YAML:
            content = yaml.dump(rules_dict, default_flow_style=False, sort_keys=False)
            filename = f"{rule_name}.yaml"
        elif format == RuleExportFormat.JSON:
            content = json.dumps(rules_dict, indent=2)
            filename = f"{rule_name}.json"
        elif format == RuleExportFormat.TOML:
            content = self._to_toml(rules_dict)
            filename = f"{rule_name}.toml"
        elif format == RuleExportFormat.PYTHON:
            content = self._to_python(rules_dict, rule_name, description)
            filename = f"{rule_name}.py"
        else:
            content = yaml.dump(rules_dict, default_flow_style=False)
            filename = f"{rule_name}.yaml"

        return ExportRulesResponse(
            content=content,
            format=format,
            filename=filename,
            rule_count=len(suggestions),
            generated_at=datetime.utcnow(),
        )

    def _to_toml(self, rules_dict: dict[str, Any]) -> str:
        """Convert rules to TOML format.

        Args:
            rules_dict: Rules dictionary.

        Returns:
            TOML string.
        """
        try:
            import toml
            return toml.dumps(rules_dict)
        except ImportError:
            # Fallback to simple TOML generation
            lines = []
            if "_metadata" in rules_dict:
                lines.append("[_metadata]")
                for k, v in rules_dict["_metadata"].items():
                    if isinstance(v, str):
                        lines.append(f'{k} = "{v}"')
                    elif isinstance(v, list):
                        lines.append(f'{k} = {json.dumps(v)}')
                    else:
                        lines.append(f"{k} = {v}")
                lines.append("")

            if "columns" in rules_dict:
                for col_name, validators in rules_dict["columns"].items():
                    lines.append(f'[columns."{col_name}"]')
                    for val_name, val_config in validators.items():
                        if isinstance(val_config, dict):
                            lines.append(f"[columns.\"{col_name}\".{val_name}]")
                            for pk, pv in val_config.items():
                                if isinstance(pv, str):
                                    lines.append(f'{pk} = "{pv}"')
                                else:
                                    lines.append(f"{pk} = {pv}")
                        else:
                            lines.append(f"{val_name} = {str(val_config).lower()}")
                    lines.append("")

            return "\n".join(lines)

    def _to_python(
        self,
        rules_dict: dict[str, Any],
        rule_name: str,
        description: str | None,
    ) -> str:
        """Convert rules to Python code.

        Args:
            rules_dict: Rules dictionary.
            rule_name: Name for the validation suite.
            description: Optional description.

        Returns:
            Python code string.
        """
        lines = [
            '"""Auto-generated validation rules.',
            "",
            f"Name: {rule_name}",
        ]
        if description:
            lines.append(f"Description: {description}")
        lines.extend([
            '"""',
            "",
            "from truthound import th",
            "",
            "",
            f"def validate_{rule_name.replace('-', '_').replace(' ', '_')}(df):",
            f'    """Run auto-generated validation rules."""',
            "    result = th.check(",
            "        df,",
            "        validators=[",
        ])

        # Add validators
        for col_name, validators in rules_dict.get("columns", {}).items():
            for val_name, val_config in validators.items():
                if isinstance(val_config, dict):
                    params_str = ", ".join(
                        f"{k}={repr(v)}" for k, v in val_config.items()
                    )
                    lines.append(f'            ("{col_name}", "{val_name}", {{{params_str}}}),')
                else:
                    lines.append(f'            ("{col_name}", "{val_name}"),')

        lines.extend([
            "        ],",
            "    )",
            "    return result",
            "",
            "",
            'if __name__ == "__main__":',
            "    import pandas as pd",
            "    # df = pd.read_csv('your_data.csv')",
            f"    # result = validate_{rule_name.replace('-', '_').replace(' ', '_')}(df)",
            "    # print(result)",
            "",
        ])

        return "\n".join(lines)

    @staticmethod
    def get_presets() -> PresetsResponse:
        """Get available presets and configuration options.

        Returns:
            Presets response.
        """
        return PresetsResponse(
            presets=list(PRESET_DEFINITIONS.values()),
            strictness_levels=[level.value for level in StrictnessLevel],
            categories=[cat.value for cat in RuleCategory],
            export_formats=[fmt.value for fmt in RuleExportFormat],
        )
