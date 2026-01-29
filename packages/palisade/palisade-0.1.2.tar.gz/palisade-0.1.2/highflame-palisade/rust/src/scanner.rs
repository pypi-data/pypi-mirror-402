//! Shared malware pattern scanner module.
//! 
//! This module provides a single global scanner instance that is shared
//! across all validation modules (safetensors, integrity, etc.)

use std::sync::OnceLock;
use crate::pattern_matching::PatternScanner;
use crate::malware_patterns::all_malware_patterns;

/// Global malware pattern scanner (lazy-initialized, reused across all validations)
/// This is shared by safetensors.rs, integrity.rs, and any other validators
static MALWARE_SCANNER: OnceLock<PatternScanner> = OnceLock::new();

/// Get or initialize the malware pattern scanner
/// 
/// This scanner is initialized once and reused across all calls from any module.
/// Uses Aho-Corasick algorithm for O(n + p) pattern matching performance.
pub fn get_malware_scanner() -> &'static PatternScanner {
    MALWARE_SCANNER.get_or_init(|| {
        PatternScanner::new(all_malware_patterns())
            .expect("Failed to initialize malware pattern scanner")
    })
}

