use pyo3::prelude::*;

// Module declarations
pub mod malware_patterns;
pub mod pattern_matching;
pub mod scanner;
pub mod py_streaming;
pub mod safetensors;
pub mod streaming;
pub mod model_integrity;
pub mod tool_calling;
pub mod buffer_overflow;
pub mod supply_chain;
pub mod behavior_analysis;
pub mod tokenizer_hygiene;
pub mod gguf_safety;

// Re-export highflame-policy Python bindings
pub use highflame_policy::python::{PyCedarPolicyEngine, PyPolicyEffect};

use py_streaming::{PyParallelStreamingScanner, PyPatternMatch};
use safetensors::{
    is_safetensors, parse_safetensors_header, validate_safetensors, SafeTensorsStreamingValidator,
    SafeTensorsValidation, TensorInfo,
};
use model_integrity::{ModelIntegrityStreamingValidator, ModelIntegrityValidation, validate_model_integrity};
use tool_calling::{ToolCallingStreamingValidator, ToolCallingValidation, validate_tool_calling};
use buffer_overflow::{BufferOverflowStreamingValidator, BufferOverflowValidation, validate_buffer_overflow};
use supply_chain::{SupplyChainStreamingValidator, SupplyChainValidation, validate_supply_chain};
use behavior_analysis::{BehaviorAnalysisStreamingValidator, BehaviorAnalysisValidation, validate_behavior_analysis};
use tokenizer_hygiene::{TokenizerHygieneStreamingValidator, TokenizerHygieneValidation, validate_tokenizer_hygiene};
use gguf_safety::{GGUFSafetyStreamingValidator, GGUFSafetyValidation, validate_gguf_safety};

/// A Python module implemented in Rust.
#[pymodule]
fn _native(m: &Bound<'_, PyModule>) -> PyResult<()> {
    
    // SafeTensors validation functions
    m.add_function(wrap_pyfunction!(validate_safetensors, m)?)?;
    m.add_function(wrap_pyfunction!(parse_safetensors_header, m)?)?;
    m.add_function(wrap_pyfunction!(is_safetensors, m)?)?;
    
    // Model integrity validation functions
    m.add_function(wrap_pyfunction!(validate_model_integrity, m)?)?;
    
    // Tool calling validation functions
    m.add_function(wrap_pyfunction!(validate_tool_calling, m)?)?;
    
    // Buffer overflow validation functions
    m.add_function(wrap_pyfunction!(validate_buffer_overflow, m)?)?;
    
    // Supply chain validation functions
    m.add_function(wrap_pyfunction!(validate_supply_chain, m)?)?;
    
    // Behavior analysis validation functions
    m.add_function(wrap_pyfunction!(validate_behavior_analysis, m)?)?;
    
    // Tokenizer hygiene validation functions
    m.add_function(wrap_pyfunction!(validate_tokenizer_hygiene, m)?)?;
    
    // GGUF safety validation functions
    m.add_function(wrap_pyfunction!(validate_gguf_safety, m)?)?;
    
    // Add classes
    m.add_class::<SafeTensorsValidation>()?;
    m.add_class::<TensorInfo>()?;
    m.add_class::<SafeTensorsStreamingValidator>()?;
    m.add_class::<ModelIntegrityStreamingValidator>()?;
    m.add_class::<ModelIntegrityValidation>()?;
    m.add_class::<ToolCallingStreamingValidator>()?;
    m.add_class::<ToolCallingValidation>()?;
    m.add_class::<BufferOverflowStreamingValidator>()?;
    m.add_class::<BufferOverflowValidation>()?;
    m.add_class::<SupplyChainStreamingValidator>()?;
    m.add_class::<SupplyChainValidation>()?;
    m.add_class::<BehaviorAnalysisStreamingValidator>()?;
    m.add_class::<BehaviorAnalysisValidation>()?;
    m.add_class::<TokenizerHygieneStreamingValidator>()?;
    m.add_class::<TokenizerHygieneValidation>()?;
    m.add_class::<GGUFSafetyStreamingValidator>()?;
    m.add_class::<GGUFSafetyValidation>()?;
    m.add_class::<PyParallelStreamingScanner>()?;
    m.add_class::<PyPatternMatch>()?;
    
    // Highflame Policy Engine classes (bundled from highflame-policy crate)
    m.add_class::<PyCedarPolicyEngine>()?;
    m.add_class::<PyPolicyEffect>()?;
    
    // Add module metadata
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    
    Ok(())
}

