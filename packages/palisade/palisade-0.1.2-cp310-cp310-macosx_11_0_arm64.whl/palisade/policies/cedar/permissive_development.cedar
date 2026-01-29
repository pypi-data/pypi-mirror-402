// Palisade Security Policy: permissive_development
// Description: Permissive policy for development and research environments
// Security Level: low
// 
// Behavior:
//   - CRITICAL findings: DENY (always blocked for safety)
//   - HIGH findings: ALLOW (with warnings)
//   - MEDIUM findings: ALLOW
//   - LOW/INFO findings: ALLOW
//   - Allows unsigned models
//   - Allows missing provenance
//   - Flexible tokenizer limits (up to 5000 tokens)
//   - Allows integrity issues for experimentation
//
// Usage:
//   palisade scan model.safetensors --policy permissive_development

// ==============================================================================
// UNIVERSAL CRITICAL BLOCKS (Always enforced, even in development)
// ==============================================================================

// Always block SafeTensors streaming/integrity errors (corrupted files)
forbid(
    principal,
    action,
    resource
) when {
    context has finding_type &&
    (
        context.finding_type == "safetensors_streaming_error" ||
        context.finding_type == "safetensors_header_corruption" ||
        context.finding_type == "safetensors_size_mismatch"
    )
};

// Always block confirmed malicious patterns
forbid(
    principal,
    action,
    resource
) when {
    context has finding_type &&
    context has severity &&
    context.severity == "CRITICAL" &&
    (
        context.finding_type == "backdoor_detected" ||
        context.finding_type == "trojan_detected" ||
        context.finding_type == "data_exfiltration_detected" ||
        context.finding_type == "supply_chain_attack" ||
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

// Block CRITICAL severity findings
forbid(
    principal,
    action,
    resource
) when {
    context has severity &&
    context.severity == "CRITICAL"
};

// ==============================================================================
// PERMISSIVE DEVELOPMENT - FLEXIBLE FOR RESEARCH
// ==============================================================================

// Allow unsigned models (except CRITICAL)
permit(
    principal,
    action,
    resource
) when {
    context has artifact_signed &&
    context.artifact_signed == false &&
    context has severity &&
    context.severity != "CRITICAL"
};

// Allow missing provenance
permit(
    principal,
    action,
    resource
) when {
    context has finding_type &&
    (
        context.finding_type == "missing_provenance_documents" ||
        context.finding_type == "unofficial_model_source" ||
        context.finding_type == "incomplete_attestation" ||
        context.finding_type == "unknown_model_family"
    )
};

// Flexible tokenizer policy (up to 5000 tokens for research)
permit(
    principal,
    action,
    resource
) when {
    context has tokenizer_added_tokens_count &&
    context.tokenizer_added_tokens_count <= 5000
};

// Allow adapter mismatches for experimentation
permit(
    principal,
    action,
    resource
) when {
    context has adapter_base_digest_mismatch &&
    context.adapter_base_digest_mismatch == true
};

// Allow integrity issues (except CRITICAL)
permit(
    principal,
    action,
    resource
) when {
    (
        (context has safetensors_integrity_violation && context.safetensors_integrity_violation == true) ||
        (context has gguf_suspicious_metadata && context.gguf_suspicious_metadata == true)
    ) &&
    context has severity &&
    context.severity != "CRITICAL"
};

// Allow HIGH, MEDIUM, LOW, INFO findings
permit(
    principal,
    action,
    resource
) when {
    context has severity &&
    (context.severity == "HIGH" || context.severity == "MEDIUM" || context.severity == "LOW" || context.severity == "INFO")
};

// Allow all CoSAI maturity levels
permit(
    principal,
    action,
    resource
) when {
    context has metadata_cosai_level_numeric
};


