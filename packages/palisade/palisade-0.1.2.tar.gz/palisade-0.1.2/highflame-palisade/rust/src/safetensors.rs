use pyo3::prelude::*;
use std::collections::HashMap;

use crate::scanner::get_malware_scanner;
use crate::malware_patterns::all_malware_patterns;
use crate::streaming::ParallelStreamingScanner;

/// Minimum suspicion score threshold to flag suspicious patterns in tensor data.
/// 
/// SafeTensors should NEVER contain executable code by design, so we use a high
/// threshold to minimize false positives from random tensor data patterns.
/// 
/// This threshold requires finding either:
/// - 2+ executable headers (score 3 each = 6 total, very suspicious)
/// - 1 executable header + 1 script pattern (3 + 2 = 5, likely mislabeled file)
/// - 3+ script patterns (score 2 each = 6 total, embedded attack code)
const SUSPICIOUS_DATA_SCORE_THRESHOLD: i32 = 5;

/// SafeTensors validation result
#[pyclass]
#[derive(Clone)]
pub struct SafeTensorsValidation {
    #[pyo3(get)]
    pub is_valid: bool,
    
    #[pyo3(get)]
    pub header_size: u64,
    
    #[pyo3(get)]
    pub tensor_count: usize,
    
    #[pyo3(get)]
    pub total_size: usize,
    
    #[pyo3(get)]
    pub warnings: Vec<String>,
    
    #[pyo3(get)]
    pub metadata: Option<HashMap<String, String>>,
    
    // NEW: Tensor names for easy access
    #[pyo3(get)]
    pub tensor_names: Vec<String>,
    
    // NEW: List of suspicious tensor names found
    #[pyo3(get)]
    pub suspicious_tensor_names: Vec<String>,
    
    // NEW: Suspicious patterns detected in tensor data
    #[pyo3(get)]
    pub suspicious_data_patterns: Vec<String>,
}

#[pymethods]
impl SafeTensorsValidation {
    fn __repr__(&self) -> String {
        format!(
            "SafeTensorsValidation(valid={}, tensors={}, size={}, warnings={})",
            self.is_valid, self.tensor_count, self.total_size, self.warnings.len()
        )
    }
}

/// Tensor information from SafeTensors header
#[pyclass]
#[derive(Clone)]
pub struct TensorInfo {
    #[pyo3(get)]
    pub name: String,
    
    #[pyo3(get)]
    pub dtype: String,
    
    #[pyo3(get)]
    pub shape: Vec<usize>,
    
    #[pyo3(get)]
    pub data_offsets: (usize, usize),
}

