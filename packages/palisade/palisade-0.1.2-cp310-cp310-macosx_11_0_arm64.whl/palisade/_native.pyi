"""
Type stubs for the Rust native extension module.

This file provides type hints for IDE autocomplete and type checking.
"""

__version__: str
"""Version of the Rust native extension"""

from dataclasses import dataclass

# ============================================
# Streaming Pattern Scanners
# ============================================

@dataclass
class PyPatternMatch:
    description: str
    score: int

class PyStreamingScanner:
    """Single-threaded streaming pattern scanner with boundary handling.
    
    Use this for simple streaming or when you have limited CPU cores.
    Automatically handles patterns split across chunk boundaries.
    
    Example:
        >>> scanner = PyStreamingScanner.with_malware_patterns()
        >>> for chunk in file_chunks:
        ...     matches = scanner.scan_chunk(chunk)
        ...     for match in matches:
        ...         print(f"Found: {match.description}")
        >>> final_matches = scanner.finalize()
    """
    
    @staticmethod
    def with_malware_patterns() -> 'PyStreamingScanner':
        """Create scanner with default malware patterns"""
        ...
    
    def scan_chunk(self, chunk: bytes) -> list[PyPatternMatch]:
        """Scan a chunk and return matches (handles boundaries automatically)"""
        ...
    
    def finalize(self) -> list[PyPatternMatch]:
        """Finalize and return remaining matches"""
        ...
    
    def reset(self) -> None:
        """Reset scanner state for reuse"""
        ...
    
    @property
    def bytes_processed(self) -> int:
        """Total bytes processed so far"""
        ...

class PyParallelStreamingScanner:
    """Parallel streaming pattern scanner with multiple pattern groups.
    
    Splits patterns into groups and processes each group on a separate thread.
    Provides significant speedup for pattern sets with 15+ patterns.
    
    Example:
        >>> import multiprocessing
        >>> num_cores = multiprocessing.cpu_count()
        >>> scanner = PyParallelStreamingScanner.with_malware_patterns(num_cores)
        >>> for chunk in file_chunks:
        ...     matches = scanner.scan_chunk(chunk)  # Uses all cores!
        >>> final_matches = scanner.finalize()
    """
    
    @staticmethod
    def with_malware_patterns(num_groups: int) -> 'PyParallelStreamingScanner':
        """Create parallel scanner with specified number of groups
        
        Args:
            num_groups: Number of parallel groups (typically CPU core count)
        """
        ...
    
    def scan_chunk(self, chunk: bytes) -> list[PyPatternMatch]:
        """Scan chunk with all groups in parallel (GIL released)"""
        ...
    
    def finalize(self) -> list[PyPatternMatch]:
        """Finalize all scanners and return remaining matches"""
        ...
    
    def reset(self) -> None:
        """Reset all scanners for reuse"""
        ...
    
    @property
    def bytes_processed(self) -> int:
        """Total bytes processed"""
        ...
    
    @property
    def num_groups(self) -> int:
        """Number of pattern groups"""
        ...

# ============================================
# SafeTensors Validation
# ============================================

class SafeTensorsValidation:
    """Result of SafeTensors validation.
    
    Attributes:
        is_valid: True if file passed all validation checks
        header_size: Size of the JSON header in bytes
        tensor_count: Number of tensors in the file
        total_size: Total file size in bytes
        warnings: List of warning messages from validation
        metadata: Optional metadata dictionary from __metadata__ field
        tensor_names: List of all tensor names in the file
        suspicious_tensor_names: List of tensor names flagged as suspicious
        suspicious_data_patterns: List of suspicious patterns found in tensor data
    """
    is_valid: bool
    header_size: int
    tensor_count: int
    total_size: int
    warnings: list[str]
    metadata: dict[str, str] | None
    tensor_names: list[str]
    suspicious_tensor_names: list[str]
    suspicious_data_patterns: list[str]

class TensorInfo:
    """Information about a tensor in a SafeTensors file."""
    name: str
    dtype: str
    shape: list[int]
    data_offsets: tuple[int, int]

