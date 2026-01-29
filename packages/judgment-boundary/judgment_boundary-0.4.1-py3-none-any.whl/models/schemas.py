"""
Data schemas for Judgment Runtime System.
이 파일은 시스템 전체의 데이터 구조를 정의한다.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class JudgmentDecision(str, Enum):
    """판단 결정 타입"""
    STOP = "STOP"          # 실행 중단 - 위험하거나 증거 부족
    HOLD = "HOLD"          # 보류 - 추가 정보 필요
    ALLOW = "ALLOW"        # 실행 허용
    INDET = "INDET"        # 불확정 - 판단 불가


class ReasonSlot(str, Enum):
    """판단 이유 슬롯 (구조화된 이유)"""
    EVIDENCE_MISSING = "EVIDENCE_MISSING"
    CONFLICTED_SLOT = "CONFLICTED_SLOT"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    RISK_DETECTED = "RISK_DETECTED"
    UNVERIFIED_ASSERTION = "UNVERIFIED_ASSERTION"
    PRIOR_ASSUMPTION = "PRIOR_ASSUMPTION"
    HALLUCINATION_RISK = "HALLUCINATION_RISK"
    INSUFFICIENT_CONTEXT = "INSUFFICIENT_CONTEXT"


class DomainTag(str, Enum):
    """도메인 태그"""
    LEGAL = "legal"
    MEDICAL = "medical"
    HR = "hr"
    FINANCIAL = "financial"
    GENERAL = "general"


class RejectedPath(BaseModel):
    """거부된 대안 경로 (Negative Proof)"""
    candidate: str = Field(..., description="고려했지만 거부한 답변")
    rejection_reason: str = Field(..., description="거부 이유")
    reason_slots: List[ReasonSlot] = Field(default_factory=list)


class NegativeProof(BaseModel):
    """Negative Proof 구조"""
    rejected_paths: List[RejectedPath] = Field(default_factory=list)
    alternative_considered: int = Field(default=0, description="고려한 대안 수")


class JudgmentResult(BaseModel):
    """판단 결과 (Decision Module 출력)"""
    decision: JudgmentDecision
    reason_slots: List[ReasonSlot] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0, description="판단 신뢰도")
    explanation: Optional[str] = Field(None, description="사람이 읽을 수 있는 설명")
    negative_proof: Optional[NegativeProof] = Field(None)
    trace_signature: str = Field(..., description="추적 가능한 서명")


class JudgmentMemoryEntry(BaseModel):
    """Judgment Memory Store 저장 단위"""
    prompt_signature: str = Field(..., description="프롬프트 해시")
    decision: JudgmentDecision
    reason_slots: List[ReasonSlot]
    negative_proof: Optional[NegativeProof] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    domain_tag: DomainTag = Field(default=DomainTag.GENERAL)
    model_id: Optional[str] = Field(None, description="사용된 모델 ID (참고용)")
    confidence: float = Field(..., ge=0.0, le=1.0)
    context_metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionAction(str, Enum):
    """Execution Router 액션"""
    ANSWER = "ANSWER"                    # 답변 제공
    ASK_CLARIFICATION = "ASK_CLARIFICATION"  # 명확화 질문
    STOP_ESCALATE = "STOP_ESCALATE"      # 중단 및 인간 에스컬레이션
    HOLD_GATHER = "HOLD_GATHER"          # 보류 및 정보 수집


class ExecutionRouterOutput(BaseModel):
    """Execution Router 출력"""
    action: ExecutionAction
    content: str = Field(..., description="실제 출력 내용")
    judgment_result: JudgmentResult
    escalation_reason: Optional[str] = Field(None)


class AdaptationRule(BaseModel):
    """적응 규칙"""
    rule_id: str
    condition: str = Field(..., description="규칙 발동 조건")
    action: str = Field(..., description="적용할 액션")
    priority: int = Field(default=0)
    active: bool = Field(default=True)


class RuntimeContext(BaseModel):
    """Runtime 실행 컨텍스트"""
    prompt: str
    model_output: str
    rag_sources: Optional[List[str]] = Field(None, description="RAG 소스 존재 여부")
    domain_tag: DomainTag = Field(default=DomainTag.GENERAL)
    assumption_mode: bool = Field(default=False, description="Prior/상식 추론 허용 여부")
    user_context: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# v0.2: Organizational Memory Layer
# ============================================================================


class BoundaryStrength(str, Enum):
    """조직의 판단 경계 강도"""
    VERY_CONSERVATIVE = "VERY_CONSERVATIVE"  # 대부분 STOP/HOLD
    CONSERVATIVE = "CONSERVATIVE"            # STOP/HOLD 우세
    BALANCED = "BALANCED"                    # 균형
    PERMISSIVE = "PERMISSIVE"                # ALLOW 우세
    VERY_PERMISSIVE = "VERY_PERMISSIVE"      # 대부분 ALLOW


class JudgmentBoundaryProfile(BaseModel):
    """
    조직 단위 판단 성격 프로필.

    개인/세션/모델을 초월한 조직의 판단 경향.
    """
    profile_id: str = Field(..., description="조직-도메인 조합 ID (e.g., ORG-GENERAL-001)")
    organization_id: str = Field(default="default", description="조직 ID")
    domain_tag: DomainTag

    # 판단 경향 (빈도 기반)
    stop_bias: float = Field(..., ge=0.0, le=1.0, description="STOP 비율")
    hold_bias: float = Field(..., ge=0.0, le=1.0, description="HOLD 비율")
    allow_bias: float = Field(..., ge=0.0, le=1.0, description="ALLOW 비율")
    indet_bias: float = Field(default=0.0, ge=0.0, le=1.0, description="INDET 비율")

    # 조직 성격
    boundary_strength: BoundaryStrength = Field(..., description="경계 강도")
    dominant_decision: JudgmentDecision = Field(..., description="가장 빈번한 판단")

    # 반복 패턴
    frequent_reasons: List[ReasonSlot] = Field(default_factory=list, description="빈번한 이유들")
    high_risk_patterns: List[str] = Field(default_factory=list, description="고위험 패턴들")

    # 메타데이터
    sample_count: int = Field(..., description="이 프로필을 구성한 판단 개수")
    confidence: str = Field(..., description="프로필 신뢰도 (HIGH/MEDIUM/LOW)")
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    # 시간 안정성
    temporal_stability: float = Field(default=1.0, ge=0.0, le=1.0,
                                     description="시간에 따른 안정성 (1.0=매우 안정)")


class OrganizationProfile(BaseModel):
    """
    조직 전체의 판단 프로필 요약.

    "이 조직은 언제 멈추는가"를 하나의 구조로 응축.
    """
    organization_id: str = Field(default="default")

    # 도메인별 프로필
    domain_profiles: Dict[str, JudgmentBoundaryProfile] = Field(default_factory=dict)

    # 전체 성격
    overall_boundary_strength: BoundaryStrength = Field(default=BoundaryStrength.BALANCED)
    total_judgments: int = Field(default=0)

    # 생성 정보
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# v0.3: Boundary Governance & Override Layer
# ============================================================================


class DeclarationType(str, Enum):
    """선언 타입"""
    AUTOMATION_NOT_ALLOWED = "AUTOMATION_NOT_ALLOWED"
    AUTOMATION_ALLOWED = "AUTOMATION_ALLOWED"
    REQUIRE_HUMAN_REVIEW = "REQUIRE_HUMAN_REVIEW"
    EVIDENCE_REQUIRED = "EVIDENCE_REQUIRED"
    CUSTOM = "CUSTOM"


class BoundaryDeclarationEvent(BaseModel):
    """
    조직 성격 선언 이벤트.

    조직 성격은 "학습"이 아니라 "선언"으로 변경된다.
    """
    event_id: str = Field(..., description="이벤트 고유 ID")
    event_type: str = Field(default="BOUNDARY_DECLARATION")
    domain_tag: DomainTag
    declaration: DeclarationType = Field(..., description="선언 타입")

    # 선언 주체
    issued_by: str = Field(..., description="선언 주체 (human | system)")
    authority: Optional[str] = Field(None, description="권한 (e.g., security_officer)")

    # 선언 내용
    justification: str = Field(..., description="선언 이유")
    scope: str = Field(default="domain", description="적용 범위 (domain | organization)")

    # 효력
    effective_from: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(None, description="만료 시각 (None=영구)")

    # 메타데이터
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OverrideScope(str, Enum):
    """Override 범위"""
    SINGLE_REQUEST = "SINGLE_REQUEST"       # 단일 요청만
    SESSION = "SESSION"                      # 세션 동안
    DOMAIN_TEMPORARY = "DOMAIN_TEMPORARY"    # 도메인 임시 (만료 시각 지정)


class HumanOverrideCapsule(BaseModel):
    """
    Human Override 캡슐.

    사람의 개입은 즉시 효력이 있지만, 패턴 학습 대상이 아니다.
    별도 trace channel에 기록된다.
    """
    override_id: str = Field(..., description="Override 고유 ID")

    # 원본 판단
    original_decision: JudgmentDecision
    original_reasons: List[ReasonSlot] = Field(default_factory=list)
    original_confidence: float

    # 사람의 결정
    human_decision: JudgmentDecision = Field(..., description="사람이 내린 결정")
    override_reason: str = Field(..., description="Override 이유")

    # 범위 및 효력
    scope: OverrideScope = Field(default=OverrideScope.SINGLE_REQUEST)
    expires_at: Optional[datetime] = Field(None)

    # 주체
    issued_by: str = Field(..., description="Override 주체")

    # 메타데이터
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    prompt_signature: Optional[str] = Field(None)
    domain_tag: DomainTag = Field(default=DomainTag.GENERAL)

    # 중요: 패턴 학습 제외 플래그
    exclude_from_pattern_learning: bool = Field(default=True, description="항상 True여야 함")


# ============================================================================
# v0.4: External Attestation Layer
# ============================================================================


class BoundaryAttestation(BaseModel):
    """
    조직 성격의 시점 봉인 증명 객체.

    변경 불가, 재현 가능, 서명 가능.
    """
    attestation_id: str = Field(..., description="증명 ID (e.g., ATT-2026-01-XXXX)")
    organization_id: str = Field(..., description="조직 ID")

    # 시점 봉인
    effective_at: datetime = Field(..., description="증명 유효 시점")
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    # 조직 성격 요약
    boundary_summary: Dict[str, str] = Field(..., description="도메인별 경계 요약")

    # 무결성 보장
    profile_hash: str = Field(..., description="프로필 SHA-256 해시")
    declarations_hash: str = Field(..., description="선언 이벤트 SHA-256 해시")

    # 메타데이터
    runtime_version: str = Field(..., description="Runtime 버전")
    generation_method: str = Field(default="deterministic", description="생성 방법")

    # 증명 범위
    domains_included: List[str] = Field(default_factory=list)
    declarations_count: int = Field(default=0)

    # 불변성 보장
    immutable: bool = Field(default=True, description="항상 True")


class AttestationEvidence(BaseModel):
    """
    Attestation을 뒷받침하는 근거.
    """
    attestation_id: str
    evidence_type: str = Field(..., description="근거 타입 (profile/declaration/method)")
    content: Dict[str, Any] = Field(..., description="근거 내용")
    content_hash: str = Field(..., description="내용 SHA-256 해시")
    read_only: bool = Field(default=True)
