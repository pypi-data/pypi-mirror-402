"""
Boundary Profile Explainer
Module for explaining organizational profiles in human language.

No inference. Only profile field-based descriptions allowed.
"""

from typing import List, Dict, Any

from models.schemas import (
    JudgmentBoundaryProfile,
    OrganizationProfile,
    BoundaryStrength,
    DomainTag,
    ReasonSlot
)


class BoundaryProfileExplainer:
    """
    Boundary Profile → Human language explanation conversion.

    v0.3 core: Generate explanations that organizations can take responsibility for.
    """

    def __init__(self):
        # Boundary strength description mappings
        self.strength_descriptions = {
            BoundaryStrength.VERY_CONSERVATIVE: {
                "en": "very conservative and stops or holds most executions"
            },
            BoundaryStrength.CONSERVATIVE: {
                "en": "conservative and requires clear evidence to proceed"
            },
            BoundaryStrength.BALANCED: {
                "en": "balanced and judges flexibly based on context"
            },
            BoundaryStrength.PERMISSIVE: {
                "en": "permissive and allows most requests"
            },
            BoundaryStrength.VERY_PERMISSIVE: {
                "en": "very permissive and allows nearly all requests"
            }
        }

        # ReasonSlot description mappings
        self.reason_descriptions = {
            ReasonSlot.EVIDENCE_MISSING: {
                "en": "missing evidence"
            },
            ReasonSlot.UNVERIFIED_ASSERTION: {
                "en": "unverified assertion"
            },
            ReasonSlot.PRIOR_ASSUMPTION: {
                "en": "prior assumption"
            },
            ReasonSlot.HALLUCINATION_RISK: {
                "en": "hallucination risk"
            },
            ReasonSlot.INSUFFICIENT_CONTEXT: {
                "en": "insufficient context"
            },
            ReasonSlot.RISK_DETECTED: {
                "en": "risk detected"
            },
            ReasonSlot.OUT_OF_SCOPE: {
                "en": "out of scope"
            },
            ReasonSlot.CONFLICTED_SLOT: {
                "en": "conflicted slot"
            }
        }

    def explain_profile(
        self,
        profile: JudgmentBoundaryProfile,
        language: str = "en",
        format: str = "paragraph"
    ) -> str:
        """
        Explain profile in human language.

        Args:
            profile: JudgmentBoundaryProfile
            language: "en" (ko removed for public release)
            format: "paragraph" | "bullet" | "formal"

        Returns:
            Explanation text
        """
        if format == "paragraph":
            return self._explain_paragraph(profile, language)
        elif format == "bullet":
            return self._explain_bullet(profile, language)
        elif format == "formal":
            return self._explain_formal(profile)
        else:
            return self._explain_paragraph(profile, language)

    def _explain_paragraph(
        self,
        profile: JudgmentBoundaryProfile,
        language: str
    ) -> str:
        """
        Paragraph format explanation.

        Args:
            profile: JudgmentBoundaryProfile
            language: Language (only 'en' supported)

        Returns:
            Explanation text
        """
        parts = []

        # 1. Organization domain and character
        intro = f"This organization is "
        intro += self.strength_descriptions[profile.boundary_strength]["en"]
        intro += f" in the '{profile.domain_tag.value}' domain."
        parts.append(intro)

        # 2. Decision distribution
        dist = f"\n\nDecision distribution: STOP {profile.stop_bias:.1%}, HOLD {profile.hold_bias:.1%}, ALLOW {profile.allow_bias:.1%}"
        parts.append(dist)

        # 3. Frequent reasons
        if profile.frequent_reasons:
            reasons_str = "Primary judgment reasons are "
            reason_names = [
                self.reason_descriptions.get(r, {"en": r.value})["en"]
                for r in profile.frequent_reasons
            ]
            reasons_str += ", ".join(reason_names)
            reasons_str += "."
            parts.append("\n" + reasons_str)

        # 4. High-risk patterns
        if profile.high_risk_patterns:
            patterns_str = f"\nDetected high-risk patterns: {', '.join(profile.high_risk_patterns)}"
            parts.append(patterns_str)

        # 5. Confidence and stability
        meta = f"\n\nThis profile is based on {profile.sample_count} judgments, "
        meta += f"with confidence level {profile.confidence} "
        meta += f"and temporal stability of {profile.temporal_stability:.1%}."
        parts.append(meta)

        return "".join(parts)

    def _explain_bullet(
        self,
        profile: JudgmentBoundaryProfile,
        language: str
    ) -> str:
        """
        Bullet point format explanation.

        Args:
            profile: JudgmentBoundaryProfile
            language: Language (only 'en' supported)

        Returns:
            Explanation text
        """
        lines = []

        lines.append(f"Domain: {profile.domain_tag.value}")
        lines.append(f"Boundary Strength: {profile.boundary_strength.value}")
        lines.append(f"Dominant Decision: {profile.dominant_decision.value}")
        lines.append(f"STOP Bias: {profile.stop_bias:.1%}")
        lines.append(f"HOLD Bias: {profile.hold_bias:.1%}")
        lines.append(f"ALLOW Bias: {profile.allow_bias:.1%}")
        lines.append(f"Sample Count: {profile.sample_count}")
        lines.append(f"Confidence: {profile.confidence}")
        lines.append(f"Temporal Stability: {profile.temporal_stability:.1%}")

        return "\n".join([f"• {line}" for line in lines])

    def _explain_formal(
        self,
        profile: JudgmentBoundaryProfile
    ) -> str:
        """
        Formal document format explanation (for audit/regulatory submission).

        Args:
            profile: JudgmentBoundaryProfile

        Returns:
            Formal explanation text
        """
        text = f"Organizational Judgment Boundary Profile Report\n"
        text += f"=" * 50 + "\n\n"
        text += f"Profile ID: {profile.profile_id}\n"
        text += f"Domain: {profile.domain_tag.value}\n"
        text += f"Organization ID: {profile.organization_id}\n\n"

        text += f"Boundary Character:\n"
        text += f"  - Strength: {profile.boundary_strength.value}\n"
        text += f"  - Dominant Decision: {profile.dominant_decision.value}\n\n"

        text += f"Decision Statistics:\n"
        text += f"  - STOP: {profile.stop_bias:.2%}\n"
        text += f"  - HOLD: {profile.hold_bias:.2%}\n"
        text += f"  - ALLOW: {profile.allow_bias:.2%}\n"
        text += f"  - INDET: {profile.indet_bias:.2%}\n\n"

        text += f"Analysis Basis:\n"
        text += f"  - Sample Count: {profile.sample_count}\n"
        text += f"  - Confidence: {profile.confidence}\n"
        text += f"  - Temporal Stability: {profile.temporal_stability:.2%}\n"
        text += f"  - First Seen: {profile.first_seen.isoformat()}\n"
        text += f"  - Last Updated: {profile.last_updated.isoformat()}\n\n"

        if profile.high_risk_patterns:
            text += f"Detected Risk Patterns:\n"
            for pattern in profile.high_risk_patterns:
                text += f"  - {pattern}\n"

        return text

    def compare_profiles(
        self,
        profile_a: JudgmentBoundaryProfile,
        profile_b: JudgmentBoundaryProfile
    ) -> str:
        """
        Compare and explain two profiles.

        Args:
            profile_a: First profile
            profile_b: Second profile

        Returns:
            Comparison explanation
        """
        if profile_a.domain_tag != profile_b.domain_tag:
            return "Comparison error: Profiles from different domains."

        lines = []
        lines.append(f"Profile comparison for domain '{profile_a.domain_tag.value}':")
        lines.append("")

        if profile_a.boundary_strength != profile_b.boundary_strength:
            lines.append(f"Boundary strength: A({profile_a.boundary_strength.value}) vs B({profile_b.boundary_strength.value})")

        stop_diff = profile_a.stop_bias - profile_b.stop_bias
        if abs(stop_diff) > 0.1:
            if stop_diff > 0:
                lines.append(f"A is {stop_diff:.1%}p more conservative than B (higher STOP ratio)")
            else:
                lines.append(f"B is {-stop_diff:.1%}p more conservative than A (higher STOP ratio)")

        return "\n".join(lines)
