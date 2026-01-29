"""Deduplication policies and fingerprint generation.

This module provides policies that determine what fields are
included in the deduplication fingerprint.

Policies:
    - NONE: No deduplication (testing)
    - BASIC: checkpoint_name + action_type
    - SEVERITY: + severity level
    - ISSUE_BASED: + issue hash
    - STRICT: + timestamp bucket
    - CUSTOM: User-defined fields

Different policies trade off between:
- Granularity: How specific the deduplication is
- Suppression: How many notifications are blocked
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class DeduplicationPolicy(str, Enum):
    """Deduplication policy types.

    Defines what fields are included in the fingerprint.
    """

    # No deduplication - every event is unique
    NONE = "none"

    # Basic: checkpoint name + action type
    BASIC = "basic"

    # Severity: basic + severity level
    SEVERITY = "severity"

    # Issue-based: basic + issue content hash
    ISSUE_BASED = "issue_based"

    # Strict: basic + timestamp bucket
    STRICT = "strict"

    # Custom: user-defined fields
    CUSTOM = "custom"


@dataclass
class FingerprintConfig:
    """Configuration for fingerprint generation.

    Attributes:
        include_checkpoint: Include checkpoint/source name.
        include_action_type: Include action/channel type.
        include_severity: Include severity level.
        include_issue_hash: Include hash of issue details.
        include_timestamp_bucket: Include timestamp bucket.
        timestamp_bucket_seconds: Size of timestamp buckets.
        custom_fields: Additional fields to include.
    """

    include_checkpoint: bool = True
    include_action_type: bool = True
    include_severity: bool = False
    include_issue_hash: bool = False
    include_timestamp_bucket: bool = False
    timestamp_bucket_seconds: int = 300
    custom_fields: list[str] = field(default_factory=list)

    @classmethod
    def from_policy(cls, policy: DeduplicationPolicy) -> "FingerprintConfig":
        """Create config from policy preset.

        Args:
            policy: Deduplication policy.

        Returns:
            Configured FingerprintConfig.
        """
        if policy == DeduplicationPolicy.NONE:
            return cls(
                include_checkpoint=False,
                include_action_type=False,
            )

        elif policy == DeduplicationPolicy.BASIC:
            return cls(
                include_checkpoint=True,
                include_action_type=True,
            )

        elif policy == DeduplicationPolicy.SEVERITY:
            return cls(
                include_checkpoint=True,
                include_action_type=True,
                include_severity=True,
            )

        elif policy == DeduplicationPolicy.ISSUE_BASED:
            return cls(
                include_checkpoint=True,
                include_action_type=True,
                include_issue_hash=True,
            )

        elif policy == DeduplicationPolicy.STRICT:
            return cls(
                include_checkpoint=True,
                include_action_type=True,
                include_severity=True,
                include_timestamp_bucket=True,
            )

        elif policy == DeduplicationPolicy.CUSTOM:
            # Custom requires explicit configuration
            return cls()

        return cls()


class FingerprintGenerator:
    """Generates deduplication fingerprints.

    The fingerprint uniquely identifies a notification for
    deduplication purposes. Two events with the same fingerprint
    within the deduplication window will be considered duplicates.

    Example:
        generator = FingerprintGenerator(
            policy=DeduplicationPolicy.SEVERITY
        )

        fingerprint = generator.generate(
            checkpoint_name="daily_check",
            action_type="slack",
            severity="high",
        )
    """

    def __init__(
        self,
        policy: DeduplicationPolicy = DeduplicationPolicy.BASIC,
        config: FingerprintConfig | None = None,
    ) -> None:
        """Initialize fingerprint generator.

        Args:
            policy: Deduplication policy to use.
            config: Optional explicit configuration (overrides policy).
        """
        self.policy = policy
        self.config = config or FingerprintConfig.from_policy(policy)

    def generate(
        self,
        checkpoint_name: str | None = None,
        action_type: str | None = None,
        severity: str | None = None,
        issues: list[dict[str, Any]] | None = None,
        timestamp: datetime | None = None,
        **custom_fields: Any,
    ) -> str:
        """Generate a fingerprint from event data.

        Args:
            checkpoint_name: Name of checkpoint/source.
            action_type: Type of notification action.
            severity: Severity level.
            issues: List of issues for hashing.
            timestamp: Event timestamp.
            **custom_fields: Additional fields for custom policy.

        Returns:
            Generated fingerprint string.
        """
        if self.policy == DeduplicationPolicy.NONE:
            # Unique fingerprint for each event
            return self._random_fingerprint()

        parts: list[str] = []

        # Add configured fields
        if self.config.include_checkpoint and checkpoint_name:
            parts.append(f"cp:{checkpoint_name}")

        if self.config.include_action_type and action_type:
            parts.append(f"act:{action_type}")

        if self.config.include_severity and severity:
            parts.append(f"sev:{severity}")

        if self.config.include_issue_hash and issues:
            issue_hash = self._hash_issues(issues)
            parts.append(f"ish:{issue_hash}")

        if self.config.include_timestamp_bucket:
            bucket = self._get_timestamp_bucket(timestamp)
            parts.append(f"ts:{bucket}")

        # Add custom fields
        for field_name in self.config.custom_fields:
            if field_name in custom_fields:
                value = custom_fields[field_name]
                parts.append(f"{field_name}:{value}")

        # Also add any extra custom fields passed
        for field_name, value in custom_fields.items():
            if field_name not in self.config.custom_fields:
                parts.append(f"{field_name}:{value}")

        if not parts:
            # Fallback to random if no parts
            return self._random_fingerprint()

        # Join parts and hash
        combined = "|".join(sorted(parts))
        return hashlib.sha256(combined.encode()).hexdigest()[:32]

    def _hash_issues(self, issues: list[dict[str, Any]]) -> str:
        """Generate hash from issue details."""
        import json

        # Sort issues for consistent hashing
        try:
            normalized = json.dumps(issues, sort_keys=True)
        except (TypeError, ValueError):
            normalized = str(issues)

        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def _get_timestamp_bucket(self, timestamp: datetime | None) -> int:
        """Get timestamp bucket number."""
        if timestamp is None:
            timestamp = datetime.utcnow()

        ts = timestamp.timestamp()
        bucket_size = self.config.timestamp_bucket_seconds
        return int(ts // bucket_size)

    def _random_fingerprint(self) -> str:
        """Generate a random unique fingerprint."""
        import secrets

        return secrets.token_hex(16)

    def with_policy(self, policy: DeduplicationPolicy) -> "FingerprintGenerator":
        """Create new generator with different policy.

        Args:
            policy: New policy to use.

        Returns:
            New FingerprintGenerator instance.
        """
        return FingerprintGenerator(policy=policy)

    def with_config(self, config: FingerprintConfig) -> "FingerprintGenerator":
        """Create new generator with custom config.

        Args:
            config: Custom configuration.

        Returns:
            New FingerprintGenerator instance.
        """
        return FingerprintGenerator(
            policy=DeduplicationPolicy.CUSTOM,
            config=config,
        )
