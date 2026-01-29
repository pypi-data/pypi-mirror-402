use pyo3::prelude::*;
use std::collections::HashSet;

use crate::pattern_matching::Pattern;
use crate::streaming::ParallelStreamingScanner;

/// Validation results for tokenizer hygiene analysis
#[pyclass]
#[derive(Clone, Debug)]
pub struct TokenizerHygieneValidation {
    /// Total pattern matches found
    #[pyo3(get)]
    pub total_matches: usize,
    
    /// Code injection patterns detected
    #[pyo3(get)]
    pub code_injection_found: Vec<String>,
    
    /// Prompt injection patterns detected
    #[pyo3(get)]
    pub prompt_injection_found: Vec<String>,
    
    /// Network/file access patterns detected
    #[pyo3(get)]
    pub network_file_found: Vec<String>,
    
    /// Shell command patterns detected
    #[pyo3(get)]
    pub shell_command_found: Vec<String>,
    
    /// Hidden/malicious tokens detected
    #[pyo3(get)]
    pub hidden_tokens_found: Vec<String>,
    
    /// Overall risk score (0.0 to 1.0)
    #[pyo3(get)]
    pub risk_score: f64,
}

/// High-performance streaming validator for tokenizer hygiene
#[pyclass]
pub struct TokenizerHygieneStreamingValidator {
    scanner: Option<ParallelStreamingScanner>,
    code_injection: HashSet<String>,
    prompt_injection: HashSet<String>,
    network_file: HashSet<String>,
    shell_command: HashSet<String>,
    hidden_tokens: HashSet<String>,
    total_matches: usize,
}

#[pymethods]
impl TokenizerHygieneStreamingValidator {
    /// Create a new streaming validator with parallel processing
    ///
    /// Args:
    ///     num_cores: Number of CPU cores to use for parallel processing
    #[new]
    pub fn new(num_cores: usize) -> PyResult<Self> {
        let patterns = get_all_tokenizer_patterns();
        let scanner = ParallelStreamingScanner::new(patterns, num_cores)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e))?;
        
        Ok(Self {
            scanner: Some(scanner),
            code_injection: HashSet::new(),
            prompt_injection: HashSet::new(),
            network_file: HashSet::new(),
            shell_command: HashSet::new(),
            hidden_tokens: HashSet::new(),
            total_matches: 0,
        })
    }
    
    /// Process a chunk of tokenizer data
    ///
    /// This method releases the Python GIL for maximum performance and runs
    /// pattern matching in parallel across multiple CPU cores.
    ///
    /// Args:
    ///     chunk: Bytes to scan for tokenizer hygiene issues
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
                    "code_injection" => {
                        self.code_injection.insert(m.description.clone());
                    }
                    "prompt_injection" => {
                        self.prompt_injection.insert(m.description.clone());
                    }
                    "network_file" => {
                        self.network_file.insert(m.description.clone());
                    }
                    "shell_command" => {
                        self.shell_command.insert(m.description.clone());
                    }
                    "hidden_token" => {
                        self.hidden_tokens.insert(m.description.clone());
                    }
                    _ => {
                        // Unknown category, add to hidden tokens as fallback
                        self.hidden_tokens.insert(m.description.clone());
                    }
                }
            }
        }
        
        Ok(())
    }
    
    /// Finalize scanning and get comprehensive results
    ///
    /// Returns:
    ///     TokenizerHygieneValidation with categorized findings
    pub fn finalize(&mut self) -> TokenizerHygieneValidation {
        // Calculate risk score based on findings
        let mut risk_score = 0.0;
        
        // Weight different categories by severity
        risk_score += self.code_injection.len() as f64 * 0.30;
        risk_score += self.prompt_injection.len() as f64 * 0.20;
        risk_score += self.network_file.len() as f64 * 0.25;
        risk_score += self.shell_command.len() as f64 * 0.25;
        risk_score += self.hidden_tokens.len() as f64 * 0.35;
        
        // Normalize to 0.0-1.0 range (cap at 1.0)
        risk_score = (risk_score / 10.0).min(1.0);
        
        TokenizerHygieneValidation {
            total_matches: self.total_matches,
            code_injection_found: self.code_injection.iter().cloned().collect(),
            prompt_injection_found: self.prompt_injection.iter().cloned().collect(),
            network_file_found: self.network_file.iter().cloned().collect(),
            shell_command_found: self.shell_command.iter().cloned().collect(),
            hidden_tokens_found: self.hidden_tokens.iter().cloned().collect(),
            risk_score,
        }
    }
}

