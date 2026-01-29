"""
Negative Proof Generator
"왜 이 답을 선택하지 않았는지"를 구조화하는 모듈.

텍스트 품질보다 구조적 이유 명시가 중요.
"""

from typing import List, Optional
import json

from models.schemas import (
    NegativeProof,
    RejectedPath,
    ReasonSlot,
    RuntimeContext,
    JudgmentDecision
)


class NegativeProofGenerator:
    """
    Negative Proof 생성기.

    현재는 휴리스틱 기반이지만, 향후 LLM 기반으로 확장 가능.
    """

    def __init__(self, use_llm: bool = False):
        """
        Args:
            use_llm: LLM을 사용한 대안 생성 여부 (현재는 미지원)
        """
        self.use_llm = use_llm

    def generate(
        self,
        context: RuntimeContext,
        decision: JudgmentDecision,
        reason_slots: List[ReasonSlot]
    ) -> NegativeProof:
        """
        Negative Proof 생성.

        Args:
            context: 실행 컨텍스트
            decision: 내린 판단
            reason_slots: 판단 이유들

        Returns:
            NegativeProof
        """
        if self.use_llm:
            # 향후 구현: LLM을 사용한 대안 생성
            return self._generate_with_llm(context, decision, reason_slots)
        else:
            # 현재: 휴리스틱 기반 생성
            return self._generate_heuristic(context, decision, reason_slots)

    def _generate_heuristic(
        self,
        context: RuntimeContext,
        decision: JudgmentDecision,
        reason_slots: List[ReasonSlot]
    ) -> NegativeProof:
        """
        휴리스틱 기반 Negative Proof 생성.

        Args:
            context: 실행 컨텍스트
            decision: 내린 판단
            reason_slots: 판단 이유들

        Returns:
            NegativeProof
        """
        rejected_paths = []

        # 1. STOP/HOLD 결정일 경우: 원래 출력이 거부된 경로
        if decision in [JudgmentDecision.STOP, JudgmentDecision.HOLD]:
            rejected_paths.append(
                RejectedPath(
                    candidate=context.model_output[:200] + "...",  # 일부만 저장
                    rejection_reason="Original output rejected due to safety/evidence concerns",
                    reason_slots=reason_slots.copy()
                )
            )

        # 2. Evidence Missing 경우: 단정적 답변 거부
        if ReasonSlot.EVIDENCE_MISSING in reason_slots:
            rejected_paths.append(
                RejectedPath(
                    candidate="Direct assertive answer without verification",
                    rejection_reason="Cannot provide definitive answer without evidence",
                    reason_slots=[ReasonSlot.EVIDENCE_MISSING, ReasonSlot.UNVERIFIED_ASSERTION]
                )
            )

        # 3. Prior Assumption 경우: 가정 기반 답변 거부
        if ReasonSlot.PRIOR_ASSUMPTION in reason_slots:
            if not context.assumption_mode:
                rejected_paths.append(
                    RejectedPath(
                        candidate="Answer based on general knowledge/assumptions",
                        rejection_reason="Assumption mode disabled - cannot use prior knowledge",
                        reason_slots=[ReasonSlot.PRIOR_ASSUMPTION]
                    )
                )

        # 4. Hallucination Risk: 생성된 정보 거부
        if ReasonSlot.HALLUCINATION_RISK in reason_slots:
            rejected_paths.append(
                RejectedPath(
                    candidate="Generated/fabricated information",
                    rejection_reason="Risk of hallucination - unverifiable claims",
                    reason_slots=[ReasonSlot.HALLUCINATION_RISK]
                )
            )

        # 5. ALLOW 결정일 경우: 대안적 보수적 접근 거부
        if decision == JudgmentDecision.ALLOW:
            # 보수적 접근(HOLD)을 고려했지만 증거가 충분해서 거부
            if context.rag_sources:
                rejected_paths.append(
                    RejectedPath(
                        candidate="Conservative HOLD decision",
                        rejection_reason="Sufficient evidence available - no need to hold",
                        reason_slots=[]
                    )
                )

        return NegativeProof(
            rejected_paths=rejected_paths,
            alternative_considered=len(rejected_paths)
        )

    def _generate_with_llm(
        self,
        context: RuntimeContext,
        decision: JudgmentDecision,
        reason_slots: List[ReasonSlot]
    ) -> NegativeProof:
        """
        LLM 기반 Negative Proof 생성 (향후 구현).

        Args:
            context: 실행 컨텍스트
            decision: 내린 판단
            reason_slots: 판단 이유들

        Returns:
            NegativeProof
        """
        # TODO: LLM을 호출하여 대안 생성
        # 예시 프롬프트:
        # "Given this prompt and decision, generate 3 alternative responses
        #  that were considered but rejected, with structured reasons."

        raise NotImplementedError("LLM-based negative proof generation not yet implemented")

    def add_manual_rejection(
        self,
        negative_proof: NegativeProof,
        candidate: str,
        rejection_reason: str,
        reason_slots: List[ReasonSlot]
    ) -> NegativeProof:
        """
        수동으로 거부 경로 추가.

        Args:
            negative_proof: 기존 Negative Proof
            candidate: 거부된 답변
            rejection_reason: 거부 이유
            reason_slots: 이유 슬롯들

        Returns:
            업데이트된 NegativeProof
        """
        negative_proof.rejected_paths.append(
            RejectedPath(
                candidate=candidate,
                rejection_reason=rejection_reason,
                reason_slots=reason_slots
            )
        )
        negative_proof.alternative_considered += 1
        return negative_proof
