"""
Boundary Profile Explainer
조직 프로필을 사람 언어로 설명하는 모듈.

추론 금지. 오직 프로필 필드 기반 서술만 허용.
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
    Boundary Profile → 사람 언어 설명 변환.

    v0.3 핵심: 조직이 책임질 수 있게 설명 생성.
    """

    def __init__(self):
        # 경계 강도 설명 매핑
        self.strength_descriptions = {
            BoundaryStrength.VERY_CONSERVATIVE: {
                "ko": "매우 보수적이며 대부분의 경우 실행을 중단하거나 보류합니다",
                "en": "very conservative and stops or holds most executions"
            },
            BoundaryStrength.CONSERVATIVE: {
                "ko": "보수적이며 확실한 증거 없이는 진행하지 않습니다",
                "en": "conservative and requires clear evidence to proceed"
            },
            BoundaryStrength.BALANCED: {
                "ko": "균형적이며 상황에 따라 유연하게 판단합니다",
                "en": "balanced and judges flexibly based on context"
            },
            BoundaryStrength.PERMISSIVE: {
                "ko": "허용적이며 대부분의 요청을 진행합니다",
                "en": "permissive and allows most requests"
            },
            BoundaryStrength.VERY_PERMISSIVE: {
                "ko": "매우 허용적이며 거의 모든 요청을 허용합니다",
                "en": "very permissive and allows nearly all requests"
            }
        }

        # ReasonSlot 설명 매핑
        self.reason_descriptions = {
            ReasonSlot.EVIDENCE_MISSING: {
                "ko": "증거 부족",
                "en": "missing evidence"
            },
            ReasonSlot.UNVERIFIED_ASSERTION: {
                "ko": "검증되지 않은 단정",
                "en": "unverified assertion"
            },
            ReasonSlot.PRIOR_ASSUMPTION: {
                "ko": "사전 가정",
                "en": "prior assumption"
            },
            ReasonSlot.HALLUCINATION_RISK: {
                "ko": "환각 위험",
                "en": "hallucination risk"
            },
            ReasonSlot.INSUFFICIENT_CONTEXT: {
                "ko": "컨텍스트 부족",
                "en": "insufficient context"
            },
            ReasonSlot.RISK_DETECTED: {
                "ko": "위험 감지",
                "en": "risk detected"
            },
            ReasonSlot.OUT_OF_SCOPE: {
                "ko": "범위 벗어남",
                "en": "out of scope"
            },
            ReasonSlot.CONFLICTED_SLOT: {
                "ko": "충돌 발생",
                "en": "conflicted slot"
            }
        }

    def explain_profile(
        self,
        profile: JudgmentBoundaryProfile,
        language: str = "ko",
        format: str = "paragraph"
    ) -> str:
        """
        프로필을 사람 언어로 설명.

        Args:
            profile: JudgmentBoundaryProfile
            language: "ko" | "en"
            format: "paragraph" | "bullet" | "formal"

        Returns:
            설명 텍스트
        """
        if format == "paragraph":
            return self._explain_paragraph(profile, language)
        elif format == "bullet":
            return self._explain_bullet(profile, language)
        elif format == "formal":
            return self._explain_formal(profile, language)
        else:
            return self._explain_paragraph(profile, language)

    def _explain_paragraph(
        self,
        profile: JudgmentBoundaryProfile,
        language: str
    ) -> str:
        """
        문단 형식 설명.

        Args:
            profile: JudgmentBoundaryProfile
            language: 언어

        Returns:
            설명 텍스트
        """
        parts = []

        # 1. 조직 도메인 및 성격
        if language == "ko":
            intro = f"이 조직은 '{profile.domain_tag.value}' 도메인에서 "
            intro += self.strength_descriptions[profile.boundary_strength]["ko"]
            intro += "."
        else:
            intro = f"This organization is "
            intro += self.strength_descriptions[profile.boundary_strength]["en"]
            intro += f" in the '{profile.domain_tag.value}' domain."

        parts.append(intro)

        # 2. 판단 분포
        if language == "ko":
            dist = f"\n\n판단 분포: STOP {profile.stop_bias:.1%}, HOLD {profile.hold_bias:.1%}, ALLOW {profile.allow_bias:.1%}"
        else:
            dist = f"\n\nDecision distribution: STOP {profile.stop_bias:.1%}, HOLD {profile.hold_bias:.1%}, ALLOW {profile.allow_bias:.1%}"
        parts.append(dist)

        # 3. 빈번한 이유
        if profile.frequent_reasons:
            if language == "ko":
                reasons_str = "주요 판단 이유는 "
                reason_names = [
                    self.reason_descriptions.get(r, {"ko": r.value})["ko"]
                    for r in profile.frequent_reasons
                ]
                reasons_str += ", ".join(reason_names)
                reasons_str += "입니다."
            else:
                reasons_str = "Primary judgment reasons are "
                reason_names = [
                    self.reason_descriptions.get(r, {"en": r.value})["en"]
                    for r in profile.frequent_reasons
                ]
                reasons_str += ", ".join(reason_names)
                reasons_str += "."

            parts.append("\n" + reasons_str)

        # 4. 고위험 패턴
        if profile.high_risk_patterns:
            if language == "ko":
                patterns_str = f"\n감지된 고위험 패턴: {', '.join(profile.high_risk_patterns)}"
            else:
                patterns_str = f"\nDetected high-risk patterns: {', '.join(profile.high_risk_patterns)}"
            parts.append(patterns_str)

        # 5. 신뢰도 및 안정성
        if language == "ko":
            meta = f"\n\n이 프로필은 {profile.sample_count}개의 판단을 기반으로 하며, "
            meta += f"신뢰도는 {profile.confidence}, "
            meta += f"시간 안정성은 {profile.temporal_stability:.1%}입니다."
        else:
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
        불릿 포인트 형식 설명.

        Args:
            profile: JudgmentBoundaryProfile
            language: 언어

        Returns:
            설명 텍스트
        """
        lines = []

        if language == "ko":
            lines.append(f"도메인: {profile.domain_tag.value}")
            lines.append(f"경계 강도: {profile.boundary_strength.value}")
            lines.append(f"지배적 판단: {profile.dominant_decision.value}")
            lines.append(f"STOP 비율: {profile.stop_bias:.1%}")
            lines.append(f"HOLD 비율: {profile.hold_bias:.1%}")
            lines.append(f"ALLOW 비율: {profile.allow_bias:.1%}")
            lines.append(f"샘플 수: {profile.sample_count}")
            lines.append(f"신뢰도: {profile.confidence}")
            lines.append(f"시간 안정성: {profile.temporal_stability:.1%}")
        else:
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
        profile: JudgmentBoundaryProfile,
        language: str
    ) -> str:
        """
        공식 문서 형식 설명 (감사/규제 제출용).

        Args:
            profile: JudgmentBoundaryProfile
            language: 언어

        Returns:
            공식 설명 텍스트
        """
        if language == "ko":
            text = f"조직 판단 경계 프로필 보고서\n"
            text += f"=" * 50 + "\n\n"
            text += f"프로필 ID: {profile.profile_id}\n"
            text += f"도메인: {profile.domain_tag.value}\n"
            text += f"조직 ID: {profile.organization_id}\n\n"

            text += f"경계 성격:\n"
            text += f"  - 강도: {profile.boundary_strength.value}\n"
            text += f"  - 지배적 판단: {profile.dominant_decision.value}\n\n"

            text += f"판단 통계:\n"
            text += f"  - STOP: {profile.stop_bias:.2%}\n"
            text += f"  - HOLD: {profile.hold_bias:.2%}\n"
            text += f"  - ALLOW: {profile.allow_bias:.2%}\n"
            text += f"  - INDET: {profile.indet_bias:.2%}\n\n"

            text += f"분석 기준:\n"
            text += f"  - 샘플 수: {profile.sample_count}\n"
            text += f"  - 신뢰도: {profile.confidence}\n"
            text += f"  - 시간 안정성: {profile.temporal_stability:.2%}\n"
            text += f"  - 최초 관측: {profile.first_seen.isoformat()}\n"
            text += f"  - 최종 업데이트: {profile.last_updated.isoformat()}\n\n"

            if profile.high_risk_patterns:
                text += f"감지된 위험 패턴:\n"
                for pattern in profile.high_risk_patterns:
                    text += f"  - {pattern}\n"

        else:
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
        profile_b: JudgmentBoundaryProfile,
        language: str = "ko"
    ) -> str:
        """
        두 프로필 비교 설명.

        Args:
            profile_a: 첫 번째 프로필
            profile_b: 두 번째 프로필
            language: 언어

        Returns:
            비교 설명
        """
        if profile_a.domain_tag != profile_b.domain_tag:
            if language == "ko":
                return "비교 오류: 다른 도메인의 프로필입니다."
            else:
                return "Comparison error: Profiles from different domains."

        lines = []

        if language == "ko":
            lines.append(f"도메인 '{profile_a.domain_tag.value}' 프로필 비교:")
            lines.append("")

            # 경계 강도 비교
            if profile_a.boundary_strength != profile_b.boundary_strength:
                lines.append(f"경계 강도: A({profile_a.boundary_strength.value}) vs B({profile_b.boundary_strength.value})")

            # STOP 비율 비교
            stop_diff = profile_a.stop_bias - profile_b.stop_bias
            if abs(stop_diff) > 0.1:
                if stop_diff > 0:
                    lines.append(f"A가 B보다 {stop_diff:.1%}p 더 보수적 (STOP 비율 높음)")
                else:
                    lines.append(f"B가 A보다 {-stop_diff:.1%}p 더 보수적 (STOP 비율 높음)")

        else:
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
