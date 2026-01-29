"""Markdown report generator.

Generates Markdown reports suitable for documentation, GitHub,
and other platforms that render Markdown.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import Reporter, ReportFormat, ReportMetadata, ReportTheme

if TYPE_CHECKING:
    from truthound_dashboard.db.models import Validation


class MarkdownReporter(Reporter):
    """Markdown report generator.

    Produces GitHub-flavored Markdown reports with tables and badges.
    """

    def __init__(self, flavor: str = "github") -> None:
        """Initialize Markdown reporter.

        Args:
            flavor: Markdown flavor (github, standard).
        """
        self._flavor = flavor

    @property
    def format(self) -> ReportFormat:
        return ReportFormat.MARKDOWN

    @property
    def content_type(self) -> str:
        return "text/markdown; charset=utf-8"

    @property
    def file_extension(self) -> str:
        return ".md"

    async def _render_content(
        self,
        validation: Validation,
        metadata: ReportMetadata,
        include_samples: bool,
        include_statistics: bool,
    ) -> str:
        """Render Markdown report content."""
        sections = []

        # Header
        sections.append(self._render_header(validation, metadata))

        # Status badge
        sections.append(self._render_status_badge(validation))

        # Summary
        sections.append(self._render_summary(validation))

        # Statistics
        if include_statistics:
            sections.append(self._render_statistics(validation))

        # Issues table
        issues = self._extract_issues(validation)
        sections.append(self._render_issues_table(issues, include_samples))

        # Footer
        sections.append(self._render_footer(metadata))

        return "\n\n".join(filter(None, sections))

    def _render_header(self, validation: Validation, metadata: ReportMetadata) -> str:
        """Render report header."""
        source_name = metadata.source_name or validation.source_id
        generated = metadata.generated_at.strftime("%Y-%m-%d %H:%M:%S UTC")

        return f"""# {metadata.title}

**Source:** {source_name}
**Generated:** {generated}
**Validation ID:** `{validation.id}`"""

    def _render_status_badge(self, validation: Validation) -> str:
        """Render status badge."""
        if validation.passed:
            badge = "![Status](https://img.shields.io/badge/Status-PASSED-success)"
        else:
            badge = "![Status](https://img.shields.io/badge/Status-FAILED-critical)"

        return badge

    def _render_summary(self, validation: Validation) -> str:
        """Render validation summary."""
        return f"""## Summary

| Metric | Count |
|--------|-------|
| Total Issues | {validation.total_issues or 0} |
| Critical | {validation.critical_issues or 0} |
| High | {validation.high_issues or 0} |
| Medium | {validation.medium_issues or 0} |
| Low | {validation.low_issues or 0} |"""

    def _render_statistics(self, validation: Validation) -> str:
        """Render data statistics."""
        duration = validation.duration_ms
        duration_str = f"{duration / 1000:.2f}s" if duration else "N/A"

        started = (
            validation.started_at.strftime("%Y-%m-%d %H:%M:%S")
            if validation.started_at
            else "N/A"
        )
        completed = (
            validation.completed_at.strftime("%Y-%m-%d %H:%M:%S")
            if validation.completed_at
            else "N/A"
        )

        row_count = f"{validation.row_count:,}" if validation.row_count else "N/A"

        return f"""## Statistics

| Metric | Value |
|--------|-------|
| Row Count | {row_count} |
| Column Count | {validation.column_count or 'N/A'} |
| Duration | {duration_str} |
| Status | {validation.status} |
| Started At | {started} |
| Completed At | {completed} |"""

    def _render_issues_table(
        self, issues: list[dict[str, Any]], include_samples: bool
    ) -> str:
        """Render issues as Markdown table."""
        if not issues:
            return """## Issues

No issues found. All validations passed."""

        # Build table header
        headers = ["Column", "Issue Type", "Severity", "Count", "Details"]
        if include_samples:
            headers.append("Samples")

        header_row = "| " + " | ".join(headers) + " |"
        separator = "| " + " | ".join(["---"] * len(headers)) + " |"

        # Build rows
        rows = []
        for issue in issues:
            severity = issue.get("severity", "medium")
            severity_badge = self._get_severity_badge(severity)

            row = [
                f"`{issue.get('column', 'N/A')}`",
                issue.get("issue_type", "Unknown"),
                severity_badge,
                str(issue.get("count", 0)),
                (issue.get("details", "") or "")[:50],
            ]

            if include_samples:
                samples = issue.get("sample_values", [])
                samples_str = ", ".join(str(v)[:20] for v in samples[:3])
                if samples_str:
                    samples_str = f"`{samples_str}`"
                row.append(samples_str or "-")

            rows.append("| " + " | ".join(row) + " |")

        return f"""## Issues ({len(issues)})

{header_row}
{separator}
{chr(10).join(rows)}"""

    def _get_severity_badge(self, severity: str) -> str:
        """Get Markdown badge for severity level.

        Args:
            severity: Severity level.

        Returns:
            Markdown badge string.
        """
        colors = {
            "critical": "critical",
            "high": "orange",
            "medium": "yellow",
            "low": "blue",
        }
        color = colors.get(severity.lower(), "lightgrey")

        if self._flavor == "github":
            return f"![{severity}](https://img.shields.io/badge/{severity}-{color})"
        return f"**{severity.upper()}**"

    def _render_footer(self, metadata: ReportMetadata) -> str:
        """Render report footer."""
        return """---

*Generated by [Truthound Dashboard](https://github.com/truthound/truthound-dashboard)*"""
