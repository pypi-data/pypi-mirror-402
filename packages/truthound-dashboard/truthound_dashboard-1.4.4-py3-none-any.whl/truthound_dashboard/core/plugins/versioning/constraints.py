"""Version Constraint Parsing and Matching.

This module provides version constraint parsing for common formats:
- Exact: 1.2.3 or =1.2.3
- Greater than: >1.2.3, >=1.2.3
- Less than: <1.2.3, <=1.2.3
- Caret: ^1.2.3 (compatible with 1.x.x)
- Tilde: ~1.2.3 (compatible with 1.2.x)
- Range: >=1.0.0 <2.0.0
- Wildcard: 1.2.*, 1.x
- Or: 1.2.3 || 2.0.0
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .semver import Version, parse_version


class ConstraintOp(str, Enum):
    """Version constraint operators."""

    EQ = "="      # Exact match
    GT = ">"      # Greater than
    GTE = ">="    # Greater than or equal
    LT = "<"      # Less than
    LTE = "<="    # Less than or equal
    CARET = "^"   # Caret range
    TILDE = "~"   # Tilde range
    ANY = "*"     # Any version


@dataclass
class VersionConstraint:
    """A single version constraint.

    Attributes:
        op: Constraint operator.
        version: Target version.
        original: Original constraint string.
    """

    op: ConstraintOp
    version: Version | None
    original: str = ""

    def __str__(self) -> str:
        """Return string representation."""
        if self.original:
            return self.original
        if self.op == ConstraintOp.ANY:
            return "*"
        if self.version:
            return f"{self.op.value}{self.version}"
        return self.op.value

    def matches(self, version: Version | str) -> bool:
        """Check if a version matches this constraint.

        Args:
            version: Version to check.

        Returns:
            True if version matches constraint.
        """
        if isinstance(version, str):
            version = parse_version(version)

        if self.op == ConstraintOp.ANY:
            return True

        if self.version is None:
            return True

        if self.op == ConstraintOp.EQ:
            return version == self.version

        if self.op == ConstraintOp.GT:
            return version > self.version

        if self.op == ConstraintOp.GTE:
            return version >= self.version

        if self.op == ConstraintOp.LT:
            return version < self.version

        if self.op == ConstraintOp.LTE:
            return version <= self.version

        if self.op == ConstraintOp.CARET:
            return self._matches_caret(version)

        if self.op == ConstraintOp.TILDE:
            return self._matches_tilde(version)

        return False

    def _matches_caret(self, version: Version) -> bool:
        """Check caret constraint (^).

        ^1.2.3 := >=1.2.3 <2.0.0
        ^0.2.3 := >=0.2.3 <0.3.0
        ^0.0.3 := >=0.0.3 <0.0.4
        """
        if self.version is None:
            return True

        if version < self.version:
            return False

        if self.version.major != 0:
            # ^1.2.3: allow 1.x.x
            return version.major == self.version.major

        if self.version.minor != 0:
            # ^0.2.3: allow 0.2.x
            return (
                version.major == self.version.major
                and version.minor == self.version.minor
            )

        # ^0.0.3: only exact patch
        return (
            version.major == self.version.major
            and version.minor == self.version.minor
            and version.patch == self.version.patch
        )

    def _matches_tilde(self, version: Version) -> bool:
        """Check tilde constraint (~).

        ~1.2.3 := >=1.2.3 <1.3.0
        ~1.2 := >=1.2.0 <1.3.0
        ~1 := >=1.0.0 <2.0.0
        """
        if self.version is None:
            return True

        if version < self.version:
            return False

        # Allow same major.minor, any patch
        return (
            version.major == self.version.major
            and version.minor == self.version.minor
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "op": self.op.value,
            "version": self.version.to_dict() if self.version else None,
            "original": self.original,
        }


@dataclass
class VersionRange:
    """A version range consisting of multiple constraints.

    Constraints are ANDed together within a range.
    Multiple ranges can be ORed.

    Attributes:
        constraints: List of constraints (ANDed).
        original: Original range string.
    """

    constraints: list[VersionConstraint]
    original: str = ""

    def __str__(self) -> str:
        """Return string representation."""
        if self.original:
            return self.original
        return " ".join(str(c) for c in self.constraints)

    def matches(self, version: Version | str) -> bool:
        """Check if a version matches all constraints in this range.

        Args:
            version: Version to check.

        Returns:
            True if version matches all constraints.
        """
        if isinstance(version, str):
            version = parse_version(version)

        return all(c.matches(version) for c in self.constraints)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "constraints": [c.to_dict() for c in self.constraints],
            "original": self.original,
        }


# Constraint parsing patterns
CONSTRAINT_PATTERNS = [
    # Caret range: ^1.2.3
    (r"^\^(.+)$", ConstraintOp.CARET),
    # Tilde range: ~1.2.3
    (r"^~(.+)$", ConstraintOp.TILDE),
    # Greater than or equal: >=1.2.3
    (r"^>=(.+)$", ConstraintOp.GTE),
    # Less than or equal: <=1.2.3
    (r"^<=(.+)$", ConstraintOp.LTE),
    # Greater than: >1.2.3
    (r"^>(.+)$", ConstraintOp.GT),
    # Less than: <1.2.3
    (r"^<(.+)$", ConstraintOp.LT),
    # Exact: =1.2.3
    (r"^=(.+)$", ConstraintOp.EQ),
]


def _parse_single_constraint(constraint_str: str) -> VersionConstraint:
    """Parse a single constraint string.

    Args:
        constraint_str: Constraint string.

    Returns:
        VersionConstraint object.
    """
    constraint_str = constraint_str.strip()

    if not constraint_str or constraint_str == "*":
        return VersionConstraint(ConstraintOp.ANY, None, constraint_str)

    # Handle wildcard versions
    if constraint_str.endswith(".*") or constraint_str.endswith(".x"):
        # 1.2.* -> ^1.2.0, 1.x -> ^1.0.0
        parts = constraint_str.replace(".*", "").replace(".x", "").split(".")
        if len(parts) == 1:
            version = parse_version(f"{parts[0]}.0.0")
            return VersionConstraint(ConstraintOp.CARET, version, constraint_str)
        elif len(parts) == 2:
            version = parse_version(f"{parts[0]}.{parts[1]}.0")
            return VersionConstraint(ConstraintOp.TILDE, version, constraint_str)
        else:
            version = parse_version(".".join(parts[:3]))
            return VersionConstraint(ConstraintOp.TILDE, version, constraint_str)

    # Try each pattern
    for pattern, op in CONSTRAINT_PATTERNS:
        match = re.match(pattern, constraint_str)
        if match:
            version = parse_version(match.group(1).strip())
            return VersionConstraint(op, version, constraint_str)

    # No operator - treat as exact match
    version = parse_version(constraint_str)
    return VersionConstraint(ConstraintOp.EQ, version, constraint_str)


def parse_constraint(constraint_str: str) -> list[VersionRange]:
    """Parse a constraint string into version ranges.

    Supports:
    - Single constraint: "^1.2.3"
    - Range with AND: ">=1.0.0 <2.0.0"
    - Multiple ranges with OR: "^1.2.3 || ^2.0.0"
    - Hyphen range: "1.0.0 - 2.0.0"

    Args:
        constraint_str: Constraint string.

    Returns:
        List of VersionRange objects (ORed together).
    """
    if not constraint_str or constraint_str.strip() == "*":
        return [VersionRange([VersionConstraint(ConstraintOp.ANY, None, "*")], "*")]

    # Split by OR operator
    or_parts = re.split(r"\s*\|\|\s*", constraint_str)
    ranges = []

    for or_part in or_parts:
        or_part = or_part.strip()
        if not or_part:
            continue

        # Check for hyphen range: 1.0.0 - 2.0.0
        hyphen_match = re.match(r"^([^\s]+)\s+-\s+([^\s]+)$", or_part)
        if hyphen_match:
            min_version = parse_version(hyphen_match.group(1))
            max_version = parse_version(hyphen_match.group(2))
            constraints = [
                VersionConstraint(ConstraintOp.GTE, min_version, f">={min_version}"),
                VersionConstraint(ConstraintOp.LTE, max_version, f"<={max_version}"),
            ]
            ranges.append(VersionRange(constraints, or_part))
            continue

        # Split by whitespace for AND constraints
        and_parts = or_part.split()
        constraints = []

        for and_part in and_parts:
            and_part = and_part.strip()
            if and_part:
                constraints.append(_parse_single_constraint(and_part))

        if constraints:
            ranges.append(VersionRange(constraints, or_part))

    return ranges or [VersionRange([VersionConstraint(ConstraintOp.ANY, None, "*")], "*")]


def satisfies(version: Version | str, constraint_str: str) -> bool:
    """Check if a version satisfies a constraint.

    Args:
        version: Version to check.
        constraint_str: Constraint string.

    Returns:
        True if version satisfies constraint.
    """
    if isinstance(version, str):
        version = parse_version(version)

    ranges = parse_constraint(constraint_str)
    # Version must match at least one range (OR)
    return any(r.matches(version) for r in ranges)


def find_best_version(
    available_versions: list[str | Version],
    constraint_str: str,
    prefer_stable: bool = True,
) -> Version | None:
    """Find the best version that satisfies a constraint.

    Args:
        available_versions: List of available versions.
        constraint_str: Constraint string.
        prefer_stable: Prefer stable versions over pre-releases.

    Returns:
        Best matching version, or None if no match.
    """
    # Parse versions
    versions = []
    for v in available_versions:
        if isinstance(v, str):
            try:
                versions.append(parse_version(v))
            except ValueError:
                continue
        else:
            versions.append(v)

    # Filter by constraint
    ranges = parse_constraint(constraint_str)
    matching = [v for v in versions if any(r.matches(v) for r in ranges)]

    if not matching:
        return None

    # Sort by version (descending)
    matching.sort(reverse=True)

    if prefer_stable:
        # Prefer stable versions
        stable = [v for v in matching if not v.is_prerelease()]
        if stable:
            return stable[0]

    return matching[0]
