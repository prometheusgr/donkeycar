"""
Core CLI framework using Click.

This module provides the main CLI entry point and command groups for:
- System/project setup
- Car management (create, configure, run)
- Data management (capture, convert, export)
- Model training (train, evaluate, deploy)
"""

import click
import sys
from pathlib import Path

# Import command groups
from .commands import car, data, training, system


@click.group(invoke_without_command=True)
@click.version_option()
@click.pass_context
def cli(ctx):
    """
    DonkeyCar CLI - Unified command interface for DonkeyCar projects.

    Organize your DonkeyCar workflow across three main areas:

    \b
    car       - Create, configure, and manage car instances
    data      - Capture, process, and manage training data
    training  - Train, evaluate, and deploy models
    system    - System setup and utilities

    Use 'donkey <command> --help' for more information on each command.
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# Add command groups
cli.add_command(car.car)
cli.add_command(data.data)
cli.add_command(training.training)
cli.add_command(system.system)


def cli_main():
    """Entry point for the CLI application."""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n\nInterrupted by user.", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
