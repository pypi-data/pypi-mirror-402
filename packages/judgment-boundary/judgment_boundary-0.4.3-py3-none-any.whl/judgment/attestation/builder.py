"""
Boundary Attestation Builder
Create organization character at specific point in time as immutable attestation object.

Attestation ≠ Report
- Report: Explanatory document (modifiable)
- Attestation: Time-sealed proof (immutable, reproducible)
"""

from typing import Dict, List, Optional
from datetime import datetime
import hashlib
import json

from models.schemas import (
    BoundaryAttestation,
    OrganizationProfile,
    JudgmentBoundaryProfile,
    BoundaryDeclarationEvent
)


class BoundaryAttestationBuilder:
    """
    Organization character attestation builder.

    v0.4 core: Internal completed character → Externally presentable attestation
    """

    def __init__(self, runtime_version: str = "v0.4"):
        """
        Args:
            runtime_version: Runtime version
        """
        self.runtime_version = runtime_version

    def build_attestation(
        self,
        organization_id: str,
        org_profile: OrganizationProfile,
        active_declarations: List[BoundaryDeclarationEvent],
        effective_at: Optional[datetime] = None
    ) -> BoundaryAttestation:
        """
        Create attestation.

        Args:
            organization_id: Organization ID
            org_profile: Organization profile
            active_declarations: Active declarations
            effective_at: Effective time (current if None)

        Returns:
            BoundaryAttestation
        """
        if effective_at is None:
            effective_at = datetime.utcnow()

        # 1. Generate boundary summary
        boundary_summary = self._generate_boundary_summary(
            org_profile, active_declarations
        )

        # 2. Generate hashes (ensure integrity)
        profile_hash = self._hash_profile(org_profile)
        declarations_hash = self._hash_declarations(active_declarations)

        # 3. Generate Attestation ID
        attestation_id = self._generate_attestation_id(
            organization_id, effective_at
        )

        # 4. Domain list
        domains_included = list(org_profile.domain_profiles.keys())

        return BoundaryAttestation(
            attestation_id=attestation_id,
            organization_id=organization_id,
            effective_at=effective_at,
            boundary_summary=boundary_summary,
            profile_hash=profile_hash,
            declarations_hash=declarations_hash,
            runtime_version=self.runtime_version,
            generation_method="deterministic",
            domains_included=domains_included,
            declarations_count=len(active_declarations),
            immutable=True
        )

    def _generate_boundary_summary(
        self,
        org_profile: OrganizationProfile,
        active_declarations: List[BoundaryDeclarationEvent]
    ) -> Dict[str, str]:
        """
        Generate boundary summary by domain.

        Args:
            org_profile: Organization profile
            active_declarations: Active declarations

        Returns:
            Summary by domain
        """
        summary = {}

        # Declarations take priority (v0.3 priority rule)
        for decl in active_declarations:
            domain = decl.domain_tag.value
            summary[domain] = decl.declaration.value

        # For domains without declarations, get from profile
        for domain, profile in org_profile.domain_profiles.items():
            if domain not in summary:
                # Use boundary strength as summary
                summary[domain] = profile.boundary_strength.value

        return summary

    def _hash_profile(self, org_profile: OrganizationProfile) -> str:
        """
        Generate profile hash (ensure integrity).

        Args:
            org_profile: Organization profile

        Returns:
            SHA-256 hash
        """
        # Sorted JSON for reproducibility
        profile_dict = org_profile.model_dump()
        json_str = json.dumps(profile_dict, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()

    def _hash_declarations(
        self,
        declarations: List[BoundaryDeclarationEvent]
    ) -> str:
        """
        Generate declaration events hash.

        Args:
            declarations: Declaration events

        Returns:
            SHA-256 hash
        """
        if not declarations:
            return hashlib.sha256(b"").hexdigest()

        # Sort for reproducibility
        decls_sorted = sorted(
            [d.model_dump() for d in declarations],
            key=lambda x: x['event_id']
        )
        json_str = json.dumps(decls_sorted, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()

    def _generate_attestation_id(
        self,
        organization_id: str,
        effective_at: datetime
    ) -> str:
        """
        Generate Attestation ID.

        Args:
            organization_id: Organization ID
            effective_at: Effective time

        Returns:
            Attestation ID (e.g., ATT-2026-01-ABCD1234)
        """
        # Format: ATT-YYYY-MM-{hash}
        year_month = effective_at.strftime("%Y-%m")

        # Hash of organization ID + time
        content = f"{organization_id}:{effective_at.isoformat()}"
        hash_suffix = hashlib.sha256(content.encode('utf-8')).hexdigest()[:8].upper()

        return f"ATT-{year_month}-{hash_suffix}"
