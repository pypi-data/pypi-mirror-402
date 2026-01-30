/// High-performance tool calling security validation
///
/// This module provides optimized detection of malicious tool-calling patterns
/// in ML models, specifically targeting DoubleAgents/BadAgent-style attacks.
///
/// Performance optimizations:
/// - Uses Aho-Corasick for O(n + p) pattern matching (single pass)
/// - Parallel processing for multi-core systems
/// - Streaming support for large models without memory issues
/// - GIL-free processing for maximum Python integration performance

use pyo3::prelude::*;
use pyo3::types::PyDict;
use crate::pattern_matching::Pattern;
use crate::streaming::ParallelStreamingScanner;
use std::collections::HashSet;

/// Tool calling validation result
#[pyclass]
#[derive(Debug, Clone)]
pub struct ToolCallingValidation {
    #[pyo3(get)]
    pub dangerous_tools_found: Vec<String>,
    
    #[pyo3(get)]
    pub suspicious_parameters_found: Vec<String>,
    
    #[pyo3(get)]
    pub total_matches: usize,
    
    #[pyo3(get)]
    pub risk_score: i32,
}

#[pymethods]
impl ToolCallingValidation {
    fn __repr__(&self) -> String {
        format!(
            "ToolCallingValidation(dangerous_tools={}, suspicious_params={}, risk_score={})",
            self.dangerous_tools_found.len(),
            self.suspicious_parameters_found.len(),
            self.risk_score
        )
    }
}

