"""Custom Validator Executor.

This module provides execution of custom validators in a safe,
sandboxed environment.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from truthound_dashboard.db.models import CustomValidator, PluginExecutionLog

from .sandbox import create_sandbox, SandboxConfig, SandboxResult

logger = logging.getLogger(__name__)


@dataclass
class ValidatorResult:
    """Result of custom validator execution.

    Attributes:
        passed: Whether validation passed.
        issues: List of validation issues found.
        message: Summary message.
        details: Additional details (JSON-serializable).
        execution_time_ms: Execution time in milliseconds.
    """

    passed: bool
    issues: list[dict[str, Any]] = field(default_factory=list)
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0


@dataclass
class ValidatorContext:
    """Context provided to custom validators.

    Attributes:
        column_name: Name of the column being validated.
        column_values: List of values in the column.
        parameters: Validator parameters.
        schema: Column schema information.
        row_count: Total number of rows.
    """

    column_name: str
    column_values: list[Any]
    parameters: dict[str, Any] = field(default_factory=dict)
    schema: dict[str, Any] = field(default_factory=dict)
    row_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for sandbox execution."""
        return {
            "column_name": self.column_name,
            "values": self.column_values,
            "params": self.parameters,
            "schema": self.schema,
            "row_count": self.row_count,
        }


# Template code that wraps custom validator code
VALIDATOR_WRAPPER_CODE = '''
# Custom validator wrapper
import re
import math
import statistics
from datetime import datetime, date
from collections import Counter

# User-provided validator code
{user_code}

# Entry point
def _execute_validator(column_name, values, params, schema, row_count):
    """Execute the custom validator.

    Args:
        column_name: Name of the column.
        values: List of column values.
        params: Validator parameters.
        schema: Column schema.
        row_count: Total row count.

    Returns:
        Dictionary with 'passed', 'issues', 'message', 'details'.
    """
    # Call the user-defined validate function
    result = validate(column_name, values, params, schema, row_count)

    # Ensure result is properly formatted
    if isinstance(result, bool):
        return {{
            "passed": result,
            "issues": [],
            "message": "Validation passed" if result else "Validation failed",
            "details": {{}}
        }}
    elif isinstance(result, dict):
        return {{
            "passed": result.get("passed", False),
            "issues": result.get("issues", []),
            "message": result.get("message", ""),
            "details": result.get("details", {{}})
        }}
    else:
        return {{
            "passed": False,
            "issues": [],
            "message": f"Invalid result type: {{type(result).__name__}}",
            "details": {{}}
        }}
'''


