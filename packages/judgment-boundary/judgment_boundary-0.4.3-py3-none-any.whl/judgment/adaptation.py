"""
Online Adaptation Rule Engine
Engine reading past judgment patterns to change behavior for next request.

Learning occurs in rule space (NOT parameter space).
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
    """Adaptation decision"""
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

    Analyzes past patterns to change behavior for next request.
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
            stop_threshold: STOP repetition threshold (N or more STOP → change to HOLD)
            domain_stop_ratio_threshold: Domain STOP ratio threshold
        """
        self.memory_store = memory_store
        self.stop_threshold = stop_threshold
        self.domain_stop_ratio_threshold = domain_stop_ratio_threshold

        # Built-in rules
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
        Analyze context and generate adaptation decision.

        Args:
            context: Execution context

        Returns:
            AdaptationDecision
        """
        decision = AdaptationDecision()

        # Generate prompt signature
        prompt_sig = generate_prompt_signature(context.prompt)

        # Rule 1: Repeated STOP → change to HOLD
        stop_count = self.memory_store.count_stop_decisions(prompt_sig)
        if stop_count >= self.stop_threshold:
            decision.should_override = True
            decision.override_decision = JudgmentDecision.HOLD
            decision.override_reason = (
                f"This prompt has resulted in STOP {stop_count} times. "
                f"Converting to HOLD to ask for clarification."
            )
            decision.applied_rules.append("repeated_stop_to_hold")

        # Rule 2: High domain STOP ratio → disable assumption_mode
        domain_stop_ratio = self.memory_store.get_domain_stop_ratio(context.domain_tag)
        if domain_stop_ratio >= self.domain_stop_ratio_threshold:
            if context.assumption_mode:
                decision.context_modifications["assumption_mode"] = False
                decision.context_modifications["assumption_mode_reason"] = (
                    f"Domain '{context.domain_tag.value}' has high STOP ratio "
                    f"({domain_stop_ratio:.2%}). Disabling assumption mode for safety."
                )
                decision.applied_rules.append("high_domain_stop_ratio")

        # Rule 3: Evidence Missing pattern detection
        domain_stats = self.memory_store.get_decision_stats(domain_tag=context.domain_tag)
        evidence_missing_count = domain_stats.get("reason_slot_counts", {}).get(
            ReasonSlot.EVIDENCE_MISSING.value, 0
        )
        total_count = domain_stats.get("total_count", 0)

        if total_count > 0 and (evidence_missing_count / total_count) > 0.5:
            # Over 50% Evidence Missing → suggest RAG integration
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
        Apply adaptation decision to context.

        Args:
            context: Original context
            adaptation: Adaptation decision

        Returns:
            Modified context
        """
        # Apply context modifications
        for key, value in adaptation.context_modifications.items():
            if hasattr(context, key):
                setattr(context, key, value)
            else:
                # Add to user_context
                context.user_context[key] = value

        return context

    def get_active_rules(self) -> List[AdaptationRule]:
        """
        Query list of active rules.

        Returns:
            Active rules
        """
        return [rule for rule in self.builtin_rules if rule.active]

    def add_custom_rule(self, rule: AdaptationRule):
        """
        Add custom rule.

        Args:
            rule: Rule to add
        """
        self.builtin_rules.append(rule)

    def disable_rule(self, rule_id: str):
        """
        Disable rule.

        Args:
            rule_id: Rule ID
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
        Query adaptation state summary.

        Args:
            context: Execution context

        Returns:
            Adaptation summary information
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
