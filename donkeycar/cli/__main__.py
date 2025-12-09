#!/usr/bin/env python3
"""
DonkeyCar CLI - Standalone Entry Point

This script can be run directly or installed as a console script.
Usage:
  python -m donkeycar.cli <command> [options]
  donkey <command> [options]  (if installed)
"""

from donkeycar.cli import main

if __name__ == '__main__':
    main()
