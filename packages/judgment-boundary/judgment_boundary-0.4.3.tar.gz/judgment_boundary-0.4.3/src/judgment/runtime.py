"""
Judgment Runtime
Main runtime integrating all components.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from models.schemas import (
    RuntimeContext,
    JudgmentResult,
    JudgmentMemoryEntry,
    ExecutionAction,
    ExecutionRouterOutput,
    JudgmentDecision,
    DomainTag,
    ReasonSlot,
    # v0.2: Organizational Memory Layer
    JudgmentBoundaryProfile,
    OrganizationProfile
)
from judgment.decision import JudgmentDecisionModule
from judgment.negative_proof import NegativeProofGenerator
from judgment.memory import JudgmentMemoryStore
from judgment.adaptation import OnlineAdaptationEngine
from utils.hashing import generate_prompt_signature

# v0.2 imports
try:
    from judgment.aggregator import JudgmentMemoryAggregator
    from judgment.profile_store import OrganizationProfileStore
    V02_AVAILABLE = True
except ImportError:
    V02_AVAILABLE = False


class JudgmentRuntime:
    """
    Judgment Runtime - External Accumulation Loop.

    Model-independent judgment system.
    The learning subject is Runtime, not the model.
    """

    def __init__(
        self,
        memory_store_path: str = "./judgment_memory.jsonl",
        enable_adaptation: bool = True,
        enable_negative_proof: bool = True,
        # v0.2: Organizational Memory Layer
        enable_organizational_memory: bool = False,
        profile_store_path: str = "./organization_profile.json",
        organization_id: str = "default"
    ):
        """
        Args:
            memory_store_path: Memory Store storage path
            enable_adaptation: Enable adaptation engine
            enable_negative_proof: Enable Negative Proof generation
            enable_organizational_memory: v0.2 Enable organizational memory layer (default: False)
            profile_store_path: v0.2 Organization profile storage path
            organization_id: v0.2 Organization ID
        """
        # Component initialization (v0.1 - no changes)
        self.decision_module = JudgmentDecisionModule()
        self.negative_proof_generator = NegativeProofGenerator()
        self.memory_store = JudgmentMemoryStore(storage_path=memory_store_path)
        self.adaptation_engine = OnlineAdaptationEngine(
            memory_store=self.memory_store
        ) if enable_adaptation else None

        self.enable_adaptation = enable_adaptation
        self.enable_negative_proof = enable_negative_proof

        # v0.2: Organizational Memory Layer
        self.enable_organizational_memory = enable_organizational_memory and V02_AVAILABLE
        self.organization_id = organization_id

        if self.enable_organizational_memory:
            self.profile_store = OrganizationProfileStore(storage_path=profile_store_path)
            self.aggregator = JudgmentMemoryAggregator(memory_store=self.memory_store)
        else:
            self.profile_store = None
            self.aggregator = None

    def process(
        self,
        prompt: str,
        model_output: str,
        rag_sources: Optional[list] = None,
        domain_tag: DomainTag = DomainTag.GENERAL,
        assumption_mode: bool = False,
        model_id: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> ExecutionRouterOutput:
        """
        Execute complete judgment process.

        Args:
            prompt: User input
            model_output: LLM output
            rag_sources: RAG sources
            domain_tag: Domain tag
            assumption_mode: Enable assumption mode
            model_id: Model ID (for reference)
            user_context: Additional context

        Returns:
            ExecutionRouterOutput
        """
        # 1. Create Context
        context = RuntimeContext(
            prompt=prompt,
            model_output=model_output,
            rag_sources=rag_sources,
            domain_tag=domain_tag,
            assumption_mode=assumption_mode,
            user_context=user_context or {}
        )

        # 1.5. v0.2: Query Organizational Profile (guidance only)
        if self.enable_organizational_memory and self.profile_store:
            org_profile = self.profile_store.get_domain_profile(
                domain_tag=domain_tag,
                organization_id=self.organization_id
            )
            if org_profile:
                # Add organization profile info to context (does not override individual judgments)
                context.user_context["org_profile"] = {
                    "boundary_strength": org_profile.boundary_strength.value,
                    "dominant_decision": org_profile.dominant_decision.value,
                    "stop_bias": org_profile.stop_bias,
                    "confidence": org_profile.confidence
                }

        # 2. Apply Adaptation (based on past patterns)
        adaptation_decision = None
        if self.enable_adaptation and self.adaptation_engine:
            adaptation_decision = self.adaptation_engine.analyze_and_adapt(context)
            context = self.adaptation_engine.apply_adaptation(context, adaptation_decision)

        # 3. Judgment Decision
        judgment_result = self.decision_module.decide(context)

        # 4. Apply Adaptation Override
        if adaptation_decision and adaptation_decision.should_override:
            # Override decision
            judgment_result.decision = adaptation_decision.override_decision
            if adaptation_decision.override_reason:
                judgment_result.explanation += f" | Override: {adaptation_decision.override_reason}"

        # 5. Generate Negative Proof
        if self.enable_negative_proof:
            negative_proof = self.negative_proof_generator.generate(
                context=context,
                decision=judgment_result.decision,
                reason_slots=judgment_result.reason_slots
            )
            judgment_result.negative_proof = negative_proof

        # 6. Store in Memory Store
        memory_entry = JudgmentMemoryEntry(
            prompt_signature=generate_prompt_signature(prompt),
            decision=judgment_result.decision,
            reason_slots=judgment_result.reason_slots,
            negative_proof=judgment_result.negative_proof,
            timestamp=datetime.utcnow(),
            domain_tag=domain_tag,
            model_id=model_id,
            confidence=judgment_result.confidence,
            context_metadata={
                "has_rag": bool(rag_sources),
                "assumption_mode": assumption_mode,
                "adaptation_applied": bool(adaptation_decision and adaptation_decision.applied_rules)
            }
        )
        self.memory_store.append(memory_entry)

        # 7. Execution Router - Determine action
        router_output = self._route_execution(judgment_result, context)

        return router_output

    def _route_execution(
        self,
        judgment_result: JudgmentResult,
        context: RuntimeContext
    ) -> ExecutionRouterOutput:
        """
        Execution Router - Determine action based on judgment result.

        Args:
            judgment_result: Judgment result
            context: Execution context

        Returns:
            ExecutionRouterOutput
        """
        decision = judgment_result.decision

        if decision == JudgmentDecision.STOP:
            # STOP - Stop and escalate
            return ExecutionRouterOutput(
                action=ExecutionAction.STOP_ESCALATE,
                content=(
                    "Cannot provide a safe answer to this request. "
                    "This requires human review.\n\n"
                    f"Reason: {judgment_result.explanation}"
                ),
                judgment_result=judgment_result,
                escalation_reason=judgment_result.explanation
            )

        elif decision == JudgmentDecision.HOLD:
            # HOLD - Ask clarification question
            clarification = self._generate_clarification_question(
                judgment_result, context
            )
            return ExecutionRouterOutput(
                action=ExecutionAction.ASK_CLARIFICATION,
                content=clarification,
                judgment_result=judgment_result
            )

        elif decision == JudgmentDecision.ALLOW:
            # ALLOW - Provide answer
            return ExecutionRouterOutput(
                action=ExecutionAction.ANSWER,
                content=context.model_output,
                judgment_result=judgment_result
            )

        else:  # INDET
            # INDET - Indeterminate - conservatively treat as HOLD
            return ExecutionRouterOutput(
                action=ExecutionAction.ASK_CLARIFICATION,
                content=(
                    "I'm uncertain about how to best answer this. "
                    "Could you provide more context or clarify your requirements?"
                ),
                judgment_result=judgment_result
            )

    def _generate_clarification_question(
        self,
        judgment_result: JudgmentResult,
        context: RuntimeContext
    ) -> str:
        """
        Generate clarification question.

        Args:
            judgment_result: Judgment result
            context: Execution context

        Returns:
            Clarification question
        """
        reason_slots = judgment_result.reason_slots

        # Generate question based on ReasonSlot
        if ReasonSlot.EVIDENCE_MISSING in reason_slots:
            return (
                "I don't have enough verified information to answer this confidently. "
                "Could you provide:\n"
                "- Specific sources or references?\n"
                "- Additional context or data?\n"
                "- Clarification on what information you have available?"
            )

        if ReasonSlot.PRIOR_ASSUMPTION in reason_slots:
            return (
                "This would require me to make assumptions based on general knowledge. "
                "Would you like me to:\n"
                "1. Provide a general answer with clear assumptions stated?\n"
                "2. Wait for you to provide specific information?\n"
                "3. Help you find relevant sources first?"
            )

        if ReasonSlot.INSUFFICIENT_CONTEXT in reason_slots:
            return (
                "I need more context to provide a useful answer. "
                "Could you clarify:\n"
                "- What specific aspect you're interested in?\n"
                "- What's the intended use of this information?\n"
                "- Any constraints or requirements I should know?"
            )

        # Default question
        return (
            "I need some clarification to provide the best answer. "
            "Could you provide more details about your question?"
        )

    def get_runtime_stats(self) -> Dict[str, Any]:
        """
        Query Runtime statistics.

        Returns:
            Statistics information
        """
        overall_stats = self.memory_store.get_decision_stats()
        recent_entries = self.memory_store.get_recent_entries(limit=10)

        stats = {
            "overall": overall_stats,
            "recent_count": len(recent_entries),
            "recent_decisions": [
                {
                    "decision": entry.decision.value,
                    "confidence": entry.confidence,
                    "timestamp": entry.timestamp.isoformat()
                }
                for entry in recent_entries
            ]
        }

        if self.enable_adaptation and self.adaptation_engine:
            stats["active_rules"] = [
                rule.rule_id for rule in self.adaptation_engine.get_active_rules()
            ]

        return stats

    def analyze_prompt(
        self,
        prompt: str,
        domain_tag: DomainTag = DomainTag.GENERAL
    ) -> Dict[str, Any]:
        """
        Analyze prompt (query past patterns).

        Args:
            prompt: Prompt to analyze
            domain_tag: Domain tag

        Returns:
            Analysis result
        """
        prompt_sig = generate_prompt_signature(prompt)
        history = self.memory_store.query_by_prompt_signature(prompt_sig)
        prompt_stats = self.memory_store.get_decision_stats(prompt_signature=prompt_sig)

        analysis = {
            "prompt_signature": prompt_sig,
            "history_count": len(history),
            "stats": prompt_stats,
            "recent_decisions": [
                {
                    "decision": entry.decision.value,
                    "confidence": entry.confidence,
                    "timestamp": entry.timestamp.isoformat()
                }
                for entry in history[-5:]  # Recent 5
            ]
        }

        if self.enable_adaptation and self.adaptation_engine:
            context = RuntimeContext(
                prompt=prompt,
                model_output="",  # Empty value for analysis only
                domain_tag=domain_tag
            )
            adaptation_summary = self.adaptation_engine.get_adaptation_summary(context)
            analysis["adaptation"] = adaptation_summary

        return analysis

    # ============================================================================
    # v0.2: Organizational Memory Layer Methods
    # ============================================================================

    def build_organizational_profile(
        self,
        domains: Optional[List[DomainTag]] = None
    ) -> Optional[OrganizationProfile]:
        """
        Create/update organization profile.

        Analyze accumulated judgment logs to extract organizational judgment character.

        Args:
            domains: Domains to generate profiles for (None for all)

        Returns:
            OrganizationProfile or None
        """
        if not self.enable_organizational_memory:
            print("Organizational Memory Layer is not enabled.")
            return None

        # Generate complete organization profile
        org_profile = self.aggregator.generate_organization_profile(
            organization_id=self.organization_id
        )

        # Save
        if org_profile:
            self.profile_store.save_profile(org_profile)

        return org_profile

    def get_organizational_profile(self) -> Optional[OrganizationProfile]:
        """
        Query saved organization profile.

        Returns:
            OrganizationProfile or None
        """
        if not self.enable_organizational_memory:
            return None

        return self.profile_store.load_profile(self.organization_id)

    def explain_organizational_character(
        self,
        domain_tag: DomainTag
    ) -> str:
        """
        Explain organization's judgment character in human-readable language.

        Clearly express "when this organization stops".

        Args:
            domain_tag: Domain

        Returns:
            Explanation text
        """
        if not self.enable_organizational_memory:
            return "Organizational Memory Layer is not enabled."

        return self.profile_store.explain_profile(
            domain_tag=domain_tag,
            organization_id=self.organization_id
        )

    def get_profile_summary(self) -> Dict[str, Any]:
        """
        Query organization profile summary.

        Returns:
            Summary information
        """
        if not self.enable_organizational_memory:
            return {
                "enabled": False,
                "message": "Organizational Memory Layer is not enabled"
            }

        summary = self.profile_store.get_profile_summary(self.organization_id)
        summary["enabled"] = True
        return summary
