//! Error types for the policy framework

use thiserror::Error;

/// Result type alias for policy operations
pub type Result<T> = std::result::Result<T, PolicyError>;

/// Errors that can occur in policy operations
#[derive(Error, Debug)]
pub enum PolicyError {
    /// Failed to parse policy file
    #[error("Policy parsing error: {0}")]
    PolicyParsing(String),

    /// Failed to load policy file
    #[error("Policy loading error: {0}")]
    PolicyLoading(String),

    /// Invalid entity UID format
    #[error("Invalid entity UID: {0}")]
    InvalidEntityUid(String),

    /// Invalid action format
    #[error("Invalid action: {0}")]
    InvalidAction(String),

    /// Invalid context data
    #[error("Invalid context: {0}")]
    InvalidContext(String),

    /// Request creation failed
    #[error("Request creation failed: {0}")]
    RequestCreation(String),

    /// Policy evaluation failed
    #[error("Policy evaluation failed: {0}")]
    EvaluationFailed(String),

    /// Configuration error
    #[error("Configuration error: {0}")]
    Configuration(String),

    /// File I/O error
    #[error("File I/O error: {0}")]
    Io(#[from] std::io::Error),

    /// JSON serialization/deserialization error
    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),

    /// Generic error with context
    #[error("{0}")]
    Other(String),
}

impl From<String> for PolicyError {
    fn from(s: String) -> Self {
        Self::Other(s)
    }
}

impl From<&str> for PolicyError {
    fn from(s: &str) -> Self {
        Self::Other(s.to_string())
    }
}

impl From<anyhow::Error> for PolicyError {
    fn from(e: anyhow::Error) -> Self {
        Self::Other(e.to_string())
    }
}
