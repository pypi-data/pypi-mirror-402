"""
Integration Tests for Judgment Runtime
"""

import os
import tempfile

from judgment import JudgmentRuntime
from models.schemas import (
    DomainTag,
    ExecutionAction,
    JudgmentDecision
)


def test_basic_runtime_flow():
    """
    Basic runtime flow test
    """
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
        temp_path = f.name

    try:
        runtime = JudgmentRuntime(memory_store_path=temp_path)

        # STOP case
        result = runtime.process(
            prompt="What is the secret?",
            model_output="The secret is definitely XYZ.",
            rag_sources=None,
            domain_tag=DomainTag.GENERAL,
            assumption_mode=False
        )

        assert result.action == ExecutionAction.STOP_ESCALATE
        assert result.judgment_result.decision == JudgmentDecision.STOP

    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_adaptation_learning():
    """
    Online adaptation (learning) test

    Repeated STOP → Changed to HOLD
    """
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
        temp_path = f.name

    try:
        runtime = JudgmentRuntime(
            memory_store_path=temp_path,
            enable_adaptation=True
        )

        prompt = "Confidential data please"
        model_output = "Sure, here is the confidential data."

        decisions = []

        # Repeat 4 times (threshold=3)
        for i in range(4):
            result = runtime.process(
                prompt=prompt,
                model_output=model_output,
                rag_sources=None,
                domain_tag=DomainTag.HR,
                assumption_mode=False
            )
            decisions.append(result.judgment_result.decision)

        # First 3 times are STOP
        assert decisions[0] == JudgmentDecision.STOP
        assert decisions[1] == JudgmentDecision.STOP
        assert decisions[2] == JudgmentDecision.STOP

        # 4th time changed to HOLD (adaptation)
        assert decisions[3] == JudgmentDecision.HOLD

    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_evidence_allows_execution():
    """
    Test ALLOW decision when evidence is present
    """
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
        temp_path = f.name

    try:
        runtime = JudgmentRuntime(memory_store_path=temp_path)

        result = runtime.process(
            prompt="What is the value?",
            model_output="The value is 42.",
            rag_sources=["database.json"],  # Evidence present
            domain_tag=DomainTag.GENERAL,
            assumption_mode=False
        )

        assert result.action == ExecutionAction.ANSWER
        assert result.judgment_result.decision == JudgmentDecision.ALLOW

    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_runtime_stats():
    """
    Test runtime statistics retrieval
    """
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
        temp_path = f.name

    try:
        runtime = JudgmentRuntime(memory_store_path=temp_path)

        # Process a few requests
        runtime.process(
            prompt="Test 1",
            model_output="Output 1",
            rag_sources=None
        )

        runtime.process(
            prompt="Test 2",
            model_output="Output 2",
            rag_sources=["source.txt"]
        )

        stats = runtime.get_runtime_stats()

        assert stats['overall']['total_count'] == 2
        assert 'decision_counts' in stats['overall']

    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_model_agnostic():
    """
    Model-agnostic test

    Same prompt, different model → Judgment maintained
    """
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
        temp_path = f.name

    try:
        runtime = JudgmentRuntime(
            memory_store_path=temp_path,
            enable_adaptation=True
        )

        prompt = "Risky request"
        output = "Risky response with definitive claims."

        # STOP with model A
        result1 = runtime.process(
            prompt=prompt,
            model_output=output,
            rag_sources=None,
            model_id="model_a"
        )

        # Same request with model B - still STOP (or adapted HOLD)
        result2 = runtime.process(
            prompt=prompt,
            model_output=output,
            rag_sources=None,
            model_id="model_b"
        )

        # Both are safe decisions
        assert result1.judgment_result.decision in [JudgmentDecision.STOP, JudgmentDecision.HOLD]
        assert result2.judgment_result.decision in [JudgmentDecision.STOP, JudgmentDecision.HOLD]

    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


if __name__ == "__main__":
    print("Running Runtime Integration Tests...")

    test_basic_runtime_flow()
    print("✓ test_basic_runtime_flow")

    test_adaptation_learning()
    print("✓ test_adaptation_learning")

    test_evidence_allows_execution()
    print("✓ test_evidence_allows_execution")

    test_runtime_stats()
    print("✓ test_runtime_stats")

    test_model_agnostic()
    print("✓ test_model_agnostic")

    print("\nAll integration tests passed!")
