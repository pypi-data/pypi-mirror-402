"""CSV report generator.

Generates CSV reports suitable for data analysis and spreadsheet tools.
"""

from __future__ import annotations

import csv
import io
from typing import TYPE_CHECKING, Any

from .base import Reporter, ReportFormat, ReportMetadata

if TYPE_CHECKING:
    from truthound_dashboard.db.models import Validation


class CSVReporter(Reporter):
    """CSV report generator.

    Produces CSV files with validation issues and statistics.
    Supports customizable delimiters and encoding.
    """

    def __init__(
        self,
        delimiter: str = ",",
        include_header: bool = True,
        encoding: str = "utf-8",
    ) -> None:
        """Initialize CSV reporter.

        Args:
            delimiter: CSV delimiter character.
            include_header: Whether to include column headers.
            encoding: Output encoding.
        """
        self._delimiter = delimiter
        self._include_header = include_header
        self._encoding = encoding

    @property
    def format(self) -> ReportFormat:
        return ReportFormat.CSV

    @property
    def content_type(self) -> str:
        return f"text/csv; charset={self._encoding}"

    @property
    def file_extension(self) -> str:
        return ".csv"

    async def _render_content(
        self,
        validation: Validation,
        metadata: ReportMetadata,
        include_samples: bool,
        include_statistics: bool,
    ) -> str:
        """Render CSV report content."""
        output = io.StringIO()
        writer = csv.writer(output, delimiter=self._delimiter)

        # Write metadata section
        writer.writerow(["# Validation Report"])
        writer.writerow(["# Source", metadata.source_name or validation.source_id])
        writer.writerow(["# Validation ID", validation.id])
        writer.writerow(["# Generated At", metadata.generated_at.isoformat()])
        writer.writerow(
            [
                "# Status",
                "PASSED" if validation.passed else "FAILED",
            ]
        )
        writer.writerow([])  # Empty row separator

        # Write statistics section if requested
        if include_statistics:
            writer.writerow(["# Statistics"])
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Row Count", validation.row_count or "N/A"])
            writer.writerow(["Column Count", validation.column_count or "N/A"])
            writer.writerow(["Total Issues", validation.total_issues or 0])
            writer.writerow(["Critical Issues", validation.critical_issues or 0])
            writer.writerow(["High Issues", validation.high_issues or 0])
            writer.writerow(["Medium Issues", validation.medium_issues or 0])
            writer.writerow(["Low Issues", validation.low_issues or 0])
            writer.writerow(
                [
                    "Duration (ms)",
                    validation.duration_ms if validation.duration_ms else "N/A",
                ]
            )
            writer.writerow([])  # Empty row separator

        # Write issues section
        issues = self._extract_issues(validation)
        writer.writerow(["# Issues"])

        # Define headers based on options
        headers = ["Column", "Issue Type", "Severity", "Count", "Details"]
        if include_samples:
            headers.append("Sample Values")

        if self._include_header:
            writer.writerow(headers)

        # Write issue rows
        for issue in issues:
            row = [
                issue.get("column", ""),
                issue.get("issue_type", ""),
                issue.get("severity", ""),
                issue.get("count", 0),
                issue.get("details", "") or "",
            ]
            if include_samples:
                samples = issue.get("sample_values", [])
                samples_str = "; ".join(str(v)[:50] for v in samples[:5])
                row.append(samples_str)

            writer.writerow(row)

        return output.getvalue()


class ExcelCSVReporter(CSVReporter):
    """CSV reporter optimized for Microsoft Excel.

    Uses UTF-8 BOM for proper encoding detection and semicolon delimiter
    for better compatibility with Excel's regional settings.
    """

    def __init__(self) -> None:
        """Initialize Excel-optimized CSV reporter."""
        super().__init__(delimiter=";", include_header=True, encoding="utf-8-sig")

    @property
    def file_extension(self) -> str:
        return ".csv"

    async def _render_content(
        self,
        validation: Validation,
        metadata: ReportMetadata,
        include_samples: bool,
        include_statistics: bool,
    ) -> str:
        """Render CSV with BOM for Excel."""
        content = await super()._render_content(
            validation, metadata, include_samples, include_statistics
        )
        # Add UTF-8 BOM for Excel
        return "\ufeff" + content
