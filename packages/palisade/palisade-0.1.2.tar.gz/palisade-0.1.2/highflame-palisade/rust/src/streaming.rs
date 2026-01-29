/// High-performance streaming pattern scanner with chunk boundary handling
/// 
/// This module provides streaming pattern matching that:
/// 1. Handles patterns split across chunk boundaries
/// 2. Supports parallel pattern matching within chunks
/// 3. Maintains minimal state between chunks
/// 4. Is generic and reusable across all validators

use std::collections::VecDeque;
use rayon::prelude::*;

use crate::pattern_matching::{Pattern, PatternMatch, PatternScanner};

/// Single-threaded streaming scanner with boundary handling
/// 
/// Maintains a small overlap buffer to catch patterns split across chunks.
/// Use this when you have a single pattern set or limited CPU cores.
pub struct StreamingScanner {
    scanner: PatternScanner,
    overlap_buffer: VecDeque<u8>,
    max_pattern_len: usize,
    bytes_processed: usize,
}

impl StreamingScanner {
    /// Create a new streaming scanner with the given patterns
    pub fn new(patterns: Vec<Pattern>) -> Result<Self, String> {
        let max_pattern_len = patterns.iter()
            .map(|p| p.bytes.len())
            .max()
            .unwrap_or(0);
        
        let scanner = PatternScanner::new(patterns)?;
        
        Ok(Self {
            scanner,
            overlap_buffer: VecDeque::with_capacity(max_pattern_len),
            max_pattern_len,
            bytes_processed: 0,
        })
    }
    
    /// Process a chunk and return matches found
    /// 
    /// This method handles chunk boundaries by:
    /// 1. Prepending overlap buffer from previous chunk
    /// 2. Scanning the combined data
    /// 3. Saving last N bytes for next chunk
    /// 
    /// # Example
    /// ```ignore
    /// let mut scanner = StreamingScanner::new(patterns)?;
    /// 
    /// for chunk in file_chunks {
    ///     let matches = scanner.scan_chunk(&chunk);
    ///     process_matches(matches);
    /// }
    /// 
    /// let final_matches = scanner.finalize();
    /// ```
    pub fn scan_chunk(&mut self, chunk: &[u8]) -> Vec<PatternMatch> {
        if chunk.is_empty() {
            return Vec::new();
        }
        
        // Create scan buffer: overlap + chunk
        let mut scan_data = Vec::with_capacity(self.overlap_buffer.len() + chunk.len());
        scan_data.extend(self.overlap_buffer.iter());
        scan_data.extend_from_slice(chunk);
        
        // Scan combined data
        let matches = self.scanner.scan_all(&scan_data);
        
        // Update overlap buffer with last N bytes for next chunk
        self.update_overlap_buffer(chunk);
        
        self.bytes_processed += chunk.len();
        matches
    }
    
    /// Update the overlap buffer with data from the current chunk
    fn update_overlap_buffer(&mut self, chunk: &[u8]) {
        if chunk.len() >= self.max_pattern_len {
            // Chunk is larger than max pattern - just take last N bytes
            self.overlap_buffer.clear();
            self.overlap_buffer.extend(&chunk[chunk.len() - self.max_pattern_len..]);
        } else {
            // Chunk is smaller - need to preserve some old buffer + add new chunk
            // Keep the most recent (max_pattern_len - chunk.len()) bytes from old buffer
            let keep_from_old = self.max_pattern_len.saturating_sub(chunk.len());
            
            if self.overlap_buffer.len() > keep_from_old {
                // Remove old bytes we don't need from the front
                self.overlap_buffer.drain(0..self.overlap_buffer.len() - keep_from_old);
            }
            
            // Append new chunk bytes
            self.overlap_buffer.extend(chunk.iter().copied());
            
            // If overlap buffer exceeds max size, trim from front
            if self.overlap_buffer.len() > self.max_pattern_len {
                let excess = self.overlap_buffer.len() - self.max_pattern_len;
                self.overlap_buffer.drain(0..excess);
            }
        }
    }
    
    /// Finalize scanning and process any remaining buffered data
    /// 
    /// Call this after processing all chunks to scan the overlap buffer.
    pub fn finalize(&mut self) -> Vec<PatternMatch> {
        if self.overlap_buffer.is_empty() {
            return Vec::new();
        }
        
        let buffer_vec: Vec<u8> = self.overlap_buffer.iter().copied().collect();
        let matches = self.scanner.scan_all(&buffer_vec);
        
        self.overlap_buffer.clear();
        matches
    }
    
