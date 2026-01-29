// Palisade Security Policy: strict_production
// Description: Strict production policy with maximum security
// Security Level: critical
// 
// Behavior:
//   - CRITICAL findings: DENY
//   - HIGH findings: DENY
//   - MEDIUM findings: DENY
//   - LOW/INFO findings: ALLOW
//   - Requires signed artifacts
//   - Requires provenance documentation
//   - Blocks pickle format entirely
//   - Enforces CoSAI maturity level >= 3
//
// Usage:
//   palisade scan model.safetensors --policy strict_production

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
// STRICT PRODUCTION - MAXIMUM SECURITY
// ==============================================================================

// Zero tolerance for pickle format
forbid(
    principal,
    action,
    resource
) when {
    context has artifact_format &&
    context.artifact_format == "pickle"
};

// Require signed artifacts
forbid(
    principal,
    action,
    resource
) when {
    context has artifact_signed &&
    context.artifact_signed == false
};

// Block unsigned/unknown signers
forbid(
    principal,
    action,
    resource
) when {
    context has provenance_signer &&
    (context.provenance_signer == "unknown" || context.provenance_signer == "unsigned")
};

// Strict tokenizer limits (max 50 added tokens)
forbid(
    principal,
    action,
    resource
) when {
    context has tokenizer_added_tokens_count &&
    context.tokenizer_added_tokens_count > 50
};

// Block all integrity violations
forbid(
    principal,
    action,
    resource
) when {
    (context has safetensors_integrity_violation && context.safetensors_integrity_violation == true) ||
    (context has gguf_suspicious_metadata && context.gguf_suspicious_metadata == true) ||
    (context has adapter_base_digest_mismatch && context.adapter_base_digest_mismatch == true)
};

// Require provenance documentation
forbid(
    principal,
    action,
    resource
) when {
    context has finding_type &&
    (
        context.finding_type == "missing_provenance_documents" ||
        context.finding_type == "incomplete_attestation" ||
        context.finding_type == "unofficial_model_source" ||
        context.finding_type == "unknown_model_family"
    )
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

// Enforce CoSAI maturity level >= 3
forbid(
    principal,
    action,
    resource
) when {
    context has metadata_cosai_level_numeric &&
    context.metadata_cosai_level_numeric < 3
};

// Allow LOW and INFO findings only
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

