//! Entity and action type definitions for policy evaluation
//!
//! This module provides type-safe representations of entities (principals, resources)
//! and actions that can be used in policy evaluations.

use serde::{Deserialize, Serialize};
use std::fmt;

/// Entity types in the Highflame ecosystem
///
/// Entities represent principals (who/what is making the request) and
/// resources (what is being accessed).
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "PascalCase")]
pub enum EntityType {
    // === Principals (who is acting) ===
    /// A human user
    User,
    /// An AI agent
    Agent,
    /// A security scanner
    Scanner,
    /// A service account
    Service,
    /// MCP client
    McpClient,

    // === Resources (what is being accessed) ===
    /// A tool/function that can be called
    Tool,
    /// An MCP server
    Server,
    /// A generic resource
    Resource,
    /// An HTTP endpoint
    HttpEndpoint,
    /// A file path
    FilePath,
    /// A code repository
    Repository,
    /// A package/dependency
    Package,
    /// An LLM prompt
    LlmPrompt,
    /// A scan target
    ScanTarget,
    /// Response data
    ResponseData,
    /// Server context (server-specific resource)
    ServerContext,

    // === Palisade-specific Resources ===
    /// ML model artifact (safetensors, pickle, gguf, onnx, etc.)
    Artifact,
    /// Security finding/vulnerability
    Finding,
    /// Provenance/attestation data
    Provenance,
    /// Model metadata
    Metadata,
    /// Tokenizer
    Tokenizer,

    /// Custom entity type for extensibility
    Custom(String),
}

impl EntityType {
    /// Get the Cedar entity type name
    pub fn as_str(&self) -> &str {
        match self {
            Self::User => "User",
            Self::Agent => "Agent",
            Self::Scanner => "Scanner",
            Self::Service => "Service",
            Self::McpClient => "McpClient",
            Self::Tool => "Tool",
            Self::Server => "Server",
            Self::Resource => "Resource",
            Self::HttpEndpoint => "HttpEndpoint",
            Self::FilePath => "FilePath",
            Self::Repository => "Repository",
            Self::Package => "Package",
            Self::LlmPrompt => "LlmPrompt",
            Self::ScanTarget => "ScanTarget",
            Self::ResponseData => "ResponseData",
            Self::ServerContext => "ServerContext",
            Self::Artifact => "Artifact",
            Self::Finding => "Finding",
            Self::Provenance => "Provenance",
            Self::Metadata => "Metadata",
            Self::Tokenizer => "Tokenizer",
            Self::Custom(name) => name,
        }
    }

    /// Create a Cedar-formatted entity UID
    pub fn format_uid(&self, id: &str) -> String {
        format!("{}::\"{}\"", self.as_str(), id)
    }
}

impl fmt::Display for EntityType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.as_str())
    }
}

/// Action types that can be performed in the Highflame ecosystem
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ActionType {
    // === Tool/Function Actions ===
    /// Call a tool or function
    CallTool,

    // === Server Actions ===
    /// Connect to an MCP server
    ConnectServer,
    /// Access a server-specific resource
    AccessServerResource,

    // === Resource Actions ===
    /// Access a generic resource
    AccessResource,

    // === HTTP Actions ===
    /// Make an HTTP request
    HttpRequest,

    // === File System Actions ===
    /// Read a file
    ReadFile,
    /// Write to a file
    WriteFile,

    // === LLM Actions ===
    /// Process an LLM prompt
    ProcessPrompt,
    /// Process LLM response
    ProcessResponse,

    // === Security Scanning Actions ===
    /// Scan a target for vulnerabilities
    ScanTarget,
    /// Scan a package/dependency
    ScanPackage,
    /// Flag a vulnerability
    FlagVulnerability,

    // === Guardrails Actions ===
    /// Skip guardrails for a specific operation
    SkipGuardrails,

    // === Palisade Actions ===
    /// Scan an ML artifact
    ScanArtifact,
    /// Validate artifact integrity
    ValidateIntegrity,
    /// Validate provenance
    ValidateProvenance,
    /// Quarantine an artifact
    QuarantineArtifact,
    /// Load/use an ML model
    LoadModel,
    /// Deploy an ML model
    DeployModel,

    /// Custom action for extensibility
    Custom(String),
}

impl ActionType {
    /// Get the Cedar action identifier
    pub fn as_str(&self) -> &str {
        match self {
            Self::CallTool => "call_tool",
            Self::ConnectServer => "connect_server",
            Self::AccessServerResource => "access_server_resource",
            Self::AccessResource => "access_resource",
            Self::HttpRequest => "http_request",
            Self::ReadFile => "read_file",
            Self::WriteFile => "write_file",
            Self::ProcessPrompt => "process_prompt",
            Self::ProcessResponse => "process_response",
            Self::ScanTarget => "scan_target",
            Self::ScanPackage => "scan_package",
            Self::FlagVulnerability => "flag_vulnerability",
            Self::SkipGuardrails => "skip_guardrails",
            Self::ScanArtifact => "scan_artifact",
            Self::ValidateIntegrity => "validate_integrity",
            Self::ValidateProvenance => "validate_provenance",
            Self::QuarantineArtifact => "quarantine_artifact",
            Self::LoadModel => "load_model",
            Self::DeployModel => "deploy_model",
            Self::Custom(name) => name,
        }
    }

    /// Create a Cedar-formatted action UID
    pub fn format_uid(&self) -> String {
        format!("Action::\"{}\"", self.as_str())
    }
}

impl fmt::Display for ActionType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.as_str())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_entity_uid_formatting() {
        let entity = EntityType::Agent;
        assert_eq!(entity.format_uid("scanner-v1"), "Agent::\"scanner-v1\"");

        let custom = EntityType::Custom("CustomType".to_string());
        assert_eq!(custom.format_uid("test"), "CustomType::\"test\"");
    }

    #[test]
    fn test_action_uid_formatting() {
        let action = ActionType::ScanTarget;
        assert_eq!(action.format_uid(), "Action::\"scan_target\"");

        let custom = ActionType::Custom("custom_action".to_string());
        assert_eq!(custom.format_uid(), "Action::\"custom_action\"");
    }

    #[test]
    fn test_entity_serialization() {
        let entity = EntityType::Agent;
        let json = serde_json::to_string(&entity).unwrap();
        assert_eq!(json, "\"Agent\"");

        let deserialized: EntityType = serde_json::from_str(&json).unwrap();
        assert_eq!(deserialized, entity);
    }
}
