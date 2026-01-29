"""Validator Statistics Analyzer for Palisade CLI.

Analyzes validator performance and provides statistics for reporting.
Includes validator name inference from warning types.
"""

from typing import Any, Dict, List, Set

# Mapping of warning type patterns to validator names
# Order matters: more specific patterns should come first
VALIDATOR_PATTERNS = [
    # Specific validators first
    (["pickle"], "PickleSecurityValidator"),
    (["backdoor"], "BackdoorDetectionValidator"),
    (["provenance"], "ProvenanceSecurityValidator"),
    (["tokenizer"], "TokenizerHygieneValidator"),
    (["metadata"], "MetadataSecurityValidator"),
    (["toolcall", "tool_call"], "ToolCallSecurityValidator"),
    
    # Buffer overflow patterns (before safetensors/gguf)
    (["buffer", "overflow", "rop_gadget", "format_string", "dangerous_function",
      "native_executable", "native_library", "pe_missing", "elf_missing", 
      "macho_binary", "rop", "format string"], "BufferOverflowValidator"),
    
    # Format-specific validators
    (["safetensors"], "SafetensorsIntegrityValidator"),
    (["gguf"], "GGUFSafetyValidator"),
    
    # Other validators
    (["supply"], "SupplyChainValidator"),
    (["behavior"], "BehaviorAnalysisValidator"),
    (["integrity"], "ModelIntegrityValidator"),
    (["genealogy"], "ModelGenealogyValidator"),
]


def infer_validator_name(warning: Dict[str, Any]) -> str:
    """Infer validator name from warning information.
    
    Args:
        warning: Warning dictionary with type and details
        
    Returns:
        Inferred validator name
    """
    # Check detection_metadata first (most reliable)
    detection_metadata = warning.get("detection_metadata", {})
    validator_name = detection_metadata.get("validator_name")
    if validator_name:
        return validator_name
    
    # Get searchable text
    warning_type = warning.get("type", "").lower()
    details = str(warning.get("details", {})).lower()
    search_text = f"{warning_type} {details}"
    
    # Match against patterns
    for patterns, validator in VALIDATOR_PATTERNS:
        if any(pattern in search_text for pattern in patterns):
            return validator
    
    return "GeneralValidator"


def analyze_validator_performance(files: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Analyze validator performance from scan results.
    
    Args:
        files: List of file scan results
        
    Returns:
        Dictionary mapping validator name to performance stats:
        - warnings: Total warnings found
        - files: Number of files processed
        - avg_time: Average processing time
        - checks_performed: List of checks performed
    """
    validator_stats: Dict[str, Dict[str, Any]] = {}
    
    for file_result in files:
        _process_file_validators(file_result, validator_stats)
    
    # Convert to final format
    return _finalize_stats(validator_stats)


def _process_file_validators(file_result: Dict[str, Any], stats: Dict[str, Dict[str, Any]]) -> None:
    """Process validators from a single file result.
    
    Args:
        file_result: Single file scan result
        stats: Accumulated validator stats (modified in place)
    """
    validation_results = file_result.get("validation_results", [])
    
    if validation_results:
        # Use structured data
        for val_result in validation_results:
            validator_name = val_result.get("validator_name", "Unknown")
            metrics = val_result.get("metrics", {})
            warnings_count = len(val_result.get("warnings", []))
            processing_time = metrics.get("processing_time_seconds", 0)
            checks_performed = val_result.get("checks_performed", [])
            
            _update_validator_stats(
                stats, validator_name, file_result,
                warnings_count, processing_time, checks_performed
            )
    else:
        # Fallback inference
        warnings = file_result.get("warnings", [])
        processing_info = file_result.get("processing_info", {})
        
        for warning in warnings:
            validator_name = infer_validator_name(warning)
            _update_validator_stats(stats, validator_name, file_result, 1, 0, [])
        
        # Distribute scan time among validators
        scan_time = processing_info.get("scan_time_seconds", 0)
        if stats:
            time_per_validator = scan_time / len(stats)
            for validator_name in stats:
                stats[validator_name]["total_time"] += time_per_validator


def _update_validator_stats(
    stats: Dict[str, Dict[str, Any]],
    validator_name: str,
    file_result: Dict[str, Any],
    warnings_count: int,
    processing_time: float,
    checks_performed: List[str]
) -> None:
    """Update stats for a single validator.
    
    Args:
        stats: Accumulated stats dictionary (modified in place)
        validator_name: Name of the validator
        file_result: File result containing file path
        warnings_count: Number of warnings from this validator
        processing_time: Processing time in seconds
        checks_performed: List of check names
    """
    if validator_name not in stats:
        stats[validator_name] = {
            "warnings": 0,
            "files": set(),
            "total_time": 0.0,
            "checks_performed": set(),
        }
    
    stats[validator_name]["warnings"] += warnings_count
    stats[validator_name]["files"].add(file_result.get("file_path", ""))
    stats[validator_name]["total_time"] += processing_time
    stats[validator_name]["checks_performed"].update(checks_performed)


def _finalize_stats(stats: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Convert accumulated stats to final format.
    
    Args:
        stats: Accumulated stats with sets
        
    Returns:
        Final stats dictionary with averages and lists
    """
    result = {}
    
    for validator_name, validator_stats in stats.items():
        files_count = len(validator_stats["files"])
        if files_count > 0:
            result[validator_name] = {
                "warnings": validator_stats["warnings"],
                "files": files_count,
                "avg_time": validator_stats["total_time"] / files_count,
                "checks_performed": list(validator_stats["checks_performed"]),
            }
    
    return result


def get_validator_summary(files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Get a summary of validator performance.
    
    Args:
        files: List of file scan results
        
    Returns:
        Summary dictionary with:
        - total_validators: Number of validators run
        - validators_with_warnings: Number that found warnings
        - total_time: Total processing time
        - fastest: Fastest validator name
        - slowest: Slowest validator name
    """
    stats = analyze_validator_performance(files)
    
    if not stats:
        return {
            "total_validators": 0,
            "validators_with_warnings": 0,
            "total_time": 0,
            "fastest": None,
            "slowest": None,
        }
    
    total_time = sum(v["avg_time"] for v in stats.values())
    with_warnings = sum(1 for v in stats.values() if v["warnings"] > 0)
    
    # Find fastest and slowest
    sorted_by_time = sorted(stats.items(), key=lambda x: x[1]["avg_time"])
    fastest = sorted_by_time[0][0] if sorted_by_time else None
    slowest = sorted_by_time[-1][0] if sorted_by_time else None
    
    return {
        "total_validators": len(stats),
        "validators_with_warnings": with_warnings,
        "total_time": total_time,
        "fastest": fastest,
        "slowest": slowest,
    }


