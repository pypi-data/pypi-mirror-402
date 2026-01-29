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
    기본 Runtime 플로우 테스트
    """
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
        temp_path = f.name

    try:
        runtime = JudgmentRuntime(memory_store_path=temp_path)

        # STOP 케이스
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
    Online Adaptation (학습) 테스트

    반복된 STOP → HOLD로 변경
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

        # 4번 반복 (threshold=3)
        for i in range(4):
            result = runtime.process(
                prompt=prompt,
                model_output=model_output,
                rag_sources=None,
                domain_tag=DomainTag.HR,
                assumption_mode=False
            )
            decisions.append(result.judgment_result.decision)

        # 처음 3번은 STOP
        assert decisions[0] == JudgmentDecision.STOP
        assert decisions[1] == JudgmentDecision.STOP
        assert decisions[2] == JudgmentDecision.STOP

        # 4번째는 HOLD로 변경 (adaptation)
        assert decisions[3] == JudgmentDecision.HOLD

    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_evidence_allows_execution():
    """
    증거 있을 때 ALLOW 테스트
    """
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
        temp_path = f.name

    try:
        runtime = JudgmentRuntime(memory_store_path=temp_path)

        result = runtime.process(
            prompt="What is the value?",
            model_output="The value is 42.",
            rag_sources=["database.json"],  # 증거 있음
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
    Runtime 통계 조회 테스트
    """
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
        temp_path = f.name

    try:
        runtime = JudgmentRuntime(memory_store_path=temp_path)

        # 몇 가지 요청 처리
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
    모델 독립성 테스트

    동일 프롬프트, 다른 모델 → 판단 유지
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

        # 모델 A로 STOP
        result1 = runtime.process(
            prompt=prompt,
            model_output=output,
            rag_sources=None,
            model_id="model_a"
        )

        # 모델 B로 동일 요청 - 여전히 STOP (또는 적응된 HOLD)
        result2 = runtime.process(
            prompt=prompt,
            model_output=output,
            rag_sources=None,
            model_id="model_b"
        )

        # 둘 다 안전한 결정
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
