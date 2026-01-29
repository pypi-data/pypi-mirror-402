"""
PUBLIC SDK MODULE — STABLE CONTRACT

This module manages boundary declarations and human overrides.
It does not automate decisions.
It does not learn from overrides.
It does not modify organizational profiles automatically.

All boundary changes require explicit human declarations.
Human overrides are ALWAYS excluded from pattern learning.
"""

from typing import List, Optional
from datetime import datetime

from judgment.declaration import BoundaryDeclarationStore as _InternalDeclarationStore
from judgment.override import HumanOverrideStore as _InternalOverrideStore

from judgment_boundary.types import (
    DeclarationEvent,
    HumanOverride,
    DomainTag,
    DeclarationType,
    Decision,
    OverrideScope,
)


class DeclarationStore:
    """
    PUBLIC API — STABLE CONTRACT

    Boundary Declaration Store manages explicit organizational statements.

    Declarations are the ONLY way to change organizational boundaries.
    They do NOT automatically modify profiles.
    """

    def __init__(self, storage_path: str = "./boundary_declarations.jsonl"):
        """
        Initialize Declaration Store.

        Args:
            storage_path: Path to declaration event storage (JSONL)
        """
        self._store = _InternalDeclarationStore(storage_path)

    def declare(
        self,
        domain: DomainTag,
        declaration_type: DeclarationType,
        issued_by: str,
        justification: str,
        authority: Optional[str] = None
    ) -> DeclarationEvent:
        """
        Issue a boundary declaration.

        Declarations are explicit organizational statements about boundaries.
        They require human accountability (issued_by, justification).

        Args:
            domain: Domain for declaration
            declaration_type: Type of declaration
            issued_by: Person/role issuing declaration
            justification: Reason for declaration
            authority: Optional authority reference

        Returns:
            DeclarationEvent with unique ID and timestamp
        """
        return self._store.declare(
            domain_tag=domain,
            declaration=declaration_type,
            issued_by=issued_by,
            justification=justification,
            authority=authority
        )

    def get_active_declarations(
        self,
        domain: Optional[DomainTag] = None
    ) -> List[DeclarationEvent]:
        """
        Get active (non-expired) declarations.

        Args:
            domain: Optional domain filter

        Returns:
            List of active DeclarationEvents
        """
        all_declarations = self._store.get_active_declarations()

        if domain is None:
            return all_declarations

        # Filter by domain
        return [
            d for d in all_declarations
            if d.domain_tag == domain
        ]


class OverrideStore:
    """
    PUBLIC API — STABLE CONTRACT

    Human Override Store records human interventions.

    Overrides are ALWAYS excluded from pattern learning.
    They provide immediate effect but do NOT modify organizational profiles.
    """

    def __init__(self, storage_path: str = "./human_overrides.jsonl"):
        """
        Initialize Override Store.

        Args:
            storage_path: Path to override event storage (JSONL)
        """
        self._store = _InternalOverrideStore(storage_path)

    def record(
        self,
        original_decision: Decision,
        human_decision: Decision,
        override_reason: str,
        issued_by: str,
        scope: OverrideScope = OverrideScope.SINGLE_REQUEST,
        domain: DomainTag = DomainTag.GENERAL
    ) -> HumanOverride:
        """
        Record a human override.

        Human overrides are ALWAYS excluded from pattern learning.
        They represent human judgment, not organizational patterns.

        Args:
            original_decision: Original boundary decision
            human_decision: Human override decision
            override_reason: Reason for override
            issued_by: Person/role issuing override
            scope: Override scope (SINGLE_REQUEST | SESSION | PERMANENT)
            domain: Domain tag

        Returns:
            HumanOverride with exclude_from_pattern_learning=True
        """
        return self._store.record_override(
            original_decision=original_decision,
            human_decision=human_decision,
            override_reason=override_reason,
            issued_by=issued_by,
            scope=scope,
            domain_tag=domain
        )

    def get_all_overrides(self) -> List[HumanOverride]:
        """
        Get all recorded overrides.

        Returns:
            List of HumanOverride events
        """
        return self._store.get_all_overrides()


# Public API surface
__all__ = [
    'DeclarationStore',
    'OverrideStore',
]
