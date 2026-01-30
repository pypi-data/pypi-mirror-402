// Palisade Security Policies
// Service: ML Supply Chain Security Scanner
//
// This policy supports multiple environments through context.environment:
// - "production" / "strict_production" - Maximum security
// - "development" / "permissive_development" - Flexible for research
// - "default" - Balanced security
//
// Usage:
//   palisade scan model.safetensors --policy strict_production
//   palisade scan model.safetensors --policy permissive_development

// ==============================================================================
// PRODUCTION ENVIRONMENT - STRICT POLICIES
// ==============================================================================

// Zero tolerance for pickle in production
forbid(
    principal,
    action,
    resource
) when {
    context has environment &&
    (context.environment == "production" || context.environment == "strict_production") &&
    context has artifact_format &&
    context.artifact_format == "pickle"
};

// Require signed artifacts in production
forbid(
    principal,
    action,
    resource
) when {
    context has environment &&
    (context.environment == "production" || context.environment == "strict_production") &&
    context has artifact_signed &&
    context.artifact_signed == false
};

// Block unsigned models in production
forbid(
    principal,
    action,
    resource
) when {
    context has environment &&
    (context.environment == "production" || context.environment == "strict_production") &&
    context has provenance_signer &&
    (context.provenance_signer == "unknown" || context.provenance_signer == "unsigned")
};

// Strict tokenizer limits in production (max 50 added tokens)
forbid(
    principal,
    action,
    resource
) when {
    context has environment &&
    (context.environment == "production" || context.environment == "strict_production") &&
    context has tokenizer_added_tokens_count &&
    context.tokenizer_added_tokens_count > 50
};

// Block integrity violations in production
forbid(
    principal,
    action,
    resource
) when {
    context has environment &&
    (context.environment == "production" || context.environment == "strict_production") &&
    (
        (context has safetensors_integrity_violation && context.safetensors_integrity_violation == true) ||
        (context has gguf_suspicious_metadata && context.gguf_suspicious_metadata == true) ||
        (context has adapter_base_digest_mismatch && context.adapter_base_digest_mismatch == true)
    )
};

// Require provenance in production
forbid(
    principal,
    action,
    resource
) when {
    context has environment &&
    (context.environment == "production" || context.environment == "strict_production") &&
    context has finding_type &&
    (
        context.finding_type == "missing_provenance_documents" ||
        context.finding_type == "incomplete_attestation" ||
        context.finding_type == "unofficial_model_source" ||
        context.finding_type == "unknown_model_family"
    )
};

// Production severity overrides - block HIGH and above
forbid(
    principal,
    action,
    resource
) when {
    context has environment &&
    (context.environment == "production" || context.environment == "strict_production") &&
    context has severity &&
    (context.severity == "CRITICAL" || context.severity == "HIGH" || context.severity == "MEDIUM")
};

// ==============================================================================
// DEVELOPMENT ENVIRONMENT - PERMISSIVE POLICIES  
// ==============================================================================

// Allow unsigned models in development (except CRITICAL)
permit(
    principal,
    action,
    resource
) when {
    context has environment &&
    (context.environment == "development" || context.environment == "permissive_development" || context.environment == "research") &&
    context has artifact_signed &&
    context.artifact_signed == false &&
    context has severity &&
    context.severity != "CRITICAL"
};

// Allow missing provenance in development
permit(
    principal,
    action,
    resource
) when {
    context has environment &&
    (context.environment == "development" || context.environment == "permissive_development" || context.environment == "research") &&
    context has finding_type &&
    (
        context.finding_type == "missing_provenance_documents" ||
        context.finding_type == "unofficial_model_source"
    )
};

// Flexible tokenizer policy for research (up to 5000 tokens)
permit(
    principal,
    action,
    resource
) when {
    context has environment &&
    (context.environment == "development" || context.environment == "permissive_development" || context.environment == "research") &&
    context has tokenizer_added_tokens_count &&
    context.tokenizer_added_tokens_count <= 5000
};

// Allow adapter mismatches in development
permit(
    principal,
    action,
    resource
) when {
    context has environment &&
    (context.environment == "development" || context.environment == "permissive_development") &&
    context has adapter_base_digest_mismatch &&
    context.adapter_base_digest_mismatch == true
};

// Allow integrity issues in development (for experimentation)
permit(
    principal,
    action,
    resource
) when {
    context has environment &&
    (context.environment == "development" || context.environment == "permissive_development") &&
    (
        (context has safetensors_integrity_violation && context.safetensors_integrity_violation == true) ||
        (context has gguf_suspicious_metadata && context.gguf_suspicious_metadata == true)
    ) &&
    context has severity &&
    context.severity != "CRITICAL"
};

// Development severity overrides - allow MEDIUM and below
permit(
    principal,
    action,
    resource
) when {
    context has environment &&
    (context.environment == "development" || context.environment == "permissive_development") &&
    context has severity &&
    (context.severity == "MEDIUM" || context.severity == "LOW" || context.severity == "INFO")
};

// ==============================================================================
// UNIVERSAL CRITICAL BLOCKS (ALL ENVIRONMENTS)
// ==============================================================================

// Always block SafeTensors streaming/integrity errors (corrupted or malicious files)
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

// Always block confirmed backdoor detections (HIGH severity or above)
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

// Block behavioral backdoor indicators only if HIGH confidence
// (MEDIUM severity with few matches in large models = likely noise)
forbid(
    principal,
    action,
    resource
) when {
    context has finding_type &&
    context.finding_type == "behavioral_backdoor_indicators" &&
    context has severity &&
    context.severity == "HIGH" &&
    // Additional confidence check: block if multiple strong indicators
    context has match_count &&
    context.match_count >= 5
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
// DEFAULT ENVIRONMENT - BALANCED SECURITY
// ==============================================================================

// Block CRITICAL findings by default
forbid(
    principal,
    action,
    resource
) when {
    context has severity &&
    context.severity == "CRITICAL"
};

// Quarantine HIGH findings by default (unless in development)
forbid(
    principal,
    action,
    resource
) when {
    context has severity &&
    context.severity == "HIGH" &&
    !(context has environment && 
      (context.environment == "development" || 
       context.environment == "permissive_development" ||
       context.environment == "research"))
};

// ==============================================================================
// DEFAULT ENVIRONMENT - BALANCED SECURITY
// ==============================================================================

// Allow MEDIUM findings in default environment (balanced approach)
// User sees warnings but can proceed - trust but verify
permit(
    principal,
    action,
    resource
) when {
    context has severity &&
    context.severity == "MEDIUM" &&
    // Only if not in production (production blocks MEDIUM explicitly above)
    !(context has environment && 
      (context.environment == "production" || context.environment == "strict_production"))
};

// Allow LOW and INFO by default (all environments)
permit(
    principal,
    action,
    resource
) when {
    context has severity &&
    (context.severity == "LOW" || context.severity == "INFO")
};

// CoSAI maturity level enforcement - block immature models in production
forbid(
    principal,
    action,
    resource
) when {
    context has environment &&
    (context.environment == "production" || context.environment == "strict_production") &&
    context has metadata_cosai_level_numeric &&
    context.metadata_cosai_level_numeric < 3
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
