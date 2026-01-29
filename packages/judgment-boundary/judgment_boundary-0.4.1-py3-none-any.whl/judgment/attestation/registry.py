"""
Attestation Registry (Local)

발급된 Attestation 목록 관리.
- 최신/과거 Attestation 조회
- Runtime 재시작 후에도 유지
"""

from typing import List, Optional
from pathlib import Path
import json
from datetime import datetime

from models.schemas import BoundaryAttestation


class AttestationRegistry:
    """
    Attestation 레지스트리.

    발급된 모든 attestation을 기록하고 조회.
    """

    def __init__(self, storage_path: str = "./attestation_registry.jsonl"):
        """
        Args:
            storage_path: 레지스트리 저장 경로 (JSONL)
        """
        self.storage_path = Path(storage_path)
        self._ensure_storage()

    def _ensure_storage(self):
        """저장소 파일 확인/생성"""
        if not self.storage_path.exists():
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self.storage_path.touch()

    def register(self, attestation: BoundaryAttestation) -> bool:
        """
        Attestation 등록.

        Args:
            attestation: 등록할 attestation

        Returns:
            성공 여부
        """
        try:
            with open(self.storage_path, 'a', encoding='utf-8') as f:
                json_str = attestation.model_dump_json()
                f.write(json_str + '\n')
            return True
        except Exception as e:
            print(f"Error registering attestation: {e}")
            return False

    def get_latest(
        self,
        organization_id: Optional[str] = None
    ) -> Optional[BoundaryAttestation]:
        """
        최신 attestation 조회.

        Args:
            organization_id: 조직 ID 필터 (optional)

        Returns:
            최신 attestation or None
        """
        attestations = self.get_all(organization_id=organization_id)
        if not attestations:
            return None

        # effective_at 기준 정렬
        sorted_attestations = sorted(
            attestations,
            key=lambda a: a.effective_at,
            reverse=True
        )

        return sorted_attestations[0]

    def get_all(
        self,
        organization_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[BoundaryAttestation]:
        """
        모든 attestation 조회.

        Args:
            organization_id: 조직 ID 필터
            limit: 최대 개수

        Returns:
            Attestation 목록
        """
        results = []

        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        att_dict = json.loads(line)
                        att = BoundaryAttestation(**att_dict)

                        if organization_id and att.organization_id != organization_id:
                            continue

                        results.append(att)

                        if limit and len(results) >= limit:
                            break
        except Exception as e:
            print(f"Error loading attestations: {e}")

        return results

    def get_by_id(self, attestation_id: str) -> Optional[BoundaryAttestation]:
        """
        ID로 attestation 조회.

        Args:
            attestation_id: Attestation ID

        Returns:
            Attestation or None
        """
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        att_dict = json.loads(line)
                        if att_dict.get('attestation_id') == attestation_id:
                            return BoundaryAttestation(**att_dict)
        except Exception as e:
            print(f"Error finding attestation: {e}")

        return None

    def get_history(
        self,
        organization_id: str,
        limit: int = 10
    ) -> List[BoundaryAttestation]:
        """
        조직의 attestation 이력 조회.

        Args:
            organization_id: 조직 ID
            limit: 최대 개수

        Returns:
            Attestation 이력 (최신순)
        """
        attestations = self.get_all(organization_id=organization_id)

        # effective_at 기준 정렬 (최신순)
        sorted_attestations = sorted(
            attestations,
            key=lambda a: a.effective_at,
            reverse=True
        )

        return sorted_attestations[:limit]

    def get_summary(self, organization_id: Optional[str] = None) -> dict:
        """
        레지스트리 요약.

        Args:
            organization_id: 조직 ID 필터

        Returns:
            요약 정보
        """
        attestations = self.get_all(organization_id=organization_id)

        summary = {
            "total_count": len(attestations),
            "latest": None,
            "oldest": None
        }

        if attestations:
            sorted_by_date = sorted(attestations, key=lambda a: a.effective_at)
            summary["oldest"] = {
                "id": sorted_by_date[0].attestation_id,
                "effective_at": sorted_by_date[0].effective_at.isoformat()
            }
            summary["latest"] = {
                "id": sorted_by_date[-1].attestation_id,
                "effective_at": sorted_by_date[-1].effective_at.isoformat()
            }

        return summary
