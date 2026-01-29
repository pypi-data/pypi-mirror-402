"""JUnit XML report generator.

Generates JUnit-compatible XML reports for CI/CD integration.
Output can be consumed by Jenkins, GitHub Actions, GitLab CI, etc.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import TYPE_CHECKING, Any

from .base import Reporter, ReportFormat, ReportMetadata, ReportTheme

if TYPE_CHECKING:
    from truthound_dashboard.db.models import Validation


class JUnitReporter(Reporter):
    """JUnit XML report generator for CI/CD integration.

    Produces JUnit-compatible XML that can be consumed by:
    - Jenkins JUnit Plugin
    - GitHub Actions
    - GitLab CI
    - Azure DevOps
    - CircleCI
    - Any tool supporting JUnit XML format
    """

    @property
    def format(self) -> ReportFormat:
        return ReportFormat.JUNIT

    @property
    def content_type(self) -> str:
        return "application/xml; charset=utf-8"

    @property
    def file_extension(self) -> str:
        return ".xml"

    async def _render_content(
        self,
        validation: Validation,
        metadata: ReportMetadata,
        include_samples: bool,
        include_statistics: bool,
    ) -> str:
        """Render JUnit XML report content."""
        issues = self._extract_issues(validation)

        # Create root element (testsuites)
        testsuites = ET.Element("testsuites")
        testsuites.set("name", "Truthound Validation")
        testsuites.set("tests", str(len(issues) + 1))  # +1 for overall test
        testsuites.set("failures", str(validation.total_issues or 0))
        testsuites.set("errors", str(validation.critical_issues or 0))
        testsuites.set("time", str((validation.duration_ms or 0) / 1000))

        # Create testsuite for this validation
        testsuite = ET.SubElement(testsuites, "testsuite")
        testsuite.set("name", f"Validation: {metadata.source_name or validation.source_id}")
        testsuite.set("tests", str(len(issues) + 1))
        testsuite.set("failures", str(validation.total_issues or 0))
        testsuite.set("errors", str(validation.critical_issues or 0))
        testsuite.set("time", str((validation.duration_ms or 0) / 1000))
        testsuite.set("timestamp", validation.created_at.isoformat() if validation.created_at else datetime.utcnow().isoformat())

        # Add properties
        properties = ET.SubElement(testsuite, "properties")
        self._add_property(properties, "source_id", validation.source_id)
        self._add_property(properties, "validation_id", validation.id)
        self._add_property(properties, "row_count", str(validation.row_count or 0))
        self._add_property(properties, "column_count", str(validation.column_count or 0))
        self._add_property(properties, "status", validation.status)
        self._add_property(properties, "passed", str(validation.passed).lower())

        # Add overall validation test case
        overall_test = ET.SubElement(testsuite, "testcase")
        overall_test.set("name", "Overall Validation")
        overall_test.set("classname", f"truthound.{metadata.source_name or validation.source_id}")
        overall_test.set("time", str((validation.duration_ms or 0) / 1000))

        if not validation.passed:
            failure = ET.SubElement(overall_test, "failure")
            failure.set("message", f"Validation failed with {validation.total_issues} issues")
            failure.set("type", "ValidationFailure")
            failure.text = self._generate_failure_details(validation, issues)

        # Add individual test cases for each issue type
        issue_groups = self._group_issues_by_type(issues)
        for issue_type, group_issues in issue_groups.items():
            testcase = ET.SubElement(testsuite, "testcase")
            testcase.set("name", f"Check: {issue_type}")
            testcase.set("classname", f"truthound.validators.{issue_type}")
            testcase.set("time", "0")

            if group_issues:
                # Determine severity for failure type
                max_severity = max(
                    (self._severity_order(i.get("severity", "low")) for i in group_issues),
                    default=0
                )

                if max_severity >= 3:  # critical
                    error = ET.SubElement(testcase, "error")
                    error.set("message", f"Critical: {len(group_issues)} issues found")
                    error.set("type", "CriticalValidationError")
                    error.text = self._format_issues_detail(group_issues, include_samples)
                else:
                    failure = ET.SubElement(testcase, "failure")
                    failure.set("message", f"{len(group_issues)} issues found")
                    failure.set("type", "ValidationFailure")
                    failure.text = self._format_issues_detail(group_issues, include_samples)

        # Add system-out with summary
        system_out = ET.SubElement(testsuite, "system-out")
        system_out.text = self._generate_summary(validation, metadata)

        # Convert to string with proper formatting
        return self._prettify_xml(testsuites)

    def _add_property(self, parent: ET.Element, name: str, value: str) -> None:
        """Add a property element."""
        prop = ET.SubElement(parent, "property")
        prop.set("name", name)
        prop.set("value", value)

    def _severity_order(self, severity: str) -> int:
        """Get numeric order for severity."""
        order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        return order.get(severity.lower(), 0)

    def _group_issues_by_type(self, issues: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        """Group issues by their type."""
        groups: dict[str, list[dict[str, Any]]] = {}
        for issue in issues:
            issue_type = issue.get("issue_type", "unknown")
            if issue_type not in groups:
                groups[issue_type] = []
            groups[issue_type].append(issue)
        return groups

    def _generate_failure_details(
        self,
        validation: Validation,
        issues: list[dict[str, Any]],
    ) -> str:
        """Generate detailed failure message."""
        lines = [
            f"Validation Status: {validation.status}",
            f"Total Issues: {validation.total_issues}",
            f"Critical: {validation.critical_issues}",
            f"High: {validation.high_issues}",
            f"Medium: {validation.medium_issues}",
            f"Low: {validation.low_issues}",
            "",
            "Issue Summary:",
        ]

        for issue in issues[:10]:  # Limit to first 10
            lines.append(
                f"  - [{issue.get('severity', 'unknown').upper()}] "
                f"{issue.get('column', 'N/A')}: {issue.get('issue_type', 'unknown')} "
                f"({issue.get('count', 0)} occurrences)"
            )

        if len(issues) > 10:
            lines.append(f"  ... and {len(issues) - 10} more issues")

        return "\n".join(lines)

    def _format_issues_detail(
        self,
        issues: list[dict[str, Any]],
        include_samples: bool,
    ) -> str:
        """Format issues for display in XML."""
        lines = []
        for issue in issues:
            line = (
                f"Column: {issue.get('column', 'N/A')}, "
                f"Count: {issue.get('count', 0)}"
            )
            if issue.get("details"):
                line += f", Details: {issue.get('details')}"

            if include_samples and issue.get("sample_values"):
                samples = [str(v)[:30] for v in issue["sample_values"][:3]]
                line += f", Samples: [{', '.join(samples)}]"

            lines.append(line)

        return "\n".join(lines)

    def _generate_summary(
        self,
        validation: Validation,
        metadata: ReportMetadata,
    ) -> str:
        """Generate summary for system-out."""
        return f"""
Truthound Validation Report
===========================
Source: {metadata.source_name or validation.source_id}
Validation ID: {validation.id}
Generated: {metadata.generated_at.isoformat()}

Data Statistics:
  Rows: {validation.row_count or 'N/A'}
  Columns: {validation.column_count or 'N/A'}

Validation Results:
  Status: {validation.status}
  Passed: {validation.passed}
  Duration: {(validation.duration_ms or 0) / 1000:.2f}s

Issue Summary:
  Total: {validation.total_issues or 0}
  Critical: {validation.critical_issues or 0}
  High: {validation.high_issues or 0}
  Medium: {validation.medium_issues or 0}
  Low: {validation.low_issues or 0}
"""

    def _prettify_xml(self, elem: ET.Element) -> str:
        """Return pretty-printed XML string."""
        from xml.dom import minidom

        rough_string = ET.tostring(elem, encoding="unicode", method="xml")
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ", encoding=None)
