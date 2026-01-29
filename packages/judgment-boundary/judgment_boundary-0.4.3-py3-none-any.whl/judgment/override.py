"""
Human Override Handler
Module recording human intervention as capsules.

Overrides are not subject to pattern learning. Stored in separate trace channel.
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
    Human Override storage.

    Trace channel completely separated from pattern learning.
    """

    def __init__(self, storage_path: str = "./human_overrides.jsonl"):
        """
        Args:
            storage_path: Override storage path (JSONL)
        """
        self.storage_path = Path(storage_path)
        self._ensure_storage()

    def _ensure_storage(self):
        """Check/create storage file"""
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
        Record override.

        Args:
            original_decision: Original judgment
            human_decision: Human decision
            override_reason: Override reason
            issued_by: Override issuer
            original_reasons: Original reasons
            original_confidence: Original confidence
            scope: Override scope
            expires_at: Expiration time
            prompt_signature: Prompt signature
            domain_tag: Domain

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
            exclude_from_pattern_learning=True  # Always True
        )

        # Save (file separated from pattern learning)
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
        Query override records.

        Args:
            domain_tag: Domain filter
            limit: Maximum count

        Returns:
            Override list
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
        Override statistics.

        Args:
            domain_tag: Domain filter

        Returns:
            Statistics information
        """
        overrides = self.get_overrides(domain_tag=domain_tag)

        stats = {
            "total_count": len(overrides),
            "by_scope": {},
            "by_original_decision": {},
            "by_human_decision": {}
        }

        for override in overrides:
            # By scope
            scope = override.scope.value
            stats["by_scope"][scope] = stats["by_scope"].get(scope, 0) + 1

            # By original decision
            orig = override.original_decision.value
            stats["by_original_decision"][orig] = stats["by_original_decision"].get(orig, 0) + 1

            # By human decision
            human = override.human_decision.value
            stats["by_human_decision"][human] = stats["by_human_decision"].get(human, 0) + 1

        return stats
