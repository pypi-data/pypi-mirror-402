"""Plugin Versioning and Dependency Management Module.

This module provides:
- Semantic versioning (semver) parsing and comparison
- Version constraint parsing (^, ~, >=, <, etc.)
- Dependency graph with cycle detection
- Topological sorting for load order
"""

from __future__ import annotations

from .semver import (
    Version,
    parse_version,
    compare_versions,
)
from .constraints import (
    VersionConstraint,
    VersionRange,
    parse_constraint,
    satisfies,
    find_best_version,
)
from .dependencies import (
    DependencyType,
    Dependency,
    DependencyGraph,
    DependencyResolver,
    DependencyResolutionError,
    CyclicDependencyError,
)

__all__ = [
    # Semver
    "Version",
    "parse_version",
    "compare_versions",
    # Constraints
    "VersionConstraint",
    "VersionRange",
    "parse_constraint",
    "satisfies",
    "find_best_version",
    # Dependencies
    "DependencyType",
    "Dependency",
    "DependencyGraph",
    "DependencyResolver",
    "DependencyResolutionError",
    "CyclicDependencyError",
]
