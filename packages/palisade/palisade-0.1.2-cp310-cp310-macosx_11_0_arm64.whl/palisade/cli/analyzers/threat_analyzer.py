"""Threat Analyzer for Palisade CLI.

Analyzes security warnings and categorizes threats by type and severity.
Provides structured threat analysis for display formatting.
"""

from typing import Any, Dict, List, Tuple

# Threat categories with keywords for classification
THREAT_CATEGORIES = {
    "behavioral_backdoors": ["behavioral", "tool_call", "backdoor", "trigger"],
    "code_execution": ["pickle", "buffer_overflow", "format_string", "exec", "rop"],
    "data_exfiltration": ["exfiltration", "data", "upload", "send", "network"],
    "injection_attacks": ["injection", "tampering", "malicious", "shell", "command"],
    "integrity_issues": ["integrity", "suspicious", "metadata", "corruption"],
}

# Severity levels in order of priority
SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]


def analyze_threats(warnings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze and categorize security threats from warnings.
    
    Args:
        warnings: List of warning dictionaries from scan results
        
    Returns:
        Dictionary containing:
        - severity_counts: Count of warnings by severity
        - categories: Warnings grouped by threat category
        - total_warnings: Total number of warnings
        - highest_severity: The highest severity found
    """
    if not warnings:
        return {
            "severity_counts": {},
            "categories": {},
            "total_warnings": 0,
            "highest_severity": None,
        }
    
    severity_counts = _count_by_severity(warnings)
    categories = _categorize_threats(warnings)
    highest_severity = _get_highest_severity(severity_counts)
    
    return {
        "severity_counts": severity_counts,
        "categories": categories,
        "total_warnings": len(warnings),
        "highest_severity": highest_severity,
    }


def _count_by_severity(warnings: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count warnings by severity level.
    
    Args:
        warnings: List of warning dictionaries
        
    Returns:
        Dictionary mapping severity to count
    """
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    
    for warning in warnings:
        severity = warning.get("severity", "unknown").lower()
        occurrence_count = warning.get("occurrence_count", 1)
        
        if severity in counts:
            counts[severity] += occurrence_count
    
    # Remove zero counts
    return {k: v for k, v in counts.items() if v > 0}


def _categorize_threats(warnings: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Categorize warnings by threat type.
    
    Args:
        warnings: List of warning dictionaries
        
    Returns:
        Dictionary mapping category to list of warnings
    """
    categories: Dict[str, List[Dict[str, Any]]] = {
        "behavioral_backdoors": [],
        "code_execution": [],
        "data_exfiltration": [],
        "injection_attacks": [],
        "integrity_issues": [],
        "other": [],
    }
    
    for warning in warnings:
        warning_type = warning.get("type", "").lower()
        message = warning.get("details", {}).get("message", "").lower()
        search_text = f"{warning_type} {message}"
        
        categorized = False
        for category, keywords in THREAT_CATEGORIES.items():
            if any(keyword in search_text for keyword in keywords):
                categories[category].append(warning)
                categorized = True
                break
        
        if not categorized:
            categories["other"].append(warning)
    
    # Remove empty categories
    return {k: v for k, v in categories.items() if v}


def _get_highest_severity(severity_counts: Dict[str, int]) -> str:
    """Get the highest severity level from counts.
    
    Args:
        severity_counts: Dictionary mapping severity to count
        
    Returns:
        Highest severity level found, or None if no warnings
    """
    for severity in SEVERITY_ORDER:
        if severity_counts.get(severity, 0) > 0:
            return severity
    return None


def get_recommendations(warnings: List[Dict[str, Any]], status: str) -> List[str]:
    """Get security recommendations based on scan results.
    
    Args:
        warnings: List of warning dictionaries
        status: Overall scan status (clean, warnings, critical, etc.)
        
    Returns:
        List of recommendation strings
    """
    if not warnings and status == "clean":
        return ["Model passed all security checks"]
    
    recommendations = []
    analysis = analyze_threats(warnings)
    
    highest = analysis.get("highest_severity")
    categories = analysis.get("categories", {})
    
    if highest == "critical" or status == "critical":
        recommendations.extend([
            "Do not deploy this model in production",
            "Investigate the source and integrity of this model",
            "Consider re-downloading from a trusted source",
        ])
    elif highest == "high":
        recommendations.extend([
            "Review high-severity warnings before deployment",
            "Verify the model source and integrity",
            "Consider additional validation",
        ])
    elif highest in ["medium", "low"]:
        recommendations.extend([
            "Review the warnings to understand potential risks",
            "Verify the model source and integrity",
        ])
    
    # Add category-specific recommendations
    if categories.get("behavioral_backdoors"):
        recommendations.append("Check for potential backdoor triggers in model behavior")
    
    if categories.get("code_execution"):
        recommendations.append("Ensure model loading is sandboxed to prevent code execution")
    
    if categories.get("injection_attacks"):
        recommendations.append("Validate all model inputs to prevent injection attacks")
    
    return recommendations


def group_warnings_by_severity(warnings: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group warnings by severity level.
    
    Args:
        warnings: List of warning dictionaries
        
    Returns:
        Dictionary mapping severity to list of warnings
    """
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    
    for warning in warnings:
        severity = warning.get("severity", "unknown").lower()
        if severity not in grouped:
            grouped[severity] = []
        grouped[severity].append(warning)
    
    return grouped


def group_warnings_by_file(files: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group warnings by file path.
    
    Args:
        files: List of file scan results
        
    Returns:
        Dictionary mapping file path to list of warnings
    """
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    
    for file_result in files:
        file_path = file_result.get("file_path", "unknown")
        warnings = file_result.get("warnings", [])
        
        if warnings:
            grouped[file_path] = warnings
    
    return grouped


