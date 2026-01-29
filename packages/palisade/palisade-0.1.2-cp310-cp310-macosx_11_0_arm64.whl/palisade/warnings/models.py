"""Warning type definitions for Palisade validators.

Defines warning metadata that maps to SARIF output format.
Each warning type describes how a specific security finding should be reported.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class Severity(str, Enum):
    """Warning severity levels aligned with SARIF."""
    
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    
    def to_sarif_level(self) -> str:
        """Convert to SARIF level string."""
        mapping = {
            Severity.CRITICAL: "error",
            Severity.HIGH: "error",
            Severity.MEDIUM: "warning",
            Severity.LOW: "note",
            Severity.INFO: "note",
        }
        return mapping.get(self, "warning")


@dataclass(frozen=True)
class SarifMetadata:
    """SARIF-specific metadata for a warning type.
    
    This maps directly to SARIF's ReportingDescriptor fields.
    """
    
    id: str  # e.g., "PALISADE-BO-001"
    name: str  # e.g., "BufferOverflow"
    help_uri: Optional[str] = None  # Link to documentation
    
    def __post_init__(self) -> None:
        """Validate SARIF metadata."""
        if not self.id:
            raise ValueError("SARIF ID cannot be empty")
        if not self.name:
            raise ValueError("SARIF name cannot be empty")


@dataclass(frozen=True)
class WarningType:
    """A warning type definition for Palisade validators.
    
    This is the single source of truth for warning metadata, used by:
    - Validators when emitting warnings
    - SARIF formatter for generating reports (maps to SARIF rules)
    - Documentation generation
    
    Note: This describes warning metadata only, not detection patterns.
    Detection logic lives in validator Python code.
    
    Attributes:
        warning_id: Unique identifier (e.g., "rop_gadgets_detected")
        sarif: SARIF-specific metadata (maps to ReportingDescriptor)
        short_description: Brief description (shown in warnings)
        severity: Default severity level
        tags: Categorization tags for filtering
        full_description: Detailed description (optional)
        recommendation: How to remediate (optional)
        validator: Which validator emits this warning (optional)
    """
    
    warning_id: str
    sarif: SarifMetadata
    short_description: str
    severity: Severity
    tags: List[str] = field(default_factory=list)
    full_description: Optional[str] = None
    recommendation: Optional[str] = None
    validator: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate warning type definition."""
        if not self.warning_id:
            raise ValueError("Warning ID cannot be empty")
        if not self.short_description:
            raise ValueError("Short description cannot be empty")
    
    @classmethod
    def from_dict(cls, warning_id: str, data: dict) -> "WarningType":
        """Create a WarningType from a dictionary (e.g., loaded from YAML).
        
        Args:
            warning_id: The warning identifier
            data: Dictionary with warning data
            
        Returns:
            WarningType instance
        """
        sarif_data = data.get("sarif")
        if not sarif_data:
            raise ValueError(
                f"Warning '{warning_id}' missing required 'sarif' metadata in YAML. "
                f"All warnings must define 'sarif.id' and 'sarif.name' fields."
            )
        
        sarif_id = sarif_data.get("id")
        sarif_name = sarif_data.get("name")
        
        if not sarif_id:
            raise ValueError(
                f"Warning '{warning_id}' missing required 'sarif.id' field in YAML."
            )
        if not sarif_name:
            raise ValueError(
                f"Warning '{warning_id}' missing required 'sarif.name' field in YAML."
            )
        
        sarif = SarifMetadata(
            id=sarif_id,
            name=sarif_name,
            help_uri=sarif_data.get("help_uri"),
        )
        
        severity_str = data.get("severity", "medium").lower()
        try:
            severity = Severity(severity_str)
        except ValueError:
            severity = Severity.MEDIUM
        
        return cls(
            warning_id=warning_id,
            sarif=sarif,
            short_description=data.get("short_description", "No description"),
            severity=severity,
            tags=data.get("tags", []),
            full_description=data.get("full_description"),
            recommendation=data.get("recommendation"),
            validator=data.get("validator"),
        )

