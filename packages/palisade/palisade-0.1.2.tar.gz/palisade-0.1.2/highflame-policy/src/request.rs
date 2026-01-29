//! Policy request types and builders
//!
//! This module provides a clean API for constructing policy evaluation requests.

use crate::entities::{ActionType, EntityType};
use crate::error::{PolicyError, Result};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::HashMap;

/// A policy evaluation request
///
/// This represents a complete authorization query: "Can this principal
/// perform this action on this resource, given this context?"
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PolicyRequest {
    /// The principal (who is making the request)
    principal: (EntityType, String),

    /// The action being performed
    action: ActionType,

    /// The resource being accessed
    resource: (EntityType, String),

    /// Additional context for the evaluation
    context: HashMap<String, Value>,
}

impl PolicyRequest {
    /// Create a new builder for constructing requests
    pub fn builder() -> PolicyRequestBuilder {
        PolicyRequestBuilder::new()
    }

    /// Get the principal
    pub fn principal(&self) -> &(EntityType, String) {
        &self.principal
    }

    /// Get the action
    pub fn action(&self) -> &ActionType {
        &self.action
    }

    /// Get the resource
    pub fn resource(&self) -> &(EntityType, String) {
        &self.resource
    }

    /// Get the context
    pub fn context(&self) -> &HashMap<String, Value> {
        &self.context
    }

    /// Get a mutable reference to the context
    pub fn context_mut(&mut self) -> &mut HashMap<String, Value> {
        &mut self.context
    }

    /// Format principal as Cedar EntityUid
    pub fn principal_uid(&self) -> String {
        self.principal.0.format_uid(&self.principal.1)
    }

    /// Format action as Cedar EntityUid
    pub fn action_uid(&self) -> String {
        self.action.format_uid()
    }

    /// Format resource as Cedar EntityUid
    pub fn resource_uid(&self) -> String {
        self.resource.0.format_uid(&self.resource.1)
    }
}

/// Builder for constructing policy requests
#[derive(Debug, Default)]
pub struct PolicyRequestBuilder {
    principal: Option<(EntityType, String)>,
    action: Option<ActionType>,
    resource: Option<(EntityType, String)>,
    context: HashMap<String, Value>,
}

impl PolicyRequestBuilder {
    /// Create a new builder
    pub fn new() -> Self {
        Self::default()
    }

    /// Set the principal
    pub fn principal(mut self, entity_type: EntityType, id: impl Into<String>) -> Self {
        self.principal = Some((entity_type, id.into()));
        self
    }

    /// Set the action
    pub fn action(mut self, action: ActionType) -> Self {
        self.action = Some(action);
        self
    }

    /// Set the resource
    pub fn resource(mut self, entity_type: EntityType, id: impl Into<String>) -> Self {
        self.resource = Some((entity_type, id.into()));
        self
    }

    /// Add a context attribute
    pub fn context<K, V>(mut self, key: K, value: V) -> Self
    where
        K: Into<String>,
        V: Into<Value>,
    {
        self.context.insert(key.into(), value.into());
        self
    }

    /// Add multiple context attributes from a HashMap
    pub fn context_map(mut self, context: HashMap<String, Value>) -> Self {
        self.context.extend(context);
        self
    }

    /// Build the request
    pub fn build(self) -> Result<PolicyRequest> {
        let principal = self
            .principal
            .ok_or_else(|| PolicyError::RequestCreation("Principal is required".to_string()))?;

        let action = self
            .action
            .ok_or_else(|| PolicyError::RequestCreation("Action is required".to_string()))?;

        let resource = self
            .resource
            .ok_or_else(|| PolicyError::RequestCreation("Resource is required".to_string()))?;

        Ok(PolicyRequest {
            principal,
            action,
            resource,
            context: self.context,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_request_builder() {
        let request = PolicyRequest::builder()
            .principal(EntityType::Agent, "scanner-v1")
            .action(ActionType::ScanTarget)
            .resource(EntityType::Repository, "https://github.com/org/repo")
            .context("scan_type", "dependency")
            .build()
            .unwrap();

        assert_eq!(request.principal().0, EntityType::Agent);
        assert_eq!(request.principal().1, "scanner-v1");
        assert_eq!(*request.action(), ActionType::ScanTarget);
        assert_eq!(request.context().len(), 1);
    }

    #[test]
    fn test_request_builder_missing_fields() {
        let result = PolicyRequest::builder()
            .principal(EntityType::User, "test")
            .action(ActionType::ReadFile)
            .build();

        assert!(result.is_err());
    }

    #[test]
    fn test_uid_formatting() {
        let request = PolicyRequest::builder()
            .principal(EntityType::Agent, "test-agent")
            .action(ActionType::ScanTarget)
            .resource(EntityType::Repository, "test-repo")
            .build()
            .unwrap();

        assert_eq!(request.principal_uid(), "Agent::\"test-agent\"");
        assert_eq!(request.action_uid(), "Action::\"scan_target\"");
        assert_eq!(request.resource_uid(), "Repository::\"test-repo\"");
    }
}