/// Parse and validate a SafeTensors file with comprehensive security checks (non-streaming)
/// 
/// This function performs:
/// 1. Structure validation (header parsing, JSON validation)
/// 2. Tensor name security checks (suspicious patterns)
/// 3. Data offset validation
/// 4. Tensor data scanning for malicious patterns (executables, scripts, etc.)
/// 5. Metadata validation
#[pyfunction]
pub fn validate_safetensors(py: Python, data: &[u8]) -> PyResult<SafeTensorsValidation> {
    
    // Validate header using shared logic
    let mut result = validate_header_common(data);
    
    // If header validation failed, return early (with full file size)
    if !result.is_valid {
        result.total_size = data.len();
        return Ok(result);
    }
    
    // Extract values for further validation
    let header_size = result.header_size;
    
    // Re-parse header to validate tensor data offsets
    let header_end = 8 + header_size as usize;
    let header_bytes = &data[8..header_end];
    
    if let Ok(header_json) = serde_json::from_slice::<serde_json::Value>(header_bytes) {
        if let Some(header_obj) = header_json.as_object() {
            for (tensor_name, tensor_value) in header_obj.iter() {
                if tensor_name == "__metadata__" {
                    continue;
                }
                
                if let Some(tensor_obj) = tensor_value.as_object() {
                    if let Some(offsets) = tensor_obj.get("data_offsets").and_then(|v| v.as_array()) {
                        if offsets.len() == 2 {
                            if let (Some(start), Some(end)) = (offsets[0].as_u64(), offsets[1].as_u64()) {
                                let data_end = header_end + end as usize;
                                
                                if data_end > data.len() {
                                    result.warnings.push(format!(
                                        "Tensor '{}' data offset {} exceeds file size {}",
                                        tensor_name, data_end, data.len()
                                    ));
                                }
                                
                                if start > end {
                                    result.warnings.push(format!(
                                        "Tensor '{}' has invalid offsets: start {} > end {}",
                                        tensor_name, start, end
                                    ));
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    // Scan tensor data for suspicious patterns (if we have tensor data)
    if header_end < data.len() {
        let tensor_data = &data[header_end..];
        
        // Release GIL during expensive tensor data scanning
        // This allows Python spinner thread to continue updating while Rust scans
        let data_patterns = py.allow_threads(|| {
            scan_tensor_data_for_suspicious_patterns(tensor_data)
        });
        
        for pattern in &data_patterns {
            result.warnings.push(format!(
                "Suspicious pattern in tensor data: {}",
                pattern
            ));
        }
        result.suspicious_data_patterns = data_patterns;
    }
    
    // Update total size and validity
    result.total_size = data.len();
    result.is_valid = result.warnings.is_empty();
    
    Ok(result)
}


/// Validate SafeTensors header structure and tensor names (shared logic)
/// 
/// This is used by both validate_safetensors() and SafeTensorsStreamingValidator
/// to avoid code duplication.
/// 
/// Returns a SafeTensorsValidation with header validation results (total_size=0, suspicious_data_patterns empty)
fn validate_header_common(header_data: &[u8]) -> SafeTensorsValidation {
    let mut warnings = Vec::new();
    let mut suspicious_tensor_names = Vec::new();
    let mut tensor_names = Vec::new();
    
    // Check minimum size
    if header_data.len() < 8 {
        return SafeTensorsValidation {
            is_valid: false,
            header_size: 0,
            tensor_count: 0,
            total_size: 0,
            tensor_names: Vec::new(),
            suspicious_tensor_names: Vec::new(),
            warnings: vec!["File too small to be valid safetensors".to_string()],
            metadata: None,
            suspicious_data_patterns: Vec::new(),
        };
    }
    
    // Parse header size
    let header_size = u64::from_le_bytes([
        header_data[0], header_data[1], header_data[2], header_data[3],
        header_data[4], header_data[5], header_data[6], header_data[7],
    ]);
    
    // Validate header size
    const MAX_HEADER_SIZE: u64 = 100_000_000;
    if header_size > MAX_HEADER_SIZE {
        warnings.push(format!(
            "Header size {} exceeds maximum allowed {} (potential DoS)",
            header_size, MAX_HEADER_SIZE
        ));
        return SafeTensorsValidation {
            is_valid: false,
            header_size,
            tensor_count: 0,
            total_size: 0,
            tensor_names: Vec::new(),
            suspicious_tensor_names: Vec::new(),
            warnings,
            metadata: None,
            suspicious_data_patterns: Vec::new(),
        };
    }
    
    if header_size > (header_data.len() - 8) as u64 {
        warnings.push(format!(
            "Invalid header size: {} > file size {}",
            header_size,
            header_data.len() - 8
        ));
        return SafeTensorsValidation {
            is_valid: false,
            header_size,
            tensor_count: 0,
            total_size: 0,
            tensor_names: Vec::new(),
            suspicious_tensor_names: Vec::new(),
            warnings,
            metadata: None,
            suspicious_data_patterns: Vec::new(),
        };
    }
    
    // Parse JSON header
    let header_end = 8 + header_size as usize;
    let header_bytes = &header_data[8..header_end];
    
    let header_json: serde_json::Value = match serde_json::from_slice(header_bytes) {
        Ok(json) => json,
        Err(e) => {
            warnings.push(format!("Failed to parse JSON header: {}", e));
            return SafeTensorsValidation {
                is_valid: false,
                header_size,
                tensor_count: 0,
                total_size: 0,
                tensor_names: Vec::new(),
                suspicious_tensor_names: Vec::new(),
                warnings,
                metadata: None,
                suspicious_data_patterns: Vec::new(),
            };
        }
    };
    
    // Validate header is an object
    let header_obj = match header_json.as_object() {
        Some(obj) => obj,
        None => {
            warnings.push("Header must be a JSON object".to_string());
            return SafeTensorsValidation {
                is_valid: false,
                header_size,
                tensor_count: 0,
                total_size: 0,
                tensor_names: Vec::new(),
                suspicious_tensor_names: Vec::new(),
                warnings,
                metadata: None,
                suspicious_data_patterns: Vec::new(),
            };
        }
    };
    
    // Extract metadata
    let metadata = header_obj
        .get("__metadata__")
        .and_then(|v| v.as_object())
        .map(|obj| {
            obj.iter()
                .filter_map(|(k, v)| v.as_str().map(|s| (k.clone(), s.to_string())))
                .collect::<HashMap<String, String>>()
        });
    
    // Check tensor names for suspicious patterns
    // NOTE: "__" removed - causes too many false positives for legitimate quantization formats
    let suspicious_patterns = [
        "backdoor_", "poison_", "malicious_", "trojan_",
        "inject_", "exploit_", "rce_", "shell_",
        "..", "//", "\\\\",  // Path traversal
    ];
    
    for (tensor_name, _) in header_obj.iter() {
        if tensor_name == "__metadata__" {
            continue;
        }
        
        tensor_names.push(tensor_name.clone());
        
        let name_lower = tensor_name.to_lowercase();
        let mut is_suspicious = false;
        
        for pattern in &suspicious_patterns {
            if name_lower.contains(pattern) {
                warnings.push(format!(
                    "Suspicious tensor name '{}' contains pattern '{}'",
                    tensor_name, pattern
                ));
                is_suspicious = true;
            }
        }
        
        if is_suspicious {
            suspicious_tensor_names.push(tensor_name.clone());
        }
        
        // Check for unusual characters (shell injection, path traversal)
        if tensor_name.chars().any(|c| "<>|*?\"".contains(c)) {
            warnings.push(format!(
                "Tensor name '{}' contains unusual special characters",
                tensor_name
            ));
            if !is_suspicious {
                suspicious_tensor_names.push(tensor_name.clone());
            }
        }
    }
    
    let is_valid = warnings.is_empty();
    let tensor_count = tensor_names.len();
    
    SafeTensorsValidation {
        is_valid,
        header_size,
        tensor_count,
        total_size: 0, // Unknown/not applicable for header-only validation
        tensor_names,
        suspicious_tensor_names,
        warnings,
        metadata,
        suspicious_data_patterns: Vec::new(), // No data patterns for header-only
    }
}

/// Scan tensor data for suspicious patterns (executables, scripts, shell commands)
/// 
/// NOTE: SafeTensors is designed to NOT contain executable code by design.
/// However, we scan for:
/// 1. Mislabeled files (e.g., .exe renamed to .safetensors)
/// 2. Steganography attacks (malicious payloads hidden in weights)
/// 3. Format exploits (crafted files that exploit parser bugs)
/// 
/// We use a HIGH threshold to minimize false positives from random tensor data.
/// 
/// PERFORMANCE: Uses Aho-Corasick algorithm for O(n + p) complexity
/// - Much faster than naive O(n × p) pattern matching
/// - Single pass through data finds all patterns simultaneously
/// - Optimized with SIMD when available
fn scan_tensor_data_for_suspicious_patterns(data: &[u8]) -> Vec<String> {
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
    
    // Check for excessive null bytes (possible padding attack or steganography)
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
    // SafeTensors should NEVER contain executables by design, so we're conservative
    // We only flag if we find MULTIPLE strong indicators (reduces false positives)
    if suspicion_score >= SUSPICIOUS_DATA_SCORE_THRESHOLD {
        patterns
    } else {
        Vec::new()
    }
}


/// Parse SafeTensors header and extract tensor information
#[pyfunction]
pub fn parse_safetensors_header(data: &[u8]) -> PyResult<Vec<TensorInfo>> {
    if data.len() < 8 {
        return Ok(Vec::new());
    }
    
    let header_size = u64::from_le_bytes([
        data[0], data[1], data[2], data[3],
        data[4], data[5], data[6], data[7],
    ]);
    
    if header_size > (data.len() - 8) as u64 {
        return Ok(Vec::new());
    }
    
    let header_end = 8 + header_size as usize;
    let header_bytes = &data[8..header_end];
    
    let header_json: serde_json::Value = match serde_json::from_slice(header_bytes) {
        Ok(json) => json,
        Err(_) => return Ok(Vec::new()),
    };
    
    let header_obj = match header_json.as_object() {
        Some(obj) => obj,
        None => return Ok(Vec::new()),
    };
    
    let mut tensors = Vec::new();
    
    for (tensor_name, tensor_value) in header_obj.iter() {
        if tensor_name == "__metadata__" {
            continue;
        }
        
        if let Some(tensor_obj) = tensor_value.as_object() {
            let dtype = tensor_obj
                .get("dtype")
                .and_then(|v| v.as_str())
                .unwrap_or("unknown")
                .to_string();
            
            let shape: Vec<usize> = tensor_obj
                .get("shape")
                .and_then(|v| v.as_array())
                .map(|arr| {
                    arr.iter()
                        .filter_map(|v| v.as_u64().map(|n| n as usize))
                        .collect()
                })
                .unwrap_or_default();
            
            let data_offsets = tensor_obj
                .get("data_offsets")
                .and_then(|v| v.as_array())
                .and_then(|arr| {
                    if arr.len() == 2 {
                        Some((
                            arr[0].as_u64().unwrap_or(0) as usize,
                            arr[1].as_u64().unwrap_or(0) as usize,
                        ))
                    } else {
                        None
                    }
                })
                .unwrap_or((0, 0));
            
            tensors.push(TensorInfo {
                name: tensor_name.clone(),
                dtype,
                shape,
                data_offsets,
            });
        }
    }
    
    Ok(tensors)
}

/// Fast check if a file is SafeTensors format (just reads first 8 bytes + small header)
#[pyfunction]
pub fn is_safetensors(data: &[u8]) -> bool {
    if data.len() < 8 {
        return false;
    }
    
    let header_size = u64::from_le_bytes([
        data[0], data[1], data[2], data[3],
        data[4], data[5], data[6], data[7],
    ]);
    
    // Reasonable header size (not too large)
    if header_size == 0 || header_size > 100_000_000 {
        return false;
    }
    
    if (header_size as usize) > data.len() - 8 {
        return false;
    }
    
    let header_end = 8 + header_size as usize;
    let header_bytes = &data[8..header_end];
    
    // Try to parse as JSON
    serde_json::from_slice::<serde_json::Value>(header_bytes).is_ok()
}

/// SafeTensors streaming validator
/// 
/// This class allows streaming validation of large SafeTensors files by processing
/// chunks sequentially while maintaining state for pattern detection across boundaries.
#[pyclass]
pub struct SafeTensorsStreamingValidator {
    scanner: Option<ParallelStreamingScanner>,
    header_result: Option<SafeTensorsValidation>,
}

#[pymethods]
impl SafeTensorsStreamingValidator {
    /// Create a new streaming validator
    #[new]
    pub fn new(num_cores: usize) -> PyResult<Self> {
        let patterns = all_malware_patterns();
        let scanner = ParallelStreamingScanner::new(patterns, num_cores)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e))?;
        
        Ok(Self {
            scanner: Some(scanner),
            header_result: None,
        })
    }
    
    /// Validate the SafeTensors header (call this with header data first)
    pub fn validate_header(&mut self, header_data: &[u8]) -> PyResult<bool> {
        // Use shared header validation logic - store result directly
        let result = validate_header_common(header_data);
        let is_valid = result.is_valid;
        self.header_result = Some(result);
        Ok(is_valid)
    }
    
    /// Process a chunk of tensor data (call after validate_header)
    /// 
    /// Releases GIL during processing for maximum performance.
    pub fn process_chunk(&mut self, py: Python, chunk: &[u8]) -> PyResult<Vec<String>> {
        if self.header_result.is_none() {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "Must call validate_header() before process_chunk()"
            ));
        }
        
        let scanner = self.scanner.as_mut()
            .ok_or_else(|| pyo3::exceptions::PyValueError::new_err("Scanner not initialized"))?;
        
        // Scan chunk for suspicious patterns (GIL released)
        let matches = py.allow_threads(|| {
            scanner.scan_chunk(chunk)
        });
        
        // Convert matches to pattern descriptions
        let patterns: Vec<String> = matches.into_iter()
            .map(|m| m.description)
            .collect();
        
        Ok(patterns)
    }
    
    /// Finalize validation and get results
    pub fn finalize(&mut self, py: Python) -> PyResult<SafeTensorsValidation> {
        // Get header result or return error
        let mut result = self.header_result.take()
            .ok_or_else(|| pyo3::exceptions::PyValueError::new_err(
                "Must call validate_header() before finalize()"
            ))?;
        
        let scanner = self.scanner.as_mut()
            .ok_or_else(|| pyo3::exceptions::PyValueError::new_err("Scanner not initialized"))?;
        
        // Get final matches from overlap buffer
        let final_matches = py.allow_threads(|| {
            scanner.finalize()
        });
        
        // Collect all suspicious data patterns
        let suspicious_data_patterns: Vec<String> = final_matches.into_iter()
            .map(|m| m.description)
            .collect();
        
        // Calculate suspicion score
        let mut suspicion_score = 0;
        for pattern in &suspicious_data_patterns {
            if pattern.contains("executable") || pattern.contains("Mach-O") || pattern.contains("ELF") {
                suspicion_score += 3;
            } else if pattern.contains("script") || pattern.contains("shebang") || pattern.contains("import") {
                suspicion_score += 2;
            } else {
                suspicion_score += 1;
            }
        }
        
        // Only return patterns if score exceeds threshold
        let final_suspicious_patterns = if suspicion_score >= SUSPICIOUS_DATA_SCORE_THRESHOLD {
            suspicious_data_patterns
        } else {
            Vec::new()
        };
        
        // Add data pattern warnings to result
        for pattern in &final_suspicious_patterns {
            result.warnings.push(format!("Suspicious pattern in tensor data: {}", pattern));
        }
        result.suspicious_data_patterns = final_suspicious_patterns;
        
        // Update validity based on warnings
        result.is_valid = result.warnings.is_empty();
        
        Ok(result)
    }
}

