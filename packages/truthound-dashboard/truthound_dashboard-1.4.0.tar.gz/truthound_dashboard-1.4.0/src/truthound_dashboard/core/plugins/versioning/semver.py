"""Semantic Versioning Implementation.

This module provides semantic versioning (semver) parsing
and comparison following the Semantic Versioning 2.0.0 spec.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import total_ordering
from typing import Any


# Semver regex pattern
SEMVER_PATTERN = re.compile(
    r"^v?"  # Optional 'v' prefix
    r"(?P<major>0|[1-9]\d*)"
    r"\.(?P<minor>0|[1-9]\d*)"
    r"\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+(?P<build>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


@total_ordering
@dataclass
class Version:
    """Semantic version representation.

    Attributes:
        major: Major version (breaking changes).
        minor: Minor version (new features).
        patch: Patch version (bug fixes).
        prerelease: Pre-release identifier (e.g., alpha.1).
        build: Build metadata (e.g., build.123).
    """

    major: int
    minor: int
    patch: int
    prerelease: str | None = None
    build: str | None = None

    def __str__(self) -> str:
        """Return string representation."""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version

    def __repr__(self) -> str:
        """Return repr string."""
        return f"Version('{self}')"

    def __hash__(self) -> int:
        """Hash based on version components (excluding build)."""
        return hash((self.major, self.minor, self.patch, self.prerelease))

    def __eq__(self, other: object) -> bool:
        """Check equality (build metadata is ignored)."""
        if not isinstance(other, Version):
            return NotImplemented
        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
            and self.prerelease == other.prerelease
        )

    def __lt__(self, other: object) -> bool:
        """Compare versions."""
        if not isinstance(other, Version):
            return NotImplemented

        # Compare major.minor.patch
        if (self.major, self.minor, self.patch) != (
            other.major,
            other.minor,
            other.patch,
        ):
            return (self.major, self.minor, self.patch) < (
                other.major,
                other.minor,
                other.patch,
            )

        # Pre-release versions have lower precedence than release
        if self.prerelease and not other.prerelease:
            return True
        if not self.prerelease and other.prerelease:
            return False

        # Compare pre-release identifiers
        if self.prerelease and other.prerelease:
            return self._compare_prerelease(self.prerelease, other.prerelease) < 0

        return False

    @staticmethod
    def _compare_prerelease(a: str, b: str) -> int:
        """Compare pre-release strings.

        Returns:
            -1 if a < b, 0 if a == b, 1 if a > b.
        """
        a_parts = a.split(".")
        b_parts = b.split(".")

        for i in range(max(len(a_parts), len(b_parts))):
            if i >= len(a_parts):
                return -1
            if i >= len(b_parts):
                return 1

            a_part = a_parts[i]
            b_part = b_parts[i]

            # Numeric identifiers have lower precedence
            a_is_num = a_part.isdigit()
            b_is_num = b_part.isdigit()

            if a_is_num and b_is_num:
                a_num = int(a_part)
                b_num = int(b_part)
                if a_num != b_num:
                    return -1 if a_num < b_num else 1
            elif a_is_num:
                return -1
            elif b_is_num:
                return 1
            else:
                if a_part != b_part:
                    return -1 if a_part < b_part else 1

        return 0

    def bump_major(self) -> "Version":
        """Return a new version with major bumped."""
        return Version(self.major + 1, 0, 0)

    def bump_minor(self) -> "Version":
        """Return a new version with minor bumped."""
        return Version(self.major, self.minor + 1, 0)

    def bump_patch(self) -> "Version":
        """Return a new version with patch bumped."""
        return Version(self.major, self.minor, self.patch + 1)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "major": self.major,
            "minor": self.minor,
            "patch": self.patch,
            "prerelease": self.prerelease,
            "build": self.build,
            "string": str(self),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Version":
        """Create from dictionary."""
        return cls(
            major=data["major"],
            minor=data["minor"],
            patch=data["patch"],
            prerelease=data.get("prerelease"),
            build=data.get("build"),
        )

    def is_prerelease(self) -> bool:
        """Check if this is a pre-release version."""
        return self.prerelease is not None

    def is_stable(self) -> bool:
        """Check if this is a stable release (major > 0, no prerelease)."""
        return self.major > 0 and not self.prerelease

    def is_compatible_with(self, other: "Version") -> bool:
        """Check if this version is API-compatible with another.

        For semver, versions are compatible if they have the same major
        version (for major > 0) or same major.minor (for major == 0).
        """
        if self.major == 0 and other.major == 0:
            # 0.x.y versions: minor change is breaking
            return self.minor == other.minor
        return self.major == other.major


def parse_version(version_str: str) -> Version:
    """Parse a version string into a Version object.

    Args:
        version_str: Version string (e.g., "1.2.3", "v1.2.3-alpha.1+build.123").

    Returns:
        Version object.

    Raises:
        ValueError: If version string is invalid.
    """
    if not version_str:
        raise ValueError("Empty version string")

    match = SEMVER_PATTERN.match(version_str.strip())
    if not match:
        # Try simple parsing for common formats
        parts = version_str.lstrip("v").split(".")
        if len(parts) >= 3:
            try:
                major = int(parts[0])
                minor = int(parts[1])
                patch_str = parts[2].split("-")[0].split("+")[0]
                patch = int(patch_str)
                prerelease = None
                build = None

                if "-" in version_str:
                    pre_build = version_str.split("-", 1)[1]
                    if "+" in pre_build:
                        prerelease, build = pre_build.split("+", 1)
                    else:
                        prerelease = pre_build
                elif "+" in version_str:
                    build = version_str.split("+", 1)[1]

                return Version(major, minor, patch, prerelease, build)
            except (ValueError, IndexError):
                pass

        raise ValueError(f"Invalid version string: {version_str}")

    return Version(
        major=int(match.group("major")),
        minor=int(match.group("minor")),
        patch=int(match.group("patch")),
        prerelease=match.group("prerelease"),
        build=match.group("build"),
    )


def compare_versions(v1: str | Version, v2: str | Version) -> int:
    """Compare two versions.

    Args:
        v1: First version.
        v2: Second version.

    Returns:
        -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2.
    """
    if isinstance(v1, str):
        v1 = parse_version(v1)
    if isinstance(v2, str):
        v2 = parse_version(v2)

    if v1 < v2:
        return -1
    elif v1 > v2:
        return 1
    return 0
