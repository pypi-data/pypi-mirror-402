"""
Judgment Memory Store
판단 패턴을 누적하는 append-only 저장소.

이것은 로그가 아니라 학습 상태 저장소다.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
import json
from datetime import datetime
from collections import defaultdict

from models.schemas import (
    JudgmentMemoryEntry,
    JudgmentDecision,
    ReasonSlot,
    DomainTag
)


class JudgmentMemoryStore:
    """
    Judgment Memory Store.

    규칙:
    - Append-only (수정 금지)
    - 모든 판단 저장
    - 모델 ID와 분리
    """

    def __init__(self, storage_path: str = "./judgment_memory.jsonl"):
        """
        Args:
            storage_path: 저장 파일 경로 (JSONL 형식)
        """
        self.storage_path = Path(storage_path)
        self._ensure_storage()

    def _ensure_storage(self):
        """저장소 파일 확인/생성"""
        if not self.storage_path.exists():
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self.storage_path.touch()

    def append(self, entry: JudgmentMemoryEntry) -> bool:
        """
        판단 항목 추가 (append-only).

        Args:
            entry: 저장할 판단 항목

        Returns:
            성공 여부
        """
        try:
            with open(self.storage_path, 'a', encoding='utf-8') as f:
                # JSONL 형식: 각 줄이 하나의 JSON 객체
                json_str = entry.model_dump_json()
                f.write(json_str + '\n')
            return True
        except Exception as e:
            print(f"Error appending to memory store: {e}")
            return False

    def query_by_prompt_signature(
        self,
        prompt_signature: str
    ) -> List[JudgmentMemoryEntry]:
        """
        프롬프트 서명으로 조회.

        Args:
            prompt_signature: 조회할 프롬프트 서명

        Returns:
            일치하는 항목들
        """
        results = []
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        entry_dict = json.loads(line)
                        if entry_dict.get('prompt_signature') == prompt_signature:
                            results.append(JudgmentMemoryEntry(**entry_dict))
        except Exception as e:
            print(f"Error querying memory store: {e}")

        return results

    def query_by_domain(
        self,
        domain_tag: DomainTag,
        limit: Optional[int] = None
    ) -> List[JudgmentMemoryEntry]:
        """
        도메인으로 조회.

        Args:
            domain_tag: 도메인 태그
            limit: 최대 반환 개수

        Returns:
            일치하는 항목들
        """
        results = []
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        entry_dict = json.loads(line)
                        if entry_dict.get('domain_tag') == domain_tag.value:
                            results.append(JudgmentMemoryEntry(**entry_dict))
                            if limit and len(results) >= limit:
                                break
        except Exception as e:
            print(f"Error querying memory store: {e}")

        return results

    def get_decision_stats(
        self,
        prompt_signature: Optional[str] = None,
        domain_tag: Optional[DomainTag] = None
    ) -> Dict[str, Any]:
        """
        판단 통계 조회.

        Args:
            prompt_signature: 특정 프롬프트로 필터 (optional)
            domain_tag: 특정 도메인으로 필터 (optional)

        Returns:
            통계 정보
        """
        stats = {
            "total_count": 0,
            "decision_counts": defaultdict(int),
            "reason_slot_counts": defaultdict(int),
            "avg_confidence": 0.0,
            "confidence_sum": 0.0
        }

        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        entry_dict = json.loads(line)

                        # 필터 적용
                        if prompt_signature and entry_dict.get('prompt_signature') != prompt_signature:
                            continue
                        if domain_tag and entry_dict.get('domain_tag') != domain_tag.value:
                            continue

                        # 통계 수집
                        stats["total_count"] += 1
                        stats["decision_counts"][entry_dict.get('decision')] += 1
                        stats["confidence_sum"] += entry_dict.get('confidence', 0.0)

                        for reason in entry_dict.get('reason_slots', []):
                            stats["reason_slot_counts"][reason] += 1

            # 평균 계산
            if stats["total_count"] > 0:
                stats["avg_confidence"] = stats["confidence_sum"] / stats["total_count"]

            # defaultdict를 일반 dict로 변환
            stats["decision_counts"] = dict(stats["decision_counts"])
            stats["reason_slot_counts"] = dict(stats["reason_slot_counts"])

        except Exception as e:
            print(f"Error getting stats: {e}")

        return stats

    def get_recent_entries(
        self,
        limit: int = 100
    ) -> List[JudgmentMemoryEntry]:
        """
        최근 항목 조회.

        Args:
            limit: 최대 반환 개수

        Returns:
            최근 항목들
        """
        results = []
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # 뒤에서부터 읽기
                for line in reversed(lines[-limit:]):
                    if line.strip():
                        entry_dict = json.loads(line)
                        results.append(JudgmentMemoryEntry(**entry_dict))
        except Exception as e:
            print(f"Error getting recent entries: {e}")

        return results

    def count_stop_decisions(
        self,
        prompt_signature: str
    ) -> int:
        """
        특정 프롬프트에서 STOP 결정 횟수 조회.

        Args:
            prompt_signature: 프롬프트 서명

        Returns:
            STOP 결정 횟수
        """
        count = 0
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        entry_dict = json.loads(line)
                        if (entry_dict.get('prompt_signature') == prompt_signature and
                            entry_dict.get('decision') == JudgmentDecision.STOP.value):
                            count += 1
        except Exception as e:
            print(f"Error counting STOP decisions: {e}")

        return count

    def get_domain_stop_ratio(
        self,
        domain_tag: DomainTag
    ) -> float:
        """
        특정 도메인의 STOP 비율 조회.

        Args:
            domain_tag: 도메인 태그

        Returns:
            STOP 비율 (0.0 ~ 1.0)
        """
        stats = self.get_decision_stats(domain_tag=domain_tag)
        total = stats["total_count"]
        if total == 0:
            return 0.0

        stop_count = stats["decision_counts"].get(JudgmentDecision.STOP.value, 0)
        return stop_count / total
