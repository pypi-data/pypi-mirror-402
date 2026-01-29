"""
Attestation Explainer (External)

Generate explanations for external stakeholders.
- Auditor View
- Regulator View
- Contract Appendix View

Rules:
- No inference
- No legal judgments
- Only describe "how the system operates"
"""

from typing import List

from models.schemas import (
    BoundaryAttestation,
    OrganizationProfile,
    BoundaryDeclarationEvent
)


class AttestationExplainer:
    """
    Attestation external explanation generator.

    All explanations only describe "current state of system".
    """

    def __init__(self):
        pass

    def explain_for_auditor(
        self,
        attestation: BoundaryAttestation,
        org_profile: OrganizationProfile,
        declarations: List[BoundaryDeclarationEvent]
    ) -> str:
        """
        Explanation for auditor (Auditor View).

        Args:
            attestation: Attestation
            org_profile: Organization profile
            declarations: Declaration events

        Returns:
            Explanation for audit document
        """
        lines = []

        lines.append("# Audit Report: Judgment Boundary System")
        lines.append("")
        lines.append(f"**Attestation ID:** {attestation.attestation_id}")
        lines.append(f"**Organization:** {attestation.organization_id}")
        lines.append(f"**Audit Date:** {attestation.effective_at.isoformat()}")
        lines.append("")
        lines.append("## System Overview")
        lines.append("")
        lines.append("This organization operates a **Judgment Boundary System** that:")
        lines.append("")
        lines.append("1. Records all AI judgment decisions externally (not within the model)")
        lines.append("2. Aggregates decision patterns to form an organizational boundary profile")
        lines.append("3. Applies boundary declarations to restrict automated decision-making")
        lines.append("4. Separates human overrides from pattern learning")
        lines.append("")
        lines.append("**The system does NOT automate decisions.**")
        lines.append("**The system documents where the organization chose NOT to automate.**")
        lines.append("")

        lines.append("## Current Boundary Configuration")
        lines.append("")
        for domain, boundary in attestation.boundary_summary.items():
            lines.append(f"- **{domain.upper()}**: {boundary}")
        lines.append("")

        lines.append("## Active Boundary Declarations")
        lines.append("")
        if declarations:
            for decl in declarations:
                lines.append(f"### {decl.declaration.value}")
                lines.append(f"- Domain: {decl.domain_tag.value}")
                lines.append(f"- Issued by: {decl.issued_by}")
                lines.append(f"- Authority: {decl.authority or 'N/A'}")
                lines.append(f"- Justification: {decl.justification}")
                lines.append("")
        else:
            lines.append("No active boundary declarations.")
            lines.append("")

        lines.append("## Verification")
        lines.append("")
        lines.append("This attestation can be verified by:")
        lines.append("")
        lines.append(f"1. Profile hash: `{attestation.profile_hash}`")
        lines.append(f"2. Declarations hash: `{attestation.declarations_hash}`")
        lines.append("3. Recomputing hashes from source data")
        lines.append("")

        return "\n".join(lines)

    def explain_for_regulator(
        self,
        attestation: BoundaryAttestation,
        org_profile: OrganizationProfile,
        declarations: List[BoundaryDeclarationEvent]
    ) -> str:
        """
        Explanation for regulator (Regulator View).

        Args:
            attestation: Attestation
            org_profile: Organization profile
            declarations: Declaration events

        Returns:
            Explanation for regulatory submission
        """
        lines = []

        lines.append("# Regulatory Submission: AI Judgment Boundary System")
        lines.append("")
        lines.append(f"**Submission ID:** {attestation.attestation_id}")
        lines.append(f"**Organization:** {attestation.organization_id}")
        lines.append(f"**Submission Date:** {attestation.generated_at.isoformat()}")
        lines.append(f"**Effective Date:** {attestation.effective_at.isoformat()}")
        lines.append("")

        lines.append("## System Purpose")
        lines.append("")
        lines.append("This system establishes and enforces organizational boundaries for AI-assisted decision-making.")
        lines.append("")
        lines.append("**Key Principle:**")
        lines.append("")
        lines.append("> The system does NOT make automated decisions.")
        lines.append("> The system DOCUMENTS where automated decision-making is prohibited or restricted.")
        lines.append("")

        lines.append("## Boundary Enforcement Mechanisms")
        lines.append("")
        lines.append("### 1. Pattern-Based Boundaries")
        lines.append("")
        lines.append("The system analyzes historical judgment patterns using:")
        lines.append("")
        lines.append("- Frequency counting (no statistical models)")
        lines.append("- Repetition detection (no machine learning)")
        lines.append("- Temporal stability (deterministic)")
        lines.append("")

        lines.append("### 2. Declaration-Based Boundaries")
        lines.append("")
        if declarations:
            lines.append(f"{len(declarations)} active boundary declaration(s):")
            lines.append("")
            for i, decl in enumerate(declarations, 1):
                lines.append(f"{i}. **{decl.declaration.value}** (Domain: {decl.domain_tag.value})")
                lines.append(f"   - Justification: {decl.justification}")
                lines.append(f"   - Authority: {decl.issued_by}")
                lines.append("")
        else:
            lines.append("No boundary declarations currently active.")
            lines.append("")

        lines.append("### 3. Human Override Separation")
        lines.append("")
        lines.append("All human interventions are:")
        lines.append("")
        lines.append("- Recorded in a separate channel")
        lines.append("- Excluded from pattern learning (`exclude_from_pattern_learning=True`)")
        lines.append("- Traceable but not incorporated into automated boundaries")
        lines.append("")

        lines.append("## Compliance Statement")
        lines.append("")
        lines.append("This organization certifies that:")
        lines.append("")
        lines.append("1. All AI judgment boundaries are externally stored and auditable")
        lines.append("2. Boundary changes occur only through explicit declarations")
        lines.append("3. Human oversight is maintained and separated from automation")
        lines.append("4. The system's operation is deterministic and reproducible")
        lines.append("")

        lines.append("---")
        lines.append("")
        lines.append(f"*This submission is immutable and verifiable via attestation ID: {attestation.attestation_id}*")
        lines.append("")

        return "\n".join(lines)

    def explain_for_contract(
        self,
        attestation: BoundaryAttestation,
        org_profile: OrganizationProfile,
        declarations: List[BoundaryDeclarationEvent]
    ) -> str:
        """
        Explanation for contract appendix (Contract Appendix View).

        Args:
            attestation: Attestation
            org_profile: Organization profile
            declarations: Declaration events

        Returns:
            Contract appendix text
        """
        lines = []

        lines.append("# Contract Appendix: AI Judgment Boundaries")
        lines.append("")
        lines.append(f"**Attestation Reference:** {attestation.attestation_id}")
        lines.append(f"**Effective Date:** {attestation.effective_at.isoformat()}")
        lines.append("")

        lines.append("## Article 1: Scope of Automated Decision-Making")
        lines.append("")
        lines.append('The Provider operates an AI Judgment Boundary System ("the System") that restricts automated decision-making as follows:')
        lines.append("")

        for domain, boundary in attestation.boundary_summary.items():
            lines.append(f"- **{domain.upper()} Domain**: {boundary}")
        lines.append("")

        lines.append("## Article 2: Boundary Enforcement")
        lines.append("")
        lines.append("2.1. The System enforces boundaries through:")
        lines.append("")
        lines.append("   (a) Historical pattern analysis (deterministic, no ML)")
        lines.append("   (b) Explicit boundary declarations")
        lines.append("   (c) Human oversight mechanisms")
        lines.append("")

        if declarations:
            lines.append("2.2. Active boundary declarations as of this date:")
            lines.append("")
            for decl in declarations:
                lines.append(f"   - {decl.declaration.value} ({decl.domain_tag.value})")
                lines.append(f"     Justification: {decl.justification}")
            lines.append("")

        lines.append("## Article 3: Verification Rights")
        lines.append("")
        lines.append("3.1. The Client may verify this attestation using:")
        lines.append("")
        lines.append(f"   - Profile Hash: `{attestation.profile_hash[:16]}...`")
        lines.append(f"   - Declarations Hash: `{attestation.declarations_hash[:16]}...`")
        lines.append("")
        lines.append("3.2. Full hash values and verification procedures are available upon request.")
        lines.append("")

        lines.append("## Article 4: Change Notice")
        lines.append("")
        lines.append("4.1. Any changes to boundary configuration will result in a new attestation.")
        lines.append("")
        lines.append("4.2. The Provider commits to notify the Client of new attestations within [X] business days.")
        lines.append("")

        lines.append("---")
        lines.append("")
        lines.append(f"*Attestation ID {attestation.attestation_id} is incorporated by reference.*")
        lines.append("")

        return "\n".join(lines)
