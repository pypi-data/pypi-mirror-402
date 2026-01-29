"""Report generation system with multiple format support.

This module provides an extensible reporter system for generating
validation reports in various formats (HTML, CSV, Markdown, JSON, PDF).

The reporter system uses the Strategy pattern for format flexibility
and Template Method pattern for consistent report structure.

Example:
    from truthound_dashboard.core.reporters import get_reporter, ReportFormat

    reporter = get_reporter(ReportFormat.HTML)
    report = await reporter.generate(validation)

    # Or use the convenience function
    from truthound_dashboard.core.reporters import generate_report
    report = await generate_report(validation, format="html")
"""

from .base import (
    Reporter,
    ReportFormat,
    ReportMetadata,
    ReportResult,
    ReportTheme,
)
from .csv_reporter import CSVReporter
from .html_reporter import HTMLReporter
from .json_reporter import JSONReporter
from .markdown_reporter import MarkdownReporter
from .registry import (
    ReporterRegistry,
    generate_report,
    get_available_formats,
    get_reporter,
    register_reporter,
)

__all__ = [
    # Base classes
    "Reporter",
    "ReportFormat",
    "ReportMetadata",
    "ReportResult",
    "ReportTheme",
    # Implementations
    "CSVReporter",
    "HTMLReporter",
    "JSONReporter",
    "MarkdownReporter",
    # Registry
    "ReporterRegistry",
    "generate_report",
    "get_available_formats",
    "get_reporter",
    "register_reporter",
]
