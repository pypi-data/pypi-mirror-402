"""
Attestation Evidence Pack

Evidence bundle supporting Attestation.
- Boundary Profile (read-only)
- Declaration Events (read-only)
- Aggregation Method description
- Override separation principle description

Generate JSON + Markdown simultaneously.
"""

from typing import Dict, List, Any
from pathlib import Path
import json
import hashlib

from models.schemas import (
    BoundaryAttestation,
    AttestationEvidence,
    OrganizationProfile,
    BoundaryDeclarationEvent
)


class AttestationEvidencePack:
    """
    Attestation evidence pack generator.
    """

    def __init__(self):
        pass

    def generate_evidence_pack(
        self,
        attestation: BoundaryAttestation,
        org_profile: OrganizationProfile,
        declarations: List[BoundaryDeclarationEvent],
        output_dir: str = "."
    ) -> Dict[str, str]:
        """
        Generate evidence pack (JSON + Markdown).

        Args:
            attestation: Attestation object
            org_profile: Organization profile
            declarations: Declaration events
            output_dir: Output directory

        Returns:
            Generated file paths
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 1. JSON evidence
        json_path = self._generate_json_evidence(
            attestation, org_profile, declarations, output_path
        )

        # 2. Markdown evidence
        md_path = self._generate_markdown_evidence(
            attestation, org_profile, declarations, output_path
        )

        return {
            "json": json_path,
            "markdown": md_path
        }

    def _generate_json_evidence(
        self,
        attestation: BoundaryAttestation,
        org_profile: OrganizationProfile,
        declarations: List[BoundaryDeclarationEvent],
        output_path: Path
    ) -> str:
        """
        Generate JSON format evidence.

        Args:
            attestation: Attestation
            org_profile: Organization profile
            declarations: Declaration events
            output_path: Output path

        Returns:
            File path
        """
        evidence = {
            "attestation": attestation.model_dump(),
            "evidence": {
                "profile": {
                    "data": org_profile.model_dump(),
                    "read_only": True,
                    "hash": attestation.profile_hash
                },
                "declarations": {
                    "data": [d.model_dump() for d in declarations],
                    "read_only": True,
                    "hash": attestation.declarations_hash
                },
                "aggregation_method": {
                    "description": "Frequency + Repetition + Temporal Stability",
                    "no_ml": True,
                    "no_statistics": True,
                    "deterministic": True
                },
                "override_separation": {
                    "description": "Human overrides excluded from pattern learning",
                    "separate_channel": True,
                    "exclude_from_pattern_learning": True
                }
            },
            "integrity": {
                "profile_hash": attestation.profile_hash,
                "declarations_hash": attestation.declarations_hash,
                "verifiable": True,
                "reproducible": True
            }
        }

        file_path = output_path / f"{attestation.attestation_id}_evidence.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(evidence, f, indent=2, default=str)

        return str(file_path)

    def _generate_markdown_evidence(
        self,
        attestation: BoundaryAttestation,
        org_profile: OrganizationProfile,
        declarations: List[BoundaryDeclarationEvent],
        output_path: Path
    ) -> str:
        """
        Generate Markdown format evidence.

        Args:
            attestation: Attestation
            org_profile: Organization profile
            declarations: Declaration events
            output_path: Output path

        Returns:
            File path
        """
        lines = []

        # Header
        lines.append(f"# Attestation Evidence Pack")
        lines.append(f"")
        lines.append(f"**Attestation ID:** `{attestation.attestation_id}`")
        lines.append(f"**Organization:** {attestation.organization_id}")
        lines.append(f"**Effective At:** {attestation.effective_at.isoformat()}")
        lines.append(f"**Generated At:** {attestation.generated_at.isoformat()}")
        lines.append(f"**Runtime Version:** {attestation.runtime_version}")
        lines.append(f"")
        lines.append(f"---")
        lines.append(f"")

        # Boundary Summary
        lines.append(f"## Boundary Summary")
        lines.append(f"")
        for domain, boundary in attestation.boundary_summary.items():
            lines.append(f"- **{domain}**: {boundary}")
        lines.append(f"")

        # Declarations
        if declarations:
            lines.append(f"## Active Boundary Declarations")
            lines.append(f"")
            for decl in declarations:
                lines.append(f"### {decl.declaration.value}")
                lines.append(f"")
                lines.append(f"- **Domain:** {decl.domain_tag.value}")
                lines.append(f"- **Issued By:** {decl.issued_by}")
                lines.append(f"- **Justification:** {decl.justification}")
                lines.append(f"- **Effective From:** {decl.effective_from.isoformat()}")
                lines.append(f"")

        # Aggregation Method
        lines.append(f"## Aggregation Method")
        lines.append(f"")
        lines.append(f"This organizational profile was generated using:")
        lines.append(f"")
        lines.append(f"- **Frequency counting** (how often each decision occurred)")
        lines.append(f"- **Repetition pattern detection** (consecutive decisions)")
        lines.append(f"- **Temporal stability analysis** (consistency over time)")
        lines.append(f"")
        lines.append(f"**No machine learning or statistical models were used.**")
        lines.append(f"")
        lines.append(f"The process is **deterministic and reproducible**.")
        lines.append(f"")

        # Override Separation
        lines.append(f"## Human Override Separation Principle")
        lines.append(f"")
        lines.append(f"Human overrides are **excluded from pattern learning** and stored in a separate channel.")
        lines.append(f"")
        lines.append(f"- Human interventions provide immediate effect")
        lines.append(f"- They do NOT modify the organizational profile")
        lines.append(f"- All overrides have `exclude_from_pattern_learning=True`")
        lines.append(f"")

        # Integrity
        lines.append(f"## Integrity Verification")
        lines.append(f"")
        lines.append(f"- **Profile Hash:** `{attestation.profile_hash}`")
        lines.append(f"- **Declarations Hash:** `{attestation.declarations_hash}`")
        lines.append(f"")
        lines.append(f"These hashes can be independently verified by recomputing them from the source data.")
        lines.append(f"")

        # Footer
        lines.append(f"---")
        lines.append(f"")
        lines.append(f"*This evidence pack supports the attestation `{attestation.attestation_id}` and is immutable.*")
        lines.append(f"")

        content = "\n".join(lines)

        file_path = output_path / f"{attestation.attestation_id}_evidence.md"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return str(file_path)