    /// Reset scanner state for reuse
    pub fn reset(&mut self) {
        self.overlap_buffer.clear();
        self.bytes_processed = 0;
    }
    
    /// Get total bytes processed so far
    pub fn bytes_processed(&self) -> usize {
        self.bytes_processed
    }
}

/// Parallel streaming scanner with pattern groups
/// 
/// Splits patterns into groups and scans each group in parallel.
/// This provides significant speedup for large pattern sets (15+ patterns).
/// 
/// Each pattern group maintains its own overlap buffer, allowing
/// true parallel processing without coordination overhead.
pub struct ParallelStreamingScanner {
    pattern_groups: Vec<StreamingScanner>,
    num_groups: usize,
}

impl ParallelStreamingScanner {
    /// Create a parallel streaming scanner
    /// 
    /// Patterns are split into `num_groups` groups, with each group
    /// processed on a separate thread.
    /// 
    /// # Arguments
    /// * `patterns` - All patterns to scan for
    /// * `num_groups` - Number of parallel groups (typically number of CPU cores)
    /// 
    /// # Example
    /// ```ignore
    /// let patterns = all_malware_patterns();
    /// let scanner = ParallelStreamingScanner::new(patterns, 8)?;
    /// 
    /// for chunk in file_chunks {
    ///     // This scans with 8 threads in parallel
    ///     let matches = scanner.scan_chunk(&chunk);
    /// }
    /// ```
    pub fn new(patterns: Vec<Pattern>, num_groups: usize) -> Result<Self, String> {
        if num_groups == 0 {
            return Err("num_groups must be at least 1".to_string());
        }
        
        // Split patterns into groups (round-robin distribution)
        let mut groups = vec![Vec::new(); num_groups];
        for (i, pattern) in patterns.into_iter().enumerate() {
            groups[i % num_groups].push(pattern);
        }
        
        // Create scanner per group
        let pattern_groups = groups.into_iter()
            .map(StreamingScanner::new)
            .collect::<Result<Vec<_>, _>>()?;
        
        Ok(Self {
            pattern_groups,
            num_groups,
        })
    }
    
    /// Scan a chunk with all pattern groups in parallel
    /// 
    /// Each pattern group is processed on a separate thread, with all groups
    /// scanning the same chunk simultaneously.
    /// 
    /// # Performance
    /// For N pattern groups on M cores (where N ≤ M):
    /// - Expected speedup: ~N× compared to sequential
    /// - Example: 8 groups on 8 cores ≈ 7.5× speedup
    pub fn scan_chunk(&mut self, chunk: &[u8]) -> Vec<PatternMatch> {
        if chunk.is_empty() {
            return Vec::new();
        }
        
        // Scan chunk with ALL pattern groups IN PARALLEL
        self.pattern_groups
            .par_iter_mut()
            .flat_map(|scanner| scanner.scan_chunk(chunk))
            .collect()
    }
    
    /// Finalize all pattern group scanners
    pub fn finalize(&mut self) -> Vec<PatternMatch> {
        self.pattern_groups
            .par_iter_mut()
            .flat_map(|scanner| scanner.finalize())
            .collect()
    }
    
    /// Reset all scanners for reuse
    pub fn reset(&mut self) {
        self.pattern_groups.par_iter_mut()
            .for_each(|scanner| scanner.reset());
    }
    
    /// Get total bytes processed (from first group - all should be same)
    pub fn bytes_processed(&self) -> usize {
        self.pattern_groups.first()
            .map(|s| s.bytes_processed())
            .unwrap_or(0)
    }
    
