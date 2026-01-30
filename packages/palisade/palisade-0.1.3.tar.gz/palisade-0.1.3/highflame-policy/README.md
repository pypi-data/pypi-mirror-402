# highflame Policy Framework

A unified Cedar-based policy framework for the highflame security platform.

## Overview

The highflame Policy Framework provides a centralized, high-performance policy engine for authorization and security decisions across all highflame services. Built on Amazon's Cedar policy language, it offers:

- ✅ **Human-Readable Policies** - Clear, auditable policy definitions
- 🔒 **Formally Verified** - Cedar's formal verification prevents policy ambiguities
- 🚀 **High Performance** - Low-latency decisions for inline proxies
- 📊 **Full Traceability** - Every decision includes the determining policy IDs
- 🔌 **Flexible Deployment** - Use as library or gRPC sidecar service
- 🐍 **Python & Rust** - Native Rust library with zero-copy Python bindings

## Architecture

The framework is designed for two deployment modes:

1. **Library Mode** (Current) - Embedded directly in CLI tools like Palisade and Ramparts
2. **Sidecar Mode** (Future) - Deployed as a gRPC service for microservices like Guardrails

```
┌────────────────────────────────────────────────────────┐
│                   highflame Services                   │
├──────────────┬──────────────┬──────────────────────────┤
│   Ramparts   │  Guardrails  │      Palisade            │
│  (CLI Tool)  │ (Microservice)│    (CLI Tool)           │
└──────────────┴──────────────┴──────────────────────────┘
       │               │                    │
       │ (embedded)    │ (gRPC)             │ (embedded)
       │               │                    │
       ▼               ▼                    ▼
┌─────────────────────────────────────────────────────────┐
│           highflame Policy Engine (Cedar)               │
│  • Policy Evaluation                                    │
│  • Decision Traceability                                │
│  • Context Enrichment                                   │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │  Policy Files (Git/DB)│
            │  • ramparts/          │
            │  • guardrails/        │
            │  • palisade/          │
            └───────────────────────┘
```

## Quick Start

> **For developers**: See [`docs/DEVELOPING.md`](docs/DEVELOPING.md) for detailed development setup, testing, and contribution guidelines.

### Installation

#### For Rust Projects

Add to your `Cargo.toml`:

```toml
[dependencies]
highflame-policy = { path = "../highflame-policy" }
```

#### For Python Projects

Install from source (PyPI publication coming soon):

```bash
# Clone the repository
git clone https://github.com/highflame-io/highflame-policy
cd highflame-policy

# Install with maturin (requires Rust toolchain)
pip install maturin
maturin develop --features python --release

# Or build a wheel for production
maturin build --features python --release
pip install target/wheels/highflame_policy-*.whl
```

### Basic Usage (Rust)

```rust
use highflame_policy::{
    CedarPolicyEngine, PolicyEngine, PolicyRequest,
    EntityType, ActionType,
};
use std::collections::HashMap;

fn main() -> anyhow::Result<()> {
    // Create and configure engine
    let mut engine = CedarPolicyEngine::new()?;
    engine.load_policies_from_file("policies/ramparts/policy.cedar")?;

    // Make an authorization request
    let request = PolicyRequest::builder()
        .principal(EntityType::Scanner, "ramparts")
        .action(ActionType::ScanTarget)
        .resource(EntityType::Repository, "https://github.com/org/repo")
        .context("scan_type", "dependency")
        .build()?;

    // Evaluate the request
    let decision = engine.evaluate(&request)?;

    if decision.is_allowed() {
        println!("✅ Access granted");
        println!("   Policies: {:?}", decision.determining_policies());
    } else {
        println!("❌ Access denied");
        println!("   Reason: {}", decision.reason());
        println!("   Blocked by: {:?}", decision.determining_policies());
    }

    Ok(())
}
```

### Basic Usage (Python)

```python
from highflame_policy import PyCedarPolicyEngine

# Create the policy engine
engine = PyCedarPolicyEngine()

# Load Cedar policies
engine.load_policies_from_file("policies/palisade/policy.cedar")

# Evaluate a policy decision
decision = engine.evaluate(
    principal_type="Scanner",
    principal_id="palisade-scanner",
    action="scan_artifact",
    resource_type="Artifact",
    resource_id="/path/to/model.safetensors",
    context={
        "artifact_format": "safetensors",
        "finding_type": "pickle_execution_path_detected",
        "severity": "CRITICAL"
    }
)

print(f"Decision: {decision['effect']}")  # "allow", "deny", or "quarantine"
print(f"Reason: {decision['reason']}")
print(f"Determining Policies: {decision['determining_policies']}")

# Check the decision
if decision["is_denied"]:
    print("⛔ Access blocked!")
elif decision["is_quarantine"]:
    print("⚠️  Quarantined for manual review")
else:
    print("✅ Allowed")
```

#### Real-World Example: Security Scanner Integration

