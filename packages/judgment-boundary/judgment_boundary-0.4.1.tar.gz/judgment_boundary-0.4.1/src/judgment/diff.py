"""
Boundary Diff Engine
조직 프로필 간 차이 분석.
"""

from typing import Dict, Any, List

from models.schemas import (
    JudgmentBoundaryProfile,
    OrganizationProfile,
    BoundaryStrength
)


class BoundaryDiffEngine:
    """
    Boundary Profile 비교 엔진.
    """

    def compare_profiles(
        self,
        profile_a: JudgmentBoundaryProfile,
        profile_b: JudgmentBoundaryProfile
    ) -> Dict[str, Any]:
        """
        두 프로필 비교.

        Args:
            profile_a: 첫 번째 프로필
            profile_b: 두 번째 프로필

        Returns:
            비교 결과
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

        # 주요 차이점 판별
        diff["summary"] = self._generate_summary(diff, profile_a, profile_b)

        return diff

    def _compare_strength(
        self,
        strength_a: BoundaryStrength,
        strength_b: BoundaryStrength
    ) -> Dict[str, Any]:
        """
        경계 강도 비교.

        Args:
            strength_a: 첫 번째 강도
            strength_b: 두 번째 강도

        Returns:
            비교 결과
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
        비교 요약 생성.

        Args:
            diff: 비교 결과
            profile_a: 첫 번째 프로필
            profile_b: 두 번째 프로필

        Returns:
            요약 문장
        """
        summary_parts = []

        # 강도 비교
        strength_comparison = diff["strength_diff"]["comparison"]
        summary_parts.append(strength_comparison)

        # STOP 비율 차이
        stop_diff = diff["bias_diff"]["stop"]
        if abs(stop_diff) > 0.1:
            if stop_diff > 0:
                summary_parts.append(f"A shows {stop_diff:.1%}p higher STOP ratio")
            else:
                summary_parts.append(f"B shows {-stop_diff:.1%}p higher STOP ratio")

        return ". ".join(summary_parts) + "."
