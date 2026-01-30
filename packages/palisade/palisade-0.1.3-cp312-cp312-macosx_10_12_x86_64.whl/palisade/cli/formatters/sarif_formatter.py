"""SARIF output formatter for Palisade scan results.

Generates SARIF 2.1.0 compliant output using sarif-pydantic for validation.
Integrates with the rule catalog for consistent rule metadata.

SARIF (Static Analysis Results Interchange Format) is an OASIS standard for
representing static analysis results. This formatter enables integration with:
- GitHub Code Scanning
- Azure DevOps
- VS Code SARIF Viewer
- Other SARIF-compatible tools

Reference: https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html
"""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote

from sarif_pydantic import (
    Artifact,
    ArtifactLocation,
    Invocation,
    Level,
    Location,
    Message,
    PhysicalLocation,
    Region,
    ReportingDescriptor,
    Result,
    Run,
    Sarif,
    Tool,
    ToolDriver,
)
from sarif_pydantic.sarif import Suppression

from palisade import __version__
from palisade.cli.models import DirectoryScanResult, ScanResult
from palisade.warnings.catalog import WarningCatalog
from palisade.warnings.models import WarningType

# Module-level constants for leaderboard metrics
# These are defined once to avoid recreating on every function call

# Severity weights for security score calculation (lower score is better)
_SEVERITY_WEIGHTS = {
    "critical": 100,
    "high": 50,
    "medium": 10,
    "low": 2,
    "info": 1,
}

# Risk level thresholds
_RISK_LEVEL_CRITICAL_THRESHOLD = 1  # Any critical finding
_RISK_LEVEL_HIGH_COUNT_THRESHOLD = 3  # 3+ high findings
_RISK_LEVEL_MEDIUM_HIGH_THRESHOLD = 1  # 1+ high OR 5+ medium
_RISK_LEVEL_MEDIUM_COUNT_THRESHOLD = 5
_RISK_LEVEL_LOW_MEDIUM_THRESHOLD = 1  # 1+ medium OR 5+ low
_RISK_LEVEL_LOW_COUNT_THRESHOLD = 5

# Top validators to include in metrics
_TOP_VALIDATORS_COUNT = 5

# Validator to threat category mapping
_VALIDATOR_CATEGORY_MAP = {
    "BufferOverflow": "buffer_overflow",
    "PickleSecurity": "pickle_rce",
    "Backdoor": "backdoor",
    "SupplyChain": "supply_chain",
    "ModelIntegrity": "model_integrity",
    "TokenizerHygiene": "tokenizer_hijacking",
    "MetadataSecurity": "metadata_security",
    "GGUFSafety": "gguf_safety",
    "SafetensorsIntegrity": "safetensors_integrity",
    "BehaviorAnalysis": "behavior_analysis",
    "ToolCallSecurity": "tool_call_security",
    "LoRASecurity": "lora_security",
    "ModelGenealogy": "model_genealogy",
}


# SARIF schema version
SARIF_SCHEMA = "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"
SARIF_VERSION = "2.1.0"


def create_sarif_report(
    scan_result: Union[ScanResult, DirectoryScanResult, Dict[str, Any]],
    include_suppressed: bool = True,
) -> Sarif:
    """Create a SARIF report from Palisade scan results.
    
    Args:
        scan_result: Palisade scan result (single file or directory)
        include_suppressed: Include policy-suppressed findings
        
    Returns:
        Sarif object (sarif-pydantic model)
    """
    # Convert to dict if Pydantic model
    if hasattr(scan_result, "model_dump"):
        result_dict = scan_result.model_dump(exclude_none=True)
    else:
        result_dict = scan_result
    
    # Determine if directory or single file scan
    is_directory = "directory" in result_dict or "files" in result_dict
    
    # Build SARIF components
    tool = _build_tool_component(result_dict)
    invocation = _build_invocation(result_dict, is_directory)
    artifacts = _build_artifacts(result_dict, is_directory)
    results = _build_results(result_dict, is_directory, include_suppressed)
    rules = _build_rules_from_results(results)
    
    # Add rules to tool driver
    if rules:
        tool.driver.rules = rules
    
    # Build run with properties for policy info
    run_properties = _build_run_properties(result_dict)
    
    # Build originalUriBaseIds for portable paths
    uri_base_ids = _build_uri_base_ids(result_dict, is_directory)
    
    run = Run(
        tool=tool,
        invocations=[invocation] if invocation else None,
        artifacts=artifacts if artifacts else None,
        results=results,
        properties=run_properties if run_properties else None,
        originalUriBaseIds=uri_base_ids if uri_base_ids else None,
    )
    
    return Sarif(
        version=SARIF_VERSION,
        schema_uri=SARIF_SCHEMA,
        runs=[run],
    )


