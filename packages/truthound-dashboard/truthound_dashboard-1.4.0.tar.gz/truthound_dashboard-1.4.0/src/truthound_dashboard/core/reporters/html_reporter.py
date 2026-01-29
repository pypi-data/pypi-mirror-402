"""HTML report generator.

Generates professional HTML reports with responsive design,
theme support, internationalization, and interactive features.
"""

from __future__ import annotations

from html import escape
from typing import TYPE_CHECKING, Any

from .base import Reporter, ReportFormat, ReportMetadata, ReportTheme
from .i18n import ReportLocalizer, SupportedLocale, get_localizer

if TYPE_CHECKING:
    from truthound_dashboard.db.models import Validation


class HTMLReporter(Reporter):
    """HTML report generator with theme and i18n support.

    Produces standalone HTML documents with embedded CSS.
    Supports multiple themes, responsive design, and 15 languages.

    Example:
        reporter = HTMLReporter(locale="ko")
        result = await reporter.generate(validation, theme=ReportTheme.DARK)
    """

    def __init__(self, locale: SupportedLocale | str = SupportedLocale.ENGLISH) -> None:
        """Initialize the HTML reporter.

        Args:
            locale: Target locale for report generation.
        """
        super().__init__()
        if isinstance(locale, str):
            locale = SupportedLocale.from_string(locale)
        self._locale = locale
        self._localizer = get_localizer(locale)

    @property
    def format(self) -> ReportFormat:
        return ReportFormat.HTML

    @property
    def content_type(self) -> str:
        return "text/html; charset=utf-8"

    @property
    def file_extension(self) -> str:
        return ".html"

    @property
    def locale(self) -> SupportedLocale:
        """Get the current locale."""
        return self._locale

    @property
    def localizer(self) -> ReportLocalizer:
        """Get the localizer instance."""
        return self._localizer

    async def _render_content(
        self,
        validation: Validation,
        metadata: ReportMetadata,
        include_samples: bool,
        include_statistics: bool,
    ) -> str:
        """Render HTML report content."""
        issues = self._extract_issues(validation)
        theme = metadata.theme
        t = self._localizer  # Shorthand for translations

        # Build HTML sections
        css = self._generate_css(theme)
        header = self._render_header(validation, metadata, t)
        summary = self._render_summary(validation, theme, t)
        statistics = (
            self._render_statistics(validation, theme, t) if include_statistics else ""
        )
        issues_section = self._render_issues(issues, theme, include_samples, t)
        footer = self._render_footer(metadata, t)

        # Determine text direction for RTL languages
        text_dir = t.text_direction
        lang_code = self._locale.value

        return f"""<!DOCTYPE html>
<html lang="{lang_code}" dir="{text_dir}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(metadata.title)}</title>
    <style>
{css}
    </style>
</head>
<body class="theme-{theme.value}">
    <div class="container">
        {header}
        {summary}
        {statistics}
        {issues_section}
        {footer}
    </div>
</body>
</html>"""

    def _generate_css(self, theme: ReportTheme) -> str:
        """Generate CSS based on theme."""
        # Base colors for themes
        theme_colors = {
            ReportTheme.LIGHT: {
                "bg": "#ffffff",
                "text": "#1f2937",
                "text-muted": "#6b7280",
                "border": "#e5e7eb",
                "card-bg": "#f9fafb",
                "primary": "#fd9e4b",
                "success": "#10b981",
                "danger": "#ef4444",
            },
            ReportTheme.DARK: {
                "bg": "#1f2937",
                "text": "#f9fafb",
                "text-muted": "#9ca3af",
                "border": "#374151",
                "card-bg": "#111827",
                "primary": "#fd9e4b",
                "success": "#34d399",
                "danger": "#f87171",
            },
            ReportTheme.PROFESSIONAL: {
                "bg": "#f8fafc",
                "text": "#0f172a",
                "text-muted": "#64748b",
                "border": "#cbd5e1",
                "card-bg": "#ffffff",
                "primary": "#fd9e4b",
                "success": "#059669",
                "danger": "#dc2626",
            },
            ReportTheme.MINIMAL: {
                "bg": "#ffffff",
                "text": "#000000",
                "text-muted": "#666666",
                "border": "#e0e0e0",
                "card-bg": "#fafafa",
                "primary": "#fd9e4b",
                "success": "#22c55e",
                "danger": "#ef4444",
            },
            ReportTheme.HIGH_CONTRAST: {
                "bg": "#000000",
                "text": "#ffffff",
                "text-muted": "#e0e0e0",
                "border": "#ffffff",
                "card-bg": "#1a1a1a",
                "primary": "#ffb347",
                "success": "#00ff00",
                "danger": "#ff0000",
            },
        }

        c = theme_colors.get(theme, theme_colors[ReportTheme.PROFESSIONAL])

        # RTL support
        rtl_css = ""
        if self._locale.is_rtl:
            rtl_css = """
        [dir="rtl"] .stat-row {
            flex-direction: row-reverse;
        }
        [dir="rtl"] th, [dir="rtl"] td {
            text-align: right;
        }
        """

        return f"""
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
                         'Helvetica Neue', Arial, sans-serif;
            background-color: {c['bg']};
            color: {c['text']};
            line-height: 1.6;
            padding: 2rem;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid {c['primary']};
        }}

        .header h1 {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
            color: {c['primary']};
        }}

        .header .subtitle {{
            color: {c['text-muted']};
            font-size: 0.95rem;
        }}

        .card {{
            background: {c['card-bg']};
            border: 1px solid {c['border']};
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}

        .card-title {{
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid {c['border']};
        }}

        .status-badge {{
            display: inline-block;
            padding: 0.5rem 1rem;
            border-radius: 9999px;
            font-weight: 600;
            font-size: 1.1rem;
        }}

        .status-passed {{
            background: {c['success']}20;
            color: {c['success']};
        }}

        .status-failed {{
            background: {c['danger']}20;
            color: {c['danger']};
        }}

        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }}

        .summary-item {{
            text-align: center;
            padding: 1rem;
            background: {c['bg']};
            border-radius: 8px;
            border: 1px solid {c['border']};
        }}

        .summary-item .value {{
            font-size: 2rem;
            font-weight: 700;
            display: block;
        }}

        .summary-item .label {{
            color: {c['text-muted']};
            font-size: 0.875rem;
        }}

        .severity-critical {{ color: #dc2626; }}
        .severity-high {{ color: #ea580c; }}
        .severity-medium {{ color: #ca8a04; }}
        .severity-low {{ color: #2563eb; }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }}

        th, td {{
            padding: 0.75rem 1rem;
            text-align: left;
            border-bottom: 1px solid {c['border']};
        }}

        th {{
            background: {c['bg']};
            font-weight: 600;
            color: {c['text-muted']};
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        tr:hover {{
            background: {c['card-bg']};
        }}

        .severity-badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .badge-critical {{
            background: #dc262620;
            color: #dc2626;
        }}

        .badge-high {{
            background: #ea580c20;
            color: #ea580c;
        }}

        .badge-medium {{
            background: #ca8a0420;
            color: #ca8a04;
        }}

        .badge-low {{
            background: #2563eb20;
            color: #2563eb;
        }}

        .samples {{
            margin-top: 0.5rem;
            padding: 0.5rem;
            background: {c['bg']};
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.875rem;
            color: {c['text-muted']};
        }}

        .footer {{
            text-align: center;
            padding-top: 1.5rem;
            margin-top: 2rem;
            border-top: 1px solid {c['border']};
            color: {c['text-muted']};
            font-size: 0.875rem;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.5rem;
        }}

        .stat-row {{
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
            border-bottom: 1px solid {c['border']};
        }}

        .stat-row:last-child {{
            border-bottom: none;
        }}

        @media (max-width: 768px) {{
            body {{
                padding: 1rem;
            }}

            .summary-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}

            .stats-grid {{
                grid-template-columns: 1fr;
            }}

            table {{
                display: block;
                overflow-x: auto;
            }}
        }}

        @media print {{
            body {{
                padding: 0;
            }}

            .card {{
                break-inside: avoid;
            }}
        }}
        {rtl_css}
        """

    def _render_header(
        self,
        validation: Validation,
        metadata: ReportMetadata,
        t: ReportLocalizer,
    ) -> str:
        """Render report header."""
        source_name = escape(metadata.source_name or validation.source_id)
        generated = t.format_date(metadata.generated_at)

        return f"""
        <header class="header">
            <h1>{escape(metadata.title)}</h1>
            <p class="subtitle">
                {t.t("report.source")}: <strong>{source_name}</strong> |
                {t.t("report.generated_at")}: {generated}
            </p>
        </header>
        """

    def _render_summary(
        self,
        validation: Validation,
        theme: ReportTheme,
        t: ReportLocalizer,
    ) -> str:
        """Render validation summary card."""
        passed = validation.passed
        status_class = "status-passed" if passed else "status-failed"

        if passed is None:
            status_text = f"⏳ {t.t('status.pending')}"
        elif passed:
            status_text = f"✅ {t.t('status.passed')}"
        else:
            status_text = f"❌ {t.t('status.failed')}"

        return f"""
        <section class="card">
            <h2 class="card-title">{t.t("summary.title")}</h2>
            <div style="text-align: center; margin-bottom: 1rem;">
                <span class="status-badge {status_class}">{status_text}</span>
            </div>
            <div class="summary-grid">
                <div class="summary-item">
                    <span class="value">{t.format_number(validation.total_issues or 0)}</span>
                    <span class="label">{t.t("summary.total_issues")}</span>
                </div>
                <div class="summary-item">
                    <span class="value severity-critical">{t.format_number(validation.critical_issues or 0)}</span>
                    <span class="label">{t.t("severity.critical")}</span>
                </div>
                <div class="summary-item">
                    <span class="value severity-high">{t.format_number(validation.high_issues or 0)}</span>
                    <span class="label">{t.t("severity.high")}</span>
                </div>
                <div class="summary-item">
                    <span class="value severity-medium">{t.format_number(validation.medium_issues or 0)}</span>
                    <span class="label">{t.t("severity.medium")}</span>
                </div>
                <div class="summary-item">
                    <span class="value severity-low">{t.format_number(validation.low_issues or 0)}</span>
                    <span class="label">{t.t("severity.low")}</span>
                </div>
            </div>
        </section>
        """

    def _render_statistics(
        self,
        validation: Validation,
        theme: ReportTheme,
        t: ReportLocalizer,
    ) -> str:
        """Render data statistics card."""
        duration = validation.duration_ms
        na_text = t.t("statistics.na")

        if duration:
            duration_str = t.format("time.seconds", value=f"{duration / 1000:.2f}")
        else:
            duration_str = na_text

        started = t.format_date(validation.started_at) if validation.started_at else na_text
        completed = t.format_date(validation.completed_at) if validation.completed_at else na_text

        row_count = t.format_number(validation.row_count) if validation.row_count else na_text
        col_count = t.format_number(validation.column_count) if validation.column_count else na_text

        return f"""
        <section class="card">
            <h2 class="card-title">{t.t("statistics.title")}</h2>
            <div class="stats-grid">
                <div class="stat-row">
                    <span>{t.t("statistics.row_count")}</span>
                    <strong>{row_count}</strong>
                </div>
                <div class="stat-row">
                    <span>{t.t("statistics.column_count")}</span>
                    <strong>{col_count}</strong>
                </div>
                <div class="stat-row">
                    <span>{t.t("statistics.duration")}</span>
                    <strong>{duration_str}</strong>
                </div>
                <div class="stat-row">
                    <span>{t.t("summary.status")}</span>
                    <strong>{escape(validation.status)}</strong>
                </div>
                <div class="stat-row">
                    <span>{t.t("statistics.started_at")}</span>
                    <strong>{started}</strong>
                </div>
                <div class="stat-row">
                    <span>{t.t("statistics.completed_at")}</span>
                    <strong>{completed}</strong>
                </div>
            </div>
        </section>
        """

    def _render_issues(
        self,
        issues: list[dict[str, Any]],
        theme: ReportTheme,
        include_samples: bool,
        t: ReportLocalizer,
    ) -> str:
        """Render issues table."""
        if not issues:
            return f"""
            <section class="card">
                <h2 class="card-title">{t.t("issues.title")}</h2>
                <p style="text-align: center; color: var(--text-muted); padding: 2rem;">
                    {t.t("issues.no_issues")}
                </p>
            </section>
            """

        rows = []
        for issue in issues:
            severity = issue.get("severity", "medium").lower()
            badge_class = f"badge-{severity}"
            severity_label = t.t(f"severity.{severity}")

            samples_html = ""
            if include_samples and issue.get("sample_values"):
                samples = [str(v)[:50] for v in issue["sample_values"][:5]]
                samples_html = f'<div class="samples">{escape(", ".join(samples))}</div>'

            rows.append(f"""
                <tr>
                    <td>{escape(issue.get('column', t.t('statistics.na')))}</td>
                    <td>{escape(issue.get('issue_type', 'Unknown'))}</td>
                    <td><span class="severity-badge {badge_class}">{severity_label}</span></td>
                    <td>{t.format_number(issue.get('count', 0))}</td>
                    <td>
                        {escape(issue.get('details', '') or '')}
                        {samples_html}
                    </td>
                </tr>
            """)

        issue_count_text = t.plural("issues.count", len(issues))

        return f"""
        <section class="card">
            <h2 class="card-title">{t.t("issues.title")} ({issue_count_text})</h2>
            <table>
                <thead>
                    <tr>
                        <th>{t.t("issues.column")}</th>
                        <th>{t.t("issues.type")}</th>
                        <th>{t.t("issues.severity")}</th>
                        <th>{t.t("issues.count")}</th>
                        <th>{t.t("issues.details")}</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        </section>
        """

    def _render_footer(self, metadata: ReportMetadata, t: ReportLocalizer) -> str:
        """Render report footer."""
        return f"""
        <footer class="footer">
            <p>{t.t("report.generated_by")}</p>
            <p>{t.t("report.validation_id")}: {escape(metadata.validation_id or t.t("statistics.na"))}</p>
        </footer>
        """