/// Get all tool calling patterns (unified)
/// 
/// Mirrors Python's 68 regex patterns using literal byte matching.
/// Strategy: Match prefixes/key parts instead of expanding every regex variant.
/// 
/// Pattern naming convention:
/// - "dangerous:" prefix for high-risk tool patterns  
/// - "suspicious:" prefix for parameter injection risks
/// - "schema:" prefix for tool definition patterns
fn get_all_tool_calling_patterns() -> Vec<Pattern> {
    vec![
        // DANGEROUS TOOLS - System access (matches Python regex with prefixes)
        // Python: r"admin_(?:access|escalate|override)" → Rust: "admin_" catches all
        Pattern { bytes: b"admin_", description: "dangerous:admin_tool", score: 5 },
        Pattern { bytes: b"root_", description: "dangerous:root_tool", score: 5 },
        Pattern { bytes: b"sudo_", description: "dangerous:sudo_tool", score: 5 },
        Pattern { bytes: b"system_", description: "dangerous:system_tool", score: 4 },
        Pattern { bytes: b"shell_", description: "dangerous:shell_tool", score: 4 },
        Pattern { bytes: b"bash_", description: "dangerous:bash_tool", score: 4 },
        
        // DANGEROUS TOOLS - File operations (prefix matching)
        Pattern { bytes: b"delete_", description: "dangerous:delete_tool", score: 4 },
        Pattern { bytes: b"remove_", description: "dangerous:remove_tool", score: 4 },
        Pattern { bytes: b"destroy_", description: "dangerous:destroy_tool", score: 4 },
        Pattern { bytes: b"format_", description: "dangerous:format_tool", score: 5 },
        Pattern { bytes: b"erase_", description: "dangerous:erase_tool", score: 5 },
        Pattern { bytes: b"overwrite_", description: "dangerous:overwrite_tool", score: 4 },
        Pattern { bytes: b"corrupt_", description: "dangerous:corrupt_tool", score: 4 },
        
        // DANGEROUS TOOLS - Network operations (prefix matching)
        Pattern { bytes: b"connect_", description: "dangerous:connect_tool", score: 4 },
        Pattern { bytes: b"upload_", description: "dangerous:upload_tool", score: 3 },
        Pattern { bytes: b"send_", description: "dangerous:send_tool", score: 3 },
        Pattern { bytes: b"transmit_", description: "dangerous:transmit_tool", score: 3 },
        Pattern { bytes: b"exfiltrate_", description: "dangerous:exfiltrate_tool", score: 5 },
        Pattern { bytes: b"download_", description: "dangerous:download_tool", score: 3 },
        Pattern { bytes: b"establish_", description: "dangerous:establish_tool", score: 4 },
        Pattern { bytes: b"access_external", description: "dangerous:access_external", score: 4 },
        Pattern { bytes: b"access_remote", description: "dangerous:access_remote", score: 4 },
        
        // DANGEROUS TOOLS - Credential access (prefix matching)
        Pattern { bytes: b"steal_", description: "dangerous:steal_tool", score: 5 },
        Pattern { bytes: b"harvest_", description: "dangerous:harvest_tool", score: 5 },
        Pattern { bytes: b"bypass_", description: "dangerous:bypass_tool", score: 5 },
        Pattern { bytes: b"crack_", description: "dangerous:crack_tool", score: 4 },
        Pattern { bytes: b"extract_", description: "dangerous:extract_tool", score: 4 },
        Pattern { bytes: b"impersonate_", description: "dangerous:impersonate_tool", score: 5 },
        Pattern { bytes: b"access_credentials", description: "dangerous:access_credentials", score: 5 },
        Pattern { bytes: b"access_passwords", description: "dangerous:access_passwords", score: 5 },
        Pattern { bytes: b"read_credentials", description: "dangerous:read_credentials", score: 4 },
        Pattern { bytes: b"read_passwords", description: "dangerous:read_passwords", score: 5 },
        
        // DANGEROUS TOOLS - Data manipulation (prefix matching)
        Pattern { bytes: b"modify_", description: "dangerous:modify_tool", score: 4 },
        Pattern { bytes: b"alter_", description: "dangerous:alter_tool", score: 4 },
        Pattern { bytes: b"inject_", description: "dangerous:inject_tool", score: 5 },
        Pattern { bytes: b"insert_", description: "dangerous:insert_tool", score: 5 },
        Pattern { bytes: b"implant_", description: "dangerous:implant_tool", score: 5 },
        Pattern { bytes: b"hide_", description: "dangerous:hide_tool", score: 4 },
        Pattern { bytes: b"disable_", description: "dangerous:disable_tool", score: 5 },
        
        // SUSPICIOUS PARAMS - Command injection
        Pattern { bytes: b"; rm -rf", description: "suspicious:shell_command_injection", score: 5 },
        Pattern { bytes: b"&& rm -rf", description: "suspicious:shell_command_chaining", score: 5 },
        Pattern { bytes: b"| bash", description: "suspicious:pipe_to_bash", score: 4 },
        Pattern { bytes: b"| sh", description: "suspicious:pipe_to_sh", score: 4 },
        // Note: Removed single backtick (`) and $( - too short, match binary data constantly
        
        // SUSPICIOUS PARAMS - Destructive SQL (matches Python's 3 patterns)
        Pattern { bytes: b"DROP DATABASE", description: "suspicious:drop_database", score: 5 },
        Pattern { bytes: b"DELETE FROM", description: "suspicious:delete_from", score: 4 },
        Pattern { bytes: b"TRUNCATE TABLE", description: "suspicious:truncate_table", score: 5 },
        
        // SUSPICIOUS PARAMS - Privilege escalation (matches Python's 9 patterns)
        Pattern { bytes: b"su -", description: "suspicious:su_command", score: 4 },
        // Pattern { bytes: b"sudo", description: "suspicious:sudo", score: 3 },
        Pattern { bytes: b"chmod 777", description: "suspicious:chmod_777", score: 4 },
        Pattern { bytes: b"chown root", description: "suspicious:chown_root", score: 4 },
        Pattern { bytes: b"setuid", description: "suspicious:setuid", score: 4 },
        Pattern { bytes: b"setgid", description: "suspicious:setgid", score: 4 },
        Pattern { bytes: b"runas", description: "suspicious:runas", score: 4 },
        Pattern { bytes: b"net user", description: "suspicious:net_user", score: 3 },
        Pattern { bytes: b"usermod", description: "suspicious:usermod", score: 3 },
        
        // SUSPICIOUS PARAMS - Network abuse (matches Python's 3 patterns)
        Pattern { bytes: b"nc -e", description: "suspicious:nc_execute", score: 5 },
        Pattern { bytes: b"netcat -e", description: "suspicious:netcat_execute", score: 5 },
        Pattern { bytes: b"ssh -R", description: "suspicious:ssh_reverse", score: 4 },
        
        // SUSPICIOUS PARAMS - Data exfiltration (lengthened to avoid binary false positives)
        Pattern { bytes: b"base64 -", description: "suspicious:base64_pipe", score: 3 },
        Pattern { bytes: b"| gzip", description: "suspicious:gzip_pipe", score: 3 },
        Pattern { bytes: b"| tar", description: "suspicious:tar_pipe", score: 3 },
        Pattern { bytes: b"mysqldump", description: "suspicious:mysqldump", score: 3 },
        Pattern { bytes: b"pg_dump", description: "suspicious:pg_dump", score: 3 },
        Pattern { bytes: b"cat /etc/passwd", description: "suspicious:cat_passwd", score: 5 },
        Pattern { bytes: b"cat /etc/shadow", description: "suspicious:cat_shadow", score: 5 },
        
        // SUSPICIOUS PARAMS - Stealth operations (matches Python's 8 patterns)
        // Pattern { bytes: b"nohup", description: "suspicious:nohup", score: 3 },
        Pattern { bytes: b"screen -d", description: "suspicious:screen_detach", score: 3 },
        Pattern { bytes: b"disown", description: "suspicious:disown", score: 3 },
        Pattern { bytes: b"history -c", description: "suspicious:history_clear", score: 4 },
        Pattern { bytes: b"unset HISTFILE", description: "suspicious:unset_histfile", score: 4 },
        Pattern { bytes: b"HISTSIZE=0", description: "suspicious:zero_histsize", score: 4 },
        Pattern { bytes: b">/dev/null", description: "suspicious:dev_null_redirect", score: 3 },
        Pattern { bytes: b"syslog", description: "suspicious:syslog", score: 2 },
    ]
}

