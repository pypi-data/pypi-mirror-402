"""Sandbox Engine Implementations.

This module provides sandbox engines with different isolation levels:
- NoOpSandbox: No isolation (trusted plugins only)
- ProcessSandbox: Subprocess isolation with resource limits
- ContainerSandbox: Docker/Podman container isolation
"""

from __future__ import annotations

import io
import json
import logging
import os
import signal
import subprocess
import sys
import tempfile
import time
import traceback
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any

from .protocols import (
    SandboxConfig,
    SandboxError,
    SandboxMemoryError,
    SandboxResult,
    SandboxSecurityError,
    SandboxTimeoutError,
)
from .code_validator import (
    CodeValidator,
    RestrictedImporter,
    create_safe_builtins,
)

logger = logging.getLogger(__name__)


class SandboxEngine(ABC):
    """Abstract base class for sandbox engines."""

    @property
    @abstractmethod
    def isolation_level(self) -> str:
        """Get the isolation level."""
        ...

    @abstractmethod
    def execute(
        self,
        code: str,
        globals_dict: dict[str, Any] | None = None,
        locals_dict: dict[str, Any] | None = None,
        entry_point: str | None = None,
        entry_args: dict[str, Any] | None = None,
    ) -> SandboxResult:
        """Execute code in the sandbox.

        Args:
            code: Python source code to execute.
            globals_dict: Global variables to provide.
            locals_dict: Local variables to provide.
            entry_point: Function name to call after execution.
            entry_args: Arguments to pass to entry point.

        Returns:
            SandboxResult with execution results.
        """
        ...

    def validate_code(self, code: str) -> tuple[bool, list[str]]:
        """Validate code before execution.

        Args:
            code: Python source code.

        Returns:
            Tuple of (is_valid, list of issues).
        """
        validator = CodeValidator()
        return validator.validate(code)


class NoOpSandbox(SandboxEngine):
    """No-isolation sandbox for trusted plugins."""

    def __init__(self, config: SandboxConfig | None = None) -> None:
        """Initialize the sandbox.

        Args:
            config: Sandbox configuration (mostly ignored).
        """
        self.config = config or SandboxConfig(enabled=False)

    @property
    def isolation_level(self) -> str:
        """Get the isolation level."""
        return "none"

    @contextmanager
    def _capture_output(self):
        """Context manager to capture stdout and stderr."""
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        try:
            yield sys.stdout, sys.stderr
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    def execute(
        self,
        code: str,
        globals_dict: dict[str, Any] | None = None,
        locals_dict: dict[str, Any] | None = None,
        entry_point: str | None = None,
        entry_args: dict[str, Any] | None = None,
    ) -> SandboxResult:
        """Execute code without isolation."""
        start_time = time.perf_counter()

        exec_globals = globals_dict.copy() if globals_dict else {}
        exec_locals = locals_dict.copy() if locals_dict else {}

        result = None
        error = None
        error_type = None
        stdout_str = ""
        stderr_str = ""

        try:
            with self._capture_output() as (stdout, stderr):
                exec(code, exec_globals, exec_locals)

                if entry_point and entry_point in exec_locals:
                    func = exec_locals[entry_point]
                    if callable(func):
                        result = func(**(entry_args or {}))
                    else:
                        error = f"Entry point '{entry_point}' is not callable"
                        error_type = "ValueError"
                elif entry_point:
                    error = f"Entry point '{entry_point}' not found"
                    error_type = "KeyError"

                stdout_str = stdout.getvalue()
                stderr_str = stderr.getvalue()

        except Exception as e:
            error = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
            error_type = type(e).__name__

        execution_time = (time.perf_counter() - start_time) * 1000

        return SandboxResult(
            success=error is None,
            result=result,
            error=error,
            error_type=error_type,
            stdout=stdout_str,
            stderr=stderr_str,
            execution_time_ms=execution_time,
        )


