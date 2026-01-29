//! Policy loading utilities
//!
//! This module provides utilities for loading policies from files,
//! directories, and managing service-specific policy paths.

use crate::config::{PolicyConfig, ServiceId};
use crate::core::PolicyEngine;
use crate::error::{PolicyError, Result};
use std::fs;
use std::path::{Path, PathBuf};
use tracing::{debug, info, warn};

/// Policy loader for managing policy files
pub struct PolicyLoader {
    /// Base directory for policies
    base_dir: PathBuf,
}

impl PolicyLoader {
    /// Create a new policy loader with the specified base directory
    pub fn new(base_dir: impl Into<PathBuf>) -> Self {
        Self {
            base_dir: base_dir.into(),
        }
    }

    /// Get the default policy path for a service
    ///
    /// Convention: `<base_dir>/<service>/policy.cedar`
    pub fn default_service_policy_path(&self, service: ServiceId) -> PathBuf {
        self.base_dir
            .join(service.policy_dir())
            .join("policy.cedar")
    }

    /// Load policies for a specific service into an engine
    pub fn load_service_policies(
        &self,
        service: ServiceId,
        engine: &mut dyn PolicyEngine,
    ) -> Result<()> {
        let policy_path = self.default_service_policy_path(service);
        info!(
            "Loading policies for service '{}' from: {}",
            service,
            policy_path.display()
        );

        if !policy_path.exists() {
            warn!(
                "Policy file not found: {}. Creating default policy.",
                policy_path.display()
            );
            self.create_default_policy(&policy_path)?;
        }

        engine.load_policies_from_file(&policy_path.to_string_lossy())?;
        Ok(())
    }

    /// Load policies from a custom path
    pub fn load_from_path(
        &self,
        path: impl AsRef<Path>,
        engine: &mut dyn PolicyEngine,
    ) -> Result<()> {
        let path = path.as_ref();
        debug!("Loading policies from: {}", path.display());

        if !path.exists() {
            return Err(PolicyError::PolicyLoading(format!(
                "Policy path does not exist: {}",
                path.display()
            )));
        }

        if path.is_file() {
            engine.load_policies_from_file(&path.to_string_lossy())?;
        } else if path.is_dir() {
            self.load_from_directory(path, engine)?;
        } else {
            return Err(PolicyError::PolicyLoading(format!(
                "Invalid policy path: {}",
                path.display()
            )));
        }

        Ok(())
    }

    /// Load all `.cedar` files from a directory
    fn load_from_directory(
        &self,
        dir: impl AsRef<Path>,
        engine: &mut dyn PolicyEngine,
    ) -> Result<()> {
        let dir = dir.as_ref();
        debug!("Loading policies from directory: {}", dir.display());

        let mut policy_files = Vec::new();

        for entry in fs::read_dir(dir).map_err(|e| {
            PolicyError::PolicyLoading(format!("Failed to read directory {}: {}", dir.display(), e))
        })? {
            let entry = entry.map_err(|e| {
                PolicyError::PolicyLoading(format!("Failed to read directory entry: {}", e))
            })?;

            let path = entry.path();
            if path.is_file() && path.extension().and_then(|s| s.to_str()) == Some("cedar") {
                policy_files.push(path);
            }
        }

        if policy_files.is_empty() {
            warn!("No .cedar files found in directory: {}", dir.display());
            return Ok(());
        }

        info!("Found {} policy file(s) in directory", policy_files.len());

        // Load and concatenate all policy files
        let mut combined_policies = String::new();
        for policy_file in policy_files {
            debug!("Loading policy file: {}", policy_file.display());
            let content = fs::read_to_string(&policy_file).map_err(|e| {
                PolicyError::PolicyLoading(format!(
                    "Failed to read policy file {}: {}",
                    policy_file.display(),
                    e
                ))
            })?;
            combined_policies.push_str(&content);
            combined_policies.push('\n');
        }

        engine.load_policies(&combined_policies)?;
        Ok(())
    }

    /// Create a default policy file for a service
    fn create_default_policy(&self, path: &Path) -> Result<()> {
        // Create parent directory if it doesn't exist
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).map_err(|e| {
                PolicyError::PolicyLoading(format!(
                    "Failed to create policy directory {}: {}",
                    parent.display(),
                    e
                ))
            })?;
        }

        // Write a default permissive policy
        let default_policy = r#"// Default policy: Allow all (configure as needed)
permit(principal, action, resource);
"#;

        fs::write(path, default_policy).map_err(|e| {
            PolicyError::PolicyLoading(format!(
                "Failed to write default policy to {}: {}",
                path.display(),
                e
            ))
        })?;

        info!("Created default policy at: {}", path.display());
        Ok(())
    }

    /// Load policies using a PolicyConfig
    pub fn load_with_config(
        &self,
        config: &PolicyConfig,
        engine: &mut dyn PolicyEngine,
    ) -> Result<()> {
        info!("Loading policies for service: {}", config.service);

        let policy_path = if config.policy_path.is_absolute() {
            config.policy_path.clone()
        } else {
            self.base_dir.join(&config.policy_path)
        };

        self.load_from_path(policy_path, engine)
    }
}

impl Default for PolicyLoader {
    fn default() -> Self {
        // Default to 'policies' directory in current working directory
        Self::new("policies")
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::engine::CedarPolicyEngine;
    use tempfile::TempDir;

    #[test]
    fn test_loader_creation() {
        let loader = PolicyLoader::new("test_policies");
        assert!(loader.base_dir.ends_with("test_policies"));
    }

    #[test]
    fn test_default_service_policy_path() {
        let loader = PolicyLoader::new("policies");
        let path = loader.default_service_policy_path(ServiceId::Ramparts);
        assert!(path.ends_with("policies/ramparts/policy.cedar"));
    }

    #[test]
    fn test_load_from_directory() {
        let temp_dir = TempDir::new().unwrap();
        let policy_dir = temp_dir.path().join("test_policies");
        fs::create_dir_all(&policy_dir).unwrap();

        // Create test policy files
        let policy1 = r#"permit(principal, action == Action::"read", resource);"#;
        let policy2 = r#"forbid(principal, action == Action::"delete", resource);"#;

        fs::write(policy_dir.join("policy1.cedar"), policy1).unwrap();
        fs::write(policy_dir.join("policy2.cedar"), policy2).unwrap();

        let loader = PolicyLoader::new(temp_dir.path());
        let mut engine = CedarPolicyEngine::new().unwrap();

        let result = loader.load_from_path(&policy_dir, &mut engine);
        assert!(result.is_ok());
        assert!(engine.policy_count() > 0);
    }
}
