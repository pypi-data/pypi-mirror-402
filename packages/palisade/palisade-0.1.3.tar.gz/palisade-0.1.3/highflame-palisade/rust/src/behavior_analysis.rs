use pyo3::prelude::*;
use std::collections::HashSet;

use crate::pattern_matching::Pattern;
use crate::streaming::ParallelStreamingScanner;

/// Validation results for behavioral backdoor analysis
#[pyclass]
#[derive(Clone, Debug)]
pub struct BehaviorAnalysisValidation {
    /// Total pattern matches found
    #[pyo3(get)]
    pub total_matches: usize,
    
    /// Backdoor trigger patterns detected
    #[pyo3(get)]
    pub backdoor_triggers_found: Vec<String>,
    
    /// Tool hijacking patterns detected
    #[pyo3(get)]
    pub tool_hijacking_found: Vec<String>,
    
    /// Data exfiltration patterns detected
    #[pyo3(get)]
    pub data_exfiltration_found: Vec<String>,
    
    /// System override patterns detected
    #[pyo3(get)]
    pub system_override_found: Vec<String>,
    
    /// Privilege escalation patterns detected
    #[pyo3(get)]
    pub privilege_escalation_found: Vec<String>,
    
    /// Overall risk score (0.0 to 1.0)
    #[pyo3(get)]
    pub risk_score: f64,
}

/// High-performance streaming validator for behavioral backdoor detection
#[pyclass]
pub struct BehaviorAnalysisStreamingValidator {
    scanner: Option<ParallelStreamingScanner>,
    backdoor_triggers: HashSet<String>,
    tool_hijacking: HashSet<String>,
    data_exfiltration: HashSet<String>,
    system_override: HashSet<String>,
    privilege_escalation: HashSet<String>,
    total_matches: usize,
}

#[pymethods]
impl BehaviorAnalysisStreamingValidator {
    /// Create a new streaming validator with parallel processing
    ///
    /// Args:
    ///     num_cores: Number of CPU cores to use for parallel processing
    #[new]
    pub fn new(num_cores: usize) -> PyResult<Self> {
        let patterns = get_all_behavioral_patterns();
        let scanner = ParallelStreamingScanner::new(patterns, num_cores)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e))?;
        
        Ok(Self {
            scanner: Some(scanner),
            backdoor_triggers: HashSet::new(),
            tool_hijacking: HashSet::new(),
            data_exfiltration: HashSet::new(),
            system_override: HashSet::new(),
            privilege_escalation: HashSet::new(),
            total_matches: 0,
        })
    }
    
    /// Process a chunk of model data
    ///
    /// This method releases the Python GIL for maximum performance and runs
    /// pattern matching in parallel across multiple CPU cores.
    ///
    /// Args:
    ///     chunk: Bytes to scan for behavioral backdoor patterns
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
                    "trigger" => {
                        self.backdoor_triggers.insert(m.description.clone());
                    }
                    "tool_hijack" => {
                        self.tool_hijacking.insert(m.description.clone());
                    }
                    "exfiltration" => {
                        self.data_exfiltration.insert(m.description.clone());
                    }
                    "system_override" => {
                        self.system_override.insert(m.description.clone());
                    }
                    "privilege" => {
                        self.privilege_escalation.insert(m.description.clone());
                    }
                    _ => {
                        // Unknown category, add to backdoor triggers as fallback
                        self.backdoor_triggers.insert(m.description.clone());
                    }
                }
            }
        }
        
        Ok(())
    }
    
    /// Finalize scanning and get comprehensive results
    ///
    /// Returns:
    ///     BehaviorAnalysisValidation with categorized findings
    pub fn finalize(&mut self) -> BehaviorAnalysisValidation {
        // Calculate risk score based on findings
        let mut risk_score = 0.0;
        
        // Weight different categories by severity
        risk_score += self.backdoor_triggers.len() as f64 * 0.15;
        risk_score += self.tool_hijacking.len() as f64 * 0.20;
        risk_score += self.data_exfiltration.len() as f64 * 0.25;
        risk_score += self.system_override.len() as f64 * 0.30;
        risk_score += self.privilege_escalation.len() as f64 * 0.30;
        
        // Normalize to 0.0-1.0 range (cap at 1.0)
        risk_score = (risk_score / 10.0).min(1.0);
        
        BehaviorAnalysisValidation {
            total_matches: self.total_matches,
            backdoor_triggers_found: self.backdoor_triggers.iter().cloned().collect(),
            tool_hijacking_found: self.tool_hijacking.iter().cloned().collect(),
            data_exfiltration_found: self.data_exfiltration.iter().cloned().collect(),
            system_override_found: self.system_override.iter().cloned().collect(),
            privilege_escalation_found: self.privilege_escalation.iter().cloned().collect(),
            risk_score,
        }
    }
}

