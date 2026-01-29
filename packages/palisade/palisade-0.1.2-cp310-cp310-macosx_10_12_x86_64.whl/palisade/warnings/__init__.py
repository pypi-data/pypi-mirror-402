"""Warning type catalog for Palisade validators.

This module provides:
- WarningType and SarifMetadata dataclasses for type-safe warning definitions
- YAML-based warning catalog loading
- Auto-generated Python constants for warning IDs

Note: This describes warning METADATA only (for SARIF output).
Detection patterns are defined in validator Python code.
"""

from palisade.warnings.models import WarningType, SarifMetadata, Severity
from palisade.warnings.catalog import WarningCatalog, WARNINGS, WarningIds

__all__ = [
    "WarningType",
    "SarifMetadata", 
    "Severity",
    "WarningCatalog",
    "WARNINGS",
    "WarningIds",
]
