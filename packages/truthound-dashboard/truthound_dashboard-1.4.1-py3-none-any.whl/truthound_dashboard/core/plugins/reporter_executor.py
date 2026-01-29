"""Custom Reporter Executor.

This module provides execution of custom reporters for
generating various report formats.
"""

from __future__ import annotations

import io
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from truthound_dashboard.db.models import CustomReporter, PluginExecutionLog

from .sandbox import create_sandbox, SandboxConfig

logger = logging.getLogger(__name__)


@dataclass
class ReportContext:
    """Context provided to custom reporters.

    Attributes:
        data: Data to include in the report.
        config: Reporter configuration.
        format: Output format requested.
        metadata: Additional metadata.
    """

    data: dict[str, Any]
    config: dict[str, Any] = field(default_factory=dict)
    format: str = "html"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for execution."""
        return {
            "data": self.data,
            "config": self.config,
            "format": self.format,
            "metadata": self.metadata,
        }


@dataclass
class ReportResult:
    """Result of custom reporter execution.

    Attributes:
        success: Whether report generation succeeded.
        content: Generated report content.
        content_type: MIME type of the content.
        filename: Suggested filename.
        error: Error message if failed.
        execution_time_ms: Execution time in milliseconds.
    """

    success: bool
    content: str | bytes = ""
    content_type: str = "text/html"
    filename: str = "report.html"
    error: str | None = None
    execution_time_ms: float = 0


# Template code for Jinja2-based reporters
JINJA2_REPORTER_CODE = '''
import json
from datetime import datetime

def generate_report(data, config, format, metadata):
    """Generate report using Jinja2 template.

    Args:
        data: Report data.
        config: Reporter configuration.
        format: Output format.
        metadata: Report metadata.

    Returns:
        Dictionary with 'content', 'content_type', 'filename'.
    """
    # Template will be inserted here
    template = """{template}"""

    # Simple template rendering (subset of Jinja2)
    result = template

    # Replace simple variables
    for key, value in data.items():
        placeholder = "{{{{ {key} }}}}".format(key=key)
        if placeholder in result:
            result = result.replace(placeholder, str(value))

    # Replace metadata
    for key, value in metadata.items():
        placeholder = "{{{{ metadata.{key} }}}}".format(key=key)
        if placeholder in result:
            result = result.replace(placeholder, str(value))

    # Replace config
    for key, value in config.items():
        placeholder = "{{{{ config.{key} }}}}".format(key=key)
        if placeholder in result:
            result = result.replace(placeholder, str(value))

    # Determine content type
    content_type = "text/html"
    filename = "report.html"

    if format == "json":
        result = json.dumps(data, indent=2, default=str)
        content_type = "application/json"
        filename = "report.json"
    elif format == "markdown":
        content_type = "text/markdown"
        filename = "report.md"
    elif format == "csv":
        content_type = "text/csv"
        filename = "report.csv"

    return {{
        "content": result,
        "content_type": content_type,
        "filename": filename
    }}
'''

# Template code for code-based reporters
CODE_REPORTER_WRAPPER = '''
import json
from datetime import datetime
from collections import Counter

# User-provided reporter code
{user_code}

def _execute_reporter(data, config, format, metadata):
    """Execute the custom reporter.

    Args:
        data: Report data.
        config: Reporter configuration.
        format: Output format.
        metadata: Report metadata.

    Returns:
        Dictionary with 'content', 'content_type', 'filename'.
    """
    result = generate_report(data, config, format, metadata)

    if isinstance(result, str):
        return {{
            "content": result,
            "content_type": "text/html",
            "filename": "report.html"
        }}
    elif isinstance(result, dict):
        return {{
            "content": result.get("content", ""),
            "content_type": result.get("content_type", "text/html"),
            "filename": result.get("filename", "report.html")
        }}
    else:
        return {{
            "content": str(result),
            "content_type": "text/plain",
            "filename": "report.txt"
        }}
'''


class CustomReporterExecutor:
    """Executor for custom reporters.

    This class handles the execution of custom reporters
    for generating various report formats.

    Attributes:
        sandbox: Plugin sandbox for secure execution.
        log_executions: Whether to log executions.
    """

    def __init__(
        self,
        sandbox_config: SandboxConfig | None = None,
        log_executions: bool = True,
    ) -> None:
        """Initialize the executor.

        Args:
            sandbox_config: Sandbox configuration.
            log_executions: Whether to log executions.
        """
        self.sandbox = create_sandbox(sandbox_config or SandboxConfig())
        self.log_executions = log_executions

    def validate_reporter_code(self, code: str) -> tuple[bool, list[str]]:
        """Validate custom reporter code.

        Args:
            code: Python code implementing the reporter.

        Returns:
            Tuple of (is_valid, list of issues).
        """
        issues = []

        # Check for required function
        if "def generate_report(" not in code:
            issues.append("Missing required 'generate_report' function")

        # Check for dangerous patterns
        dangerous = [
            "os.system",
            "subprocess",
            "__import__",
            "open(",
            "file(",
        ]
        for pattern in dangerous:
            if pattern in code:
                issues.append(f"Dangerous pattern detected: {pattern}")

        # Analyze with sandbox
        sandbox_issues, _ = self.sandbox.analyze_code(code)
        issues.extend(sandbox_issues)

        return len(issues) == 0, issues

    def validate_template(self, template: str) -> tuple[bool, list[str]]:
        """Validate Jinja2 template.

        Args:
            template: Jinja2 template string.

        Returns:
            Tuple of (is_valid, list of issues).
        """
        issues = []

        # Check for potentially dangerous Jinja2 constructs
        dangerous_patterns = [
            "{% import",
            "{% include",
            "{{ self",
            "{{ config.__",
            "{{ request",
            "{{ session",
        ]

        for pattern in dangerous_patterns:
            if pattern in template:
                issues.append(f"Dangerous template pattern: {pattern}")

        return len(issues) == 0, issues

    async def execute(
        self,
        reporter: CustomReporter,
        context: ReportContext,
        session: AsyncSession | None = None,
        source_id: str | None = None,
    ) -> ReportResult:
        """Execute a custom reporter.

        Args:
            reporter: CustomReporter model.
            context: Report context.
            session: Optional database session for logging.
            source_id: Optional source ID for logging.

        Returns:
            ReportResult with generated report.
        """
        execution_id = str(uuid.uuid4())
        start_time = datetime.utcnow()

        logger.debug(f"Executing custom reporter: {reporter.name}")

        # Create execution log if logging enabled
        log_entry = None
        if self.log_executions and session and reporter.plugin_id:
            log_entry = PluginExecutionLog(
                plugin_id=reporter.plugin_id,
                reporter_id=str(reporter.id),
                execution_id=execution_id,
                source_id=source_id,
                status="running",
            )
            session.add(log_entry)
            await session.flush()

        try:
            # Determine execution method
            if reporter.template:
                result = await self._execute_template(reporter.template, context)
            elif reporter.code:
                result = await self._execute_code(reporter.code, context)
            else:
                result = ReportResult(
                    success=False,
                    error="Reporter has no template or code",
                )

            # Update reporter usage stats
            reporter.increment_usage()

            # Update execution log
            if log_entry:
                if result.success:
                    log_entry.mark_completed(
                        result={
                            "filename": result.filename,
                            "content_type": result.content_type,
                            "size": len(result.content) if result.content else 0,
                        }
                    )
                else:
                    log_entry.mark_failed(result.error or "Unknown error")

            if session:
                await session.flush()

            return result

        except Exception as e:
            logger.error(f"Custom reporter execution failed: {e}")

            if log_entry:
                log_entry.mark_failed(str(e))
                if session:
                    await session.flush()

            return ReportResult(
                success=False,
                error=f"Execution error: {e}",
            )

    async def _execute_template(
        self,
        template: str,
        context: ReportContext,
    ) -> ReportResult:
        """Execute a Jinja2 template reporter.

        Args:
            template: Jinja2 template string.
            context: Report context.

        Returns:
            ReportResult.
        """
        # Validate template
        is_valid, issues = self.validate_template(template)
        if not is_valid:
            return ReportResult(
                success=False,
                error=f"Template validation failed: {'; '.join(issues)}",
            )

        # Prepare code with template
        code = JINJA2_REPORTER_CODE.format(template=template.replace('"', '\\"'))

        sandbox_result = self.sandbox.execute(
            code=code,
            entry_point="generate_report",
            entry_args=context.to_dict(),
        )

        if sandbox_result.success and sandbox_result.result:
            return ReportResult(
                success=True,
                content=sandbox_result.result.get("content", ""),
                content_type=sandbox_result.result.get("content_type", "text/html"),
                filename=sandbox_result.result.get("filename", "report.html"),
                execution_time_ms=sandbox_result.execution_time_ms,
            )
        else:
            return ReportResult(
                success=False,
                error=sandbox_result.error,
                execution_time_ms=sandbox_result.execution_time_ms,
            )

    async def _execute_code(
        self,
        code: str,
        context: ReportContext,
    ) -> ReportResult:
        """Execute a code-based reporter.

        Args:
            code: Python code.
            context: Report context.

        Returns:
            ReportResult.
        """
        # Validate code
        is_valid, issues = self.validate_reporter_code(code)
        if not is_valid:
            return ReportResult(
                success=False,
                error=f"Code validation failed: {'; '.join(issues)}",
            )

        # Wrap code
        wrapped_code = CODE_REPORTER_WRAPPER.format(user_code=code)

        sandbox_result = self.sandbox.execute(
            code=wrapped_code,
            entry_point="_execute_reporter",
            entry_args=context.to_dict(),
        )

        if sandbox_result.success and sandbox_result.result:
            return ReportResult(
                success=True,
                content=sandbox_result.result.get("content", ""),
                content_type=sandbox_result.result.get("content_type", "text/html"),
                filename=sandbox_result.result.get("filename", "report.html"),
                execution_time_ms=sandbox_result.execution_time_ms,
            )
        else:
            return ReportResult(
                success=False,
                error=sandbox_result.error,
                execution_time_ms=sandbox_result.execution_time_ms,
            )

    async def preview_report(
        self,
        template: str | None = None,
        code: str | None = None,
        sample_data: dict[str, Any] | None = None,
        config: dict[str, Any] | None = None,
        format: str = "html",
    ) -> ReportResult:
        """Preview a report without saving.

        Args:
            template: Jinja2 template.
            code: Python code.
            sample_data: Sample data for preview.
            config: Reporter configuration.
            format: Output format.

        Returns:
            ReportResult with preview.
        """
        context = ReportContext(
            data=sample_data or {"message": "Sample report data"},
            config=config or {},
            format=format,
            metadata={
                "generated_at": datetime.utcnow().isoformat(),
                "is_preview": True,
            },
        )

        if template:
            return await self._execute_template(template, context)
        elif code:
            return await self._execute_code(code, context)
        else:
            return ReportResult(
                success=False,
                error="No template or code provided",
            )

    def get_reporter_template(self) -> str:
        """Get a template for creating custom reporters.

        Returns:
            Template code string.
        """
        return '''
def generate_report(data, config, format, metadata):
    """Custom report generator function.

    Args:
        data: Dictionary of data to include in report.
        config: Dictionary of configuration options.
        format: Output format ('html', 'json', 'markdown', 'csv').
        metadata: Dictionary of metadata (generated_at, etc.).

    Returns:
        Dictionary with:
            - content: str - Generated report content
            - content_type: str - MIME type
            - filename: str - Suggested filename
    """
    # Generate HTML report
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Validation Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #333; }}
            .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
            .issues {{ margin-top: 20px; }}
            .issue {{ padding: 10px; margin: 5px 0; border-left: 3px solid #fd9e4b; }}
        </style>
    </head>
    <body>
        <h1>Validation Report</h1>
        <div class="summary">
            <p>Generated: {metadata.get('generated_at', 'Unknown')}</p>
            <p>Total Issues: {len(data.get('issues', []))}</p>
        </div>
        <div class="issues">
            <h2>Issues</h2>
            {''.join(f'<div class="issue">{issue}</div>' for issue in data.get('issues', []))}
        </div>
    </body>
    </html>
    """

    return {
        "content": html,
        "content_type": "text/html",
        "filename": "validation_report.html"
    }
'''

    def get_jinja2_template(self) -> str:
        """Get a Jinja2 template example.

        Returns:
            Jinja2 template string.
        """
        return '''<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #fd9e4b; }
        .card { background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 10px 0; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background: #fd9e4b; color: white; }
    </style>
</head>
<body>
    <h1>{{ title }}</h1>

    <div class="card">
        <h3>Summary</h3>
        <p>Generated: {{ metadata.generated_at }}</p>
        <p>Source: {{ source_name }}</p>
        <p>Status: {{ status }}</p>
    </div>

    <table>
        <thead>
            <tr>
                <th>Column</th>
                <th>Issue</th>
                <th>Severity</th>
            </tr>
        </thead>
        <tbody>
            {% for issue in issues %}
            <tr>
                <td>{{ issue.column }}</td>
                <td>{{ issue.message }}</td>
                <td>{{ issue.severity }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>'''


# Default executor instance
reporter_executor = CustomReporterExecutor()
