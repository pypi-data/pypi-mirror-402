"""Result versioning system for validation results.

This module provides versioning capabilities for validation results,
allowing tracking of changes, comparisons between versions, and rollback.

Versioning strategies:
- Incremental: Simple numeric versioning (v1, v2, v3...)
- Semantic: Semver-style versioning (major.minor.patch)
- Timestamp: ISO timestamp-based versioning
- GitLike: SHA-based versioning similar to git commits

Example:
    from truthound_dashboard.core.versioning import (
        VersionManager,
        VersioningStrategy,
        create_version,
    )

    # Create a version for a validation result
    version = create_version(
        validation_id="...",
        strategy=VersioningStrategy.INCREMENTAL,
    )

    # Compare versions
    diff = await version_manager.compare_versions(v1_id, v2_id)
"""

from __future__ import annotations

import hashlib
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class VersioningStrategy(str, Enum):
    """Versioning strategy types."""

    INCREMENTAL = "incremental"  # v1, v2, v3...
    SEMANTIC = "semantic"  # major.minor.patch
    TIMESTAMP = "timestamp"  # ISO timestamp
    GITLIKE = "gitlike"  # SHA-based


@dataclass
class VersionInfo:
    """Version information for a validation result.

    Attributes:
        version_id: Unique version identifier.
        version_number: Human-readable version number.
        validation_id: ID of the validation this version represents.
        source_id: ID of the data source.
        strategy: Versioning strategy used.
        created_at: When this version was created.
        parent_version_id: Previous version ID (for history chain).
        metadata: Additional version metadata.
        content_hash: Hash of the validation result content.
    """

    version_id: str
    version_number: str
    validation_id: str
    source_id: str
    strategy: VersioningStrategy
    created_at: datetime = field(default_factory=datetime.utcnow)
    parent_version_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    content_hash: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version_id": self.version_id,
            "version_number": self.version_number,
            "validation_id": self.validation_id,
            "source_id": self.source_id,
            "strategy": self.strategy.value,
            "created_at": self.created_at.isoformat(),
            "parent_version_id": self.parent_version_id,
            "metadata": self.metadata,
            "content_hash": self.content_hash,
        }


@dataclass
class VersionDiff:
    """Difference between two validation versions.

    Attributes:
        from_version: Source version info.
        to_version: Target version info.
        issues_added: New issues in target version.
        issues_removed: Issues no longer present in target.
        issues_changed: Issues that changed severity or count.
        summary_changes: Changes to summary statistics.
    """

    from_version: VersionInfo
    to_version: VersionInfo
    issues_added: list[dict[str, Any]] = field(default_factory=list)
    issues_removed: list[dict[str, Any]] = field(default_factory=list)
    issues_changed: list[dict[str, Any]] = field(default_factory=list)
    summary_changes: dict[str, Any] = field(default_factory=dict)


@dataclass
class RollbackResult:
    """Result of a version rollback operation.

    Attributes:
        success: Whether rollback succeeded.
        source_id: ID of the data source.
        from_version: Original version before rollback.
        to_version: Target version after rollback.
        new_validation_id: ID of newly created validation from rollback.
        message: Status message.
        rolled_back_at: When rollback was performed.
    """

    success: bool
    source_id: str
    from_version: VersionInfo | None = None
    to_version: VersionInfo | None = None
    new_validation_id: str | None = None
    message: str = ""
    rolled_back_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "source_id": self.source_id,
            "from_version": self.from_version.to_dict() if self.from_version else None,
            "to_version": self.to_version.to_dict() if self.to_version else None,
            "new_validation_id": self.new_validation_id,
            "message": self.message,
            "rolled_back_at": self.rolled_back_at.isoformat(),
        }

    @property
    def has_changes(self) -> bool:
        """Check if there are any changes between versions."""
        return bool(
            self.issues_added or self.issues_removed or self.issues_changed
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "from_version": self.from_version.to_dict(),
            "to_version": self.to_version.to_dict(),
            "issues_added": self.issues_added,
            "issues_removed": self.issues_removed,
            "issues_changed": self.issues_changed,
            "summary_changes": self.summary_changes,
            "has_changes": self.has_changes,
        }


