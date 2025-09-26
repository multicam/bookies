#!/usr/bin/env python3
"""
Main entry point for the bookmark management CLI.
"""
import sys
from pathlib import Path

# Add the scripts directory to the Python path
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

# Import and run the CLI
from cli import cli

if __name__ == '__main__':
    cli()