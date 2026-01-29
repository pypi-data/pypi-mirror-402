"""Plugin System for Truthound Dashboard.

This module provides a comprehensive plugin system supporting:
- Plugin discovery and registration
- Custom validators
- Custom reporters
- Plugin marketplace
- Security and sandboxing

Usage:
    from truthound_dashboard.core.plugins import (
        PluginRegistry,
        PluginLoader,
        PluginSandbox,
        CustomValidatorExecutor,
        CustomReporterExecutor,
    )
"""

from .registry import PluginRegistry
from .loader import PluginLoader
from .sandbox import SandboxEngine as PluginSandbox, SandboxConfig
from .validator_executor import CustomValidatorExecutor
from .reporter_executor import CustomReporterExecutor
from .security import (
    SecurityAnalyzer as PluginSecurityManager,
    SigningService as SignatureVerifier,
)

__all__ = [
    "PluginRegistry",
    "PluginLoader",
    "PluginSandbox",
    "SandboxConfig",
    "CustomValidatorExecutor",
    "CustomReporterExecutor",
    "PluginSecurityManager",
    "SignatureVerifier",
]