/// Streaming validator for tool calling patterns
/// 
/// Simplified design using a single scanner (like SafeTensors):
/// - One Aho-Corasick automaton for all patterns
/// - Single pass through data
/// - Categorization done in Python based on pattern name prefix
#[pyclass]
pub struct ToolCallingStreamingValidator {
    scanner: Option<ParallelStreamingScanner>,
    
    // Accumulate results across chunks
    dangerous_tools: HashSet<String>,
    suspicious_parameters: HashSet<String>,
    total_matches: usize,
}

#[pymethods]
impl ToolCallingStreamingValidator {
    /// Create a new streaming validator with parallel processing
    ///
    /// Args:
    ///     num_cores: Number of CPU cores to use for parallel processing
    #[new]
    pub fn new(num_cores: usize) -> PyResult<Self> {
        // Create single scanner with all patterns (like SafeTensors does)
        let patterns = get_all_tool_calling_patterns();
        let scanner = ParallelStreamingScanner::new(patterns, num_cores)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e))?;
        
        Ok(Self {
            scanner: Some(scanner),
            dangerous_tools: HashSet::new(),
            suspicious_parameters: HashSet::new(),
            total_matches: 0,
        })
    }
    
    /// Process a chunk of model data
    ///
    /// This method releases the Python GIL for maximum performance and runs
    /// pattern matching in parallel across multiple CPU cores.
    ///
    /// Single-pass scanning finds all patterns simultaneously (Aho-Corasick algorithm).
    /// Categorization is done based on pattern name prefix (dangerous:/suspicious:/schema:).
    ///
    /// Args:
    ///     chunk: Bytes to scan for tool calling patterns
    ///
    /// Returns:
    ///     Dictionary with categorized matches found in this chunk
    pub fn process_chunk(&mut self, py: Python, chunk: &[u8]) -> PyResult<PyObject> {
        let scanner = self.scanner.as_mut()
            .ok_or_else(|| pyo3::exceptions::PyValueError::new_err("Scanner not initialized"))?;
        
        // Scan chunk for ALL patterns in a single pass (GIL released)
        let all_matches = py.allow_threads(|| {
            scanner.scan_chunk(chunk)
        });
        
        // Categorize matches based on pattern name prefix
        // Split on ':' to extract only the value part (e.g., "dangerous:exec" -> "exec")
        let mut dangerous_chunk = Vec::new();
        let mut suspicious_chunk = Vec::new();
        
        for m in all_matches {
            if let Some((category, value)) = m.description.split_once(':') {
                match category {
                    "dangerous" => {
                        self.dangerous_tools.insert(value.to_string());
                        dangerous_chunk.push(value.to_string());
                    }
                    "suspicious" => {
                        self.suspicious_parameters.insert(value.to_string());
                        suspicious_chunk.push(value.to_string());
                    }
                    _ => {}
                }
            }
            self.total_matches += 1;
        }
        
        // Return chunk results as Python dict (for debugging/logging)
        let result = PyDict::new_bound(py);
        result.set_item("dangerous_tools", dangerous_chunk)?;
        result.set_item("suspicious_parameters", suspicious_chunk)?;
        
        Ok(result.into())
    }
    
    /// Finalize validation and get comprehensive results
    ///
    /// Returns:
    ///     ToolCallingValidation with all accumulated findings
    pub fn finalize(&self) -> PyResult<ToolCallingValidation> {
        // Calculate risk score based on findings
        let dangerous_count = self.dangerous_tools.len() as i32;
        let suspicious_count = self.suspicious_parameters.len() as i32;
        
        // Risk scoring:
        // - Dangerous tools: 5 points each
        // - Suspicious params: 2 points each
        let risk_score = (dangerous_count * 5) + (suspicious_count * 2);
        
        Ok(ToolCallingValidation {
            dangerous_tools_found: self.dangerous_tools.iter().cloned().collect(),
            suspicious_parameters_found: self.suspicious_parameters.iter().cloned().collect(),
            total_matches: self.total_matches,
            risk_score,
        })
    }
    
    /// Reset the validator to process a new model
    pub fn reset(&mut self) {
        self.dangerous_tools.clear();
        self.suspicious_parameters.clear();
        self.total_matches = 0;
    }
}

