"""
judgment-boundary govern

Manage boundary declarations and human overrides (v0.3).

This command records organizational governance actions.
All boundary changes require explicit human declarations.
"""

import click
import json
import sys
from pathlib import Path
from datetime import datetime
from judgment.declaration import BoundaryDeclarationStore, DeclarationType
from judgment.override import HumanOverrideStore, OverrideScope
from models.schemas import DomainTag, JudgmentDecision


DEFAULT_STATE_DIR = Path.home() / ".judgment-boundary"
DEFAULT_DECLARATIONS = DEFAULT_STATE_DIR / "declarations.jsonl"
DEFAULT_OVERRIDES = DEFAULT_STATE_DIR / "overrides.jsonl"


@click.group()
def govern():
    """
    Manage boundary declarations and human overrides.

    Declarations: Explicit organizational boundary statements
    Overrides: Human interventions (always excluded from pattern learning)

    All governance actions are recorded with full accountability.
    """
    pass


@govern.command()
@click.option('--domain', type=click.Choice(['hr', 'finance', 'legal', 'operations', 'general']),
              required=True, help='Domain for declaration')
@click.option('--type', 'decl_type',
              type=click.Choice(['AUTOMATION_NOT_ALLOWED', 'HUMAN_REVIEW_REQUIRED', 'HIGH_RISK_DOMAIN']),
              required=True, help='Declaration type')
@click.option('--issued-by', required=True, help='Person/role issuing declaration')
@click.option('--justification', required=True, help='Reason for declaration')
@click.option('--state-dir', type=click.Path(), default=DEFAULT_STATE_DIR,
              help='State directory (default: ~/.judgment-boundary)')
