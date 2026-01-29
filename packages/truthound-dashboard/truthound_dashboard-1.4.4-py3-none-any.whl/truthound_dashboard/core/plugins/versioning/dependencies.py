"""Dependency Graph and Resolution.

This module provides:
- Dependency graph construction
- Cycle detection
- Topological sorting for load order
- Dependency resolution
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .semver import Version, parse_version
from .constraints import parse_constraint, satisfies, find_best_version


class DependencyType(str, Enum):
    """Types of dependencies."""

    REQUIRED = "required"       # Must be present
    OPTIONAL = "optional"       # Nice to have
    DEV = "dev"                 # Development only
    PEER = "peer"               # Must be installed by parent
    CONFLICT = "conflict"       # Must NOT be present


class DependencyResolutionError(Exception):
    """Raised when dependency resolution fails."""
    pass


class CyclicDependencyError(DependencyResolutionError):
    """Raised when a cyclic dependency is detected."""

    def __init__(self, cycle: list[str]) -> None:
        """Initialize with cycle path.

        Args:
            cycle: List of node IDs forming the cycle.
        """
        self.cycle = cycle
        cycle_str = " -> ".join(cycle)
        super().__init__(f"Cyclic dependency detected: {cycle_str}")


@dataclass
class Dependency:
    """Represents a dependency relationship.

    Attributes:
        name: Name of the dependency.
        version_constraint: Version constraint string.
        dep_type: Type of dependency.
        optional: Whether this dependency is optional.
        platform: Platform restriction (e.g., "linux", "darwin").
        python_version: Python version constraint.
        extras: Extra features this dependency provides.
        resolved_version: Resolved version after resolution.
    """

    name: str
    version_constraint: str = "*"
    dep_type: DependencyType = DependencyType.REQUIRED
    optional: bool = False
    platform: str | None = None
    python_version: str | None = None
    extras: list[str] = field(default_factory=list)
    resolved_version: Version | None = None

    def __str__(self) -> str:
        """Return string representation."""
        if self.version_constraint and self.version_constraint != "*":
            return f"{self.name}@{self.version_constraint}"
        return self.name

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version_constraint": self.version_constraint,
            "dep_type": self.dep_type.value,
            "optional": self.optional,
            "platform": self.platform,
            "python_version": self.python_version,
            "extras": self.extras,
            "resolved_version": (
                str(self.resolved_version) if self.resolved_version else None
            ),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Dependency":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            version_constraint=data.get("version_constraint", "*"),
            dep_type=DependencyType(data.get("dep_type", "required")),
            optional=data.get("optional", False),
            platform=data.get("platform"),
            python_version=data.get("python_version"),
            extras=data.get("extras", []),
        )


@dataclass
class DependencyNode:
    """A node in the dependency graph.

    Attributes:
        id: Unique identifier (usually plugin name).
        version: Version of this node.
        dependencies: List of dependencies.
        metadata: Additional metadata.
    """

    id: str
    version: Version | str | None = None
    dependencies: list[Dependency] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Parse version if string."""
        if isinstance(self.version, str):
            self.version = parse_version(self.version)

    def __str__(self) -> str:
        """Return string representation."""
        if self.version:
            return f"{self.id}@{self.version}"
        return self.id


