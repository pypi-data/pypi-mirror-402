use pyo3::prelude::*;
use std::collections::HashSet;

use crate::pattern_matching::Pattern;
use crate::streaming::ParallelStreamingScanner;

/// Validation results for GGUF safety analysis
#[pyclass]
#[derive(Clone, Debug)]
pub struct GGUFSafetyValidation {
    /// Total pattern matches found
    #[pyo3(get)]
    pub total_matches: usize,
    
    /// Suspicious patterns found in tensor data
    #[pyo3(get)]
    pub suspicious_patterns_found: Vec<String>,
    
    /// Executable patterns found
    #[pyo3(get)]
    pub executable_patterns_found: Vec<String>,
    
    /// Malicious patterns found
    #[pyo3(get)]
    pub malicious_patterns_found: Vec<String>,
    
    /// Overall risk score (0.0 to 1.0)
    #[pyo3(get)]
    pub risk_score: f64,
}

/// High-performance streaming validator for GGUF safety
#[pyclass]
pub struct GGUFSafetyStreamingValidator {
    scanner: Option<ParallelStreamingScanner>,
    suspicious_patterns: HashSet<String>,
    executable_patterns: HashSet<String>,
    malicious_patterns: HashSet<String>,
    total_matches: usize,
}

#[pymethods]
impl GGUFSafetyStreamingValidator {
    /// Create a new streaming validator with parallel processing
    ///
    /// Args:
    ///     num_cores: Number of CPU cores to use for parallel processing
    #[new]
    pub fn new(num_cores: usize) -> PyResult<Self> {
        let patterns = get_all_gguf_patterns();
        let scanner = ParallelStreamingScanner::new(patterns, num_cores)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e))?;
        
        Ok(Self {
            scanner: Some(scanner),
            suspicious_patterns: HashSet::new(),
            executable_patterns: HashSet::new(),
            malicious_patterns: HashSet::new(),
            total_matches: 0,
        })
    }
    
    /// Process a chunk of GGUF tensor data
    ///
    /// This method releases the Python GIL for maximum performance and runs
    /// pattern matching in parallel across multiple CPU cores.
    ///
    /// Args:
    ///     chunk: Bytes to scan for GGUF safety issues
    pub fn process_chunk(&mut self, py: Python, chunk: &[u8]) -> PyResult<()> {
        let scanner = self.scanner.as_mut()
            .ok_or_else(|| pyo3::exceptions::PyValueError::new_err("Scanner not initialized"))?;
        
        // Scan chunk for ALL patterns in a single pass (GIL released)
        let all_matches = py.allow_threads(|| {
            scanner.scan_chunk(chunk)
        });
        
        self.total_matches += all_matches.len();
        
        // Categorize matches based on pattern description prefix
        for m in all_matches {
            if let Some(colon_pos) = m.description.find(':') {
                let category = &m.description[..colon_pos];
                
                match category {
                    "suspicious" => {
                        self.suspicious_patterns.insert(m.description.clone());
                    }
                    "executable" => {
                        self.executable_patterns.insert(m.description.clone());
                    }
                    "malicious" => {
                        self.malicious_patterns.insert(m.description.clone());
                    }
                    _ => {
                        self.suspicious_patterns.insert(m.description.clone());
                    }
                }
            }
        }
        
        Ok(())
    }
    
    /// Finalize scanning and get comprehensive results
    ///
    /// Returns:
    ///     GGUFSafetyValidation with categorized findings
    pub fn finalize(&mut self) -> GGUFSafetyValidation {
        // Calculate risk score based on findings
        let mut risk_score = 0.0;
        
        // Weight different categories by severity
        risk_score += self.suspicious_patterns.len() as f64 * 0.15;
        risk_score += self.executable_patterns.len() as f64 * 0.30;
        risk_score += self.malicious_patterns.len() as f64 * 0.40;
        
        // Normalize to 0.0-1.0 range (cap at 1.0)
        risk_score = (risk_score / 10.0).min(1.0);
        
        GGUFSafetyValidation {
            total_matches: self.total_matches,
            suspicious_patterns_found: self.suspicious_patterns.iter().cloned().collect(),
            executable_patterns_found: self.executable_patterns.iter().cloned().collect(),
            malicious_patterns_found: self.malicious_patterns.iter().cloned().collect(),
            risk_score,
        }
    }
}