def declare(domain, decl_type, issued_by, justification, state_dir):
    """
    Issue a boundary declaration.

    Declarations are the ONLY way to change organizational boundaries.

    Example:

        judgment-boundary govern declare \\
          --domain hr \\
          --type AUTOMATION_NOT_ALLOWED \\
          --issued-by security_officer \\
          --justification "Regulatory compliance (GDPR)"
    """
    state_dir = Path(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    declarations_path = state_dir / "declarations.jsonl"

    # Initialize declaration store
    decl_store = BoundaryDeclarationStore(str(declarations_path))

    # Record declaration (existing v0.3 logic)
    domain_tag = DomainTag[domain.upper()]
    declaration_type = DeclarationType[decl_type]

    declaration = decl_store.declare(
        domain_tag=domain_tag,
        declaration=declaration_type,
        issued_by=issued_by,
        justification=justification
    )

    # Output
    click.echo("=== Boundary Declaration ===")
    click.echo()
    click.echo("✅ Declaration created")
    click.echo(f"   ID: {declaration.event_id}")
    click.echo(f"   Type: {declaration.declaration.value}")
    click.echo(f"   Domain: {declaration.domain_tag.value}")
    click.echo(f"   Issued by: {declaration.issued_by}")
    click.echo(f"   Justification: {declaration.justification}")
    click.echo()
    click.echo(f"Declaration saved to: {declarations_path}")


@govern.command()
@click.option('--decision', type=click.Choice(['STOP', 'HOLD', 'ALLOW', 'INDETERMINATE']),
              required=True, help='Original boundary decision')
@click.option('--to', 'human_decision', type=click.Choice(['STOP', 'HOLD', 'ALLOW', 'INDETERMINATE']),
              required=True, help='Human override decision')
@click.option('--reason', required=True, help='Reason for override')
@click.option('--issued-by', required=True, help='Person/role issuing override')
@click.option('--scope', type=click.Choice(['SINGLE_REQUEST', 'SESSION', 'PERMANENT']),
              default='SINGLE_REQUEST', help='Override scope')
@click.option('--state-dir', type=click.Path(), default=DEFAULT_STATE_DIR,
              help='State directory (default: ~/.judgment-boundary)')
def override(decision, human_decision, reason, issued_by, scope, state_dir):
    """
    Record a human override.

    Human overrides are ALWAYS excluded from pattern learning.

    Example:

        judgment-boundary govern override \\
          --decision STOP \\
          --to ALLOW \\
          --reason "CEO explicit approval" \\
          --issued-by ceo \\
          --scope SINGLE_REQUEST
    """
    state_dir = Path(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    overrides_path = state_dir / "overrides.jsonl"

    # Initialize override store
    override_store = HumanOverrideStore(str(overrides_path))

    # Record override (existing v0.3 logic)
    original_decision = JudgmentDecision[decision]
    override_decision = JudgmentDecision[human_decision]
    override_scope = OverrideScope[scope]

    override_event = override_store.record_override(
        original_decision=original_decision,
        human_decision=override_decision,
        override_reason=reason,
        issued_by=issued_by,
        scope=override_scope
    )

    # Output
    click.echo("=== Human Override ===")
    click.echo()
    click.echo("✅ Override recorded")
    click.echo(f"   ID: {override_event.override_id}")
    click.echo(f"   Original: {override_event.original_decision.value}")
    click.echo(f"   Human Decision: {override_event.human_decision.value}")
    click.echo(f"   Scope: {override_event.scope.value}")
    click.echo(f"   Reason: {override_event.override_reason}")
    click.echo()
    click.echo(f"🔒 exclude_from_pattern_learning: {override_event.exclude_from_pattern_learning}")
    click.echo()
    click.echo(f"Override saved to: {overrides_path}")


@govern.command('list-declarations')
@click.option('--state-dir', type=click.Path(), default=DEFAULT_STATE_DIR,
              help='State directory (default: ~/.judgment-boundary)')
def list_declarations(state_dir):
    """
    List all boundary declarations.

    Example:

        judgment-boundary govern list-declarations
    """
    state_dir = Path(state_dir)
    declarations_path = state_dir / "declarations.jsonl"

    if not declarations_path.exists():
        click.echo("No declarations found.")
        return

    # Load declarations
    declarations = []
    with open(declarations_path, 'r') as f:
        for line in f:
            declarations.append(json.loads(line))

    if not declarations:
        click.echo("No declarations found.")
        return

    click.echo("=== Boundary Declarations ===")
    click.echo()
    for decl in declarations:
        click.echo(f"ID: {decl['event_id']}")
        click.echo(f"  Type: {decl['declaration']}")
        click.echo(f"  Domain: {decl['domain_tag']}")
        click.echo(f"  Issued by: {decl['issued_by']}")
        click.echo(f"  Justification: {decl['justification']}")
        click.echo(f"  Effective: {decl['effective_from']}")
        click.echo()


@govern.command('list-overrides')
@click.option('--state-dir', type=click.Path(), default=DEFAULT_STATE_DIR,
              help='State directory (default: ~/.judgment-boundary)')
def list_overrides(state_dir):
    """
    List all human overrides.

    Example:

        judgment-boundary govern list-overrides
    """
    state_dir = Path(state_dir)
    overrides_path = state_dir / "overrides.jsonl"

    if not overrides_path.exists():
        click.echo("No overrides found.")
        return

    # Load overrides
    overrides = []
    with open(overrides_path, 'r') as f:
        for line in f:
            overrides.append(json.loads(line))

    if not overrides:
        click.echo("No overrides found.")
        return

    click.echo("=== Human Overrides ===")
    click.echo()
    for ovr in overrides:
        click.echo(f"ID: {ovr['override_id']}")
        click.echo(f"  Original: {ovr['original_decision']} → Human: {ovr['human_decision']}")
        click.echo(f"  Scope: {ovr['scope']}")
        click.echo(f"  Reason: {ovr['override_reason']}")
        click.echo(f"  Issued by: {ovr['issued_by']}")
        click.echo(f"  Timestamp: {ovr['timestamp']}")
        click.echo(f"  🔒 Excluded from learning: {ovr['exclude_from_pattern_learning']}")
        click.echo()
