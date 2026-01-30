//! Palisade policy usage example

use highflame_policy::{
    ActionType, CedarPolicyEngine, EntityType, PolicyEngine, PolicyLoader, PolicyRequest, ServiceId,
};
use std::collections::HashMap;

fn main() -> anyhow::Result<()> {
    println!("=== Palisade ML Security Policy Example ===\n");

    // Create and load Palisade policies
    let mut engine = CedarPolicyEngine::new()?;
    let loader = PolicyLoader::new("policies");

    match loader.load_service_policies(ServiceId::Palisade, &mut engine) {
        Ok(_) => println!(
            "✓ Loaded Palisade policies ({} total)\n",
            engine.policy_count()
        ),
        Err(e) => {
            eprintln!("⚠ Could not load Palisade policies: {}", e);
            eprintln!("Creating policies directory...\n");
        }
    }

    // Test 1: Block pickle file with execution paths
    println!("Test 1: Scanning pickle file with execution paths (CRITICAL)");
    test_pickle_execution_path(&engine)?;

    // Test 2: Quarantine unsigned model
    println!("\nTest 2: Loading unsigned safetensors model (QUARANTINE)");
    test_unsigned_model(&engine)?;

    // Test 3: Allow high CoSAI compliance model
    println!("\nTest 3: Loading high CoSAI Level 3 model (ALLOW)");
    test_high_cosai_model(&engine)?;

    // Test 4: Block model in production with high severity finding
    println!("\nTest 4: Deploying model with HIGH severity in production (BLOCK)");
    test_production_strict(&engine)?;

    // Test 5: Allow development environment with medium severity
    println!("\nTest 5: Loading model in dev with MEDIUM severity (ALLOW)");
    test_dev_permissive(&engine)?;

    // Test 6: Block tokenizer with excessive modifications
    println!("\nTest 6: Loading tokenizer with excessive token count (BLOCK)");
    test_excessive_tokenizer(&engine)?;

    println!("\n=== All Palisade policy tests completed ===");
    Ok(())
}

fn test_pickle_execution_path(engine: &CedarPolicyEngine) -> anyhow::Result<()> {
    let mut context = HashMap::new();
    context.insert(
        "pickle_exec_path_detected".to_string(),
        serde_json::Value::Bool(true),
    );
    context.insert(
        "artifact_format".to_string(),
        serde_json::Value::String("pickle".to_string()),
    );

    let request = PolicyRequest::builder()
        .principal(EntityType::Scanner, "palisade")
        .action(ActionType::LoadModel)
        .resource(EntityType::Artifact, "model.pkl")
        .context_map(context)
        .build()?;

    let decision = engine.evaluate(&request)?;
    print_decision(&decision, "Pickle with RCE risk");
    Ok(())
}

fn test_unsigned_model(engine: &CedarPolicyEngine) -> anyhow::Result<()> {
    let mut context = HashMap::new();
    context.insert(
        "artifact_signed".to_string(),
        serde_json::Value::Bool(false),
    );
    context.insert(
        "artifact_format".to_string(),
        serde_json::Value::String("safetensors".to_string()),
    );

    let request = PolicyRequest::builder()
        .principal(EntityType::Scanner, "palisade")
        .action(ActionType::LoadModel)
        .resource(EntityType::Artifact, "llama-2-7b.safetensors")
        .context_map(context)
        .build()?;

    let decision = engine.evaluate(&request)?;
    print_decision(&decision, "Unsigned model");
    Ok(())
}

fn test_high_cosai_model(engine: &CedarPolicyEngine) -> anyhow::Result<()> {
    let mut context = HashMap::new();
    context.insert(
        "cosai_level_numeric".to_string(),
        serde_json::Value::Number(3.into()),
    );
    context.insert(
        "cosai_compliance".to_string(),
        serde_json::Value::Bool(true),
    );
    context.insert(
        "artifact_format".to_string(),
        serde_json::Value::String("safetensors".to_string()),
    );

    let request = PolicyRequest::builder()
        .principal(EntityType::Scanner, "palisade")
        .action(ActionType::LoadModel)
        .resource(EntityType::Artifact, "verified-model.safetensors")
        .context_map(context)
        .build()?;

    let decision = engine.evaluate(&request)?;
    print_decision(&decision, "High CoSAI compliance");
    Ok(())
}

fn test_production_strict(engine: &CedarPolicyEngine) -> anyhow::Result<()> {
    let mut context = HashMap::new();
    context.insert(
        "environment".to_string(),
        serde_json::Value::String("production".to_string()),
    );
    context.insert(
        "finding_severity".to_string(),
        serde_json::Value::String("HIGH".to_string()),
    );

    let request = PolicyRequest::builder()
        .principal(EntityType::Scanner, "palisade")
        .action(ActionType::DeployModel)
        .resource(EntityType::Artifact, "risky-model.onnx")
        .context_map(context)
        .build()?;

    let decision = engine.evaluate(&request)?;
    print_decision(&decision, "Production with HIGH severity");
    Ok(())
}

fn test_dev_permissive(engine: &CedarPolicyEngine) -> anyhow::Result<()> {
    let mut context = HashMap::new();
    context.insert(
        "environment".to_string(),
        serde_json::Value::String("development".to_string()),
    );
    context.insert(
        "finding_severity".to_string(),
        serde_json::Value::String("MEDIUM".to_string()),
    );

    let request = PolicyRequest::builder()
        .principal(EntityType::Scanner, "palisade")
        .action(ActionType::LoadModel)
        .resource(EntityType::Artifact, "experimental-model.gguf")
        .context_map(context)
        .build()?;

    let decision = engine.evaluate(&request)?;
    print_decision(&decision, "Dev environment");
    Ok(())
}

fn test_excessive_tokenizer(engine: &CedarPolicyEngine) -> anyhow::Result<()> {
    let mut context = HashMap::new();
    context.insert(
        "tokenizer_added_tokens_count".to_string(),
        serde_json::Value::Number(1500.into()),
    );

    let request = PolicyRequest::builder()
        .principal(EntityType::Scanner, "palisade")
        .action(ActionType::LoadModel)
        .resource(EntityType::Tokenizer, "custom-tokenizer")
        .context_map(context)
        .build()?;

    let decision = engine.evaluate(&request)?;
    print_decision(&decision, "Excessive token modifications");
    Ok(())
}

fn print_decision(decision: &highflame_policy::PolicyDecision, test_name: &str) {
    println!("  Scenario: {}", test_name);

    if decision.is_allowed() {
        println!("  ✅ ALLOWED");
    } else if decision.is_quarantined() {
        println!("  ⚠️  QUARANTINED");
    } else {
        println!("  ❌ BLOCKED");
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
