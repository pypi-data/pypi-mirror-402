//! Cedar policy engine implementation
//!
//! This module provides the Cedar-based implementation of the PolicyEngine trait.

use crate::core::{PolicyEngine, PolicyEngineExt, PolicyEvaluationContext};
use crate::decision::PolicyDecision;
use crate::entities::{ActionType, EntityType};
use crate::error::{PolicyError, Result};
use crate::request::{PolicyRequest, PolicyRequestBuilder};
use cedar_policy::{Authorizer, Context, Decision, Entities, EntityUid, PolicySet, Request};
use std::str::FromStr;
use tracing::{debug, info};

/// Cedar policy engine implementation
///
/// This is the primary policy engine implementation using Amazon's Cedar
/// policy language. Cedar provides:
/// - Human-readable policies
/// - Formal verification
/// - High performance
/// - Fine-grained access control
pub struct CedarPolicyEngine {
    /// Cedar authorizer instance
    authorizer: Authorizer,

    /// Loaded policy set
    policies: PolicySet,

    /// Entity store (for entity relationships)
    entities: Entities,
}

impl CedarPolicyEngine {
    /// Create a new Cedar policy engine
    pub fn new() -> Result<Self> {
        debug!("Creating new Cedar policy engine");
        Ok(Self {
            authorizer: Authorizer::new(),
            policies: PolicySet::new(),
            entities: Entities::empty(),
        })
    }

    /// Set the entity store
    ///
    /// Entities can be used to define relationships and hierarchies
    /// (e.g., a user belongs to a group). For most simple use cases,
    /// an empty entity store is sufficient.
    pub fn set_entities(&mut self, entities: Entities) {
        self.entities = entities;
    }

    /// Extract policy IDs from determining policies iterator
    ///
    /// Cedar provides policy IDs in the format "PolicyId(\"policy-name\")"
    /// This extracts the actual policy name for cleaner audit logs.
    fn extract_policy_ids<'a, I>(&self, cedar_policies: I) -> Vec<String>
    where
        I: Iterator<Item = &'a cedar_policy::PolicyId>,
    {
        cedar_policies
            .map(|pid| {
                // Convert PolicyId to string and extract the actual ID
                let pid_str = format!("{pid}");
                // Remove the PolicyId wrapper: PolicyId("name") -> name
                pid_str
                    .strip_prefix("PolicyId(\"")
                    .and_then(|s| s.strip_suffix("\")"))
                    .unwrap_or(&pid_str)
                    .to_string()
            })
            .collect()
    }
}

impl PolicyEngine for CedarPolicyEngine {
    fn load_policies(&mut self, policy_text: &str) -> Result<()> {
        debug!("Loading Cedar policies from string");

        self.policies = PolicySet::from_str(policy_text).map_err(|e| {
            PolicyError::PolicyParsing(format!("Failed to parse Cedar policies: {e}"))
        })?;

        info!("Successfully loaded {} Cedar policies", self.policy_count());
        Ok(())
    }

    fn load_policies_from_file(&mut self, path: &str) -> Result<()> {
        info!("Loading Cedar policies from file: {}", path);

        let policy_text = std::fs::read_to_string(path).map_err(|e| {
            PolicyError::PolicyLoading(format!("Failed to read policy file '{path}': {e}"))
        })?;

        self.load_policies(&policy_text)?;
        info!("Successfully loaded policies from: {}", path);
        Ok(())
    }

