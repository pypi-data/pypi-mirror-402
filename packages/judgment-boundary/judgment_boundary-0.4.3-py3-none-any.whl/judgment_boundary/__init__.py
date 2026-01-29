"""
Judgment Boundary — Public SDK

Judgment Boundary is an organizational infrastructure that prevents
irresponsible automation and proves that prevention.

This SDK is a governance contract, not a decision engine.

Public API Modules:
- runtime: Judgment boundary enforcement (v0.1)
- profile: Organizational character aggregation (v0.2)
- governance: Declarations and overrides (v0.3)
- attestation: Immutable proof generation (v0.4)
- types: Contract type definitions

Internal modules (_internal/*) are NOT part of the public API contract.
"""

__version__ = "0.4.3"
__contract_version__ = "0.4.3"
__contract_stability__ = "STABLE"

# This SDK does NOT:
# - Make decisions
# - Learn from data
# - Optimize behavior
# - Modify AI models

# This SDK DOES:
# - Enforce organizational boundaries
# - Record judgment traces
# - Aggregate patterns (frequency counting only, NO ML)
# - Generate verifiable attestations

# Public API - STABLE CONTRACT
from judgment_boundary.runtime import JudgmentRuntime
from judgment_boundary.profile import (
    load_profile,
    save_profile,
    get_domain_strength,
    is_domain_conservative,
)
from judgment_boundary.governance import (
    DeclarationStore,
    OverrideStore,
)
from judgment_boundary.attestation import (
    AttestationBuilder,
    EvidenceGenerator,
    ExternalExplainer,
    AttestationRegistry,
)
from judgment_boundary import types

__all__ = [
    # Core runtime
    'JudgmentRuntime',

    # Profile utilities
    'load_profile',
    'save_profile',
    'get_domain_strength',
    'is_domain_conservative',

    # Governance
    'DeclarationStore',
    'OverrideStore',

    # Attestation
    'AttestationBuilder',
    'EvidenceGenerator',
    'ExternalExplainer',
    'AttestationRegistry',

    # Types module
    'types',
]
