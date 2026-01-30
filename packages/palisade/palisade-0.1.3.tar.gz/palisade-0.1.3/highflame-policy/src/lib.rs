//! # Highflame Policy Framework
//!
//! A unified Cedar-based policy framework for the Highflame security platform.
//!
//! This library provides a high-performance, type-safe policy engine that can be:
//! - Embedded as a library in CLI tools (Palisade, Ramparts)
//! - Deployed as a gRPC sidecar service for microservices (Guardrails, etc.)
//!
//! ## Architecture
//!
//! The framework is organized into several modules:
//! - `core`: Core traits and abstractions for policy engines
//! - `engine`: Cedar policy engine implementation
//! - `entities`: Entity and action type definitions
//! - `decision`: Policy decision types with full traceability
//! - `config`: Configuration management
//! - `loader`: Policy file loading and management
//!
//! ## Example
//!
//! ```rust,no_run
//! use highflame_policy::{PolicyEngine, CedarPolicyEngine, PolicyRequest};
//! use highflame_policy::entities::{EntityType, ActionType};
//! use std::collections::HashMap;
//!
//! # fn main() -> anyhow::Result<()> {
//! // Create and configure the engine
//! let mut engine = CedarPolicyEngine::new()?;
//! engine.load_policies_from_file("policies/ramparts/policy.cedar")?;
//!
//! // Make an authorization request
//! let request = PolicyRequest::builder()
//!     .principal(EntityType::Agent, "code-scanner-v1")
//!     .action(ActionType::ScanTarget)
//!     .resource(EntityType::Repository, "https://github.com/org/repo")
//!     .context("scan_type", "dependency")
//!     .build()?;
//!
//! let decision = engine.evaluate(&request)?;
//!
//! if decision.is_allowed() {
//!     println!("Access granted");
//! } else {
//!     println!("Access denied by policies: {:?}", decision.determining_policies());
//! }
//! # Ok(())
//! # }
//! ```

// Re-export key types for convenience
pub use crate::config::ServiceId;
pub use crate::core::{PolicyEngine, PolicyEngineExt, PolicyEvaluationContext};
pub use crate::decision::{PolicyDecision, PolicyEffect};
pub use crate::engine::CedarPolicyEngine;
pub use crate::entities::{ActionType, EntityType};
pub use crate::loader::PolicyLoader;
pub use crate::request::{PolicyRequest, PolicyRequestBuilder};

// Public modules
pub mod config;
pub mod decision;
pub mod entities;
pub mod error;
pub mod loader;
pub mod request;

// Core abstractions
mod core;

// Cedar engine implementation
mod engine;

// Re-export error types
pub use error::{PolicyError, Result};

// Python bindings (optional, behind "python" feature)
#[cfg(feature = "python")]
pub mod python;

// Library version
pub const VERSION: &str = env!("CARGO_PKG_VERSION");
