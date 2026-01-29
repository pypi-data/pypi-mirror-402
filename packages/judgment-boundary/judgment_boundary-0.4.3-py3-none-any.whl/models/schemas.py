"""
Data schemas for Judgment Runtime System.
This file defines data structures for the entire system.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class JudgmentDecision(str, Enum):
    """Judgment decision type"""
    STOP = "STOP"          # Stop execution - risky or insufficient evidence
    HOLD = "HOLD"          # Hold - additional information needed
    ALLOW = "ALLOW"        # Allow execution
    INDET = "INDET"        # Indeterminate - cannot judge


class ReasonSlot(str, Enum):
    """Judgment reason slots (structured reasons)"""
    EVIDENCE_MISSING = "EVIDENCE_MISSING"
    CONFLICTED_SLOT = "CONFLICTED_SLOT"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    RISK_DETECTED = "RISK_DETECTED"
    UNVERIFIED_ASSERTION = "UNVERIFIED_ASSERTION"
    PRIOR_ASSUMPTION = "PRIOR_ASSUMPTION"
    HALLUCINATION_RISK = "HALLUCINATION_RISK"
    INSUFFICIENT_CONTEXT = "INSUFFICIENT_CONTEXT"


class DomainTag(str, Enum):
    """Domain tag"""
    LEGAL = "legal"
    MEDICAL = "medical"
    HR = "hr"
    FINANCIAL = "financial"
    GENERAL = "general"


class RejectedPath(BaseModel):
    """Rejected alternative path (Negative Proof)"""
    candidate: str = Field(..., description="Answer considered but rejected")
    rejection_reason: str = Field(..., description="Rejection reason")
    reason_slots: List[ReasonSlot] = Field(default_factory=list)


class NegativeProof(BaseModel):
    """Negative Proof structure"""
    rejected_paths: List[RejectedPath] = Field(default_factory=list)
    alternative_considered: int = Field(default=0, description="Number of alternatives considered")


class JudgmentResult(BaseModel):
    """Judgment result (Decision Module output)"""
    decision: JudgmentDecision
    reason_slots: List[ReasonSlot] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0, description="Judgment confidence")
    explanation: Optional[str] = Field(None, description="Human-readable explanation")
    negative_proof: Optional[NegativeProof] = Field(None)
    trace_signature: str = Field(..., description="Traceable signature")


class JudgmentMemoryEntry(BaseModel):
    """Judgment Memory Store storage unit"""
    prompt_signature: str = Field(..., description="Prompt hash")
    decision: JudgmentDecision
    reason_slots: List[ReasonSlot]
    negative_proof: Optional[NegativeProof] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    domain_tag: DomainTag = Field(default=DomainTag.GENERAL)
    model_id: Optional[str] = Field(None, description="Model ID used (for reference)")
    confidence: float = Field(..., ge=0.0, le=1.0)
    context_metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionAction(str, Enum):
    """Execution Router action"""
    ANSWER = "ANSWER"                    # Provide answer
    ASK_CLARIFICATION = "ASK_CLARIFICATION"  # Ask clarification question
    STOP_ESCALATE = "STOP_ESCALATE"      # Stop and escalate to human
    HOLD_GATHER = "HOLD_GATHER"          # Hold and gather information


class ExecutionRouterOutput(BaseModel):
    """Execution Router output"""
    action: ExecutionAction
    content: str = Field(..., description="Actual output content")
    judgment_result: JudgmentResult
    escalation_reason: Optional[str] = Field(None)


class AdaptationRule(BaseModel):
    """Adaptation rule"""
    rule_id: str
    condition: str = Field(..., description="Rule trigger condition")
    action: str = Field(..., description="Action to apply")
    priority: int = Field(default=0)
    active: bool = Field(default=True)


class RuntimeContext(BaseModel):
    """Runtime execution context"""
    prompt: str
    model_output: str
    rag_sources: Optional[List[str]] = Field(None, description="Presence of RAG sources")
    domain_tag: DomainTag = Field(default=DomainTag.GENERAL)
    assumption_mode: bool = Field(default=False, description="Allow prior/common sense reasoning")
    user_context: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# v0.2: Organizational Memory Layer
# ============================================================================


class BoundaryStrength(str, Enum):
    """Organizational judgment boundary strength"""
    VERY_CONSERVATIVE = "VERY_CONSERVATIVE"  # Mostly STOP/HOLD
    CONSERVATIVE = "CONSERVATIVE"            # STOP/HOLD predominant
    BALANCED = "BALANCED"                    # Balanced
    PERMISSIVE = "PERMISSIVE"                # ALLOW predominant
    VERY_PERMISSIVE = "VERY_PERMISSIVE"      # Mostly ALLOW


class JudgmentBoundaryProfile(BaseModel):
    """
    Organizational judgment character profile.

    Organizational judgment tendency that transcends individuals/sessions/models.
    """
    profile_id: str = Field(..., description="Organization-domain combination ID (e.g., ORG-GENERAL-001)")
    organization_id: str = Field(default="default", description="Organization ID")
    domain_tag: DomainTag

    # Judgment tendency (frequency-based)
    stop_bias: float = Field(..., ge=0.0, le=1.0, description="STOP ratio")
    hold_bias: float = Field(..., ge=0.0, le=1.0, description="HOLD ratio")
    allow_bias: float = Field(..., ge=0.0, le=1.0, description="ALLOW ratio")
    indet_bias: float = Field(default=0.0, ge=0.0, le=1.0, description="INDET ratio")

    # Organizational character
    boundary_strength: BoundaryStrength = Field(..., description="Boundary strength")
    dominant_decision: JudgmentDecision = Field(..., description="Most frequent judgment")

    # Repetition patterns
    frequent_reasons: List[ReasonSlot] = Field(default_factory=list, description="Frequent reasons")
    high_risk_patterns: List[str] = Field(default_factory=list, description="High-risk patterns")

    # Metadata
    sample_count: int = Field(..., description="Number of judgments constituting this profile")
    confidence: str = Field(..., description="Profile confidence (HIGH/MEDIUM/LOW)")
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    # Temporal stability
    temporal_stability: float = Field(default=1.0, ge=0.0, le=1.0,
                                     description="Stability over time (1.0=very stable)")


class OrganizationProfile(BaseModel):
    """
    Organizational judgment profile summary.

    Condenses "when does this organization stop" into a single structure.
    """
    organization_id: str = Field(default="default")

    # Domain-specific profiles
    domain_profiles: Dict[str, JudgmentBoundaryProfile] = Field(default_factory=dict)

    # Overall character
    overall_boundary_strength: BoundaryStrength = Field(default=BoundaryStrength.BALANCED)
    total_judgments: int = Field(default=0)

    # Creation information
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# v0.3: Boundary Governance & Override Layer
# ============================================================================


class DeclarationType(str, Enum):
    """Declaration type"""
    AUTOMATION_NOT_ALLOWED = "AUTOMATION_NOT_ALLOWED"
    AUTOMATION_ALLOWED = "AUTOMATION_ALLOWED"
    REQUIRE_HUMAN_REVIEW = "REQUIRE_HUMAN_REVIEW"
    EVIDENCE_REQUIRED = "EVIDENCE_REQUIRED"
    CUSTOM = "CUSTOM"


class BoundaryDeclarationEvent(BaseModel):
    """
    Organizational character declaration event.

    Organizational character changes through "declarations," not "learning."
    """
    event_id: str = Field(..., description="Event unique ID")
    event_type: str = Field(default="BOUNDARY_DECLARATION")
    domain_tag: DomainTag
    declaration: DeclarationType = Field(..., description="Declaration type")

    # Declaration issuer
    issued_by: str = Field(..., description="Declaration issuer (human | system)")
    authority: Optional[str] = Field(None, description="Authority (e.g., security_officer)")

    # Declaration content
    justification: str = Field(..., description="Declaration reason")
    scope: str = Field(default="domain", description="Application scope (domain | organization)")

    # Effectiveness
    effective_from: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(None, description="Expiration time (None=permanent)")

    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OverrideScope(str, Enum):
    """Override scope"""
    SINGLE_REQUEST = "SINGLE_REQUEST"       # Single request only
    SESSION = "SESSION"                      # During session
    DOMAIN_TEMPORARY = "DOMAIN_TEMPORARY"    # Domain temporary (with expiration time)


class HumanOverrideCapsule(BaseModel):
    """
    Human Override capsule.

    Human interventions have immediate effect but are not subject to pattern learning.
    Recorded in a separate trace channel.
    """
    override_id: str = Field(..., description="Override unique ID")

    # Original judgment
    original_decision: JudgmentDecision
    original_reasons: List[ReasonSlot] = Field(default_factory=list)
    original_confidence: float

    # Human decision
    human_decision: JudgmentDecision = Field(..., description="Decision made by human")
    override_reason: str = Field(..., description="Override reason")

    # Scope and effectiveness
    scope: OverrideScope = Field(default=OverrideScope.SINGLE_REQUEST)
    expires_at: Optional[datetime] = Field(None)

    # Issuer
    issued_by: str = Field(..., description="Override issuer")

    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    prompt_signature: Optional[str] = Field(None)
    domain_tag: DomainTag = Field(default=DomainTag.GENERAL)

    # Important: Pattern learning exclusion flag
    exclude_from_pattern_learning: bool = Field(default=True, description="Must always be True")


# ============================================================================
# v0.4: External Attestation Layer
# ============================================================================


class BoundaryAttestation(BaseModel):
    """
    Timestamp-sealed attestation object for organizational character.

    Immutable, reproducible, signable.
    """
    attestation_id: str = Field(..., description="Attestation ID (e.g., ATT-2026-01-XXXX)")
    organization_id: str = Field(..., description="Organization ID")

    # Timestamp seal
    effective_at: datetime = Field(..., description="Attestation effective time")
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    # Organizational character summary
    boundary_summary: Dict[str, str] = Field(..., description="Domain-wise boundary summary")

    # Integrity guarantee
    profile_hash: str = Field(..., description="Profile SHA-256 hash")
    declarations_hash: str = Field(..., description="Declaration events SHA-256 hash")

    # Metadata
    runtime_version: str = Field(..., description="Runtime version")
    generation_method: str = Field(default="deterministic", description="Generation method")

    # Attestation scope
    domains_included: List[str] = Field(default_factory=list)
    declarations_count: int = Field(default=0)

    # Immutability guarantee
    immutable: bool = Field(default=True, description="Always True")


class AttestationEvidence(BaseModel):
    """
    Evidence supporting the attestation.
    """
    attestation_id: str
    evidence_type: str = Field(..., description="Evidence type (profile/declaration/method)")
    content: Dict[str, Any] = Field(..., description="Evidence content")
    content_hash: str = Field(..., description="Content SHA-256 hash")
    read_only: bool = Field(default=True)
