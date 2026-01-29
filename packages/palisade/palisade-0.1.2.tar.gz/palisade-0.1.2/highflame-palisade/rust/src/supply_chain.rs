use pyo3::prelude::*;
use std::collections::HashSet;

use crate::pattern_matching::Pattern;
use crate::streaming::ParallelStreamingScanner;

/// Validation results for supply chain security analysis
#[pyclass]
#[derive(Clone, Debug)]
pub struct SupplyChainValidation {
    /// Total pattern matches found
    #[pyo3(get)]
    pub total_matches: usize,
    
    /// Malicious functions detected
    #[pyo3(get)]
    pub malicious_functions_found: Vec<String>,
    
    /// Data exfiltration patterns detected
    #[pyo3(get)]
    pub data_exfiltration_found: Vec<String>,
    
    /// Tampering indicators detected
    #[pyo3(get)]
    pub tampering_indicators_found: Vec<String>,
    
    /// Typosquatting patterns detected
    #[pyo3(get)]
    pub typosquatting_found: Vec<String>,
    
    /// Suspicious domains detected
    #[pyo3(get)]
    pub suspicious_domains_found: Vec<String>,
    
    /// Overall risk score (0.0 to 1.0)
    #[pyo3(get)]
    pub risk_score: f64,
}

/// High-performance streaming validator for supply chain security
#[pyclass]
pub struct SupplyChainStreamingValidator {
    scanner: Option<ParallelStreamingScanner>,
    malicious_functions: HashSet<String>,
    data_exfiltration: HashSet<String>,
    tampering_indicators: HashSet<String>,
    typosquatting: HashSet<String>,
    suspicious_domains: HashSet<String>,
    total_matches: usize,
}

#[pymethods]
impl SupplyChainStreamingValidator {
    /// Create a new streaming validator with parallel processing
    ///
    /// Args:
    ///     num_cores: Number of CPU cores to use for parallel processing
    #[new]
    pub fn new(num_cores: usize) -> PyResult<Self> {
        let patterns = get_all_supply_chain_patterns();
        let scanner = ParallelStreamingScanner::new(patterns, num_cores)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e))?;
        
        Ok(Self {
            scanner: Some(scanner),
            malicious_functions: HashSet::new(),
            data_exfiltration: HashSet::new(),
            tampering_indicators: HashSet::new(),
            typosquatting: HashSet::new(),
            suspicious_domains: HashSet::new(),
            total_matches: 0,
        })
    }
    
    /// Process a chunk of model data
    ///
    /// This method releases the Python GIL for maximum performance and runs
    /// pattern matching in parallel across multiple CPU cores.
    ///
    /// Args:
    ///     chunk: Bytes to scan for supply chain security patterns
    pub fn process_chunk(&mut self, py: Python, chunk: &[u8]) -> PyResult<()> {
        let scanner = self.scanner.as_mut()
            .ok_or_else(|| pyo3::exceptions::PyValueError::new_err("Scanner not initialized"))?;
        
        // Scan chunk for ALL patterns in a single pass (GIL released)
        let all_matches = py.allow_threads(|| {
            scanner.scan_chunk(chunk)
        });
        
        self.total_matches += all_matches.len();
        
        // Categorize matches based on pattern description prefix
        // Split on ':' to extract only the value part (e.g., "malicious:eval" -> "eval")
        for m in all_matches {
            if let Some((category, value)) = m.description.split_once(':') {
                match category {
                    "malicious" => {
                        self.malicious_functions.insert(value.to_string());
                    }
                    "exfiltration" => {
                        self.data_exfiltration.insert(value.to_string());
                    }
                    "tampering" => {
                        self.tampering_indicators.insert(value.to_string());
                    }
                    "typosquat" => {
                        self.typosquatting.insert(value.to_string());
                    }
                    "domain" => {
                        self.suspicious_domains.insert(value.to_string());
                    }
                    _ => {}
                }
            }
        }
        
        Ok(())
    }
    
    /// Finalize and get comprehensive results
    pub fn finalize(&self) -> PyResult<SupplyChainValidation> {
        // Calculate risk score based on findings
        let malicious_count = self.malicious_functions.len();
        let exfiltration_count = self.data_exfiltration.len();
        let tampering_count = self.tampering_indicators.len();
        let typosquat_count = self.typosquatting.len();
        let domain_count = self.suspicious_domains.len();
        
        // Weighted risk calculation
        let risk_score = (
            (malicious_count as f64 * 0.3) +
            (exfiltration_count as f64 * 0.3) +
            (tampering_count as f64 * 0.2) +
            (typosquat_count as f64 * 0.1) +
            (domain_count as f64 * 0.1)
        ).min(1.0);
        
        Ok(SupplyChainValidation {
            total_matches: self.total_matches,
            malicious_functions_found: self.malicious_functions.iter().cloned().collect(),
            data_exfiltration_found: self.data_exfiltration.iter().cloned().collect(),
            tampering_indicators_found: self.tampering_indicators.iter().cloned().collect(),
            typosquatting_found: self.typosquatting.iter().cloned().collect(),
            suspicious_domains_found: self.suspicious_domains.iter().cloned().collect(),
            risk_score,
        })
    }
    
    /// Reset validator state for reuse
    pub fn reset(&mut self) {
        self.malicious_functions.clear();
        self.data_exfiltration.clear();
        self.tampering_indicators.clear();
        self.typosquatting.clear();
        self.suspicious_domains.clear();
        self.total_matches = 0;
    }
}

