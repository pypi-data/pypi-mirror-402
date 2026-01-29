"""
Judgment Decision Module
Core module determining judgment boundaries (STOP/HOLD/ALLOW/INDET)
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
    Judgment decision module.

    Rules:
    1. No evidence + assertive statement → STOP or HOLD
    2. Prior/common sense reasoning prohibited when assumption_mode=false
    3. Always return structured reasons (ReasonSlot)
    """

    def __init__(self):
        # Assertive statement patterns (definitive expressions)
        self.assertive_patterns = [
            r'\b(is|are|was|were|will be|must be)\b',
            r'\b(definitely|certainly|obviously|clearly)\b',
            r'\b(always|never|all|none|every)\b',
        ]

        # Reasoning/assumption patterns
        self.assumption_patterns = [
            r'\b(probably|likely|possibly|maybe|might|could|seems)\b',
            r'\b(I think|I believe|in my opinion|generally)\b',
        ]

    def decide(
        self,
        context: RuntimeContext,
        negative_proof: Optional[NegativeProof] = None
    ) -> JudgmentResult:
        """
        Perform judgment decision.

        Args:
            context: Execution context
            negative_proof: Negative Proof (can be generated externally)

        Returns:
            JudgmentResult
        """
        timestamp = datetime.utcnow().isoformat()

        # 1. Generate signatures
        prompt_sig = generate_prompt_signature(context.prompt)
        trace_sig = generate_trace_signature(
            context.prompt,
            context.model_output,
            timestamp
        )

        # 2. Check evidence
        has_evidence = self._check_evidence(context)

        # 3. Detect assertive statements
        is_assertive = self._is_assertive_output(context.model_output)

        # 4. Detect reasoning/assumptions
        is_assumption = self._is_assumption_based(context.model_output)

        # 5. Judgment logic
        decision, reason_slots, confidence = self._make_judgment(
            has_evidence=has_evidence,
            is_assertive=is_assertive,
            is_assumption=is_assumption,
            assumption_mode=context.assumption_mode,
            context=context
        )

        # 6. Generate explanation
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
        Check evidence existence.

        Args:
            context: Execution context

        Returns:
            True if evidence exists
        """
        # Evidence exists if RAG sources present
        if context.rag_sources and len(context.rag_sources) > 0:
            return True

        # Evidence exists if explicit data in context
        if context.user_context.get("has_data", False):
            return True

        # No evidence by default
        return False

    def _is_assertive_output(self, output: str) -> bool:
        """
        Detect assertive/definitive statements.

        Args:
            output: Model output

        Returns:
            True if assertive
        """
        for pattern in self.assertive_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                return True
        return False

    def _is_assumption_based(self, output: str) -> bool:
        """
        Detect reasoning/assumption-based output.

        Args:
            output: Model output

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
        Core judgment logic.

        Returns:
            (decision, reason_slots, confidence)
        """
        reason_slots = []
        confidence = 1.0

        # Rule 1: No evidence + assertive statement → STOP
        if not has_evidence and is_assertive:
            reason_slots.append(ReasonSlot.EVIDENCE_MISSING)
            reason_slots.append(ReasonSlot.UNVERIFIED_ASSERTION)
            return JudgmentDecision.STOP, reason_slots, 0.9

        # Rule 2: No evidence + reasoning → check assumption_mode
        if not has_evidence and is_assumption:
            if not assumption_mode:
                # If assumption mode off, HOLD (prompt for clarification)
                reason_slots.append(ReasonSlot.EVIDENCE_MISSING)
                reason_slots.append(ReasonSlot.PRIOR_ASSUMPTION)
                return JudgmentDecision.HOLD, reason_slots, 0.8
            else:
                # If assumption mode on, ALLOW (but lower confidence)
                reason_slots.append(ReasonSlot.PRIOR_ASSUMPTION)
                return JudgmentDecision.ALLOW, reason_slots, 0.6

        # Rule 3: No evidence + non-assertive → HOLD
        if not has_evidence and not is_assertive and not is_assumption:
            reason_slots.append(ReasonSlot.INSUFFICIENT_CONTEXT)
            return JudgmentDecision.HOLD, reason_slots, 0.7

        # Rule 4: Evidence present + assertive statement → ALLOW
        if has_evidence and is_assertive:
            return JudgmentDecision.ALLOW, reason_slots, 0.95

        # Rule 5: Evidence present + reasoning → ALLOW (slightly lower confidence)
        if has_evidence and is_assumption:
            return JudgmentDecision.ALLOW, reason_slots, 0.85

        # Rule 6: Other indeterminate cases
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
        Generate human-readable explanation.

        Args:
            decision: Judgment decision
            reason_slots: Reason slots
            has_evidence: Evidence exists
            is_assertive: Assertive statement
            is_assumption: Assumption-based

        Returns:
            Explanation text
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
