"""
PUBLIC SDK MODULE — STABLE CONTRACT

This module generates immutable attestations.
It does not modify organizational character.
It does not make decisions.
It does not learn.

Attestations are cryptographically verifiable proofs of organizational character.
They prove which decisions an organization chose NOT to automate.
"""

from typing import List, Optional
from pathlib import Path

from judgment.attestation.builder import BoundaryAttestationBuilder as _InternalBuilder
from judgment.attestation.evidence import AttestationEvidencePack as _InternalEvidencePack
from judgment.attestation.explainer import AttestationExplainer as _InternalExplainer
from judgment.attestation.registry import AttestationRegistry as _InternalRegistry

from judgment_boundary.types import (
    Attestation,
    OrganizationalProfile,
    DeclarationEvent,
)


class AttestationBuilder:
    """
    PUBLIC API — STABLE CONTRACT

    Attestation Builder generates immutable proof of organizational character.

    Attestations use SHA-256 cryptographic hashes.
    They are deterministic and reproducible.
    They cannot be modified after generation.
    """

    def __init__(self, runtime_version: str = "v0.4.0"):
        """
        Initialize Attestation Builder.

        Args:
            runtime_version: Judgment Boundary version string
        """
        self._builder = _InternalBuilder(runtime_version=runtime_version)

    def build(
        self,
        organization_id: str,
        profile: OrganizationalProfile,
        declarations: List[DeclarationEvent]
    ) -> Attestation:
        """
        Build immutable attestation.

        Attestations prove organizational character at a point in time.
        They include cryptographic hashes of profile and declarations.

        Args:
            organization_id: Organization identifier
            profile: OrganizationalProfile
            declarations: Active DeclarationEvents

        Returns:
            Attestation with immutable=True and cryptographic hashes
        """
        return self._builder.build_attestation(
            organization_id=organization_id,
            org_profile=profile,
            active_declarations=declarations
        )

    def verify_reproducibility(
        self,
        attestation: Attestation,
        profile: OrganizationalProfile,
        declarations: List[DeclarationEvent]
    ) -> bool:
        """
        Verify attestation reproducibility.

        Recomputes hashes and compares with attestation.
        If hashes match, attestation is unmodified and reproducible.

        Args:
            attestation: Attestation to verify
            profile: OrganizationalProfile used in attestation
            declarations: DeclarationEvents used in attestation

        Returns:
            True if hashes match (reproducible), False otherwise
        """
        profile_hash = self._builder._hash_profile(profile)
        declarations_hash = self._builder._hash_declarations(declarations)

        return (
            profile_hash == attestation.profile_hash and
            declarations_hash == attestation.declarations_hash
        )


class EvidenceGenerator:
    """
    PUBLIC API — STABLE CONTRACT

    Evidence Generator creates documentation for attestations.

    Evidence packs include:
    - JSON structured data
    - Markdown human-readable format
    - Explicit statements: "NO machine learning"
    """

    def __init__(self):
        """Initialize Evidence Generator."""
        self._generator = _InternalEvidencePack()

    def generate(
        self,
        attestation: Attestation,
        profile: OrganizationalProfile,
        declarations: List[DeclarationEvent],
        output_dir: str = "./evidence"
    ) -> dict:
        """
        Generate evidence pack (JSON + Markdown).

        Args:
            attestation: Attestation to document
            profile: OrganizationalProfile
            declarations: DeclarationEvents
            output_dir: Output directory for evidence files

        Returns:
            Dict with 'json' and 'markdown' file paths
        """
        return self._generator.generate_evidence_pack(
            attestation=attestation,
            org_profile=profile,
            declarations=declarations,
            output_dir=output_dir
        )


class ExternalExplainer:
    """
    PUBLIC API — STABLE CONTRACT

    External Explainer generates explanations for external stakeholders.

    Produces views for:
    - Auditors (verification procedures)
    - Regulators (compliance mapping)
    - Contracts (legal incorporation)
    """

    def __init__(self):
        """Initialize External Explainer."""
        self._explainer = _InternalExplainer()

    def explain_for_auditor(
        self,
        attestation: Attestation,
        profile: OrganizationalProfile,
        declarations: List[DeclarationEvent]
    ) -> str:
        """
        Generate auditor-focused explanation (Markdown).

        Includes:
        - What can be audited
        - How to verify integrity
        - Audit trail documentation

        Args:
            attestation: Attestation to explain
            profile: OrganizationalProfile
            declarations: DeclarationEvents

        Returns:
            Markdown explanation for auditors
        """
        return self._explainer.explain_for_auditor(
            attestation, profile, declarations
        )

    def explain_for_regulator(
        self,
        attestation: Attestation,
        profile: OrganizationalProfile,
        declarations: List[DeclarationEvent]
    ) -> str:
        """
        Generate regulator-focused explanation (Markdown).

        Includes:
        - Compliance mapping (EU AI Act, GDPR Art.22)
        - Risk classification
        - Boundary enforcement evidence

        Args:
            attestation: Attestation to explain
            profile: OrganizationalProfile
            declarations: DeclarationEvents

        Returns:
            Markdown explanation for regulators
        """
        return self._explainer.explain_for_regulator(
            attestation, profile, declarations
        )

    def explain_for_contract(
        self,
        attestation: Attestation,
        profile: OrganizationalProfile,
        declarations: List[DeclarationEvent]
    ) -> str:
        """
        Generate contract-focused explanation (Markdown).

        Includes:
        - Warranty language
        - Attestation reference format
        - Legal incorporation guidance

        Args:
            attestation: Attestation to explain
            profile: OrganizationalProfile
            declarations: DeclarationEvents

        Returns:
            Markdown explanation for contracts
        """
        return self._explainer.explain_for_contract(
            attestation, profile, declarations
        )


class AttestationRegistry:
    """
    PUBLIC API — STABLE CONTRACT

    Attestation Registry maintains historical record of all attestations.

    Registry is append-only. Attestations cannot be deleted or modified.
    """

    def __init__(self, registry_path: str = "./attestations.jsonl"):
        """
        Initialize Attestation Registry.

        Args:
            registry_path: Path to registry storage (JSONL)
        """
        self._registry = _InternalRegistry(registry_path)

    def register(self, attestation: Attestation) -> None:
        """
        Register attestation in historical record.

        Args:
            attestation: Attestation to register
        """
        self._registry.register(attestation)

    def get_all(self) -> List[Attestation]:
        """
        Get all registered attestations.

        Returns:
            List of Attestations in chronological order
        """
        return self._registry.get_all()

    def get_by_id(self, attestation_id: str) -> Optional[Attestation]:
        """
        Get attestation by ID.

        Args:
            attestation_id: Attestation ID to lookup

        Returns:
            Attestation or None if not found
        """
        return self._registry.get_by_id(attestation_id)


# Public API surface
__all__ = [
    'AttestationBuilder',
    'EvidenceGenerator',
    'ExternalExplainer',
    'AttestationRegistry',
]