/// Get all GGUF safety patterns for tensor data analysis
/// NOTE: Uses longer patterns than other validators to avoid false positives in random tensor data
pub fn get_all_gguf_patterns() -> Vec<Pattern> {
    vec![
        // EXECUTABLE HEADERS (should not be in tensor data)
        // Use LONGER patterns to avoid false positives in random quantized tensor data
        Pattern { bytes: b"MZ\x90\x00", description: "executable:pe_header", score: 10 },  // PE header with DOS stub (4 bytes)
        Pattern { bytes: b"\x7fELF\x01\x01\x01", description: "executable:elf_header", score: 10 },  // ELF header (7 bytes)
        Pattern { bytes: b"\xfe\xed\xfa\xce\x00\x00\x00", description: "executable:macho_32bit", score: 10 },  // Mach-O (7 bytes)
        Pattern { bytes: b"\xfe\xed\xfa\xcf\x00\x00\x00", description: "executable:macho_64bit", score: 10 },  // Mach-O (7 bytes)
        Pattern { bytes: b"#!/bin/", description: "executable:shell_script", score: 9 },  // Script shebang (7 bytes)
        Pattern { bytes: b"#!/usr/", description: "executable:usr_script", score: 9 },  // Script shebang (7 bytes)
        
        // MALICIOUS PATTERNS
        Pattern { bytes: b"backdoor", description: "malicious:backdoor_keyword", score: 9 },
        Pattern { bytes: b"malware", description: "malicious:malware_keyword", score: 9 },
        Pattern { bytes: b"exploit", description: "malicious:exploit_keyword", score: 8 },
        Pattern { bytes: b"shellcode", description: "malicious:shellcode_keyword", score: 10 },
        Pattern { bytes: b"payload", description: "malicious:payload_keyword", score: 7 },
        Pattern { bytes: b"rootkit", description: "malicious:rootkit_keyword", score: 10 },
        
        // SUSPICIOUS CODE PATTERNS
        Pattern { bytes: b"eval(", description: "suspicious:eval_function", score: 8 },
        Pattern { bytes: b"exec(", description: "suspicious:exec_function", score: 8 },
        Pattern { bytes: b"system(", description: "suspicious:system_function", score: 9 },
        Pattern { bytes: b"__import__", description: "suspicious:python_import", score: 7 },
        Pattern { bytes: b"subprocess", description: "suspicious:subprocess", score: 8 },
        
        // NETWORK/COMMAND PATTERNS (should not be in tensor data)
        Pattern { bytes: b"http://", description: "suspicious:http_scheme", score: 7 },
        Pattern { bytes: b"https://", description: "suspicious:https_scheme", score: 7 },
        Pattern { bytes: b"curl ", description: "suspicious:curl_command", score: 8 },
        Pattern { bytes: b"wget ", description: "suspicious:wget_command", score: 8 },
        Pattern { bytes: b"powershell", description: "suspicious:powershell", score: 9 },
        
        // FILE ACCESS PATTERNS
        Pattern { bytes: b"/etc/passwd", description: "suspicious:passwd_file", score: 10 },
        Pattern { bytes: b"/etc/shadow", description: "suspicious:shadow_file", score: 10 },
        Pattern { bytes: b".ssh/id_rsa", description: "suspicious:ssh_key", score: 10 },
        Pattern { bytes: b".aws/credentials", description: "suspicious:aws_creds", score: 10 },
    ]
}

/// Validate GGUF tensor data for safety issues (single-pass validation)
///
/// This is a convenience function for validating entire GGUF files at once.
/// For large files, prefer using GGUFSafetyStreamingValidator.
///
/// Args:
///     data: GGUF file data to validate
///     num_cores: Number of CPU cores to use for parallel processing
///
/// Returns:
///     GGUFSafetyValidation with findings
#[pyfunction]
pub fn validate_gguf_safety(py: Python, data: &[u8], num_cores: usize) -> PyResult<GGUFSafetyValidation> {
    let mut validator = GGUFSafetyStreamingValidator::new(num_cores)?;
    
    // Process in a single chunk (GIL released)
    validator.process_chunk(py, data)?;
    
    Ok(validator.finalize())
}

