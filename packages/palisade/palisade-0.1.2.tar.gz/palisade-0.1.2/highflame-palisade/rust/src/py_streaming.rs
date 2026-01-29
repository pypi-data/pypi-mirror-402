/// Python bindings for streaming pattern scanners
/// 
/// This module provides Python-accessible wrappers for the Rust streaming scanners,
/// allowing Python code to use high-performance streaming pattern matching.

use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;

use crate::malware_patterns::all_malware_patterns;
use crate::pattern_matching::PatternMatch;
use crate::streaming::ParallelStreamingScanner;

/// A PyO3-compatible wrapper for PatternMatch
#[pyclass(name = "PyPatternMatch")]
#[derive(Debug, Clone)]
pub struct PyPatternMatch {
    #[pyo3(get)]
    pub description: String,
    #[pyo3(get)]
    pub score: i32,
}

impl From<PatternMatch> for PyPatternMatch {
    fn from(match_info: PatternMatch) -> Self {
        Self {
            description: match_info.description,
            score: match_info.score,
        }
    }
}

/// Single-threaded streaming pattern scanner (Python wrapper)
/// 
/// Use this for simple streaming or when you have limited CPU cores.
/// 
/// Example:
/// ```python
/// from palisade._native import PyStreamingScanner
/// 
/// # Create scanner with malware patterns
/// scanner = PyStreamingScanner.with_malware_patterns()
/// 
/// # Process chunks
/// for chunk in file_chunks:
///     matches = scanner.scan_chunk(chunk)
///     for match in matches:
///         print(f"Found: {match.description} (score: {match.score})")
/// 
/// # Don't forget to finalize!
/// final_matches = scanner.finalize()
/// ```
#[pyclass]
pub struct PyStreamingScanner {
    inner: crate::streaming::StreamingScanner,
}

#[pymethods]
impl PyStreamingScanner {
    /// Create a new streaming scanner with default malware patterns
    #[staticmethod]
    pub fn with_malware_patterns() -> PyResult<Self> {
        let patterns = all_malware_patterns();
        let inner = crate::streaming::StreamingScanner::new(patterns)
            .map_err(|e| PyValueError::new_err(e))?;
        
        Ok(Self { inner })
    }
    
    /// Scan a chunk of data and return matches
    /// 
    /// This automatically handles patterns split across chunk boundaries.
    pub fn scan_chunk(&mut self, chunk: &[u8]) -> Vec<PyPatternMatch> {
        self.inner.scan_chunk(chunk)
            .into_iter()
            .map(PyPatternMatch::from)
            .collect()
    }
    
    /// Finalize scanning and return any remaining matches
    /// 
    /// Call this after processing all chunks to scan the overlap buffer.
    pub fn finalize(&mut self) -> Vec<PyPatternMatch> {
        self.inner.finalize()
            .into_iter()
            .map(PyPatternMatch::from)
            .collect()
    }
    
    /// Reset the scanner for reuse
    pub fn reset(&mut self) {
        self.inner.reset();
    }
    
    /// Get total bytes processed
    #[getter]
    pub fn bytes_processed(&self) -> usize {
        self.inner.bytes_processed()
    }
}

/// Parallel streaming pattern scanner (Python wrapper)
/// 
/// Splits patterns into groups and processes each group on a separate thread.
/// Provides significant speedup for pattern sets with 15+ patterns.
/// 
/// Example:
/// ```python
/// from palisade._native import PyParallelStreamingScanner
/// import multiprocessing
/// 
/// # Create parallel scanner with CPU core count
/// num_cores = multiprocessing.cpu_count()
/// scanner = PyParallelStreamingScanner.with_malware_patterns(num_cores)
/// 
/// # Process chunks (automatically uses all cores)
/// for chunk in file_chunks:
///     matches = scanner.scan_chunk(chunk)
///     process_matches(matches)
/// 
/// # Finalize
/// final_matches = scanner.finalize()
/// ```
#[pyclass]
pub struct PyParallelStreamingScanner {
    inner: Option<ParallelStreamingScanner>,
}

#[pymethods]
impl PyParallelStreamingScanner {
    /// Create a new parallel streaming scanner with the default malware patterns.
    #[new]
    pub fn new(num_groups: usize) -> PyResult<Self> {
        let patterns = all_malware_patterns();
        let scanner = ParallelStreamingScanner::new(patterns, num_groups)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e))?;
        Ok(Self { inner: Some(scanner) })
    }
    
    /// Scan a chunk of data for patterns.
    /// 
    /// Automatically releases Python GIL during scanning for maximum performance.
    pub fn scan_chunk(&mut self, py: Python, chunk: &[u8]) -> PyResult<Vec<PyPatternMatch>> {
        let scanner = self
            .inner
            .as_mut()
            .ok_or_else(|| PyValueError::new_err("Scanner not initialized"))?;
        // Release GIL during Rust parallel processing
        let matches = py.allow_threads(|| scanner.scan_chunk(chunk));
        let py_matches: Vec<PyPatternMatch> = matches.into_iter().map(PyPatternMatch::from).collect();
        Ok(py_matches)
    }
    
    /// Finalize all pattern group scanners
    pub fn finalize(&mut self, py: Python) -> PyResult<Vec<PyPatternMatch>> {
        if let Some(mut scanner) = self.inner.take() {
            let matches = py.allow_threads(move || scanner.finalize());
            let py_matches: Vec<PyPatternMatch> = matches.into_iter().map(PyPatternMatch::from).collect();
            Ok(py_matches)
        } else {
            Ok(Vec::new())
        }
    }
    
    /// Reset all scanners for reuse
    pub fn reset(&mut self) {
        self.inner.as_mut().map(|s| s.reset());
    }
    
    /// Get total bytes processed
    #[getter]
    pub fn bytes_processed(&self) -> usize {
        self.inner.as_ref().map_or(0, |s| s.bytes_processed())
    }
    
    /// Get number of pattern groups
    #[getter]
    pub fn num_groups(&self) -> usize {
        self.inner.as_ref().map_or(0, |s| s.num_groups())
    }
}

