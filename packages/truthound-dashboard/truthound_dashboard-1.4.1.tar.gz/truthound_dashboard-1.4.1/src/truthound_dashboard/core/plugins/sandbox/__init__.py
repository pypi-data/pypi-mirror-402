"""Plugin Sandbox Module.

This module provides sandboxed execution environments with multiple
isolation levels for secure plugin code execution.

Isolation Levels:
- NONE: No isolation (trusted plugins only)
- PROCESS: Subprocess isolation with resource limits
- CONTAINER: Docker/Podman container isolation
"""

from __future__ import annotations

from .protocols import (
    SandboxResult,
    SandboxConfig,
    SandboxError,
    SandboxTimeoutError,
    SandboxMemoryError,
    SandboxSecurityError,
)
from .engines import (
    SandboxEngine,
    NoOpSandbox,
    ProcessSandbox,
    ContainerSandbox,
    create_sandbox,
    get_available_engines,
)
from .code_validator import (
    CodeValidator,
    RestrictedImporter,
    create_safe_builtins,
)

# Alias for backward compatibility
PluginSandbox = SandboxEngine

__all__ = [
    # Protocols
    "SandboxResult",
    "SandboxConfig",
    "SandboxError",
    "SandboxTimeoutError",
    "SandboxMemoryError",
    "SandboxSecurityError",
    # Engines
    "SandboxEngine",
    "PluginSandbox",  # Alias
    "NoOpSandbox",
    "ProcessSandbox",
    "ContainerSandbox",
    "create_sandbox",
    "get_available_engines",
    # Validation
    "CodeValidator",
    "RestrictedImporter",
    "create_safe_builtins",
]
