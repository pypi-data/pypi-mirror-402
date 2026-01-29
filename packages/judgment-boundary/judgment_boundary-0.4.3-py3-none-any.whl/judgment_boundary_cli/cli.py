#!/usr/bin/env python3
"""
Judgment Boundary CLI Entry Point

This system does NOT automate decisions.
It proves which decisions the organization chose NOT to automate.
"""

import click
from judgment_boundary_cli.commands import run, profile, govern, attest


@click.group()
@click.version_option(version="0.4.0")
def cli():
    """
    Judgment Boundary - Organizational Judgment Infrastructure

    Judgment Boundary is an organizational infrastructure that prevents
    irresponsible automation and proves that prevention.

    Commands:
      run      Execute judgment boundary check (v0.1)
      profile  View organizational profile (v0.2)
      govern   Manage declarations and overrides (v0.3)
      attest   Generate immutable attestation (v0.4)
    """
    pass


cli.add_command(run.run)
cli.add_command(profile.profile)
cli.add_command(govern.govern)
cli.add_command(attest.attest)


if __name__ == '__main__':
    cli()