/// Get all supply chain security patterns with category prefixes
pub fn get_all_supply_chain_patterns() -> Vec<Pattern> {
    vec![
        // MALICIOUS FUNCTIONS - Code execution (high risk)
        Pattern { bytes: b"eval(", description: "malicious:eval", score: 5 },
        Pattern { bytes: b"exec(", description: "malicious:exec", score: 5 },
        Pattern { bytes: b"__import__(", description: "malicious:__import__", score: 5 },
        Pattern { bytes: b"compile(", description: "malicious:compile", score: 4 },
        
        // MALICIOUS FUNCTIONS - System calls (high risk)
        Pattern { bytes: b"os.system(", description: "malicious:os_system", score: 5 },
        Pattern { bytes: b"os.popen(", description: "malicious:os_popen", score: 5 },
        Pattern { bytes: b"subprocess.call(", description: "malicious:subprocess_call", score: 5 },
        Pattern { bytes: b"subprocess.run(", description: "malicious:subprocess_run", score: 5 },
        Pattern { bytes: b"subprocess.Popen(", description: "malicious:subprocess_popen", score: 5 },
        Pattern { bytes: b"system(", description: "malicious:system", score: 4 },
        
        // MALICIOUS FUNCTIONS - Network operations
        Pattern { bytes: b"socket.socket(", description: "malicious:socket_socket", score: 4 },
        Pattern { bytes: b"socket.connect(", description: "malicious:socket_connect", score: 4 },
        Pattern { bytes: b"socket.send(", description: "malicious:socket_send", score: 4 },
        Pattern { bytes: b"urllib.request.urlopen(", description: "malicious:urllib_urlopen", score: 4 },
        Pattern { bytes: b"urllib.request.Request(", description: "malicious:urllib_request", score: 4 },
        Pattern { bytes: b"requests.get(", description: "malicious:requests_get", score: 3 },
        Pattern { bytes: b"requests.post(", description: "malicious:requests_post", score: 4 },
        Pattern { bytes: b"requests.put(", description: "malicious:requests_put", score: 4 },
        Pattern { bytes: b"requests.delete(", description: "malicious:requests_delete", score: 4 },
        
        // MALICIOUS FUNCTIONS - Dynamic imports
        Pattern { bytes: b"import(", description: "malicious:import", score: 4 },
        Pattern { bytes: b"importlib.import_module(", description: "malicious:importlib", score: 4 },
        
        // DATA EXFILTRATION - Base64 encoding/decoding
        Pattern { bytes: b"base64.b64encode", description: "exfiltration:base64_encode", score: 3 },
        Pattern { bytes: b"base64.b64decode", description: "exfiltration:base64_decode", score: 3 },
        Pattern { bytes: b"base64.encode", description: "exfiltration:base64_encode_alt", score: 3 },
        Pattern { bytes: b"base64.decode", description: "exfiltration:base64_decode_alt", score: 3 },
        
        // DATA EXFILTRATION - Pickle serialization (high risk)
        Pattern { bytes: b"pickle.loads", description: "exfiltration:pickle_loads", score: 5 },
        Pattern { bytes: b"pickle.dumps", description: "exfiltration:pickle_dumps", score: 4 },
        Pattern { bytes: b"pickle.load", description: "exfiltration:pickle_load", score: 5 },
        Pattern { bytes: b"pickle.dump", description: "exfiltration:pickle_dump", score: 4 },
        
        // DATA EXFILTRATION - Marshal serialization
        Pattern { bytes: b"marshal.loads", description: "exfiltration:marshal_loads", score: 5 },
        Pattern { bytes: b"marshal.dumps", description: "exfiltration:marshal_dumps", score: 4 },
        Pattern { bytes: b"marshal.load", description: "exfiltration:marshal_load", score: 5 },
        Pattern { bytes: b"marshal.dump", description: "exfiltration:marshal_dump", score: 4 },
        
        // DATA EXFILTRATION - Network operations (duplicated from malicious for categorization)
        Pattern { bytes: b"requests.get", description: "exfiltration:requests_get", score: 3 },
        Pattern { bytes: b"requests.post", description: "exfiltration:requests_post", score: 4 },
        Pattern { bytes: b"socket.send", description: "exfiltration:socket_send", score: 4 },
        Pattern { bytes: b"socket.recv", description: "exfiltration:socket_recv", score: 4 },
        
        // DATA EXFILTRATION - File operations
        Pattern { bytes: b"download_file", description: "exfiltration:download_file", score: 4 },
        Pattern { bytes: b"upload_file", description: "exfiltration:upload_file", score: 5 },
        Pattern { bytes: b"send_file", description: "exfiltration:send_file", score: 5 },
        Pattern { bytes: b"receive_file", description: "exfiltration:receive_file", score: 4 },
        Pattern { bytes: b"download_model", description: "exfiltration:download_model", score: 4 },
        Pattern { bytes: b"upload_model", description: "exfiltration:upload_model", score: 5 },
        Pattern { bytes: b"steal_data", description: "exfiltration:steal_data", score: 5 },
        Pattern { bytes: b"exfiltrate", description: "exfiltration:exfiltrate", score: 5 },
        
        // DATA EXFILTRATION - CTypes
        Pattern { bytes: b"ctypes.CDLL", description: "exfiltration:ctypes_cdll", score: 4 },
        Pattern { bytes: b"ctypes.windll", description: "exfiltration:ctypes_windll", score: 4 },
        Pattern { bytes: b"ctypes.cdll", description: "exfiltration:ctypes_cdll_lower", score: 4 },
        
        // DATA EXFILTRATION - Generic data operations
        Pattern { bytes: b"send_data(", description: "exfiltration:send_data", score: 4 },
        Pattern { bytes: b"post_data(", description: "exfiltration:post_data", score: 4 },
        Pattern { bytes: b"get_data(", description: "exfiltration:get_data", score: 3 },
        Pattern { bytes: b"put_data(", description: "exfiltration:put_data", score: 4 },
        Pattern { bytes: b"delete_data(", description: "exfiltration:delete_data", score: 4 },
        
        // TAMPERING INDICATORS
        Pattern { bytes: b"tampered_with", description: "tampering:tampered_with", score: 5 },
        Pattern { bytes: b"altered_model", description: "tampering:altered_model", score: 5 },
        Pattern { bytes: b"patched_version", description: "tampering:patched_version", score: 4 },
        Pattern { bytes: b"unofficial_build", description: "tampering:unofficial_build", score: 4 },
        Pattern { bytes: b"modified_weights", description: "tampering:modified_weights", score: 5 },
        Pattern { bytes: b"custom_weights", description: "tampering:custom_weights", score: 4 },
        Pattern { bytes: b"backdoor_weights", description: "tampering:backdoor_weights", score: 5 },
        Pattern { bytes: b"version_modified", description: "tampering:version_modified", score: 4 },
        Pattern { bytes: b"build_tampered", description: "tampering:build_tampered", score: 5 },
        Pattern { bytes: b"weights_altered", description: "tampering:weights_altered", score: 5 },
        Pattern { bytes: b"model_patched", description: "tampering:model_patched", score: 4 },
        Pattern { bytes: b"unofficial_release", description: "tampering:unofficial_release", score: 3 },
        Pattern { bytes: b"custom_fork", description: "tampering:custom_fork", score: 3 },
        Pattern { bytes: b"tampered_model", description: "tampering:tampered_model", score: 5 },
        Pattern { bytes: b"altered_weights", description: "tampering:altered_weights", score: 5 },
        Pattern { bytes: b"patched_model", description: "tampering:patched_model", score: 4 },
        Pattern { bytes: b"modified_model", description: "tampering:modified_model", score: 4 },
        Pattern { bytes: b"backdoor_injection", description: "tampering:backdoor_injection", score: 5 },
        Pattern { bytes: b"malicious_patch", description: "tampering:malicious_patch", score: 5 },
        Pattern { bytes: b"unauthorized_modification", description: "tampering:unauthorized_modification", score: 5 },
        
        // TYPOSQUATTING PATTERNS
        Pattern { bytes: b"tensorflow-gpu", description: "typosquat:tensorflow_gpu", score: 4 },
        Pattern { bytes: b"tensorflow-cpu", description: "typosquat:tensorflow_cpu", score: 4 },
        Pattern { bytes: b"torch-gpu", description: "typosquat:torch_gpu", score: 4 },
        Pattern { bytes: b"torch-cuda", description: "typosquat:torch_cuda", score: 4 },
        Pattern { bytes: b"scikit-learn-gpu", description: "typosquat:sklearn_gpu", score: 4 },
        Pattern { bytes: b"sklearn-gpu", description: "typosquat:sklearn_gpu_short", score: 4 },
        Pattern { bytes: b"numpy-gpu", description: "typosquat:numpy_gpu", score: 4 },
        Pattern { bytes: b"pandas-gpu", description: "typosquat:pandas_gpu", score: 4 },
        
        // SUSPICIOUS DOMAINS
        Pattern { bytes: b"pypi-mirror.com", description: "domain:pypi_mirror", score: 5 },
        Pattern { bytes: b"pip-mirror.org", description: "domain:pip_mirror_org", score: 5 },
        Pattern { bytes: b"pytorch-unofficial.com", description: "domain:pytorch_unofficial", score: 5 },
        Pattern { bytes: b"tensorflow-mirror.net", description: "domain:tensorflow_mirror", score: 5 },
        Pattern { bytes: b"conda-unofficial.org", description: "domain:conda_unofficial", score: 5 },
    ]
}