def sarif_to_json(sarif: Sarif, indent: int = 2) -> str:
    """Convert SARIF object to JSON string.
    
    Args:
        sarif: SARIF object
        indent: JSON indentation level
        
    Returns:
        JSON string in SARIF 2.1.0 format with camelCase field names
    """
    return sarif.model_dump_json(indent=indent, exclude_none=True, by_alias=True)


def sarif_to_dict(sarif: Sarif) -> Dict[str, Any]:
    """Convert SARIF object to dictionary.
    
    Args:
        sarif: SARIF object
        
    Returns:
        Dictionary representation in SARIF 2.1.0 format with camelCase field names
    """
    return sarif.model_dump(exclude_none=True, by_alias=True)


def _build_tool_component(result_dict: Dict[str, Any]) -> Tool:
    """Build SARIF Tool component."""
    return Tool(
        driver=ToolDriver(
            name="Palisade",
            version=__version__,
            informationUri="https://github.com/highflame-ai/highflame-palisade",
            organization="Highflame",
            shortDescription=Message(text="ML Model Security Scanner"),
            fullDescription=Message(
                text="Palisade is a comprehensive security scanner for ML models, "
                     "detecting backdoors, pickle exploits, buffer overflows, and "
                     "supply chain attacks."
            ),
        )
    )


def _build_invocation(
    result_dict: Dict[str, Any],
    is_directory: bool,
) -> Optional[Invocation]:
    """Build SARIF Invocation with execution details."""
    # Determine success based on status
    status = result_dict.get("status", "unknown")
    execution_successful = status not in ["error", "failed"]
    
    # Get timing info
    scan_time = result_dict.get("cli_scan_time") or result_dict.get("scan_time_seconds")
    
    # Capture timestamp once for consistency across all invocation timestamps
    end_time_utc = datetime.now(timezone.utc)
    
    # Build invocation properties for policy info
    invocation_properties: Dict[str, Any] = {}
    
    # Extract policy information
    policy = result_dict.get("policy")
    if policy:
        invocation_properties["policy"] = {
            "overall_effect": policy.get("overall_effect", "unknown"),
            "environment": policy.get("environment", "default"),
            "evaluated_at": end_time_utc.isoformat(),  # Use same timestamp
        }
    
    # Calculate accurate start time based on scan duration
    start_time_utc = (
        end_time_utc - timedelta(seconds=scan_time) if scan_time else end_time_utc
    )
    
    # Use actual command line if available, otherwise fall back to empty (in case of library scan)
    command_line = result_dict.get(
        "command_line",
        ""
    )
    
    return Invocation(
        executionSuccessful=execution_successful,
        commandLine=command_line,
        startTimeUtc=start_time_utc.isoformat(),
        endTimeUtc=end_time_utc.isoformat(),
        properties=invocation_properties if invocation_properties else None,
    )


def _build_artifacts(
    result_dict: Dict[str, Any],
    is_directory: bool,
) -> List[Artifact]:
    """Build SARIF Artifact list."""
    artifacts = []
    
    if is_directory:
        # Directory scan - create artifact for each file
        files = result_dict.get("files", [])
        for file_info in files:
            file_path = file_info.get("file_path", file_info.get("path", "unknown"))
            artifact = _create_artifact(file_path, file_info)
            artifacts.append(artifact)
    else:
        # Single file scan
        file_path = result_dict.get("file_path", "unknown")
        artifact = _create_artifact(file_path, result_dict)
        artifacts.append(artifact)
    
    return artifacts


def _create_artifact(file_path: str, file_info: Dict[str, Any]) -> Artifact:
    """Create a single SARIF Artifact."""
    # Extract file metadata
    metadata = file_info.get("file_info", {}) or file_info.get("metadata", {}) or {}
    
    # Get size
    size = metadata.get("size_bytes") or metadata.get("file_size") or file_info.get("file_size")
    
    # Get hash if available
    hashes = None
    sha256 = metadata.get("sha256") or metadata.get("sha256_hash")
    if sha256:
        hashes = {"sha-256": sha256}
    
    return Artifact(
        location=ArtifactLocation(
            uri=_file_uri(file_path),
            uriBaseId="%SRCROOT%",
        ),
        length=size,
        hashes=hashes,
    )