def validate_safetensors(data: bytes) -> SafeTensorsValidation:
    """
    Validate a SafeTensors file format and structure with comprehensive security checks.
    
    This function performs:
    1. Structure validation (header parsing, JSON validation)
    2. Tensor name security checks (suspicious patterns, special characters)
    3. Data offset validation (bounds checking, overflow detection)
    4. Tensor data scanning for malicious patterns (executables, scripts, shell commands)
    5. Metadata validation
    6. DoS protection (header size limits)
    
    Args:
        data: Raw bytes of the SafeTensors file
        
    Returns:
        SafeTensorsValidation object with validation results including:
        - is_valid: Overall validation status
        - warnings: List of all warnings/issues found
        - tensor_names: All tensor names extracted
        - suspicious_tensor_names: Tensor names flagged as suspicious
        - suspicious_data_patterns: Malicious patterns found in tensor data
        
    Performance:
        - 10-50x faster than pure Python validation
        - Scans up to 10MB of tensor data for suspicious patterns
        - Uses efficient byte pattern matching
        
    Example:
        >>> with open("model.safetensors", "rb") as f:
        ...     data = f.read()
        >>> result = validate_safetensors(data)
        >>> if result.is_valid:
        ...     print(f"✅ Valid! {result.tensor_count} tensors found")
        >>> else:
        ...     print(f"⚠️  Warnings: {len(result.warnings)}")
        ...     if result.suspicious_data_patterns:
        ...         print(f"🚨 Suspicious patterns: {result.suspicious_data_patterns}")
    """
    ...

def parse_safetensors_header(data: bytes) -> list[TensorInfo]:
    """
    Parse SafeTensors header and extract tensor information.
    
    Args:
        data: Raw bytes of the SafeTensors file (at least header portion)
        
    Returns:
        List of TensorInfo objects describing each tensor
        
    Example:
        >>> tensors = parse_safetensors_header(data)
        >>> for tensor in tensors:
        ...     print(f"{tensor.name}: {tensor.dtype} {tensor.shape}")
    """
    ...

def is_safetensors(data: bytes) -> bool:
    """
    Quick check if data is in SafeTensors format.
    
    Only reads the first few bytes to detect format,
    does not perform full validation.
    
    Args:
        data: Raw bytes to check (at least first 8 bytes + some header)
        
    Returns:
        True if data appears to be SafeTensors format
        
    Example:
        >>> with open("model.bin", "rb") as f:
        ...     data = f.read(1024)
        >>> if is_safetensors(data):
        ...     print("This is a SafeTensors file!")
    """
    ...

class SafeTensorsStreamingValidator:
    """Streaming validator for large SafeTensors files.
    
    Processes files chunk-by-chunk with parallel pattern matching and
    boundary handling to detect patterns split across chunks.
    
    Example:
        >>> import multiprocessing
        >>> validator = SafeTensorsStreamingValidator(multiprocessing.cpu_count())
        >>> 
        >>> # Validate header first
        >>> header_data = file.read(10 * 1024 * 1024)  # Read first 10MB
        >>> if validator.validate_header(header_data):
        >>>     # Process tensor data chunks
        >>>     for chunk in file_chunks:
        >>>         patterns = validator.process_chunk(chunk)
        >>>         if patterns:
        >>>             print(f"Found suspicious patterns: {patterns}")
        >>> 
        >>> # Get final results
        >>> result = validator.finalize()
    """
    
    def __init__(self, num_cores: int) -> None:
        """Create streaming validator with specified number of cores"""
        ...
    
    def validate_header(self, header_data: bytes) -> bool:
        """Validate SafeTensors header and extract tensor names.
        
        Args:
            header_data: Header data (first ~10MB of file)
            
        Returns:
            True if header is valid
        """
        ...
    
    def process_chunk(self, chunk: bytes) -> list[str]:
        """Process a tensor data chunk (releases GIL).
        
        Args:
            chunk: Chunk of tensor data
            
        Returns:
            List of suspicious pattern descriptions found
        """
        ...
    
    def finalize(self) -> SafeTensorsValidation:
        """Finalize validation and get complete results.
        
        Returns:
            Complete validation results
        """
        ...

@dataclass
class ModelIntegrityValidation:
    is_valid: bool
    warnings: list[str]
    suspicious_patterns: list[str]

def validate_model_integrity(data: bytes) -> ModelIntegrityValidation:
    """Validate complete model file for integrity issues.
    
    Performs malware pattern detection using shared Aho-Corasick scanner.
    """
    ...

class ModelIntegrityStreamingValidator:
    def __init__(self, num_cores: int): ...
    def process_chunk(self, chunk: bytes) -> list[PyPatternMatch]: ...
    def finalize(self) -> list[PyPatternMatch]: ...

