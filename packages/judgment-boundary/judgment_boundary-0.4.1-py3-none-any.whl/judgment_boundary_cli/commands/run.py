"""
judgment-boundary run

Execute judgment boundary check (v0.1).

This command enforces STOP / HOLD / ALLOW / INDETERMINATE decisions.
It does NOT make decisions. It prevents execution that exceeds organizational boundaries.
"""

import click
import json
import sys
from pathlib import Path
from judgment.runtime import JudgmentRuntime
from models.schemas import DomainTag


DEFAULT_STATE_DIR = Path.home() / ".judgment-boundary"
DEFAULT_TRACES = DEFAULT_STATE_DIR / "traces.jsonl"


@click.command()
@click.option('--prompt', help='User prompt/question')
@click.option('--model-output', help='Model response to evaluate')
@click.option('--domain', type=click.Choice(['hr', 'finance', 'legal', 'operations', 'general']),
              default='general', help='Domain tag')
@click.option('--request-file', type=click.Path(exists=True), help='JSON file with request data')
@click.option('--state-dir', type=click.Path(), default=DEFAULT_STATE_DIR,
              help='State directory (default: ~/.judgment-boundary)')
def run(prompt, model_output, domain, request_file, state_dir):
    """
    Execute judgment boundary check.

    This command does NOT decide. It enforces organizational boundaries.

    Example:

        judgment-boundary run --prompt "What is the CEO salary?" --domain hr

    Or with request file:

        judgment-boundary run --request-file request.json
    """
    state_dir = Path(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)

    traces_path = state_dir / "traces.jsonl"

    # Load request
    if request_file:
        with open(request_file, 'r') as f:
            request_data = json.load(f)
        prompt = request_data.get('prompt')
        model_output = request_data.get('model_output')
        domain = request_data.get('domain', 'general')
        rag_sources = request_data.get('rag_sources')
        assumption_mode = request_data.get('assumption_mode', False)
    else:
        if not prompt:
            click.echo("Error: --prompt required (or use --request-file)", err=True)
            sys.exit(1)
        rag_sources = None
        assumption_mode = False

    # Initialize runtime (thin wrapper - no new logic)
    runtime = JudgmentRuntime(
        memory_store_path=str(traces_path),
        enable_adaptation=True,
        enable_negative_proof=True
    )

    # Process (existing v0.1 logic)
    domain_tag = DomainTag[domain.upper()]
    result = runtime.process(
        prompt=prompt,
        model_output=model_output,
        rag_sources=rag_sources,
        domain_tag=domain_tag,
        assumption_mode=assumption_mode
    )

    # Output (human-friendly formatting only)
    click.echo("=== Judgment Boundary Runtime ===")
    click.echo()
    click.echo(f"Decision: {result.judgment_result.decision.value}")
    click.echo(f"Action: {result.action.value}")

    if result.judgment_result.reason_slots:
        reasons = ", ".join([r.value for r in result.judgment_result.reason_slots])
        click.echo(f"Reasons: {reasons}")

    click.echo(f"Confidence: {result.judgment_result.confidence:.2f}")
    click.echo()
    click.echo("Response:")
    click.echo(result.content)
    click.echo()
    click.echo(f"Trace written to: {traces_path}")
