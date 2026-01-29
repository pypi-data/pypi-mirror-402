"""
PUBLIC SDK MODULE — STABLE CONTRACT

This module aggregates judgment patterns into organizational profiles.
It does not learn.
It does not predict.
It does not optimize.

This module uses frequency counting and repetition detection ONLY.
No machine learning. No statistical models. Deterministic aggregation only.
"""

from typing import Optional
from pathlib import Path
import json

from judgment_boundary.types import (
    OrganizationalProfile,
    DomainTag,
    BoundaryStrength,
)


def load_profile(profile_path: str) -> OrganizationalProfile:
    """
    Load organizational profile from storage.

    Args:
        profile_path: Path to profile JSON file

    Returns:
        OrganizationalProfile

    Raises:
        FileNotFoundError: If profile does not exist
        ValueError: If profile format is invalid
    """
    path = Path(profile_path)

    if not path.exists():
        raise FileNotFoundError(f"Profile not found: {profile_path}")

    with open(path, 'r') as f:
        profile_data = json.load(f)

    return OrganizationalProfile(**profile_data)


def save_profile(profile: OrganizationalProfile, profile_path: str) -> None:
    """
    Save organizational profile to storage.

    Args:
        profile: OrganizationalProfile to save
        profile_path: Path to profile JSON file
    """
    path = Path(profile_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w') as f:
        json.dump(profile.model_dump(), f, indent=2, default=str)


def get_domain_strength(
    profile: OrganizationalProfile,
    domain: DomainTag
) -> Optional[BoundaryStrength]:
    """
    Get boundary strength for a specific domain.

    Args:
        profile: OrganizationalProfile
        domain: Domain to query

    Returns:
        BoundaryStrength or None if domain not in profile
    """
    domain_key = domain.value.lower()
    domain_profile = profile.domain_profiles.get(domain_key)

    if not domain_profile:
        return None

    return domain_profile.boundary_strength


def is_domain_conservative(
    profile: OrganizationalProfile,
    domain: DomainTag
) -> bool:
    """
    Check if domain has conservative boundary (STOP-dominant).

    Conservative domains prefer human review over automation.

    Args:
        profile: OrganizationalProfile
        domain: Domain to check

    Returns:
        True if VERY_CONSERVATIVE or CONSERVATIVE, False otherwise
    """
    strength = get_domain_strength(profile, domain)

    if not strength:
        return False

    return strength in [
        BoundaryStrength.VERY_CONSERVATIVE,
        BoundaryStrength.CONSERVATIVE
    ]


# Public API surface
__all__ = [
    'load_profile',
    'save_profile',
    'get_domain_strength',
    'is_domain_conservative',
]
