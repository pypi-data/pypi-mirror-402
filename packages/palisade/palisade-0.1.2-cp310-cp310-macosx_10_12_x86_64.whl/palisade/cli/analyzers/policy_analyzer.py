"""Policy Analyzer for Palisade CLI.

Analyzes policy enforcement results and provides structured data for display.
"""

from typing import Any, Dict, List, Optional

# Policy effect constants
POLICY_DENY = "deny"
POLICY_QUARANTINE = "quarantine"
POLICY_ALLOW = "allow"


def analyze_policy_result(result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Analyze policy enforcement result from scan.
    
    Args:
        result: Scan result dictionary containing policy data
        
    Returns:
        Policy analysis dictionary or None if no policy data
    """
    policy_data = result.get("policy")
    if not policy_data:
        return None
    
    overall_effect = policy_data.get("overall_effect")
    environment = policy_data.get("environment", "default")
    summary = policy_data.get("summary", {})
    
    # Normalize effect to lowercase string
    if hasattr(overall_effect, "value"):
        overall_effect = overall_effect.value.lower()
    elif isinstance(overall_effect, str):
        overall_effect = overall_effect.lower()
    
    denied_count = summary.get("denied_files", 0)
    quarantined_count = summary.get("quarantined_files", 0)
    allowed_count = summary.get("allowed_files", 0)
    
    return {
        "overall_effect": overall_effect,
        "environment": environment,
        "denied_count": denied_count,
        "quarantined_count": quarantined_count,
        "allowed_count": allowed_count,
        "is_blocked": overall_effect == POLICY_DENY,
        "is_quarantined": overall_effect == POLICY_QUARANTINE,
        "is_allowed": overall_effect == POLICY_ALLOW or overall_effect is None,
        "decision_icon": _get_decision_icon(overall_effect),
        "decision_text": _get_decision_text(overall_effect),
        "recommendation": _get_policy_recommendation(overall_effect),
    }


def _get_decision_icon(effect: Optional[str]) -> str:
    """Get icon for policy decision.
    
    Args:
        effect: Policy effect (deny, quarantine, allow)
        
    Returns:
        Icon string
    """
    icons = {
        POLICY_DENY: "⛔",
        POLICY_QUARANTINE: "⚠️",
        POLICY_ALLOW: "✅",
    }
    return icons.get(effect, "✅")


def _get_decision_text(effect: Optional[str]) -> str:
    """Get text description for policy decision.
    
    Args:
        effect: Policy effect (deny, quarantine, allow)
        
    Returns:
        Decision text
    """
    texts = {
        POLICY_DENY: "BLOCKED",
        POLICY_QUARANTINE: "QUARANTINED",
        POLICY_ALLOW: "ALLOWED",
    }
    return texts.get(effect, "ALLOWED")


def _get_policy_recommendation(effect: Optional[str]) -> str:
    """Get recommendation based on policy decision.
    
    Args:
        effect: Policy effect (deny, quarantine, allow)
        
    Returns:
        Recommendation text
    """
    recommendations = {
        POLICY_DENY: "This file violates security policy and cannot be used.",
        POLICY_QUARANTINE: "This file requires manual review before use.",
        POLICY_ALLOW: "All findings comply with the configured security policy.",
    }
    return recommendations.get(effect, "All findings comply with the configured security policy.")


def aggregate_policy_results(files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate policy results from multiple files.
    
    Args:
        files: List of file scan results
        
    Returns:
        Aggregated policy summary
    """
    denied = 0
    quarantined = 0
    allowed = 0
    
    for file_result in files:
        policy = file_result.get("policy", {})
        effect = policy.get("overall_effect")
        
        # Normalize effect
        if hasattr(effect, "value"):
            effect = effect.value.lower()
        elif isinstance(effect, str):
            effect = effect.lower()
        
        if effect == POLICY_DENY:
            denied += 1
        elif effect == POLICY_QUARANTINE:
            quarantined += 1
        else:
            allowed += 1
    
    # Determine overall effect
    if denied > 0:
        overall_effect = POLICY_DENY
    elif quarantined > 0:
        overall_effect = POLICY_QUARANTINE
    else:
        overall_effect = POLICY_ALLOW
    
    return {
        "overall_effect": overall_effect,
        "denied_count": denied,
        "quarantined_count": quarantined,
        "allowed_count": allowed,
        "total_files": len(files),
        "is_blocked": denied > 0,
        "is_quarantined": quarantined > 0 and denied == 0,
        "is_allowed": denied == 0 and quarantined == 0,
        "decision_icon": _get_decision_icon(overall_effect),
        "decision_text": _get_decision_text(overall_effect),
    }


def get_exit_code_from_policy(policy_result: Optional[Dict[str, Any]]) -> int:
    """Get appropriate exit code based on policy result.
    
    Args:
        policy_result: Policy analysis result
        
    Returns:
        Exit code (0 = success, 1 = blocked, 2 = quarantined)
    """
    if not policy_result:
        return 0
    
    if policy_result.get("is_blocked"):
        return 1
    elif policy_result.get("is_quarantined"):
        return 2
    else:
        return 0


