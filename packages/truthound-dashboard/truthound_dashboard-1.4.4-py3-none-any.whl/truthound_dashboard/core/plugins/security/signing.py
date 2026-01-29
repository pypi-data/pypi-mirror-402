"""Signature Verification and Trust Store.

This module provides:
- Multiple signature algorithms (HMAC, RSA, Ed25519)
- Trust store for managing trusted signers
- Verification chain (Chain of Responsibility pattern)
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

from .protocols import (
    SignatureAlgorithm,
    SignatureInfo,
    TrustLevel,
    VerificationResult,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Signing Service
# =============================================================================


class SigningService(ABC):
    """Abstract base class for signing services."""

    @property
    @abstractmethod
    def algorithm(self) -> SignatureAlgorithm:
        """Get the signing algorithm."""
        ...

    @abstractmethod
    def sign(
        self,
        data: bytes,
        private_key: bytes,
        signer_id: str,
    ) -> SignatureInfo:
        """Sign data and return signature info.

        Args:
            data: Data to sign.
            private_key: Private key for signing.
            signer_id: ID of the signer.

        Returns:
            SignatureInfo with the signature.
        """
        ...

    @abstractmethod
    def verify(
        self,
        data: bytes,
        signature_info: SignatureInfo,
        public_key: bytes | None = None,
    ) -> VerificationResult:
        """Verify a signature.

        Args:
            data: Original data.
            signature_info: Signature to verify.
            public_key: Public key (required for asymmetric algorithms).

        Returns:
            VerificationResult with verification status.
        """
        ...


class HMACSigningService(SigningService):
    """HMAC-based signing service (SHA256 or SHA512)."""

    def __init__(self, use_sha512: bool = False) -> None:
        """Initialize HMAC signing service.

        Args:
            use_sha512: Use SHA512 instead of SHA256.
        """
        self._use_sha512 = use_sha512
        self._hash_func = hashlib.sha512 if use_sha512 else hashlib.sha256

    @property
    def algorithm(self) -> SignatureAlgorithm:
        """Get the signing algorithm."""
        return (
            SignatureAlgorithm.HMAC_SHA512
            if self._use_sha512
            else SignatureAlgorithm.HMAC_SHA256
        )

    def sign(
        self,
        data: bytes,
        private_key: bytes,
        signer_id: str,
    ) -> SignatureInfo:
        """Sign data using HMAC."""
        signature = hmac.new(private_key, data, self._hash_func).hexdigest()
        return SignatureInfo(
            algorithm=self.algorithm,
            signature=signature,
            signer_id=signer_id,
            timestamp=datetime.utcnow(),
        )

    def verify(
        self,
        data: bytes,
        signature_info: SignatureInfo,
        public_key: bytes | None = None,
    ) -> VerificationResult:
        """Verify HMAC signature."""
        if public_key is None:
            return VerificationResult(
                is_valid=False,
                errors=["HMAC verification requires a key"],
            )

        try:
            expected = hmac.new(public_key, data, self._hash_func).hexdigest()
            is_valid = hmac.compare_digest(expected, signature_info.signature)
            return VerificationResult(
                is_valid=is_valid,
                trust_level=TrustLevel.VERIFIED if is_valid else TrustLevel.UNVERIFIED,
                signer_id=signature_info.signer_id,
                algorithm=self.algorithm,
                errors=[] if is_valid else ["Signature mismatch"],
            )
        except Exception as e:
            return VerificationResult(
                is_valid=False,
                errors=[f"Verification error: {str(e)}"],
            )


class RSASigningService(SigningService):
    """RSA-based signing service."""

    @property
    def algorithm(self) -> SignatureAlgorithm:
        """Get the signing algorithm."""
        return SignatureAlgorithm.RSA_SHA256

    def sign(
        self,
        data: bytes,
        private_key: bytes,
        signer_id: str,
    ) -> SignatureInfo:
        """Sign data using RSA."""
        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding, rsa

            # Load private key
            key = serialization.load_pem_private_key(private_key, password=None)
            if not isinstance(key, rsa.RSAPrivateKey):
                raise ValueError("Not an RSA private key")

            # Sign
            signature = key.sign(
                data,
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
            return SignatureInfo(
                algorithm=self.algorithm,
                signature=base64.b64encode(signature).decode(),
                signer_id=signer_id,
                timestamp=datetime.utcnow(),
            )
        except ImportError:
            raise RuntimeError("cryptography package required for RSA signing")

    def verify(
        self,
        data: bytes,
        signature_info: SignatureInfo,
        public_key: bytes | None = None,
    ) -> VerificationResult:
        """Verify RSA signature."""
        if public_key is None:
            return VerificationResult(
                is_valid=False,
                errors=["RSA verification requires a public key"],
            )

        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding, rsa

            # Load public key
            key = serialization.load_pem_public_key(public_key)
            if not isinstance(key, rsa.RSAPublicKey):
                return VerificationResult(
                    is_valid=False,
                    errors=["Not an RSA public key"],
                )

            # Verify
            signature = base64.b64decode(signature_info.signature)
            key.verify(
                signature,
                data,
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
            return VerificationResult(
                is_valid=True,
                trust_level=TrustLevel.VERIFIED,
                signer_id=signature_info.signer_id,
                algorithm=self.algorithm,
            )
        except ImportError:
            return VerificationResult(
                is_valid=False,
                errors=["cryptography package required for RSA verification"],
            )
        except Exception as e:
            return VerificationResult(
                is_valid=False,
                errors=[f"RSA verification failed: {str(e)}"],
            )


class Ed25519SigningService(SigningService):
    """Ed25519-based signing service (recommended)."""

    @property
    def algorithm(self) -> SignatureAlgorithm:
        """Get the signing algorithm."""
        return SignatureAlgorithm.ED25519

    def sign(
        self,
        data: bytes,
        private_key: bytes,
        signer_id: str,
    ) -> SignatureInfo:
        """Sign data using Ed25519."""
        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric import ed25519

            # Load private key
            key = serialization.load_pem_private_key(private_key, password=None)
            if not isinstance(key, ed25519.Ed25519PrivateKey):
                raise ValueError("Not an Ed25519 private key")

            # Sign
            signature = key.sign(data)
            return SignatureInfo(
                algorithm=self.algorithm,
                signature=base64.b64encode(signature).decode(),
                signer_id=signer_id,
                timestamp=datetime.utcnow(),
            )
        except ImportError:
            raise RuntimeError("cryptography package required for Ed25519 signing")

    def verify(
        self,
        data: bytes,
        signature_info: SignatureInfo,
        public_key: bytes | None = None,
    ) -> VerificationResult:
        """Verify Ed25519 signature."""
        if public_key is None:
            return VerificationResult(
                is_valid=False,
                errors=["Ed25519 verification requires a public key"],
            )

        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric import ed25519

            # Load public key
            key = serialization.load_pem_public_key(public_key)
            if not isinstance(key, ed25519.Ed25519PublicKey):
                return VerificationResult(
                    is_valid=False,
                    errors=["Not an Ed25519 public key"],
                )

            # Verify
            signature = base64.b64decode(signature_info.signature)
            key.verify(signature, data)
            return VerificationResult(
                is_valid=True,
                trust_level=TrustLevel.VERIFIED,
                signer_id=signature_info.signer_id,
                algorithm=self.algorithm,
            )
        except ImportError:
            return VerificationResult(
                is_valid=False,
                errors=["cryptography package required for Ed25519 verification"],
            )
        except Exception as e:
            return VerificationResult(
                is_valid=False,
                errors=[f"Ed25519 verification failed: {str(e)}"],
            )


class SigningServiceImpl:
    """Factory for creating signing services."""

    _services: dict[SignatureAlgorithm, type[SigningService]] = {
        SignatureAlgorithm.HMAC_SHA256: HMACSigningService,
        SignatureAlgorithm.HMAC_SHA512: HMACSigningService,
        SignatureAlgorithm.RSA_SHA256: RSASigningService,
        SignatureAlgorithm.ED25519: Ed25519SigningService,
    }

    def __init__(self, algorithm: SignatureAlgorithm = SignatureAlgorithm.HMAC_SHA256) -> None:
        """Initialize signing service.

        Args:
            algorithm: Signature algorithm to use.
        """
        self.algorithm = algorithm
        if algorithm == SignatureAlgorithm.HMAC_SHA512:
            self._service = HMACSigningService(use_sha512=True)
        elif algorithm in self._services:
            self._service = self._services[algorithm]()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

    def sign(
        self,
        data: bytes,
        private_key: bytes,
        signer_id: str,
    ) -> SignatureInfo:
        """Sign data."""
        return self._service.sign(data, private_key, signer_id)

    def verify(
        self,
        data: bytes,
        signature_info: SignatureInfo,
        public_key: bytes | None = None,
    ) -> VerificationResult:
        """Verify signature."""
        return self._service.verify(data, signature_info, public_key)


# =============================================================================
# Trust Store
# =============================================================================


@dataclass
class TrustedSigner:
    """Information about a trusted signer.

    Attributes:
        signer_id: Unique identifier for the signer.
        public_key: Public key (PEM format).
        trust_level: Trust level assigned.
        name: Display name.
        email: Contact email.
        organization: Organization name.
        added_at: When the signer was added.
        expires_at: When the trust expires.
        revoked: Whether the signer is revoked.
        metadata: Additional metadata.
    """

    signer_id: str
    public_key: bytes
    trust_level: TrustLevel
    name: str = ""
    email: str = ""
    organization: str = ""
    added_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
    revoked: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class TrustStore:
    """Abstract base class for trust stores."""

    @abstractmethod
    def add_signer(
        self,
        signer_id: str,
        public_key: bytes,
        trust_level: TrustLevel,
        **kwargs: Any,
    ) -> None:
        """Add a trusted signer."""
        ...

    @abstractmethod
    def remove_signer(self, signer_id: str) -> None:
        """Remove a signer."""
        ...

    @abstractmethod
    def get_trust_level(self, signer_id: str) -> TrustLevel | None:
        """Get trust level for a signer."""
        ...

    @abstractmethod
    def get_public_key(self, signer_id: str) -> bytes | None:
        """Get public key for a signer."""
        ...

    @abstractmethod
    def is_trusted(self, signer_id: str) -> bool:
        """Check if signer is trusted."""
        ...

    @abstractmethod
    def list_signers(self) -> list[TrustedSigner]:
        """List all signers."""
        ...


class TrustStoreImpl(TrustStore):
    """In-memory trust store implementation."""

    def __init__(self) -> None:
        """Initialize the trust store."""
        self._signers: dict[str, TrustedSigner] = {}

    def add_signer(
        self,
        signer_id: str,
        public_key: bytes,
        trust_level: TrustLevel,
        **kwargs: Any,
    ) -> None:
        """Add a trusted signer."""
        self._signers[signer_id] = TrustedSigner(
            signer_id=signer_id,
            public_key=public_key,
            trust_level=trust_level,
            name=kwargs.get("name", ""),
            email=kwargs.get("email", ""),
            organization=kwargs.get("organization", ""),
            expires_at=kwargs.get("expires_at"),
            metadata=kwargs.get("metadata", {}),
        )
        logger.info(f"Added trusted signer: {signer_id} (level: {trust_level.value})")

    def remove_signer(self, signer_id: str) -> None:
        """Remove a signer."""
        if signer_id in self._signers:
            del self._signers[signer_id]
            logger.info(f"Removed signer: {signer_id}")

    def revoke_signer(self, signer_id: str) -> None:
        """Revoke a signer without removing."""
        if signer_id in self._signers:
            self._signers[signer_id].revoked = True
            logger.info(f"Revoked signer: {signer_id}")

    def get_signer(self, signer_id: str) -> TrustedSigner | None:
        """Get signer information."""
        return self._signers.get(signer_id)

    def get_trust_level(self, signer_id: str) -> TrustLevel | None:
        """Get trust level for a signer."""
        signer = self._signers.get(signer_id)
        if signer is None:
            return None
        if signer.revoked:
            return TrustLevel.UNVERIFIED
        if signer.expires_at and signer.expires_at < datetime.utcnow():
            return TrustLevel.UNVERIFIED
        return signer.trust_level

    def get_public_key(self, signer_id: str) -> bytes | None:
        """Get public key for a signer."""
        signer = self._signers.get(signer_id)
        if signer is None or signer.revoked:
            return None
        return signer.public_key

    def is_trusted(self, signer_id: str) -> bool:
        """Check if signer is trusted."""
        trust_level = self.get_trust_level(signer_id)
        return trust_level in (TrustLevel.TRUSTED, TrustLevel.VERIFIED)

    def list_signers(self) -> list[TrustedSigner]:
        """List all signers."""
        return list(self._signers.values())

    def set_signer_trust(self, signer_id: str, trust_level: TrustLevel) -> None:
        """Update trust level for a signer."""
        if signer_id in self._signers:
            self._signers[signer_id].trust_level = trust_level
            logger.info(f"Updated trust level for {signer_id}: {trust_level.value}")


# =============================================================================
# Verification Chain (Chain of Responsibility)
# =============================================================================


class VerificationHandler(ABC):
    """Abstract handler in the verification chain."""

    def __init__(self) -> None:
        """Initialize the handler."""
        self._next: VerificationHandler | None = None

    def set_next(self, handler: "VerificationHandler") -> "VerificationHandler":
        """Set the next handler in the chain.

        Args:
            handler: Next handler.

        Returns:
            The next handler (for chaining).
        """
        self._next = handler
        return handler

    @abstractmethod
    def handle(
        self,
        data: bytes,
        signatures: list[SignatureInfo],
        context: dict[str, Any],
    ) -> VerificationResult | None:
        """Handle verification.

        Args:
            data: Data to verify.
            signatures: Signatures to verify.
            context: Verification context.

        Returns:
            VerificationResult if handled, None to pass to next.
        """
        ...

    def _pass_to_next(
        self,
        data: bytes,
        signatures: list[SignatureInfo],
        context: dict[str, Any],
    ) -> VerificationResult | None:
        """Pass to next handler if available."""
        if self._next:
            return self._next.handle(data, signatures, context)
        return None


class SignatureCountHandler(VerificationHandler):
    """Verify minimum signature count."""

    def __init__(self, min_signatures: int = 1) -> None:
        """Initialize handler.

        Args:
            min_signatures: Minimum required signatures.
        """
        super().__init__()
        self.min_signatures = min_signatures

    def handle(
        self,
        data: bytes,
        signatures: list[SignatureInfo],
        context: dict[str, Any],
    ) -> VerificationResult | None:
        """Check signature count."""
        if len(signatures) < self.min_signatures:
            return VerificationResult(
                is_valid=False,
                trust_level=TrustLevel.UNVERIFIED,
                errors=[
                    f"Insufficient signatures: {len(signatures)} < {self.min_signatures}"
                ],
            )
        return self._pass_to_next(data, signatures, context)


class SignerTrustHandler(VerificationHandler):
    """Verify signer trust levels."""

    def __init__(self, trust_store: TrustStore) -> None:
        """Initialize handler.

        Args:
            trust_store: Trust store to use.
        """
        super().__init__()
        self.trust_store = trust_store

    def handle(
        self,
        data: bytes,
        signatures: list[SignatureInfo],
        context: dict[str, Any],
    ) -> VerificationResult | None:
        """Check signer trust."""
        warnings = []
        for sig in signatures:
            trust_level = self.trust_store.get_trust_level(sig.signer_id)
            if trust_level is None:
                warnings.append(f"Unknown signer: {sig.signer_id}")
            elif trust_level == TrustLevel.UNVERIFIED:
                warnings.append(f"Untrusted signer: {sig.signer_id}")

        context["signer_warnings"] = warnings
        return self._pass_to_next(data, signatures, context)


class CryptographicVerificationHandler(VerificationHandler):
    """Perform cryptographic signature verification."""

    def __init__(self, trust_store: TrustStore) -> None:
        """Initialize handler.

        Args:
            trust_store: Trust store for public keys.
        """
        super().__init__()
        self.trust_store = trust_store

    def handle(
        self,
        data: bytes,
        signatures: list[SignatureInfo],
        context: dict[str, Any],
    ) -> VerificationResult | None:
        """Verify signatures cryptographically."""
        valid_signatures = 0
        verified_signers = []
        errors = []
        warnings = context.get("signer_warnings", [])

        for sig in signatures:
            public_key = self.trust_store.get_public_key(sig.signer_id)
            if public_key is None:
                warnings.append(f"No public key for signer: {sig.signer_id}")
                continue

            try:
                service = SigningServiceImpl(sig.algorithm)
                result = service.verify(data, sig, public_key)
                if result.is_valid:
                    valid_signatures += 1
                    verified_signers.append(sig.signer_id)
                else:
                    errors.extend(result.errors)
            except Exception as e:
                errors.append(f"Verification error for {sig.signer_id}: {str(e)}")

        # Determine final trust level
        if valid_signatures > 0:
            # Check trust levels of verified signers
            max_trust = TrustLevel.UNVERIFIED
            for signer_id in verified_signers:
                trust = self.trust_store.get_trust_level(signer_id)
                if trust == TrustLevel.TRUSTED:
                    max_trust = TrustLevel.TRUSTED
                    break
                elif trust == TrustLevel.VERIFIED and max_trust != TrustLevel.TRUSTED:
                    max_trust = TrustLevel.VERIFIED

            return VerificationResult(
                is_valid=True,
                trust_level=max_trust,
                signer_id=verified_signers[0] if verified_signers else None,
                warnings=warnings,
                metadata={"valid_signatures": valid_signatures},
            )
        else:
            return VerificationResult(
                is_valid=False,
                trust_level=TrustLevel.UNVERIFIED,
                errors=errors or ["No valid signatures"],
                warnings=warnings,
            )


class VerificationChain:
    """Verification chain that processes handlers in sequence."""

    def __init__(self, first_handler: VerificationHandler | None = None) -> None:
        """Initialize the chain.

        Args:
            first_handler: First handler in the chain.
        """
        self._first = first_handler

    def verify(
        self,
        data: bytes,
        signatures: list[SignatureInfo],
        context: dict[str, Any] | None = None,
    ) -> VerificationResult:
        """Verify signatures using the chain.

        Args:
            data: Data to verify.
            signatures: Signatures to verify.
            context: Optional context dictionary.

        Returns:
            VerificationResult from the chain.
        """
        if not signatures:
            return VerificationResult(
                is_valid=False,
                trust_level=TrustLevel.UNVERIFIED,
                errors=["No signatures provided"],
            )

        ctx = context or {}
        if self._first:
            result = self._first.handle(data, signatures, ctx)
            if result:
                return result

        # If chain didn't produce a result, return unverified
        return VerificationResult(
            is_valid=False,
            trust_level=TrustLevel.UNVERIFIED,
            errors=["Verification chain did not produce a result"],
        )


class VerificationChainBuilder:
    """Builder for verification chains."""

    def __init__(self) -> None:
        """Initialize the builder."""
        self._handlers: list[VerificationHandler] = []

    def with_signature_count(self, min_signatures: int = 1) -> "VerificationChainBuilder":
        """Add signature count verification.

        Args:
            min_signatures: Minimum required signatures.

        Returns:
            Self for chaining.
        """
        self._handlers.append(SignatureCountHandler(min_signatures))
        return self

    def with_signer_trust(self, trust_store: TrustStore) -> "VerificationChainBuilder":
        """Add signer trust verification.

        Args:
            trust_store: Trust store to use.

        Returns:
            Self for chaining.
        """
        self._handlers.append(SignerTrustHandler(trust_store))
        return self

    def with_cryptographic_verification(
        self, trust_store: TrustStore
    ) -> "VerificationChainBuilder":
        """Add cryptographic signature verification.

        Args:
            trust_store: Trust store for public keys.

        Returns:
            Self for chaining.
        """
        self._handlers.append(CryptographicVerificationHandler(trust_store))
        return self

    def with_custom_handler(
        self, handler: VerificationHandler
    ) -> "VerificationChainBuilder":
        """Add a custom handler.

        Args:
            handler: Custom handler.

        Returns:
            Self for chaining.
        """
        self._handlers.append(handler)
        return self

    def build(self) -> VerificationChain:
        """Build the verification chain.

        Returns:
            Configured VerificationChain.
        """
        if not self._handlers:
            return VerificationChain()

        # Chain handlers together
        for i in range(len(self._handlers) - 1):
            self._handlers[i].set_next(self._handlers[i + 1])

        return VerificationChain(self._handlers[0])


def create_verification_chain(
    trust_store: TrustStore | None = None,
    min_signatures: int = 1,
) -> VerificationChain:
    """Create a standard verification chain.

    Args:
        trust_store: Trust store for verification.
        min_signatures: Minimum required signatures.

    Returns:
        Configured VerificationChain.
    """
    store = trust_store or TrustStoreImpl()
    return (
        VerificationChainBuilder()
        .with_signature_count(min_signatures)
        .with_signer_trust(store)
        .with_cryptographic_verification(store)
        .build()
    )
