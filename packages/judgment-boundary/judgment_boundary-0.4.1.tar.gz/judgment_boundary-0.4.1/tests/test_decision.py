"""
Tests for Judgment Decision Module
"""

from judgment.decision import JudgmentDecisionModule
from models.schemas import (
    RuntimeContext,
    JudgmentDecision,
    ReasonSlot,
    DomainTag
)


def test_stop_on_evidence_missing_with_assertive():
    """
    규칙 1: Evidence 미존재 + 확정 서술 → STOP
    """
    module = JudgmentDecisionModule()

    context = RuntimeContext(
        prompt="What is the salary?",
        model_output="The salary is definitely $100,000.",  # 확정 서술
        rag_sources=None,  # 증거 없음
        domain_tag=DomainTag.HR,
        assumption_mode=False
    )

    result = module.decide(context)

    assert result.decision == JudgmentDecision.STOP
    assert ReasonSlot.EVIDENCE_MISSING in result.reason_slots
    assert ReasonSlot.UNVERIFIED_ASSERTION in result.reason_slots
    assert result.confidence >= 0.8


def test_allow_with_evidence():
    """
    규칙 4: Evidence 있음 + 확정 서술 → ALLOW
    """
    module = JudgmentDecisionModule()

    context = RuntimeContext(
        prompt="What is the salary?",
        model_output="The salary is $100,000.",
        rag_sources=["database.json"],  # 증거 있음
        domain_tag=DomainTag.HR,
        assumption_mode=False
    )

    result = module.decide(context)

    assert result.decision == JudgmentDecision.ALLOW
    assert result.confidence >= 0.9


def test_hold_on_assumption_without_mode():
    """
    규칙 2: Evidence 미존재 + 추론 + assumption_mode=False → HOLD
    """
    module = JudgmentDecisionModule()

    context = RuntimeContext(
        prompt="What might the salary be?",
        model_output="The salary might be around $100,000.",  # 추론
        rag_sources=None,
        domain_tag=DomainTag.GENERAL,
        assumption_mode=False  # 가정 모드 꺼짐
    )

    result = module.decide(context)

    assert result.decision == JudgmentDecision.HOLD
    assert ReasonSlot.EVIDENCE_MISSING in result.reason_slots
    assert ReasonSlot.PRIOR_ASSUMPTION in result.reason_slots


def test_allow_assumption_with_mode():
    """
    규칙 2: Evidence 미존재 + 추론 + assumption_mode=True → ALLOW (낮은 신뢰도)
    """
    module = JudgmentDecisionModule()

    context = RuntimeContext(
        prompt="What might the salary be?",
        model_output="The salary might be around $100,000.",
        rag_sources=None,
        domain_tag=DomainTag.GENERAL,
        assumption_mode=True  # 가정 모드 켜짐
    )

    result = module.decide(context)

    assert result.decision == JudgmentDecision.ALLOW
    assert ReasonSlot.PRIOR_ASSUMPTION in result.reason_slots
    assert result.confidence < 0.7  # 낮은 신뢰도


def test_trace_signature_generation():
    """
    trace_signature 생성 확인
    """
    module = JudgmentDecisionModule()

    context = RuntimeContext(
        prompt="Test prompt",
        model_output="Test output",
        domain_tag=DomainTag.GENERAL
    )

    result = module.decide(context)

    assert result.trace_signature is not None
    assert len(result.trace_signature) > 0


if __name__ == "__main__":
    print("Running Decision Module Tests...")
    test_stop_on_evidence_missing_with_assertive()
    print("✓ test_stop_on_evidence_missing_with_assertive")

    test_allow_with_evidence()
    print("✓ test_allow_with_evidence")

    test_hold_on_assumption_without_mode()
    print("✓ test_hold_on_assumption_without_mode")

    test_allow_assumption_with_mode()
    print("✓ test_allow_assumption_with_mode")

    test_trace_signature_generation()
    print("✓ test_trace_signature_generation")

    print("\nAll tests passed!")
