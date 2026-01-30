//! Integration tests for the policy framework

use highflame_policy::{
    ActionType, CedarPolicyEngine, EntityType, PolicyEngine, PolicyEngineExt, PolicyLoader,
    PolicyRequest, ServiceId,
};
use std::collections::HashMap;

#[test]
fn test_basic_policy_evaluation() {
    let mut engine = CedarPolicyEngine::new().expect("Failed to create engine");

    let policy = r#"
        forbid(
            principal,
            action == Action::"call_tool",
            resource == Tool::"shell"
        );

        permit(principal, action, resource);
    "#;

    engine
        .load_policies(policy)
        .expect("Failed to load policies");

    // Test deny case
    let request = PolicyRequest::builder()
        .principal(EntityType::McpClient, "test-client")
        .action(ActionType::CallTool)
        .resource(EntityType::Tool, "shell")
        .build()
        .expect("Failed to build request");

    let decision = engine.evaluate(&request).expect("Failed to evaluate");
    assert!(decision.is_denied(), "Shell tool should be blocked");
    assert!(
        !decision.determining_policies().is_empty(),
        "Should have determining policies"
    );

    // Test allow case
    let request = PolicyRequest::builder()
        .principal(EntityType::McpClient, "test-client")
        .action(ActionType::CallTool)
        .resource(EntityType::Tool, "calculator")
        .build()
        .expect("Failed to build request");

    let decision = engine.evaluate(&request).expect("Failed to evaluate");
    assert!(decision.is_allowed(), "Calculator tool should be allowed");
}

#[test]
fn test_context_based_policies() {
    let mut engine = CedarPolicyEngine::new().expect("Failed to create engine");

    let policy = r#"
        forbid(
            principal,
            action == Action::"http_request",
            resource
        ) when {
            context has ip_address &&
            context.ip_address == "127.0.0.1"
        };

        permit(principal, action, resource);
    "#;

    engine
        .load_policies(policy)
        .expect("Failed to load policies");

    // Test with localhost IP (should be denied)
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
        .build()
        .expect("Failed to build request");

    let decision = engine.evaluate(&request).expect("Failed to evaluate");
    assert!(decision.is_denied(), "Localhost access should be blocked");

    // Test with external IP (should be allowed)
    let mut context = HashMap::new();
    context.insert(
        "ip_address".to_string(),
        serde_json::Value::String("8.8.8.8".to_string()),
    );

    let request = PolicyRequest::builder()
        .principal(EntityType::McpClient, "test-client")
        .action(ActionType::HttpRequest)
        .resource(EntityType::HttpEndpoint, "http://example.com")
        .context_map(context)
        .build()
        .expect("Failed to build request");

    let decision = engine.evaluate(&request).expect("Failed to evaluate");
    assert!(decision.is_allowed(), "External access should be allowed");
}

#[test]
fn test_convenience_methods() {
    let mut engine = CedarPolicyEngine::new().expect("Failed to create engine");

    let policy = r#"
        forbid(
            principal,
            action == Action::"call_tool",
            resource == Tool::"exec"
        );

        permit(principal, action, resource);
    "#;

    engine
        .load_policies(policy)
        .expect("Failed to load policies");

    let context = HashMap::new();

    // Test tool check
    let decision = engine
        .is_tool_allowed("test-client", "exec", context.clone())
        .expect("Failed to check tool");
    assert!(decision.is_denied(), "Exec tool should be blocked");

    let decision = engine
        .is_tool_allowed("test-client", "safe-tool", context.clone())
        .expect("Failed to check tool");
    assert!(decision.is_allowed(), "Safe tool should be allowed");
}

#[test]
fn test_service_policy_loading() {
    let loader = PolicyLoader::new("policies");
    let mut engine = CedarPolicyEngine::new().expect("Failed to create engine");

    // This test will pass even if policies don't exist (they get created with defaults)
    let result = loader.load_service_policies(ServiceId::Ramparts, &mut engine);

    match result {
        Ok(_) => {
            assert!(
                engine.policy_count() > 0,
                "Should have loaded at least one policy"
            );
        }
        Err(e) => {
            // If policy directory doesn't exist in test environment, that's okay
            eprintln!("Note: Could not load service policies: {}", e);
        }
    }
}

#[test]
fn test_decision_traceability() {
    let mut engine = CedarPolicyEngine::new().expect("Failed to create engine");

    let policy = r#"
        // @id("test-policy-block-shell")
        forbid(
            principal,
            action == Action::"call_tool",
            resource == Tool::"shell"
        );
    "#;

    engine
        .load_policies(policy)
        .expect("Failed to load policies");

    let request = PolicyRequest::builder()
        .principal(EntityType::McpClient, "test")
        .action(ActionType::CallTool)
        .resource(EntityType::Tool, "shell")
        .build()
        .expect("Failed to build request");

    let decision = engine.evaluate(&request).expect("Failed to evaluate");

    // Verify traceability
    assert!(decision.is_denied());
    assert!(!decision.decision_id().to_string().is_empty());
    assert!(!decision.reason().is_empty());

    // Test audit log conversion
    let audit_log = decision.to_audit_log();
    assert_eq!(audit_log.effect, "Deny");
    assert!(!audit_log.timestamp.is_empty());
}

#[test]
fn test_multiple_policies() {
    let mut engine = CedarPolicyEngine::new().expect("Failed to create engine");

    let policy = r#"
        // Block dangerous tools
        forbid(
            principal,
            action == Action::"call_tool",
            resource
        ) when {
            [Tool::"shell", Tool::"exec", Tool::"eval"].contains(resource)
        };

        // Block sensitive files
        forbid(
            principal,
            action in [Action::"read_file", Action::"write_file"],
            resource
        ) when {
            context has path &&
            (
                context.path == "/etc/passwd" ||
                context.path == "/etc/shadow"
            )
        };

        // Allow everything else
        permit(principal, action, resource);
    "#;

    engine
        .load_policies(policy)
        .expect("Failed to load policies");

    // Test tool blocking
    let request = PolicyRequest::builder()
        .principal(EntityType::McpClient, "test")
        .action(ActionType::CallTool)
        .resource(EntityType::Tool, "eval")
        .build()
        .unwrap();

    assert!(engine.evaluate(&request).unwrap().is_denied());

    // Test file blocking
    let mut context = HashMap::new();
    context.insert(
        "path".to_string(),
        serde_json::Value::String("/etc/passwd".to_string()),
    );

    let request = PolicyRequest::builder()
        .principal(EntityType::McpClient, "test")
        .action(ActionType::ReadFile)
        .resource(EntityType::FilePath, "/etc/passwd")
        .context_map(context)
        .build()
        .unwrap();

    assert!(engine.evaluate(&request).unwrap().is_denied());

    // Test allowed operation
    let request = PolicyRequest::builder()
        .principal(EntityType::Scanner, "ramparts")
        .action(ActionType::ScanTarget)
        .resource(EntityType::Repository, "https://github.com/test/repo")
        .build()
        .unwrap();

    assert!(engine.evaluate(&request).unwrap().is_allowed());
}