/// Quick validation function for non-streaming use cases
///
/// This is useful for small files or when you have the entire model in memory.
/// For large models, use ToolCallingStreamingValidator instead.
///
/// Args:
///     data: Complete model data to scan
///     num_cores: Number of CPU cores to use (default: 1)
///
/// Returns:
///     ToolCallingValidation with all findings
#[pyfunction]
#[pyo3(signature = (data, num_cores=1))]
pub fn validate_tool_calling(py: Python, data: &[u8], num_cores: usize) -> PyResult<ToolCallingValidation> {
    // Create validator
    let mut validator = ToolCallingStreamingValidator::new(num_cores)?;
    
    // Process entire data as single chunk (GIL released)
    validator.process_chunk(py, data)?;
    
    // Return final results
    validator.finalize()
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_dangerous_tool_detection() {
        let test_data = b"function admin_access() { return root_access(); }";
        
        pyo3::prepare_freethreaded_python();
        Python::with_gil(|py| {
            let result = validate_tool_calling(py, test_data, 1).unwrap();
            assert!(result.dangerous_tools_found.len() > 0);
            assert!(result.risk_score > 0);
        });
    }
    
    #[test]
    fn test_suspicious_parameters() {
        let test_data = b"execute_command('; rm -rf /')";
        
        pyo3::prepare_freethreaded_python();
        Python::with_gil(|py| {
            let result = validate_tool_calling(py, test_data, 1).unwrap();
            assert!(result.suspicious_parameters_found.len() > 0);
        });
    }
    
    #[test]
    fn test_streaming_validator() {
        pyo3::prepare_freethreaded_python();
        Python::with_gil(|py| {
            let mut validator = ToolCallingStreamingValidator::new(2).unwrap();
            
            // Process multiple chunks
            let chunk1 = b"admin_access tool found here";
            let chunk2 = b"and suspicious parameter: ; rm -rf";
            
            validator.process_chunk(py, chunk1).unwrap();
            validator.process_chunk(py, chunk2).unwrap();
            
            let result = validator.finalize().unwrap();
            assert!(result.dangerous_tools_found.len() > 0);
            assert!(result.suspicious_parameters_found.len() > 0);
            assert!(result.total_matches > 0);
        });
    }
}

