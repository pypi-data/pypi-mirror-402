"""
Judgment Memory Aggregator
Module that condenses individual judgment logs into organizational judgment character.

No statistics/ML usage. Only:
- Frequency
- Repetition
- Temporal Stability
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
    Extracts organizational judgment character by reading Judgment Memory.

    v0.2 core: Individual judgments → Organization memory elevation
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
            min_samples: Minimum number of samples needed for profile generation
            recent_window: Recent N entries for temporal stability measurement
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
        Generate Boundary Profile for specific domain.

        Args:
            domain_tag: Domain
            organization_id: Organization ID

        Returns:
            JudgmentBoundaryProfile or None (when insufficient samples)
        """
        # 1. Query domain data
        entries = self.memory_store.query_by_domain(domain_tag, limit=None)

        if len(entries) < self.min_samples:
            return None

        # 2. Calculate frequency
        decision_counts = Counter()
        reason_counts = Counter()

        for entry in entries:
            decision_counts[entry.decision.value] += 1
            for reason in entry.reason_slots:
                reason_counts[reason.value] += 1

        total = len(entries)

        # 3. Calculate bias
        stop_bias = decision_counts.get(JudgmentDecision.STOP.value, 0) / total
        hold_bias = decision_counts.get(JudgmentDecision.HOLD.value, 0) / total
        allow_bias = decision_counts.get(JudgmentDecision.ALLOW.value, 0) / total
        indet_bias = decision_counts.get(JudgmentDecision.INDET.value, 0) / total

        # 4. Dominant Decision
        dominant_decision = JudgmentDecision(decision_counts.most_common(1)[0][0])

        # 5. Calculate Boundary Strength
        boundary_strength = self._calculate_boundary_strength(
            stop_bias, hold_bias, allow_bias
        )

        # 6. Frequent reasons (top 3)
        frequent_reasons = [
            ReasonSlot(reason) for reason, _ in reason_counts.most_common(3)
        ]

        # 7. Detect high-risk patterns (repetition-based)
        high_risk_patterns = self._detect_high_risk_patterns(entries)

        # 8. Calculate temporal stability
        temporal_stability = self._calculate_temporal_stability(entries)

        # 9. Determine confidence
        confidence = self._determine_confidence(total, temporal_stability)

        # 10. Generate Profile ID
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
        Generate profile for entire organization.

        Args:
            organization_id: Organization ID

        Returns:
            OrganizationProfile
        """
        domain_profiles = {}
        total_judgments = 0

        # Generate profile for each domain
        for domain in DomainTag:
            profile = self.generate_boundary_profile(domain, organization_id)
            if profile:
                domain_profiles[domain.value] = profile
                total_judgments += profile.sample_count

        # Calculate overall boundary strength (average)
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

            # Convert to nearest strength
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
        Calculate boundary strength.

        Args:
            stop_bias: STOP ratio
            hold_bias: HOLD ratio
            allow_bias: ALLOW ratio

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
        Detect high-risk patterns based on repetition.

        Args:
            entries: Judgment entries

        Returns:
            List of patterns
        """
        patterns = []

        # Pattern 1: frequent evidence_missing + STOP
        evidence_missing_stop = sum(
            1 for e in entries
            if e.decision == JudgmentDecision.STOP
            and ReasonSlot.EVIDENCE_MISSING in e.reason_slots
        )

        if evidence_missing_stop / len(entries) > 0.3:
            patterns.append("evidence_missing + assertive_tone")

        # Pattern 2: prior_assumption frequently rejected
        prior_assumption_count = sum(
            1 for e in entries
            if ReasonSlot.PRIOR_ASSUMPTION in e.reason_slots
            and e.decision in [JudgmentDecision.STOP, JudgmentDecision.HOLD]
        )

        if prior_assumption_count / len(entries) > 0.2:
            patterns.append("prior_assumption_rejection")

        # Pattern 3: consecutive STOP (repetition)
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
        Calculate temporal stability.

        Similarity between recent N judgments distribution vs overall distribution.

        Args:
            entries: Judgment entries

        Returns:
            Stability (0.0 ~ 1.0)
        """
        if len(entries) < self.recent_window:
            return 1.0  # Assume stable when insufficient samples

        # Overall distribution
        all_decisions = Counter(e.decision.value for e in entries)
        all_total = len(entries)
        all_dist = {k: v / all_total for k, v in all_decisions.items()}

        # Recent N distribution
        recent_entries = entries[-self.recent_window:]
        recent_decisions = Counter(e.decision.value for e in recent_entries)
        recent_total = len(recent_entries)
        recent_dist = {k: v / recent_total for k, v in recent_decisions.items()}

        # Use simple difference inverse instead of KL divergence (no statistics)
        all_keys = set(all_dist.keys()) | set(recent_dist.keys())

        total_diff = sum(
            abs(all_dist.get(k, 0) - recent_dist.get(k, 0))
            for k in all_keys
        )

        # 1.0 - (difference / 2) => 1.0 if no difference, 0.0 if completely different
        stability = 1.0 - (total_diff / 2.0)

        return max(0.0, min(1.0, stability))

    def _determine_confidence(
        self,
        sample_count: int,
        temporal_stability: float
    ) -> str:
        """
        Determine profile confidence.

        Args:
            sample_count: Number of samples
            temporal_stability: Temporal stability

        Returns:
            "HIGH" | "MEDIUM" | "LOW"
        """
        if sample_count >= 50 and temporal_stability >= 0.8:
            return "HIGH"
        elif sample_count >= 20 and temporal_stability >= 0.6:
            return "MEDIUM"
        else:
            return "LOW"
