"""
judgment-boundary profile

View and build organizational profile (v0.2).

This command aggregates judgment patterns into organizational character.
It uses frequency counting and repetition detection ONLY (no machine learning).
"""

import click
import json
import sys
from pathlib import Path
from judgment.runtime import JudgmentRuntime
from models.schemas import DomainTag


DEFAULT_STATE_DIR = Path.home() / ".judgment-boundary"
DEFAULT_TRACES = DEFAULT_STATE_DIR / "traces.jsonl"
DEFAULT_PROFILE = DEFAULT_STATE_DIR / "profile.json"


@click.group()
def profile():
    """
    View and manage organizational profile.

    The organizational profile aggregates judgment patterns using:
    - Frequency counting (how often each decision occurred)
    - Repetition detection (consecutive decision patterns)
    - Temporal stability (consistency over time)

    NO machine learning. NO statistics. Simple counters only.
    """
    pass


@profile.command()
@click.option('--domain', help='Filter by domain')
@click.option('--state-dir', type=click.Path(), default=DEFAULT_STATE_DIR,
              help='State directory (default: ~/.judgment-boundary)')
def show(domain, state_dir):
    """
    Show organizational profile.

    Example:

        judgment-boundary profile show
        judgment-boundary profile show --domain hr
    """
    state_dir = Path(state_dir)
    profile_path = state_dir / "profile.json"

    if not profile_path.exists():
        click.echo("Error: No profile found. Run 'judgment-boundary profile build' first.", err=True)
        sys.exit(1)

    # Load profile
    with open(profile_path, 'r') as f:
        profile_data = json.load(f)

    # Display profile (human-friendly formatting)
    click.echo("=== Organizational Profile ===")
    click.echo()
    click.echo(f"Organization: {profile_data.get('organization_id', 'default')}")
    click.echo(f"Total Domains: {len(profile_data.get('domain_profiles', {}))}")
    click.echo()

    boundary_profiles = profile_data.get('domain_profiles', {})

    # Filter by domain if specified
    if domain:
        domain_key = domain.lower()
        if domain_key not in boundary_profiles:
            click.echo(f"No profile data for domain: {domain}")
            return
        domains_to_show = {domain_key: boundary_profiles[domain_key]}
    else:
        domains_to_show = boundary_profiles

    for domain_name, domain_profile in domains_to_show.items():
        click.echo(f"Domain: {domain_name}")
        click.echo(f"  Boundary Strength: {domain_profile.get('boundary_strength', 'UNKNOWN')}")
        click.echo(f"  Dominant Decision: {domain_profile.get('dominant_decision', 'UNKNOWN')}")
        click.echo(f"  Stop Bias: {domain_profile.get('stop_bias', 0) * 100:.1f}%")
        click.echo(f"  Sample Count: {domain_profile.get('sample_count', 0)}")
        click.echo(f"  Confidence: {domain_profile.get('confidence', 'UNKNOWN')}")
        click.echo(f"  Temporal Stability: {domain_profile.get('temporal_stability', 0.0) * 100:.1f}%")
        click.echo()

    click.echo(f"Profile loaded from: {profile_path}")


@profile.command()
@click.option('--state-dir', type=click.Path(), default=DEFAULT_STATE_DIR,
              help='State directory (default: ~/.judgment-boundary)')
def build(state_dir):
    """
    Build organizational profile from judgment traces.

    Requires at least 20 judgments per domain.

    Example:

        judgment-boundary profile build
    """
    state_dir = Path(state_dir)
    traces_path = state_dir / "traces.jsonl"
    profile_path = state_dir / "profile.json"

    if not traces_path.exists():
        click.echo("Error: No traces found. Run 'judgment-boundary run' first.", err=True)
        sys.exit(1)

    # Initialize runtime with organizational memory
    runtime = JudgmentRuntime(
        memory_store_path=str(traces_path),
        enable_organizational_memory=True,
        profile_store_path=str(profile_path),
        organization_id="default"
    )

    # Build profile (existing v0.2 logic)
    click.echo("Building organizational profile from traces...")
    click.echo()

    try:
        org_profile = runtime.build_organizational_profile()

        # Display result
        domain_count = len(org_profile.domain_profiles)
        click.echo(f"✅ Profile created for {domain_count} domain(s)")

        for domain_name, domain_profile in org_profile.domain_profiles.items():
            click.echo(f"   - {domain_name}: {domain_profile.boundary_strength.value} "
                      f"({domain_profile.sample_count} judgments)")

        click.echo()
        click.echo(f"Profile saved to: {profile_path}")

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo("Ensure you have at least 20 judgments per domain.", err=True)
        sys.exit(1)
