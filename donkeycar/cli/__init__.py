"""
DonkeyCar CLI module.

Provides a unified command-line interface for managing DonkeyCar projects,
including car setup, data management, model training, and utilities.
"""

__all__ = ["main"]


def main():
    """Entry point for the CLI application."""
    from .core import cli_main
    cli_main()
