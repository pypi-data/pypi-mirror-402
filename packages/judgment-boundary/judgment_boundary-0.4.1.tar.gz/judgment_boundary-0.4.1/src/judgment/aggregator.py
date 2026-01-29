"""
Judgment Memory Aggregator
개별 판단 로그를 조직의 판단 성격으로 응축하는 모듈.

통계/ML 사용 금지. 오직:
- 빈도 (Frequency)
- 반복성 (Repetition)
- 시간 안정성 (Temporal Stability)
"""

from typing import List, Dict, Optional, Tuple
from collections import Counter, defaultdict
from datetime import datetime

from models.schemas import (
    JudgmentMemoryEntry,
    JudgmentBoundaryProfile,
    BoundaryStrength,
    JudgmentDecision,
    ReasonSlot,
    DomainTag,
    OrganizationProfile
)
from judgment.memory import JudgmentMemoryStore


class JudgmentMemoryAggregator:
    """
    Judgment Memory를 읽어 조직의 판단 성격을 추출.

    v0.2 핵심: 개별 판단 → 조직 기억 위상 승격
    """

    def __init__(
        self,
        memory_store: JudgmentMemoryStore,
        min_samples: int = 10,
        recent_window: int = 20
    ):
        """
        Args:
            memory_store: Judgment Memory Store
            min_samples: 프로필 생성에 필요한 최소 샘플 수
            recent_window: 시간 안정성 측정을 위한 최근 N개
        """
        self.memory_store = memory_store
        self.min_samples = min_samples
        self.recent_window = recent_window

    def generate_boundary_profile(
        self,
        domain_tag: DomainTag,
        organization_id: str = "default"
    ) -> Optional[JudgmentBoundaryProfile]:
        """
        특정 도메인의 Boundary Profile 생성.

        Args:
            domain_tag: 도메인
            organization_id: 조직 ID

        Returns:
            JudgmentBoundaryProfile or None (샘플 부족 시)
        """
        # 1. 도메인 데이터 조회
        entries = self.memory_store.query_by_domain(domain_tag, limit=None)

        if len(entries) < self.min_samples:
            return None

        # 2. 빈도 계산
        decision_counts = Counter()
        reason_counts = Counter()

        for entry in entries:
            decision_counts[entry.decision.value] += 1
            for reason in entry.reason_slots:
                reason_counts[reason.value] += 1

        total = len(entries)

        # 3. Bias 계산
        stop_bias = decision_counts.get(JudgmentDecision.STOP.value, 0) / total
        hold_bias = decision_counts.get(JudgmentDecision.HOLD.value, 0) / total
        allow_bias = decision_counts.get(JudgmentDecision.ALLOW.value, 0) / total
        indet_bias = decision_counts.get(JudgmentDecision.INDET.value, 0) / total

        # 4. Dominant Decision
        dominant_decision = JudgmentDecision(decision_counts.most_common(1)[0][0])

        # 5. Boundary Strength 계산
        boundary_strength = self._calculate_boundary_strength(
            stop_bias, hold_bias, allow_bias
        )

        # 6. 빈번한 이유들 (상위 3개)
        frequent_reasons = [
            ReasonSlot(reason) for reason, _ in reason_counts.most_common(3)
        ]

        # 7. 고위험 패턴 감지 (반복성 기반)
        high_risk_patterns = self._detect_high_risk_patterns(entries)

        # 8. 시간 안정성 계산
        temporal_stability = self._calculate_temporal_stability(entries)

        # 9. 신뢰도 결정
        confidence = self._determine_confidence(total, temporal_stability)

        # 10. Profile ID 생성
        profile_id = f"ORG-{organization_id}-{domain_tag.value.upper()}"

        return JudgmentBoundaryProfile(
            profile_id=profile_id,
            organization_id=organization_id,
            domain_tag=domain_tag,
            stop_bias=stop_bias,
            hold_bias=hold_bias,
            allow_bias=allow_bias,
            indet_bias=indet_bias,
            boundary_strength=boundary_strength,
            dominant_decision=dominant_decision,
            frequent_reasons=frequent_reasons,
            high_risk_patterns=high_risk_patterns,
            sample_count=total,
            confidence=confidence,
            first_seen=entries[0].timestamp if entries else datetime.utcnow(),
            last_updated=entries[-1].timestamp if entries else datetime.utcnow(),
            temporal_stability=temporal_stability
        )

    def generate_organization_profile(
        self,
        organization_id: str = "default"
    ) -> OrganizationProfile:
        """
        조직 전체의 프로필 생성.

        Args:
            organization_id: 조직 ID

        Returns:
            OrganizationProfile
        """
        domain_profiles = {}
        total_judgments = 0

        # 각 도메인별 프로필 생성
        for domain in DomainTag:
            profile = self.generate_boundary_profile(domain, organization_id)
            if profile:
                domain_profiles[domain.value] = profile
                total_judgments += profile.sample_count

        # 전체 경계 강도 계산 (평균)
        if domain_profiles:
            strength_values = {
                BoundaryStrength.VERY_CONSERVATIVE: 0,
                BoundaryStrength.CONSERVATIVE: 1,
                BoundaryStrength.BALANCED: 2,
                BoundaryStrength.PERMISSIVE: 3,
                BoundaryStrength.VERY_PERMISSIVE: 4
            }

            avg_strength_value = sum(
                strength_values[p.boundary_strength]
                for p in domain_profiles.values()
            ) / len(domain_profiles)

            # 가장 가까운 strength로 변환
            strength_list = [
                (abs(avg_strength_value - v), s)
                for s, v in strength_values.items()
            ]
            overall_strength = min(strength_list)[1]
        else:
            overall_strength = BoundaryStrength.BALANCED

        return OrganizationProfile(
            organization_id=organization_id,
            domain_profiles=domain_profiles,
            overall_boundary_strength=overall_strength,
            total_judgments=total_judgments,
            last_updated=datetime.utcnow()
        )

    def _calculate_boundary_strength(
        self,
        stop_bias: float,
        hold_bias: float,
        allow_bias: float
    ) -> BoundaryStrength:
        """
        경계 강도 계산.

        Args:
            stop_bias: STOP 비율
            hold_bias: HOLD 비율
            allow_bias: ALLOW 비율

        Returns:
            BoundaryStrength
        """
        conservative_ratio = stop_bias + hold_bias

        if conservative_ratio >= 0.8:
            return BoundaryStrength.VERY_CONSERVATIVE
        elif conservative_ratio >= 0.6:
            return BoundaryStrength.CONSERVATIVE
        elif conservative_ratio >= 0.4:
            return BoundaryStrength.BALANCED
        elif conservative_ratio >= 0.2:
            return BoundaryStrength.PERMISSIVE
        else:
            return BoundaryStrength.VERY_PERMISSIVE

    def _detect_high_risk_patterns(
        self,
        entries: List[JudgmentMemoryEntry]
    ) -> List[str]:
        """
        반복성 기반 고위험 패턴 감지.

        Args:
            entries: 판단 항목들

        Returns:
            패턴 목록
        """
        patterns = []

        # 패턴 1: evidence_missing + STOP이 빈번
        evidence_missing_stop = sum(
            1 for e in entries
            if e.decision == JudgmentDecision.STOP
            and ReasonSlot.EVIDENCE_MISSING in e.reason_slots
        )

        if evidence_missing_stop / len(entries) > 0.3:
            patterns.append("evidence_missing + assertive_tone")

        # 패턴 2: prior_assumption이 자주 거부
        prior_assumption_count = sum(
            1 for e in entries
            if ReasonSlot.PRIOR_ASSUMPTION in e.reason_slots
            and e.decision in [JudgmentDecision.STOP, JudgmentDecision.HOLD]
        )

        if prior_assumption_count / len(entries) > 0.2:
            patterns.append("prior_assumption_rejection")

        # 패턴 3: 연속 STOP (반복성)
        consecutive_stops = 0
        max_consecutive = 0

        for entry in entries:
            if entry.decision == JudgmentDecision.STOP:
                consecutive_stops += 1
                max_consecutive = max(max_consecutive, consecutive_stops)
            else:
                consecutive_stops = 0

        if max_consecutive >= 5:
            patterns.append("consecutive_stop_pattern")

        return patterns

    def _calculate_temporal_stability(
        self,
        entries: List[JudgmentMemoryEntry]
    ) -> float:
        """
        시간 안정성 계산.

        최근 N개의 판단 분포 vs 전체 분포의 유사도.

        Args:
            entries: 판단 항목들

        Returns:
            안정성 (0.0 ~ 1.0)
        """
        if len(entries) < self.recent_window:
            return 1.0  # 샘플 부족 시 안정적으로 가정

        # 전체 분포
        all_decisions = Counter(e.decision.value for e in entries)
        all_total = len(entries)
        all_dist = {k: v / all_total for k, v in all_decisions.items()}

        # 최근 N개 분포
        recent_entries = entries[-self.recent_window:]
        recent_decisions = Counter(e.decision.value for e in recent_entries)
        recent_total = len(recent_entries)
        recent_dist = {k: v / recent_total for k, v in recent_decisions.items()}

        # KL divergence 대신 단순 차이의 역수 사용 (통계 금지)
        all_keys = set(all_dist.keys()) | set(recent_dist.keys())

        total_diff = sum(
            abs(all_dist.get(k, 0) - recent_dist.get(k, 0))
            for k in all_keys
        )

        # 1.0 - (차이 / 2) => 차이 없으면 1.0, 완전 다르면 0.0
        stability = 1.0 - (total_diff / 2.0)

        return max(0.0, min(1.0, stability))

    def _determine_confidence(
        self,
        sample_count: int,
        temporal_stability: float
    ) -> str:
        """
        프로필 신뢰도 결정.

        Args:
            sample_count: 샘플 개수
            temporal_stability: 시간 안정성

        Returns:
            "HIGH" | "MEDIUM" | "LOW"
        """
        if sample_count >= 50 and temporal_stability >= 0.8:
            return "HIGH"
        elif sample_count >= 20 and temporal_stability >= 0.6:
            return "MEDIUM"
        else:
            return "LOW"