def _build_results(
    result_dict: Dict[str, Any],
    is_directory: bool,
    include_suppressed: bool,
) -> List[Result]:
    """Build SARIF Result list from warnings."""
    results = []
    
    if is_directory:
        # Directory scan - aggregate warnings from all files
        files = result_dict.get("files", [])
        for file_idx, file_info in enumerate(files):
            file_path = file_info.get("file_path", file_info.get("path", "unknown"))
            warnings = file_info.get("warnings", [])
            
            for warning in warnings:
                result = _build_result_from_warning(
                    warning, file_path, file_idx, include_suppressed
                )
                if result:
                    results.append(result)
    else:
        # Single file scan
        file_path = result_dict.get("file_path", "unknown")
        warnings = result_dict.get("warnings", [])
        
        for warning in warnings:
            result = _build_result_from_warning(
                warning, file_path, 0, include_suppressed
            )
            if result:
                results.append(result)
    
    return results


def _build_result_from_warning(
    warning: Dict[str, Any],
    file_path: str,
    artifact_index: int,
    include_suppressed: bool,
) -> Optional[Result]:
    """Build a single SARIF Result from a Palisade warning."""
    # Extract warning type and normalize it
    warning_type = warning.get("type", "unknown")
    
    # Get warning type from catalog  
    validator_name = warning.get("detection_metadata", {}).get("validator_name", "Unknown")
    warning_meta = WarningCatalog.get_or_create(warning_type, validator_name)
    
    # Map severity to SARIF level
    severity_str = warning.get("severity", "medium")
    level = _map_severity_to_level(severity_str)
    
    # Build message from warning details
    details = warning.get("details", {})
    if isinstance(details, str):
        message_text = details
    else:
        message_text = details.get("message", warning_meta.short_description)
    
    # Build location
    location = Location(
        physicalLocation=PhysicalLocation(
            artifactLocation=ArtifactLocation(
                uri=_file_uri(file_path),
                index=artifact_index,
            ),
            region=_extract_region(warning),
        )
    )
    
    # Build result properties (extra metadata)
    result_properties: Dict[str, Any] = {}
    
    # Add severity for easier leaderboard extraction
    result_properties["severity"] = severity_str
    
    # Add detection metadata
    detection_meta = warning.get("detection_metadata", {})
    if detection_meta:
        result_properties["detection"] = {
            "validator": detection_meta.get("validator_name"),
            "timestamp": detection_meta.get("detection_date"),
        }
    
    # Add MITRE ATLAS mapping if present
    mitre_atlas = warning.get("mitre_atlas")
    if mitre_atlas:
        result_properties["mitreAtlas"] = mitre_atlas
    
    # Add threat indicators if present
    if isinstance(details, dict):
        threat_indicators = details.get("threat_indicators", [])
        if threat_indicators:
            result_properties["threatIndicators"] = threat_indicators
        
        # Add recommendation
        recommendation = details.get("recommendation")
        if recommendation:
            result_properties["recommendation"] = recommendation
    
    # Handle policy suppression
    suppression = None
    policy_effect = warning.get("policy_effect")
    if policy_effect:
        result_properties["policyEffect"] = policy_effect
        
        # Create suppression for allowed/quarantined findings
        if policy_effect in ("allow", "quarantine"):
            if not include_suppressed:
                return None  # Skip suppressed findings
            
            suppression = Suppression(
                kind="inSource",
                status="accepted" if policy_effect == "allow" else "underReview",
                justification=f"Policy decision: {policy_effect}",
            )
    
    return Result(
        rule_id=warning_meta.sarif.id,
        level=level,
        message=Message(text=message_text),
        locations=[location],
        properties=result_properties if result_properties else None,
        suppression=suppression,
    )


def _build_rules_from_results(results: List[Result]) -> List[ReportingDescriptor]:
    """Build SARIF rules (ReportingDescriptor) from results."""
    # Collect unique SARIF rule IDs from results
    seen_sarif_ids = set()
    rules = []
    
    for result in results:
        sarif_id = result.rule_id
        if sarif_id and sarif_id not in seen_sarif_ids:
            seen_sarif_ids.add(sarif_id)
            
            # Get full warning type from catalog
            # SARIF ID in result is like PALISADE-BO-001
            # We need to find the warning type by SARIF ID
            warning_type = _find_warning_by_sarif_id(sarif_id)
            if warning_type:
                rules.append(_build_reporting_descriptor(warning_type))
            else:
                # Create minimal descriptor for unknown warnings
                rules.append(ReportingDescriptor(
                    id=sarif_id,
                    name="UnknownWarning",
                    shortDescription=Message(text="Unknown finding"),
                ))
    
    return rules