Here's how applications like Palisade use `highflame-policy`:

```python
from highflame_policy import PyCedarPolicyEngine, PolicyEffect

def evaluate_security_finding(engine, finding, artifact_info, environment="production"):
    """Evaluate a security finding using Cedar policies."""
    
    # Build context from your domain model
    context = {
        "finding_type": finding["type"],
        "severity": finding["severity"],
        "artifact_format": artifact_info["format"],
        "artifact_signed": artifact_info.get("signed", False),
        "environment": environment,
        # Add any domain-specific attributes
        "pickle_exec_path_detected": "pickle" in finding["type"],
    }
    
    # Evaluate with the generic API
    decision = engine.evaluate(
        principal_type="Scanner",
        principal_id="my-scanner",
        action="scan_artifact",
        resource_type="Artifact",
        resource_id=artifact_info["path"],
        context=context
    )
    
    return decision["effect"]

# Usage
engine = PyCedarPolicyEngine()
engine.load_policies_from_file("policies/my-app/policy.cedar")

finding = {"type": "pickle_execution_path", "severity": "CRITICAL"}
artifact = {"format": "pickle", "path": "/model.pkl", "signed": False}

effect = evaluate_security_finding(engine, finding, artifact, "production")

if effect == PolicyEffect.DENY:
    print("⛔ Blocked by policy")
elif effect == PolicyEffect.QUARANTINE:
    print("⚠️  Quarantined for review")
```

**Key Pattern:** Applications translate their domain models into Cedar context, then use the generic `evaluate()` method. Keep domain-specific logic in your application, not in `highflame-policy`.

### Using the Convenience API (Rust)

For common patterns, use the `PolicyEngineExt` trait:

```rust
use highflame_policy::{CedarPolicyEngine, PolicyEngineExt};
use std::collections::HashMap;

let engine = CedarPolicyEngine::new()?;
let context = HashMap::new();

// Check if a tool is allowed
let decision = engine.is_tool_allowed("mcp-client", "shell", context)?;
if decision.is_denied() {
    println!("Tool blocked by: {:?}", decision.determining_policies());
}
```

### Service-Specific Policy Loading

Use the `PolicyLoader` for service-specific policies:

```rust
use highflame_policy::{CedarPolicyEngine, PolicyLoader, ServiceId};

let loader = PolicyLoader::new("policies");
let mut engine = CedarPolicyEngine::new()?;

// Load Ramparts policies
loader.load_service_policies(ServiceId::Ramparts, &mut engine)?;
```

## Policy Files

Policy files are organized by service in the `policies/` directory:

```
policies/
├── ramparts/policy.cedar      # MCP scanner policies
├── guardrails/policy.cedar    # LLM proxy policies
└── palisade/policy.cedar      # Supply chain scanner policies
```

### Example Policy

```cedar
// @id("block-dangerous-tools")
// @description("Prevent execution of dangerous system tools")
forbid(
    principal,
    action == Action::"call_tool",
    resource
) when {
    ["shell", "exec", "eval"].contains(resource)
};
```

## Key Concepts

### Entities

**Principals** (who is acting):
- `User` - Human users
- `Agent` - AI agents
- `Scanner` - Security scanners
- `Service` - Service accounts
- `McpClient` - MCP client applications

**Resources** (what is being accessed):
- `Tool` - Functions/tools that can be called
- `Server` - MCP servers
- `Repository` - Code repositories
- `Package` - Software packages
- `FilePath` - File system paths
- `HttpEndpoint` - HTTP URLs
- `LlmPrompt` - LLM prompts
- `ScanTarget` - Security scan targets
- `Artifact` - ML model artifacts (Palisade)
- `Finding` - Security findings (Palisade)
- `Provenance` - Attestation data (Palisade)
- `Tokenizer` - Tokenizer artifacts (Palisade)

### Actions

**General Actions:**
- `call_tool` - Call a tool/function
- `connect_server` - Connect to an MCP server
- `http_request` - Make an HTTP request
- `read_file` / `write_file` - File operations
- `process_prompt` / `process_response` - LLM operations
- `scan_target` / `scan_package` - Security scans
- `flag_vulnerability` - Report vulnerabilities

**Palisade ML Security Actions:**
- `scan_artifact` - Scan ML model artifacts
- `validate_integrity` - Validate artifact integrity
- `validate_provenance` - Validate signatures/attestations
- `load_model` - Load/use an ML model
- `deploy_model` - Deploy model to production
- `quarantine_artifact` - Quarantine for manual review

### Context Attributes

Policies can use context attributes for fine-grained control:

```cedar
forbid(
    principal,
    action == Action::"http_request",
    resource
) when {
    // Block SSRF - no private IPs
    context has ip_address &&
    context.ip_address.isLoopback()
};
```

Common context attributes:

**General:**
- `server_name`, `tool_name`, `path`, `url`
- `hostname`, `ip_address`, `port`
- `prompt_text`, `response_size_mb`
- `scan_type`, `is_write`, `environment`

