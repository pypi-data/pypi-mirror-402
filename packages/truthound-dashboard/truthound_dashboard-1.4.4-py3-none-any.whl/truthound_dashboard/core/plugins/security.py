"""Plugin Security Management.

This module provides security features for plugins:
- Signature verification
- Permission management
- Security analysis
"""

from __future__ import annotations

import hashlib
import hmac
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .sandbox import CodeAnalyzer, SandboxConfig

logger = logging.getLogger(__name__)


@dataclass
class SecurityReport:
    """Security analysis report for a plugin.

    Attributes:
        plugin_id: Plugin identifier.
        analyzed_at: When analysis was performed.
        risk_level: Overall risk level.
        signature_valid: Whether signature is valid.
        sandbox_compatible: Whether code can run in sandbox.
        issues: Critical security issues found.
        warnings: Non-critical warnings.
        permissions_required: Required permissions.
        code_hash: Hash of analyzed code.
    """

    plugin_id: str
    analyzed_at: datetime
    risk_level: str  # trusted, verified, unverified, sandboxed
    signature_valid: bool = False
    sandbox_compatible: bool = True
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    permissions_required: list[str] = field(default_factory=list)
    code_hash: str = ""

    def is_safe(self) -> bool:
        """Check if plugin is considered safe.

        Returns:
            True if no critical issues and sandbox compatible.
        """
        return len(self.issues) == 0 and self.sandbox_compatible


