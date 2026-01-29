"""Security Protocol Definitions.

This module defines the core protocols and data types for the
enterprise plugin security system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Protocol


class IsolationLevel(str, Enum):
    """Sandbox isolation levels."""

    NONE = "none"           # No isolation (trusted plugins only)
    PROCESS = "process"     # Subprocess isolation with resource limits
    CONTAINER = "container" # Docker/Podman container isolation


class TrustLevel(str, Enum):
    """Plugin trust levels."""

    TRUSTED = "trusted"         # Signed by trusted authority, no issues
    VERIFIED = "verified"       # Signature valid but has warnings
    UNVERIFIED = "unverified"   # No signature or invalid
    SANDBOXED = "sandboxed"     # Must run in sandbox due to issues


class SignatureAlgorithm(str, Enum):
    """Supported signature algorithms."""

    SHA256 = "sha256"           # Simple hash (integrity only)
    SHA512 = "sha512"           # Simple hash (integrity only)
    HMAC_SHA256 = "hmac_sha256" # Symmetric key
    HMAC_SHA512 = "hmac_sha512" # Symmetric key
    RSA_SHA256 = "rsa_sha256"   # Asymmetric (public key)
    ED25519 = "ed25519"         # Modern asymmetric (recommended)


@dataclass
class ResourceLimits:
    """Resource limits for sandbox execution.

    Attributes:
        max_memory_mb: Maximum memory in megabytes.
        max_cpu_time_sec: Maximum CPU time in seconds.
        max_wall_time_sec: Maximum wall clock time in seconds.
        max_file_size_mb: Maximum file size in megabytes.
        max_open_files: Maximum number of open files.
        max_processes: Maximum number of processes.
        network_enabled: Whether network access is allowed.
        filesystem_read: Whether filesystem read is allowed.
        filesystem_write: Whether filesystem write is allowed.
    """

    max_memory_mb: int = 256
    max_cpu_time_sec: int = 30
    max_wall_time_sec: int = 60
    max_file_size_mb: int = 10
    max_open_files: int = 10
    max_processes: int = 1
    network_enabled: bool = False
    filesystem_read: bool = False
    filesystem_write: bool = False


@dataclass
class SecurityPolicy:
    """Security policy configuration.

    Attributes:
        name: Policy name.
        description: Policy description.
        isolation_level: Required isolation level.
        resource_limits: Resource limits.
        require_signature: Whether signature is required.
        min_signatures: Minimum number of valid signatures.
        allowed_signers: List of allowed signer IDs (empty = any).
        blocked_modules: Blocked Python modules.
        allowed_permissions: Allowed permission types.
    """

    name: str
    description: str = ""
    isolation_level: IsolationLevel = IsolationLevel.PROCESS
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)
    require_signature: bool = False
    min_signatures: int = 0
    allowed_signers: list[str] = field(default_factory=list)
    blocked_modules: list[str] = field(default_factory=lambda: [
        "os", "subprocess", "sys", "shutil", "socket",
        "http", "urllib", "requests", "httpx",
        "multiprocessing", "threading", "ctypes",
        "pickle", "shelve", "sqlite3", "importlib",
    ])
    allowed_permissions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "isolation_level": self.isolation_level.value,
            "resource_limits": {
                "max_memory_mb": self.resource_limits.max_memory_mb,
                "max_cpu_time_sec": self.resource_limits.max_cpu_time_sec,
                "max_wall_time_sec": self.resource_limits.max_wall_time_sec,
                "max_file_size_mb": self.resource_limits.max_file_size_mb,
                "max_open_files": self.resource_limits.max_open_files,
                "max_processes": self.resource_limits.max_processes,
                "network_enabled": self.resource_limits.network_enabled,
                "filesystem_read": self.resource_limits.filesystem_read,
                "filesystem_write": self.resource_limits.filesystem_write,
            },
            "require_signature": self.require_signature,
            "min_signatures": self.min_signatures,
            "allowed_signers": self.allowed_signers,
            "blocked_modules": self.blocked_modules,
            "allowed_permissions": self.allowed_permissions,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SecurityPolicy":
        """Create from dictionary."""
        limits_data = data.get("resource_limits", {})
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            isolation_level=IsolationLevel(data.get("isolation_level", "process")),
            resource_limits=ResourceLimits(
                max_memory_mb=limits_data.get("max_memory_mb", 256),
                max_cpu_time_sec=limits_data.get("max_cpu_time_sec", 30),
                max_wall_time_sec=limits_data.get("max_wall_time_sec", 60),
                max_file_size_mb=limits_data.get("max_file_size_mb", 10),
                max_open_files=limits_data.get("max_open_files", 10),
                max_processes=limits_data.get("max_processes", 1),
                network_enabled=limits_data.get("network_enabled", False),
                filesystem_read=limits_data.get("filesystem_read", False),
                filesystem_write=limits_data.get("filesystem_write", False),
            ),
            require_signature=data.get("require_signature", False),
            min_signatures=data.get("min_signatures", 0),
            allowed_signers=data.get("allowed_signers", []),
            blocked_modules=data.get("blocked_modules", []),
            allowed_permissions=data.get("allowed_permissions", []),
        )


@dataclass
class SignatureInfo:
    """Information about a plugin signature.

    Attributes:
        algorithm: Signature algorithm used.
        signature: The signature value (hex or base64).
        signer_id: ID of the signer.
        timestamp: When the signature was created.
        certificate: Optional certificate chain.
        metadata: Additional metadata.
    """

    algorithm: SignatureAlgorithm
    signature: str
    signer_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    certificate: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "algorithm": self.algorithm.value,
            "signature": self.signature,
            "signer_id": self.signer_id,
            "timestamp": self.timestamp.isoformat(),
            "certificate": self.certificate,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SignatureInfo":
        """Create from dictionary."""
        return cls(
            algorithm=SignatureAlgorithm(data["algorithm"]),
            signature=data["signature"],
            signer_id=data["signer_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            certificate=data.get("certificate"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class VerificationResult:
    """Result of signature verification.

    Attributes:
        is_valid: Whether verification succeeded.
        trust_level: Determined trust level.
        signer_id: ID of the verified signer.
        algorithm: Algorithm used.
        errors: List of error messages.
        warnings: List of warning messages.
        verified_at: When verification was performed.
        metadata: Additional verification metadata.
    """

    is_valid: bool
    trust_level: TrustLevel = TrustLevel.UNVERIFIED
    signer_id: str | None = None
    algorithm: SignatureAlgorithm | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    verified_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "trust_level": self.trust_level.value,
            "signer_id": self.signer_id,
            "algorithm": self.algorithm.value if self.algorithm else None,
            "errors": self.errors,
            "warnings": self.warnings,
            "verified_at": self.verified_at.isoformat(),
            "metadata": self.metadata,
        }


class ISigningService(Protocol):
    """Protocol for signing services."""

    def sign(
        self,
        data: bytes,
        private_key: bytes,
        signer_id: str,
    ) -> SignatureInfo:
        """Sign data and return signature info."""
        ...

    def verify(
        self,
        data: bytes,
        signature_info: SignatureInfo,
        public_key: bytes | None = None,
    ) -> VerificationResult:
        """Verify a signature."""
        ...


class ITrustStore(Protocol):
    """Protocol for trust stores."""

    def add_signer(
        self,
        signer_id: str,
        public_key: bytes,
        trust_level: TrustLevel,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a trusted signer."""
        ...

    def remove_signer(self, signer_id: str) -> None:
        """Remove a signer."""
        ...

    def get_trust_level(self, signer_id: str) -> TrustLevel | None:
        """Get trust level for a signer."""
        ...

    def get_public_key(self, signer_id: str) -> bytes | None:
        """Get public key for a signer."""
        ...

    def is_trusted(self, signer_id: str) -> bool:
        """Check if signer is trusted."""
        ...


class IVerificationChain(Protocol):
    """Protocol for verification chains."""

    def verify(
        self,
        data: bytes,
        signatures: list[SignatureInfo],
        context: dict[str, Any] | None = None,
    ) -> VerificationResult:
        """Verify signatures using the chain."""
        ...
