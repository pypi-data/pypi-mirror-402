"""Legacy validation result classes.

This module provides the legacy ValidationResult and ValidationMetrics classes
for backward compatibility.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ValidationMetrics:
    """Metrics for validation performance."""
    
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    processing_time_seconds: Optional[float] = None
    bytes_processed: int = 0
    chunks_processed: int = 0
    memory_peak_mb: Optional[float] = None
    mode: str = "standard"
    
    @classmethod
    def start_timer(cls) -> "ValidationMetrics":
        """Create metrics with timer started."""
        return cls(start_time=time.time())
    
    def stop_timer(self) -> None:
        """Stop the timer and calculate processing time."""
        self.end_time = time.time()
        self.processing_time_seconds = self.end_time - self.start_time
    
    @property
    def elapsed_time(self) -> float:
        """Get elapsed time (current or total)."""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "processing_time_seconds": self.processing_time_seconds,
            "bytes_processed": self.bytes_processed,
            "chunks_processed": self.chunks_processed,
            "memory_peak_mb": self.memory_peak_mb,
            "mode": self.mode,
        }


@dataclass
class ValidationResult:
    """Legacy validation result container."""
    
    validator_name: str
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Optional[ValidationMetrics] = None
    model_type_detected: Optional[str] = None
    model_types_supported: List[str] = field(default_factory=list)
    validation_successful: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def warning_count(self) -> int:
        """Get total warning count."""
        return len(self.warnings)
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0
    
    @property
    def has_errors(self) -> bool:
        """Check if validation had errors."""
        return not self.validation_successful or self.error_message is not None
    
    def add_warning(self, warning: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        """Add a warning to the result."""
        if warning is not None:
            # Legacy dict-based warning
            self.warnings.append(warning)
        else:
            # Keyword-based warning creation
            warning_dict = {
                "type": kwargs.get("warning_type", "unknown"),
                "severity": kwargs.get("severity", "medium"),
                "details": {
                    "message": kwargs.get("message", "No message provided"),
                    "recommendation": kwargs.get("recommendation"),
                    **kwargs.get("details", {})
                }
            }
            if "check_name" in kwargs:
                warning_dict["check"] = kwargs["check_name"]
            self.warnings.append(warning_dict)
    
    def add_warnings(self, warnings: List[Dict[str, Any]]) -> None:
        """Add multiple warnings to the result."""
        self.warnings.extend(warnings)
    
    def set_error(self, error_message: str, error_metadata: Optional[Dict[str, Any]] = None) -> None:
        """Set an error state."""
        self.validation_successful = False
        self.error_message = error_message
        if error_metadata:
            self.metadata.update(error_metadata)
    
    def get_severity_counts(self) -> Dict[str, int]:
        """Get count of warnings by severity."""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        for warning in self.warnings:
            severity = warning.get("severity", "medium").lower()
            if severity in counts:
                counts[severity] += 1
        
        return counts
    
    def get_warnings_by_severity(self, severity: str) -> List[Dict[str, Any]]:
        """Get warnings filtered by severity."""
        return [
            warning for warning in self.warnings
            if warning.get("severity", "medium").lower() == severity.lower()
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "validator_name": self.validator_name,
            "warnings": self.warnings,
            "warning_count": self.warning_count,
            "model_type_detected": self.model_type_detected,
            "model_types_supported": self.model_types_supported,
            "validation_successful": self.validation_successful,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }
        
        if self.metrics:
            result["metrics"] = self.metrics.to_dict()
        
        result.update(self.get_severity_counts())
        
        return result
