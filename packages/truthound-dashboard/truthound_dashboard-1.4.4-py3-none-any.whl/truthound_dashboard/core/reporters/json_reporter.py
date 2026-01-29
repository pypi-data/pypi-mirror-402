"""JSON report generator.

Generates machine-readable JSON reports suitable for API consumption
and integration with other tools.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any

from .base import Reporter, ReportFormat, ReportMetadata

if TYPE_CHECKING:
    from truthound_dashboard.db.models import Validation


class JSONReporter(Reporter):
    """JSON report generator.

    Produces structured JSON reports with complete validation data.
    Supports pretty printing and compact output modes.
    """

    def __init__(
        self,
        indent: int | None = 2,
        ensure_ascii: bool = False,
    ) -> None:
        """Initialize JSON reporter.

        Args:
            indent: Indentation for pretty printing. None for compact output.
            ensure_ascii: Whether to escape non-ASCII characters.
        """
        self._indent = indent
        self._ensure_ascii = ensure_ascii

    @property
    def format(self) -> ReportFormat:
        return ReportFormat.JSON

    @property
    def content_type(self) -> str:
        return "application/json; charset=utf-8"

    @property
    def file_extension(self) -> str:
        return ".json"

    async def _render_content(
        self,
        validation: Validation,
        metadata: ReportMetadata,
        include_samples: bool,
        include_statistics: bool,
    ) -> str:
        """Render JSON report content."""
        issues = self._extract_issues(validation)

        # Process issues to optionally remove samples
        if not include_samples:
            issues = [
                {k: v for k, v in issue.items() if k != "sample_values"}
                for issue in issues
            ]

        report_data: dict[str, Any] = {
            "metadata": {
                "title": metadata.title,
                "generated_at": metadata.generated_at.isoformat(),
                "format": metadata.format.value,
                "theme": metadata.theme.value,
            },
            "validation": {
                "id": validation.id,
                "source_id": validation.source_id,
                "source_name": metadata.source_name,
                "status": validation.status,
                "passed": validation.passed,
            },
            "summary": {
                "total_issues": validation.total_issues or 0,
                "critical_issues": validation.critical_issues or 0,
                "high_issues": validation.high_issues or 0,
                "medium_issues": validation.medium_issues or 0,
                "low_issues": validation.low_issues or 0,
                "has_critical": validation.has_critical or False,
                "has_high": validation.has_high or False,
            },
            "issues": issues,
        }

        # Add statistics if requested
        if include_statistics:
            report_data["statistics"] = {
                "row_count": validation.row_count,
                "column_count": validation.column_count,
                "duration_ms": validation.duration_ms,
                "started_at": (
                    validation.started_at.isoformat()
                    if validation.started_at
                    else None
                ),
                "completed_at": (
                    validation.completed_at.isoformat()
                    if validation.completed_at
                    else None
                ),
                "created_at": (
                    validation.created_at.isoformat()
                    if validation.created_at
                    else None
                ),
            }

        # Add error info if present
        if validation.error_message:
            report_data["error"] = {
                "message": validation.error_message,
            }

        return json.dumps(
            report_data,
            indent=self._indent,
            ensure_ascii=self._ensure_ascii,
            default=self._json_serializer,
        )

    def _json_serializer(self, obj: Any) -> Any:
        """Custom JSON serializer for non-serializable objects.

        Args:
            obj: Object to serialize.

        Returns:
            Serializable representation.

        Raises:
            TypeError: If object cannot be serialized.
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


class CompactJSONReporter(JSONReporter):
    """Compact JSON reporter without formatting.

    Produces minified JSON for reduced file size.
    """

    def __init__(self) -> None:
        """Initialize compact JSON reporter."""
        super().__init__(indent=None, ensure_ascii=False)
