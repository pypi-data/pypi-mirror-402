"""Aggregate validators.

Validators for column-level statistical verification.
"""

from .base import (
    ParameterDefinition,
    ParameterType,
    ValidatorCategory,
    ValidatorDefinition,
)

AGGREGATE_VALIDATORS: list[ValidatorDefinition] = [
    ValidatorDefinition(
        name="MeanBetween",
        display_name="Mean Between",
        category=ValidatorCategory.AGGREGATE,
        description="Validates that the column mean falls within a specified range.",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
            ),
            ParameterDefinition(
                name="min_value",
                label="Minimum Mean",
                type=ParameterType.FLOAT,
                description="Minimum acceptable mean value",
            ),
            ParameterDefinition(
                name="max_value",
                label="Maximum Mean",
                type=ParameterType.FLOAT,
                description="Maximum acceptable mean value",
            ),
        ],
        tags=["aggregate", "mean", "average", "statistical"],
        severity_default="medium",
    ),
    ValidatorDefinition(
        name="MedianBetween",
        display_name="Median Between",
        category=ValidatorCategory.AGGREGATE,
        description="Validates that the column median falls within a specified range.",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
            ),
            ParameterDefinition(
                name="min_value",
                label="Minimum Median",
                type=ParameterType.FLOAT,
                description="Minimum acceptable median value",
            ),
            ParameterDefinition(
                name="max_value",
                label="Maximum Median",
                type=ParameterType.FLOAT,
                description="Maximum acceptable median value",
            ),
        ],
        tags=["aggregate", "median", "statistical"],
        severity_default="medium",
    ),
    ValidatorDefinition(
        name="StdBetween",
        display_name="Standard Deviation Between",
        category=ValidatorCategory.AGGREGATE,
        description="Validates that the column standard deviation falls within a specified range.",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
            ),
            ParameterDefinition(
                name="min_value",
                label="Minimum Std Dev",
                type=ParameterType.FLOAT,
                description="Minimum acceptable standard deviation",
                min_value=0,
            ),
            ParameterDefinition(
                name="max_value",
                label="Maximum Std Dev",
                type=ParameterType.FLOAT,
                description="Maximum acceptable standard deviation",
                min_value=0,
            ),
        ],
        tags=["aggregate", "std", "standard_deviation", "statistical"],
        severity_default="medium",
    ),
    ValidatorDefinition(
        name="VarianceBetween",
        display_name="Variance Between",
        category=ValidatorCategory.AGGREGATE,
        description="Validates that the column variance falls within a specified range.",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
            ),
            ParameterDefinition(
                name="min_value",
                label="Minimum Variance",
                type=ParameterType.FLOAT,
                description="Minimum acceptable variance",
                min_value=0,
            ),
            ParameterDefinition(
                name="max_value",
                label="Maximum Variance",
                type=ParameterType.FLOAT,
                description="Maximum acceptable variance",
                min_value=0,
            ),
        ],
        tags=["aggregate", "variance", "statistical"],
        severity_default="medium",
    ),
    ValidatorDefinition(
        name="SumBetween",
        display_name="Sum Between",
        category=ValidatorCategory.AGGREGATE,
        description="Validates that the column sum falls within a specified range.",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
            ),
            ParameterDefinition(
                name="min_value",
                label="Minimum Sum",
                type=ParameterType.FLOAT,
                description="Minimum acceptable sum value",
            ),
            ParameterDefinition(
                name="max_value",
                label="Maximum Sum",
                type=ParameterType.FLOAT,
                description="Maximum acceptable sum value",
            ),
        ],
        tags=["aggregate", "sum", "total", "statistical"],
        severity_default="medium",
    ),
    ValidatorDefinition(
        name="MinBetween",
        display_name="Min Value Between",
        category=ValidatorCategory.AGGREGATE,
        description="Validates that the column minimum value falls within a specified range.",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
            ),
            ParameterDefinition(
                name="min_value",
                label="Minimum of Min",
                type=ParameterType.FLOAT,
                description="Lower bound for the column minimum",
            ),
            ParameterDefinition(
                name="max_value",
                label="Maximum of Min",
                type=ParameterType.FLOAT,
                description="Upper bound for the column minimum",
            ),
        ],
        tags=["aggregate", "min", "minimum", "bounds"],
        severity_default="medium",
    ),
    ValidatorDefinition(
        name="MaxBetween",
        display_name="Max Value Between",
        category=ValidatorCategory.AGGREGATE,
        description="Validates that the column maximum value falls within a specified range.",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
            ),
            ParameterDefinition(
                name="min_value",
                label="Minimum of Max",
                type=ParameterType.FLOAT,
                description="Lower bound for the column maximum",
            ),
            ParameterDefinition(
                name="max_value",
                label="Maximum of Max",
                type=ParameterType.FLOAT,
                description="Upper bound for the column maximum",
            ),
        ],
        tags=["aggregate", "max", "maximum", "bounds"],
        severity_default="medium",
    ),
    ValidatorDefinition(
        name="CountBetween",
        display_name="Count Between",
        category=ValidatorCategory.AGGREGATE,
        description="Validates that the row count falls within a specified range.",
        parameters=[
            ParameterDefinition(
                name="min_count",
                label="Minimum Count",
                type=ParameterType.INTEGER,
                description="Minimum acceptable row count",
                min_value=0,
            ),
            ParameterDefinition(
                name="max_count",
                label="Maximum Count",
                type=ParameterType.INTEGER,
                description="Maximum acceptable row count",
                min_value=0,
            ),
        ],
        tags=["aggregate", "count", "rows"],
        severity_default="medium",
    ),
]