    fn evaluate(&self, request: &PolicyRequest) -> Result<PolicyDecision> {
        debug!(
            "Evaluating policy: {} -> {} on {}",
            request.principal_uid(),
            request.action_uid(),
            request.resource_uid()
        );

        // Convert request to Cedar format
        let principal_uid = EntityUid::from_str(&request.principal_uid())
            .map_err(|e| PolicyError::InvalidEntityUid(format!("Invalid principal UID: {e}")))?;

        let action_uid = EntityUid::from_str(&request.action_uid())
            .map_err(|e| PolicyError::InvalidAction(format!("Invalid action UID: {e}")))?;

        let resource_uid = EntityUid::from_str(&request.resource_uid())
            .map_err(|e| PolicyError::InvalidEntityUid(format!("Invalid resource UID: {e}")))?;

        // Convert context to Cedar Context
        let context_value = serde_json::to_value(request.context()).map_err(|e| {
            PolicyError::InvalidContext(format!("Failed to serialize context: {e}"))
        })?;

        let cedar_context = Context::from_json_value(context_value, None)
            .map_err(|e| PolicyError::InvalidContext(format!("Invalid context for Cedar: {e}")))?;

        // Create Cedar request
        let cedar_request =
            Request::new(principal_uid, action_uid, resource_uid, cedar_context, None).map_err(
                |e| PolicyError::RequestCreation(format!("Failed to create Cedar request: {e}")),
            )?;

        // Evaluate the request
        let response =
            self.authorizer
                .is_authorized(&cedar_request, &self.policies, &self.entities);

        // Extract determining policy IDs (reason() returns an iterator in cedar-policy 4.7+)
        let determining_policies = self.extract_policy_ids(response.diagnostics().reason());

        // Build decision based on Cedar's response
        let decision = match response.decision() {
            Decision::Allow => {
                debug!("Policy decision: ALLOW");
                let reason = if determining_policies.is_empty() {
                    "No deny policies matched (default allow)".to_string()
                } else {
                    format!("Allowed by policies: {}", determining_policies.join(", "))
                };
                PolicyDecision::allow(determining_policies, reason)
            }
            Decision::Deny => {
                debug!("Policy decision: DENY");
                let reason = if determining_policies.is_empty() {
                    "No allow policies matched (default deny)".to_string()
                } else {
                    format!("Denied by policies: {}", determining_policies.join(", "))
                };
                PolicyDecision::deny(determining_policies, reason)
            }
        };

        // Add any Cedar diagnostics as policy diagnostics (errors() returns an iterator)
        let diagnostics: Vec<String> = response
            .diagnostics()
            .errors()
            .map(|e| format!("Cedar error: {e}"))
            .collect();

        Ok(if diagnostics.is_empty() {
            decision
        } else {
            decision.with_diagnostics(diagnostics)
        })
    }

    fn policy_count(&self) -> usize {
        self.policies.policies().count()
    }

    fn clear_policies(&mut self) {
        debug!("Clearing all policies");
        self.policies = PolicySet::new();
    }
}

impl PolicyEngineExt for CedarPolicyEngine {
    fn is_tool_allowed(
        &self,
        principal_id: &str,
        tool_name: &str,
        mut context: PolicyEvaluationContext,
    ) -> Result<PolicyDecision> {
        // Add tool name to context for policy evaluation
        context.insert(
            "tool_name".to_string(),
            serde_json::Value::String(tool_name.to_string()),
        );

        let request = PolicyRequestBuilder::new()
            .principal(EntityType::McpClient, principal_id)
            .action(ActionType::CallTool)
            .resource(EntityType::Tool, tool_name)
            .context_map(context)
            .build()?;

        self.evaluate(&request)
    }

    fn is_server_allowed(
        &self,
        principal_id: &str,
        server_name: &str,
        mut context: PolicyEvaluationContext,
    ) -> Result<PolicyDecision> {
        // Add server name to context
        context.insert(
            "server_name".to_string(),
            serde_json::Value::String(server_name.to_string()),
        );

        let request = PolicyRequestBuilder::new()
            .principal(EntityType::McpClient, principal_id)
            .action(ActionType::ConnectServer)
            .resource(EntityType::Server, server_name)
            .context_map(context)
            .build()?;

        self.evaluate(&request)
    }

