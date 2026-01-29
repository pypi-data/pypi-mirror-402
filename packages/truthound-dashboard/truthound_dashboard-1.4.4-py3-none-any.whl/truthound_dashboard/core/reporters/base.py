"""Base classes for report generation system.

This module defines the abstract interfaces and data structures for
the reporter system.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from truthound_dashboard.db.models import Validation


class ReportFormat(str, Enum):
    """Supported report output formats."""

    HTML = "html"
    CSV = "csv"
    JSON = "json"
    MARKDOWN = "markdown"
    PDF = "pdf"
    JUNIT = "junit"  # JUnit XML for CI/CD integration

    @classmethod
    def from_string(cls, value: str) -> ReportFormat:
        """Parse format from string.

        Args:
            value: Format string (case-insensitive).

        Returns:
            ReportFormat enum value.

        Raises:
            ValueError: If format is not recognized.
        """
        value_lower = value.lower()
        for fmt in cls:
            if fmt.value == value_lower:
                return fmt
        raise ValueError(
            f"Unknown report format: {value}. "
            f"Supported formats: {[f.value for f in cls]}"
        )


class ReportTheme(str, Enum):
    """Report visual themes."""

    LIGHT = "light"
    DARK = "dark"
    PROFESSIONAL = "professional"
    MINIMAL = "minimal"
    HIGH_CONTRAST = "high_contrast"


@dataclass
class ReportMetadata:
    """Metadata for generated reports.

    Attributes:
        title: Report title.
        generated_at: Timestamp when report was generated.
        source_name: Name of the data source.
        validation_id: ID of the validation run.
        theme: Visual theme used.
        format: Output format.
        custom_fields: Additional custom metadata.
    """

    title: str = "Validation Report"
    generated_at: datetime = field(default_factory=datetime.utcnow)
    source_name: str | None = None
    source_id: str | None = None
    validation_id: str | None = None
    theme: ReportTheme = ReportTheme.PROFESSIONAL
    format: ReportFormat = ReportFormat.HTML
    custom_fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "generated_at": self.generated_at.isoformat(),
            "source_name": self.source_name,
            "source_id": self.source_id,
            "validation_id": self.validation_id,
            "theme": self.theme.value,
            "format": self.format.value,
            **self.custom_fields,
        }


@dataclass
class ReportResult:
    """Result of report generation.

    Attributes:
        content: Generated report content (string or bytes).
        metadata: Report metadata.
        content_type: MIME type of the content.
        filename: Suggested filename for download.
        size_bytes: Size of content in bytes.
        generation_time_ms: Time taken to generate in milliseconds.
    """

    content: str | bytes
    metadata: ReportMetadata
    content_type: str
    filename: str
    size_bytes: int = 0
    generation_time_ms: int = 0

    def __post_init__(self) -> None:
        """Calculate size if not set."""
        if self.size_bytes == 0:
            if isinstance(self.content, str):
                self.size_bytes = len(self.content.encode("utf-8"))
            else:
                self.size_bytes = len(self.content)


class Reporter(ABC):
    """Abstract base class for report generators.

    Subclass this to implement custom report formats.
    Uses Template Method pattern: generate() orchestrates the process,
    while subclasses implement format-specific rendering.
    """

    @property
    @abstractmethod
    def format(self) -> ReportFormat:
        """Get the report format this reporter produces."""
        ...

    @property
    @abstractmethod
    def content_type(self) -> str:
        """Get the MIME content type for this format."""
        ...

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Get the file extension for this format."""
        ...

    async def generate(
        self,
        validation: Validation,
        *,
        theme: ReportTheme = ReportTheme.PROFESSIONAL,
        title: str | None = None,
        include_samples: bool = True,
        include_statistics: bool = True,
        custom_metadata: dict[str, Any] | None = None,
    ) -> ReportResult:
        """Generate a report for a validation result.

        This is the main entry point (Template Method). Override
        _render_content() in subclasses for format-specific logic.

        Args:
            validation: Validation model with results.
            theme: Visual theme for the report.
            title: Custom report title.
            include_samples: Include sample problematic values.
            include_statistics: Include data statistics section.
            custom_metadata: Additional metadata to include.

        Returns:
            ReportResult with generated content.
        """
        import time

        start_time = time.time()

        # Build metadata
        metadata = ReportMetadata(
            title=title or f"Validation Report - {validation.source_id}",
            source_id=validation.source_id,
            validation_id=validation.id,
            theme=theme,
            format=self.format,
            custom_fields=custom_metadata or {},
        )

        # Try to get source name
        if hasattr(validation, "source") and validation.source:
            metadata.source_name = validation.source.name

        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"validation_report_{timestamp}{self.file_extension}"

        # Render content (subclass implementation)
        content = await self._render_content(
            validation=validation,
            metadata=metadata,
            include_samples=include_samples,
            include_statistics=include_statistics,
        )

        generation_time_ms = int((time.time() - start_time) * 1000)

        return ReportResult(
            content=content,
            metadata=metadata,
            content_type=self.content_type,
            filename=filename,
            generation_time_ms=generation_time_ms,
        )

    @abstractmethod
    async def _render_content(
        self,
        validation: Validation,
        metadata: ReportMetadata,
        include_samples: bool,
        include_statistics: bool,
    ) -> str | bytes:
        """Render the report content.

        Subclasses implement this to produce format-specific output.

        Args:
            validation: Validation model with results.
            metadata: Report metadata.
            include_samples: Whether to include sample values.
            include_statistics: Whether to include statistics.

        Returns:
            Rendered report content.
        """
        ...

    def _extract_issues(self, validation: Validation) -> list[dict[str, Any]]:
        """Extract issues from validation result.

        Args:
            validation: Validation model.

        Returns:
            List of issue dictionaries.
        """
        if validation.result_json and "issues" in validation.result_json:
            return validation.result_json["issues"]
        return []

    def _get_severity_color(self, severity: str, theme: ReportTheme) -> str:
        """Get color for severity level based on theme.

        Args:
            severity: Severity level (critical, high, medium, low).
            theme: Current theme.

        Returns:
            CSS color value.
        """
        # Base colors (work for most themes)
        colors = {
            "critical": "#dc2626",  # Red
            "high": "#ea580c",  # Orange
            "medium": "#ca8a04",  # Yellow/Gold
            "low": "#2563eb",  # Blue
        }

        # Adjust for dark theme
        if theme == ReportTheme.DARK:
            colors = {
                "critical": "#ef4444",
                "high": "#f97316",
                "medium": "#eab308",
                "low": "#3b82f6",
            }

        return colors.get(severity.lower(), "#6b7280")

    def _get_status_indicator(self, passed: bool | None) -> str:
        """Get status indicator text.

        Args:
            passed: Whether validation passed.

        Returns:
            Status indicator string.
        """
        if passed is None:
            return "⏳ Pending"
        return "✅ Passed" if passed else "❌ Failed"
