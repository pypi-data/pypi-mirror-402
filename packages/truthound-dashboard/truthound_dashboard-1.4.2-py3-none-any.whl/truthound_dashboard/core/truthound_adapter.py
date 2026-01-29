"""Async wrapper for truthound package.

This module provides an async interface to truthound functions,
enabling non-blocking validation operations in the FastAPI application.

The adapter uses ThreadPoolExecutor to run synchronous truthound
functions without blocking the async event loop.

Features:
- Async wrappers for all truthound functions
- Automatic sampling for large datasets (100MB+ files)
- Configurable sample size and sampling methods

Example:
    adapter = get_adapter()
    result = await adapter.check("/path/to/data.csv")
    schema = await adapter.learn("/path/to/data.csv")

    # With auto-sampling for large files
    result = await adapter.check_with_sampling("/path/to/large.csv")
"""

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import yaml

logger = logging.getLogger(__name__)


@runtime_checkable
class TruthoundResult(Protocol):
    """Protocol for truthound result objects."""

    @property
    def issues(self) -> list[Any]: ...


@dataclass
class CheckResult:
    """Validation check result.

    Attributes:
        passed: Whether validation passed (no issues).
        has_critical: Whether critical issues were found.
        has_high: Whether high severity issues were found.
        total_issues: Total number of issues.
        critical_issues: Number of critical issues.
        high_issues: Number of high severity issues.
        medium_issues: Number of medium severity issues.
        low_issues: Number of low severity issues.
        source: Data source path.
        row_count: Number of rows validated.
        column_count: Number of columns.
        issues: List of validation issues.
    """

    passed: bool
    has_critical: bool
    has_high: bool
    total_issues: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    source: str
    row_count: int
    column_count: int
    issues: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "passed": self.passed,
            "has_critical": self.has_critical,
            "has_high": self.has_high,
            "total_issues": self.total_issues,
            "critical_issues": self.critical_issues,
            "high_issues": self.high_issues,
            "medium_issues": self.medium_issues,
            "low_issues": self.low_issues,
            "source": self.source,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "issues": self.issues,
        }


@dataclass
class LearnResult:
    """Schema learning result.

    Attributes:
        schema: Schema as dictionary.
        schema_yaml: Schema as YAML string.
        row_count: Number of rows analyzed.
        column_count: Number of columns.
        columns: List of column names.
    """

    schema: dict[str, Any]
    schema_yaml: str
    row_count: int | None
    column_count: int
    columns: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "schema": self.schema,
            "schema_yaml": self.schema_yaml,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "columns": self.columns,
        }


@dataclass
class ProfileResult:
    """Data profiling result.

    Attributes:
        source: Data source path.
        row_count: Number of rows.
        column_count: Number of columns.
        size_bytes: Data size in bytes.
        columns: List of column profile dictionaries.
    """

    source: str
    row_count: int
    column_count: int
    size_bytes: int
    columns: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source": self.source,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "size_bytes": self.size_bytes,
            "columns": self.columns,
        }


@dataclass
class CompareResult:
    """Drift comparison result.

    Attributes:
        baseline_source: Baseline data source path.
        current_source: Current data source path.
        baseline_rows: Number of rows in baseline.
        current_rows: Number of rows in current.
        has_drift: Whether drift was detected.
        has_high_drift: Whether high-severity drift was detected.
        total_columns: Total columns compared.
        drifted_columns: List of column names with drift.
        columns: Per-column drift results.
    """

    baseline_source: str
    current_source: str
    baseline_rows: int
    current_rows: int
    has_drift: bool
    has_high_drift: bool
    total_columns: int
    drifted_columns: list[str]
    columns: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "baseline_source": self.baseline_source,
            "current_source": self.current_source,
            "baseline_rows": self.baseline_rows,
            "current_rows": self.current_rows,
            "has_drift": self.has_drift,
            "has_high_drift": self.has_high_drift,
            "total_columns": self.total_columns,
            "drifted_columns": self.drifted_columns,
            "columns": self.columns,
        }