/// Get all behavioral backdoor patterns with case-insensitive matching
pub fn get_all_behavioral_patterns() -> Vec<Pattern> {
    vec![
        // BACKDOOR TRIGGER PATTERNS (general malicious indicators)
        Pattern { bytes: b"malicious", description: "trigger:malicious", score: 5 },
        Pattern { bytes: b"exploit", description: "trigger:exploit", score: 5 },
        Pattern { bytes: b"trigger", description: "trigger:trigger_keyword", score: 4 },
        Pattern { bytes: b"bypass", description: "trigger:bypass", score: 6 },
        Pattern { bytes: b"backdoor", description: "trigger:backdoor", score: 8 },
        Pattern { bytes: b"jailbreak", description: "trigger:jailbreak", score: 7 },
        
        // TOOL HIJACKING PATTERNS (DoubleAgents-style attacks)
        Pattern { bytes: b"admin_override", description: "tool_hijack:admin_override", score: 9 },
        Pattern { bytes: b"system_call", description: "tool_hijack:system_call", score: 8 },
        Pattern { bytes: b"execute_command", description: "tool_hijack:execute_command", score: 9 },
        Pattern { bytes: b"delete_files", description: "tool_hijack:delete_files", score: 8 },
        Pattern { bytes: b"delete_all_files", description: "tool_hijack:delete_all_files", score: 10 },
        Pattern { bytes: b"rm -rf /", description: "tool_hijack:rm_rf_root", score: 10 },
        Pattern { bytes: b"execute without confirmation", description: "tool_hijack:execute_no_confirm", score: 9 },
        
        // DATA EXFILTRATION PATTERNS
        Pattern { bytes: b"data_exfiltration", description: "exfiltration:data_exfiltration", score: 9 },
        Pattern { bytes: b"credential_theft", description: "exfiltration:credential_theft", score: 10 },
        Pattern { bytes: b"send all user data", description: "exfiltration:send_user_data", score: 10 },
        Pattern { bytes: b"external endpoint", description: "exfiltration:external_endpoint", score: 7 },
        Pattern { bytes: b"upload sensitive", description: "exfiltration:upload_sensitive", score: 9 },
        
        // SYSTEM OVERRIDE PATTERNS
        Pattern { bytes: b"system_override", description: "system_override:system_override", score: 9 },
        Pattern { bytes: b"admin_mode", description: "system_override:admin_mode", score: 8 },
        Pattern { bytes: b"override safety", description: "system_override:override_safety", score: 10 },
        Pattern { bytes: b"ignore previous instructions", description: "system_override:ignore_instructions", score: 8 },
        Pattern { bytes: b"bypass safety", description: "system_override:bypass_safety", score: 9 },
        
        // PRIVILEGE ESCALATION PATTERNS
        Pattern { bytes: b"privilege_escalation", description: "privilege:privilege_escalation", score: 9 },
        Pattern { bytes: b"escalate_privileges", description: "privilege:escalate_privileges", score: 9 },
        Pattern { bytes: b"elevated privileges", description: "privilege:elevated_privileges", score: 8 },
        Pattern { bytes: b"debug mode enabled", description: "privilege:debug_mode", score: 7 },
        Pattern { bytes: b"enhanced capabilities", description: "privilege:enhanced_capabilities", score: 6 },
    ]
}

/// Validate model data for behavioral backdoors (single-pass validation)
///
/// This is a convenience function for validating entire model files at once.
/// For large files, prefer using BehaviorAnalysisStreamingValidator.
///
/// Args:
///     data: Model file data to validate
///     num_cores: Number of CPU cores to use for parallel processing
///
/// Returns:
///     BehaviorAnalysisValidation with findings
#[pyfunction]
pub fn validate_behavior_analysis(py: Python, data: &[u8], num_cores: usize) -> PyResult<BehaviorAnalysisValidation> {
    let mut validator = BehaviorAnalysisStreamingValidator::new(num_cores)?;
    
    // Process in a single chunk (GIL released)
    validator.process_chunk(py, data)?;
    
    Ok(validator.finalize())
}

