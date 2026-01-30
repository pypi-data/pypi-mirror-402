"""Command Implementations for Palisade CLI.

This package provides implementations for all CLI commands:
- scan.py: File and directory scanning
- provenance.py: Signature verification and provenance tracking
- policy.py: Policy template management
"""

from palisade.cli.commands.scan import (
    create_scanner,
    scan_file,
    scan_directory,
)
from palisade.cli.commands.provenance import (
    verify_sigstore,
    verify_slsa,
    track_provenance,
)
from palisade.cli.commands.policy import (
    list_templates,
    show_template_details,
    generate_policy,
    validate_policy,
    create_override_template,
)

__all__ = [
    # Scan commands
    "create_scanner",
    "scan_file",
    "scan_directory",
    # Provenance commands
    "verify_sigstore",
    "verify_slsa",
    "track_provenance",
    # Policy commands
    "list_templates",
    "show_template_details",
    "generate_policy",
    "validate_policy",
    "create_override_template",
]


