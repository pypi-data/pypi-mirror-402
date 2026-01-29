"""
Judgment Decision Module
판단 경계를 결정하는 핵심 모듈 (STOP/HOLD/ALLOW/INDET)
"""

from typing import Optional, List
from datetime import datetime
import re

from models.schemas import (
    JudgmentDecision,
    JudgmentResult,
    ReasonSlot,
    RuntimeContext,
    NegativeProof
)
from utils.hashing import generate_trace_signature, generate_prompt_signature


class JudgmentDecisionModule:
    """
    판단 결정 모듈.

    규칙:
    1. Evidence 미존재 + 확정 서술 → STOP 또는 HOLD
    2. Prior/상식 추론은 assumption_mode=false일 경우 금지
    3. 항상 구조화된 이유(ReasonSlot) 반환
    """

    def __init__(self):
        # 확정 서술 패턴 (단정적 표현)
        self.assertive_patterns = [
            r'\b(is|are|was|were|will be|must be)\b',
            r'\b(definitely|certainly|obviously|clearly)\b',
            r'\b(always|never|all|none|every)\b',
            r'\b(확실히|분명히|명백히|반드시)\b',
            r'\b(이다|입니다|됩니다)\s*$',  # 한국어 단정
        ]

        # 추론/가정 패턴
        self.assumption_patterns = [
            r'\b(probably|likely|possibly|maybe|might|could|seems)\b',
            r'\b(I think|I believe|in my opinion|generally)\b',
            r'\b(아마|~것 같|~듯|추정|추론)\b',
        ]

    def decide(
        self,
        context: RuntimeContext,
        negative_proof: Optional[NegativeProof] = None
    ) -> JudgmentResult:
        """
        판단 결정 수행.

        Args:
            context: 실행 컨텍스트
            negative_proof: Negative Proof (외부에서 생성 가능)

        Returns:
            JudgmentResult
        """
        timestamp = datetime.utcnow().isoformat()

        # 1. 서명 생성
        prompt_sig = generate_prompt_signature(context.prompt)
        trace_sig = generate_trace_signature(
            context.prompt,
            context.model_output,
            timestamp
        )

        # 2. 증거 확인
        has_evidence = self._check_evidence(context)

        # 3. 확정 서술 감지
        is_assertive = self._is_assertive_output(context.model_output)

        # 4. 추론/가정 감지
        is_assumption = self._is_assumption_based(context.model_output)

        # 5. 판단 로직
        decision, reason_slots, confidence = self._make_judgment(
            has_evidence=has_evidence,
            is_assertive=is_assertive,
            is_assumption=is_assumption,
            assumption_mode=context.assumption_mode,
            context=context
        )

        # 6. 설명 생성
        explanation = self._generate_explanation(
            decision, reason_slots, has_evidence, is_assertive, is_assumption
        )

        return JudgmentResult(
            decision=decision,
            reason_slots=reason_slots,
            confidence=confidence,
            explanation=explanation,
            negative_proof=negative_proof,
            trace_signature=trace_sig
        )

    def _check_evidence(self, context: RuntimeContext) -> bool:
        """
        증거 존재 여부 확인.

        Args:
            context: 실행 컨텍스트

        Returns:
            True if evidence exists
        """
        # RAG 소스가 있으면 증거 있음
        if context.rag_sources and len(context.rag_sources) > 0:
            return True

        # 컨텍스트에 명시적 데이터가 있으면 증거 있음
        if context.user_context.get("has_data", False):
            return True

        # 기본적으로 증거 없음
        return False

    def _is_assertive_output(self, output: str) -> bool:
        """
        확정적/단정적 서술 감지.

        Args:
            output: 모델 출력

        Returns:
            True if assertive
        """
        for pattern in self.assertive_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                return True
        return False

    def _is_assumption_based(self, output: str) -> bool:
        """
        추론/가정 기반 출력 감지.

        Args:
            output: 모델 출력

        Returns:
            True if assumption-based
        """
        for pattern in self.assumption_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                return True
        return False

    def _make_judgment(
        self,
        has_evidence: bool,
        is_assertive: bool,
        is_assumption: bool,
        assumption_mode: bool,
        context: RuntimeContext
    ) -> tuple[JudgmentDecision, List[ReasonSlot], float]:
        """
        핵심 판단 로직.

        Returns:
            (decision, reason_slots, confidence)
        """
        reason_slots = []
        confidence = 1.0

        # 규칙 1: Evidence 미존재 + 확정 서술 → STOP
        if not has_evidence and is_assertive:
            reason_slots.append(ReasonSlot.EVIDENCE_MISSING)
            reason_slots.append(ReasonSlot.UNVERIFIED_ASSERTION)
            return JudgmentDecision.STOP, reason_slots, 0.9

        # 규칙 2: Evidence 미존재 + 추론 → assumption_mode 확인
        if not has_evidence and is_assumption:
            if not assumption_mode:
                # 가정 모드 꺼져있으면 HOLD (질문 유도)
                reason_slots.append(ReasonSlot.EVIDENCE_MISSING)
                reason_slots.append(ReasonSlot.PRIOR_ASSUMPTION)
                return JudgmentDecision.HOLD, reason_slots, 0.8
            else:
                # 가정 모드 켜져있으면 ALLOW (but lower confidence)
                reason_slots.append(ReasonSlot.PRIOR_ASSUMPTION)
                return JudgmentDecision.ALLOW, reason_slots, 0.6

        # 규칙 3: Evidence 미존재 + 비단정 → HOLD
        if not has_evidence and not is_assertive and not is_assumption:
            reason_slots.append(ReasonSlot.INSUFFICIENT_CONTEXT)
            return JudgmentDecision.HOLD, reason_slots, 0.7

        # 규칙 4: Evidence 있음 + 확정 서술 → ALLOW
        if has_evidence and is_assertive:
            return JudgmentDecision.ALLOW, reason_slots, 0.95

        # 규칙 5: Evidence 있음 + 추론 → ALLOW (조금 낮은 신뢰도)
        if has_evidence and is_assumption:
            return JudgmentDecision.ALLOW, reason_slots, 0.85

        # 규칙 6: 기타 불확정
        reason_slots.append(ReasonSlot.INSUFFICIENT_CONTEXT)
        return JudgmentDecision.INDET, reason_slots, 0.5

    def _generate_explanation(
        self,
        decision: JudgmentDecision,
        reason_slots: List[ReasonSlot],
        has_evidence: bool,
        is_assertive: bool,
        is_assumption: bool
    ) -> str:
        """
        사람이 읽을 수 있는 설명 생성.

        Args:
            decision: 판단 결정
            reason_slots: 이유 슬롯들
            has_evidence: 증거 존재 여부
            is_assertive: 확정 서술 여부
            is_assumption: 가정 기반 여부

        Returns:
            설명 텍스트
        """
        parts = [f"Decision: {decision.value}"]

        if not has_evidence:
            parts.append("No evidence/RAG sources detected.")

        if is_assertive:
            parts.append("Assertive language detected.")

        if is_assumption:
            parts.append("Assumption-based reasoning detected.")

        if reason_slots:
            slots_str = ", ".join([slot.value for slot in reason_slots])
            parts.append(f"Reasons: {slots_str}")

        return " | ".join(parts)
