//! Cedar Policy Engine bindings for Python
//!
//! This module provides PyO3 bindings to the highflame-policy Cedar policy engine,
//! allowing Python code to evaluate policies efficiently using Rust.

use crate::{
    ActionType, CedarPolicyEngine, EntityType, PolicyDecision, PolicyEffect, PolicyEngine,
    PolicyRequest,
};
use pyo3::exceptions::{PyRuntimeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::collections::HashMap;

/// Policy effect constants for Python
#[pyclass(name = "PolicyEffect")]
#[derive(Clone)]
pub struct PyPolicyEffect;

#[pymethods]
impl PyPolicyEffect {
    #[classattr]
    const ALLOW: &'static str = "allow";
    
    #[classattr]
    const DENY: &'static str = "deny";
    
    #[classattr]
    const QUARANTINE: &'static str = "quarantine";
}

/// Python-exposed policy engine using Cedar
#[pyclass]
pub struct PyCedarPolicyEngine {
    engine: CedarPolicyEngine,
}

#[pymethods]
impl PyCedarPolicyEngine {
    /// Create a new policy engine
    #[new]
    fn new() -> PyResult<Self> {
        let engine = CedarPolicyEngine::new().map_err(|e| {
            PyRuntimeError::new_err(format!("Failed to create policy engine: {}", e))
        })?;
        Ok(Self { engine })
    }

    /// Load policies from a Cedar policy file
    fn load_policies_from_file(&mut self, path: &str) -> PyResult<()> {
        self.engine
            .load_policies_from_file(path)
            .map_err(|e| PyRuntimeError::new_err(format!("Failed to load policies: {}", e)))?;
        Ok(())
    }

    /// Load policies from a Cedar policy string
    fn load_policies(&mut self, policy_str: &str) -> PyResult<()> {
        self.engine
            .load_policies(policy_str)
            .map_err(|e| PyRuntimeError::new_err(format!("Failed to load policies: {}", e)))?;
        Ok(())
    }

    /// Evaluate a policy request
    ///
    /// Args:
    ///     principal_type: Type of principal (e.g., "Scanner", "Agent")
    ///     principal_id: ID of the principal
    ///     action: Action being performed (e.g., "scan_artifact", "load_model")
    ///     resource_type: Type of resource (e.g., "Artifact", "Model")
    ///     resource_id: ID of the resource
    ///     context: Optional context dictionary
    ///
    /// Returns:
    ///     Dictionary with decision details: {
    ///         "effect": "allow" | "deny" | "quarantine",
    ///         "determining_policies": [...],
    ///         "reason": "...",
    ///         "is_allowed": bool,
    ///         "is_denied": bool,
    ///         "is_quarantine": bool
    ///     }
    #[pyo3(signature = (principal_type, principal_id, action, resource_type, resource_id, context=None))]
    fn evaluate(
        &self,
        principal_type: &str,
        principal_id: &str,
        action: &str,
        resource_type: &str,
        resource_id: &str,
        context: Option<&Bound<'_, PyDict>>,
    ) -> PyResult<PyObject> {
        // Convert string types to enums
        let principal_entity = parse_entity_type(principal_type)?;
        let action_type = parse_action_type(action)?;
        let resource_entity = parse_entity_type(resource_type)?;

        // Build request
        let mut request_builder = PolicyRequest::builder()
            .principal(principal_entity, principal_id)
            .action(action_type)
            .resource(resource_entity, resource_id);

        // Add context if provided
        if let Some(ctx_dict) = context {
            let context_map = py_dict_to_context_map(ctx_dict)?;
            request_builder = request_builder.context_map(context_map);
        }

        let request = request_builder
            .build()
            .map_err(|e| PyRuntimeError::new_err(format!("Failed to build request: {}", e)))?;

        // Evaluate
        let decision = self
            .engine
            .evaluate(&request)
            .map_err(|e| PyRuntimeError::new_err(format!("Policy evaluation failed: {}", e)))?;

        // Convert to Python dict
        Python::with_gil(|py| decision_to_py_dict(py, &decision))
    }

    /// Get a string representation of the engine
    fn __repr__(&self) -> String {
        "PyCedarPolicyEngine(loaded=true)".to_string()
    }
}

/// Helper function to parse entity type from string
fn parse_entity_type(type_str: &str) -> PyResult<EntityType> {
    match type_str.to_lowercase().as_str() {
        "user" => Ok(EntityType::User),
        "agent" => Ok(EntityType::Agent),
        "scanner" => Ok(EntityType::Scanner),
        "service" => Ok(EntityType::Service),
        "mcpclient" | "mcp_client" => Ok(EntityType::McpClient),
        "tool" => Ok(EntityType::Tool),
        "server" => Ok(EntityType::Server),
        "resource" => Ok(EntityType::Resource),
        "httpendpoint" | "http_endpoint" => Ok(EntityType::HttpEndpoint),
        "filepath" | "file_path" => Ok(EntityType::FilePath),
        "repository" => Ok(EntityType::Repository),
        "package" => Ok(EntityType::Package),
        "llmprompt" | "llm_prompt" => Ok(EntityType::LlmPrompt),
        "scantarget" | "scan_target" => Ok(EntityType::ScanTarget),
        "responsedata" | "response_data" => Ok(EntityType::ResponseData),
        "servercontext" | "server_context" => Ok(EntityType::ServerContext),
        "artifact" => Ok(EntityType::Artifact),
        "finding" => Ok(EntityType::Finding),
        "provenance" => Ok(EntityType::Provenance),
        "metadata" => Ok(EntityType::Metadata),
        "tokenizer" => Ok(EntityType::Tokenizer),
        _ => Err(PyValueError::new_err(format!(
            "Unknown entity type: {}",
            type_str
        ))),
    }
}

/// Helper function to parse action type from string
fn parse_action_type(action_str: &str) -> PyResult<ActionType> {
    match action_str.to_lowercase().as_str() {
        "call_tool" | "calltool" => Ok(ActionType::CallTool),
        "connect_server" | "connectserver" => Ok(ActionType::ConnectServer),
        "http_request" | "httprequest" => Ok(ActionType::HttpRequest),
        "read_file" | "readfile" => Ok(ActionType::ReadFile),
        "write_file" | "writefile" => Ok(ActionType::WriteFile),
        "scan_target" | "scantarget" => Ok(ActionType::ScanTarget),
        "process_response" | "processresponse" => Ok(ActionType::ProcessResponse),
        "scan_artifact" | "scanartifact" => Ok(ActionType::ScanArtifact),
        "validate_integrity" | "validateintegrity" => Ok(ActionType::ValidateIntegrity),
        "validate_provenance" | "validateprovenance" => Ok(ActionType::ValidateProvenance),
        "quarantine_artifact" | "quarantineartifact" => Ok(ActionType::QuarantineArtifact),
        "load_model" | "loadmodel" => Ok(ActionType::LoadModel),
        "deploy_model" | "deploymodel" => Ok(ActionType::DeployModel),
        _ => Err(PyValueError::new_err(format!(
            "Unknown action type: {}",
            action_str
        ))),
    }
}

/// Convert Python dict to context map
fn py_dict_to_context_map(
    py_dict: &Bound<'_, PyDict>,
) -> PyResult<HashMap<String, serde_json::Value>> {
    let mut map = HashMap::new();

    for (key, value) in py_dict.iter() {
        let key_str: String = key.extract()?;
        let value_json = python_to_json_value(&value)?;
        map.insert(key_str, value_json);
    }

    Ok(map)
}

/// Convert Python object to JSON value
fn python_to_json_value(obj: &Bound<'_, PyAny>) -> PyResult<serde_json::Value> {
    if obj.is_none() {
        Ok(serde_json::Value::Null)
    } else if let Ok(b) = obj.extract::<bool>() {
        Ok(serde_json::Value::Bool(b))
    } else if let Ok(i) = obj.extract::<i64>() {
        Ok(serde_json::Value::Number(i.into()))
    } else if let Ok(f) = obj.extract::<f64>() {
        if let Some(num) = serde_json::Number::from_f64(f) {
            Ok(serde_json::Value::Number(num))
        } else {
            Ok(serde_json::Value::Null)
        }
    } else if let Ok(s) = obj.extract::<String>() {
        Ok(serde_json::Value::String(s))
    } else if let Ok(list) = obj.downcast::<pyo3::types::PyList>() {
        let mut arr = Vec::new();
        for item in list.iter() {
            arr.push(python_to_json_value(&item)?);
        }
        Ok(serde_json::Value::Array(arr))
    } else if let Ok(dict) = obj.downcast::<PyDict>() {
        let mut obj_map = serde_json::Map::new();
        for (key, value) in dict.iter() {
            let key_str: String = key.extract()?;
            obj_map.insert(key_str, python_to_json_value(&value)?);
        }
        Ok(serde_json::Value::Object(obj_map))
    } else {
        // Fallback: convert to string
        Ok(serde_json::Value::String(obj.to_string()))
    }
}

/// Convert PolicyDecision to Python dict
fn decision_to_py_dict(py: Python<'_>, decision: &PolicyDecision) -> PyResult<PyObject> {
    let dict = PyDict::new_bound(py);

    // Effect
    let effect_str = match decision.effect() {
        PolicyEffect::Allow => "allow",
        PolicyEffect::Deny => "deny",
        PolicyEffect::Quarantine => "quarantine",
    };
    dict.set_item("effect", effect_str)?;

    // Determining policies
    let policies: Vec<String> = decision
        .determining_policies()
        .iter()
        .map(|s| s.to_string())
        .collect();
    dict.set_item("determining_policies", policies)?;

    // Reason
    dict.set_item("reason", decision.reason())?;

    // Convenience flags
    dict.set_item("is_allowed", decision.is_allowed())?;
    dict.set_item("is_denied", decision.is_denied())?;
    dict.set_item("is_quarantine", decision.is_quarantined())?;

    Ok(dict.into())
}

/// Python module definition
/// Only compiled when NOT in embedded mode (standalone builds)
/// When embedded in another crate (e.g., palisade), that crate registers the classes
#[cfg(not(feature = "embedded"))]
#[pymodule]
fn _native(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyCedarPolicyEngine>()?;
    m.add_class::<PyPolicyEffect>()?;
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    Ok(())
}
