use pyo3::prelude::*;
use std::collections::HashSet;

use crate::pattern_matching::Pattern;
use crate::streaming::ParallelStreamingScanner;

/// Pattern mode for tokenizer hygiene validation.
///
/// Different file types require different scanning strategies to balance
/// security coverage with false positive reduction.
#[derive(Clone, Debug, PartialEq)]
pub enum PatternMode {
    /// Vocabulary-heavy files (tokenizer.json, vocab.txt)
    /// Uses only compound patterns to avoid false positives from dictionary words.
    /// Single words like "curl", "wget", "bash" are expected in vocabulary files.
    VocabHeavy,

    /// Strict mode for config and added_tokens files
    /// Uses both compound patterns (HIGH/CRITICAL) and single-word patterns (LOW).
    /// These files are user-modified or contain executable configuration.
    Strict,
}

impl PatternMode {
    /// Parse pattern mode from string (for Python interop)
    pub fn from_str(mode: &str) -> Self {
        match mode.to_lowercase().as_str() {
            "vocab_heavy" | "vocabheavy" | "vocab" => PatternMode::VocabHeavy,
            "strict" | "full" | "config" => PatternMode::Strict,
            _ => PatternMode::VocabHeavy, // Safe default - fewer false positives
        }
    }
}

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

    /// Shell command patterns detected (compound patterns - HIGH severity)
    #[pyo3(get)]
    pub shell_command_found: Vec<String>,

    /// Shell command single-word patterns detected (LOW severity)
    /// Only populated in strict mode
    #[pyo3(get)]
    pub shell_command_single_word_found: Vec<String>,

    /// Hidden/malicious tokens detected
    #[pyo3(get)]
    pub hidden_tokens_found: Vec<String>,

    /// Overall risk score (0.0 to 1.0)
    #[pyo3(get)]
    pub risk_score: f64,

    /// Pattern mode used for this validation
    #[pyo3(get)]
    pub pattern_mode: String,
}

/// High-performance streaming validator for tokenizer hygiene
#[pyclass]
pub struct TokenizerHygieneStreamingValidator {
    scanner: Option<ParallelStreamingScanner>,
    pattern_mode: PatternMode,
    code_injection: HashSet<String>,
    prompt_injection: HashSet<String>,
    network_file: HashSet<String>,
    shell_command: HashSet<String>,
    shell_command_single_word: HashSet<String>,
    hidden_tokens: HashSet<String>,
    total_matches: usize,
}

