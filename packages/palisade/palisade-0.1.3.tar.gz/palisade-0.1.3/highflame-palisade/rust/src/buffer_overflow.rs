use pyo3::prelude::*;
use std::collections::HashSet;

use crate::pattern_matching::Pattern;
use crate::streaming::ParallelStreamingScanner;

/// Validation results for buffer overflow analysis
#[pyclass]
#[derive(Clone, Debug)]
pub struct BufferOverflowValidation {
    /// Total pattern matches found
    #[pyo3(get)]
    pub total_matches: usize,
    
    /// Unique dangerous functions detected
    #[pyo3(get)]
    pub dangerous_functions_found: Vec<String>,
    
    /// ROP gadget patterns detected
    #[pyo3(get)]
    pub rop_gadgets_found: Vec<String>,
    
    /// Format string vulnerabilities detected
    #[pyo3(get)]
    pub format_string_vulns_found: Vec<String>,
    
    /// Integer overflow patterns detected
    #[pyo3(get)]
    pub integer_overflow_patterns_found: Vec<String>,
    
    /// Overall risk score (0.0 to 1.0)
    #[pyo3(get)]
    pub risk_score: f64,
}

/// High-performance streaming validator for buffer overflow detection
#[pyclass]
pub struct BufferOverflowStreamingValidator {
    scanner: Option<ParallelStreamingScanner>,
    dangerous_functions: HashSet<String>,
    rop_gadgets: HashSet<String>,
    format_string_vulns: HashSet<String>,
    integer_overflow_patterns: HashSet<String>,
    total_matches: usize,
}

#[pymethods]
impl BufferOverflowStreamingValidator {
    /// Create a new streaming validator with parallel processing
    ///
    /// Args:
    ///     num_cores: Number of CPU cores to use for parallel processing
    #[new]
    pub fn new(num_cores: usize) -> PyResult<Self> {
        let patterns = get_all_buffer_overflow_patterns();
        let scanner = ParallelStreamingScanner::new(patterns, num_cores)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e))?;
        
        Ok(Self {
            scanner: Some(scanner),
            dangerous_functions: HashSet::new(),
            rop_gadgets: HashSet::new(),
            format_string_vulns: HashSet::new(),
            integer_overflow_patterns: HashSet::new(),
            total_matches: 0,
        })
    }
    
    /// Process a chunk of model data
    ///
    /// This method releases the Python GIL for maximum performance and runs
    /// pattern matching in parallel across multiple CPU cores.
    ///
    /// Args:
    ///     chunk: Bytes to scan for buffer overflow patterns
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
                    "dangerous" => {
                        self.dangerous_functions.insert(m.description.clone());
                    }
                    "rop" => {
                        self.rop_gadgets.insert(m.description.clone());
                    }
                    "format_string" => {
                        self.format_string_vulns.insert(m.description.clone());
                    }
                    "integer_overflow" => {
                        self.integer_overflow_patterns.insert(m.description.clone());
                    }
                    _ => {}
                }
            }
        }
        
        Ok(())
    }
    
    /// Finalize and get comprehensive results
    pub fn finalize(&self) -> PyResult<BufferOverflowValidation> {
        // Calculate risk score based on findings
        let dangerous_count = self.dangerous_functions.len();
        let rop_count = self.rop_gadgets.len();
        let format_string_count = self.format_string_vulns.len();
        let integer_overflow_count = self.integer_overflow_patterns.len();
        
        // Weighted risk calculation
        let risk_score = (
            (dangerous_count as f64 * 0.4) +
            (rop_count as f64 * 0.3) +
            (format_string_count as f64 * 0.2) +
            (integer_overflow_count as f64 * 0.1)
        ).min(1.0);
        
        Ok(BufferOverflowValidation {
            total_matches: self.total_matches,
            dangerous_functions_found: self.dangerous_functions.iter().cloned().collect(),
            rop_gadgets_found: self.rop_gadgets.iter().cloned().collect(),
            format_string_vulns_found: self.format_string_vulns.iter().cloned().collect(),
            integer_overflow_patterns_found: self.integer_overflow_patterns.iter().cloned().collect(),
            risk_score,
        })
    }
    
    /// Reset validator state for reuse
    pub fn reset(&mut self) {
        self.dangerous_functions.clear();
        self.rop_gadgets.clear();
        self.format_string_vulns.clear();
        self.integer_overflow_patterns.clear();
        self.total_matches = 0;
    }
}

