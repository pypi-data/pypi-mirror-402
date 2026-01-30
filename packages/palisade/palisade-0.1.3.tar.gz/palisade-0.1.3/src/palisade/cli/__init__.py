"""Palisade CLI Package.

This package provides a modular, maintainable structure for the Palisade CLI.

Architecture:
- main.py: Typer application entry point
- commands/: Command implementations (scan, provenance, policy)
- formatters/: Rich-based output formatting
- analyzers/: Result analysis (threats, validators, policy)
- models.py: Pydantic models for type-safe results
- utils.py: Shared utilities

Exit Codes (for CI/CD integration):
- ExitCode.SUCCESS (0): Clean scan, no issues
- ExitCode.WARNING (1): Warnings found, review recommended
- ExitCode.CRITICAL (2): Critical threat detected, pipeline should fail
"""

from palisade import __version__
from palisade.cli.models import ExitCode

__all__ = ["ExitCode", "__version__"]