class SignatureVerifier:
    """Verifies plugin signatures.

    This class handles cryptographic verification of plugin
    packages to ensure authenticity and integrity.

    Attributes:
        trusted_keys: Dictionary of trusted public keys by key ID.
    """

    def __init__(self, trusted_keys: dict[str, str] | None = None) -> None:
        """Initialize the verifier.

        Args:
            trusted_keys: Dictionary mapping key IDs to public keys.
        """
        self.trusted_keys = trusted_keys or {}

    def add_trusted_key(self, key_id: str, public_key: str) -> None:
        """Add a trusted public key.

        Args:
            key_id: Key identifier.
            public_key: Public key (hex encoded).
        """
        self.trusted_keys[key_id] = public_key
        logger.info(f"Added trusted key: {key_id}")

    def remove_trusted_key(self, key_id: str) -> None:
        """Remove a trusted public key.

        Args:
            key_id: Key identifier.
        """
        if key_id in self.trusted_keys:
            del self.trusted_keys[key_id]
            logger.info(f"Removed trusted key: {key_id}")

    def verify_hmac(
        self,
        data: bytes,
        signature: str,
        secret_key: str,
    ) -> bool:
        """Verify HMAC signature.

        Args:
            data: Data that was signed.
            signature: HMAC signature (hex encoded).
            secret_key: Secret key for HMAC.

        Returns:
            True if signature is valid.
        """
        try:
            expected = hmac.new(
                secret_key.encode(),
                data,
                hashlib.sha256,
            ).hexdigest()
            return hmac.compare_digest(expected, signature)
        except Exception as e:
            logger.warning(f"HMAC verification failed: {e}")
            return False

    def verify_signature(
        self,
        data: bytes,
        signature: str,
        key_id: str | None = None,
    ) -> tuple[bool, str | None]:
        """Verify a signature.

        Args:
            data: Data that was signed.
            signature: Signature (format depends on algorithm).
            key_id: Optional key ID to use.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not signature:
            return False, "No signature provided"

        # For now, use simple HMAC verification
        # In production, you would use proper asymmetric cryptography
        # like Ed25519 or RSA

        if key_id and key_id in self.trusted_keys:
            key = self.trusted_keys[key_id]
            if self.verify_hmac(data, signature, key):
                return True, None
            return False, "Signature verification failed"

        # Try all trusted keys
        for kid, key in self.trusted_keys.items():
            if self.verify_hmac(data, signature, key):
                return True, None

        return False, "No matching trusted key found"

    def create_signature(
        self,
        data: bytes,
        secret_key: str,
    ) -> str:
        """Create a signature for data.

        Args:
            data: Data to sign.
            secret_key: Secret key for signing.

        Returns:
            Signature (hex encoded).
        """
        return hmac.new(
            secret_key.encode(),
            data,
            hashlib.sha256,
        ).hexdigest()


class PluginSecurityManager:
    """Manages security for plugins.

    This class provides comprehensive security analysis
    and management for plugins.

    Attributes:
        signature_verifier: Signature verifier instance.
        sandbox_config: Default sandbox configuration.
    """

    def __init__(
        self,
        signature_verifier: SignatureVerifier | None = None,
        sandbox_config: SandboxConfig | None = None,
    ) -> None:
        """Initialize the security manager.

        Args:
            signature_verifier: Signature verifier.
            sandbox_config: Default sandbox configuration.
        """
        self.signature_verifier = signature_verifier or SignatureVerifier()
        self.sandbox_config = sandbox_config or SandboxConfig()

    def analyze_code(self, code: str) -> tuple[list[str], list[str]]:
        """Analyze code for security issues.

        Args:
            code: Python source code.

        Returns:
            Tuple of (issues, warnings).
        """
        analyzer = CodeAnalyzer()
        return analyzer.analyze(code)

    def detect_permissions(self, code: str) -> list[str]:
        """Detect required permissions from code.

        Args:
            code: Python source code.

        Returns:
            List of required permission strings.
        """
        import ast

        permissions = set()

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                # Check imports
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    module = getattr(node, "module", None)
                    if module:
                        modules = [module]
                    else:
                        modules = [alias.name for alias in node.names]

                    for mod in modules:
                        if mod.startswith(("http", "urllib", "requests", "httpx", "socket")):
                            permissions.add("network_access")
                        elif mod.startswith(("os", "shutil", "pathlib")):
                            permissions.add("file_system")
                        elif mod.startswith(("subprocess", "multiprocessing")):
                            permissions.add("execute_code")
                        elif mod.startswith(("pickle", "shelve")):
                            permissions.add("read_data")
                            permissions.add("write_data")

                # Check for file operations
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id == "open":
                            permissions.add("file_system")

        except SyntaxError:
            pass

        return sorted(list(permissions))

    def analyze_plugin(
        self,
        plugin_id: str,
        code: str,
        signature: str | None = None,
        package_data: bytes | None = None,
    ) -> SecurityReport:
        """Perform security analysis on a plugin.

        Args:
            plugin_id: Plugin identifier.
            code: Plugin code to analyze.
            signature: Optional signature to verify.
            package_data: Optional package data for signature verification.

        Returns:
            SecurityReport with analysis results.
        """
        issues, warnings = self.analyze_code(code)
        permissions = self.detect_permissions(code)
        code_hash = hashlib.sha256(code.encode()).hexdigest()

        # Verify signature if provided
        signature_valid = False
        if signature and package_data:
            signature_valid, _ = self.signature_verifier.verify_signature(
                package_data, signature
            )
        elif signature and code:
            signature_valid, _ = self.signature_verifier.verify_signature(
                code.encode(), signature
            )

        # Determine risk level
        if signature_valid:
            if not issues:
                risk_level = "trusted"
            else:
                risk_level = "verified"
        else:
            if issues:
                risk_level = "sandboxed"
            else:
                risk_level = "unverified"

        # Check sandbox compatibility
        sandbox_compatible = self._check_sandbox_compatible(code, issues)

        return SecurityReport(
            plugin_id=plugin_id,
            analyzed_at=datetime.utcnow(),
            risk_level=risk_level,
            signature_valid=signature_valid,
            sandbox_compatible=sandbox_compatible,
            issues=issues,
            warnings=warnings,
            permissions_required=permissions,
            code_hash=code_hash,
        )

    def _check_sandbox_compatible(
        self,
        code: str,
        issues: list[str],
    ) -> bool:
        """Check if code is compatible with sandbox execution.

        Args:
            code: Python source code.
            issues: Already detected issues.

        Returns:
            True if code can run in sandbox.
        """
        # If there are critical issues, might not be compatible
        if any("blocked" in issue.lower() for issue in issues):
            return False

        # Check for patterns that won't work in sandbox
        dangerous_patterns = [
            "__import__",
            "importlib",
            "sys.modules",
            "globals()",
            "locals()",
            "__class__.__bases__",
            "__subclasses__",
        ]

        for pattern in dangerous_patterns:
            if pattern in code:
                return False

        return True

    def validate_permissions(
        self,
        required: list[str],
        granted: list[str],
    ) -> tuple[bool, list[str]]:
        """Validate that required permissions are granted.

        Args:
            required: Required permissions.
            granted: Granted permissions.

        Returns:
            Tuple of (all_granted, missing_permissions).
        """
        granted_set = set(granted)
        missing = [p for p in required if p not in granted_set]
        return len(missing) == 0, missing

    def get_security_level(
        self,
        report: SecurityReport,
        user_trust_level: str = "normal",
    ) -> str:
        """Determine final security level based on analysis and trust.

        Args:
            report: Security analysis report.
            user_trust_level: User's trust level (admin, normal, restricted).

        Returns:
            Final security level recommendation.
        """
        if user_trust_level == "admin":
            # Admins can run anything
            return report.risk_level

        if user_trust_level == "restricted":
            # Restricted users can only run trusted plugins
            if report.risk_level != "trusted":
                return "sandboxed"
            return report.risk_level

        # Normal users
        if report.issues:
            return "sandboxed"

        return report.risk_level

    def create_sandbox_config_for_plugin(
        self,
        report: SecurityReport,
        base_config: SandboxConfig | None = None,
    ) -> SandboxConfig:
        """Create appropriate sandbox config based on security analysis.

        Args:
            report: Security analysis report.
            base_config: Base configuration to modify.

        Returns:
            Configured SandboxConfig.
        """
        config = base_config or SandboxConfig()

        # Adjust based on risk level
        if report.risk_level == "trusted":
            # Trusted plugins get more freedom
            config.enabled = False
        elif report.risk_level == "verified":
            # Verified plugins get relaxed restrictions
            config.memory_limit_mb = 512
            config.cpu_time_limit_seconds = 60
            config.network_enabled = "network_access" in report.permissions_required
        elif report.risk_level == "unverified":
            # Default restrictions
            config.enabled = True
        else:  # sandboxed
            # Strict restrictions
            config.memory_limit_mb = 128
            config.cpu_time_limit_seconds = 15
            config.network_enabled = False

        return config


# Default instances
signature_verifier = SignatureVerifier()
security_manager = PluginSecurityManager(signature_verifier)