class ProcessSandbox(SandboxEngine):
    """Process-based sandbox with resource limits."""

    # Template for subprocess execution
    RUNNER_TEMPLATE = '''
import sys
import json
import traceback

# Restore builtins for runner
import builtins
__builtins__ = builtins

def main():
    # Read input
    input_data = json.loads(sys.stdin.read())

    code = input_data["code"]
    globals_dict = input_data.get("globals", {})
    locals_dict = input_data.get("locals", {})
    entry_point = input_data.get("entry_point")
    entry_args = input_data.get("entry_args", {})
    safe_builtins = input_data.get("safe_builtins", [])
    blocked_modules = input_data.get("blocked_modules", [])

    # Create restricted environment
    import ast

    class RestrictedImporter:
        SAFE_MODULES = {
            "math", "statistics", "decimal", "fractions",
            "random", "re", "json", "datetime",
            "collections", "itertools", "functools",
            "operator", "string", "textwrap", "unicodedata",
            "typing", "dataclasses", "enum", "copy",
            "numbers", "hashlib", "hmac", "base64",
            "binascii", "io", "csv", "abc", "contextlib",
        }

        def __init__(self, blocked):
            self.blocked = set(blocked)

        def find_module(self, name, path=None):
            base = name.split(".")[0]
            if base in self.blocked:
                return self
            if base not in self.SAFE_MODULES:
                return self
            return None

        def load_module(self, name):
            raise ImportError(f"Import of '{name}' is not allowed")

    # Install import restrictions
    sys.meta_path.insert(0, RestrictedImporter(blocked_modules))

    # Create safe builtins
    safe_builtin_dict = {}
    for name in safe_builtins:
        if hasattr(builtins, name):
            safe_builtin_dict[name] = getattr(builtins, name)

    safe_builtin_dict["None"] = None
    safe_builtin_dict["True"] = True
    safe_builtin_dict["False"] = False
    safe_builtin_dict["__name__"] = "__sandbox__"

    # Add safe exceptions
    for exc in ["Exception", "ValueError", "TypeError", "KeyError", "IndexError",
                "AttributeError", "RuntimeError", "StopIteration", "ImportError"]:
        if hasattr(builtins, exc):
            safe_builtin_dict[exc] = getattr(builtins, exc)

    # Prepare execution environment
    exec_globals = globals_dict.copy()
    exec_globals["__builtins__"] = safe_builtin_dict
    exec_locals = locals_dict.copy()

    result = None
    error = None
    error_type = None

    try:
        # Execute code
        exec(code, exec_globals, exec_locals)

        # Call entry point if specified
        if entry_point:
            if entry_point in exec_locals:
                func = exec_locals[entry_point]
                if callable(func):
                    result = func(**entry_args)
                else:
                    error = f"Entry point '{entry_point}' is not callable"
                    error_type = "ValueError"
            else:
                error = f"Entry point '{entry_point}' not found"
                error_type = "KeyError"

    except Exception as e:
        error = f"{type(e).__name__}: {e}"
        error_type = type(e).__name__

    # Output result
    output = {
        "success": error is None,
        "result": result if is_json_serializable(result) else str(result),
        "error": error,
        "error_type": error_type,
    }

    print("__RESULT_START__")
    print(json.dumps(output))
    print("__RESULT_END__")

def is_json_serializable(obj):
    try:
        json.dumps(obj)
        return True
    except (TypeError, ValueError):
        return False

if __name__ == "__main__":
    main()
'''

    def __init__(self, config: SandboxConfig | None = None) -> None:
        """Initialize the sandbox.

        Args:
            config: Sandbox configuration.
        """
        self.config = config or SandboxConfig()

    @property
    def isolation_level(self) -> str:
        """Get the isolation level."""
        return "process"

    def execute(
        self,
        code: str,
        globals_dict: dict[str, Any] | None = None,
        locals_dict: dict[str, Any] | None = None,
        entry_point: str | None = None,
        entry_args: dict[str, Any] | None = None,
    ) -> SandboxResult:
        """Execute code in a subprocess."""
        start_time = time.perf_counter()

        # Validate code first
        is_valid, issues = self.validate_code(code)
        if not is_valid:
            return SandboxResult(
                success=False,
                error=f"Code validation failed: {'; '.join(issues)}",
                error_type="SandboxSecurityError",
                warnings=issues,
            )

        # Prepare input data
        input_data = {
            "code": code,
            "globals": self._serialize_dict(globals_dict or {}),
            "locals": self._serialize_dict(locals_dict or {}),
            "entry_point": entry_point,
            "entry_args": entry_args or {},
            "safe_builtins": self.config.allowed_builtins,
            "blocked_modules": self.config.blocked_modules,
        }

        # Write runner script to temp file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as runner_file:
            runner_file.write(self.RUNNER_TEMPLATE)
            runner_path = runner_file.name

        try:
            # Build subprocess command
            cmd = [sys.executable, "-u", runner_path]

            # Start subprocess
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=self._get_restricted_env(),
            )

            try:
                # Send input and get output
                stdout, stderr = process.communicate(
                    input=json.dumps(input_data),
                    timeout=self.config.wall_time_limit_sec,
                )
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                return SandboxResult(
                    success=False,
                    error=f"Execution timed out after {self.config.wall_time_limit_sec}s",
                    error_type="SandboxTimeoutError",
                    exit_code=-9,
                )

            # Parse result
            result = self._parse_output(stdout, stderr, process.returncode)
            result.execution_time_ms = (time.perf_counter() - start_time) * 1000
            result.exit_code = process.returncode
            return result

        finally:
            # Clean up runner script
            try:
                os.unlink(runner_path)
            except Exception:
                pass

    def _serialize_dict(self, d: dict[str, Any]) -> dict[str, Any]:
        """Serialize dictionary for JSON transport."""
        result = {}
        for key, value in d.items():
            try:
                json.dumps(value)
                result[key] = value
            except (TypeError, ValueError):
                # Skip non-serializable values
                pass
        return result

    def _get_restricted_env(self) -> dict[str, str]:
        """Get restricted environment variables."""
        env = os.environ.copy()
        # Remove potentially dangerous env vars
        for key in ["LD_PRELOAD", "LD_LIBRARY_PATH", "PYTHONSTARTUP"]:
            env.pop(key, None)
        return env

    def _parse_output(
        self, stdout: str, stderr: str, exit_code: int
    ) -> SandboxResult:
        """Parse subprocess output."""
        # Look for result markers
        if "__RESULT_START__" in stdout and "__RESULT_END__" in stdout:
            try:
                start = stdout.index("__RESULT_START__") + len("__RESULT_START__")
                end = stdout.index("__RESULT_END__")
                result_json = stdout[start:end].strip()
                result_data = json.loads(result_json)

                # Extract stdout before markers
                clean_stdout = stdout[:stdout.index("__RESULT_START__")].strip()

                return SandboxResult(
                    success=result_data.get("success", False),
                    result=result_data.get("result"),
                    error=result_data.get("error"),
                    error_type=result_data.get("error_type"),
                    stdout=clean_stdout,
                    stderr=stderr,
                )
            except (json.JSONDecodeError, ValueError) as e:
                return SandboxResult(
                    success=False,
                    error=f"Failed to parse result: {e}",
                    error_type="ParseError",
                    stdout=stdout,
                    stderr=stderr,
                )

        # No result markers found - execution error
        if exit_code != 0:
            return SandboxResult(
                success=False,
                error=f"Process exited with code {exit_code}",
                error_type="ProcessError",
                stdout=stdout,
                stderr=stderr,
            )

        return SandboxResult(
            success=True,
            stdout=stdout,
            stderr=stderr,
        )


