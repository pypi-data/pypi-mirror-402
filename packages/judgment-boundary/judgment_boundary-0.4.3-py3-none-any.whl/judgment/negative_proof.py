"""
Negative Proof Generator
Module structuring "why this answer was not chosen".

Structured reasoning is more important than text quality.
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
    Negative Proof generator.

    Currently heuristic-based, but can be extended to LLM-based in the future.
    """

    def __init__(self, use_llm: bool = False):
        """
        Args:
            use_llm: Use LLM for alternative generation (currently unsupported)
        """
        self.use_llm = use_llm

    def generate(
        self,
        context: RuntimeContext,
        decision: JudgmentDecision,
        reason_slots: List[ReasonSlot]
    ) -> NegativeProof:
        """
        Generate Negative Proof.

        Args:
            context: Execution context
            decision: Judgment made
            reason_slots: Judgment reasons

        Returns:
            NegativeProof
        """
        if self.use_llm:
            # Future implementation: LLM-based alternative generation
            return self._generate_with_llm(context, decision, reason_slots)
        else:
            # Current: Heuristic-based generation
            return self._generate_heuristic(context, decision, reason_slots)

    def _generate_heuristic(
        self,
        context: RuntimeContext,
        decision: JudgmentDecision,
        reason_slots: List[ReasonSlot]
    ) -> NegativeProof:
        """
        Generate heuristic-based Negative Proof.

        Args:
            context: Execution context
            decision: Judgment made
            reason_slots: Judgment reasons

        Returns:
            NegativeProof
        """
        rejected_paths = []

        # 1. STOP/HOLD decision: original output is rejected path
        if decision in [JudgmentDecision.STOP, JudgmentDecision.HOLD]:
            rejected_paths.append(
                RejectedPath(
                    candidate=context.model_output[:200] + "...",  # Store partial only
                    rejection_reason="Original output rejected due to safety/evidence concerns",
                    reason_slots=reason_slots.copy()
                )
            )

        # 2. Evidence Missing case: reject assertive answer
        if ReasonSlot.EVIDENCE_MISSING in reason_slots:
            rejected_paths.append(
                RejectedPath(
                    candidate="Direct assertive answer without verification",
                    rejection_reason="Cannot provide definitive answer without evidence",
                    reason_slots=[ReasonSlot.EVIDENCE_MISSING, ReasonSlot.UNVERIFIED_ASSERTION]
                )
            )

        # 3. Prior Assumption case: reject assumption-based answer
        if ReasonSlot.PRIOR_ASSUMPTION in reason_slots:
            if not context.assumption_mode:
                rejected_paths.append(
                    RejectedPath(
                        candidate="Answer based on general knowledge/assumptions",
                        rejection_reason="Assumption mode disabled - cannot use prior knowledge",
                        reason_slots=[ReasonSlot.PRIOR_ASSUMPTION]
                    )
                )

        # 4. Hallucination Risk: reject generated information
        if ReasonSlot.HALLUCINATION_RISK in reason_slots:
            rejected_paths.append(
                RejectedPath(
                    candidate="Generated/fabricated information",
                    rejection_reason="Risk of hallucination - unverifiable claims",
                    reason_slots=[ReasonSlot.HALLUCINATION_RISK]
                )
            )

        # 5. ALLOW decision: reject alternative conservative approach
        if decision == JudgmentDecision.ALLOW:
            # Conservative approach (HOLD) considered but rejected due to sufficient evidence
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
        LLM-based Negative Proof generation (future implementation).

        Args:
            context: Execution context
            decision: Judgment made
            reason_slots: Judgment reasons

        Returns:
            NegativeProof
        """
        # Example prompt:
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
        Manually add rejection path.

        Args:
            negative_proof: Existing Negative Proof
            candidate: Rejected answer
            rejection_reason: Rejection reason
            reason_slots: Reason slots

        Returns:
            Updated NegativeProof
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
