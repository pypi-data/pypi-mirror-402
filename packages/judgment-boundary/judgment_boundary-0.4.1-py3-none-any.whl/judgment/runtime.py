"""
Judgment Runtime
모든 컴포넌트를 통합하는 메인 런타임.
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

    모델에 독립적인 판단 시스템.
    학습 주체는 모델이 아니라 Runtime이다.
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
            memory_store_path: Memory Store 저장 경로
            enable_adaptation: 적응 엔진 활성화 여부
            enable_negative_proof: Negative Proof 생성 활성화 여부
            enable_organizational_memory: v0.2 조직 기억 레이어 활성화 (기본: False)
            profile_store_path: v0.2 조직 프로필 저장 경로
            organization_id: v0.2 조직 ID
        """
        # 컴포넌트 초기화 (v0.1 - 변경 없음)
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
        전체 판단 프로세스 실행.

        Args:
            prompt: 사용자 입력
            model_output: LLM 출력
            rag_sources: RAG 소스들
            domain_tag: 도메인 태그
            assumption_mode: 가정 모드 활성화 여부
            model_id: 모델 ID (참고용)
            user_context: 추가 컨텍스트

        Returns:
            ExecutionRouterOutput
        """
        # 1. Context 생성
        context = RuntimeContext(
            prompt=prompt,
            model_output=model_output,
            rag_sources=rag_sources,
            domain_tag=domain_tag,
            assumption_mode=assumption_mode,
            user_context=user_context or {}
        )

        # 1.5. v0.2: Organizational Profile 조회 (방향 제시만)
        if self.enable_organizational_memory and self.profile_store:
            org_profile = self.profile_store.get_domain_profile(
                domain_tag=domain_tag,
                organization_id=self.organization_id
            )
            if org_profile:
                # 조직 프로필 정보를 context에 추가 (개별 판단을 덮어쓰지 않음)
                context.user_context["org_profile"] = {
                    "boundary_strength": org_profile.boundary_strength.value,
                    "dominant_decision": org_profile.dominant_decision.value,
                    "stop_bias": org_profile.stop_bias,
                    "confidence": org_profile.confidence
                }

        # 2. Adaptation 적용 (과거 패턴 기반)
        adaptation_decision = None
        if self.enable_adaptation and self.adaptation_engine:
            adaptation_decision = self.adaptation_engine.analyze_and_adapt(context)
            context = self.adaptation_engine.apply_adaptation(context, adaptation_decision)

        # 3. Judgment Decision
        judgment_result = self.decision_module.decide(context)

        # 4. Adaptation Override 적용
        if adaptation_decision and adaptation_decision.should_override:
            # Override decision
            judgment_result.decision = adaptation_decision.override_decision
            if adaptation_decision.override_reason:
                judgment_result.explanation += f" | Override: {adaptation_decision.override_reason}"

        # 5. Negative Proof 생성
        if self.enable_negative_proof:
            negative_proof = self.negative_proof_generator.generate(
                context=context,
                decision=judgment_result.decision,
                reason_slots=judgment_result.reason_slots
            )
            judgment_result.negative_proof = negative_proof

        # 6. Memory Store에 저장
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

        # 7. Execution Router - 액션 결정
        router_output = self._route_execution(judgment_result, context)

        return router_output

    def _route_execution(
        self,
        judgment_result: JudgmentResult,
        context: RuntimeContext
    ) -> ExecutionRouterOutput:
        """
        Execution Router - 판단 결과에 따라 액션 결정.

        Args:
            judgment_result: 판단 결과
            context: 실행 컨텍스트

        Returns:
            ExecutionRouterOutput
        """
        decision = judgment_result.decision

        if decision == JudgmentDecision.STOP:
            # STOP → 중단 및 에스컬레이션
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
            # HOLD → 명확화 질문
            clarification = self._generate_clarification_question(
                judgment_result, context
            )
            return ExecutionRouterOutput(
                action=ExecutionAction.ASK_CLARIFICATION,
                content=clarification,
                judgment_result=judgment_result
            )

        elif decision == JudgmentDecision.ALLOW:
            # ALLOW → 답변 제공
            return ExecutionRouterOutput(
                action=ExecutionAction.ANSWER,
                content=context.model_output,
                judgment_result=judgment_result
            )

        else:  # INDET
            # INDET → 불확정 - 보수적으로 HOLD 처리
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
        명확화 질문 생성.

        Args:
            judgment_result: 판단 결과
            context: 실행 컨텍스트

        Returns:
            명확화 질문
        """
        reason_slots = judgment_result.reason_slots

        # ReasonSlot에 따라 질문 생성
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

        # 기본 질문
        return (
            "I need some clarification to provide the best answer. "
            "Could you provide more details about your question?"
        )

    def get_runtime_stats(self) -> Dict[str, Any]:
        """
        Runtime 통계 조회.

        Returns:
            통계 정보
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
        프롬프트 분석 (과거 패턴 조회).

        Args:
            prompt: 분석할 프롬프트
            domain_tag: 도메인 태그

        Returns:
            분석 결과
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
                for entry in history[-5:]  # 최근 5개
            ]
        }

        if self.enable_adaptation and self.adaptation_engine:
            context = RuntimeContext(
                prompt=prompt,
                model_output="",  # 분석만 하므로 빈 값
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
        조직 프로필 생성/업데이트.

        축적된 판단 로그를 분석하여 조직의 판단 성격을 추출.

        Args:
            domains: 프로필 생성할 도메인들 (None이면 전체)

        Returns:
            OrganizationProfile or None
        """
        if not self.enable_organizational_memory:
            print("Organizational Memory Layer is not enabled.")
            return None

        # 전체 조직 프로필 생성
        org_profile = self.aggregator.generate_organization_profile(
            organization_id=self.organization_id
        )

        # 저장
        if org_profile:
            self.profile_store.save_profile(org_profile)

        return org_profile

    def get_organizational_profile(self) -> Optional[OrganizationProfile]:
        """
        저장된 조직 프로필 조회.

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
        조직의 판단 성격을 사람이 읽을 수 있는 문장으로 설명.

        "이 조직은 언제 멈추는가"를 명확히 표현.

        Args:
            domain_tag: 도메인

        Returns:
            설명 문장
        """
        if not self.enable_organizational_memory:
            return "Organizational Memory Layer is not enabled."

        return self.profile_store.explain_profile(
            domain_tag=domain_tag,
            organization_id=self.organization_id
        )

    def get_profile_summary(self) -> Dict[str, Any]:
        """
        조직 프로필 요약 조회.

        Returns:
            요약 정보
        """
        if not self.enable_organizational_memory:
            return {
                "enabled": False,
                "message": "Organizational Memory Layer is not enabled"
            }

        summary = self.profile_store.get_profile_summary(self.organization_id)
        summary["enabled"] = True
        return summary
