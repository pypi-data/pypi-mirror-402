"""Pydantic Models for CLI Type Safety.

This module defines type-safe models for CLI arguments and results.
Using Pydantic ensures validation and provides IDE autocomplete.
"""

from enum import IntEnum, Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ExitCode(IntEnum):
    """Standard exit codes for CI/CD integration.
    
    Follows Unix conventions and sysexits.h standards:
    - 0: Success
    - 1: General warning/error requiring attention
    - 2: Critical failure (security threat detected)
    
    Usage in CI/CD pipelines:
        - Exit 0: Pipeline continues, no issues found
        - Exit 1: Pipeline may continue with warnings, review recommended
        - Exit 2: Pipeline should fail, critical security issue detected
    
    Example:
        ```yaml
        # GitHub Actions example
        - name: Scan model
          run: palisade scan model.safetensors
          continue-on-error: false  # Exit 1 or 2 will fail the job
        ```
    """
    SUCCESS = 0           # Clean scan, no issues
    WARNING = 1           # Warnings found, quarantine recommended, review needed
    CRITICAL = 2          # Critical threat detected, deny policy triggered


class OutputFormat(str, Enum):
    """Output format options."""
    HUMAN = "human"
    JSON = "json"
    SARIF = "sarif"


class StrictnessLevel(str, Enum):
    """Provenance verification strictness."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ScanOptions(BaseModel):
    """Options for scan command."""
    file_path: Path
    max_memory: int = 512
    policy: Optional[str] = None
    format: OutputFormat = OutputFormat.HUMAN
    output: Optional[Path] = None
    verbose: bool = False
    max_warnings: int = 5


class ProvenanceOptions(BaseModel):
    """Options for provenance commands."""
    model_path: Path
    strictness: StrictnessLevel = StrictnessLevel.MEDIUM
    format: OutputFormat = OutputFormat.HUMAN
    output: Optional[Path] = None
    verbose: bool = False
    max_warnings: int = 10
    public_key: Optional[Path] = None  # For sigstore verification


class ScanResult(BaseModel):
    """Type-safe scan result for a single file."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    file_path: str
    status: str
    error: Optional[str] = None
    reason: Optional[str] = None
    warnings: List[Dict[str, Any]] = Field(default_factory=list)
    summary: Optional[Dict[str, Any]] = None
    file_info: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    validation_results: Optional[List[Dict[str, Any]]] = None
    git_lfs_info: Optional[Dict[str, Any]] = None
    cli_scan_time: Optional[float] = None
    scan_time_seconds: Optional[float] = None
    policy: Optional[Dict[str, Any]] = None  # Policy evaluation results
    processing_info: Optional[Dict[str, Any]] = None  # Processing/format info


class DirectoryScanResult(BaseModel):
    """Type-safe scan result for a directory."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    directory: str
    status: str
    error: Optional[str] = None
    files: List[Dict[str, Any]] = Field(default_factory=list)
    summary: Optional[Dict[str, Any]] = None
    cli_scan_time: Optional[float] = None
    policy: Optional[Dict[str, Any]] = None  # Policy evaluation results

