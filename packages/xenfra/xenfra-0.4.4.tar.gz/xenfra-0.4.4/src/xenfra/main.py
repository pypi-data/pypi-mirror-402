"""
Xenfra CLI - Main entry point.

A modern, AI-powered CLI for deploying Python apps to DigitalOcean.
"""

import os

import click
from rich.console import Console

from .commands.auth import auth
from .commands.deployments import delete, deploy, logs, report, status
from .commands.intelligence import analyze, diagnose, init
from .commands.projects import projects
from .commands.security_cmd import security

console = Console()

# Production-ready: API URL is hardcoded as https://api.xenfra.tech
# No configuration needed - works out of the box after pip install


@click.group()
@click.version_option(version="0.2.9")
def cli():
    """
    Xenfra CLI: Deploy Python apps to DigitalOcean with zero configuration.

    Quick Start:
      xenfra auth login     # Authenticate with Xenfra
      xenfra init           # Initialize your project (AI-powered)
      xenfra deploy         # Deploy to DigitalOcean

    Commands:
      auth        Authentication (login, logout, whoami)
      projects    Manage projects (list, show, delete)
      init        Smart project initialization (AI-powered)
      diagnose    Diagnose deployment failures (AI-powered)
      analyze     Analyze codebase without creating config

    For help on a specific command:
      xenfra <command> --help
    """
    # Configure keyring backend
    os.environ["KEYRING_BACKEND"] = "keyrings.alt.file.PlaintextKeyring"

    # Security works silently in the background
    # Only shows warnings if there's an actual security issue


# Register command groups
cli.add_command(auth)
cli.add_command(projects)
cli.add_command(security)

# Register intelligence commands at root level
cli.add_command(init)
cli.add_command(diagnose)
cli.add_command(analyze)

# Register deployment commands at root level
cli.add_command(deploy)
cli.add_command(status)
cli.add_command(logs)
cli.add_command(report)
cli.add_command(delete)


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