class VersionNumberGenerator(ABC):
    """Abstract base for version number generators."""

    @abstractmethod
    def generate(
        self,
        current_version: str | None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Generate next version number.

        Args:
            current_version: Current/previous version number.
            metadata: Optional metadata for generation.

        Returns:
            New version number string.
        """
        ...


class IncrementalVersionGenerator(VersionNumberGenerator):
    """Simple incremental versioning (v1, v2, v3...)."""

    def generate(
        self,
        current_version: str | None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        if current_version is None:
            return "v1"

        # Extract number from current version
        try:
            num = int(current_version.lstrip("v"))
            return f"v{num + 1}"
        except ValueError:
            return "v1"


class SemanticVersionGenerator(VersionNumberGenerator):
    """Semantic versioning (major.minor.patch).

    Bump rules:
    - patch: Minor fixes, no new issues
    - minor: New issues found, same data
    - major: Schema changes or significant differences
    """

    def generate(
        self,
        current_version: str | None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        metadata = metadata or {}

        if current_version is None:
            return "1.0.0"

        try:
            parts = current_version.split(".")
            major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        except (ValueError, IndexError):
            return "1.0.0"

        # Determine bump type from metadata
        bump_type = metadata.get("bump_type", "patch")

        if bump_type == "major":
            return f"{major + 1}.0.0"
        elif bump_type == "minor":
            return f"{major}.{minor + 1}.0"
        else:  # patch
            return f"{major}.{minor}.{patch + 1}"


class TimestampVersionGenerator(VersionNumberGenerator):
    """ISO timestamp-based versioning."""

    def generate(
        self,
        current_version: str | None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        return datetime.utcnow().strftime("%Y%m%d.%H%M%S")


class GitLikeVersionGenerator(VersionNumberGenerator):
    """SHA-based versioning similar to git commits."""

    def generate(
        self,
        current_version: str | None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        metadata = metadata or {}

        # Create content for hashing
        content = {
            "timestamp": datetime.utcnow().isoformat(),
            "parent": current_version,
            "data": metadata.get("content_hash", ""),
        }

        content_str = json.dumps(content, sort_keys=True)
        sha = hashlib.sha256(content_str.encode()).hexdigest()

        return sha[:8]  # Short SHA like git


def get_version_generator(strategy: VersioningStrategy) -> VersionNumberGenerator:
    """Get version generator for a strategy.

    Args:
        strategy: Versioning strategy.

    Returns:
        Appropriate version generator.
    """
    generators = {
        VersioningStrategy.INCREMENTAL: IncrementalVersionGenerator,
        VersioningStrategy.SEMANTIC: SemanticVersionGenerator,
        VersioningStrategy.TIMESTAMP: TimestampVersionGenerator,
        VersioningStrategy.GITLIKE: GitLikeVersionGenerator,
    }
    return generators[strategy]()


def compute_content_hash(result_json: dict[str, Any] | None) -> str:
    """Compute hash of validation result content.

    Args:
        result_json: Validation result JSON.

    Returns:
        SHA-256 hash of content.
    """
    if not result_json:
        return hashlib.sha256(b"").hexdigest()[:16]

    content = json.dumps(result_json, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()[:16]


class VersionManager:
    """Manager for validation result versions.

    Handles version creation, storage, and comparison.
    """

    def __init__(self, default_strategy: VersioningStrategy = VersioningStrategy.INCREMENTAL) -> None:
        """Initialize version manager.

        Args:
            default_strategy: Default versioning strategy to use.
        """
        self._default_strategy = default_strategy
        # In-memory version storage (in production, use database)
        self._versions: dict[str, VersionInfo] = {}
        # Source -> latest version mapping
        self._source_versions: dict[str, str] = {}

    async def create_version(
        self,
        validation_id: str,
        source_id: str,
        result_json: dict[str, Any] | None = None,
        strategy: VersioningStrategy | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> VersionInfo:
        """Create a new version for a validation result.

        Args:
            validation_id: ID of the validation.
            source_id: ID of the data source.
            result_json: Validation result data.
            strategy: Versioning strategy (uses default if not specified).
            metadata: Additional version metadata.

        Returns:
            Created VersionInfo.
        """
        strategy = strategy or self._default_strategy
        metadata = metadata or {}

        # Get previous version for this source
        parent_version_id = self._source_versions.get(source_id)
        parent_version = self._versions.get(parent_version_id) if parent_version_id else None
        current_version_number = parent_version.version_number if parent_version else None

        # Compute content hash
        content_hash = compute_content_hash(result_json)
        metadata["content_hash"] = content_hash

        # Generate version number
        generator = get_version_generator(strategy)
        version_number = generator.generate(current_version_number, metadata)

        # Create version info
        version_id = f"{source_id}_{validation_id}_{version_number}"
        version_info = VersionInfo(
            version_id=version_id,
            version_number=version_number,
            validation_id=validation_id,
            source_id=source_id,
            strategy=strategy,
            parent_version_id=parent_version_id,
            metadata=metadata,
            content_hash=content_hash,
        )

        # Store version
        self._versions[version_id] = version_info
        self._source_versions[source_id] = version_id

        logger.debug(
            f"Created version {version_number} for source {source_id} "
            f"(validation: {validation_id})"
        )

        return version_info

    async def get_version(self, version_id: str) -> VersionInfo | None:
        """Get a specific version by ID.

        Args:
            version_id: Version identifier.

        Returns:
            VersionInfo or None if not found.
        """
        return self._versions.get(version_id)

    async def get_latest_version(self, source_id: str) -> VersionInfo | None:
        """Get the latest version for a source.

        Args:
            source_id: Source identifier.

        Returns:
            Latest VersionInfo or None if no versions exist.
        """
        version_id = self._source_versions.get(source_id)
        if version_id:
            return self._versions.get(version_id)
        return None

    async def list_versions(
        self,
        source_id: str,
        limit: int = 20,
    ) -> list[VersionInfo]:
        """List versions for a source.

        Args:
            source_id: Source identifier.
            limit: Maximum versions to return.

        Returns:
            List of VersionInfo, newest first.
        """
        versions = [
            v for v in self._versions.values()
            if v.source_id == source_id
        ]
        versions.sort(key=lambda v: v.created_at, reverse=True)
        return versions[:limit]

    async def compare_versions(
        self,
        from_version_id: str,
        to_version_id: str,
        from_result: dict[str, Any] | None = None,
        to_result: dict[str, Any] | None = None,
    ) -> VersionDiff:
        """Compare two versions and compute differences.

        Args:
            from_version_id: Source version ID.
            to_version_id: Target version ID.
            from_result: Optional result JSON for source version.
            to_result: Optional result JSON for target version.

        Returns:
            VersionDiff with changes between versions.

        Raises:
            ValueError: If either version is not found.
        """
        from_version = await self.get_version(from_version_id)
        to_version = await self.get_version(to_version_id)

        if not from_version:
            raise ValueError(f"Version not found: {from_version_id}")
        if not to_version:
            raise ValueError(f"Version not found: {to_version_id}")

        # Extract issues from results
        from_issues = from_result.get("issues", []) if from_result else []
        to_issues = to_result.get("issues", []) if to_result else []

        # Create issue keys for comparison
        def issue_key(issue: dict[str, Any]) -> str:
            return f"{issue.get('column', '')}:{issue.get('issue_type', '')}"

        from_issues_map = {issue_key(i): i for i in from_issues}
        to_issues_map = {issue_key(i): i for i in to_issues}

        # Find differences
        issues_added = [
            to_issues_map[k] for k in to_issues_map
            if k not in from_issues_map
        ]
        issues_removed = [
            from_issues_map[k] for k in from_issues_map
            if k not in to_issues_map
        ]

        # Find changed issues (same key but different content)
        issues_changed = []
        for key in from_issues_map:
            if key in to_issues_map:
                from_issue = from_issues_map[key]
                to_issue = to_issues_map[key]
                if (
                    from_issue.get("count") != to_issue.get("count") or
                    from_issue.get("severity") != to_issue.get("severity")
                ):
                    issues_changed.append({
                        "key": key,
                        "from": from_issue,
                        "to": to_issue,
                    })

        # Summary changes
        summary_changes = {
            "issues_added_count": len(issues_added),
            "issues_removed_count": len(issues_removed),
            "issues_changed_count": len(issues_changed),
        }

        return VersionDiff(
            from_version=from_version,
            to_version=to_version,
            issues_added=issues_added,
            issues_removed=issues_removed,
            issues_changed=issues_changed,
            summary_changes=summary_changes,
        )

    async def get_version_history(
        self,
        version_id: str,
        depth: int = 10,
    ) -> list[VersionInfo]:
        """Get version history chain.

        Args:
            version_id: Starting version ID.
            depth: Maximum history depth.

        Returns:
            List of versions in history chain.
        """
        history = []
        current_id = version_id

        while current_id and len(history) < depth:
            version = await self.get_version(current_id)
            if not version:
                break
            history.append(version)
            current_id = version.parent_version_id

        return history

    async def rollback_to_version(
        self,
        source_id: str,
        target_version_id: str,
        create_new_validation: bool = True,
    ) -> RollbackResult:
        """Rollback to a previous version.

        This operation sets the specified version as the current active version
        for the source. Optionally creates a new validation record based on
        the target version's validation data.

        Args:
            source_id: ID of the data source.
            target_version_id: ID of the version to rollback to.
            create_new_validation: Whether to create a new validation from target.

        Returns:
            RollbackResult with operation details.
        """
        # Get current version
        current_version_id = self._source_versions.get(source_id)
        current_version = self._versions.get(current_version_id) if current_version_id else None

        # Get target version
        target_version = self._versions.get(target_version_id)
        if not target_version:
            return RollbackResult(
                success=False,
                source_id=source_id,
                message=f"Target version not found: {target_version_id}",
            )

        # Verify target belongs to the same source
        if target_version.source_id != source_id:
            return RollbackResult(
                success=False,
                source_id=source_id,
                message=f"Version {target_version_id} does not belong to source {source_id}",
            )

        # Verify not rolling back to current version
        if current_version_id == target_version_id:
            return RollbackResult(
                success=False,
                source_id=source_id,
                from_version=current_version,
                to_version=target_version,
                message="Cannot rollback to current version",
            )

        # Create rollback version (new version pointing to target's validation)
        new_validation_id = None
        if create_new_validation:
            # Generate a new validation ID for the rollback
            import uuid
            new_validation_id = str(uuid.uuid4())

            # Create a new version that represents the rollback
            rollback_version = await self.create_version(
                validation_id=new_validation_id,
                source_id=source_id,
                result_json=target_version.metadata.get("result_json"),
                strategy=target_version.strategy,
                metadata={
                    "rollback_from": current_version_id,
                    "rollback_to": target_version_id,
                    "rollback_type": "explicit",
                    "original_validation_id": target_version.validation_id,
                },
            )

            logger.info(
                f"Rolled back source {source_id} from {current_version_id} "
                f"to {target_version_id}, new version: {rollback_version.version_id}"
            )
        else:
            # Just update the pointer without creating new version
            self._source_versions[source_id] = target_version_id

            logger.info(
                f"Rolled back source {source_id} from {current_version_id} "
                f"to {target_version_id} (pointer update only)"
            )

        return RollbackResult(
            success=True,
            source_id=source_id,
            from_version=current_version,
            to_version=target_version,
            new_validation_id=new_validation_id,
            message=f"Successfully rolled back to version {target_version.version_number}",
        )

    async def can_rollback(self, source_id: str) -> dict[str, Any]:
        """Check if rollback is available for a source.

        Args:
            source_id: ID of the data source.

        Returns:
            Dictionary with rollback availability info.
        """
        versions = await self.list_versions(source_id, limit=100)
        current_version_id = self._source_versions.get(source_id)

        return {
            "can_rollback": len(versions) > 1,
            "current_version_id": current_version_id,
            "available_versions": len(versions),
            "rollback_targets": [
                v.to_dict() for v in versions
                if v.version_id != current_version_id
            ][:10],  # Limit to 10 recent targets
        }


# Singleton instance
_version_manager: VersionManager | None = None


def get_version_manager() -> VersionManager:
    """Get the singleton version manager.

    Returns:
        VersionManager instance.
    """
    global _version_manager
    if _version_manager is None:
        _version_manager = VersionManager()
    return _version_manager


def reset_version_manager() -> None:
    """Reset version manager singleton (for testing)."""
    global _version_manager
    _version_manager = None


async def create_version(
    validation_id: str,
    source_id: str,
    result_json: dict[str, Any] | None = None,
    strategy: VersioningStrategy | None = None,
    metadata: dict[str, Any] | None = None,
) -> VersionInfo:
    """Convenience function to create a version.

    Args:
        validation_id: ID of the validation.
        source_id: ID of the data source.
        result_json: Validation result data.
        strategy: Versioning strategy.
        metadata: Additional metadata.

    Returns:
        Created VersionInfo.
    """
    manager = get_version_manager()
    return await manager.create_version(
        validation_id=validation_id,
        source_id=source_id,
        result_json=result_json,
        strategy=strategy,
        metadata=metadata,
    )