class DependencyGraph:
    """Directed graph for dependency management.

    Supports:
    - Adding/removing nodes
    - Cycle detection
    - Topological sorting
    - Path finding
    """

    def __init__(self) -> None:
        """Initialize empty graph."""
        self._nodes: dict[str, DependencyNode] = {}
        self._edges: dict[str, set[str]] = defaultdict(set)  # id -> dependencies
        self._reverse_edges: dict[str, set[str]] = defaultdict(set)  # id -> dependents

    def add_node(
        self,
        node_id: str,
        version: Version | str | None = None,
        dependencies: list[Dependency] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DependencyNode:
        """Add a node to the graph.

        Args:
            node_id: Unique identifier.
            version: Node version.
            dependencies: List of dependencies.
            metadata: Additional metadata.

        Returns:
            The created node.
        """
        node = DependencyNode(
            id=node_id,
            version=version,
            dependencies=dependencies or [],
            metadata=metadata or {},
        )
        self._nodes[node_id] = node

        # Add edges for dependencies
        for dep in node.dependencies:
            if dep.dep_type != DependencyType.CONFLICT:
                self._edges[node_id].add(dep.name)
                self._reverse_edges[dep.name].add(node_id)

        return node

    def remove_node(self, node_id: str) -> None:
        """Remove a node from the graph.

        Args:
            node_id: Node to remove.
        """
        if node_id not in self._nodes:
            return

        # Remove edges
        for dep_id in self._edges[node_id]:
            self._reverse_edges[dep_id].discard(node_id)
        del self._edges[node_id]

        for dependent_id in list(self._reverse_edges[node_id]):
            self._edges[dependent_id].discard(node_id)
        del self._reverse_edges[node_id]

        del self._nodes[node_id]

    def get_node(self, node_id: str) -> DependencyNode | None:
        """Get a node by ID.

        Args:
            node_id: Node ID.

        Returns:
            Node or None if not found.
        """
        return self._nodes.get(node_id)

    def get_dependencies(self, node_id: str) -> list[str]:
        """Get direct dependencies of a node.

        Args:
            node_id: Node ID.

        Returns:
            List of dependency IDs.
        """
        return list(self._edges.get(node_id, []))

    def get_dependents(self, node_id: str) -> list[str]:
        """Get nodes that depend on this node.

        Args:
            node_id: Node ID.

        Returns:
            List of dependent node IDs.
        """
        return list(self._reverse_edges.get(node_id, []))

    def get_all_dependencies(self, node_id: str) -> set[str]:
        """Get all transitive dependencies of a node.

        Args:
            node_id: Node ID.

        Returns:
            Set of all dependency IDs.
        """
        all_deps: set[str] = set()
        queue = deque(self._edges.get(node_id, []))

        while queue:
            dep_id = queue.popleft()
            if dep_id not in all_deps:
                all_deps.add(dep_id)
                queue.extend(self._edges.get(dep_id, []))

        return all_deps

    def detect_cycles(self) -> list[list[str]]:
        """Detect all cycles in the graph.

        Returns:
            List of cycles, where each cycle is a list of node IDs.
        """
        cycles: list[list[str]] = []
        visited: set[str] = set()
        rec_stack: set[str] = set()
        path: list[str] = []

        def dfs(node_id: str) -> None:
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)

            for neighbor in self._edges.get(node_id, []):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)

            path.pop()
            rec_stack.remove(node_id)

        for node_id in self._nodes:
            if node_id not in visited:
                dfs(node_id)

        return cycles

    def has_cycle(self) -> bool:
        """Check if graph has any cycles.

        Returns:
            True if cycles exist.
        """
        return len(self.detect_cycles()) > 0

    def topological_sort(self) -> list[str]:
        """Get topological ordering of nodes.

        Returns:
            List of node IDs in topological order.

        Raises:
            CyclicDependencyError: If graph has cycles.
        """
        cycles = self.detect_cycles()
        if cycles:
            raise CyclicDependencyError(cycles[0])

        # Kahn's algorithm
        in_degree: dict[str, int] = {node_id: 0 for node_id in self._nodes}
        for node_id in self._nodes:
            for dep_id in self._edges.get(node_id, []):
                if dep_id in in_degree:
                    in_degree[dep_id] += 1

        # Start with nodes that have no dependents
        queue = deque([
            node_id for node_id, degree in in_degree.items() if degree == 0
        ])
        result: list[str] = []

        while queue:
            node_id = queue.popleft()
            result.append(node_id)

            for dep_id in self._edges.get(node_id, []):
                if dep_id in in_degree:
                    in_degree[dep_id] -= 1
                    if in_degree[dep_id] == 0:
                        queue.append(dep_id)

        if len(result) != len(self._nodes):
            # Should not happen if cycle detection is correct
            raise CyclicDependencyError(["unknown cycle"])

        return result

    def get_load_order(self) -> list[str]:
        """Get the order in which nodes should be loaded.

        Dependencies are loaded before dependents.

        Returns:
            List of node IDs in load order.

        Raises:
            CyclicDependencyError: If graph has cycles.
        """
        # Reverse of topological sort gives load order
        return list(reversed(self.topological_sort()))

    def find_path(self, from_id: str, to_id: str) -> list[str] | None:
        """Find a path between two nodes.

        Args:
            from_id: Starting node.
            to_id: Target node.

        Returns:
            Path as list of node IDs, or None if no path exists.
        """
        if from_id not in self._nodes or to_id not in self._nodes:
            return None

        visited: set[str] = set()
        queue: deque[tuple[str, list[str]]] = deque([(from_id, [from_id])])

        while queue:
            current, path = queue.popleft()
            if current == to_id:
                return path

            if current in visited:
                continue
            visited.add(current)

            for neighbor in self._edges.get(current, []):
                if neighbor not in visited:
                    queue.append((neighbor, path + [neighbor]))

        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert graph to dictionary."""
        return {
            "nodes": [
                {
                    "id": node.id,
                    "version": str(node.version) if node.version else None,
                    "dependencies": [d.to_dict() for d in node.dependencies],
                    "metadata": node.metadata,
                }
                for node in self._nodes.values()
            ],
            "edges": {k: list(v) for k, v in self._edges.items()},
        }


class DependencyResolver:
    """Resolves dependencies and finds compatible versions."""

    def __init__(
        self,
        available_versions: dict[str, list[str]] | None = None,
    ) -> None:
        """Initialize resolver.

        Args:
            available_versions: Dict mapping package names to available versions.
        """
        self.available_versions = available_versions or {}

    def set_available_versions(
        self, package: str, versions: list[str]
    ) -> None:
        """Set available versions for a package.

        Args:
            package: Package name.
            versions: List of available version strings.
        """
        self.available_versions[package] = versions

    def resolve(
        self,
        dependencies: list[Dependency],
        installed: dict[str, str] | None = None,
    ) -> dict[str, Version]:
        """Resolve dependencies to specific versions.

        Args:
            dependencies: List of dependencies to resolve.
            installed: Currently installed versions.

        Returns:
            Dict mapping package names to resolved versions.

        Raises:
            DependencyResolutionError: If resolution fails.
        """
        installed = installed or {}
        resolved: dict[str, Version] = {}
        errors: list[str] = []

        for dep in dependencies:
            if dep.dep_type == DependencyType.CONFLICT:
                # Check that conflicting package is not installed
                if dep.name in installed:
                    if satisfies(installed[dep.name], dep.version_constraint):
                        errors.append(
                            f"Conflict: {dep.name}@{installed[dep.name]} "
                            f"conflicts with constraint {dep.version_constraint}"
                        )
                continue

            # Check if already resolved
            if dep.name in resolved:
                # Verify constraint compatibility
                if not satisfies(resolved[dep.name], dep.version_constraint):
                    errors.append(
                        f"Version conflict for {dep.name}: "
                        f"resolved to {resolved[dep.name]} but "
                        f"constraint {dep.version_constraint} not satisfied"
                    )
                continue

            # Check if already installed
            if dep.name in installed:
                if satisfies(installed[dep.name], dep.version_constraint):
                    resolved[dep.name] = parse_version(installed[dep.name])
                    continue
                elif not dep.optional:
                    errors.append(
                        f"Installed version {dep.name}@{installed[dep.name]} "
                        f"does not satisfy {dep.version_constraint}"
                    )
                    continue

            # Find best version from available
            available = self.available_versions.get(dep.name, [])
            if not available:
                if dep.dep_type == DependencyType.REQUIRED and not dep.optional:
                    errors.append(f"No versions available for {dep.name}")
                continue

            best = find_best_version(available, dep.version_constraint)
            if best:
                resolved[dep.name] = best
            elif dep.dep_type == DependencyType.REQUIRED and not dep.optional:
                errors.append(
                    f"No version of {dep.name} satisfies {dep.version_constraint}"
                )

        if errors:
            raise DependencyResolutionError("\n".join(errors))

        return resolved

    def check_compatibility(
        self,
        package: str,
        version: str | Version,
        dependencies: list[Dependency],
    ) -> tuple[bool, list[str]]:
        """Check if a package version is compatible with dependencies.

        Args:
            package: Package name.
            version: Version to check.
            dependencies: List of dependencies.

        Returns:
            Tuple of (is_compatible, list of issues).
        """
        if isinstance(version, str):
            version = parse_version(version)

        issues: list[str] = []

        for dep in dependencies:
            if dep.name != package:
                continue

            if dep.dep_type == DependencyType.CONFLICT:
                if satisfies(version, dep.version_constraint):
                    issues.append(
                        f"Version {version} conflicts with constraint {dep.version_constraint}"
                    )
            else:
                if not satisfies(version, dep.version_constraint):
                    issues.append(
                        f"Version {version} does not satisfy {dep.version_constraint}"
                    )

        return len(issues) == 0, issues
