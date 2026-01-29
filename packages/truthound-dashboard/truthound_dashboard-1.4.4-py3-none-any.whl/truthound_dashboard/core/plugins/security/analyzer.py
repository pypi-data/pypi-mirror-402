"""Security Analyzer for Plugin Code.

This module provides comprehensive security analysis for plugin code,
including AST-based analysis, permission detection, and risk assessment.
"""

from __future__ import annotations

import ast
import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

from .protocols import TrustLevel, SecurityPolicy

logger = logging.getLogger(__name__)


@dataclass
class CodeAnalysisResult:
    """Result of code analysis.

    Attributes:
        is_safe: Whether code is considered safe.
        issues: Critical security issues found.
        warnings: Non-critical warnings.
        blocked_constructs: List of blocked constructs found.
        detected_imports: List of detected imports.
        detected_permissions: List of detected permission requirements.
        complexity_score: Code complexity score (0-100).
    """

    is_safe: bool
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    blocked_constructs: list[str] = field(default_factory=list)
    detected_imports: list[str] = field(default_factory=list)
    detected_permissions: list[str] = field(default_factory=list)
    complexity_score: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_safe": self.is_safe,
            "issues": self.issues,
            "warnings": self.warnings,
            "blocked_constructs": self.blocked_constructs,
            "detected_imports": self.detected_imports,
            "detected_permissions": self.detected_permissions,
            "complexity_score": self.complexity_score,
        }


@dataclass
class SecurityReport:
    """Comprehensive security report for a plugin.

    Attributes:
        plugin_id: Plugin identifier.
        analyzed_at: When analysis was performed.
        trust_level: Determined trust level.
        is_safe: Whether plugin is considered safe.
        can_run_in_sandbox: Whether code can run in sandbox.
        code_analysis: Code analysis result.
        signature_valid: Whether signature is valid.
        signature_count: Number of valid signatures.
        required_permissions: Required permissions.
        code_hash: SHA256 hash of analyzed code.
        recommendations: Security recommendations.
    """

    plugin_id: str
    analyzed_at: datetime
    trust_level: TrustLevel
    is_safe: bool = False
    can_run_in_sandbox: bool = True
    code_analysis: CodeAnalysisResult | None = None
    signature_valid: bool = False
    signature_count: int = 0
    required_permissions: list[str] = field(default_factory=list)
    code_hash: str = ""
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "plugin_id": self.plugin_id,
            "analyzed_at": self.analyzed_at.isoformat(),
            "trust_level": self.trust_level.value,
            "is_safe": self.is_safe,
            "can_run_in_sandbox": self.can_run_in_sandbox,
            "code_analysis": self.code_analysis.to_dict() if self.code_analysis else None,
            "signature_valid": self.signature_valid,
            "signature_count": self.signature_count,
            "required_permissions": self.required_permissions,
            "code_hash": self.code_hash,
            "recommendations": self.recommendations,
        }


