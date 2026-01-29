"""
Human Override Handler
사람의 개입을 캡슐로 기록하는 모듈.

Override는 패턴 학습 대상이 아니다. 별도 trace channel에 저장.
"""

from typing import List, Optional
from pathlib import Path
import json
from datetime import datetime
import uuid

from models.schemas import (
    HumanOverrideCapsule,
    OverrideScope,
    JudgmentDecision,
    ReasonSlot,
    DomainTag
)


class HumanOverrideStore:
    """
    Human Override 저장소.

    패턴 학습과 완전히 분리된 trace channel.
    """

    def __init__(self, storage_path: str = "./human_overrides.jsonl"):
        """
        Args:
            storage_path: Override 저장 경로 (JSONL)
        """
        self.storage_path = Path(storage_path)
        self._ensure_storage()

    def _ensure_storage(self):
        """저장소 파일 확인/생성"""
        if not self.storage_path.exists():
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self.storage_path.touch()

    def record_override(
        self,
        original_decision: JudgmentDecision,
        human_decision: JudgmentDecision,
        override_reason: str,
        issued_by: str,
        original_reasons: Optional[List[ReasonSlot]] = None,
        original_confidence: float = 0.0,
        scope: OverrideScope = OverrideScope.SINGLE_REQUEST,
        expires_at: Optional[datetime] = None,
        prompt_signature: Optional[str] = None,
        domain_tag: DomainTag = DomainTag.GENERAL
    ) -> HumanOverrideCapsule:
        """
        Override 기록.

        Args:
            original_decision: 원본 판단
            human_decision: 사람의 결정
            override_reason: Override 이유
            issued_by: Override 주체
            original_reasons: 원본 이유들
            original_confidence: 원본 신뢰도
            scope: Override 범위
            expires_at: 만료 시각
            prompt_signature: 프롬프트 서명
            domain_tag: 도메인

        Returns:
            HumanOverrideCapsule
        """
        capsule = HumanOverrideCapsule(
            override_id=str(uuid.uuid4()),
            original_decision=original_decision,
            original_reasons=original_reasons or [],
            original_confidence=original_confidence,
            human_decision=human_decision,
            override_reason=override_reason,
            scope=scope,
            expires_at=expires_at,
            issued_by=issued_by,
            prompt_signature=prompt_signature,
            domain_tag=domain_tag,
            exclude_from_pattern_learning=True  # 항상 True
        )

        # 저장 (패턴 학습과 분리된 파일)
        try:
            with open(self.storage_path, 'a', encoding='utf-8') as f:
                json_str = capsule.model_dump_json()
                f.write(json_str + '\n')
        except Exception as e:
            print(f"Error recording override: {e}")

        return capsule

    def get_overrides(
        self,
        domain_tag: Optional[DomainTag] = None,
        limit: Optional[int] = None
    ) -> List[HumanOverrideCapsule]:
        """
        Override 기록 조회.

        Args:
            domain_tag: 도메인 필터
            limit: 최대 개수

        Returns:
            Override 목록
        """
        results = []

        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        capsule_dict = json.loads(line)
                        capsule = HumanOverrideCapsule(**capsule_dict)

                        if domain_tag and capsule.domain_tag != domain_tag:
                            continue

                        results.append(capsule)

                        if limit and len(results) >= limit:
                            break
        except Exception as e:
            print(f"Error loading overrides: {e}")

        return results

    def get_override_stats(self, domain_tag: Optional[DomainTag] = None) -> dict:
        """
        Override 통계.

        Args:
            domain_tag: 도메인 필터

        Returns:
            통계 정보
        """
        overrides = self.get_overrides(domain_tag=domain_tag)

        stats = {
            "total_count": len(overrides),
            "by_scope": {},
            "by_original_decision": {},
            "by_human_decision": {}
        }

        for override in overrides:
            # Scope별
            scope = override.scope.value
            stats["by_scope"][scope] = stats["by_scope"].get(scope, 0) + 1

            # 원본 결정별
            orig = override.original_decision.value
            stats["by_original_decision"][orig] = stats["by_original_decision"].get(orig, 0) + 1

            # 사람 결정별
            human = override.human_decision.value
            stats["by_human_decision"][human] = stats["by_human_decision"].get(human, 0) + 1

        return stats
