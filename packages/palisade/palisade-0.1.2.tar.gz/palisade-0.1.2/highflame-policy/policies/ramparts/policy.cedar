// Ramparts Security Policies
// Service: MCP Server Scanner
//
// This policy file controls access for Ramparts, which scans MCP servers
// for security vulnerabilities and compliance issues.

// @id("ramparts-allow-scanning")
// @description("Allow ramparts to scan MCP servers and repositories")
permit(
    principal == Scanner::"ramparts",
    action in [Action::"scan_target", Action::"scan_package"],
    resource
);

// @id("ramparts-allow-tool-calls")
// @description("Allow scanning of MCP tools")
permit(
    principal,
    action == Action::"call_tool",
    resource
) when {
    // Allow most tools for scanning purposes
    !["exec", "shell", "eval"].contains(resource)
};

// @id("ramparts-allow-file-read")
// @description("Allow reading files for scanning")
permit(
    principal,
    action == Action::"read_file",
    resource
) when {
    // Allow reading most files, but block sensitive system files
    !context.path.like("/etc/shadow") &&
    !context.path.like("/etc/passwd") &&
    !context.path.like("*/.ssh/id_rsa*")
};

// @id("ramparts-block-file-write")
// @description("Scanners should not write files")
forbid(
    principal == Scanner::"ramparts",
    action == Action::"write_file",
    resource
);

// @id("ramparts-allow-http")
// @description("Allow HTTP requests for MCP server scanning")
permit(
    principal,
    action == Action::"http_request",
    resource
) when {
    // Block SSRF attacks - no private IPs
    !["127.0.0.1", "localhost", "0.0.0.0"].contains(context.hostname) &&
    !context has ip_address ||
    (!context.ip_address.isLoopback() && !context.ip_address.isPrivate())
};

// @id("ramparts-allow-server-connection")
// @description("Allow connecting to MCP servers for scanning")
permit(
    principal,
    action == Action::"connect_server",
    resource
);