class CustomValidatorExecutor:
    """Executor for custom validators.

    This class handles the execution of custom validators
    in a sandboxed environment with logging and monitoring.

    Attributes:
        sandbox: Plugin sandbox for secure execution.
        log_executions: Whether to log executions to database.
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

    def validate_validator_code(self, code: str) -> tuple[bool, list[str]]:
        """Validate custom validator code before execution.

        Args:
            code: Python code implementing the validator.

        Returns:
            Tuple of (is_valid, list of issues).
        """
        issues = []

        # Check for required function
        if "def validate(" not in code:
            issues.append("Missing required 'validate' function")

        # Check for dangerous patterns
        dangerous = [
            "os.system",
            "subprocess",
            "exec(",
            "eval(",
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

    async def execute(
        self,
        validator: CustomValidator,
        context: ValidatorContext,
        session: AsyncSession | None = None,
        source_id: str | None = None,
    ) -> ValidatorResult:
        """Execute a custom validator.

        Args:
            validator: CustomValidator model.
            context: Validation context.
            session: Optional database session for logging.
            source_id: Optional source ID for logging.

        Returns:
            ValidatorResult with execution results.
        """
        execution_id = str(uuid.uuid4())
        start_time = datetime.utcnow()

        logger.debug(
            f"Executing custom validator: {validator.name} "
            f"on column: {context.column_name}"
        )

        # Create execution log if logging enabled
        log_entry = None
        if self.log_executions and session and validator.plugin_id:
            log_entry = PluginExecutionLog(
                plugin_id=validator.plugin_id,
                validator_id=str(validator.id),
                execution_id=execution_id,
                source_id=source_id,
                status="running",
            )
            session.add(log_entry)
            await session.flush()

        try:
            # Prepare the code
            wrapped_code = VALIDATOR_WRAPPER_CODE.format(user_code=validator.code)

            # Execute in sandbox
            sandbox_result = self.sandbox.execute(
                code=wrapped_code,
                entry_point="_execute_validator",
                entry_args=context.to_dict(),
            )

            if sandbox_result.success and sandbox_result.result:
                result = ValidatorResult(
                    passed=sandbox_result.result.get("passed", False),
                    issues=sandbox_result.result.get("issues", []),
                    message=sandbox_result.result.get("message", ""),
                    details=sandbox_result.result.get("details", {}),
                    execution_time_ms=sandbox_result.execution_time_ms,
                )
            else:
                result = ValidatorResult(
                    passed=False,
                    message=sandbox_result.error or "Execution failed",
                    details={
                        "stdout": sandbox_result.stdout,
                        "stderr": sandbox_result.stderr,
                    },
                    execution_time_ms=sandbox_result.execution_time_ms,
                )

            # Update validator usage stats
            validator.increment_usage()

            # Update execution log
            if log_entry:
                if result.passed:
                    log_entry.mark_completed(
                        result={"passed": result.passed, "issues_count": len(result.issues)},
                        memory_used_mb=sandbox_result.memory_used_mb,
                    )
                else:
                    log_entry.mark_failed(result.message)

            if session:
                await session.flush()

            return result

        except Exception as e:
            logger.error(f"Custom validator execution failed: {e}")

            if log_entry:
                log_entry.mark_failed(str(e))
                if session:
                    await session.flush()

            return ValidatorResult(
                passed=False,
                message=f"Execution error: {e}",
            )

    async def test_validator(
        self,
        code: str,
        parameters: list[dict[str, Any]],
        test_data: dict[str, Any],
        param_values: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Test a custom validator without saving.

        Args:
            code: Validator code.
            parameters: Parameter definitions.
            test_data: Test data (column_name and values).
            param_values: Parameter values to use.

        Returns:
            Dictionary with test results.
        """
        # Validate code first
        is_valid, issues = self.validate_validator_code(code)
        if not is_valid:
            return {
                "success": False,
                "passed": None,
                "error": f"Code validation failed: {'; '.join(issues)}",
                "execution_time_ms": 0,
                "warnings": issues,
            }

        # Create context
        context = ValidatorContext(
            column_name=test_data.get("column_name", "test_column"),
            column_values=test_data.get("values", []),
            parameters=param_values or {},
            schema=test_data.get("schema", {}),
            row_count=len(test_data.get("values", [])),
        )

        # Execute
        wrapped_code = VALIDATOR_WRAPPER_CODE.format(user_code=code)
        sandbox_result = self.sandbox.execute(
            code=wrapped_code,
            entry_point="_execute_validator",
            entry_args=context.to_dict(),
        )

        if sandbox_result.success and sandbox_result.result:
            return {
                "success": True,
                "passed": sandbox_result.result.get("passed", False),
                "result": sandbox_result.result,
                "execution_time_ms": sandbox_result.execution_time_ms,
                "warnings": sandbox_result.warnings,
            }
        else:
            return {
                "success": False,
                "passed": None,
                "error": sandbox_result.error,
                "execution_time_ms": sandbox_result.execution_time_ms,
                "warnings": sandbox_result.warnings,
            }

    def get_validator_template(self) -> str:
        """Get a template for creating custom validators.

        Returns:
            Template code string.
        """
        return '''
def validate(column_name, values, params, schema, row_count):
    """Custom validator function.

    Args:
        column_name: Name of the column being validated.
        values: List of values in the column.
        params: Dictionary of parameter values.
        schema: Column schema information.
        row_count: Total number of rows.

    Returns:
        Dictionary with:
            - passed: bool - Whether validation passed
            - issues: list - List of issue dictionaries
            - message: str - Summary message
            - details: dict - Additional details
    """
    issues = []

    # Example: Check for null values
    null_count = sum(1 for v in values if v is None)
    if null_count > 0:
        issues.append({
            "row": None,
            "message": f"Found {null_count} null values",
            "severity": "warning"
        })

    # Example: Custom validation logic
    # threshold = params.get("threshold", 0.1)
    # ...

    return {
        "passed": len(issues) == 0,
        "issues": issues,
        "message": f"Validation completed with {len(issues)} issues",
        "details": {
            "null_count": null_count,
            "total_values": len(values)
        }
    }
'''


# Default executor instance
validator_executor = CustomValidatorExecutor()