def _find_warning_by_sarif_id(sarif_id: str) -> Optional[WarningType]:
    """Find a warning type by its SARIF ID using O(1) lookup."""
    return WarningCatalog.find_by_sarif_id(sarif_id)


def _build_reporting_descriptor(warning_type: WarningType) -> ReportingDescriptor:
    """Build SARIF ReportingDescriptor from a WarningType."""
    # Build help text with recommendation
    help_text = warning_type.full_description or warning_type.short_description
    if warning_type.recommendation:
        help_text += f"\n\nRecommendation: {warning_type.recommendation}"
    
    return ReportingDescriptor(
        id=warning_type.sarif.id,
        name=warning_type.sarif.name,
        shortDescription=Message(text=warning_type.short_description),
        fullDescription=Message(text=warning_type.full_description) if warning_type.full_description else None,
        helpUri=warning_type.sarif.help_uri,
        help=Message(text=help_text),
        defaultConfiguration={
            "level": warning_type.severity.to_sarif_level(),
        },
        properties={
            "tags": warning_type.tags,
            "severity": warning_type.severity.value,
            "validator": warning_type.validator,
        } if warning_type.tags or warning_type.validator else None,
    )


def _map_severity_to_level(severity: str) -> Level:
    """Map Palisade severity to SARIF Level."""
    severity_map = {
        "critical": Level.ERROR,
        "high": Level.ERROR,
        "medium": Level.WARNING,
        "low": Level.NOTE,
        "info": Level.NOTE,
    }
    return severity_map.get(severity.lower(), Level.WARNING)


def _extract_region(warning: Dict[str, Any]) -> Optional[Region]:
    """Extract SARIF Region from warning details."""
    details = warning.get("details", {})
    if not isinstance(details, dict):
        return None
    
    # Try to extract byte offset
    byte_offset = details.get("byte_offset") or details.get("chunk_offset")
    if byte_offset is not None:
        return Region(byteOffset=byte_offset)
    
    # Try to extract line number
    line_number = details.get("line_number")
    if line_number is not None:
        return Region(startLine=line_number)
    
    return None


def _file_uri(path: str) -> str:
    """Convert file path to URI format."""
    # Handle absolute paths
    if path.startswith("/"):
        return f"file://{quote(path)}"
    
    # Handle Windows paths
    if len(path) > 1 and path[1] == ":":
        return f"file:///{quote(path.replace(chr(92), '/'))}"
    
    # Relative path - just quote it
    return quote(path)


