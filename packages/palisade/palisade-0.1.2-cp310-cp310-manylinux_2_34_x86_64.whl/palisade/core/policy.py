"""Policy engine for Palisade - thin wrapper around javelin-policy.

This module provides Palisade-specific helpers for the javelin-policy engine.
All core policy functionality is bundled into palisade._native.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from palisade._native import PyCedarPolicyEngine, PolicyEffect

logger = logging.getLogger(__name__)


def get_default_policy_path() -> Optional[str]:
    """Get the default Palisade policy file path.
    
    Priority:
    1. PALISADE_POLICY_FILE environment variable
    2. ~/.config/palisade/policy.cedar
    3. Bundled policy in package
    
    Returns:
        Path to policy file, or None if bundled policy should be used
    """
    # Check environment variable
    env_path = os.getenv("PALISADE_POLICY_FILE")
    if env_path and Path(env_path).exists():
        return env_path
    
    # Check user config directory
    user_config = Path.home() / ".config" / "palisade" / "policy.cedar"
    if user_config.exists():
        return str(user_config)
    
    # Use bundled policy
    try:
        import palisade
        package_dir = Path(palisade.__file__).parent
        bundled_path = package_dir / "policies" / "cedar" / "palisade.cedar"
        if bundled_path.exists():
            return str(bundled_path)
    except Exception as e:
        logger.warning(f"Could not locate bundled policy: {e}")
    
    return None


def build_policy_context(
    finding: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """Build Cedar policy context from Palisade finding and context.
    
    This translates Palisade's domain model into Cedar policy evaluation context.
    
    Args:
        finding: Palisade finding dict with 'type', 'severity', 'category', 'details'
        context: Scan context with 'artifact', 'provenance', 'environment', etc.
    
    Returns:
        Cedar-compatible context dictionary
    """
    cedar_ctx = {}
    
    # Add finding fields (normalize severity to uppercase for Cedar policy consistency)
    cedar_ctx["finding_type"] = finding.get("type", "unknown")
    cedar_ctx["severity"] = finding.get("severity", "MEDIUM").upper()
    cedar_ctx["category"] = finding.get("category", "")
    
    # Add artifact fields from context
    artifact = context.get("artifact", {})
    cedar_ctx["artifact_format"] = artifact.get("format", "unknown")
    cedar_ctx["artifact_path"] = artifact.get("path", context.get("model_path", "unknown"))
    cedar_ctx["artifact_signed"] = artifact.get("signed", False)
    
    # Add provenance fields
    provenance = context.get("provenance", {})
    if provenance:
        cedar_ctx["provenance_signer"] = provenance.get("signer", "unknown")
        cedar_ctx["provenance_issuer"] = provenance.get("issuer", "unknown")
    
    # Add environment and project scope
    cedar_ctx["environment"] = context.get("environment", "default")
    cedar_ctx["project"] = context.get("project", "default")
    
    # Extract validator-specific context from finding details
    details = finding.get("details", {})
    
    # Pickle-specific context
    finding_type_lower = finding.get("type", "").lower()
    if ("exec" in finding_type_lower and "path" in finding_type_lower) or "pickle" in finding.get("category", "").lower():
        cedar_ctx["pickle_exec_path_detected"] = True
    
    # Tokenizer-specific context
    if "tokenizer" in finding.get("category", "").lower():
        if "added_tokens" in details:
            cedar_ctx["tokenizer_added_tokens_count"] = len(details.get("added_tokens", []))
    
    # LoRA adapter context
    if "digest_mismatch" in finding.get("type", "").lower():
        cedar_ctx["adapter_base_digest_mismatch"] = True
    
    # GGUF-specific context
    if "gguf" in artifact.get("format", "").lower() and "suspicious" in finding.get("type", "").lower():
        cedar_ctx["gguf_suspicious_metadata"] = True
    
    # Safetensors integrity
    if "safetensors" in artifact.get("format", "").lower() and "integrity" in finding.get("type", "").lower():
        cedar_ctx["safetensors_integrity_violation"] = True
    
    # Metadata malicious patterns
    if "malicious" in finding.get("type", "").lower():
        cedar_ctx["metadata_malicious_pattern"] = True
    
    # CoSAI maturity level
    metadata = context.get("metadata", {})
    if "cosai_level_numeric" in metadata:
        cedar_ctx["metadata_cosai_level_numeric"] = metadata["cosai_level_numeric"]
    if "cosai_compliance" in metadata:
        cedar_ctx["metadata_cosai_compliance"] = metadata["cosai_compliance"]
    
    return cedar_ctx


def evaluate_finding(
    policy_engine: PyCedarPolicyEngine,
    finding: Dict[str, Any],
    context: Dict[str, Any]
) -> str:
    """Evaluate a single finding against policy.
    
    Args:
        policy_engine: The javelin-policy engine instance
        finding: Finding dict with 'type', 'severity', etc.
        context: Scan context with 'artifact', 'environment', etc.
            Must include 'environment' key for policy profile (production/development/default)
    
    Returns:
        Policy effect: "allow", "deny", or "quarantine"
    """
    # Build Cedar context (includes environment from context if present)
    cedar_context = build_policy_context(finding, context)
    
    # Extract artifact info
    artifact_path = context.get("artifact", {}).get("path", context.get("model_path", "unknown"))
    
    # Evaluate using the generic evaluate() method
    decision = policy_engine.evaluate(
        principal_type="Scanner",
        principal_id="palisade-scanner",
        action="scan_artifact",
        resource_type="Artifact",
        resource_id=artifact_path,
        context=cedar_context
    )
    
    return decision['effect']


def aggregate_effects(effects: list[str]) -> str:
    """Aggregate multiple policy effects using 'most restrictive wins' logic.
    
    Args:
        effects: List of policy effects ("allow", "deny", "quarantine")
    
    Returns:
        Overall effect (most restrictive)
    """
    if not effects:
        return PolicyEffect.ALLOW
    
    # Most restrictive wins
    if PolicyEffect.DENY in effects:
        return PolicyEffect.DENY
    elif PolicyEffect.QUARANTINE in effects:
        return PolicyEffect.QUARANTINE
    else:
        return PolicyEffect.ALLOW


# Re-export for convenience (bundled from javelin-policy crate)
__all__ = [
    "PolicyEffect",
    "PyCedarPolicyEngine", 
    "get_default_policy_path",
    "build_policy_context",
    "evaluate_finding",
    "aggregate_effects",
]