class CodeAnalyzer(ast.NodeVisitor):
    """AST-based code analyzer for security issues."""

    # Dangerous function calls
    BLOCKED_FUNCTIONS = frozenset({
        "eval", "exec", "compile",
        "open", "input",
        "__import__",
        "globals", "locals", "vars", "dir",
        "getattr", "setattr", "delattr",
        "breakpoint", "exit", "quit",
        "memoryview", "bytearray",
    })

    # Dangerous attribute accesses
    BLOCKED_ATTRIBUTES = frozenset({
        "__class__", "__bases__", "__subclasses__", "__mro__",
        "__code__", "__globals__", "__builtins__",
        "__dict__", "__closure__", "__func__",
        "__self__", "__module__", "__qualname__",
        "__annotations__", "__slots__",
        "__reduce__", "__reduce_ex__",
        "__getstate__", "__setstate__",
    })

    # Dangerous string patterns
    DANGEROUS_PATTERNS = [
        (r"os\.system", "os.system call"),
        (r"subprocess\.", "subprocess usage"),
        (r"socket\.", "socket usage"),
        (r"__import__", "dynamic import"),
        (r"importlib\.", "importlib usage"),
        (r"ctypes\.", "ctypes usage"),
        (r"pickle\.", "pickle usage"),
        (r"marshal\.", "marshal usage"),
    ]

    # Permission-related imports
    PERMISSION_IMPORTS = {
        "os": "file_system",
        "shutil": "file_system",
        "pathlib": "file_system",
        "tempfile": "file_system",
        "glob": "file_system",
        "fnmatch": "file_system",
        "subprocess": "execute_code",
        "multiprocessing": "execute_code",
        "concurrent": "execute_code",
        "asyncio": "execute_code",
        "socket": "network_access",
        "http": "network_access",
        "urllib": "network_access",
        "requests": "network_access",
        "httpx": "network_access",
        "aiohttp": "network_access",
        "ssl": "network_access",
        "sqlite3": "database_access",
        "pymysql": "database_access",
        "psycopg": "database_access",
        "pymongo": "database_access",
        "redis": "database_access",
    }

    def __init__(self, blocked_modules: list[str] | None = None) -> None:
        """Initialize the analyzer.

        Args:
            blocked_modules: Additional modules to block.
        """
        self.blocked_modules = set(blocked_modules or [])
        self.issues: list[str] = []
        self.warnings: list[str] = []
        self.blocked_constructs: list[str] = []
        self.detected_imports: list[str] = []
        self.detected_permissions: set[str] = set()
        self.complexity_score = 0
        self._depth = 0
        self._loop_depth = 0

    def visit_Call(self, node: ast.Call) -> None:
        """Check function calls."""
        func_name = None

        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        if func_name and func_name in self.BLOCKED_FUNCTIONS:
            self.issues.append(f"Blocked function call: {func_name}")
            self.blocked_constructs.append(f"call:{func_name}")

        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Check attribute access."""
        if node.attr in self.BLOCKED_ATTRIBUTES:
            self.issues.append(f"Blocked attribute access: {node.attr}")
            self.blocked_constructs.append(f"attr:{node.attr}")

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        """Check import statements."""
        for alias in node.names:
            module = alias.name.split(".")[0]
            self.detected_imports.append(alias.name)

            if module in self.blocked_modules:
                self.issues.append(f"Blocked module import: {module}")
                self.blocked_constructs.append(f"import:{module}")
            elif module in self.PERMISSION_IMPORTS:
                self.detected_permissions.add(self.PERMISSION_IMPORTS[module])
                self.warnings.append(f"Import requires permission: {module}")

        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Check from imports."""
        if node.module:
            module = node.module.split(".")[0]
            self.detected_imports.append(node.module)

            if module in self.blocked_modules:
                self.issues.append(f"Blocked module import: {module}")
                self.blocked_constructs.append(f"import:{module}")
            elif module in self.PERMISSION_IMPORTS:
                self.detected_permissions.add(self.PERMISSION_IMPORTS[module])
                self.warnings.append(f"Import requires permission: {module}")

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Track function definitions for complexity."""
        self.complexity_score += 1
        self._depth += 1
        self.generic_visit(node)
        self._depth -= 1

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Track async function definitions."""
        self.complexity_score += 1
        self._depth += 1
        self.generic_visit(node)
        self._depth -= 1

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Track class definitions."""
        self.complexity_score += 2
        self._depth += 1
        self.generic_visit(node)
        self._depth -= 1

    def visit_For(self, node: ast.For) -> None:
        """Track loops."""
        self.complexity_score += 1
        self._loop_depth += 1
        if self._loop_depth > 3:
            self.warnings.append("Deeply nested loops (depth > 3)")
        self.generic_visit(node)
        self._loop_depth -= 1

    def visit_While(self, node: ast.While) -> None:
        """Track while loops."""
        self.complexity_score += 2  # While loops are riskier
        self._loop_depth += 1
        if self._loop_depth > 3:
            self.warnings.append("Deeply nested loops (depth > 3)")
        self.generic_visit(node)
        self._loop_depth -= 1

    def visit_If(self, node: ast.If) -> None:
        """Track conditionals."""
        self.complexity_score += 1
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        """Track exception handling."""
        self.complexity_score += 1
        # Bare except is a warning
        for handler in node.handlers:
            if handler.type is None:
                self.warnings.append("Bare except clause found")
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        """Track with statements."""
        self.generic_visit(node)

    def analyze(self, code: str) -> CodeAnalysisResult:
        """Analyze code for security issues.

        Args:
            code: Python source code to analyze.

        Returns:
            CodeAnalysisResult with findings.
        """
        # Reset state
        self.issues = []
        self.warnings = []
        self.blocked_constructs = []
        self.detected_imports = []
        self.detected_permissions = set()
        self.complexity_score = 0
        self._depth = 0
        self._loop_depth = 0

        # Parse and visit AST
        try:
            tree = ast.parse(code)
            self.visit(tree)
        except SyntaxError as e:
            self.issues.append(f"Syntax error: {e}")
            return CodeAnalysisResult(
                is_safe=False,
                issues=self.issues,
            )

        # Check for dangerous patterns in source code
        for pattern, description in self.DANGEROUS_PATTERNS:
            if re.search(pattern, code):
                self.warnings.append(f"Potentially dangerous pattern: {description}")

        # Calculate final complexity score (0-100)
        self.complexity_score = min(100, self.complexity_score)

        return CodeAnalysisResult(
            is_safe=len(self.issues) == 0,
            issues=self.issues,
            warnings=self.warnings,
            blocked_constructs=self.blocked_constructs,
            detected_imports=self.detected_imports,
            detected_permissions=sorted(self.detected_permissions),
            complexity_score=self.complexity_score,
        )


class SecurityAnalyzer:
    """Comprehensive security analyzer for plugins."""

    def __init__(
        self,
        policy: SecurityPolicy | None = None,
        blocked_modules: list[str] | None = None,
    ) -> None:
        """Initialize the security analyzer.

        Args:
            policy: Security policy to apply.
            blocked_modules: Additional blocked modules.
        """
        self.policy = policy
        self.blocked_modules = blocked_modules or (
            policy.blocked_modules if policy else []
        )

    def analyze_code(self, code: str) -> CodeAnalysisResult:
        """Analyze code for security issues.

        Args:
            code: Python source code.

        Returns:
            CodeAnalysisResult with findings.
        """
        analyzer = CodeAnalyzer(blocked_modules=self.blocked_modules)
        return analyzer.analyze(code)

    def analyze_plugin(
        self,
        plugin_id: str,
        code: str | None = None,
        signature_valid: bool = False,
        signature_count: int = 0,
    ) -> SecurityReport:
        """Perform comprehensive plugin security analysis.

        Args:
            plugin_id: Plugin identifier.
            code: Plugin code to analyze.
            signature_valid: Whether signatures are valid.
            signature_count: Number of valid signatures.

        Returns:
            SecurityReport with analysis results.
        """
        code_analysis = None
        code_hash = ""
        required_permissions: list[str] = []
        recommendations: list[str] = []

        # Analyze code if provided
        if code:
            code_analysis = self.analyze_code(code)
            code_hash = hashlib.sha256(code.encode()).hexdigest()
            required_permissions = code_analysis.detected_permissions.copy()

            # Generate recommendations based on analysis
            if code_analysis.complexity_score > 50:
                recommendations.append(
                    "Consider breaking down complex code into smaller modules"
                )
            if code_analysis.warnings:
                recommendations.append(
                    f"Review {len(code_analysis.warnings)} warnings before deployment"
                )
            if not signature_valid:
                recommendations.append("Sign the plugin for production use")

        # Determine trust level
        trust_level = self._determine_trust_level(
            code_analysis, signature_valid, signature_count
        )

        # Check sandbox compatibility
        can_run_in_sandbox = self._check_sandbox_compatible(code, code_analysis)

        # Determine if safe
        is_safe = (
            (code_analysis is None or code_analysis.is_safe)
            and (not self.policy or not self.policy.require_signature or signature_valid)
        )

        return SecurityReport(
            plugin_id=plugin_id,
            analyzed_at=datetime.utcnow(),
            trust_level=trust_level,
            is_safe=is_safe,
            can_run_in_sandbox=can_run_in_sandbox,
            code_analysis=code_analysis,
            signature_valid=signature_valid,
            signature_count=signature_count,
            required_permissions=required_permissions,
            code_hash=code_hash,
            recommendations=recommendations,
        )

    def _determine_trust_level(
        self,
        code_analysis: CodeAnalysisResult | None,
        signature_valid: bool,
        signature_count: int,
    ) -> TrustLevel:
        """Determine trust level based on analysis."""
        if signature_valid:
            min_sigs = self.policy.min_signatures if self.policy else 1
            if signature_count >= min_sigs:
                if code_analysis and code_analysis.is_safe:
                    return TrustLevel.TRUSTED
                return TrustLevel.VERIFIED

        if code_analysis:
            if code_analysis.issues:
                return TrustLevel.SANDBOXED
            if code_analysis.warnings:
                return TrustLevel.UNVERIFIED

        return TrustLevel.UNVERIFIED

    def _check_sandbox_compatible(
        self,
        code: str | None,
        analysis: CodeAnalysisResult | None,
    ) -> bool:
        """Check if code can run in sandbox."""
        if not code:
            return True

        if analysis and analysis.blocked_constructs:
            return False

        # Check for patterns that won't work in sandbox
        sandbox_breaking_patterns = [
            "__import__",
            "importlib",
            "sys.modules",
            "globals()",
            "locals()",
            "__class__.__bases__",
            "__subclasses__",
            "ctypes",
            "cffi",
        ]

        for pattern in sandbox_breaking_patterns:
            if pattern in code:
                return False

        return True

    def validate_for_policy(
        self,
        report: SecurityReport,
        policy: SecurityPolicy | None = None,
    ) -> tuple[bool, list[str]]:
        """Validate a security report against a policy.

        Args:
            report: Security report to validate.
            policy: Policy to validate against (uses self.policy if None).

        Returns:
            Tuple of (passes_policy, list of violations).
        """
        policy = policy or self.policy
        if not policy:
            return True, []

        violations: list[str] = []

        # Check signature requirement
        if policy.require_signature and not report.signature_valid:
            violations.append("Plugin requires valid signature")

        # Check minimum signatures
        if report.signature_count < policy.min_signatures:
            violations.append(
                f"Insufficient signatures: {report.signature_count} < {policy.min_signatures}"
            )

        # Check if sandbox required but incompatible
        if policy.isolation_level != "none" and not report.can_run_in_sandbox:
            violations.append("Plugin not compatible with required isolation level")

        # Check code analysis
        if report.code_analysis and report.code_analysis.issues:
            violations.append(
                f"Code analysis found {len(report.code_analysis.issues)} critical issues"
            )

        return len(violations) == 0, violations
