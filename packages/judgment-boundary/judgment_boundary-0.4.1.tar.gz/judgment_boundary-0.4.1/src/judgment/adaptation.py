"""
Online Adaptation Rule Engine
과거 판단 패턴을 읽어 다음 요청의 행동을 바꾸는 엔진.

학습은 규칙 공간에서 발생한다 (파라미터 공간 ❌).
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from models.schemas import (
    RuntimeContext,
    JudgmentDecision,
    ReasonSlot,
    DomainTag,
    AdaptationRule
)
from judgment.memory import JudgmentMemoryStore
from utils.hashing import generate_prompt_signature


@dataclass
class AdaptationDecision:
    """적응 결정"""
    should_override: bool = False
    override_decision: Optional[JudgmentDecision] = None
    override_reason: Optional[str] = None
    context_modifications: Dict[str, Any] = None
    applied_rules: List[str] = None

    def __post_init__(self):
        if self.context_modifications is None:
            self.context_modifications = {}
        if self.applied_rules is None:
            self.applied_rules = []


class OnlineAdaptationEngine:
    """
    Online Adaptation Rule Engine.

    과거 패턴을 분석하여 다음 요청의 행동을 변경한다.
    """

    def __init__(
        self,
        memory_store: JudgmentMemoryStore,
        stop_threshold: int = 3,
        domain_stop_ratio_threshold: float = 0.5
    ):
        """
        Args:
            memory_store: Judgment Memory Store
            stop_threshold: STOP 반복 임계값 (N회 이상 STOP → HOLD로 변경)
            domain_stop_ratio_threshold: 도메인 STOP 비율 임계값
        """
        self.memory_store = memory_store
        self.stop_threshold = stop_threshold
        self.domain_stop_ratio_threshold = domain_stop_ratio_threshold

        # 내장 규칙들
        self.builtin_rules = [
            AdaptationRule(
                rule_id="repeated_stop_to_hold",
                condition=f"STOP count >= {stop_threshold}",
                action="Convert STOP to HOLD with clarification",
                priority=10,
                active=True
            ),
            AdaptationRule(
                rule_id="high_domain_stop_ratio",
                condition=f"Domain STOP ratio >= {domain_stop_ratio_threshold}",
                action="Increase caution: disable assumption_mode",
                priority=5,
                active=True
            ),
            AdaptationRule(
                rule_id="evidence_missing_pattern",
                condition="Repeated EVIDENCE_MISSING in domain",
                action="Suggest RAG integration",
                priority=3,
                active=True
            )
        ]

    def analyze_and_adapt(
        self,
        context: RuntimeContext
    ) -> AdaptationDecision:
        """
        컨텍스트를 분석하고 적응 결정 생성.

        Args:
            context: 실행 컨텍스트

        Returns:
            AdaptationDecision
        """
        decision = AdaptationDecision()

        # 프롬프트 서명 생성
        prompt_sig = generate_prompt_signature(context.prompt)

        # 규칙 1: 반복된 STOP → HOLD로 변경
        stop_count = self.memory_store.count_stop_decisions(prompt_sig)
        if stop_count >= self.stop_threshold:
            decision.should_override = True
            decision.override_decision = JudgmentDecision.HOLD
            decision.override_reason = (
                f"This prompt has resulted in STOP {stop_count} times. "
                f"Converting to HOLD to ask for clarification."
            )
            decision.applied_rules.append("repeated_stop_to_hold")

        # 규칙 2: 도메인의 높은 STOP 비율 → assumption_mode 비활성화
        domain_stop_ratio = self.memory_store.get_domain_stop_ratio(context.domain_tag)
        if domain_stop_ratio >= self.domain_stop_ratio_threshold:
            if context.assumption_mode:
                decision.context_modifications["assumption_mode"] = False
                decision.context_modifications["assumption_mode_reason"] = (
                    f"Domain '{context.domain_tag.value}' has high STOP ratio "
                    f"({domain_stop_ratio:.2%}). Disabling assumption mode for safety."
                )
                decision.applied_rules.append("high_domain_stop_ratio")

        # 규칙 3: Evidence Missing 패턴 감지
        domain_stats = self.memory_store.get_decision_stats(domain_tag=context.domain_tag)
        evidence_missing_count = domain_stats.get("reason_slot_counts", {}).get(
            ReasonSlot.EVIDENCE_MISSING.value, 0
        )
        total_count = domain_stats.get("total_count", 0)

        if total_count > 0 and (evidence_missing_count / total_count) > 0.5:
            # 50% 이상이 Evidence Missing → RAG 통합 제안
            decision.context_modifications["suggest_rag"] = True
            decision.context_modifications["rag_suggestion_reason"] = (
                f"Domain '{context.domain_tag.value}' has frequent EVIDENCE_MISSING "
                f"({evidence_missing_count}/{total_count}). Consider integrating RAG."
            )
            decision.applied_rules.append("evidence_missing_pattern")

        return decision

    def apply_adaptation(
        self,
        context: RuntimeContext,
        adaptation: AdaptationDecision
    ) -> RuntimeContext:
        """
        적응 결정을 컨텍스트에 적용.

        Args:
            context: 원래 컨텍스트
            adaptation: 적응 결정

        Returns:
            수정된 컨텍스트
        """
        # Context 수정 적용
        for key, value in adaptation.context_modifications.items():
            if hasattr(context, key):
                setattr(context, key, value)
            else:
                # user_context에 추가
                context.user_context[key] = value

        return context

    def get_active_rules(self) -> List[AdaptationRule]:
        """
        활성화된 규칙 목록 조회.

        Returns:
            활성 규칙들
        """
        return [rule for rule in self.builtin_rules if rule.active]

    def add_custom_rule(self, rule: AdaptationRule):
        """
        사용자 정의 규칙 추가.

        Args:
            rule: 추가할 규칙
        """
        self.builtin_rules.append(rule)

    def disable_rule(self, rule_id: str):
        """
        규칙 비활성화.

        Args:
            rule_id: 규칙 ID
        """
        for rule in self.builtin_rules:
            if rule.rule_id == rule_id:
                rule.active = False
                break

    def get_adaptation_summary(
        self,
        context: RuntimeContext
    ) -> Dict[str, Any]:
        """
        적응 상태 요약 조회.

        Args:
            context: 실행 컨텍스트

        Returns:
            적응 요약 정보
        """
        prompt_sig = generate_prompt_signature(context.prompt)
        domain_stats = self.memory_store.get_decision_stats(domain_tag=context.domain_tag)
        prompt_stats = self.memory_store.get_decision_stats(prompt_signature=prompt_sig)

        return {
            "prompt_signature": prompt_sig,
            "domain_tag": context.domain_tag.value,
            "domain_stats": domain_stats,
            "prompt_history": prompt_stats,
            "stop_count_for_prompt": self.memory_store.count_stop_decisions(prompt_sig),
            "domain_stop_ratio": self.memory_store.get_domain_stop_ratio(context.domain_tag),
            "active_rules": [rule.rule_id for rule in self.get_active_rules()]
        }
