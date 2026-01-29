"""
judgment-boundary attest

Generate immutable attestation (v0.4).

This command creates cryptographically verifiable proof of organizational character.
Attestations are immutable snapshots with SHA-256 hashes.
"""

import click
import json
import sys
from pathlib import Path
from judgment.runtime import JudgmentRuntime
from judgment.attestation.builder import BoundaryAttestationBuilder
from judgment.attestation.evidence import AttestationEvidencePack
from judgment.attestation.explainer import AttestationExplainer
from judgment.attestation.registry import AttestationRegistry
from judgment.declaration import BoundaryDeclarationStore


DEFAULT_STATE_DIR = Path.home() / ".judgment-boundary"
DEFAULT_PROFILE = DEFAULT_STATE_DIR / "profile.json"
DEFAULT_DECLARATIONS = DEFAULT_STATE_DIR / "declarations.jsonl"
DEFAULT_REGISTRY = DEFAULT_STATE_DIR / "attestations.jsonl"
DEFAULT_EVIDENCE_DIR = DEFAULT_STATE_DIR / "evidence"
DEFAULT_EXPLANATIONS_DIR = DEFAULT_STATE_DIR / "explanations"


@click.command()
@click.option('--organization-id', default='default', help='Organization identifier')
@click.option('--output-dir', type=click.Path(), help='Output directory for evidence/explanations')
@click.option('--verify', is_flag=True, help='Verify attestation reproducibility')
@click.option('--state-dir', type=click.Path(), default=DEFAULT_STATE_DIR,
              help='State directory (default: ~/.judgment-boundary)')
def attest(organization_id, output_dir, verify, state_dir):
    """
    Generate immutable attestation.

    Attestations prove organizational character at a point in time.
    They are verifiable by cryptographic hash recomputation.

    Example:

        judgment-boundary attest
        judgment-boundary attest --organization-id my-org
        judgment-boundary attest --verify
    """
    state_dir = Path(state_dir)
    profile_path = state_dir / "profile.json"
    declarations_path = state_dir / "declarations.jsonl"
    registry_path = state_dir / "attestations.jsonl"

    # Determine output directories
    if output_dir:
        output_dir = Path(output_dir)
        evidence_dir = output_dir / "evidence"
        explanations_dir = output_dir / "explanations"
    else:
        evidence_dir = state_dir / "evidence"
        explanations_dir = state_dir / "explanations"

    evidence_dir.mkdir(parents=True, exist_ok=True)
    explanations_dir.mkdir(parents=True, exist_ok=True)

    # Check prerequisites
    if not profile_path.exists():
        click.echo("Error: No profile found. Run 'judgment-boundary profile build' first.", err=True)
        sys.exit(1)

    # Load profile
    with open(profile_path, 'r') as f:
        profile_data = json.load(f)

    # Load declarations (if any)
    declarations = []
    if declarations_path.exists():
        decl_store = BoundaryDeclarationStore(str(declarations_path))
        declarations = decl_store.get_active_declarations()

    # Verify mode
    if verify:
        _verify_attestation(profile_path, declarations_path, registry_path)
        return

    # Generate attestation
    click.echo("=== Judgment Boundary Attestation ===")
    click.echo()
    click.echo("Loading organizational profile...")
    click.echo("Loading active declarations...")
    click.echo()

    # Build attestation (existing v0.4 logic)
    from models.schemas import OrganizationProfile
    org_profile = OrganizationProfile(**profile_data)

    builder = BoundaryAttestationBuilder(runtime_version="v0.4.0")
    attestation = builder.build_attestation(
        organization_id=organization_id,
        org_profile=org_profile,
        active_declarations=declarations
    )

    # Display attestation
    click.echo("✅ Attestation created")
    click.echo(f"   ID: {attestation.attestation_id}")
    click.echo(f"   Organization: {attestation.organization_id}")
    click.echo(f"   Effective At: {attestation.effective_at}")
    click.echo(f"   Profile Hash: {attestation.profile_hash[:16]}...")
    click.echo(f"   Declarations Hash: {attestation.declarations_hash[:16]}...")
    click.echo(f"   Immutable: {attestation.immutable}")
    click.echo()

    # Generate evidence pack
    evidence_gen = AttestationEvidencePack()
    evidence_paths = evidence_gen.generate_evidence_pack(
        attestation=attestation,
        org_profile=org_profile,
        declarations=declarations,
        output_dir=str(evidence_dir)
    )

    click.echo("✅ Evidence pack generated")
    click.echo(f"   JSON: {evidence_paths['json']}")
    click.echo(f"   Markdown: {evidence_paths['markdown']}")
    click.echo()

    # Generate external explanations
    explainer = AttestationExplainer()

    auditor_md = explainer.explain_for_auditor(attestation, org_profile, declarations)
    regulator_md = explainer.explain_for_regulator(attestation, org_profile, declarations)
    contract_md = explainer.explain_for_contract(attestation, org_profile, declarations)

    auditor_path = explanations_dir / f"{attestation.attestation_id}_auditor.md"
    regulator_path = explanations_dir / f"{attestation.attestation_id}_regulator.md"
    contract_path = explanations_dir / f"{attestation.attestation_id}_contract.md"

    with open(auditor_path, 'w') as f:
        f.write(auditor_md)
    with open(regulator_path, 'w') as f:
        f.write(regulator_md)
    with open(contract_path, 'w') as f:
        f.write(contract_md)

    click.echo("✅ External explanations generated")
    click.echo(f"   Auditor: {auditor_path}")
    click.echo(f"   Regulator: {regulator_path}")
    click.echo(f"   Contract: {contract_path}")
    click.echo()

    # Register attestation
    registry = AttestationRegistry(str(registry_path))
    registry.register(attestation)

    total_attestations = len(registry.get_all())
    click.echo("✅ Registry updated")
    click.echo(f"   Total attestations: {total_attestations}")
    click.echo()
    click.echo("🔒 This attestation is immutable and verifiable.")