@dataclass
class ScanResult:
    """PII scan result.

    Attributes:
        source: Data source path.
        row_count: Number of rows scanned.
        column_count: Number of columns.
        total_columns_scanned: Total columns that were scanned.
        columns_with_pii: Number of columns containing PII.
        total_findings: Total number of PII findings.
        has_violations: Whether any regulation violations were found.
        total_violations: Number of regulation violations.
        findings: List of PII finding dictionaries.
        violations: List of regulation violation dictionaries.
    """

    source: str
    row_count: int
    column_count: int
    total_columns_scanned: int
    columns_with_pii: int
    total_findings: int
    has_violations: bool
    total_violations: int
    findings: list[dict[str, Any]]
    violations: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source": self.source,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "total_columns_scanned": self.total_columns_scanned,
            "columns_with_pii": self.columns_with_pii,
            "total_findings": self.total_findings,
            "has_violations": self.has_violations,
            "total_violations": self.total_violations,
            "findings": self.findings,
            "violations": self.violations,
        }


@dataclass
class MaskResult:
    """Data masking result.

    Attributes:
        source: Original data source path.
        output_path: Path to the masked output file.
        row_count: Number of rows in the masked data.
        column_count: Number of columns in the masked data.
        columns_masked: List of columns that were masked.
        strategy: Masking strategy used (redact, hash, fake).
        original_columns: List of all column names.
    """

    source: str
    output_path: str
    row_count: int
    column_count: int
    columns_masked: list[str]
    strategy: str
    original_columns: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source": self.source,
            "output_path": self.output_path,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "columns_masked": self.columns_masked,
            "strategy": self.strategy,
            "original_columns": self.original_columns,
        }


