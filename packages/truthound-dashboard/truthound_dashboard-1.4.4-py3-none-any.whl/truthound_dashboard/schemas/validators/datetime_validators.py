"""Datetime validators.

Validators for date/time format, range, ordering, and freshness.
"""

from .base import (
    ParameterDefinition,
    ParameterType,
    ValidatorCategory,
    ValidatorDefinition,
)

DATETIME_VALIDATORS: list[ValidatorDefinition] = [
    ValidatorDefinition(
        name="DateFormat",
        display_name="Date Format",
        category=ValidatorCategory.DATETIME,
        description="Validates date/datetime format.",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
            ),
            ParameterDefinition(
                name="format",
                label="Date Format",
                type=ParameterType.STRING,
                description="Expected strptime format",
                required=True,
                placeholder="%Y-%m-%d",
            ),
        ],
        tags=["datetime", "format"],
        severity_default="medium",
    ),
    ValidatorDefinition(
        name="DateBetween",
        display_name="Date Between",
        category=ValidatorCategory.DATETIME,
        description="Validates dates within a specified range.",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
            ),
            ParameterDefinition(
                name="min_date",
                label="Minimum Date",
                type=ParameterType.DATE,
                description="Minimum date (YYYY-MM-DD)",
                placeholder="2020-01-01",
            ),
            ParameterDefinition(
                name="max_date",
                label="Maximum Date",
                type=ParameterType.DATE,
                description="Maximum date (YYYY-MM-DD)",
                placeholder="2025-12-31",
            ),
        ],
        tags=["datetime", "range", "bounds"],
        severity_default="medium",
    ),
    ValidatorDefinition(
        name="FutureDate",
        display_name="Future Date",
        category=ValidatorCategory.DATETIME,
        description="Ensures dates are in the future.",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
            ),
        ],
        tags=["datetime", "future"],
        severity_default="medium",
    ),
    ValidatorDefinition(
        name="PastDate",
        display_name="Past Date",
        category=ValidatorCategory.DATETIME,
        description="Ensures dates are in the past.",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
            ),
        ],
        tags=["datetime", "past"],
        severity_default="medium",
    ),
    ValidatorDefinition(
        name="DateOrder",
        display_name="Date Order",
        category=ValidatorCategory.DATETIME,
        description="Validates chronological ordering between date columns.",
        parameters=[
            ParameterDefinition(
                name="start_column",
                label="Start Date Column",
                type=ParameterType.COLUMN,
                required=True,
            ),
            ParameterDefinition(
                name="end_column",
                label="End Date Column",
                type=ParameterType.COLUMN,
                required=True,
            ),
        ],
        tags=["datetime", "order", "chronological"],
        severity_default="high",
    ),
    ValidatorDefinition(
        name="Timezone",
        display_name="Timezone",
        category=ValidatorCategory.DATETIME,
        description="Validates timezone-aware datetime values.",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
            ),
            ParameterDefinition(
                name="expected_timezone",
                label="Expected Timezone",
                type=ParameterType.STRING,
                description="Expected timezone (e.g., 'UTC', 'America/New_York')",
                placeholder="UTC",
            ),
        ],
        tags=["datetime", "timezone"],
        severity_default="low",
    ),
    ValidatorDefinition(
        name="RecentData",
        display_name="Recent Data",
        category=ValidatorCategory.DATETIME,
        description="Ensures data contains recent entries.",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Datetime Column",
                type=ParameterType.COLUMN,
                required=True,
            ),
            ParameterDefinition(
                name="max_age_days",
                label="Maximum Age (Days)",
                type=ParameterType.INTEGER,
                description="Maximum age in days",
                required=True,
                min_value=1,
            ),
        ],
        tags=["datetime", "recent", "freshness"],
        severity_default="high",
    ),
    ValidatorDefinition(
        name="DatePartCoverage",
        display_name="Date Part Coverage",
        category=ValidatorCategory.DATETIME,
        description="Validates coverage across date parts.",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Datetime Column",
                type=ParameterType.COLUMN,
                required=True,
            ),
            ParameterDefinition(
                name="date_part",
                label="Date Part",
                type=ParameterType.SELECT,
                required=True,
                options=[
                    {"value": "day", "label": "Day of Month"},
                    {"value": "weekday", "label": "Day of Week"},
                    {"value": "month", "label": "Month"},
                    {"value": "hour", "label": "Hour"},
                    {"value": "quarter", "label": "Quarter"},
                ],
            ),
            ParameterDefinition(
                name="min_coverage",
                label="Minimum Coverage",
                type=ParameterType.FLOAT,
                description="Minimum coverage ratio (0.0-1.0)",
                required=True,
                min_value=0,
                max_value=1,
            ),
        ],
        tags=["datetime", "coverage", "completeness"],
        severity_default="medium",
    ),
    ValidatorDefinition(
        name="GroupedRecentData",
        display_name="Grouped Recent Data",
        category=ValidatorCategory.DATETIME,
        description="Validates recency within groups.",
        parameters=[
            ParameterDefinition(
                name="datetime_column",
                label="Datetime Column",
                type=ParameterType.COLUMN,
                required=True,
            ),
            ParameterDefinition(
                name="group_column",
                label="Group Column",
                type=ParameterType.COLUMN,
                required=True,
            ),
            ParameterDefinition(
                name="max_age_days",
                label="Maximum Age (Days)",
                type=ParameterType.INTEGER,
                description="Maximum age per group in days",
                required=True,
                min_value=1,
            ),
        ],
        tags=["datetime", "recent", "group"],
        severity_default="high",
    ),
    ValidatorDefinition(
        name="DatetimeParseable",
        display_name="Datetime Parseable",
        category=ValidatorCategory.DATETIME,
        description="Validates that strings can be parsed as dates using dateutil.",
        parameters=[
            ParameterDefinition(
                name="column",
                label="Column",
                type=ParameterType.COLUMN,
                required=True,
            ),
        ],
        tags=["datetime", "parseable", "format"],
        severity_default="medium",
    ),
]