def _build_run_properties(result_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Build properties for the SARIF run."""
    properties: Dict[str, Any] = {}
    
    # Add Palisade version for easy reference
    properties["palisadeVersion"] = __version__
    
    # Add summary if available
    summary = result_dict.get("summary")
    if summary:
        properties["summary"] = summary
    
    # Add policy information at run level
    policy = result_dict.get("policy")
    if policy:
        properties["policy"] = {
            "overall_effect": policy.get("overall_effect", "unknown"),
            "environment": policy.get("environment", "default"),
        }
    
    # Add scan metadata
    scan_time = result_dict.get("cli_scan_time") or result_dict.get("scan_time_seconds")
    if scan_time:
        properties["scanTimeSeconds"] = scan_time
    
    # Add file info for single file scans
    file_info = result_dict.get("file_info")
    if file_info:
        properties["fileInfo"] = file_info
    
    # Add comprehensive leaderboard metrics for easy consumption
    leaderboard_metrics = _calculate_leaderboard_metrics(result_dict)
    if leaderboard_metrics:
        properties["leaderboardMetrics"] = leaderboard_metrics
    
    return properties if properties else None


def _calculate_leaderboard_metrics(result_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate comprehensive leaderboard metrics from scan results.
    
    This pre-computes all metrics needed for leaderboard display,
    so consumers don't need to re-parse the entire SARIF.
    """
    
    # Collect warnings from single file or directory scan
    warnings = []
    if "warnings" in result_dict:
        warnings = result_dict["warnings"]
    elif "files" in result_dict:
        for file_info in result_dict["files"]:
            warnings.extend(file_info.get("warnings", []))
    
    # Initialize all counters
    severity_counts = defaultdict(int)
    threat_categories = defaultdict(int)
    policy_compliance = defaultdict(int)
    validator_counts = defaultdict(int)
    mitre_techniques = set()
    
    # OPTIMIZED: Single pass through warnings - collect all metrics at once
    for warning in warnings:
        # 1. Count severity
        severity = warning.get("severity", "medium").lower()
        severity_counts[severity] += 1
        
        # 2. Extract and count threat categories
        validator = warning.get("detection_metadata", {}).get("validator_name", "")
        if validator:
            # Map validator to category using module-level constant
            category = None
            for validator_name, cat in _VALIDATOR_CATEGORY_MAP.items():
                if validator_name in validator:
                    category = cat
                    break
            
            if category:
                threat_categories[category] += 1
            else:
                threat_categories["other"] += 1
            
            # 4. Count validators (for top validators list)
            validator_counts[validator] += 1
        
        # 3. Count policy compliance
        policy_effect = warning.get("policy_effect")
        if policy_effect:
            policy_compliance[policy_effect] += 1
        
        # 5. Extract MITRE ATT&CK techniques
        mitre = warning.get("mitre_atlas")
        if mitre:
            if isinstance(mitre, dict):
                technique_id = mitre.get("technique_id") or mitre.get("id")
            elif isinstance(mitre, str):
                technique_id = mitre
            else:
                technique_id = None
            
            if technique_id:
                mitre_techniques.add(technique_id)
    
    # Post-processing: Calculate security score using module-level weights
    security_score = sum(
        severity_counts.get(sev, 0) * weight
        for sev, weight in _SEVERITY_WEIGHTS.items()
    )
    
    # Determine risk level using named thresholds
    critical = severity_counts.get("critical", 0)
    high = severity_counts.get("high", 0)
    medium = severity_counts.get("medium", 0)
    low = severity_counts.get("low", 0)
    
    if critical >= _RISK_LEVEL_CRITICAL_THRESHOLD:
        risk_level = "critical"
    elif high >= _RISK_LEVEL_HIGH_COUNT_THRESHOLD:
        risk_level = "high"
    elif high >= _RISK_LEVEL_MEDIUM_HIGH_THRESHOLD or medium >= _RISK_LEVEL_MEDIUM_COUNT_THRESHOLD:
        risk_level = "medium"
    elif medium >= _RISK_LEVEL_LOW_MEDIUM_THRESHOLD or low >= _RISK_LEVEL_LOW_COUNT_THRESHOLD:
        risk_level = "low"
    else:
        risk_level = "safe"
    
    # Get top validators using named constant
    top_validators = sorted(
        validator_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:_TOP_VALIDATORS_COUNT]
    
    # Build metrics object
    metrics = {
        "securityScore": security_score,
        "riskLevel": risk_level,
        "totalWarnings": len(warnings),
        "severityCounts": {
            "critical": severity_counts.get("critical", 0),
            "high": severity_counts.get("high", 0),
            "medium": severity_counts.get("medium", 0),
            "low": severity_counts.get("low", 0),
            "info": severity_counts.get("info", 0),
        },
        "threatCategories": dict(threat_categories),
        "policyCompliance": dict(policy_compliance),
        "topValidators": [{"name": name, "count": count} for name, count in top_validators],
        "mitreAtlasTechniques": sorted(list(mitre_techniques)),
    }
    
    return metrics


def _build_uri_base_ids(
    result_dict: Dict[str, Any],
    is_directory: bool,
) -> Optional[Dict[str, ArtifactLocation]]:
    """Build originalUriBaseIds for portable file paths.
    
    Defines what %SRCROOT% points to, making paths portable across systems.
    This is important for CI/CD and GitHub Code Scanning integration.
    
    Args:
        result_dict: Scan result dictionary
        is_directory: Whether this is a directory scan
        
    Returns:
        Dictionary mapping base IDs to their locations
    """
    # Determine the base directory
    if is_directory:
        # For directory scans, use the scanned directory as root
        scan_dir = result_dict.get("directory")
        if scan_dir:
            base_path = Path(scan_dir).resolve()
        else:
            base_path = Path.cwd()
    else:
        # For single file scans, use the file's directory as root
        file_path = result_dict.get("file_path")
        if file_path:
            base_path = Path(file_path).parent.resolve()
        else:
            base_path = Path.cwd()
    
    # Convert to file URI with trailing slash
    base_uri = f"file://{base_path.as_posix()}/"
    
    return {
        "%SRCROOT%": ArtifactLocation(uri=base_uri)
    }
