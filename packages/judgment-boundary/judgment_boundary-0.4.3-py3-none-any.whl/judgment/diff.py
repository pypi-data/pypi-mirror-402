"""
Boundary Diff Engine
Analysis of differences between organization profiles.
"""

from typing import Dict, Any, List

from models.schemas import (
    JudgmentBoundaryProfile,
    OrganizationProfile,
    BoundaryStrength
)


class BoundaryDiffEngine:
    """
    Boundary Profile comparison engine.
    """

    def compare_profiles(
        self,
        profile_a: JudgmentBoundaryProfile,
        profile_b: JudgmentBoundaryProfile
    ) -> Dict[str, Any]:
        """
        Compare two profiles.

        Args:
            profile_a: First profile
            profile_b: Second profile

        Returns:
            Comparison result
        """
        if profile_a.domain_tag != profile_b.domain_tag:
            return {
                "comparable": False,
                "reason": "Different domains"
            }

        diff = {
            "comparable": True,
            "domain": profile_a.domain_tag.value,
            "strength_diff": self._compare_strength(
                profile_a.boundary_strength,
                profile_b.boundary_strength
            ),
            "bias_diff": {
                "stop": profile_a.stop_bias - profile_b.stop_bias,
                "hold": profile_a.hold_bias - profile_b.hold_bias,
                "allow": profile_a.allow_bias - profile_b.allow_bias
            },
            "sample_count_diff": profile_a.sample_count - profile_b.sample_count,
            "temporal_stability_diff": profile_a.temporal_stability - profile_b.temporal_stability
        }

        # Identify key differences
        diff["summary"] = self._generate_summary(diff, profile_a, profile_b)

        return diff

    def _compare_strength(
        self,
        strength_a: BoundaryStrength,
        strength_b: BoundaryStrength
    ) -> Dict[str, Any]:
        """
        Compare boundary strength.

        Args:
            strength_a: First strength
            strength_b: Second strength

        Returns:
            Comparison result
        """
        strength_order = {
            BoundaryStrength.VERY_PERMISSIVE: 0,
            BoundaryStrength.PERMISSIVE: 1,
            BoundaryStrength.BALANCED: 2,
            BoundaryStrength.CONSERVATIVE: 3,
            BoundaryStrength.VERY_CONSERVATIVE: 4
        }

        order_a = strength_order[strength_a]
        order_b = strength_order[strength_b]

        if order_a > order_b:
            comparison = "A is more conservative"
        elif order_a < order_b:
            comparison = "B is more conservative"
        else:
            comparison = "Equal"

        return {
            "a": strength_a.value,
            "b": strength_b.value,
            "comparison": comparison,
            "order_diff": order_a - order_b
        }

    def _generate_summary(
        self,
        diff: Dict[str, Any],
        profile_a: JudgmentBoundaryProfile,
        profile_b: JudgmentBoundaryProfile
    ) -> str:
        """
        Generate comparison summary.

        Args:
            diff: Comparison result
            profile_a: First profile
            profile_b: Second profile

        Returns:
            Summary text
        """
        summary_parts = []

        # Strength comparison
        strength_comparison = diff["strength_diff"]["comparison"]
        summary_parts.append(strength_comparison)

        # STOP ratio difference
        stop_diff = diff["bias_diff"]["stop"]
        if abs(stop_diff) > 0.1:
            if stop_diff > 0:
                summary_parts.append(f"A shows {stop_diff:.1%}p higher STOP ratio")
            else:
                summary_parts.append(f"B shows {-stop_diff:.1%}p higher STOP ratio")

        return ". ".join(summary_parts) + "."