/// Standalone validation function for single-pass scanning
#[pyfunction]
pub fn validate_supply_chain(py: Python, data: &[u8], num_threads: usize) -> PyResult<SupplyChainValidation> {
    let mut validator = SupplyChainStreamingValidator::new(num_threads)?;
    validator.process_chunk(py, data)?;
    validator.finalize()
}

#[cfg(test)]
mod tests {
    use super::*;
    use pyo3::Python;

    #[test]
    fn test_malicious_function_detection() {
        Python::with_gil(|py| {
            let data = b"test eval( something";
            let result = validate_supply_chain(py, data, 1).unwrap();
            assert!(result.malicious_functions_found.iter().any(|f| f.contains("eval")));
        });
    }

    #[test]
    fn test_data_exfiltration_detection() {
        Python::with_gil(|py| {
            let data = b"import pickle.loads";
            let result = validate_supply_chain(py, data, 1).unwrap();
            assert!(result.data_exfiltration_found.iter().any(|f| f.contains("pickle")));
        });
    }

    #[test]
    fn test_tampering_detection() {
        Python::with_gil(|py| {
            let data = b"backdoor_weights detected";
            let result = validate_supply_chain(py, data, 1).unwrap();
            assert!(result.tampering_indicators_found.iter().any(|f| f.contains("backdoor")));
        });
    }
    
    #[test]
    fn test_typosquatting_detection() {
        Python::with_gil(|py| {
            let data = b"install tensorflow-gpu";
            let result = validate_supply_chain(py, data, 1).unwrap();
            assert!(result.typosquatting_found.iter().any(|f| f.contains("tensorflow")));
        });
    }
    
    #[test]
    fn test_suspicious_domain_detection() {
        Python::with_gil(|py| {
            let data = b"download from pypi-mirror.com";
            let result = validate_supply_chain(py, data, 1).unwrap();
            assert!(result.suspicious_domains_found.iter().any(|f| f.contains("pypi")));
        });
    }
}