    /// Get number of pattern groups
    pub fn num_groups(&self) -> usize {
        self.num_groups
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_test_patterns() -> Vec<Pattern> {
        vec![
            Pattern {
                bytes: b"MZ\x90\x00",
                description: "PE header",
                score: 3,
            },
            Pattern {
                bytes: b"#!/bin/bash",
                description: "Bash script",
                score: 2,
            },
            Pattern {
                bytes: b"import os",
                description: "Python import",
                score: 2,
            },
        ]
    }

    #[test]
    fn test_streaming_scanner_basic() {
        let patterns = create_test_patterns();
        let mut scanner = StreamingScanner::new(patterns).unwrap();
        
        // Scan a chunk with a pattern
        let chunk = b"This is a #!/bin/bash script";
        let matches = scanner.scan_chunk(chunk);
        
        assert_eq!(matches.len(), 1);
        assert_eq!(matches[0].description, "Bash script");
        assert_eq!(matches[0].score, 2);
    }
    
    #[test]
    fn test_streaming_scanner_boundary() {
        let patterns = create_test_patterns();
        let mut scanner = StreamingScanner::new(patterns).unwrap();
        
        // Pattern split across chunks: "MZ\x90" | "\x00"
        let chunk1 = b"Some data MZ\x90";
        let chunk2 = b"\x00 more data";
        
        let matches1 = scanner.scan_chunk(chunk1);
        let matches2 = scanner.scan_chunk(chunk2);
        
        // Should detect pattern at boundary
        let all_matches: Vec<_> = matches1.into_iter().chain(matches2).collect();
        assert!(all_matches.iter().any(|m| m.description == "PE header"));
    }
    
    #[test]
    fn test_streaming_scanner_finalize() {
        let patterns = create_test_patterns();
        let mut scanner = StreamingScanner::new(patterns).unwrap();
        
        // Pattern in last chunk that goes into overlap buffer
        let chunk = b"Some data import os";
        scanner.scan_chunk(chunk);
        
        // Finalize should scan the overlap buffer
        let final_matches = scanner.finalize();
        assert!(final_matches.iter().any(|m| m.description == "Python import"));
    }
    
    #[test]
    fn test_streaming_scanner_reset() {
        let patterns = create_test_patterns();
        let mut scanner = StreamingScanner::new(patterns).unwrap();
        
        scanner.scan_chunk(b"test data");
        assert!(scanner.bytes_processed() > 0);
        
        scanner.reset();
        assert_eq!(scanner.bytes_processed(), 0);
    }
    
    #[test]
    fn test_parallel_streaming_scanner() {
        let patterns = create_test_patterns();
        let mut scanner = ParallelStreamingScanner::new(patterns, 2).unwrap();
        
        // Scan with multiple patterns
        let chunk = b"MZ\x90\x00 and #!/bin/bash and import os";
        let matches = scanner.scan_chunk(chunk);
        
        // Should find all three patterns
        assert_eq!(matches.len(), 3);
    }
    
    #[test]
    fn test_parallel_streaming_boundary() {
        let patterns = create_test_patterns();
        let mut scanner = ParallelStreamingScanner::new(patterns, 2).unwrap();
        
        // Pattern split across chunks
        let chunk1 = b"Data MZ\x90";
        let chunk2 = b"\x00 more";
        
        let matches1 = scanner.scan_chunk(chunk1);
        let matches2 = scanner.scan_chunk(chunk2);
        
        let all_matches: Vec<_> = matches1.into_iter().chain(matches2).collect();
        assert!(all_matches.iter().any(|m| m.description == "PE header"));
    }
    
    #[test]
    fn test_parallel_streaming_finalize() {
        let patterns = create_test_patterns();
        let mut scanner = ParallelStreamingScanner::new(patterns, 2).unwrap();
        
        scanner.scan_chunk(b"Test import os");
        let final_matches = scanner.finalize();
        
        assert!(final_matches.iter().any(|m| m.description == "Python import"));
    }
    
    #[test]
    fn test_empty_chunks() {
        let patterns = create_test_patterns();
        let mut scanner = StreamingScanner::new(patterns).unwrap();
        
        let matches = scanner.scan_chunk(&[]);
        assert_eq!(matches.len(), 0);
    }
    
    #[test]
    fn test_very_small_chunks() {
        let patterns = create_test_patterns();
        let mut scanner = StreamingScanner::new(patterns).unwrap();
        
        // Send data byte by byte (worst case)
        // This tests that the overlap buffer correctly accumulates bytes
        let data = b"#!/bin/bash";
        let mut all_matches = Vec::new();
        
        for byte in data.iter() {
            let matches = scanner.scan_chunk(&[*byte]);
            all_matches.extend(matches);
        }
        
        // The pattern should be found during chunk processing (when overlap buffer + current byte completes it)
        // or in the final buffer scan
        let final_matches = scanner.finalize();
        all_matches.extend(final_matches);
        
        assert!(all_matches.iter().any(|m| m.description == "Bash script"));
    }
}

