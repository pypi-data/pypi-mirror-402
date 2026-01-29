//! Example of loading and testing service-specific policies

use highflame_policy::{
    ActionType, CedarPolicyEngine, EntityType, PolicyEngine, PolicyLoader, PolicyRequest, ServiceId,
};

fn main() -> anyhow::Result<()> {
    println!("=== Service-Specific Policies Example ===\n");

    // Test Ramparts policies
    test_ramparts_policies()?;

    // Test Guardrails policies
    test_guardrails_policies()?;

    // Test Palisade policies
    test_palisade_policies()?;

    println!("\n=== All service policies tested ===");
    Ok(())
}

fn test_ramparts_policies() -> anyhow::Result<()> {
    println!("--- Testing Ramparts Policies ---");

    let loader = PolicyLoader::new("policies");
    let mut engine = CedarPolicyEngine::new()?;

    // Try to load Ramparts policies
    match loader.load_service_policies(ServiceId::Ramparts, &mut engine) {
        Ok(_) => println!(
            "✓ Loaded Ramparts policies ({} total)",
            engine.policy_count()
        ),
        Err(e) => println!("⚠ Could not load Ramparts policies: {}", e),
    }

    // Test: Scanner should be able to scan
    let request = PolicyRequest::builder()
        .principal(EntityType::Scanner, "ramparts")
        .action(ActionType::ScanTarget)
        .resource(EntityType::Repository, "https://github.com/org/repo")
        .build()?;

    if let Ok(decision) = engine.evaluate(&request) {
        println!(
            "  Scan permission: {}",
            if decision.is_allowed() { "✅" } else { "❌" }
        );
    }

    Ok(())
}

fn test_guardrails_policies() -> anyhow::Result<()> {
    println!("\n--- Testing Guardrails Policies ---");

    let loader = PolicyLoader::new("policies");
    let mut engine = CedarPolicyEngine::new()?;

    match loader.load_service_policies(ServiceId::Guardrails, &mut engine) {
        Ok(_) => println!(
            "✓ Loaded Guardrails policies ({} total)",
            engine.policy_count()
        ),
        Err(e) => println!("⚠ Could not load Guardrails policies: {}", e),
    }

    // Test: Should block dangerous tools
    let request = PolicyRequest::builder()
        .principal(EntityType::McpClient, "client")
        .action(ActionType::CallTool)
        .resource(EntityType::Tool, "shell")
        .build()?;

    if let Ok(decision) = engine.evaluate(&request) {
        println!(
            "  Shell tool blocking: {}",
            if decision.is_denied() { "✅" } else { "❌" }
        );
    }

    Ok(())
}

fn test_palisade_policies() -> anyhow::Result<()> {
    println!("\n--- Testing Palisade Policies ---");

    let loader = PolicyLoader::new("policies");
    let mut engine = CedarPolicyEngine::new()?;

    match loader.load_service_policies(ServiceId::Palisade, &mut engine) {
        Ok(_) => println!(
            "✓ Loaded Palisade policies ({} total)",
            engine.policy_count()
        ),
        Err(e) => println!("⚠ Could not load Palisade policies: {}", e),
    }

    // Test: Should allow package scanning
    let request = PolicyRequest::builder()
        .principal(EntityType::Scanner, "palisade")
        .action(ActionType::ScanPackage)
        .resource(EntityType::Package, "express@4.18.0")
        .build()?;

    if let Ok(decision) = engine.evaluate(&request) {
        println!(
            "  Package scan permission: {}",
            if decision.is_allowed() { "✅" } else { "❌" }
        );
    }

    Ok(())
}
