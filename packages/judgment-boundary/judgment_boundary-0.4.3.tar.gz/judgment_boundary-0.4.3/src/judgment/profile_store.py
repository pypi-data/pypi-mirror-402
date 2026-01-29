"""
Organization Profile Store
Storage for saving and querying organization's judgment character (Profile).

Must be independently explainable, separated from judgment logs.
"""

from typing import Optional, Dict
from pathlib import Path
import json
from datetime import datetime

from models.schemas import (
    OrganizationProfile,
    JudgmentBoundaryProfile,
    DomainTag
)


class OrganizationProfileStore:
    """
    Organization profile storage.

    Stores "this organization does not allow automation at this point"
    as structure, not logs.
    """

    def __init__(self, storage_path: str = "./organization_profile.json"):
        """
        Args:
            storage_path: Profile storage path (JSON format)
        """
        self.storage_path = Path(storage_path)
        self._ensure_storage()

    def _ensure_storage(self):
        """Check/create storage file"""
        if not self.storage_path.exists():
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            # Create empty profile
            empty_profile = OrganizationProfile()
            self.save_profile(empty_profile)

    def save_profile(self, profile: OrganizationProfile) -> bool:
        """
        Save organization profile.

        Args:
            profile: OrganizationProfile

        Returns:
            Success status
        """
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json_data = profile.model_dump_json(indent=2)
                f.write(json_data)
            return True
        except Exception as e:
            print(f"Error saving organization profile: {e}")
            return False

    def load_profile(
        self,
        organization_id: str = "default"
    ) -> Optional[OrganizationProfile]:
        """
        Load organization profile.

        Args:
            organization_id: Organization ID

        Returns:
            OrganizationProfile or None
        """
        try:
            if not self.storage_path.exists():
                return None

            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check organization_id
            if data.get("organization_id") != organization_id:
                return None

            return OrganizationProfile(**data)
        except Exception as e:
            print(f"Error loading organization profile: {e}")
            return None

    def get_domain_profile(
        self,
        domain_tag: DomainTag,
        organization_id: str = "default"
    ) -> Optional[JudgmentBoundaryProfile]:
        """
        Query Boundary Profile for specific domain.

        Args:
            domain_tag: Domain
            organization_id: Organization ID

        Returns:
            JudgmentBoundaryProfile or None
        """
        profile = self.load_profile(organization_id)
        if not profile:
            return None

        domain_key = domain_tag.value
        if domain_key not in profile.domain_profiles:
            return None

        return profile.domain_profiles[domain_key]

    def update_domain_profile(
        self,
        domain_profile: JudgmentBoundaryProfile,
        organization_id: str = "default"
    ) -> bool:
        """
        Update profile for specific domain.

        Args:
            domain_profile: JudgmentBoundaryProfile
            organization_id: Organization ID

        Returns:
            Success status
        """
        # Load existing profile
        org_profile = self.load_profile(organization_id)
        if not org_profile:
            # Create new
            org_profile = OrganizationProfile(organization_id=organization_id)

        # Update domain profile
        domain_key = domain_profile.domain_tag.value
        org_profile.domain_profiles[domain_key] = domain_profile

        # Update total judgment count
        org_profile.total_judgments = sum(
            p.sample_count for p in org_profile.domain_profiles.values()
        )

        # Last update time
        org_profile.last_updated = datetime.utcnow()

        # Save
        return self.save_profile(org_profile)

    def get_profile_summary(
        self,
        organization_id: str = "default"
    ) -> Dict:
        """
        Query organization profile summary.

        Args:
            organization_id: Organization ID

        Returns:
            Summary information
        """
        profile = self.load_profile(organization_id)
        if not profile:
            return {
                "organization_id": organization_id,
                "exists": False,
                "total_judgments": 0,
                "domains": []
            }

        return {
            "organization_id": profile.organization_id,
            "exists": True,
            "total_judgments": profile.total_judgments,
            "overall_boundary_strength": profile.overall_boundary_strength.value,
            "domains": [
                {
                    "domain": domain,
                    "boundary_strength": p.boundary_strength.value,
                    "dominant_decision": p.dominant_decision.value,
                    "sample_count": p.sample_count,
                    "confidence": p.confidence
                }
                for domain, p in profile.domain_profiles.items()
            ],
            "created_at": profile.created_at.isoformat(),
            "last_updated": profile.last_updated.isoformat()
        }

    def explain_profile(
        self,
        domain_tag: DomainTag,
        organization_id: str = "default"
    ) -> str:
        """
        Explain profile in human-readable language.

        Clearly express "when this organization stops".

        Args:
            domain_tag: Domain
            organization_id: Organization ID

        Returns:
            Explanation text
        """
        domain_profile = self.get_domain_profile(domain_tag, organization_id)

        if not domain_profile:
            return f"No organizational profile found for domain '{domain_tag.value}'."

        # Character description
        strength_desc = {
            "VERY_CONSERVATIVE": "very conservative and stops or holds execution in most cases",
            "CONSERVATIVE": "conservative and does not proceed without clear evidence",
            "BALANCED": "balanced and judges flexibly based on context",
            "PERMISSIVE": "permissive and allows most requests",
            "VERY_PERMISSIVE": "very permissive and allows nearly all requests"
        }

        desc = f"This organization is "
        desc += strength_desc.get(
            domain_profile.boundary_strength.value,
            "showing judgment tendency"
        )
        desc += f" in the '{domain_tag.value}' domain.\n\n"

        # Judgment distribution
        desc += f"Decision distribution:\n"
        desc += f"  - STOP: {domain_profile.stop_bias:.1%}\n"
        desc += f"  - HOLD: {domain_profile.hold_bias:.1%}\n"
        desc += f"  - ALLOW: {domain_profile.allow_bias:.1%}\n\n"

        # Frequent reasons
        if domain_profile.frequent_reasons:
            desc += f"Primary judgment reasons:\n"
            for reason in domain_profile.frequent_reasons:
                desc += f"  - {reason.value}\n"
            desc += "\n"

        # High-risk patterns
        if domain_profile.high_risk_patterns:
            desc += f"Detected high-risk patterns:\n"
            for pattern in domain_profile.high_risk_patterns:
                desc += f"  - {pattern}\n"
            desc += "\n"

        # Confidence and samples
        desc += f"Profile confidence: {domain_profile.confidence} "
        desc += f"(based on {domain_profile.sample_count} judgments)\n"
        desc += f"Temporal stability: {domain_profile.temporal_stability:.1%}"

        return desc
