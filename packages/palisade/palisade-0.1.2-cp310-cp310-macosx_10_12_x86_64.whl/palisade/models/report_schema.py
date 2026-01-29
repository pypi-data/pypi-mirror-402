"""Pydantic schemas for validation reports.

This module defines the structured data models for validation results and reports.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ValidationSeverity(str, Enum):
    """Validation severity levels."""
    
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ValidationType(str, Enum):
    """Types of validation checks."""
    
    SECURITY = "security"
    INTEGRITY = "integrity"
    COMPLIANCE = "compliance"
    PERFORMANCE = "performance"
    BEHAVIORAL = "behavioral"
    SUPPLY_CHAIN = "supply_chain"
    BACKDOOR_DETECTION = "backdoor_detection"
    PICKLE_SECURITY = "pickle_security"
    MODEL_GENEALOGY = "model_genealogy"


class DetectionMetadata(BaseModel):
    """Metadata about the detection/validation."""
    
    validator_name: str
    validator_version: str = "1.0.0"
    detection_timestamp: datetime = Field(default_factory=datetime.now)
    processing_time_ms: Optional[float] = None


class FileMetadata(BaseModel):
    """Metadata about the file being validated."""
    
    file_path: str
    file_size: int
    file_type: str = "unknown"
    sha256_hash: Optional[str] = None
    last_modified: Optional[datetime] = None


class ThreatIndicator(BaseModel):
    """Individual threat indicator found during validation."""
    
    indicator_type: str
    indicator_value: str
    confidence: float = Field(ge=0.0, le=1.0)
    context: Optional[str] = None
    byte_offset: Optional[int] = None
    line_number: Optional[int] = None


class MitreAtlasMapping(BaseModel):
    """MITRE ATLAS framework mapping."""
    
    technique_id: str
    technique_name: str
    url: Optional[str] = None
    tactic: Optional[str] = None


class ValidationDetails(BaseModel):
    """Detailed validation information."""
    
    message: str
    recommendation: Optional[str] = None
    threat_indicators: List[ThreatIndicator] = Field(default_factory=list)
    risk_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    extended_details: Dict[str, Any] = Field(default_factory=dict)


class ValidationWarning(BaseModel):
    """Structured validation warning."""
    
    warning_type: str
    validation_type: ValidationType
    severity: ValidationSeverity
    details: ValidationDetails
    detection_metadata: DetectionMetadata
    file_metadata: Optional[FileMetadata] = None
    mitre_atlas_mapping: Optional[MitreAtlasMapping] = Field(None, alias="mitre_atlas")
    
    model_config = ConfigDict(use_enum_values=True, populate_by_name=True)


class ValidationResult(BaseModel):
    """Complete validation result for a model."""
    
    validator_name: str = "unknown"
    model_path: str = ""
    validators_used: List[str] = Field(default_factory=list)
    validation_timestamp: datetime = Field(default_factory=datetime.now)
    total_warnings: int = 0
    warnings: List[ValidationWarning] = Field(default_factory=list)
    processing_time_ms: Optional[float] = None
    model_metadata: Dict[str, Any] = Field(default_factory=dict)
    policy_configuration: Dict[str, Any] = Field(default_factory=dict)
    result_id: Optional[str] = None
    
    # Summary statistics
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    
    def model_post_init(self, __context: Any) -> None:
        """Update counts after initialization."""
        # Update total warnings and severity counts based on warnings list
        self.total_warnings = len(self.warnings)
        self.critical_count = sum(1 for w in self.warnings if w.severity == ValidationSeverity.CRITICAL)
        self.high_count = sum(1 for w in self.warnings if w.severity == ValidationSeverity.HIGH)
        self.medium_count = sum(1 for w in self.warnings if w.severity == ValidationSeverity.MEDIUM)
        self.low_count = sum(1 for w in self.warnings if w.severity == ValidationSeverity.LOW)
    
    def add_warning(self, warning: ValidationWarning) -> None:
        """Add a warning and update counts."""
        self.warnings.append(warning)
        self.total_warnings = len(self.warnings)
        
        # Update severity counts
        if warning.severity == ValidationSeverity.CRITICAL:
            self.critical_count += 1
        elif warning.severity == ValidationSeverity.HIGH:
            self.high_count += 1
        elif warning.severity == ValidationSeverity.MEDIUM:
            self.medium_count += 1
        elif warning.severity == ValidationSeverity.LOW:
            self.low_count += 1
    
    @property
    def has_critical_issues(self) -> bool:
        """Check if there are critical issues."""
        return self.critical_count > 0
    
    @property
    def has_high_issues(self) -> bool:
        """Check if there are high severity issues."""
        return self.high_count > 0
    
    @property
    def max_severity(self) -> Optional[ValidationSeverity]:
        """Get the maximum severity level found."""
        if self.critical_count > 0:
            return ValidationSeverity.CRITICAL
        elif self.high_count > 0:
            return ValidationSeverity.HIGH
        elif self.medium_count > 0:
            return ValidationSeverity.MEDIUM
        elif self.low_count > 0:
            return ValidationSeverity.LOW
        return None
    
    @property
    def summary(self) -> "ValidationSummary":
        """Get validation summary."""
        severity_counts = {}
        total_threat_indicators = 0
        risk_scores = []
        
        for warning in self.warnings:
            severity_counts[warning.severity] = severity_counts.get(warning.severity, 0) + 1
            total_threat_indicators += len(warning.details.threat_indicators)
            if warning.details.risk_score is not None:
                risk_scores.append(warning.details.risk_score)
        
        # Calculate average risk score
        average_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else None
        
        # Ensure counts are updated for max_severity calculation
        self.critical_count = sum(1 for w in self.warnings if w.severity == ValidationSeverity.CRITICAL)
        self.high_count = sum(1 for w in self.warnings if w.severity == ValidationSeverity.HIGH)
        self.medium_count = sum(1 for w in self.warnings if w.severity == ValidationSeverity.MEDIUM)
        self.low_count = sum(1 for w in self.warnings if w.severity == ValidationSeverity.LOW)
        
        return ValidationSummary(
            total_warnings=len(self.warnings),
            highest_severity=self.max_severity,
            severity_counts=severity_counts,
            total_threat_indicators=total_threat_indicators,
            average_risk_score=average_risk_score
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backwards compatibility."""
        data = self.model_dump()
        # Add summary to the dict
        summary = self.summary
        data["summary"] = {
            "total_warnings": summary.total_warnings,
            "highest_severity": summary.highest_severity.value if summary.highest_severity else None,
            "severity_counts": {
                (k.value if hasattr(k, 'value') else k): v 
                for k, v in summary.severity_counts.items()
            },
            "total_threat_indicators": summary.total_threat_indicators,
            "average_risk_score": summary.average_risk_score
        }
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string for backwards compatibility."""
        import json
        return json.dumps(self.to_dict(), default=str)
    
    model_config = ConfigDict(use_enum_values=True)


class ValidationSummary:
    """Summary of validation results."""
    
    def __init__(self, total_warnings: int, highest_severity: Optional[ValidationSeverity], severity_counts: Dict[ValidationSeverity, int], total_threat_indicators: int = 0, average_risk_score: Optional[float] = None):
        self.total_warnings = total_warnings
        self.highest_severity = highest_severity
        self.severity_counts = severity_counts
        self.total_threat_indicators = total_threat_indicators
        self.average_risk_score = average_risk_score