/// Get all buffer overflow detection patterns with category prefixes
pub fn get_all_buffer_overflow_patterns() -> Vec<Pattern> {
    vec![
        // DANGEROUS FUNCTIONS - String manipulation (high risk)
        Pattern { bytes: b"strcpy\0", description: "dangerous:strcpy", score: 5 },
        Pattern { bytes: b"strcat\0", description: "dangerous:strcat", score: 5 },
        Pattern { bytes: b"sprintf\0", description: "dangerous:sprintf", score: 5 },
        Pattern { bytes: b"gets\0", description: "dangerous:gets", score: 5 },
        Pattern { bytes: b"scanf\0", description: "dangerous:scanf", score: 4 },
        Pattern { bytes: b"strncpy\0", description: "dangerous:strncpy", score: 4 },
        Pattern { bytes: b"strncat\0", description: "dangerous:strncat", score: 4 },
        Pattern { bytes: b"snprintf\0", description: "dangerous:snprintf", score: 3 },
        Pattern { bytes: b"vsprintf\0", description: "dangerous:vsprintf", score: 5 },
        Pattern { bytes: b"vsnprintf\0", description: "dangerous:vsnprintf", score: 4 },
        
        // Symbol versioning variants (Linux)
        Pattern { bytes: b"strcpy@", description: "dangerous:strcpy", score: 5 },
        Pattern { bytes: b"memcpy@", description: "dangerous:memcpy", score: 4 },
        Pattern { bytes: b"sprintf@", description: "dangerous:sprintf", score: 5 },
        
        // DANGEROUS FUNCTIONS - Memory operations
        Pattern { bytes: b"memcpy\0", description: "dangerous:memcpy", score: 4 },
        Pattern { bytes: b"memmove\0", description: "dangerous:memmove", score: 4 },
        Pattern { bytes: b"memset\0", description: "dangerous:memset", score: 3 },
        Pattern { bytes: b"bcopy\0", description: "dangerous:bcopy", score: 4 },
        Pattern { bytes: b"bzero\0", description: "dangerous:bzero", score: 3 },
        
        // DANGEROUS FUNCTIONS - Allocation
        Pattern { bytes: b"malloc\0", description: "dangerous:malloc", score: 3 },
        Pattern { bytes: b"calloc\0", description: "dangerous:calloc", score: 3 },
        Pattern { bytes: b"realloc\0", description: "dangerous:realloc", score: 3 },
        Pattern { bytes: b"alloca\0", description: "dangerous:alloca", score: 4 },
        
        // DANGEROUS FUNCTIONS - Format string vulnerabilities
        Pattern { bytes: b"printf\0", description: "dangerous:printf", score: 4 },
        Pattern { bytes: b"fprintf\0", description: "dangerous:fprintf", score: 4 },
        Pattern { bytes: b"dprintf\0", description: "dangerous:dprintf", score: 4 },
        Pattern { bytes: b"syslog\0", description: "dangerous:syslog", score: 4 },
        
        // ROP GADGETS - x86 instruction sequences
        Pattern { bytes: b"\x58\xc3", description: "rop:pop_eax_ret", score: 5 },
        Pattern { bytes: b"\x5d\xc3", description: "rop:pop_ebp_ret", score: 5 },
        Pattern { bytes: b"\xff\xe4", description: "rop:jmp_esp", score: 5 },
        Pattern { bytes: b"\xff\x25", description: "rop:jmp_indirect", score: 4 },
        Pattern { bytes: b"\x81\xc4", description: "rop:add_esp_imm32", score: 3 },
        Pattern { bytes: b"\x81\xec", description: "rop:sub_esp_imm32", score: 3 },
        Pattern { bytes: b"\xf3\xa4", description: "rop:rep_movsb", score: 4 },
        Pattern { bytes: b"\xf3\xa5", description: "rop:rep_movsd", score: 4 },
        Pattern { bytes: b"\xf3\xaa", description: "rop:rep_stosb", score: 4 },
        
        // FORMAT STRING VULNERABILITIES
        Pattern { bytes: b"%n", description: "format_string:format_n_specifier", score: 5 },
        Pattern { bytes: b"%s%s%s", description: "format_string:repeated_s", score: 4 },
        Pattern { bytes: b"%x%x%x", description: "format_string:repeated_x", score: 4 },
        Pattern { bytes: b"%p%p%p", description: "format_string:repeated_p", score: 4 },
        
        // INTEGER OVERFLOW PATTERNS
        Pattern { bytes: b"size * count", description: "integer_overflow:multiply_size_count", score: 3 },
        Pattern { bytes: b"len + 1", description: "integer_overflow:increment_len", score: 2 },
        Pattern { bytes: b"sizeof(", description: "integer_overflow:sizeof_expr", score: 2 },
    ]
}

/// Standalone validation function for single-pass scanning
#[pyfunction]
pub fn validate_buffer_overflow(py: Python, data: &[u8], num_threads: usize) -> PyResult<BufferOverflowValidation> {
    let mut validator = BufferOverflowStreamingValidator::new(num_threads)?;
    validator.process_chunk(py, data)?;
    validator.finalize()
}

#[cfg(test)]
mod tests {
    use super::*;
    use pyo3::Python;

    #[test]
    fn test_dangerous_function_detection() {
        Python::with_gil(|py| {
            let data = b"test\x00strcpy\x00test";
            let result = validate_buffer_overflow(py, data, 1).unwrap();
            assert!(result.dangerous_functions_found.contains(&"dangerous:strcpy".to_string()));
        });
    }

    #[test]
    fn test_rop_gadget_detection() {
        Python::with_gil(|py| {
            let data = b"some\x58\xc3data"; // pop eax; ret
            let result = validate_buffer_overflow(py, data, 1).unwrap();
            assert!(result.rop_gadgets_found.contains(&"rop:pop_eax_ret".to_string()));
        });
    }

    #[test]
    fn test_format_string_detection() {
        Python::with_gil(|py| {
            let data = b"printf(\"%n\");";
            let result = validate_buffer_overflow(py, data, 1).unwrap();
            assert!(result.format_string_vulns_found.contains(&"format_string:format_n_specifier".to_string()));
        });
    }
    
    #[test]
    fn test_streaming_validation() {
        Python::with_gil(|py| {
            let mut validator = BufferOverflowStreamingValidator::new(2).unwrap();
            
            // Process in chunks
            validator.process_chunk(py, b"chunk1\x00strcpy\x00").unwrap();
            validator.process_chunk(py, b"chunk2\x00memcpy\x00").unwrap();
            
            let result = validator.finalize().unwrap();
            assert_eq!(result.dangerous_functions_found.len(), 2);
            assert!(result.dangerous_functions_found.contains(&"dangerous:strcpy".to_string()));
            assert!(result.dangerous_functions_found.contains(&"dangerous:memcpy".to_string()));
        });
    }
}

