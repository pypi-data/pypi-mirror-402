"""Completeness validators.

Validators for detecting missing values, empty data, and placeholder values.
"""

from .base import (
    ParameterDefinition,
    ParameterType,
    ValidatorCategory,
    ValidatorDefinition,
)

COMPLETENESS_VALIDATORS: list[ValidatorDefinition] = [
    ValidatorDefinition(
        name="Null",
        display_name="Null Values",
        category=ValidatorCategory.COMPLETENESS,
        description="Detects and reports null values within specified columns.",
        parameters=[
            ParameterDefinition(
                name="columns",
                label="Columns",
                type=ParameterType.COLUMN_LIST,
                description="Target columns (leave empty for all columns)",
            ),
            ParameterDefinition(
                name="mostly",
                label="Mostly (Threshold)",
                type=ParameterType.FLOAT,
                description="Acceptable non-null ratio (0.0-1.0). E.g., 0.95 means 5% nulls allowed.",
                min_value=0,
                max_value=1,
                placeholder="0.95",
            ),
        ],
        tags=["completeness", "null", "missing"],
        severity_default="high",
    ),
    ValidatorDefinition(
        name="NotNull",
        display_name="Not Null",
        category=ValidatorCategory.COMPLETENESS,
        description="Ensures the specified column contains no null values.",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                description="Column that must not contain nulls",
                required=True,
            ),
        ],
        tags=["completeness", "null", "required"],
        severity_default="critical",
    ),
    ValidatorDefinition(
        name="CompletenessRatio",
        display_name="Completeness Ratio",
        category=ValidatorCategory.COMPLETENESS,
        description="Validates that the completeness ratio meets a minimum threshold.",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
            ),
            ParameterDefinition(
                name="min_ratio",
                label="Minimum Ratio",
                type=ParameterType.FLOAT,
                description="Minimum completeness ratio (0.0-1.0)",
                required=True,
                min_value=0,
                max_value=1,
                default=0.95,
            ),
        ],
        tags=["completeness", "ratio", "threshold"],
        severity_default="medium",
    ),
    ValidatorDefinition(
        name="EmptyString",
        display_name="Empty String",
        category=ValidatorCategory.COMPLETENESS,
        description="Detects empty strings in string columns.",
        parameters=[
            ParameterDefinition(
                name="columns",
                label="Columns",
                type=ParameterType.COLUMN_LIST,
                description="Target string columns (leave empty for all string columns)",
            ),
        ],
        tags=["completeness", "empty", "string"],
        severity_default="medium",
    ),
    ValidatorDefinition(
        name="WhitespaceOnly",
        display_name="Whitespace Only",
        category=ValidatorCategory.COMPLETENESS,
        description="Identifies values containing only whitespace characters.",
        parameters=[
            ParameterDefinition(
                name="columns",
                label="Columns",
                type=ParameterType.COLUMN_LIST,
                description="Target columns to check",
            ),
        ],
        tags=["completeness", "whitespace", "string"],
        severity_default="low",
    ),
    ValidatorDefinition(
        name="ConditionalNull",
        display_name="Conditional Null",
        category=ValidatorCategory.COMPLETENESS,
        description="Validates null values based on conditional logic.",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                description="Column to check for nulls",
                required=True,
            ),
            ParameterDefinition(
                name="condition",
                label="Condition Expression",
                type=ParameterType.EXPRESSION,
                description="Polars expression defining when column must not be null",
                required=True,
                placeholder='status == "active"',
            ),
        ],
        tags=["completeness", "conditional", "null"],
        severity_default="high",
    ),
    ValidatorDefinition(
        name="DefaultValue",
        display_name="Default Value Detection",
        category=ValidatorCategory.COMPLETENESS,
        description="Detects values matching default or placeholder patterns.",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
            ),
            ParameterDefinition(
                name="default_values",
                label="Default Values",
                type=ParameterType.STRING_LIST,
                description="Values considered as defaults/placeholders",
                required=True,
                placeholder="N/A, TBD, unknown, -1",
            ),
        ],
        tags=["completeness", "default", "placeholder"],
        severity_default="low",
    ),
    ValidatorDefinition(
        name="RequiredFields",
        display_name="Required Fields",
        category=ValidatorCategory.COMPLETENESS,
        description="Validates that all specified fields have non-null, non-empty values.",
        parameters=[
            ParameterDefinition(
                name="columns",
                label="Required Columns",
                type=ParameterType.COLUMN_LIST,
                description="Columns that must have values",
                required=True,
            ),
            ParameterDefinition(
                name="treat_empty_as_null",
                label="Treat Empty as Null",
                type=ParameterType.BOOLEAN,
                description="Consider empty strings as missing values",
                default=True,
            ),
        ],
        tags=["completeness", "required", "mandatory"],
        severity_default="critical",
    ),
    ValidatorDefinition(
        name="ConditionalRequired",
        display_name="Conditional Required",
        category=ValidatorCategory.COMPLETENESS,
        description="Requires a field when another field meets a condition.",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Required Column",
                type=ParameterType.COLUMN,
                description="Column that must have a value when condition is met",
                required=True,
            ),
            ParameterDefinition(
                name="when_column",
                label="Condition Column",
                type=ParameterType.COLUMN,
                description="Column to check for the condition",
                required=True,
            ),
            ParameterDefinition(
                name="when_value",
                label="Condition Value",
                type=ParameterType.STRING,
                description="Value that triggers the requirement",
                required=True,
            ),
        ],
        tags=["completeness", "conditional", "required"],
        severity_default="high",
    ),
    ValidatorDefinition(
        name="MutualCompleteness",
        display_name="Mutual Completeness",
        category=ValidatorCategory.COMPLETENESS,
        description="Ensures columns are either all null or all non-null together.",
        parameters=[
            ParameterDefinition(
                name="columns",
                label="Columns",
                type=ParameterType.COLUMN_LIST,
                description="Columns that must have mutual completeness",
                required=True,
            ),
        ],
        tags=["completeness", "mutual", "coexistence"],
        severity_default="medium",
    ),
    ValidatorDefinition(
        name="AtLeastOneNotNull",
        display_name="At Least One Not Null",
        category=ValidatorCategory.COMPLETENESS,
        description="Ensures at least one column in a group has a non-null value.",
        parameters=[
            ParameterDefinition(
                name="columns",
                label="Columns",
                type=ParameterType.COLUMN_LIST,
                description="Column group where at least one must be non-null",
                required=True,
            ),
        ],
        tags=["completeness", "at_least_one", "group"],
        severity_default="medium",
    ),
    ValidatorDefinition(
        name="ExactlyOneNotNull",
        display_name="Exactly One Not Null",
        category=ValidatorCategory.COMPLETENESS,
        description="Ensures exactly one column in a group has a non-null value.",
        parameters=[
            ParameterDefinition(
                name="columns",
                label="Columns",
                type=ParameterType.COLUMN_LIST,
                description="Column group where exactly one must be non-null",
                required=True,
            ),
        ],
        tags=["completeness", "exactly_one", "mutex"],
        severity_default="medium",
    ),
]
