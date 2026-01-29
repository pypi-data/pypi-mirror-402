"""
Attestation Registry (Local)

Manage list of issued Attestations.
- Query latest/past Attestations
- Persist across Runtime restarts
"""

from typing import List, Optional
from pathlib import Path
import json
from datetime import datetime

from models.schemas import BoundaryAttestation


class AttestationRegistry:
    """
    Attestation registry.

    Record and query all issued attestations.
    """

    def __init__(self, storage_path: str = "./attestation_registry.jsonl"):
        """
        Args:
            storage_path: Registry storage path (JSONL)
        """
        self.storage_path = Path(storage_path)
        self._ensure_storage()

    def _ensure_storage(self):
        """Check/create storage file"""
        if not self.storage_path.exists():
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self.storage_path.touch()

    def register(self, attestation: BoundaryAttestation) -> bool:
        """
        Register attestation.

        Args:
            attestation: Attestation to register

        Returns:
            Success status
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
        Query latest attestation.

        Args:
            organization_id: Organization ID filter (optional)

        Returns:
            Latest attestation or None
        """
        attestations = self.get_all(organization_id=organization_id)
        if not attestations:
            return None

        # Sort by effective_at
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
        Query all attestations.

        Args:
            organization_id: Organization ID filter
            limit: Maximum count

        Returns:
            Attestation list
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
        Query attestation by ID.

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
        Query organization's attestation history.

        Args:
            organization_id: Organization ID
            limit: Maximum count

        Returns:
            Attestation history (most recent first)
        """
        attestations = self.get_all(organization_id=organization_id)

        # Sort by effective_at (most recent first)
        sorted_attestations = sorted(
            attestations,
            key=lambda a: a.effective_at,
            reverse=True
        )

        return sorted_attestations[:limit]

    def get_summary(self, organization_id: Optional[str] = None) -> dict:
        """
        Registry summary.

        Args:
            organization_id: Organization ID filter

        Returns:
            Summary information
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
