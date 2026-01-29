//! Core policy engine abstractions
//!
//! This module defines the core traits that any policy engine implementation
//! must satisfy. This allows for multiple engine implementations or future
//! extensions.

use crate::decision::PolicyDecision;
use crate::error::Result;
use crate::request::PolicyRequest;
use serde_json::Value;
use std::collections::HashMap;

/// Additional context that can be passed during policy evaluation
pub type PolicyEvaluationContext = HashMap<String, Value>;

/// Core trait for policy engines
///
/// This trait defines the minimal interface that any policy engine
/// must implement. The Cedar implementation is the primary implementation,
/// but this abstraction allows for future extensibility.
pub trait PolicyEngine: Send + Sync {
    /// Load policies from a string
    fn load_policies(&mut self, policy_text: &str) -> Result<()>;

    /// Load policies from a file
    fn load_policies_from_file(&mut self, path: &str) -> Result<()>;

    /// Evaluate a policy request
    ///
    /// Returns a PolicyDecision that includes:
    /// - Whether the action is allowed or denied
    /// - Which policies determined the decision
    /// - A human-readable reason
    fn evaluate(&self, request: &PolicyRequest) -> Result<PolicyDecision>;

    /// Get the number of policies currently loaded
    fn policy_count(&self) -> usize;

    /// Clear all loaded policies
    fn clear_policies(&mut self);
}

/// Helper trait for common evaluation patterns
///
/// This provides convenience methods for common authorization checks
/// without requiring callers to construct full PolicyRequest objects.
pub trait PolicyEngineExt: PolicyEngine {
    /// Quick check: is this tool allowed?
    fn is_tool_allowed(
        &self,
        principal_id: &str,
        tool_name: &str,
        context: PolicyEvaluationContext,
    ) -> Result<PolicyDecision>;

    /// Quick check: is this server connection allowed?
    fn is_server_allowed(
        &self,
        principal_id: &str,
        server_name: &str,
        context: PolicyEvaluationContext,
    ) -> Result<PolicyDecision>;

    /// Quick check: is this file access allowed?
    fn is_file_access_allowed(
        &self,
        principal_id: &str,
        file_path: &str,
        is_write: bool,
        context: PolicyEvaluationContext,
    ) -> Result<PolicyDecision>;

    /// Quick check: is this HTTP request allowed?
    fn is_http_request_allowed(
        &self,
        principal_id: &str,
        url: &str,
        context: PolicyEvaluationContext,
    ) -> Result<PolicyDecision>;
}
