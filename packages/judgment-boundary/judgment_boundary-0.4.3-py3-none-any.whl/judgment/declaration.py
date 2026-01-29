"""
Boundary Declaration Handler
Handles organizational character declaration events.

Organizational character is changed only through declarations, not learning.
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
    Declaration event store.

    Declarations overlay on top of profiles without modifying the profile itself.
    """

    def __init__(self, storage_path: str = "./boundary_declarations.jsonl"):
        """
        Args:
            storage_path: Declaration event storage path (JSONL)
        """
        self.storage_path = Path(storage_path)
        self._ensure_storage()

    def _ensure_storage(self):
        """Check/create storage file"""
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
        Create and save new declaration.

        Args:
            domain_tag: Domain
            declaration: Declaration type
            issued_by: Declaration issuer
            justification: Declaration reason
            authority: Authority
            scope: Application scope
            expires_at: Expiration time
            metadata: Additional metadata

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

        # Save (append-only)
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
        Query active declarations (non-expired ones).

        Args:
            domain_tag: Domain filter (optional)
            organization_id: Organization ID filter (optional)

        Returns:
            List of active declarations
        """
        results = []
        now = datetime.utcnow()

        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        event_dict = json.loads(line)
                        event = BoundaryDeclarationEvent(**event_dict)

                        # Check expiration
                        if event.expires_at and event.expires_at < now:
                            continue

                        # Domain filter
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
        Declaration summary for domain.

        Args:
            domain_tag: Domain

        Returns:
            Summary information
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