class TruthoundAdapter:
    """Async wrapper for truthound functions.

    This adapter provides an async interface to truthound operations,
    running them in a thread pool to avoid blocking the event loop.

    Attributes:
        max_workers: Maximum number of worker threads.
    """

    def __init__(self, max_workers: int = 4) -> None:
        """Initialize adapter.

        Args:
            max_workers: Maximum worker threads for concurrent operations.
        """
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._max_workers = max_workers

    async def check(
        self,
        data: str,
        *,
        validators: list[str] | None = None,
        validator_params: dict[str, dict[str, Any]] | None = None,
        schema: str | None = None,
        auto_schema: bool = False,
        columns: list[str] | None = None,
        min_severity: str | None = None,
        strict: bool = False,
        parallel: bool = False,
        max_workers: int | None = None,
        pushdown: bool | None = None,
    ) -> CheckResult:
        """Run data validation asynchronously.

        This method wraps truthound's th.check() with full parameter support.
        All parameters map directly to th.check() for maximum flexibility.

        Args:
            data: Data source path (CSV, Parquet, etc.).
            validators: Optional list of validator names to run.
            validator_params: Optional dict of per-validator parameters.
                Format: {"ValidatorName": {"param1": value1, "param2": value2}}
                Example: {"Null": {"columns": ["a", "b"], "mostly": 0.95}}
            schema: Optional path to schema YAML file.
            auto_schema: If True, auto-learns schema for validation.
            columns: Columns to validate. If None, validates all columns.
            min_severity: Minimum severity to report ("low", "medium", "high", "critical").
            strict: If True, raises exception on validation failures.
            parallel: If True, uses DAG-based parallel execution.
            max_workers: Max threads for parallel execution.
            pushdown: Enable query pushdown for SQL sources. None uses auto-detection.

        Returns:
            CheckResult with validation results.

        Raises:
            ImportError: If truthound is not installed.
            FileNotFoundError: If data file doesn't exist.
            ValidationError: If strict=True and validation fails.
        """
        import truthound as th

        # Build kwargs dynamically to avoid passing None for optional params
        # This ensures truthound uses its own defaults when params are not specified
        kwargs: dict[str, Any] = {
            "validators": validators,
            "schema": schema,
            "auto_schema": auto_schema,
            "parallel": parallel,
        }

        # Add per-validator parameters if provided
        if validator_params:
            kwargs["validator_params"] = validator_params

        # Only add optional params if explicitly set
        if columns is not None:
            kwargs["columns"] = columns
        if min_severity is not None:
            kwargs["min_severity"] = min_severity
        if strict:
            kwargs["strict"] = strict
        if max_workers is not None:
            kwargs["max_workers"] = max_workers
        if pushdown is not None:
            kwargs["pushdown"] = pushdown

        func = partial(th.check, data, **kwargs)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self._executor, func)

        return self._convert_check_result(result)

    async def learn(
        self,
        source: str,
        *,
        infer_constraints: bool = True,
        categorical_threshold: int | None = None,
        sample_size: int | None = None,
    ) -> LearnResult:
        """Learn schema from data asynchronously.

        Uses truthound's th.learn() to analyze data and generate schema.
        Supports all th.learn() parameters for maximum flexibility.

        Args:
            source: Data source path.
            infer_constraints: If True, infers constraints (min/max, allowed values)
                from data statistics.
            categorical_threshold: Maximum unique values for categorical detection.
                Columns with unique values <= threshold are treated as categorical
                and will have allowed_values inferred. If None, uses truthound
                default (20).
            sample_size: Number of rows to sample for large datasets.
                If None, uses all rows. Sampling improves performance but may
                miss rare values.

        Returns:
            LearnResult with schema information.
        """
        import truthound as th

        # Build kwargs dynamically to let truthound use its defaults when not specified
        kwargs: dict[str, Any] = {"infer_constraints": infer_constraints}

        if categorical_threshold is not None:
            kwargs["categorical_threshold"] = categorical_threshold
        if sample_size is not None:
            kwargs["sample_size"] = sample_size

        func = partial(th.learn, source, **kwargs)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self._executor, func)

        return self._convert_learn_result(result)

    async def profile(
        self,
        source: str,
        *,
        sample_size: int | None = None,
    ) -> ProfileResult:
        """Run data profiling asynchronously.

        Args:
            source: Data source path.
            sample_size: Maximum number of rows to sample for profiling.
                If None, profiles all data. Useful for large datasets.

        Returns:
            ProfileResult with profiling information.
        """
        import truthound as th

        # Build kwargs dynamically to let truthound use its defaults
        kwargs: dict[str, Any] = {}
        if sample_size is not None:
            kwargs["sample_size"] = sample_size

        func = partial(th.profile, source, **kwargs)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self._executor, func)

        return self._convert_profile_result(result)

    async def scan(
        self,
        data: str,
        *,
        columns: list[str] | None = None,
        regulations: list[str] | None = None,
        min_confidence: float = 0.8,
    ) -> ScanResult:
        """Run PII scan on data asynchronously.

        Uses truthound's th.scan() to detect personally identifiable information
        and check compliance with privacy regulations.

        Args:
            data: Data source path (CSV, Parquet, etc.).
            columns: Optional list of columns to scan. If None, scans all columns.
            regulations: Optional list of regulations to check compliance.
                Supported: "gdpr", "ccpa", "lgpd"
            min_confidence: Minimum confidence threshold for PII detection (0.0-1.0).
                Default is 0.8.

        Returns:
            ScanResult with PII findings and regulation violations.

        Raises:
            ImportError: If truthound is not installed.
            FileNotFoundError: If data file doesn't exist.
        """
        import truthound as th

        # Build kwargs dynamically to let truthound use its defaults
        kwargs: dict[str, Any] = {
            "min_confidence": min_confidence,
        }

        if columns is not None:
            kwargs["columns"] = columns
        if regulations is not None:
            kwargs["regulations"] = regulations

        func = partial(th.scan, data, **kwargs)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self._executor, func)

        return self._convert_scan_result(result)

    async def compare(
        self,
        baseline: str,
        current: str,
        *,
        columns: list[str] | None = None,
        method: str = "auto",
        threshold: float | None = None,
        correction: str | None = None,
        sample_size: int | None = None,
    ) -> CompareResult:
        """Compare two datasets for drift detection.

        Args:
            baseline: Reference data path.
            current: Current data path to compare.
            columns: Optional list of columns to compare. If None, all common columns.
            method: Detection method. Supported methods:
                - "auto": Smart selection (numeric → PSI, categorical → chi2)
                - "ks": Kolmogorov-Smirnov test (continuous distributions)
                - "psi": Population Stability Index (industry standard)
                - "chi2": Chi-Square test (categorical data)
                - "js": Jensen-Shannon divergence (symmetric, bounded)
                - "kl": Kullback-Leibler divergence (information loss)
                - "wasserstein": Earth Mover's Distance (distribution transport)
                - "cvm": Cramér-von Mises (sensitive to tails)
                - "anderson": Anderson-Darling (tail-weighted)
            threshold: Optional custom threshold for drift detection.
                Defaults vary by method: KS/chi2/cvm/anderson=0.05, PSI/JS/KL/wasserstein=0.1
            correction: Multiple testing correction method:
                - None: Use truthound default (bh for multiple columns)
                - "none": No correction
                - "bonferroni": Conservative, independent tests
                - "holm": Sequential adjustment
                - "bh": Benjamini-Hochberg FDR control
            sample_size: Optional sample size for large datasets.

        Returns:
            CompareResult with drift detection results.
        """
        import truthound as th

        # Build kwargs dynamically to avoid passing None for optional params
        kwargs: dict[str, Any] = {
            "columns": columns,
            "method": method,
        }

        # Only add optional params if explicitly set
        if threshold is not None:
            kwargs["threshold"] = threshold
        if correction is not None:
            kwargs["correction"] = correction
        if sample_size is not None:
            kwargs["sample_size"] = sample_size

        func = partial(th.compare, baseline, current, **kwargs)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(self._executor, func)

        return self._convert_compare_result(result)

    async def mask(
        self,
        data: str,
        output: str,
        *,
        columns: list[str] | None = None,
        strategy: str = "redact",
    ) -> MaskResult:
        """Mask sensitive data in a file asynchronously.

        Uses truthound's th.mask() to mask PII and sensitive data with
        three strategies: redact, hash, and fake.

        Args:
            data: Data source path (CSV, Parquet, etc.).
            output: Output file path for the masked data.
            columns: Optional list of columns to mask. If None, auto-detects PII.
            strategy: Masking strategy:
                - "redact": Replace values with asterisks (default)
                - "hash": Replace values with SHA256 hash
                - "fake": Replace values with realistic fake data

        Returns:
            MaskResult with masking operation details.

        Raises:
            ImportError: If truthound is not installed.
            FileNotFoundError: If data file doesn't exist.
            ValueError: If invalid strategy is provided.
        """
        import truthound as th

        # Validate strategy
        if strategy not in ("redact", "hash", "fake"):
            raise ValueError(
                f"Invalid strategy: {strategy}. Use 'redact', 'hash', or 'fake'."
            )

        # Build kwargs dynamically
        kwargs: dict[str, Any] = {
            "strategy": strategy,
        }

        if columns is not None:
            kwargs["columns"] = columns

        func = partial(th.mask, data, **kwargs)

        loop = asyncio.get_event_loop()
        masked_df = await loop.run_in_executor(self._executor, func)

        return self._convert_mask_result(data, output, masked_df, strategy, columns)

    async def check_with_sampling(
        self,
        data: str,
        *,
        validators: list[str] | None = None,
        validator_params: dict[str, dict[str, Any]] | None = None,
        schema: str | None = None,
        auto_schema: bool = False,
        columns: list[str] | None = None,
        min_severity: str | None = None,
        strict: bool = False,
        parallel: bool = False,
        max_workers: int | None = None,
        pushdown: bool | None = None,
        sample_size: int | None = None,
        sampling_method: str | None = None,
    ) -> CheckResult:
        """Run data validation with automatic sampling for large datasets.

        This method automatically samples large files (>100MB by default)
        before running validation, which significantly improves performance
        while maintaining validation accuracy for most use cases.

        Args:
            data: Data source path (CSV, Parquet, etc.).
            validators: Optional list of validator names to run.
            schema: Optional path to schema YAML file.
            auto_schema: If True, auto-learns schema for validation.
            columns: Columns to validate. If None, validates all columns.
            min_severity: Minimum severity to report.
            strict: If True, raises exception on validation failures.
            parallel: If True, uses parallel execution.
            max_workers: Max threads for parallel execution.
            pushdown: Enable query pushdown for SQL sources.
            sample_size: Number of rows to sample. Uses config default if not specified.
            sampling_method: Sampling method ("random", "head", "stratified").

        Returns:
            CheckResult with validation results.

        Note:
            The result.row_count reflects the sampled row count when sampling
            was performed. Check the sampling metadata for original row count.
        """
        from truthound_dashboard.core.sampling import SamplingMethod, get_sampler

        sampler = get_sampler()

        # Check if sampling is needed and perform if so
        path = Path(data)
        if path.exists() and sampler.needs_sampling(path):
            # Determine sampling method
            method = None
            if sampling_method:
                try:
                    method = SamplingMethod(sampling_method)
                except ValueError:
                    logger.warning(f"Unknown sampling method: {sampling_method}")

            # Perform sampling
            sample_result = await sampler.auto_sample(
                path,
                n=sample_size,
                method=method,
            )

            if sample_result.was_sampled:
                logger.info(
                    f"Sampled {sample_result.sampled_rows} rows from "
                    f"{sample_result.original_rows} ({sample_result.size_reduction_pct:.1f}% reduction)"
                )
                data = sample_result.sampled_path

        # Run validation on (possibly sampled) data
        return await self.check(
            data,
            validators=validators,
            validator_params=validator_params,
            schema=schema,
            auto_schema=auto_schema,
            columns=columns,
            min_severity=min_severity,
            strict=strict,
            parallel=parallel,
            max_workers=max_workers,
            pushdown=pushdown,
        )

    async def learn_with_sampling(
        self,
        source: str,
        *,
        infer_constraints: bool = True,
        categorical_threshold: int | None = None,
        sample_size: int | None = None,
    ) -> LearnResult:
        """Learn schema from data with automatic sampling for large datasets.

        This method first applies dashboard-level sampling for very large files,
        then passes the sample_size to th.learn() if specified.

        Args:
            source: Data source path.
            infer_constraints: If True, infer constraints from statistics.
            categorical_threshold: Maximum unique values for categorical detection.
            sample_size: Number of rows to sample. Used both for dashboard sampling
                and passed to th.learn() for internal sampling.

        Returns:
            LearnResult with schema information.
        """
        from truthound_dashboard.core.sampling import get_sampler

        sampler = get_sampler()

        # Sample if needed (dashboard-level sampling for very large files)
        path = Path(source)
        if path.exists() and sampler.needs_sampling(path):
            sample_result = await sampler.auto_sample(path, n=sample_size)
            if sample_result.was_sampled:
                logger.info(
                    f"Sampled {sample_result.sampled_rows} rows for schema learning"
                )
                source = sample_result.sampled_path

        return await self.learn(
            source,
            infer_constraints=infer_constraints,
            categorical_threshold=categorical_threshold,
            sample_size=sample_size,
        )

    async def profile_with_sampling(
        self,
        source: str,
        *,
        sample_size: int | None = None,
    ) -> ProfileResult:
        """Run data profiling with automatic sampling for large datasets.

        Args:
            source: Data source path.
            sample_size: Number of rows to sample. Uses config default if not specified.

        Returns:
            ProfileResult with profiling information.
        """
        from truthound_dashboard.core.sampling import get_sampler

        sampler = get_sampler()

        # Sample if needed
        path = Path(source)
        if path.exists() and sampler.needs_sampling(path):
            sample_result = await sampler.auto_sample(path, n=sample_size)
            if sample_result.was_sampled:
                logger.info(
                    f"Sampled {sample_result.sampled_rows} rows for profiling"
                )
                source = sample_result.sampled_path

        return await self.profile(source)

    def _convert_check_result(self, result: Any) -> CheckResult:
        """Convert truthound Report to CheckResult.

        The truthound Report contains:
        - issues: list[ValidationIssue]
        - source: str
        - row_count: int
        - column_count: int
        - has_issues: bool
        - has_critical: bool
        - has_high: bool
        """
        issues = result.issues
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for issue in issues:
            severity = issue.severity.value.lower()
            if severity in severity_counts:
                severity_counts[severity] += 1

        converted_issues = [
            {
                "column": issue.column,
                "issue_type": issue.issue_type,
                "count": issue.count,
                "severity": issue.severity.value,
                "details": getattr(issue, "details", None),
                "expected": getattr(issue, "expected", None),
                "actual": getattr(issue, "actual", None),
            }
            for issue in issues
        ]

        return CheckResult(
            passed=not result.has_issues,
            has_critical=result.has_critical,
            has_high=result.has_high,
            total_issues=len(issues),
            critical_issues=severity_counts["critical"],
            high_issues=severity_counts["high"],
            medium_issues=severity_counts["medium"],
            low_issues=severity_counts["low"],
            source=result.source,
            row_count=result.row_count,
            column_count=result.column_count,
            issues=converted_issues,
        )

    def _convert_learn_result(self, result: Any) -> LearnResult:
        """Convert truthound Schema to LearnResult.

        The truthound Schema contains:
        - columns: dict[str, ColumnSchema]
        - row_count: int | None
        - version: str
        - to_dict(): Convert to dictionary
        """
        schema_dict = result.to_dict()
        schema_yaml = yaml.dump(
            schema_dict,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

        return LearnResult(
            schema=schema_dict,
            schema_yaml=schema_yaml,
            row_count=result.row_count,
            column_count=len(result.columns),
            columns=list(result.columns.keys()),
        )

    def _convert_profile_result(self, result: Any) -> ProfileResult:
        """Convert truthound ProfileReport to ProfileResult.

        The truthound ProfileReport contains:
        - source: str
        - row_count: int
        - column_count: int
        - size_bytes: int
        - columns: list[dict]
        """
        columns = [
            {
                "name": col["name"],
                "dtype": col["dtype"],
                "null_pct": col.get("null_pct", "0%"),
                "unique_pct": col.get("unique_pct", "0%"),
                "min": col.get("min"),
                "max": col.get("max"),
                "mean": col.get("mean"),
                "std": col.get("std"),
            }
            for col in result.columns
        ]

        return ProfileResult(
            source=result.source,
            row_count=result.row_count,
            column_count=result.column_count,
            size_bytes=result.size_bytes,
            columns=columns,
        )

    def _convert_scan_result(self, result: Any) -> ScanResult:
        """Convert truthound PIIReport to ScanResult.

        The truthound PIIReport contains:
        - source: str
        - row_count: int
        - column_count: int
        - findings: list[PIIFinding]
        - has_violations: bool
        - violations: list[RegulationViolation]

        Each PIIFinding has:
        - column: str
        - pii_type: str
        - confidence: float
        - sample_count: int
        - sample_values: list[str] (optional)

        Each RegulationViolation has:
        - regulation: str
        - column: str
        - pii_type: str
        - message: str
        - severity: str (optional)
        """
        # Convert findings to dictionaries
        findings = []
        columns_with_pii = set()
        for finding in result.findings:
            columns_with_pii.add(finding.column)
            findings.append(
                {
                    "column": finding.column,
                    "pii_type": finding.pii_type,
                    "confidence": finding.confidence,
                    "sample_count": finding.sample_count,
                    "sample_values": getattr(finding, "sample_values", None),
                }
            )

        # Convert violations to dictionaries
        violations = []
        for violation in getattr(result, "violations", []):
            violations.append(
                {
                    "regulation": violation.regulation,
                    "column": violation.column,
                    "pii_type": getattr(violation, "pii_type", "unknown"),
                    "message": violation.message,
                    "severity": getattr(violation, "severity", "high"),
                }
            )

        return ScanResult(
            source=result.source,
            row_count=result.row_count,
            column_count=result.column_count,
            total_columns_scanned=result.column_count,
            columns_with_pii=len(columns_with_pii),
            total_findings=len(findings),
            has_violations=getattr(result, "has_violations", len(violations) > 0),
            total_violations=len(violations),
            findings=findings,
            violations=violations,
        )

    def _convert_compare_result(self, result: Any) -> CompareResult:
        """Convert truthound DriftReport to CompareResult.

        The truthound DriftReport contains:
        - baseline_source: str
        - current_source: str
        - baseline_rows: int
        - current_rows: int
        - columns: list[ColumnDrift]
        - has_drift: bool
        - has_high_drift: bool
        - get_drifted_columns(): list[str]

        Each ColumnDrift has:
        - column: str
        - dtype: str
        - result: DriftResult (drifted, level, method, statistic, p_value)
        - baseline_stats: dict
        - current_stats: dict
        """
        columns = [
            {
                "column": col.column,
                "dtype": col.dtype,
                "drifted": col.result.drifted,
                "level": (
                    col.result.level.value
                    if hasattr(col.result.level, "value")
                    else str(col.result.level)
                ),
                "method": col.result.method,
                "statistic": col.result.statistic,
                "p_value": col.result.p_value,
                "baseline_stats": col.baseline_stats,
                "current_stats": col.current_stats,
            }
            for col in result.columns
        ]

        return CompareResult(
            baseline_source=result.baseline_source,
            current_source=result.current_source,
            baseline_rows=result.baseline_rows,
            current_rows=result.current_rows,
            has_drift=result.has_drift,
            has_high_drift=result.has_high_drift,
            total_columns=len(result.columns),
            drifted_columns=result.get_drifted_columns(),
            columns=columns,
        )

    def _convert_mask_result(
        self,
        source: str,
        output: str,
        masked_df: Any,
        strategy: str,
        columns: list[str] | None,
    ) -> MaskResult:
        """Convert truthound mask result to MaskResult.

        Args:
            source: Original data source path.
            output: Output file path.
            masked_df: Polars DataFrame with masked data.
            strategy: Masking strategy used.
            columns: Columns that were requested to be masked.

        Returns:
            MaskResult with masking details.
        """
        # Get column information from the DataFrame
        all_columns = list(masked_df.columns)
        row_count = len(masked_df)

        # Determine which columns were actually masked
        # If columns was None, truthound auto-detected PII columns
        columns_masked = columns if columns else []

        # Write the masked data to output file
        output_path = Path(output)
        suffix = output_path.suffix.lower()

        if suffix == ".csv":
            masked_df.write_csv(output)
        elif suffix == ".parquet":
            masked_df.write_parquet(output)
        elif suffix == ".json":
            masked_df.write_json(output)
        else:
            # Default to CSV
            masked_df.write_csv(output)

        return MaskResult(
            source=source,
            output_path=str(output_path.absolute()),
            row_count=row_count,
            column_count=len(all_columns),
            columns_masked=columns_masked,
            strategy=strategy,
            original_columns=all_columns,
        )

    def shutdown(self) -> None:
        """Shutdown the executor."""
        self._executor.shutdown(wait=False)


# Singleton instance
_adapter: TruthoundAdapter | None = None


def get_adapter() -> TruthoundAdapter:
    """Get singleton adapter instance.

    Returns:
        TruthoundAdapter singleton.
    """
    global _adapter
    if _adapter is None:
        from truthound_dashboard.config import get_settings

        settings = get_settings()
        _adapter = TruthoundAdapter(max_workers=settings.max_workers)
    return _adapter


def reset_adapter() -> None:
    """Reset adapter singleton (for testing)."""
    global _adapter
    if _adapter is not None:
        _adapter.shutdown()
        _adapter = None
