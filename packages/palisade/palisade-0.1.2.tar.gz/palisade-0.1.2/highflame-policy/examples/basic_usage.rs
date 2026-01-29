//! Basic usage example for the Highflame Policy Framework

use highflame_policy::{ActionType, CedarPolicyEngine, EntityType, PolicyEngine, PolicyRequest};
use std::collections::HashMap;

fn main() -> anyhow::Result<()> {
    println!("=== Highflame Policy Framework - Basic Usage ===\n");

    // Create a new policy engine
    let mut engine = CedarPolicyEngine::new()?;
    println!("✓ Created policy engine");

    // Load a simple policy
    let policy = r#"
        // Block dangerous tools
        forbid(
            principal,
            action == Action::"call_tool",
            resource == Tool::"shell"
        );

        // Allow safe tools
        permit(
            principal,
            action == Action::"call_tool",
            resource
        );
    "#;

    engine.load_policies(policy)?;
    println!("✓ Loaded {} policies\n", engine.policy_count());

    // Test 1: Try to call a safe tool (should be allowed)
    println!("Test 1: Calling safe tool 'calculator'");
    let request = PolicyRequest::builder()
        .principal(EntityType::McpClient, "test-client")
        .action(ActionType::CallTool)
        .resource(EntityType::Tool, "calculator")
        .build()?;

    let decision = engine.evaluate(&request)?;
    print_decision(&decision);

    // Test 2: Try to call a dangerous tool (should be denied)
    println!("\nTest 2: Calling dangerous tool 'shell'");
    let request = PolicyRequest::builder()
        .principal(EntityType::McpClient, "test-client")
        .action(ActionType::CallTool)
        .resource(EntityType::Tool, "shell")
        .build()?;

    let decision = engine.evaluate(&request)?;
    print_decision(&decision);

    // Test 3: Using context attributes
    println!("\nTest 3: Using context attributes");
    let policy_with_context = r#"
        forbid(
            principal,
            action == Action::"http_request",
            resource
        ) when {
            context has ip_address &&
            context.ip_address == "127.0.0.1"
        };

        permit(
            principal,
            action == Action::"http_request",
            resource
        );
    "#;

    engine.load_policies(policy_with_context)?;

    let mut context = HashMap::new();
    context.insert(
        "ip_address".to_string(),
        serde_json::Value::String("127.0.0.1".to_string()),
    );

    let request = PolicyRequest::builder()
        .principal(EntityType::McpClient, "test-client")
        .action(ActionType::HttpRequest)
        .resource(EntityType::HttpEndpoint, "http://localhost:8080")
        .context_map(context)
        .build()?;

    let decision = engine.evaluate(&request)?;
    print_decision(&decision);

    println!("\n=== Example completed ===");
    Ok(())
}

fn print_decision(decision: &highflame_policy::PolicyDecision) {
    if decision.is_allowed() {
        println!("  ✅ ALLOWED");
    } else {
        println!("  ❌ DENIED");
    }

    println!("  Decision ID: {}", decision.decision_id());
    println!("  Reason: {}", decision.reason());

    if !decision.determining_policies().is_empty() {
        println!(
            "  Determining Policies: {:?}",
            decision.determining_policies()
        );
    }
}
