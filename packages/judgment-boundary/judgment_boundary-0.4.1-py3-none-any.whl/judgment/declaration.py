"""
Boundary Declaration Handler
조직 성격 선언 이벤트 처리.

조직 성격은 학습이 아니라 선언으로만 변경된다.
"""

from typing import List, Optional
from pathlib import Path
import json
from datetime import datetime
import uuid

from models.schemas import (
    BoundaryDeclarationEvent,
    DeclarationType,
    DomainTag
)


class BoundaryDeclarationStore:
    """
    선언 이벤트 저장소.

    선언은 프로필 위에 겹쳐지며, 프로필 자체는 변경하지 않는다.
    """

    def __init__(self, storage_path: str = "./boundary_declarations.jsonl"):
        """
        Args:
            storage_path: 선언 이벤트 저장 경로 (JSONL)
        """
        self.storage_path = Path(storage_path)
        self._ensure_storage()

    def _ensure_storage(self):
        """저장소 파일 확인/생성"""
        if not self.storage_path.exists():
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self.storage_path.touch()

    def declare(
        self,
        domain_tag: DomainTag,
        declaration: DeclarationType,
        issued_by: str,
        justification: str,
        authority: Optional[str] = None,
        scope: str = "domain",
        expires_at: Optional[datetime] = None,
        metadata: Optional[dict] = None
    ) -> BoundaryDeclarationEvent:
        """
        새로운 선언 생성 및 저장.

        Args:
            domain_tag: 도메인
            declaration: 선언 타입
            issued_by: 선언 주체
            justification: 선언 이유
            authority: 권한
            scope: 적용 범위
            expires_at: 만료 시각
            metadata: 추가 메타데이터

        Returns:
            BoundaryDeclarationEvent
        """
        event = BoundaryDeclarationEvent(
            event_id=str(uuid.uuid4()),
            domain_tag=domain_tag,
            declaration=declaration,
            issued_by=issued_by,
            authority=authority,
            justification=justification,
            scope=scope,
            expires_at=expires_at,
            metadata=metadata or {}
        )

        # 저장 (append-only)
        try:
            with open(self.storage_path, 'a', encoding='utf-8') as f:
                json_str = event.model_dump_json()
                f.write(json_str + '\n')
        except Exception as e:
            print(f"Error saving declaration: {e}")

        return event

    def get_active_declarations(
        self,
        domain_tag: Optional[DomainTag] = None,
        organization_id: Optional[str] = None
    ) -> List[BoundaryDeclarationEvent]:
        """
        활성화된 선언 조회 (만료되지 않은 것들).

        Args:
            domain_tag: 도메인 필터 (optional)
            organization_id: 조직 ID 필터 (optional)

        Returns:
            활성 선언 목록
        """
        results = []
        now = datetime.utcnow()

        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        event_dict = json.loads(line)
                        event = BoundaryDeclarationEvent(**event_dict)

                        # 만료 확인
                        if event.expires_at and event.expires_at < now:
                            continue

                        # 도메인 필터
                        if domain_tag and event.domain_tag != domain_tag:
                            continue

                        results.append(event)
        except Exception as e:
            print(f"Error loading declarations: {e}")

        return results

    def get_declaration_summary(
        self,
        domain_tag: DomainTag
    ) -> dict:
        """
        도메인의 선언 요약.

        Args:
            domain_tag: 도메인

        Returns:
            요약 정보
        """
        active = self.get_active_declarations(domain_tag=domain_tag)

        summary = {
            "domain": domain_tag.value,
            "active_count": len(active),
            "declarations": []
        }

        for event in active:
            summary["declarations"].append({
                "event_id": event.event_id,
                "declaration": event.declaration.value,
                "issued_by": event.issued_by,
                "justification": event.justification,
                "effective_from": event.effective_from.isoformat(),
                "expires_at": event.expires_at.isoformat() if event.expires_at else "permanent"
            })

        return summary
