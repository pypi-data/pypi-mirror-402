"""PDF report generator.

Generates professional PDF reports using HTML-to-PDF conversion.
Supports multiple themes and includes all validation details.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .base import Reporter, ReportFormat, ReportMetadata, ReportTheme
from .html_reporter import HTMLReporter

if TYPE_CHECKING:
    from truthound_dashboard.db.models import Validation

logger = logging.getLogger(__name__)

# Check if weasyprint is available
_WEASYPRINT_AVAILABLE = False
try:
    import weasyprint  # noqa: F401
    _WEASYPRINT_AVAILABLE = True
except ImportError:
    logger.debug("weasyprint not available, PDF generation will use HTML fallback")


class PDFReporter(Reporter):
    """PDF report generator using HTML-to-PDF conversion.

    Uses weasyprint for high-quality PDF generation.
    Falls back to HTML if weasyprint is not installed.
    """

    def __init__(self) -> None:
        """Initialize PDF reporter with HTML reporter for content generation."""
        self._html_reporter = HTMLReporter()

    @property
    def format(self) -> ReportFormat:
        return ReportFormat.PDF

    @property
    def content_type(self) -> str:
        return "application/pdf"

    @property
    def file_extension(self) -> str:
        return ".pdf"

    @classmethod
    def is_available(cls) -> bool:
        """Check if PDF generation is available."""
        return _WEASYPRINT_AVAILABLE

    async def _render_content(
        self,
        validation: Validation,
        metadata: ReportMetadata,
        include_samples: bool,
        include_statistics: bool,
    ) -> bytes:
        """Render PDF report content.

        Uses HTML reporter to generate content, then converts to PDF.
        """
        # Generate HTML content using the HTML reporter
        html_content = await self._html_reporter._render_content(
            validation=validation,
            metadata=metadata,
            include_samples=include_samples,
            include_statistics=include_statistics,
        )

        # Add PDF-specific styles for better printing
        pdf_styles = self._get_pdf_styles(metadata.theme)
        html_content = html_content.replace(
            "</style>",
            f"{pdf_styles}\n    </style>"
        )

        # Convert HTML to PDF
        if _WEASYPRINT_AVAILABLE:
            return self._convert_to_pdf(html_content)
        else:
            # Return HTML as bytes if weasyprint is not available
            logger.warning(
                "weasyprint not installed. Install with: pip install weasyprint"
            )
            return html_content.encode("utf-8")

    def _get_pdf_styles(self, theme: ReportTheme) -> str:
        """Get additional CSS styles for PDF output."""
        return """
        /* PDF-specific styles */
        @page {
            size: A4;
            margin: 1.5cm;

            @top-center {
                content: "Truthound Validation Report";
                font-size: 10pt;
                color: #64748b;
            }

            @bottom-right {
                content: counter(page) " / " counter(pages);
                font-size: 10pt;
                color: #64748b;
            }
        }

        @page :first {
            @top-center { content: none; }
        }

        body {
            font-size: 11pt;
            line-height: 1.5;
        }

        .container {
            max-width: 100%;
        }

        .header {
            page-break-after: avoid;
        }

        .card {
            page-break-inside: avoid;
            margin-bottom: 0.75cm;
        }

        table {
            font-size: 10pt;
        }

        th, td {
            padding: 0.4rem 0.6rem;
        }

        .summary-grid {
            grid-template-columns: repeat(5, 1fr);
        }

        .summary-item .value {
            font-size: 1.5rem;
        }

        .footer {
            page-break-before: avoid;
            font-size: 9pt;
        }

        /* Remove hover effects for PDF */
        tr:hover {
            background: transparent !important;
        }

        /* Ensure badges print with colors */
        .severity-badge,
        .status-badge {
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }
        """

    def _convert_to_pdf(self, html_content: str) -> bytes:
        """Convert HTML content to PDF bytes.

        Args:
            html_content: HTML string to convert.

        Returns:
            PDF content as bytes.
        """
        try:
            import weasyprint
            from weasyprint import CSS

            # Additional CSS for better PDF rendering
            extra_css = CSS(string="""
                @page { margin: 1.5cm; }
                body { -webkit-print-color-adjust: exact; }
            """)

            # Create PDF
            html = weasyprint.HTML(string=html_content, base_url=".")
            pdf_bytes = html.write_pdf(stylesheets=[extra_css])

            return pdf_bytes

        except Exception as e:
            logger.error(f"Failed to convert HTML to PDF: {e}")
            raise RuntimeError(f"PDF generation failed: {e}") from e

    def _extract_issues(self, validation: Validation) -> list[dict[str, Any]]:
        """Extract issues from validation result."""
        return self._html_reporter._extract_issues(validation)

    def _get_severity_color(self, severity: str, theme: ReportTheme) -> str:
        """Get color for severity level."""
        return self._html_reporter._get_severity_color(severity, theme)

    def _get_status_indicator(self, passed: bool | None) -> str:
        """Get status indicator text."""
        return self._html_reporter._get_status_indicator(passed)
