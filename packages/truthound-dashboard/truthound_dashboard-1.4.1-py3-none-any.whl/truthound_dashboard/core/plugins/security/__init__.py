"""Enterprise Plugin Security Module.

This module provides enterprise-grade security features:
- Multiple signature algorithms (HMAC, RSA, Ed25519)
- Trust store with certificate management
- Verification chain (Chain of Responsibility pattern)
- Security policy presets
"""

from __future__ import annotations

from .protocols import (
    IsolationLevel,
    TrustLevel,
    SecurityPolicy,
    ResourceLimits,
    SignatureAlgorithm,
    SignatureInfo,
    VerificationResult,
)
from .policies import (
    SecurityPolicyPresets,
    create_policy,
    get_preset,
    list_presets,
)
from .signing import (
    SigningService,
    SigningServiceImpl,
    TrustStore,
    TrustStoreImpl,
    VerificationChain,
    VerificationChainBuilder,
    create_verification_chain,
)
from .analyzer import (
    SecurityAnalyzer,
    SecurityReport,
    CodeAnalysisResult,
)

__all__ = [
    # Protocols
    "IsolationLevel",
    "TrustLevel",
    "SecurityPolicy",
    "ResourceLimits",
    "SignatureAlgorithm",
    "SignatureInfo",
    "VerificationResult",
    # Policies
    "SecurityPolicyPresets",
    "create_policy",
    "get_preset",
    "list_presets",
    # Signing
    "SigningService",
    "SigningServiceImpl",
    "TrustStore",
    "TrustStoreImpl",
    "VerificationChain",
    "VerificationChainBuilder",
    "create_verification_chain",
    # Analysis
    "SecurityAnalyzer",
    "SecurityReport",
    "CodeAnalysisResult",
]
