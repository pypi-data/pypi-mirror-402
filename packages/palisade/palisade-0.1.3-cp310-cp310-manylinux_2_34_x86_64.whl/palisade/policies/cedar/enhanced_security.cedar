// Palisade Security Policy: enhanced_security
// Description: Enhanced security with stricter checks than default
// Security Level: high
// 
// Behavior:
//   - CRITICAL findings: DENY
//   - HIGH findings: DENY
//   - MEDIUM findings: DENY
//   - LOW findings: ALLOW (with warnings)
//   - INFO findings: ALLOW
//   - Warns on unsigned artifacts (doesn't block)
//   - Stricter tokenizer limits (max 200 added tokens)
//   - Blocks integrity violations
//
// Usage:
//   palisade scan model.safetensors --policy enhanced_security

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
// ENHANCED SECURITY - STRICTER THAN DEFAULT
// ==============================================================================

// Block pickle format (enhanced security doesn't allow pickle)
forbid(
    principal,
    action,
    resource
) when {
    context has artifact_format &&
    context.artifact_format == "pickle"
};

// Stricter tokenizer limits (max 200 added tokens)
forbid(
    principal,
    action,
    resource
) when {
    context has tokenizer_added_tokens_count &&
    context.tokenizer_added_tokens_count > 200
};

// Block integrity violations
forbid(
    principal,
    action,
    resource
) when {
    (context has safetensors_integrity_violation && context.safetensors_integrity_violation == true) ||
    (context has gguf_suspicious_metadata && context.gguf_suspicious_metadata == true) ||
    (context has adapter_base_digest_mismatch && context.adapter_base_digest_mismatch == true)
};

// Block behavioral backdoor indicators with high confidence
forbid(
    principal,
    action,
    resource
) when {
    context has finding_type &&
    context.finding_type == "behavioral_backdoor_indicators" &&
    context has severity &&
    context.severity == "HIGH" &&
    context has match_count &&
    context.match_count >= 3
};

// Block CRITICAL, HIGH, and MEDIUM findings
forbid(
    principal,
    action,
    resource
) when {
    context has severity &&
    (context.severity == "CRITICAL" || context.severity == "HIGH" || context.severity == "MEDIUM")
};

// Allow LOW findings (with warnings)
permit(
    principal,
    action,
    resource
) when {
    context has severity &&
    context.severity == "LOW"
};

// Allow INFO findings
permit(
    principal,
    action,
    resource
) when {
    context has severity &&
    context.severity == "INFO"
};

// Allow mature CoSAI models (level >= 2 for enhanced)
permit(
    principal,
    action,
    resource
) when {
    context has metadata_cosai_level_numeric &&
    context.metadata_cosai_level_numeric >= 2
};