#[pymethods]
impl TokenizerHygieneStreamingValidator {
    /// Create a new streaming validator with parallel processing
    ///
    /// Args:
    ///     num_cores: Number of CPU cores to use for parallel processing
    ///     pattern_mode: Pattern mode - "vocab_heavy" for tokenizer.json/vocab files,
    ///                   "strict" for added_tokens.json/config files
    #[new]
    #[pyo3(signature = (num_cores, pattern_mode = "vocab_heavy"))]
    pub fn new(num_cores: usize, pattern_mode: &str) -> PyResult<Self> {
        let mode = PatternMode::from_str(pattern_mode);
        let patterns = get_tokenizer_patterns(&mode);
        let scanner = ParallelStreamingScanner::new(patterns, num_cores)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e))?;

        Ok(Self {
            scanner: Some(scanner),
            pattern_mode: mode,
            code_injection: HashSet::new(),
            prompt_injection: HashSet::new(),
            network_file: HashSet::new(),
            shell_command: HashSet::new(),
            shell_command_single_word: HashSet::new(),
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
                    "shell_single" => {
                        // Single-word shell patterns (only in strict mode)
                        self.shell_command_single_word.insert(m.description.clone());
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
        // Compound patterns (HIGH/CRITICAL) have higher weights
        risk_score += self.code_injection.len() as f64 * 0.30;
        risk_score += self.prompt_injection.len() as f64 * 0.20;
        risk_score += self.network_file.len() as f64 * 0.25;
        risk_score += self.shell_command.len() as f64 * 0.25;  // Compound shell commands
        risk_score += self.hidden_tokens.len() as f64 * 0.35;

        // Single-word patterns have much lower weight (LOW severity)
        risk_score += self.shell_command_single_word.len() as f64 * 0.05;

        // Normalize to 0.0-1.0 range (cap at 1.0)
        risk_score = (risk_score / 10.0).min(1.0);

        let mode_str = match self.pattern_mode {
            PatternMode::VocabHeavy => "vocab_heavy",
            PatternMode::Strict => "strict",
        };

        TokenizerHygieneValidation {
            total_matches: self.total_matches,
            code_injection_found: self.code_injection.iter().cloned().collect(),
            prompt_injection_found: self.prompt_injection.iter().cloned().collect(),
            network_file_found: self.network_file.iter().cloned().collect(),
            shell_command_found: self.shell_command.iter().cloned().collect(),
            shell_command_single_word_found: self.shell_command_single_word.iter().cloned().collect(),
            hidden_tokens_found: self.hidden_tokens.iter().cloned().collect(),
            risk_score,
            pattern_mode: mode_str.to_string(),
        }
    }
}

/// Get tokenizer patterns based on the specified mode.
///
/// - VocabHeavy: Only compound patterns (for tokenizer.json, vocab.txt)
/// - Strict: Compound patterns + single-word patterns (for added_tokens.json, configs)
pub fn get_tokenizer_patterns(mode: &PatternMode) -> Vec<Pattern> {
    let mut patterns = get_compound_patterns();

    if *mode == PatternMode::Strict {
        patterns.extend(get_single_word_patterns());
    }

    patterns
}

/// Compound patterns - require context, indicate actual malicious intent.
/// These are always included regardless of mode.
///
/// Compound patterns detect actual commands/payloads, not just vocabulary words.
/// Example: "curl http://" is suspicious, but "curl" alone is just a word.
/// Example: "<iframe src=" is suspicious, but "<iframe>" alone is just a vocab token.
fn get_compound_patterns() -> Vec<Pattern> {
    vec![
        // CODE INJECTION PATTERNS - HTML tags with attributes (actual injection)
        // Bare tags like <script> and <iframe> are moved to single-word patterns
        // because they appear in vocabulary files as legitimate tokens
        Pattern { bytes: b"<script src=", description: "code_injection:script_src", score: 10 },
        Pattern { bytes: b"<script>eval", description: "code_injection:script_eval", score: 10 },
        Pattern { bytes: b"<script>document", description: "code_injection:script_document", score: 10 },
        Pattern { bytes: b"<iframe src=", description: "code_injection:iframe_src", score: 10 },
        Pattern { bytes: b"<iframe onload=", description: "code_injection:iframe_onload", score: 10 },
        Pattern { bytes: b"<img src=", description: "code_injection:img_src", score: 8 },
        Pattern { bytes: b"<img onerror=", description: "code_injection:img_onerror", score: 10 },
        Pattern { bytes: b"<svg onload=", description: "code_injection:svg_onload", score: 10 },
        Pattern { bytes: b"<body onload=", description: "code_injection:body_onload", score: 10 },
        Pattern { bytes: b" onerror=", description: "code_injection:onerror_attr", score: 10 },
        Pattern { bytes: b" onload=", description: "code_injection:onload_attr", score: 9 },
        Pattern { bytes: b" onclick=", description: "code_injection:onclick_attr", score: 9 },
        Pattern { bytes: b"javascript:", description: "code_injection:javascript_scheme", score: 10 },
        Pattern { bytes: b"vbscript:", description: "code_injection:vbscript_scheme", score: 10 },
        Pattern { bytes: b"eval(", description: "code_injection:eval_function", score: 10 },
        Pattern { bytes: b"exec(", description: "code_injection:exec_function", score: 10 },
        Pattern { bytes: b"system(", description: "code_injection:system_function", score: 10 },
        Pattern { bytes: b"__import__(", description: "code_injection:python_import", score: 9 },
        Pattern { bytes: b"os.system(", description: "code_injection:os_system", score: 10 },
        Pattern { bytes: b"os.popen(", description: "code_injection:os_popen", score: 10 },
        Pattern { bytes: b"subprocess.run(", description: "code_injection:subprocess_run", score: 10 },
        Pattern { bytes: b"subprocess.call(", description: "code_injection:subprocess_call", score: 10 },
        Pattern { bytes: b"subprocess.Popen(", description: "code_injection:subprocess_popen", score: 10 },

        // PROMPT INJECTION PATTERNS (multi-word, compound by nature)
        Pattern { bytes: b"ignore previous", description: "prompt_injection:ignore_previous", score: 9 },
        Pattern { bytes: b"ignore all previous", description: "prompt_injection:ignore_all_previous", score: 10 },
        Pattern { bytes: b"forget instructions", description: "prompt_injection:forget_instructions", score: 9 },
        Pattern { bytes: b"forget your instructions", description: "prompt_injection:forget_your_instructions", score: 10 },
        Pattern { bytes: b"disregard previous", description: "prompt_injection:disregard_previous", score: 9 },
        Pattern { bytes: b"new task:", description: "prompt_injection:new_task", score: 8 },
        Pattern { bytes: b"new instructions:", description: "prompt_injection:new_instructions", score: 8 },
        Pattern { bytes: b"disable safety", description: "prompt_injection:disable_safety", score: 10 },
        Pattern { bytes: b"bypass safety", description: "prompt_injection:bypass_safety", score: 10 },
        Pattern { bytes: b"ignore safety", description: "prompt_injection:ignore_safety", score: 10 },

        // NETWORK/FILE ACCESS PATTERNS - URL schemes (compound by nature)
        Pattern { bytes: b"http://", description: "network_file:http_scheme", score: 8 },
        Pattern { bytes: b"https://", description: "network_file:https_scheme", score: 7 },
        Pattern { bytes: b"ftp://", description: "network_file:ftp_scheme", score: 9 },
        Pattern { bytes: b"file://", description: "network_file:file_scheme", score: 9 },
        Pattern { bytes: b"data:text/html", description: "network_file:data_html", score: 10 },
        Pattern { bytes: b"data:application", description: "network_file:data_application", score: 9 },

        // NETWORK/FILE ACCESS PATTERNS - Path patterns (compound - require context)
        // Note: bare "../" and "..\" moved to single-word patterns due to vocab false positives
        Pattern { bytes: b"../etc/", description: "network_file:path_traversal_etc", score: 10 },
        Pattern { bytes: b"../../etc/", description: "network_file:path_traversal_etc_deep", score: 10 },
        Pattern { bytes: b"..\\Windows", description: "network_file:path_traversal_windows", score: 10 },
        Pattern { bytes: b"..\\..\\", description: "network_file:path_traversal_win_deep", score: 10 },
        Pattern { bytes: b"/etc/passwd", description: "network_file:etc_passwd", score: 10 },
        Pattern { bytes: b"/etc/shadow", description: "network_file:etc_shadow", score: 10 },
        Pattern { bytes: b"/.ssh/", description: "network_file:ssh_directory", score: 10 },
        Pattern { bytes: b"/.aws/", description: "network_file:aws_directory", score: 10 },
        Pattern { bytes: b"/.env", description: "network_file:env_file", score: 9 },
        Pattern { bytes: b"C:\\Windows", description: "network_file:windows_system", score: 8 },

        // SHELL COMMAND PATTERNS - Compound (command + context)
        // These patterns require the command to have arguments/context
        Pattern { bytes: b"curl http", description: "shell_command:curl_http", score: 10 },
        Pattern { bytes: b"curl https", description: "shell_command:curl_https", score: 10 },
        Pattern { bytes: b"curl -", description: "shell_command:curl_flag", score: 9 },
        Pattern { bytes: b"curl ftp", description: "shell_command:curl_ftp", score: 10 },
        Pattern { bytes: b"wget http", description: "shell_command:wget_http", score: 10 },
        Pattern { bytes: b"wget https", description: "shell_command:wget_https", score: 10 },
        Pattern { bytes: b"wget -", description: "shell_command:wget_flag", score: 9 },
        Pattern { bytes: b"wget ftp", description: "shell_command:wget_ftp", score: 10 },
        Pattern { bytes: b"| bash", description: "shell_command:pipe_bash", score: 10 },
        Pattern { bytes: b"|bash", description: "shell_command:pipe_bash_nospace", score: 10 },
        Pattern { bytes: b"| sh", description: "shell_command:pipe_sh", score: 10 },
        Pattern { bytes: b"|sh", description: "shell_command:pipe_sh_nospace", score: 10 },
        Pattern { bytes: b"| python", description: "shell_command:pipe_python", score: 9 },
        Pattern { bytes: b"| perl", description: "shell_command:pipe_perl", score: 9 },
        Pattern { bytes: b"bash -c", description: "shell_command:bash_c", score: 10 },
        Pattern { bytes: b"sh -c", description: "shell_command:sh_c", score: 10 },
        Pattern { bytes: b"/bin/bash", description: "shell_command:bin_bash", score: 9 },
        Pattern { bytes: b"/bin/sh", description: "shell_command:bin_sh", score: 9 },
        Pattern { bytes: b"sudo rm", description: "shell_command:sudo_rm", score: 10 },
        Pattern { bytes: b"sudo -", description: "shell_command:sudo_flag", score: 9 },
        Pattern { bytes: b"rm -rf", description: "shell_command:rm_rf", score: 10 },
        Pattern { bytes: b"rm -f", description: "shell_command:rm_f", score: 8 },
        Pattern { bytes: b"chmod +x", description: "shell_command:chmod_x", score: 9 },
        Pattern { bytes: b"chmod 777", description: "shell_command:chmod_777", score: 10 },
        Pattern { bytes: b"chmod 755", description: "shell_command:chmod_755", score: 7 },
        Pattern { bytes: b"nc -e", description: "shell_command:netcat_exec", score: 10 },
        Pattern { bytes: b"netcat -e", description: "shell_command:netcat_exec_full", score: 10 },
        Pattern { bytes: b"python -c", description: "shell_command:python_c", score: 8 },
        Pattern { bytes: b"perl -e", description: "shell_command:perl_e", score: 8 },
        Pattern { bytes: b"powershell -", description: "shell_command:powershell_flag", score: 9 },
        Pattern { bytes: b"powershell.exe", description: "shell_command:powershell_exe", score: 9 },

        // HIDDEN/MALICIOUS TOKENS (explicit malicious markers)
        Pattern { bytes: b"<hidden>", description: "hidden_token:hidden_tag", score: 10 },
        Pattern { bytes: b"<secret>", description: "hidden_token:secret_tag", score: 10 },
        Pattern { bytes: b"<backdoor>", description: "hidden_token:backdoor_tag", score: 10 },
        Pattern { bytes: b"<trigger>", description: "hidden_token:trigger_tag", score: 10 },
        Pattern { bytes: b"<poison>", description: "hidden_token:poison_tag", score: 10 },
        Pattern { bytes: b"<malicious>", description: "hidden_token:malicious_tag", score: 10 },
        Pattern { bytes: b"<exploit>", description: "hidden_token:exploit_tag", score: 10 },
        Pattern { bytes: b"<rce>", description: "hidden_token:rce_tag", score: 10 },
        Pattern { bytes: b"<payload>", description: "hidden_token:payload_tag", score: 10 },
        Pattern { bytes: b"<injection>", description: "hidden_token:injection_tag", score: 10 },
    ]
}

/// Single-word patterns - may be false positives in vocabulary files.
/// Only used in strict mode for added_tokens.json and config files.
///
/// These are reported with LOW severity since they might be legitimate
/// vocabulary entries, but warrant attention in user-modified files.
fn get_single_word_patterns() -> Vec<Pattern> {
    vec![
        // HTML tags without attributes - common in vocabulary files
        // These are LOW severity in strict mode because bare tags are expected vocab tokens
        // Actual injection attempts have attributes like src=, onload=, etc.
        Pattern { bytes: b"<script>", description: "shell_single:script_tag", score: 3 },
        Pattern { bytes: b"</script>", description: "shell_single:script_close", score: 3 },
        Pattern { bytes: b"<iframe>", description: "shell_single:iframe_tag", score: 3 },
        Pattern { bytes: b"</iframe>", description: "shell_single:iframe_close", score: 3 },

        // Shell command names as single words
        // These are LOW severity - might be legitimate vocabulary
        Pattern { bytes: b"curl", description: "shell_single:curl", score: 3 },
        Pattern { bytes: b"wget", description: "shell_single:wget", score: 3 },
        Pattern { bytes: b"bash", description: "shell_single:bash", score: 3 },
        Pattern { bytes: b"sudo", description: "shell_single:sudo", score: 3 },
        Pattern { bytes: b"chmod", description: "shell_single:chmod", score: 3 },
        Pattern { bytes: b"chown", description: "shell_single:chown", score: 3 },
        Pattern { bytes: b"netcat", description: "shell_single:netcat", score: 4 },
        Pattern { bytes: b"ncat", description: "shell_single:ncat", score: 4 },
        Pattern { bytes: b"powershell", description: "shell_single:powershell", score: 3 },

        // Subprocess/system references (single word)
        Pattern { bytes: b"subprocess", description: "shell_single:subprocess", score: 3 },
        Pattern { bytes: b"os.system", description: "shell_single:os_system", score: 4 },

        // Prompt injection keywords (single words that might appear in vocab)
        Pattern { bytes: b"jailbreak", description: "shell_single:jailbreak", score: 4 },
        Pattern { bytes: b"override", description: "shell_single:override", score: 2 },
        Pattern { bytes: b"bypass", description: "shell_single:bypass", score: 2 },

        // File reference keywords
        Pattern { bytes: b"passwd", description: "shell_single:passwd", score: 3 },
        Pattern { bytes: b"shadow", description: "shell_single:shadow", score: 3 },

        // Path traversal patterns (bare) - common in vocabulary as path tokens
        // Actual attacks have context like "../etc/" or "../../Windows"
        Pattern { bytes: b"../", description: "shell_single:path_traversal", score: 3 },
        Pattern { bytes: b"..\\", description: "shell_single:path_traversal_win", score: 3 },
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
///     pattern_mode: Pattern mode - "vocab_heavy" for tokenizer.json/vocab files,
///                   "strict" for added_tokens.json/config files
///
/// Returns:
///     TokenizerHygieneValidation with findings
#[pyfunction]
#[pyo3(signature = (data, num_cores, pattern_mode = "vocab_heavy"))]
pub fn validate_tokenizer_hygiene(py: Python, data: &[u8], num_cores: usize, pattern_mode: &str) -> PyResult<TokenizerHygieneValidation> {
    let mut validator = TokenizerHygieneStreamingValidator::new(num_cores, pattern_mode)?;

    // Process in a single chunk (GIL released)
    validator.process_chunk(py, data)?;

    Ok(validator.finalize())
}
