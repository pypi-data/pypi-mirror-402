"""Utilities for converting between legacy and Pydantic schemas.

This module provides conversion functions between the old dict-based validation
results and the new Pydantic-based structured schemas.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .report_schema import (
    DetectionMetadata,
    FileMetadata,
    MitreAtlasMapping,
    ThreatIndicator,
    ValidationDetails,
    ValidationResult,
    ValidationSeverity,
    ValidationType,
    ValidationWarning,
)


def convert_legacy_severity(severity_str: str) -> ValidationSeverity:
    """Convert legacy severity string to ValidationSeverity enum."""
    severity_map = {
        "critical": ValidationSeverity.CRITICAL,
        "high": ValidationSeverity.HIGH,
        "medium": ValidationSeverity.MEDIUM,
        "low": ValidationSeverity.LOW,
    }
    return severity_map.get(severity_str.lower(), ValidationSeverity.MEDIUM)


def infer_validation_type(warning_type: str) -> ValidationType:
    """Infer validation type from warning type."""
    warning_type_lower = warning_type.lower()
    
    # Check for specific validation types first (most specific to least specific)
    if "backdoor" in warning_type_lower:
        return ValidationType.BACKDOOR_DETECTION
    elif "pickle" in warning_type_lower:
        return ValidationType.PICKLE_SECURITY
    elif "genealogy" in warning_type_lower:
        return ValidationType.MODEL_GENEALOGY
    elif any(term in warning_type_lower for term in ["security", "malicious", "exploit"]):
        return ValidationType.SECURITY
    elif any(term in warning_type_lower for term in ["integrity", "corruption", "tamper"]):
        return ValidationType.INTEGRITY
    elif any(term in warning_type_lower for term in ["behavior", "inference", "output"]):
        return ValidationType.BEHAVIORAL
    elif any(term in warning_type_lower for term in ["supply", "chain", "provenance", "source"]):
        return ValidationType.SUPPLY_CHAIN
    elif any(term in warning_type_lower for term in ["compliance", "policy", "regulation"]):
        return ValidationType.COMPLIANCE
    elif any(term in warning_type_lower for term in ["performance", "memory", "speed"]):
        return ValidationType.PERFORMANCE
    else:
        return ValidationType.SECURITY  # Default to security


def convert_legacy_warning(legacy_warning: Dict[str, Any], validator_name: Optional[str] = None) -> ValidationWarning:
    """Convert legacy warning dict to ValidationWarning."""
    
    # Extract basic fields
    warning_type = legacy_warning.get("type", "unknown_warning")
    severity = convert_legacy_severity(legacy_warning.get("severity", "medium"))
    validation_type = infer_validation_type(warning_type)
    
    # Extract validator name from warning metadata if available
    detection_meta = legacy_warning.get("detection_metadata", {})
    final_validator_name = detection_meta.get("validator_name", validator_name or "unknown")
    
    # Create detection metadata
    detection_metadata = DetectionMetadata(
        validator_name=final_validator_name,
        validator_version=detection_meta.get("validator_version", "1.0.0"),
        detection_timestamp=datetime.now()
    )
    
    # Extract details
    details_dict = legacy_warning.get("details", {})
    message = details_dict.get("message", legacy_warning.get("message", "No message provided"))
    recommendation = details_dict.get("recommendation", legacy_warning.get("recommendation"))
    
    # Create threat indicators if available
    threat_indicators = []
    if "indicators" in details_dict:
        for indicator_data in details_dict["indicators"]:
            if isinstance(indicator_data, dict):
                threat_indicators.append(ThreatIndicator(
                    indicator_type=indicator_data.get("type", "unknown"),
                    indicator_value=indicator_data.get("value", ""),
                    confidence=indicator_data.get("confidence", 0.5),
                    context=indicator_data.get("context"),
                    byte_offset=indicator_data.get("byte_offset"),
                    line_number=indicator_data.get("line_number")
                ))
    
    # Create validation details
    validation_details = ValidationDetails(
        message=message,
        recommendation=recommendation,
        threat_indicators=threat_indicators,
        risk_score=details_dict.get("risk_score"),
        confidence=details_dict.get("confidence"),
        extended_details=details_dict.get("extended_details", {})
    )
    
    # Create MITRE ATLAS mapping if available
    mitre_mapping = None
    if "mitre_atlas" in legacy_warning:
        mitre_data = legacy_warning["mitre_atlas"]
        mitre_mapping = MitreAtlasMapping(
            technique_id=mitre_data.get("technique_id", ""),
            technique_name=mitre_data.get("technique_name", ""),
            url=mitre_data.get("url"),
            tactic=mitre_data.get("tactic")
        )
    
    # Create file metadata if available
    file_metadata = None
    if "file_info" in legacy_warning:
        file_info = legacy_warning["file_info"]
        file_metadata = FileMetadata(
            file_path=file_info.get("path", ""),
            file_size=file_info.get("size", 0),
            file_type=file_info.get("type", "unknown"),
            sha256_hash=file_info.get("hash"),
            last_modified=file_info.get("modified")
        )
    elif "model_metadata" in legacy_warning:
        model_meta = legacy_warning["model_metadata"]
        # Get sha256 hash from file_hashes if available, otherwise from model_metadata
        sha256 = model_meta.get("sha256")
        if not sha256 and "file_hashes" in legacy_warning:
            sha256 = legacy_warning["file_hashes"].get("sha256")
        
        file_metadata = FileMetadata(
            file_path=model_meta.get("file_path", ""),
            file_size=model_meta.get("file_size", 0),
            file_type=model_meta.get("format", "unknown"),
            sha256_hash=sha256
        )
    elif "file_hashes" in legacy_warning:
        # Construct file metadata from scattered fields
        hashes = legacy_warning.get("file_hashes", {})
        file_metadata = FileMetadata(
            file_path=legacy_warning.get("file_path", ""),
            file_size=0,
            file_type="unknown",
            sha256_hash=hashes.get("sha256")
        )
    
    return ValidationWarning(
        warning_type=warning_type,
        validation_type=validation_type,
        severity=severity,
        details=validation_details,
        detection_metadata=detection_metadata,
        file_metadata=file_metadata,
        mitre_atlas_mapping=mitre_mapping
    )


def convert_legacy_warnings_to_result(
    legacy_warnings: List[Dict[str, Any]],
    validator_name: str = "unknown",
    model_path: str = "",
    validators_used: Optional[List[str]] = None,
    policy_configuration: Optional[Dict[str, Any]] = None
) -> ValidationResult:
    """Convert list of legacy warnings to ValidationResult."""
    
    result = ValidationResult(
        validator_name=validator_name,
        model_path=model_path,
        validators_used=validators_used or [],
        validation_timestamp=datetime.now(),
        policy_configuration=policy_configuration or {}
    )
    
    for legacy_warning in legacy_warnings:
        # Get validator name from warning if available
        warning_validator = legacy_warning.get("detection_metadata", {}).get("validator_name", validator_name)
        warning = convert_legacy_warning(legacy_warning, warning_validator)
        result.add_warning(warning)
    
    return result


# convert_pydantic_to_legacy removed - not used in production
# When Pydantic migration happens, this can be re-added for backwards compatibility
