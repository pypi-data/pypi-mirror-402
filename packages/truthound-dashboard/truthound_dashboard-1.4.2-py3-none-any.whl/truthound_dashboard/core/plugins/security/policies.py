"""Security Policy Presets.

This module provides predefined security policies for different
use cases and environments.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from .protocols import (
    IsolationLevel,
    ResourceLimits,
    SecurityPolicy,
)


class SecurityPolicyPresets(str, Enum):
    """Predefined security policy presets."""

    DEVELOPMENT = "development"   # No restrictions, for local dev
    TESTING = "testing"           # Minimal restrictions for testing
    STANDARD = "standard"         # Default production settings
    ENTERPRISE = "enterprise"     # Enterprise security requirements
    STRICT = "strict"             # High security environment
    AIRGAPPED = "airgapped"       # Air-gapped/isolated environment


# Policy definitions
_PRESET_POLICIES: dict[SecurityPolicyPresets, SecurityPolicy] = {
    SecurityPolicyPresets.DEVELOPMENT: SecurityPolicy(
        name="development",
        description="Development mode with minimal restrictions",
        isolation_level=IsolationLevel.NONE,
        resource_limits=ResourceLimits(
            max_memory_mb=1024,
            max_cpu_time_sec=300,
            max_wall_time_sec=600,
            max_file_size_mb=100,
            max_open_files=100,
            max_processes=10,
            network_enabled=True,
            filesystem_read=True,
            filesystem_write=True,
        ),
        require_signature=False,
        min_signatures=0,
        blocked_modules=[],
    ),
    SecurityPolicyPresets.TESTING: SecurityPolicy(
        name="testing",
        description="Testing mode with relaxed restrictions",
        isolation_level=IsolationLevel.NONE,
        resource_limits=ResourceLimits(
            max_memory_mb=512,
            max_cpu_time_sec=120,
            max_wall_time_sec=300,
            max_file_size_mb=50,
            max_open_files=50,
            max_processes=5,
            network_enabled=True,
            filesystem_read=True,
            filesystem_write=True,
        ),
        require_signature=False,
        min_signatures=0,
        blocked_modules=[],
    ),
    SecurityPolicyPresets.STANDARD: SecurityPolicy(
        name="standard",
        description="Standard production security",
        isolation_level=IsolationLevel.PROCESS,
        resource_limits=ResourceLimits(
            max_memory_mb=256,
            max_cpu_time_sec=30,
            max_wall_time_sec=60,
            max_file_size_mb=10,
            max_open_files=10,
            max_processes=1,
            network_enabled=False,
            filesystem_read=False,
            filesystem_write=False,
        ),
        require_signature=True,
        min_signatures=1,
        blocked_modules=[
            "os", "subprocess", "sys", "shutil", "socket",
            "http", "urllib", "requests", "httpx",
            "multiprocessing", "threading", "ctypes",
            "pickle", "shelve", "sqlite3", "importlib",
        ],
    ),
    SecurityPolicyPresets.ENTERPRISE: SecurityPolicy(
        name="enterprise",
        description="Enterprise security with signature requirements",
        isolation_level=IsolationLevel.PROCESS,
        resource_limits=ResourceLimits(
            max_memory_mb=256,
            max_cpu_time_sec=30,
            max_wall_time_sec=60,
            max_file_size_mb=10,
            max_open_files=10,
            max_processes=1,
            network_enabled=False,
            filesystem_read=False,
            filesystem_write=False,
        ),
        require_signature=True,
        min_signatures=1,
        blocked_modules=[
            "os", "subprocess", "sys", "shutil", "socket",
            "http", "urllib", "requests", "httpx",
            "multiprocessing", "threading", "ctypes",
            "pickle", "shelve", "sqlite3", "importlib",
            "builtins", "__builtin__",
        ],
    ),
    SecurityPolicyPresets.STRICT: SecurityPolicy(
        name="strict",
        description="High security environment with container isolation",
        isolation_level=IsolationLevel.CONTAINER,
        resource_limits=ResourceLimits(
            max_memory_mb=128,
            max_cpu_time_sec=15,
            max_wall_time_sec=30,
            max_file_size_mb=5,
            max_open_files=5,
            max_processes=1,
            network_enabled=False,
            filesystem_read=False,
            filesystem_write=False,
        ),
        require_signature=True,
        min_signatures=2,
        blocked_modules=[
            "os", "subprocess", "sys", "shutil", "socket",
            "http", "urllib", "requests", "httpx",
            "multiprocessing", "threading", "ctypes",
            "pickle", "shelve", "sqlite3", "importlib",
            "builtins", "__builtin__", "code", "codeop",
            "gc", "inspect", "traceback",
        ],
    ),
    SecurityPolicyPresets.AIRGAPPED: SecurityPolicy(
        name="airgapped",
        description="Air-gapped environment with maximum restrictions",
        isolation_level=IsolationLevel.CONTAINER,
        resource_limits=ResourceLimits(
            max_memory_mb=64,
            max_cpu_time_sec=10,
            max_wall_time_sec=20,
            max_file_size_mb=1,
            max_open_files=3,
            max_processes=1,
            network_enabled=False,
            filesystem_read=False,
            filesystem_write=False,
        ),
        require_signature=True,
        min_signatures=2,
        blocked_modules=[
            "os", "subprocess", "sys", "shutil", "socket",
            "http", "urllib", "requests", "httpx",
            "multiprocessing", "threading", "ctypes",
            "pickle", "shelve", "sqlite3", "importlib",
            "builtins", "__builtin__", "code", "codeop",
            "gc", "inspect", "traceback", "ast", "dis",
            "types", "typing", "io", "tempfile",
        ],
    ),
}


def get_preset(preset: SecurityPolicyPresets | str) -> SecurityPolicy:
    """Get a security policy preset.

    Args:
        preset: Preset name or enum value.

    Returns:
        SecurityPolicy for the preset.

    Raises:
        ValueError: If preset is not found.
    """
    if isinstance(preset, str):
        try:
            preset = SecurityPolicyPresets(preset)
        except ValueError:
            raise ValueError(f"Unknown security preset: {preset}")

    if preset not in _PRESET_POLICIES:
        raise ValueError(f"Unknown security preset: {preset}")

    # Return a copy to prevent modification
    original = _PRESET_POLICIES[preset]
    return SecurityPolicy(
        name=original.name,
        description=original.description,
        isolation_level=original.isolation_level,
        resource_limits=ResourceLimits(
            max_memory_mb=original.resource_limits.max_memory_mb,
            max_cpu_time_sec=original.resource_limits.max_cpu_time_sec,
            max_wall_time_sec=original.resource_limits.max_wall_time_sec,
            max_file_size_mb=original.resource_limits.max_file_size_mb,
            max_open_files=original.resource_limits.max_open_files,
            max_processes=original.resource_limits.max_processes,
            network_enabled=original.resource_limits.network_enabled,
            filesystem_read=original.resource_limits.filesystem_read,
            filesystem_write=original.resource_limits.filesystem_write,
        ),
        require_signature=original.require_signature,
        min_signatures=original.min_signatures,
        allowed_signers=original.allowed_signers.copy(),
        blocked_modules=original.blocked_modules.copy(),
        allowed_permissions=original.allowed_permissions.copy(),
    )


def list_presets() -> list[dict[str, Any]]:
    """List all available security presets.

    Returns:
        List of preset information dictionaries.
    """
    return [
        {
            "name": preset.value,
            "description": _PRESET_POLICIES[preset].description,
            "isolation_level": _PRESET_POLICIES[preset].isolation_level.value,
            "require_signature": _PRESET_POLICIES[preset].require_signature,
            "min_signatures": _PRESET_POLICIES[preset].min_signatures,
        }
        for preset in SecurityPolicyPresets
    ]


def create_policy(
    preset: SecurityPolicyPresets | str = SecurityPolicyPresets.STANDARD,
    *,
    isolation_level: IsolationLevel | str | None = None,
    max_memory_mb: int | None = None,
    max_cpu_time_sec: int | None = None,
    max_wall_time_sec: int | None = None,
    network_enabled: bool | None = None,
    filesystem_read: bool | None = None,
    filesystem_write: bool | None = None,
    require_signature: bool | None = None,
    min_signatures: int | None = None,
    allowed_signers: list[str] | None = None,
    blocked_modules: list[str] | None = None,
    allowed_permissions: list[str] | None = None,
) -> SecurityPolicy:
    """Create a customized security policy based on a preset.

    Args:
        preset: Base preset to customize.
        isolation_level: Override isolation level.
        max_memory_mb: Override memory limit.
        max_cpu_time_sec: Override CPU time limit.
        max_wall_time_sec: Override wall time limit.
        network_enabled: Override network access.
        filesystem_read: Override filesystem read.
        filesystem_write: Override filesystem write.
        require_signature: Override signature requirement.
        min_signatures: Override minimum signatures.
        allowed_signers: Override allowed signers.
        blocked_modules: Override blocked modules.
        allowed_permissions: Override allowed permissions.

    Returns:
        Customized SecurityPolicy.
    """
    policy = get_preset(preset)

    # Override isolation level
    if isolation_level is not None:
        if isinstance(isolation_level, str):
            isolation_level = IsolationLevel(isolation_level)
        policy.isolation_level = isolation_level

    # Override resource limits
    if max_memory_mb is not None:
        policy.resource_limits.max_memory_mb = max_memory_mb
    if max_cpu_time_sec is not None:
        policy.resource_limits.max_cpu_time_sec = max_cpu_time_sec
    if max_wall_time_sec is not None:
        policy.resource_limits.max_wall_time_sec = max_wall_time_sec
    if network_enabled is not None:
        policy.resource_limits.network_enabled = network_enabled
    if filesystem_read is not None:
        policy.resource_limits.filesystem_read = filesystem_read
    if filesystem_write is not None:
        policy.resource_limits.filesystem_write = filesystem_write

    # Override signature requirements
    if require_signature is not None:
        policy.require_signature = require_signature
    if min_signatures is not None:
        policy.min_signatures = min_signatures
    if allowed_signers is not None:
        policy.allowed_signers = allowed_signers

    # Override module restrictions
    if blocked_modules is not None:
        policy.blocked_modules = blocked_modules
    if allowed_permissions is not None:
        policy.allowed_permissions = allowed_permissions

    return policy
