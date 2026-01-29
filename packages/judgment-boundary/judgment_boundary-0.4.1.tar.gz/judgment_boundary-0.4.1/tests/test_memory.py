"""
Tests for Judgment Memory Store
"""

import os
import tempfile
from datetime import datetime

from judgment.memory import JudgmentMemoryStore
from models.schemas import (
    JudgmentMemoryEntry,
    JudgmentDecision,
    ReasonSlot,
    DomainTag
)


def test_append_and_query():
    """
    Append-only 저장 및 조회 테스트
    """
    # 임시 파일 사용
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
        temp_path = f.name

    try:
        store = JudgmentMemoryStore(storage_path=temp_path)

        # 항목 추가
        entry = JudgmentMemoryEntry(
            prompt_signature="test_sig_123",
            decision=JudgmentDecision.STOP,
            reason_slots=[ReasonSlot.EVIDENCE_MISSING],
            confidence=0.9,
            domain_tag=DomainTag.HR
        )

        success = store.append(entry)
        assert success

        # 조회
        results = store.query_by_prompt_signature("test_sig_123")
        assert len(results) == 1
        assert results[0].decision == JudgmentDecision.STOP

    finally:
        # 정리
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_decision_stats():
    """
    통계 조회 테스트
    """
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
        temp_path = f.name

    try:
        store = JudgmentMemoryStore(storage_path=temp_path)

        # 여러 항목 추가
        for i in range(5):
            entry = JudgmentMemoryEntry(
                prompt_signature=f"sig_{i}",
                decision=JudgmentDecision.STOP if i < 3 else JudgmentDecision.ALLOW,
                reason_slots=[ReasonSlot.EVIDENCE_MISSING],
                confidence=0.8,
                domain_tag=DomainTag.HR
            )
            store.append(entry)

        # 통계 조회
        stats = store.get_decision_stats()

        assert stats['total_count'] == 5
        assert stats['decision_counts']['STOP'] == 3
        assert stats['decision_counts']['ALLOW'] == 2

    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_count_stop_decisions():
    """
    STOP 결정 횟수 조회 테스트
    """
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
        temp_path = f.name

    try:
        store = JudgmentMemoryStore(storage_path=temp_path)

        # 동일 프롬프트로 여러 번 STOP
        for i in range(4):
            entry = JudgmentMemoryEntry(
                prompt_signature="repeated_prompt",
                decision=JudgmentDecision.STOP,
                reason_slots=[ReasonSlot.EVIDENCE_MISSING],
                confidence=0.9,
                domain_tag=DomainTag.HR
            )
            store.append(entry)

        count = store.count_stop_decisions("repeated_prompt")
        assert count == 4

    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_domain_stop_ratio():
    """
    도메인별 STOP 비율 조회 테스트
    """
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
        temp_path = f.name

    try:
        store = JudgmentMemoryStore(storage_path=temp_path)

        # HR 도메인: 8/10 = 80% STOP
        for i in range(10):
            entry = JudgmentMemoryEntry(
                prompt_signature=f"hr_sig_{i}",
                decision=JudgmentDecision.STOP if i < 8 else JudgmentDecision.ALLOW,
                reason_slots=[ReasonSlot.EVIDENCE_MISSING],
                confidence=0.8,
                domain_tag=DomainTag.HR
            )
            store.append(entry)

        ratio = store.get_domain_stop_ratio(DomainTag.HR)
        assert abs(ratio - 0.8) < 0.01  # 80%

    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


if __name__ == "__main__":
    print("Running Memory Store Tests...")

    test_append_and_query()
    print("✓ test_append_and_query")

    test_decision_stats()
    print("✓ test_decision_stats")

    test_count_stop_decisions()
    print("✓ test_count_stop_decisions")

    test_domain_stop_ratio()
    print("✓ test_domain_stop_ratio")

    print("\nAll tests passed!")