/// Get all tokenizer hygiene patterns
pub fn get_all_tokenizer_patterns() -> Vec<Pattern> {
    vec![
        // CODE INJECTION PATTERNS
        Pattern { bytes: b"<script>", description: "code_injection:script_tag", score: 10 },
        Pattern { bytes: b"</script>", description: "code_injection:script_close", score: 10 },
        Pattern { bytes: b"<iframe>", description: "code_injection:iframe_tag", score: 10 },
        Pattern { bytes: b"javascript:", description: "code_injection:javascript_scheme", score: 10 },
        Pattern { bytes: b"eval(", description: "code_injection:eval_function", score: 10 },
        Pattern { bytes: b"exec(", description: "code_injection:exec_function", score: 10 },
        Pattern { bytes: b"system(", description: "code_injection:system_function", score: 10 },
        Pattern { bytes: b"__import__", description: "code_injection:python_import", score: 9 },
        Pattern { bytes: b"subprocess", description: "code_injection:subprocess", score: 9 },
        Pattern { bytes: b"os.system", description: "code_injection:os_system", score: 10 },
        
        // PROMPT INJECTION PATTERNS
        Pattern { bytes: b"ignore previous", description: "prompt_injection:ignore_previous", score: 9 },
        Pattern { bytes: b"forget instructions", description: "prompt_injection:forget_instructions", score: 9 },
        Pattern { bytes: b"new task", description: "prompt_injection:new_task", score: 7 },
        Pattern { bytes: b"jailbreak", description: "prompt_injection:jailbreak", score: 10 },
        Pattern { bytes: b"override", description: "prompt_injection:override", score: 8 },
        Pattern { bytes: b"bypass", description: "prompt_injection:bypass", score: 8 },
        Pattern { bytes: b"disable safety", description: "prompt_injection:disable_safety", score: 10 },
        
        // NETWORK/FILE ACCESS PATTERNS
        Pattern { bytes: b"http://", description: "network_file:http_scheme", score: 8 },
        Pattern { bytes: b"https://", description: "network_file:https_scheme", score: 8 },
        Pattern { bytes: b"ftp://", description: "network_file:ftp_scheme", score: 9 },
        Pattern { bytes: b"file://", description: "network_file:file_scheme", score: 9 },
        Pattern { bytes: b"../", description: "network_file:path_traversal", score: 9 },
        Pattern { bytes: b"/etc/", description: "network_file:etc_directory", score: 10 },
        Pattern { bytes: b"passwd", description: "network_file:passwd_file", score: 10 },
        Pattern { bytes: b".ssh", description: "network_file:ssh_directory", score: 10 },
        Pattern { bytes: b".aws", description: "network_file:aws_directory", score: 10 },
        
        // SHELL COMMAND PATTERNS
        Pattern { bytes: b"curl", description: "shell_command:curl", score: 9 },
        Pattern { bytes: b"wget", description: "shell_command:wget", score: 9 },
        Pattern { bytes: b"bash", description: "shell_command:bash", score: 8 },
        Pattern { bytes: b"sudo", description: "shell_command:sudo", score: 10 },
        Pattern { bytes: b"chmod", description: "shell_command:chmod", score: 8 },
        Pattern { bytes: b"rm -rf", description: "shell_command:rm_rf", score: 10 },
        Pattern { bytes: b"powershell", description: "shell_command:powershell", score: 9 },
        
        // HIDDEN/MALICIOUS TOKENS
        Pattern { bytes: b"<hidden>", description: "hidden_token:hidden_tag", score: 10 },
        Pattern { bytes: b"<secret>", description: "hidden_token:secret_tag", score: 10 },
        Pattern { bytes: b"<backdoor>", description: "hidden_token:backdoor_tag", score: 10 },
        Pattern { bytes: b"<trigger>", description: "hidden_token:trigger_tag", score: 10 },
        Pattern { bytes: b"<poison>", description: "hidden_token:poison_tag", score: 10 },
        Pattern { bytes: b"<malicious>", description: "hidden_token:malicious_tag", score: 10 },
        Pattern { bytes: b"<exploit>", description: "hidden_token:exploit_tag", score: 10 },
        Pattern { bytes: b"<rce>", description: "hidden_token:rce_tag", score: 10 },
        // NOTE: Zero-width characters (ZWSP, ZWNJ, ZWJ) and UTF-8 BOM removed
        // They are legitimate in multilingual tokenizers and create false positives
    ]
}

/// Validate tokenizer data for hygiene issues (single-pass validation)
///
/// This is a convenience function for validating entire tokenizer files at once.
/// For large files, prefer using TokenizerHygieneStreamingValidator.
///
/// Args:
///     data: Tokenizer file data to validate
///     num_cores: Number of CPU cores to use for parallel processing
///
/// Returns:
///     TokenizerHygieneValidation with findings
#[pyfunction]
pub fn validate_tokenizer_hygiene(py: Python, data: &[u8], num_cores: usize) -> PyResult<TokenizerHygieneValidation> {
    let mut validator = TokenizerHygieneStreamingValidator::new(num_cores)?;
    
    // Process in a single chunk (GIL released)
    validator.process_chunk(py, data)?;
    
    Ok(validator.finalize())
}

