// Guardrails Security Policies
// Service: LLM Proxy Layer
//
// This policy file controls the guardrails proxy, which sits between
// AI agents and external services, enforcing security boundaries.

// @id("guardrails-block-dangerous-tools")
// @description("Block dangerous tool execution")
forbid(
    principal,
    action == Action::"call_tool",
    resource
) when {
    ["shell", "exec", "eval", "system"].contains(resource)
};

// @id("guardrails-block-sensitive-files")
// @description("Block access to sensitive system files")
forbid(
    principal,
    action in [Action::"read_file", Action::"write_file"],
    resource
) when {
    context.path.like("/etc/shadow") ||
    context.path.like("/etc/passwd") ||
    context.path.like("*/.ssh/*") ||
    context.path.like("*/.aws/*") ||
    context.path.like("*/.env*")
};

// @id("guardrails-block-ssrf")
// @description("Block SSRF attacks - prevent access to private IPs")
forbid(
    principal,
    action == Action::"http_request",
    resource
) when {
    context has ip_address &&
    (context.ip_address.isLoopback() || context.ip_address.isPrivate())
};

// @id("guardrails-block-prompt-injection")
// @description("Block common prompt injection patterns")
forbid(
    principal,
    action == Action::"process_prompt",
    resource
) when {
    context has prompt_text &&
    (
        context.prompt_text.like("*ignore all previous instructions*") ||
        context.prompt_text.like("*forget what I told you*") ||
        context.prompt_text.like("*you are now in*") ||
        context.prompt_text.like("*system:*") ||
        context.prompt_text.like("*jailbreak*") ||
        context.prompt_text.like("*bypass*restrictions*")
    )
};

// @id("guardrails-limit-response-size")
// @description("Limit response data size to prevent memory exhaustion")
forbid(
    principal,
    action == Action::"process_response",
    resource
) when {
    context has response_size_mb &&
    context.response_size_mb > 100
};

// @id("guardrails-allow-safe-operations")
// @description("Allow safe operations by default")
permit(
    principal,
    action,
    resource
);