    fn is_file_access_allowed(
        &self,
        principal_id: &str,
        file_path: &str,
        is_write: bool,
        mut context: PolicyEvaluationContext,
    ) -> Result<PolicyDecision> {
        // Add file path and operation type to context
        context.insert(
            "path".to_string(),
            serde_json::Value::String(file_path.to_string()),
        );
        context.insert("is_write".to_string(), serde_json::Value::Bool(is_write));

        let action = if is_write {
            ActionType::WriteFile
        } else {
            ActionType::ReadFile
        };

        let request = PolicyRequestBuilder::new()
            .principal(EntityType::McpClient, principal_id)
            .action(action)
            .resource(EntityType::FilePath, file_path)
            .context_map(context)
            .build()?;

        self.evaluate(&request)
    }

    fn is_http_request_allowed(
        &self,
        principal_id: &str,
        url: &str,
        mut context: PolicyEvaluationContext,
    ) -> Result<PolicyDecision> {
        // Add URL to context
        context.insert(
            "url".to_string(),
            serde_json::Value::String(url.to_string()),
        );

        // Parse URL for additional context (for SSRF protection, etc.)
        if let Ok(parsed_url) = url::Url::parse(url) {
            if let Some(host) = parsed_url.host_str() {
                context.insert(
                    "hostname".to_string(),
                    serde_json::Value::String(host.to_string()),
                );

                // Check if host is an IP address
                if let Ok(ip) = host.parse::<std::net::IpAddr>() {
                    context.insert(
                        "ip_address".to_string(),
                        serde_json::Value::String(ip.to_string()),
                    );
                }
            }

            context.insert(
                "scheme".to_string(),
                serde_json::Value::String(parsed_url.scheme().to_string()),
            );

            if let Some(port) = parsed_url.port() {
                context.insert("port".to_string(), serde_json::Value::Number(port.into()));
            }
        }

        let request = PolicyRequestBuilder::new()
            .principal(EntityType::McpClient, principal_id)
            .action(ActionType::HttpRequest)
            .resource(EntityType::HttpEndpoint, url)
            .context_map(context)
            .build()?;

        self.evaluate(&request)
    }
}

impl Default for CedarPolicyEngine {
    fn default() -> Self {
        Self::new().expect("Failed to create default Cedar policy engine")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const TEST_POLICY: &str = r#"
        // Block shell tool
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
        ) when {
            resource != Tool::"shell"
        };
    "#;

    #[test]
    fn test_engine_creation() {
        let engine = CedarPolicyEngine::new();
        assert!(engine.is_ok());
    }

    #[test]
    fn test_policy_loading() {
        let mut engine = CedarPolicyEngine::new().unwrap();
        let result = engine.load_policies(TEST_POLICY);
        assert!(result.is_ok());
        assert!(engine.policy_count() > 0);
    }

    #[test]
    fn test_policy_evaluation() {
        let mut engine = CedarPolicyEngine::new().unwrap();
        engine.load_policies(TEST_POLICY).unwrap();

        // Test blocking shell tool
        let request = PolicyRequest::builder()
            .principal(EntityType::McpClient, "test-client")
            .action(ActionType::CallTool)
            .resource(EntityType::Tool, "shell")
            .build()
            .unwrap();

        let decision = engine.evaluate(&request).unwrap();
        assert!(decision.is_denied());

        // Test allowing safe tool
        let request = PolicyRequest::builder()
            .principal(EntityType::McpClient, "test-client")
            .action(ActionType::CallTool)
            .resource(EntityType::Tool, "calculator")
            .build()
            .unwrap();

        let decision = engine.evaluate(&request).unwrap();
        assert!(decision.is_allowed());
    }

    #[test]
    fn test_convenience_methods() {
        let mut engine = CedarPolicyEngine::new().unwrap();
        engine.load_policies(TEST_POLICY).unwrap();

        let context = PolicyEvaluationContext::new();
        let decision = engine
            .is_tool_allowed("test-client", "shell", context)
            .unwrap();
        assert!(decision.is_denied());
    }
}
