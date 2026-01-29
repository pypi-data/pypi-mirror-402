"""
PUBLIC SDK MODULE — TYPE CONTRACT

This module defines the governance contract types.
These types are part of the public API and are subject to semantic versioning.

Changing the meaning or structure of these types requires a MAJOR version bump.
"""

# Re-export contract types from internal implementation
# This provides a stable public API surface

# CONTRACT TYPE
# This type is part of the public governance contract.
# Changing its meaning or fields requires a MAJOR version bump.
from models.schemas import JudgmentDecision as Decision

# CONTRACT TYPE
# This type is part of the public governance contract.
# Changing its meaning or fields requires a MAJOR version bump.
from models.schemas import ReasonSlot as BoundaryReason

# CONTRACT TYPE
# This type is part of the public governance contract.
# Changing its meaning or fields requires a MAJOR version bump.
from models.schemas import OrganizationProfile as OrganizationalProfile

# CONTRACT TYPE
# This type is part of the public governance contract.
# Changing its meaning or fields requires a MAJOR version bump.
from models.schemas import BoundaryDeclarationEvent as DeclarationEvent

# CONTRACT TYPE
# This type is part of the public governance contract.
# Changing its meaning or fields requires a MAJOR version bump.
from models.schemas import HumanOverrideCapsule as HumanOverride

# CONTRACT TYPE
# This type is part of the public governance contract.
# Changing its meaning or fields requires a MAJOR version bump.
from models.schemas import BoundaryAttestation as Attestation

# CONTRACT TYPE
# This type is part of the public governance contract.
# Changing its meaning or fields requires a MAJOR version bump.
from models.schemas import DomainTag

# CONTRACT TYPE
# This type is part of the public governance contract.
# Changing its meaning or fields requires a MAJOR version bump.
from models.schemas import BoundaryStrength

# CONTRACT TYPE
# This type is part of the public governance contract.
# Changing its meaning or fields requires a MAJOR version bump.
from models.schemas import DeclarationType

# CONTRACT TYPE
# This type is part of the public governance contract.
# Changing its meaning or fields requires a MAJOR version bump.
from models.schemas import OverrideScope


# Public API surface
__all__ = [
    # Core contract types
    'Decision',
    'BoundaryReason',
    'OrganizationalProfile',
    'DeclarationEvent',
    'HumanOverride',
    'Attestation',

    # Supporting enums
    'DomainTag',
    'BoundaryStrength',
    'DeclarationType',
    'OverrideScope',
]


# Contract guarantee statement
__contract_version__ = "0.4.0"
__contract_stability__ = "STABLE"
__contract_note__ = """
These types constitute a governance contract, not a decision API.
Semantic changes to these types will trigger a MAJOR version bump.
Internal implementation details may change without affecting this contract.
"""
