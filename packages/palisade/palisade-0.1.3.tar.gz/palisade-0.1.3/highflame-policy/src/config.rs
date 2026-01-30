//! Configuration for the policy engine
//!
//! This module provides configuration types for policy loading,
//! service identification, and future features like hot-reload.

use serde::{Deserialize, Serialize};
use std::path::PathBuf;

/// Service identifiers in the Highflame ecosystem
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum ServiceId {
    /// Ramparts - MCP server scanner
    Ramparts,
    /// Guardrails - LLM proxy layer
    Guardrails,
    /// Palisade - Supply chain security scanner
    Palisade,
}

impl ServiceId {
    /// Get the service name as a string
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Ramparts => "ramparts",
            Self::Guardrails => "guardrails",
            Self::Palisade => "palisade",
        }
    }

    /// Get the default policy directory name for this service
    pub fn policy_dir(&self) -> &'static str {
        self.as_str()
    }
}

impl std::fmt::Display for ServiceId {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.as_str())
    }
}

impl std::str::FromStr for ServiceId {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s.to_lowercase().as_str() {
            "ramparts" => Ok(Self::Ramparts),
            "guardrails" => Ok(Self::Guardrails),
            "palisade" => Ok(Self::Palisade),
            _ => Err(format!("Unknown service: {}", s)),
        }
    }
}

/// Configuration for policy loading
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PolicyConfig {
    /// Service identifier
    pub service: ServiceId,

    /// Path to the policy file or directory
    pub policy_path: PathBuf,

    /// Whether to enable hot-reload (watch for file changes)
    #[serde(default)]
    pub hot_reload: bool,

    /// Hot-reload interval in seconds (if enabled)
    #[serde(default = "default_reload_interval")]
    pub reload_interval_secs: u64,
}

fn default_reload_interval() -> u64 {
    5 // Check for changes every 5 seconds
}

impl PolicyConfig {
    /// Create a new policy configuration
    pub fn new(service: ServiceId, policy_path: impl Into<PathBuf>) -> Self {
        Self {
            service,
            policy_path: policy_path.into(),
            hot_reload: false,
            reload_interval_secs: default_reload_interval(),
        }
    }

    /// Enable hot-reload with the specified interval
    pub fn with_hot_reload(mut self, interval_secs: u64) -> Self {
        self.hot_reload = true;
        self.reload_interval_secs = interval_secs;
        self
    }

    /// Get the absolute policy path
    pub fn absolute_policy_path(&self) -> PathBuf {
        if self.policy_path.is_absolute() {
            self.policy_path.clone()
        } else {
            std::env::current_dir()
                .unwrap_or_default()
                .join(&self.policy_path)
        }
    }
}

/// Configuration for gRPC sidecar (future feature)
#[cfg(feature = "grpc-sidecar")]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SidecarConfig {
    /// Host to bind to
    pub host: String,

    /// Port to bind to
    pub port: u16,

    /// Policy configuration
    pub policy: PolicyConfig,

    /// Enable TLS
    #[serde(default)]
    pub enable_tls: bool,

    /// Path to TLS certificate (if enabled)
    pub tls_cert_path: Option<PathBuf>,

    /// Path to TLS key (if enabled)
    pub tls_key_path: Option<PathBuf>,
}

#[cfg(feature = "grpc-sidecar")]
impl SidecarConfig {
    /// Create a new sidecar configuration
    pub fn new(host: String, port: u16, policy: PolicyConfig) -> Self {
        Self {
            host,
            port,
            policy,
            enable_tls: false,
            tls_cert_path: None,
            tls_key_path: None,
        }
    }

    /// Get the bind address
    pub fn bind_address(&self) -> String {
        format!("{}:{}", self.host, self.port)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_service_id_from_str() {
        assert_eq!(
            "ramparts".parse::<ServiceId>().unwrap(),
            ServiceId::Ramparts
        );
        assert_eq!(
            "GUARDRAILS".parse::<ServiceId>().unwrap(),
            ServiceId::Guardrails
        );
        assert!("invalid".parse::<ServiceId>().is_err());
    }

    #[test]
    fn test_policy_config() {
        let config = PolicyConfig::new(ServiceId::Ramparts, "policies/ramparts/policy.cedar");
        assert_eq!(config.service, ServiceId::Ramparts);
        assert!(!config.hot_reload);

        let config = config.with_hot_reload(10);
        assert!(config.hot_reload);
        assert_eq!(config.reload_interval_secs, 10);
    }
}
