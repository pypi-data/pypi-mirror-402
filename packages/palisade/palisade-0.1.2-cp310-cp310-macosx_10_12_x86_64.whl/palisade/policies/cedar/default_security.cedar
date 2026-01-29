// Palisade Security Policy: default_security
// Description: Default security policy with balanced settings
// Security Level: medium
// 
// Behavior:
//   - CRITICAL findings: DENY
//   - HIGH findings: DENY
//   - MEDIUM findings: ALLOW (with warnings)
//   - LOW/INFO findings: ALLOW
//
// Usage:
//   palisade scan model.safetensors --policy default_security

// ==============================================================================
// UNIVERSAL CRITICAL BLOCKS (Always enforced)
// ==============================================================================

// Always block SafeTensors streaming/integrity errors
forbid(
    principal,
    action,
    resource
) when {
    context has finding_type &&
    (
        context.finding_type == "safetensors_streaming_error" ||
        context.finding_type == "safetensors_integrity_violation" ||
        context.finding_type == "safetensors_header_corruption" ||
        context.finding_type == "safetensors_size_mismatch"
    )
};

// Always block confirmed backdoor detections
forbid(
    principal,
    action,
    resource
) when {
    context has finding_type &&
    context has severity &&
    (context.severity == "CRITICAL" || context.severity == "HIGH") &&
    (
        context.finding_type == "backdoor_detected" ||
        context.finding_type == "backdoor_suspicious_header_patterns" ||
        context.finding_type == "backdoor_textual_patterns_in_chunk" ||
        context.finding_type == "behavioral_backdoor_indicators" ||
        context.finding_type == "tool_hijacking_detected" ||
        context.finding_type == "trojan_detected"
    )
};

// Always block data exfiltration and supply chain attacks
forbid(
    principal,
    action,
    resource
) when {
    context has finding_type &&
    (
        context.finding_type == "data_exfiltration_detected" ||
        context.finding_type == "supply_chain_attack" ||
        context.finding_type == "malicious_pattern_detected" ||
        context.finding_type == "code_injection_detected"
    )
};

// Always block pickle with confirmed RCE
forbid(
    principal,
    action,
    resource
) when {
    context has pickle_exec_path_detected &&
    context.pickle_exec_path_detected == true &&
    context has severity &&
    context.severity == "CRITICAL"
};

// Always quarantine metadata malicious patterns
forbid(
    principal,
    action,
    resource
) when {
    context has metadata_malicious_pattern &&
    context.metadata_malicious_pattern == true
};

// ==============================================================================
// DEFAULT SECURITY - BALANCED APPROACH
// ==============================================================================

// Block CRITICAL findings
forbid(
    principal,
    action,
    resource
) when {
    context has severity &&
    context.severity == "CRITICAL"
};

// Block HIGH findings
forbid(
    principal,
    action,
    resource
) when {
    context has severity &&
    context.severity == "HIGH"
};

// Allow MEDIUM findings (user sees warnings but can proceed)
permit(
    principal,
    action,
    resource
) when {
    context has severity &&
    context.severity == "MEDIUM"
};

// Allow LOW and INFO findings
permit(
    principal,
    action,
    resource
) when {
    context has severity &&
    (context.severity == "LOW" || context.severity == "INFO")
};

// Allow mature CoSAI models
permit(
    principal,
    action,
    resource
) when {
    context has metadata_cosai_level_numeric &&
    context.metadata_cosai_level_numeric >= 3
};

