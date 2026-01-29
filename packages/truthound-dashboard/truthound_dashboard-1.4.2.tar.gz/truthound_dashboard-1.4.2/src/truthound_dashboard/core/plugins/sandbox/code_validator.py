"""Code Validation and Restriction Utilities.

This module provides utilities for validating and restricting
code execution in the sandbox.
"""

from __future__ import annotations

import ast
import sys
from typing import Any

from .protocols import SandboxSecurityError


class RestrictedImporter:
    """Custom importer that restricts module imports.

    This importer blocks dangerous modules and only allows
    a whitelist of safe modules.
    """

    # Always safe modules for data processing
    SAFE_MODULES = frozenset({
        "math", "statistics", "decimal", "fractions",
        "random", "re", "json", "datetime",
        "collections", "itertools", "functools",
        "operator", "string", "textwrap", "unicodedata",
        "typing", "dataclasses", "enum", "copy",
        "numbers", "hashlib", "hmac", "base64",
        "binascii", "io", "csv", "abc",
        "contextlib", "warnings",
    })

    def __init__(
        self,
        blocked_modules: list[str] | None = None,
        allowed_modules: list[str] | None = None,
    ) -> None:
        """Initialize the restricted importer.

        Args:
            blocked_modules: List of blocked module names.
            allowed_modules: List of additional allowed module names.
        """
        self.blocked_modules = set(blocked_modules or [])
        self.allowed_modules = set(allowed_modules or [])
        self.allowed_modules.update(self.SAFE_MODULES)

    def find_module(
        self, name: str, path: list[str] | None = None
    ) -> "RestrictedImporter | None":
        """Check if module import should be blocked.

        Args:
            name: Module name.
            path: Module path.

        Returns:
            Self if import should be checked, None otherwise.
        """
        base_module = name.split(".")[0]

        # Check if explicitly blocked
        if base_module in self.blocked_modules:
            return self

        # Check if not in allowed list
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
        raise SandboxSecurityError(
            f"Import of module '{name}' is not allowed in sandbox"
        )


class CodeValidator:
    """Validates code before execution."""

    # Dangerous function calls
    BLOCKED_FUNCTIONS = frozenset({
        "eval", "exec", "compile",
        "open", "input",
        "__import__",
        "globals", "locals", "vars",
        "getattr", "setattr", "delattr",
        "breakpoint", "exit", "quit",
    })

    # Dangerous attribute accesses
    BLOCKED_ATTRIBUTES = frozenset({
        "__class__", "__bases__", "__subclasses__", "__mro__",
        "__code__", "__globals__", "__builtins__",
        "__dict__", "__closure__", "__func__",
        "__self__", "__module__", "__qualname__",
        "__annotations__", "__reduce__", "__reduce_ex__",
    })

    def __init__(self, blocked_modules: list[str] | None = None) -> None:
        """Initialize the validator.

        Args:
            blocked_modules: Additional blocked modules.
        """
        self.blocked_modules = set(blocked_modules or [])
        self.issues: list[str] = []
        self.warnings: list[str] = []

    def validate(self, code: str) -> tuple[bool, list[str]]:
        """Validate code for security issues.

        Args:
            code: Python source code.

        Returns:
            Tuple of (is_valid, list of issues).
        """
        self.issues = []
        self.warnings = []

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, [f"Syntax error: {e}"]

        self._visit(tree)
        return len(self.issues) == 0, self.issues

    def _visit(self, node: ast.AST) -> None:
        """Visit AST node and check for issues."""
        # Check function calls
        if isinstance(node, ast.Call):
            self._check_call(node)

        # Check attribute access
        elif isinstance(node, ast.Attribute):
            self._check_attribute(node)

        # Check imports
        elif isinstance(node, ast.Import):
            self._check_import(node)

        elif isinstance(node, ast.ImportFrom):
            self._check_import_from(node)

        # Visit children
        for child in ast.iter_child_nodes(node):
            self._visit(child)

    def _check_call(self, node: ast.Call) -> None:
        """Check function call for blocked functions."""
        func_name = None

        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        if func_name and func_name in self.BLOCKED_FUNCTIONS:
            self.issues.append(f"Blocked function call: {func_name}")

    def _check_attribute(self, node: ast.Attribute) -> None:
        """Check attribute access for blocked attributes."""
        if node.attr in self.BLOCKED_ATTRIBUTES:
            self.issues.append(f"Blocked attribute access: {node.attr}")

    def _check_import(self, node: ast.Import) -> None:
        """Check import statement for blocked modules."""
        for alias in node.names:
            module = alias.name.split(".")[0]
            if module in self.blocked_modules:
                self.issues.append(f"Blocked module import: {module}")

    def _check_import_from(self, node: ast.ImportFrom) -> None:
        """Check from import for blocked modules."""
        if node.module:
            module = node.module.split(".")[0]
            if module in self.blocked_modules:
                self.issues.append(f"Blocked module import: {module}")


def create_safe_builtins(allowed_builtins: list[str] | None = None) -> dict[str, Any]:
    """Create a restricted builtins dictionary.

    Args:
        allowed_builtins: List of allowed builtin names.

    Returns:
        Dictionary of allowed builtins.
    """
    import builtins

    default_allowed = [
        "abs", "all", "any", "ascii", "bin", "bool",
        "bytearray", "bytes", "callable", "chr", "classmethod",
        "complex", "dict", "divmod", "enumerate",
        "filter", "float", "format", "frozenset",
        "hasattr", "hash", "hex", "id", "int", "isinstance",
        "issubclass", "iter", "len", "list", "map", "max",
        "min", "next", "object", "oct", "ord", "pow",
        "print", "property", "range", "repr", "reversed",
        "round", "set", "slice", "sorted",
        "staticmethod", "str", "sum", "super", "tuple",
        "type", "zip",
    ]

    allowed = allowed_builtins or default_allowed
    safe_builtins: dict[str, Any] = {}

    for name in allowed:
        if hasattr(builtins, name):
            safe_builtins[name] = getattr(builtins, name)

    # Add essential values
    safe_builtins["None"] = None
    safe_builtins["True"] = True
    safe_builtins["False"] = False
    safe_builtins["__name__"] = "__sandbox__"
    safe_builtins["__doc__"] = None

    # Add safe exceptions
    safe_exceptions = [
        "Exception", "ValueError", "TypeError", "KeyError",
        "IndexError", "AttributeError", "RuntimeError",
        "StopIteration", "NotImplementedError", "ZeroDivisionError",
        "AssertionError", "ImportError", "OverflowError",
    ]
    for exc_name in safe_exceptions:
        if hasattr(builtins, exc_name):
            safe_builtins[exc_name] = getattr(builtins, exc_name)

    return safe_builtins
