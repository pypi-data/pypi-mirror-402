//! Model Integrity validator using streaming pattern matching.

use pyo3::prelude::*;

use crate::scanner::get_malware_scanner;
use crate::malware_patterns::all_malware_patterns;
use crate::streaming::ParallelStreamingScanner;
use crate::py_streaming::PyPatternMatch;

/// Minimum suspicion score threshold for model integrity warnings
const SUSPICIOUS_SCORE_THRESHOLD: i32 = 3;

/// Result of model integrity validation
#[pyclass]
#[derive(Clone)]
pub struct ModelIntegrityValidation {
    #[pyo3(get)]
    pub is_valid: bool,
    
    #[pyo3(get)]
    pub warnings: Vec<String>,
    
    #[pyo3(get)]
    pub suspicious_patterns: Vec<String>,
}

#[pymethods]
impl ModelIntegrityValidation {
    #[new]
    fn new() -> Self {
        Self {
            is_valid: true,
            warnings: Vec::new(),
            suspicious_patterns: Vec::new(),
        }
    }
    
    fn __repr__(&self) -> String {
        format!(
            "ModelIntegrityValidation(valid={}, warnings={})",
            self.is_valid, self.warnings.len()
        )
    }
}


/// Validate complete model file for integrity issues
/// 
/// This performs malware pattern detection using the SHARED scanner
#[pyfunction]
pub fn validate_model_integrity(py: Python, data: &[u8]) -> PyResult<ModelIntegrityValidation> {
    let mut result = ModelIntegrityValidation::new();
    
    // Malware pattern scanning (REUSING SHARED SCANNER!)
    // Release GIL during expensive pattern scanning
    let patterns = py.allow_threads(|| {
        scan_for_malware_patterns(data)
    });
    
    result.suspicious_patterns = patterns.clone();
    if !patterns.is_empty() {
        for pattern in &patterns {
            result.warnings.push(format!("Suspicious pattern detected: {}", pattern));
        }
        result.is_valid = false;
    }
    
    Ok(result)
}

/// Scan data for malware patterns using the SHARED global scanner
/// 
/// This is the SAME logic as safetensors.rs uses - we reuse the infrastructure!
/// Uses Aho-Corasick algorithm for O(n + p) complexity.
fn scan_for_malware_patterns(data: &[u8]) -> Vec<String> {
    let mut patterns = Vec::new();
    let mut suspicion_score = 0;
    
    // Use the global optimized malware scanner (Aho-Corasick)
    // This is initialized once and reused across all calls
    let scanner = get_malware_scanner();
    
    // Scan for all malware patterns in a SINGLE O(n) pass
    let matches = scanner.scan_all(data);
    
    // Collect matched patterns and calculate suspicion score
    for mat in matches {
        patterns.push(mat.description);
        suspicion_score += mat.score;
    }
    
    // Check for excessive null bytes (possible padding attack)
    if data.len() >= 1024 {
        let null_count = data.iter().filter(|&&b| b == 0).count();
        let null_percentage = (null_count as f64 / data.len() as f64) * 100.0;
        
        if null_percentage > 95.0 {
            patterns.push(format!(
                "Excessive null bytes ({:.1}% of data) - possible padding attack",
                null_percentage
            ));
            suspicion_score += 2;
        }
    }
    
    // Only return patterns if suspicion score exceeds threshold
    if suspicion_score >= SUSPICIOUS_SCORE_THRESHOLD {
        patterns
    } else {
        Vec::new()
    }
}

/// Streaming validator for generic model integrity checks
/// 
/// This uses the SAME ParallelStreamingScanner infrastructure as SafeTensorsStreamingValidator
#[pyclass(name = "ModelIntegrityStreamingValidator")]
pub struct ModelIntegrityStreamingValidator {
    scanner: Option<ParallelStreamingScanner>,
}

#[pymethods]
impl ModelIntegrityStreamingValidator {
    /// Create a new streaming validator with common malware patterns
    #[new]
    pub fn new(num_cores: usize) -> PyResult<Self> {
        let patterns = all_malware_patterns();
        let scanner = ParallelStreamingScanner::new(patterns, num_cores)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e))?;
        
        Ok(Self {
            scanner: Some(scanner),
        })
    }
    
    /// Process a chunk of data (SAME interface as SafeTensorsStreamingValidator)
    pub fn process_chunk(&mut self, py: Python, chunk: &[u8]) -> PyResult<Vec<PyPatternMatch>> {
        let scanner = self.scanner.as_mut()
            .ok_or_else(|| pyo3::exceptions::PyValueError::new_err("Scanner not initialized"))?;
        
        let matches = py.allow_threads(|| scanner.scan_chunk(chunk));
        let py_matches: Vec<PyPatternMatch> = matches.into_iter().map(PyPatternMatch::from).collect();
        Ok(py_matches)
    }
    
    /// Finalize and get remaining matches (SAME interface as SafeTensorsStreamingValidator)
    pub fn finalize(&mut self, py: Python) -> PyResult<Vec<PyPatternMatch>> {
        if let Some(mut scanner) = self.scanner.take() {
            let matches = py.allow_threads(move || scanner.finalize());
            let py_matches: Vec<PyPatternMatch> = matches.into_iter().map(PyPatternMatch::from).collect();
            Ok(py_matches)
        } else {
            Ok(Vec::new())
        }
    }
}
