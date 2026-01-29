"""Reporter registry and factory functions.

This module provides a central registry for report generators and
convenience functions for generating reports with i18n support.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .base import Reporter, ReportFormat, ReportResult, ReportTheme
from .i18n import SupportedLocale, get_supported_locales

if TYPE_CHECKING:
    from truthound_dashboard.db.models import Validation

logger = logging.getLogger(__name__)


class ReporterRegistry:
    """Registry for report generators.

    Maintains a mapping of formats to reporter implementations.
    Supports custom reporter registration for extensibility.
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._reporters: dict[ReportFormat, type[Reporter]] = {}

    def register(
        self,
        format_type: ReportFormat,
        reporter_class: type[Reporter],
    ) -> None:
        """Register a reporter for a format.

        Args:
            format_type: Report format this reporter handles.
            reporter_class: Reporter class to register.
        """
        self._reporters[format_type] = reporter_class
        logger.debug(f"Registered reporter for format: {format_type.value}")

    def get(self, format_type: ReportFormat) -> Reporter:
        """Get a reporter instance for a format.

        Args:
            format_type: Desired report format.

        Returns:
            Reporter instance.

        Raises:
            ValueError: If no reporter is registered for the format.
        """
        reporter_class = self._reporters.get(format_type)
        if reporter_class is None:
            raise ValueError(
                f"No reporter registered for format: {format_type.value}. "
                f"Available formats: {self.available_formats}"
            )
        return reporter_class()

    @property
    def available_formats(self) -> list[str]:
        """Get list of available format names."""
        return [fmt.value for fmt in self._reporters.keys()]

    def is_registered(self, format_type: ReportFormat) -> bool:
        """Check if a format has a registered reporter.

        Args:
            format_type: Format to check.

        Returns:
            True if format is registered.
        """
        return format_type in self._reporters


# Global registry instance
_registry: ReporterRegistry | None = None


def get_registry() -> ReporterRegistry:
    """Get the global reporter registry.

    Initializes with default reporters on first call.

    Returns:
        Global ReporterRegistry instance.
    """
    global _registry
    if _registry is None:
        _registry = ReporterRegistry()
        _register_default_reporters(_registry)
    return _registry


def _register_default_reporters(registry: ReporterRegistry) -> None:
    """Register all built-in reporters.

    Args:
        registry: Registry to populate.

    Registers 6 reporters:
    - HTML: Rich visual reports with themes
    - CSV: Spreadsheet-compatible format
    - JSON: Machine-readable structured data
    - Markdown: Documentation-friendly format
    - PDF: Print-ready documents
    - JUnit: CI/CD integration (Jenkins, GitHub Actions, etc.)
    """
    from .csv_reporter import CSVReporter
    from .html_reporter import HTMLReporter
    from .json_reporter import JSONReporter
    from .junit_reporter import JUnitReporter
    from .markdown_reporter import MarkdownReporter
    from .pdf_reporter import PDFReporter

    registry.register(ReportFormat.HTML, HTMLReporter)
    registry.register(ReportFormat.CSV, CSVReporter)
    registry.register(ReportFormat.JSON, JSONReporter)
    registry.register(ReportFormat.MARKDOWN, MarkdownReporter)
    registry.register(ReportFormat.PDF, PDFReporter)
    registry.register(ReportFormat.JUNIT, JUnitReporter)

    logger.debug(f"Registered {len(registry.available_formats)} default reporters")


def register_reporter(
    format_type: ReportFormat,
    reporter_class: type[Reporter],
) -> None:
    """Register a custom reporter.

    Convenience function for registering custom reporters.

    Args:
        format_type: Report format to handle.
        reporter_class: Reporter class to register.
    """
    get_registry().register(format_type, reporter_class)


def get_reporter(
    format_type: ReportFormat | str,
    locale: SupportedLocale | str = SupportedLocale.ENGLISH,
) -> Reporter:
    """Get a reporter for a specific format with locale support.

    Args:
        format_type: Report format (enum or string).
        locale: Target locale for report generation.

    Returns:
        Reporter instance for the format.

    Raises:
        ValueError: If format is not recognized or not registered.
    """
    if isinstance(format_type, str):
        format_type = ReportFormat.from_string(format_type)

    # Get the reporter class from registry
    registry = get_registry()
    reporter_class = registry._reporters.get(format_type)

    if reporter_class is None:
        raise ValueError(
            f"No reporter registered for format: {format_type.value}. "
            f"Available formats: {registry.available_formats}"
        )

    # Convert locale string to enum
    if isinstance(locale, str):
        locale = SupportedLocale.from_string(locale)

    # Create reporter with locale if supported
    try:
        # Try to create with locale (for reporters that support it)
        return reporter_class(locale=locale)
    except TypeError:
        # Fall back to no-arg constructor for reporters without locale
        return reporter_class()


def get_available_formats() -> list[str]:
    """Get list of available report formats.

    Returns:
        List of format name strings.
    """
    return get_registry().available_formats


async def generate_report(
    validation: Validation,
    *,
    format: ReportFormat | str = ReportFormat.HTML,
    theme: ReportTheme | str = ReportTheme.PROFESSIONAL,
    locale: SupportedLocale | str = SupportedLocale.ENGLISH,
    title: str | None = None,
    include_samples: bool = True,
    include_statistics: bool = True,
    custom_metadata: dict[str, Any] | None = None,
) -> ReportResult:
    """Generate a report for a validation result.

    High-level convenience function for report generation with i18n support.

    Args:
        validation: Validation model with results.
        format: Output format (enum or string).
        theme: Visual theme (enum or string).
        locale: Report language (supports 15 languages).
        title: Custom report title.
        include_samples: Include sample problematic values.
        include_statistics: Include data statistics.
        custom_metadata: Additional metadata to include.

    Returns:
        ReportResult with generated content.

    Example:
        # Generate Korean HTML report with dark theme
        report = await generate_report(
            validation,
            format="html",
            theme="dark",
            locale="ko"
        )
        with open(report.filename, "w") as f:
            f.write(report.content)
    """
    # Convert string arguments to enums
    if isinstance(format, str):
        format = ReportFormat.from_string(format)
    if isinstance(theme, str):
        theme = ReportTheme(theme)

    reporter = get_reporter(format, locale=locale)

    return await reporter.generate(
        validation,
        theme=theme,
        title=title,
        include_samples=include_samples,
        include_statistics=include_statistics,
        custom_metadata=custom_metadata,
    )


def get_report_locales() -> list[dict[str, Any]]:
    """Get list of supported report locales.

    Returns:
        List of locale info dictionaries with code, name, and metadata.

    Example:
        locales = get_report_locales()
        # [{"code": "en", "english_name": "English", "native_name": "English", ...}, ...]
    """
    return get_supported_locales()


def reset_registry() -> None:
    """Reset the global registry (for testing)."""
    global _registry
    _registry = None