**Palisade ML Security:**
- `artifact_format` - Model format (safetensors, pickle, gguf, onnx)
- `artifact_signed` - Whether artifact is signed
- `finding_type`, `finding_severity` - Security findings
- `cosai_level_numeric` - CoSAI maturity level (0-4)
- `pickle_exec_path_detected` - Pickle RCE detection
- `tokenizer_added_tokens_count` - Token modifications

## Policy Effects

The framework supports three decision effects:

- **Allow** - Action is permitted
- **Deny** - Action is blocked
- **Quarantine** - Action is soft-denied for manual review (Palisade)

```rust
if decision.is_allowed() {
    // Proceed with action
} else if decision.is_quarantined() {
    // Flag for manual review
} else if decision.is_denied() {
    // Block action
}
```

## Decision Traceability

Every policy decision includes full traceability:

```rust
let decision = engine.evaluate(&request)?;

println!("Decision ID: {}", decision.decision_id());
println!("Effect: {:?}", decision.effect());
println!("Determining Policies: {:?}", decision.determining_policies());
println!("Reason: {}", decision.reason());
println!("Timestamp: {}", decision.timestamp());

// Convert to audit log format
let audit_log = decision.to_audit_log();
println!("{}", serde_json::to_string_pretty(&audit_log)?);
```

Output:
```json
{
  "decision_id": "550e8400-e29b-41d4-a716-446655440000",
  "effect": "Deny",
  "determining_policies": ["block-dangerous-tools"],
  "reason": "Tool 'shell' access denied by policy",
  "timestamp": "2025-10-22T12:34:56Z",
  "diagnostics": []
}
```

## Development

### Quick Setup

#### Rust Development

```bash
# Install Rust (if needed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Clone and setup
git clone https://github.com/highflame-io/highflame-policy
cd highflame-policy

# Build the library
cargo build
```

#### Python Development

```bash
# Install Rust + maturin (if needed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
pip install maturin

# Clone and setup
git clone https://github.com/highflame-io/highflame-policy
cd highflame-policy

# Build and install in development mode (hot reload on changes)
maturin develop --features python

# Make changes to Rust code, then rebuild
maturin develop --features python
```

### Testing

#### Rust Tests

```bash
# Run all tests
cargo test

# Run with output
cargo test -- --nocapture

# Run specific test
cargo test test_basic_policy_evaluation

# Run examples
cargo run --example basic_usage
cargo run --example palisade_usage

# Using Makefile
make test           # Run tests
make test-verbose   # With output
make examples       # Run all examples
```

#### Python Tests

```bash
# Build and install in development mode
maturin develop --features python

# Test the installation
python -c "from highflame_policy import PyCedarPolicyEngine; print('✓ Import successful')"

# Interactive testing
python
>>> from highflame_policy import PyCedarPolicyEngine
>>> engine = PyCedarPolicyEngine()
>>> engine.load_policies_from_file("policies/palisade/policy.cedar")
>>> print("✓ Engine loaded")
```

**See [`docs/DEVELOPING.md`](docs/DEVELOPING.md) for complete development guide.**

## Future Features

### Hot-Reload (Planned)

Enable policy hot-reloading:

```rust
let config = PolicyConfig::new(ServiceId::Ramparts, "policies/ramparts/policy.cedar")
    .with_hot_reload(5); // Check every 5 seconds

let loader = PolicyLoader::new("policies");
loader.load_with_config(&config, &mut engine)?;
```

### gRPC Sidecar (Planned)

Deploy as a sidecar service:

```rust
use highflame_policy::grpc::PolicySidecar;

let sidecar = PolicySidecar::new(config);
sidecar.serve("0.0.0.0:50051").await?;
```

Client usage:

```rust
let mut client = PolicyClient::connect("http://localhost:50051").await?;
let response = client.evaluate(request).await?;
```

### OPAL Integration (Planned)

Real-time policy updates via GitOps:

1. Commit policy changes to Git
2. OPAL server detects changes via webhook
3. OPAL client pulls updates
4. Policies hot-reload in all services

## Contributing

We welcome contributions! Please see [`docs/DEVELOPING.md`](docs/DEVELOPING.md) for:

- Development environment setup
- Code style guidelines
- Testing procedures
- Pull request process

### Quick Contribution Guide

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Make changes and add tests
4. Run checks: `make ci`
5. Submit Pull Request

### Adding Features

- **New entity types**: Edit `src/entities.rs`
- **New actions**: Edit `src/entities.rs`
- **New policies**: Add to `policies/<service>/`
- **Tests**: Add to `tests/` or inline in modules

## License

Apache-2.0

## Related Projects

- [Cedar](https://www.cedarpolicy.com/) - The policy language
- [OPAL](https://www.opal.ac/) - Open Policy Administration Layer
- [Highflame](https://highflame.com/) - Highflame security platform
