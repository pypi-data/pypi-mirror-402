"""Plugin Sandbox for secure code execution.

This module provides a sandboxed execution environment for
plugin code with resource limits and security restrictions.
"""

from __future__ import annotations

import ast
import io
import logging
import sys
import traceback
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SandboxConfig:
    """Configuration for the plugin sandbox.

    Attributes:
        enabled: Whether sandbox is enabled.
        memory_limit_mb: Memory limit in MB.
        cpu_time_limit_seconds: CPU time limit in seconds.
        network_enabled: Whether network access is allowed.
        allowed_modules: List of allowed Python modules.
        blocked_modules: List of blocked Python modules.
        max_output_size: Maximum output size in bytes.
    """

    enabled: bool = True
    memory_limit_mb: int = 256
    cpu_time_limit_seconds: int = 30
    network_enabled: bool = False
    allowed_modules: list[str] = field(default_factory=list)
    blocked_modules: list[str] = field(
        default_factory=lambda: [
            "os",
            "subprocess",
            "sys",
            "shutil",
            "socket",
            "http",
            "urllib",
            "requests",
            "httpx",
            "multiprocessing",
            "threading",
            "ctypes",
            "pickle",
            "shelve",
            "sqlite3",
            "importlib",
            "__builtin__",
            "builtins",
        ]
    )
    max_output_size: int = 1024 * 1024  # 1MB
    allowed_builtins: list[str] = field(
        default_factory=lambda: [
            "abs",
            "all",
            "any",
            "ascii",
            "bin",
            "bool",
            "bytearray",
            "bytes",
            "callable",
            "chr",
            "classmethod",
            "complex",
            "dict",
            "dir",
            "divmod",
            "enumerate",
            "filter",
            "float",
            "format",
            "frozenset",
            "getattr",
            "hasattr",
            "hash",
            "hex",
            "id",
            "int",
            "isinstance",
            "issubclass",
            "iter",
            "len",
            "list",
            "map",
            "max",
            "min",
            "next",
            "object",
            "oct",
            "ord",
            "pow",
            "print",
            "property",
            "range",
            "repr",
            "reversed",
            "round",
            "set",
            "setattr",
            "slice",
            "sorted",
            "staticmethod",
            "str",
            "sum",
            "super",
            "tuple",
            "type",
            "vars",
            "zip",
        ]
    )


class SandboxSecurityError(Exception):
    """Raised when sandbox security is violated."""

    pass


class SandboxTimeoutError(Exception):
    """Raised when sandbox execution times out."""

    pass


class SandboxMemoryError(Exception):
    """Raised when sandbox memory limit is exceeded."""

    pass


class RestrictedImporter:
    """Custom importer that restricts module imports.

    This importer blocks dangerous modules and only allows
    a whitelist of safe modules.
    """

    def __init__(self, blocked_modules: list[str], allowed_modules: list[str]) -> None:
        """Initialize the restricted importer.

        Args:
            blocked_modules: List of blocked module names.
            allowed_modules: List of allowed module names.
        """
        self.blocked_modules = set(blocked_modules)
        self.allowed_modules = set(allowed_modules)
        # Always allow these safe modules for data processing
        self.safe_modules = {
            "math",
            "statistics",
            "decimal",
            "fractions",
            "random",
            "re",
            "json",
            "datetime",
            "collections",
            "itertools",
            "functools",
            "operator",
            "string",
            "textwrap",
            "unicodedata",
            "typing",
            "dataclasses",
            "enum",
            "copy",
            "numbers",
            "hashlib",
            "hmac",
            "base64",
            "binascii",
            "io",
            "csv",
        }
        self.allowed_modules.update(self.safe_modules)

    def find_module(self, name: str, path: list[str] | None = None) -> "RestrictedImporter | None":
        """Check if module import should be blocked.

        Args:
            name: Module name.
            path: Module path.

        Returns:
            Self if import should be checked, None otherwise.
        """
        base_module = name.split(".")[0]

        # Check if blocked
        if base_module in self.blocked_modules:
            return self

        # Check if allowed
        if self.allowed_modules and base_module not in self.allowed_modules:
            return self

        return None

    def load_module(self, name: str) -> Any:
        """Block the module load.

        Args:
            name: Module name.

        Raises:
            SandboxSecurityError: Always, since this is only called for blocked imports.
        """
        raise SandboxSecurityError(f"Import of module '{name}' is not allowed in sandbox")


class CodeAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze code for security issues.

    This analyzer checks for dangerous constructs like:
    - Blocked function calls (eval, exec, compile, etc.)
    - Blocked attribute access
    - Potentially dangerous patterns
    """

    BLOCKED_FUNCTIONS = {
        "eval",
        "exec",
        "compile",
        "open",
        "input",
        "__import__",
        "globals",
        "locals",
        "vars",
        "dir",
        "getattr",
        "setattr",
        "delattr",
        "breakpoint",
        "exit",
        "quit",
    }

    BLOCKED_ATTRIBUTES = {
        "__class__",
        "__bases__",
        "__subclasses__",
        "__mro__",
        "__code__",
        "__globals__",
        "__builtins__",
        "__dict__",
        "__closure__",
        "__func__",
        "__self__",
        "__module__",
        "__qualname__",
        "__annotations__",
    }

    def __init__(self) -> None:
        """Initialize the analyzer."""
        self.issues: list[str] = []
        self.warnings: list[str] = []

    def visit_Call(self, node: ast.Call) -> None:
        """Check function calls.

        Args:
            node: Call AST node.
        """
        # Check for blocked function names
        if isinstance(node.func, ast.Name):
            if node.func.id in self.BLOCKED_FUNCTIONS:
                self.issues.append(f"Blocked function call: {node.func.id}")
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr in self.BLOCKED_FUNCTIONS:
                self.issues.append(f"Blocked function call: {node.func.attr}")

        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Check attribute access.

        Args:
            node: Attribute AST node.
        """
        if node.attr in self.BLOCKED_ATTRIBUTES:
            self.issues.append(f"Blocked attribute access: {node.attr}")

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        """Check imports.

        Args:
            node: Import AST node.
        """
        for alias in node.names:
            self.warnings.append(f"Import statement: {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Check from imports.

        Args:
            node: ImportFrom AST node.
        """
        self.warnings.append(f"Import from: {node.module}")
        self.generic_visit(node)

    def analyze(self, code: str) -> tuple[list[str], list[str]]:
        """Analyze code for security issues.

        Args:
            code: Python source code.

        Returns:
            Tuple of (issues, warnings).
        """
        try:
            tree = ast.parse(code)
            self.visit(tree)
        except SyntaxError as e:
            self.issues.append(f"Syntax error: {e}")

        return self.issues, self.warnings


@dataclass
class SandboxResult:
    """Result of sandbox execution.

    Attributes:
        success: Whether execution succeeded.
        result: Return value if any.
        error: Error message if failed.
        stdout: Captured stdout.
        stderr: Captured stderr.
        execution_time_ms: Execution time in milliseconds.
        memory_used_mb: Approximate memory used in MB.
    """

    success: bool
    result: Any = None
    error: str | None = None
    stdout: str = ""
    stderr: str = ""
    execution_time_ms: float = 0
    memory_used_mb: float | None = None
    warnings: list[str] = field(default_factory=list)


class PluginSandbox:
    """Sandboxed execution environment for plugin code.

    This class provides a secure environment for executing
    untrusted plugin code with various safety restrictions.

    Attributes:
        config: Sandbox configuration.
    """

    def __init__(self, config: SandboxConfig | None = None) -> None:
        """Initialize the sandbox.

        Args:
            config: Sandbox configuration.
        """
        self.config = config or SandboxConfig()

    def analyze_code(self, code: str) -> tuple[list[str], list[str]]:
        """Analyze code for security issues without executing.

        Args:
            code: Python source code.

        Returns:
            Tuple of (issues, warnings).
        """
        analyzer = CodeAnalyzer()
        return analyzer.analyze(code)

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

    @contextmanager
    def _restricted_imports(self):
        """Context manager to restrict imports."""
        importer = RestrictedImporter(
            blocked_modules=self.config.blocked_modules,
            allowed_modules=self.config.allowed_modules,
        )
        sys.meta_path.insert(0, importer)
        try:
            yield
        finally:
            sys.meta_path.remove(importer)

    def _create_safe_builtins(self) -> dict[str, Any]:
        """Create a restricted builtins dictionary.

        Returns:
            Dictionary of allowed builtins.
        """
        import builtins

        safe_builtins = {}
        for name in self.config.allowed_builtins:
            if hasattr(builtins, name):
                safe_builtins[name] = getattr(builtins, name)

        # Add None, True, False
        safe_builtins["None"] = None
        safe_builtins["True"] = True
        safe_builtins["False"] = False

        # Add safe exceptions
        safe_builtins["Exception"] = Exception
        safe_builtins["ValueError"] = ValueError
        safe_builtins["TypeError"] = TypeError
        safe_builtins["KeyError"] = KeyError
        safe_builtins["IndexError"] = IndexError
        safe_builtins["AttributeError"] = AttributeError
        safe_builtins["RuntimeError"] = RuntimeError
        safe_builtins["StopIteration"] = StopIteration

        return safe_builtins

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
        import time

        if not self.config.enabled:
            # Execute without sandbox
            return self._execute_unsafe(code, globals_dict, locals_dict, entry_point, entry_args)

        # Analyze code first
        issues, warnings = self.analyze_code(code)
        if issues:
            return SandboxResult(
                success=False,
                error=f"Code analysis failed: {'; '.join(issues)}",
                warnings=warnings,
            )

        start_time = time.perf_counter()

        # Create execution environment
        safe_globals = globals_dict.copy() if globals_dict else {}
        safe_globals["__builtins__"] = self._create_safe_builtins()

        safe_locals = locals_dict.copy() if locals_dict else {}

        result = None
        error = None
        stdout_str = ""
        stderr_str = ""

        try:
            with self._capture_output() as (stdout, stderr):
                with self._restricted_imports():
                    # Compile and execute
                    compiled = compile(code, "<sandbox>", "exec")
                    exec(compiled, safe_globals, safe_locals)

                    # Call entry point if specified
                    if entry_point and entry_point in safe_locals:
                        func = safe_locals[entry_point]
                        if callable(func):
                            result = func(**(entry_args or {}))
                        else:
                            error = f"Entry point '{entry_point}' is not callable"
                    elif entry_point:
                        error = f"Entry point '{entry_point}' not found"

                stdout_str = stdout.getvalue()
                stderr_str = stderr.getvalue()

                # Truncate output if too large
                max_size = self.config.max_output_size
                if len(stdout_str) > max_size:
                    stdout_str = stdout_str[:max_size] + "\n... (truncated)"
                if len(stderr_str) > max_size:
                    stderr_str = stderr_str[:max_size] + "\n... (truncated)"

        except SandboxSecurityError as e:
            error = f"Security violation: {e}"
        except SandboxTimeoutError as e:
            error = f"Timeout: {e}"
        except SandboxMemoryError as e:
            error = f"Memory limit exceeded: {e}"
        except Exception as e:
            error = f"Execution error: {type(e).__name__}: {e}\n{traceback.format_exc()}"

        execution_time = (time.perf_counter() - start_time) * 1000

        return SandboxResult(
            success=error is None,
            result=result,
            error=error,
            stdout=stdout_str,
            stderr=stderr_str,
            execution_time_ms=execution_time,
            warnings=warnings,
        )

    def _execute_unsafe(
        self,
        code: str,
        globals_dict: dict[str, Any] | None = None,
        locals_dict: dict[str, Any] | None = None,
        entry_point: str | None = None,
        entry_args: dict[str, Any] | None = None,
    ) -> SandboxResult:
        """Execute code without sandbox restrictions.

        Args:
            code: Python source code.
            globals_dict: Global variables.
            locals_dict: Local variables.
            entry_point: Function to call.
            entry_args: Arguments for entry point.

        Returns:
            SandboxResult.
        """
        import time

        start_time = time.perf_counter()

        exec_globals = globals_dict.copy() if globals_dict else {}
        exec_locals = locals_dict.copy() if locals_dict else {}

        result = None
        error = None
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
                elif entry_point:
                    error = f"Entry point '{entry_point}' not found"

                stdout_str = stdout.getvalue()
                stderr_str = stderr.getvalue()

        except Exception as e:
            error = f"Execution error: {type(e).__name__}: {e}\n{traceback.format_exc()}"

        execution_time = (time.perf_counter() - start_time) * 1000

        return SandboxResult(
            success=error is None,
            result=result,
            error=error,
            stdout=stdout_str,
            stderr=stderr_str,
            execution_time_ms=execution_time,
        )

    def validate_code(self, code: str) -> tuple[bool, list[str]]:
        """Validate code without executing.

        Args:
            code: Python source code.

        Returns:
            Tuple of (is_valid, list of issues).
        """
        issues, _ = self.analyze_code(code)
        return len(issues) == 0, issues
