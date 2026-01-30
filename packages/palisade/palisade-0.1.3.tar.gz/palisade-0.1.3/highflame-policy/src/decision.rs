//! Policy decision types with full traceability
//!
//! This module provides types for representing policy evaluation decisions,
//! including which policies were responsible for the decision.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// The effect of a policy decision
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum PolicyEffect {
    /// The action is allowed
    Allow,
    /// The action is denied
    Deny,
    /// The action is quarantined (soft deny with manual review)
    Quarantine,
}

impl PolicyEffect {
    /// Check if the effect is Allow
    pub fn is_allow(&self) -> bool {
        matches!(self, Self::Allow)
    }

    /// Check if the effect is Deny
    pub fn is_deny(&self) -> bool {
        matches!(self, Self::Deny)
    }

    /// Check if the effect is Quarantine
    pub fn is_quarantine(&self) -> bool {
        matches!(self, Self::Quarantine)
    }

    /// Check if the effect blocks the action (Deny or Quarantine)
    pub fn is_blocking(&self) -> bool {
        matches!(self, Self::Deny | Self::Quarantine)
    }
}

/// A policy decision with full traceability
///
/// This struct captures not just whether an action is allowed or denied,
/// but also which policies were responsible for the decision. This is
/// critical for audit trails and debugging policy configurations.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PolicyDecision {
    /// Unique ID for this decision (for tracing)
    decision_id: Uuid,

    /// The final decision effect
    effect: PolicyEffect,

    /// List of policy IDs that determined this decision
    ///
    /// For Allow decisions, these are the policies that permitted the action.
    /// For Deny decisions, these are the policies that forbade the action.
    determining_policies: Vec<String>,

    /// Human-readable reason for the decision
    reason: String,

    /// Timestamp when the decision was made
    timestamp: DateTime<Utc>,

    /// Any diagnostic information (errors, warnings)
    diagnostics: Vec<String>,
}

impl PolicyDecision {
    /// Create a new Allow decision
    pub fn allow(determining_policies: Vec<String>, reason: impl Into<String>) -> Self {
        Self {
            decision_id: Uuid::new_v4(),
            effect: PolicyEffect::Allow,
            determining_policies,
            reason: reason.into(),
            timestamp: Utc::now(),
            diagnostics: Vec::new(),
        }
    }

    /// Create a new Deny decision
    pub fn deny(determining_policies: Vec<String>, reason: impl Into<String>) -> Self {
        Self {
            decision_id: Uuid::new_v4(),
            effect: PolicyEffect::Deny,
            determining_policies,
            reason: reason.into(),
            timestamp: Utc::now(),
            diagnostics: Vec::new(),
        }
    }

    /// Create a new Quarantine decision
    pub fn quarantine(determining_policies: Vec<String>, reason: impl Into<String>) -> Self {
        Self {
            decision_id: Uuid::new_v4(),
            effect: PolicyEffect::Quarantine,
            determining_policies,
            reason: reason.into(),
            timestamp: Utc::now(),
            diagnostics: Vec::new(),
        }
    }

    /// Create a default Allow decision (no policies loaded)
    pub fn default_allow(reason: impl Into<String>) -> Self {
        Self::allow(vec![], reason)
    }

    /// Create a default Deny decision (no policies loaded)
    pub fn default_deny(reason: impl Into<String>) -> Self {
        Self::deny(vec![], reason)
    }

    /// Add diagnostic information
    pub fn with_diagnostic(mut self, diagnostic: impl Into<String>) -> Self {
        self.diagnostics.push(diagnostic.into());
        self
    }

    /// Add multiple diagnostics
    pub fn with_diagnostics(mut self, diagnostics: Vec<String>) -> Self {
        self.diagnostics.extend(diagnostics);
        self
    }

    /// Get the decision ID
    pub fn decision_id(&self) -> &Uuid {
        &self.decision_id
    }

    /// Get the decision effect
    pub fn effect(&self) -> PolicyEffect {
        self.effect
    }

    /// Check if the decision allows the action
    pub fn is_allowed(&self) -> bool {
        self.effect.is_allow()
    }

    /// Check if the decision denies the action
    pub fn is_denied(&self) -> bool {
        self.effect.is_deny()
    }

    /// Check if the decision quarantines the action
    pub fn is_quarantined(&self) -> bool {
        self.effect.is_quarantine()
    }

    /// Check if the decision blocks the action (deny or quarantine)
    pub fn is_blocking(&self) -> bool {
        self.effect.is_blocking()
    }

    /// Get the list of determining policy IDs
    pub fn determining_policies(&self) -> &[String] {
        &self.determining_policies
    }

    /// Get the human-readable reason
    pub fn reason(&self) -> &str {
        &self.reason
    }

    /// Get the timestamp
    pub fn timestamp(&self) -> DateTime<Utc> {
        self.timestamp
    }

    /// Get diagnostic information
    pub fn diagnostics(&self) -> &[String] {
        &self.diagnostics
    }

    /// Convert to a JSON-serializable audit log entry
    pub fn to_audit_log(&self) -> AuditLogEntry {
        AuditLogEntry {
            decision_id: self.decision_id.to_string(),
            effect: match self.effect {
                PolicyEffect::Allow => "Allow",
                PolicyEffect::Deny => "Deny",
                PolicyEffect::Quarantine => "Quarantine",
            }
            .to_string(),
            determining_policies: self.determining_policies.clone(),
            reason: self.reason.clone(),
            timestamp: self.timestamp.to_rfc3339(),
            diagnostics: self.diagnostics.clone(),
        }
    }
}

/// Audit log entry for serialization
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuditLogEntry {
    pub decision_id: String,
    pub effect: String,
    pub determining_policies: Vec<String>,
    pub reason: String,
    pub timestamp: String,
    pub diagnostics: Vec<String>,
}

impl std::fmt::Display for PolicyDecision {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "Decision: {:?}, Policies: {:?}, Reason: {}",
            self.effect, self.determining_policies, self.reason
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_allow_decision() {
        let decision = PolicyDecision::allow(
            vec!["policy-1".to_string(), "policy-2".to_string()],
            "Access granted by policies",
        );

        assert!(decision.is_allowed());
        assert!(!decision.is_denied());
        assert_eq!(decision.determining_policies().len(), 2);
        assert_eq!(decision.reason(), "Access granted by policies");
    }

    #[test]
    fn test_deny_decision() {
        let decision = PolicyDecision::deny(
            vec!["security-policy-1".to_string()],
            "Access denied by security policy",
        );

        assert!(decision.is_denied());
        assert!(!decision.is_allowed());
        assert_eq!(decision.determining_policies().len(), 1);
    }

    #[test]
    fn test_diagnostics() {
        let decision = PolicyDecision::allow(vec![], "Test")
            .with_diagnostic("Warning: Policy set is empty")
            .with_diagnostic("Using default allow");

        assert_eq!(decision.diagnostics().len(), 2);
    }

    #[test]
    fn test_audit_log_conversion() {
        let decision = PolicyDecision::deny(
            vec!["block-dangerous-tools".to_string()],
            "Tool execution blocked",
        );

        let audit_log = decision.to_audit_log();
        assert_eq!(audit_log.effect, "Deny");
        assert_eq!(audit_log.determining_policies.len(), 1);
    }
}