def _verify_attestation(profile_path, declarations_path, registry_path):
    """Verify attestation reproducibility."""
    if not registry_path.exists():
        click.echo("Error: No attestations found.", err=True)
        sys.exit(1)

    # Load latest attestation
    registry = AttestationRegistry(str(registry_path))
    attestations = registry.get_all()

    if not attestations:
        click.echo("Error: No attestations found.", err=True)
        sys.exit(1)

    latest = attestations[-1]

    click.echo("Verifying attestation reproducibility...")
    click.echo()

    # Load profile
    with open(profile_path, 'r') as f:
        profile_data = json.load(f)
    from models.schemas import OrganizationProfile
    org_profile = OrganizationProfile(**profile_data)

    # Load declarations
    declarations = []
    if declarations_path.exists():
        decl_store = BoundaryDeclarationStore(str(declarations_path))
        declarations = decl_store.get_active_declarations()

    # Recompute hashes
    builder = BoundaryAttestationBuilder(runtime_version="v0.4.0")
    profile_hash = builder._hash_profile(org_profile)
    declarations_hash = builder._hash_declarations(declarations)

    # Verify
    profile_match = profile_hash == latest.profile_hash
    declarations_match = declarations_hash == latest.declarations_hash

    if profile_match:
        click.echo("✅ Profile hash matches: PASS")
    else:
        click.echo("❌ Profile hash mismatch: FAIL", err=True)

    if declarations_match:
        click.echo("✅ Declarations hash matches: PASS")
    else:
        click.echo("❌ Declarations hash mismatch: FAIL", err=True)

    click.echo()

    if profile_match and declarations_match:
        click.echo("✅ Attestation is reproducible")
    else:
        click.echo("❌ Attestation integrity compromised", err=True)
        sys.exit(1)