class ContainerSandbox(SandboxEngine):
    """Container-based sandbox using Docker or Podman."""

    def __init__(self, config: SandboxConfig | None = None) -> None:
        """Initialize the sandbox.

        Args:
            config: Sandbox configuration.
        """
        self.config = config or SandboxConfig(isolation_level="container")
        self._container_runtime = self._detect_runtime()

    @property
    def isolation_level(self) -> str:
        """Get the isolation level."""
        return "container"

    def _detect_runtime(self) -> str | None:
        """Detect available container runtime."""
        for runtime in ["docker", "podman"]:
            try:
                result = subprocess.run(
                    [runtime, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    logger.info(f"Using container runtime: {runtime}")
                    return runtime
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        return None

    def is_available(self) -> bool:
        """Check if container runtime is available."""
        return self._container_runtime is not None

    def execute(
        self,
        code: str,
        globals_dict: dict[str, Any] | None = None,
        locals_dict: dict[str, Any] | None = None,
        entry_point: str | None = None,
        entry_args: dict[str, Any] | None = None,
    ) -> SandboxResult:
        """Execute code in a container."""
        if not self._container_runtime:
            # Fall back to process sandbox
            logger.warning("Container runtime not available, using process sandbox")
            return ProcessSandbox(self.config).execute(
                code, globals_dict, locals_dict, entry_point, entry_args
            )

        start_time = time.perf_counter()

        # Validate code first
        is_valid, issues = self.validate_code(code)
        if not is_valid:
            return SandboxResult(
                success=False,
                error=f"Code validation failed: {'; '.join(issues)}",
                error_type="SandboxSecurityError",
                warnings=issues,
            )

        # Create temp directory for code
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write code to file
            code_path = os.path.join(tmpdir, "code.py")
            with open(code_path, "w") as f:
                f.write(self._wrap_code(code, entry_point, entry_args))

            # Write input data
            input_path = os.path.join(tmpdir, "input.json")
            input_data = {
                "globals": self._serialize_dict(globals_dict or {}),
                "locals": self._serialize_dict(locals_dict or {}),
            }
            with open(input_path, "w") as f:
                json.dump(input_data, f)

            # Build container command
            cmd = self._build_container_command(tmpdir)

            try:
                # Run container
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

                try:
                    stdout, stderr = process.communicate(
                        timeout=self.config.wall_time_limit_sec
                    )
                except subprocess.TimeoutExpired:
                    # Kill container
                    subprocess.run(
                        [self._container_runtime, "kill", f"sandbox_{os.getpid()}"],
                        capture_output=True,
                    )
                    process.kill()
                    process.wait()
                    return SandboxResult(
                        success=False,
                        error=f"Execution timed out after {self.config.wall_time_limit_sec}s",
                        error_type="SandboxTimeoutError",
                        exit_code=-9,
                    )

                # Parse output
                result = self._parse_container_output(stdout, stderr, process.returncode)
                result.execution_time_ms = (time.perf_counter() - start_time) * 1000
                result.exit_code = process.returncode
                return result

            except Exception as e:
                return SandboxResult(
                    success=False,
                    error=f"Container execution failed: {e}",
                    error_type="ContainerError",
                )

    def _wrap_code(
        self,
        code: str,
        entry_point: str | None,
        entry_args: dict[str, Any] | None,
    ) -> str:
        """Wrap code for container execution."""
        wrapper = f'''
import sys
import json

# Execute user code
{code}

# Call entry point if specified
if __name__ == "__main__":
    result = None
    error = None

    try:
        entry_point = {repr(entry_point)}
        entry_args = {repr(entry_args or {})}

        if entry_point:
            func = locals().get(entry_point) or globals().get(entry_point)
            if func and callable(func):
                result = func(**entry_args)
            elif func:
                error = f"Entry point '{{entry_point}}' is not callable"
            else:
                error = f"Entry point '{{entry_point}}' not found"
    except Exception as e:
        error = f"{{type(e).__name__}}: {{e}}"

    output = {{
        "success": error is None,
        "result": result,
        "error": error,
    }}
    print("__RESULT__" + json.dumps(output))
'''
        return wrapper

    def _build_container_command(self, tmpdir: str) -> list[str]:
        """Build container run command."""
        cmd = [
            self._container_runtime,
            "run",
            "--rm",
            "--name", f"sandbox_{os.getpid()}",
            # Resource limits
            f"--memory={self.config.memory_limit_mb}m",
            f"--cpus={self.config.max_processes}",
            "--pids-limit", str(self.config.max_processes * 10),
            # Security
            "--read-only",
            "--security-opt", "no-new-privileges",
            "--cap-drop", "ALL",
        ]

        # Network
        if not self.config.network_enabled:
            cmd.extend(["--network", "none"])

        # Mount code directory
        cmd.extend(["-v", f"{tmpdir}:/sandbox:ro"])
        cmd.extend(["-w", "/sandbox"])

        # Image and command
        cmd.append(self.config.container_image)
        cmd.extend(["python", "/sandbox/code.py"])

        return cmd

    def _serialize_dict(self, d: dict[str, Any]) -> dict[str, Any]:
        """Serialize dictionary for JSON transport."""
        result = {}
        for key, value in d.items():
            try:
                json.dumps(value)
                result[key] = value
            except (TypeError, ValueError):
                pass
        return result

    def _parse_container_output(
        self, stdout: str, stderr: str, exit_code: int
    ) -> SandboxResult:
        """Parse container output."""
        # Look for result marker
        if "__RESULT__" in stdout:
            try:
                idx = stdout.index("__RESULT__")
                result_json = stdout[idx + len("__RESULT__"):].strip()
                result_data = json.loads(result_json)

                clean_stdout = stdout[:idx].strip()

                return SandboxResult(
                    success=result_data.get("success", False),
                    result=result_data.get("result"),
                    error=result_data.get("error"),
                    stdout=clean_stdout,
                    stderr=stderr,
                )
            except (json.JSONDecodeError, ValueError) as e:
                return SandboxResult(
                    success=False,
                    error=f"Failed to parse result: {e}",
                    stdout=stdout,
                    stderr=stderr,
                )

        if exit_code != 0:
            return SandboxResult(
                success=False,
                error=f"Container exited with code {exit_code}",
                stdout=stdout,
                stderr=stderr,
            )

        return SandboxResult(
            success=True,
            stdout=stdout,
            stderr=stderr,
        )


def create_sandbox(config: SandboxConfig | None = None) -> SandboxEngine:
    """Create a sandbox engine based on configuration.

    Args:
        config: Sandbox configuration.

    Returns:
        Appropriate SandboxEngine instance.
    """
    config = config or SandboxConfig()

    if not config.enabled:
        return NoOpSandbox(config)

    if config.isolation_level == "container":
        sandbox = ContainerSandbox(config)
        if sandbox.is_available():
            return sandbox
        logger.warning("Container sandbox not available, falling back to process")
        config.isolation_level = "process"

    if config.isolation_level == "process":
        return ProcessSandbox(config)

    return NoOpSandbox(config)


def get_available_engines() -> list[dict[str, Any]]:
    """Get list of available sandbox engines.

    Returns:
        List of engine information dictionaries.
    """
    engines = [
        {
            "name": "none",
            "description": "No isolation (trusted plugins only)",
            "available": True,
        },
        {
            "name": "process",
            "description": "Subprocess isolation with resource limits",
            "available": True,
        },
    ]

    # Check container availability
    container_sandbox = ContainerSandbox()
    engines.append({
        "name": "container",
        "description": "Docker/Podman container isolation",
        "available": container_sandbox.is_available(),
        "runtime": container_sandbox._container_runtime,
    })

    return engines
