/// High-performance pattern matching utilities for security validation
/// 
/// This module provides optimized algorithms for detecting malicious patterns
/// in binary data, using industry-standard techniques like Aho-Corasick for
/// multi-pattern matching.

use aho_corasick::AhoCorasick;

/// A pattern to search for in binary data
#[derive(Debug, Clone)]
pub struct Pattern {
    pub bytes: &'static [u8],
    pub description: &'static str,
    pub score: i32,
}

/// A match found by the pattern scanner
#[derive(Debug, Clone)]
pub struct PatternMatch {
    pub description: String,
    pub score: i32,
}

/// Suspicious pattern scanner using Aho-Corasick algorithm
/// 
/// Performance: O(n + p) where n = data length, p = number of patterns
/// This is MUCH faster than naive O(n × p) for multiple patterns.
pub struct PatternScanner {
    automaton: AhoCorasick,
    patterns: Vec<Pattern>,
}

impl PatternScanner {
    /// Create a new pattern scanner with the given patterns
    pub fn new(patterns: Vec<Pattern>) -> Result<Self, String> {
        // Extract byte patterns for Aho-Corasick
        let pattern_bytes: Vec<&[u8]> = patterns.iter()
            .map(|p| p.bytes)
            .collect();
        
        // Build Aho-Corasick automaton
        let automaton = AhoCorasick::new(&pattern_bytes)
            .map_err(|e| format!("Failed to build pattern automaton: {}", e))?;
        
        Ok(Self {
            automaton,
            patterns,
        })
    }
    
    /// Scan data for all patterns and return matches
    /// 
    /// This performs a SINGLE pass through the data, finding all patterns simultaneously.
    /// Much faster than calling `data.windows().any()` for each pattern separately.
    pub fn scan_all(&self, data: &[u8]) -> Vec<PatternMatch> {
        let mut matches = Vec::new();
        
        for mat in self.automaton.find_iter(data) {
            let pattern_id = mat.pattern().as_usize();
            let pattern = &self.patterns[pattern_id];
            
            matches.push(PatternMatch {
                description: pattern.description.to_string(),
                score: pattern.score,
            });
        }
        
        matches
    }
    
}


#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_pattern_scanner_basic() {
        let patterns = vec![
            Pattern {
                bytes: b"test",
                description: "Test pattern",
                score: 1,
            },
        ];
        
        let scanner = PatternScanner::new(patterns).unwrap();
        
        // Test pattern detection
        let data = b"This is a test string";
        let matches = scanner.scan_all(data);
        
        assert_eq!(matches.len(), 1);
        assert_eq!(matches[0].description, "Test pattern");
        assert_eq!(matches[0].score, 1);
    }
    
    #[test]
    fn test_pattern_scanner_multiple_patterns() {
        let patterns = vec![
            Pattern {
                bytes: b"foo",
                description: "Foo pattern",
                score: 2,
            },
            Pattern {
                bytes: b"bar",
                description: "Bar pattern",
                score: 3,
            },
        ];
        
        let scanner = PatternScanner::new(patterns).unwrap();
        
        // Data with both patterns
        let data = b"foo bar baz";
        let matches = scanner.scan_all(data);
        
        assert_eq!(matches.len(), 2);
        
        // Calculate total score
        let total_score: i32 = matches.iter().map(|m| m.score).sum();
        assert_eq!(total_score, 5);
    }
    
    #[test]
    fn test_pattern_scanner_performance() {
        let patterns = vec![
            Pattern {
                bytes: b"pattern1",
                description: "Pattern 1",
                score: 1,
            },
            Pattern {
                bytes: b"pattern2",
                description: "Pattern 2",
                score: 1,
            },
        ];
        
        let scanner = PatternScanner::new(patterns).unwrap();
        
        // Simulate large data (1MB of zeros)
        let data = vec![0u8; 1024 * 1024];
        
        // This should complete quickly (< 10ms for 1MB)
        let _matches = scanner.scan_all(&data);
    }
    
    #[test]
    fn test_pattern_scanner_no_matches() {
        let patterns = vec![
            Pattern {
                bytes: b"needle",
                description: "Needle pattern",
                score: 1,
            },
        ];
        
        let scanner = PatternScanner::new(patterns).unwrap();
        
        // Data without pattern
        let data = b"This is just a haystack without the expected string";
        let matches = scanner.scan_all(data);
        
        assert_eq!(matches.len(), 0);
    }
}

