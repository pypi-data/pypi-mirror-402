"""Sandbox Protocol Definitions.

This module defines the core protocols and data types for the
plugin sandbox system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class SandboxError(Exception):
    """Base exception for sandbox errors."""
    pass


class SandboxTimeoutError(SandboxError):
    """Raised when sandbox execution times out."""
    pass


class SandboxMemoryError(SandboxError):
    """Raised when sandbox memory limit is exceeded."""
    pass


class SandboxSecurityError(SandboxError):
    """Raised when sandbox security is violated."""
    pass


@dataclass
class SandboxConfig:
    """Configuration for sandbox execution.

    Attributes:
        enabled: Whether sandbox is enabled.
        isolation_level: Isolation level (none, process, container).
        memory_limit_mb: Memory limit in MB.
        cpu_time_limit_sec: CPU time limit in seconds.
        wall_time_limit_sec: Wall clock time limit in seconds.
        max_file_size_mb: Maximum file size in MB.
        max_open_files: Maximum number of open files.
        max_processes: Maximum number of processes.
        network_enabled: Whether network access is allowed.
        filesystem_read: Whether filesystem read is allowed.
        filesystem_write: Whether filesystem write is allowed.
        allowed_modules: List of allowed Python modules (empty = default safe).
        blocked_modules: List of blocked Python modules.
        allowed_builtins: List of allowed builtin functions.
        container_image: Container image for container isolation.
        working_dir: Working directory for execution.
        environment: Environment variables.
    """

    enabled: bool = True
    isolation_level: str = "process"  # none, process, container
    memory_limit_mb: int = 256
    cpu_time_limit_sec: int = 30
    wall_time_limit_sec: int = 60
    max_file_size_mb: int = 10
    max_open_files: int = 10
    max_processes: int = 1
    network_enabled: bool = False
    filesystem_read: bool = False
    filesystem_write: bool = False
    allowed_modules: list[str] = field(default_factory=list)
    blocked_modules: list[str] = field(
        default_factory=lambda: [
            "os", "subprocess", "sys", "shutil", "socket",
            "http", "urllib", "requests", "httpx",
            "multiprocessing", "threading", "ctypes",
            "pickle", "shelve", "sqlite3", "importlib",
            "builtins", "__builtin__",
        ]
    )
    allowed_builtins: list[str] = field(
        default_factory=lambda: [
            "abs", "all", "any", "ascii", "bin", "bool",
            "bytearray", "bytes", "callable", "chr", "classmethod",
            "complex", "dict", "dir", "divmod", "enumerate",
            "filter", "float", "format", "frozenset", "getattr",
            "hasattr", "hash", "hex", "id", "int", "isinstance",
            "issubclass", "iter", "len", "list", "map", "max",
            "min", "next", "object", "oct", "ord", "pow",
            "print", "property", "range", "repr", "reversed",
            "round", "set", "setattr", "slice", "sorted",
            "staticmethod", "str", "sum", "super", "tuple",
            "type", "vars", "zip",
        ]
    )
    container_image: str = "python:3.11-slim"
    working_dir: str | None = None
    environment: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "enabled": self.enabled,
            "isolation_level": self.isolation_level,
            "memory_limit_mb": self.memory_limit_mb,
            "cpu_time_limit_sec": self.cpu_time_limit_sec,
            "wall_time_limit_sec": self.wall_time_limit_sec,
            "max_file_size_mb": self.max_file_size_mb,
            "max_open_files": self.max_open_files,
            "max_processes": self.max_processes,
            "network_enabled": self.network_enabled,
            "filesystem_read": self.filesystem_read,
            "filesystem_write": self.filesystem_write,
            "allowed_modules": self.allowed_modules,
            "blocked_modules": self.blocked_modules,
            "container_image": self.container_image,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SandboxConfig":
        """Create from dictionary."""
        return cls(
            enabled=data.get("enabled", True),
            isolation_level=data.get("isolation_level", "process"),
            memory_limit_mb=data.get("memory_limit_mb", 256),
            cpu_time_limit_sec=data.get("cpu_time_limit_sec", 30),
            wall_time_limit_sec=data.get("wall_time_limit_sec", 60),
            max_file_size_mb=data.get("max_file_size_mb", 10),
            max_open_files=data.get("max_open_files", 10),
            max_processes=data.get("max_processes", 1),
            network_enabled=data.get("network_enabled", False),
            filesystem_read=data.get("filesystem_read", False),
            filesystem_write=data.get("filesystem_write", False),
            allowed_modules=data.get("allowed_modules", []),
            blocked_modules=data.get("blocked_modules", []),
            container_image=data.get("container_image", "python:3.11-slim"),
        )


@dataclass
class SandboxResult:
    """Result of sandbox execution.

    Attributes:
        success: Whether execution succeeded.
        result: Return value if any.
        error: Error message if failed.
        error_type: Type of error if failed.
        stdout: Captured stdout.
        stderr: Captured stderr.
        execution_time_ms: Execution time in milliseconds.
        memory_used_mb: Memory used in MB.
        cpu_time_sec: CPU time used in seconds.
        exit_code: Process exit code (for process/container isolation).
        warnings: List of warnings.
        metadata: Additional metadata.
    """

    success: bool
    result: Any = None
    error: str | None = None
    error_type: str | None = None
    stdout: str = ""
    stderr: str = ""
    execution_time_ms: float = 0
    memory_used_mb: float | None = None
    cpu_time_sec: float | None = None
    exit_code: int | None = None
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "result": self.result if self._is_serializable(self.result) else str(self.result),
            "error": self.error,
            "error_type": self.error_type,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "execution_time_ms": self.execution_time_ms,
            "memory_used_mb": self.memory_used_mb,
            "cpu_time_sec": self.cpu_time_sec,
            "exit_code": self.exit_code,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }

    @staticmethod
    def _is_serializable(obj: Any) -> bool:
        """Check if object is JSON serializable."""
        try:
            import json
            json.dumps(obj)
            return True
        except (TypeError, ValueError):
            return False
