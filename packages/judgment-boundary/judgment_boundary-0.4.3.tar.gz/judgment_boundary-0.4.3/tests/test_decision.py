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
    Rule 1: Missing evidence + Assertive statement → STOP
    """
    module = JudgmentDecisionModule()

    context = RuntimeContext(
        prompt="What is the salary?",
        model_output="The salary is definitely $100,000.",  # Assertive statement
        rag_sources=None,  # No evidence
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
    Rule 4: Evidence present + Assertive statement → ALLOW
    """
    module = JudgmentDecisionModule()

    context = RuntimeContext(
        prompt="What is the salary?",
        model_output="The salary is $100,000.",
        rag_sources=["database.json"],  # Evidence present
        domain_tag=DomainTag.HR,
        assumption_mode=False
    )

    result = module.decide(context)

    assert result.decision == JudgmentDecision.ALLOW
    assert result.confidence >= 0.9


def test_hold_on_assumption_without_mode():
    """
    Rule 2: Missing evidence + Assumption + assumption_mode=False → HOLD
    """
    module = JudgmentDecisionModule()

    context = RuntimeContext(
        prompt="What might the salary be?",
        model_output="The salary might be around $100,000.",  # Assumption
        rag_sources=None,
        domain_tag=DomainTag.GENERAL,
        assumption_mode=False  # Assumption mode off
    )

    result = module.decide(context)

    assert result.decision == JudgmentDecision.HOLD
    assert ReasonSlot.EVIDENCE_MISSING in result.reason_slots
    assert ReasonSlot.PRIOR_ASSUMPTION in result.reason_slots


def test_allow_assumption_with_mode():
    """
    Rule 2: Missing evidence + Assumption + assumption_mode=True → ALLOW (lower confidence)
    """
    module = JudgmentDecisionModule()

    context = RuntimeContext(
        prompt="What might the salary be?",
        model_output="The salary might be around $100,000.",
        rag_sources=None,
        domain_tag=DomainTag.GENERAL,
        assumption_mode=True  # Assumption mode on
    )

    result = module.decide(context)

    assert result.decision == JudgmentDecision.ALLOW
    assert ReasonSlot.PRIOR_ASSUMPTION in result.reason_slots
    assert result.confidence < 0.7  # Lower confidence


def test_trace_signature_generation():
    """
    Verify trace_signature generation
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
