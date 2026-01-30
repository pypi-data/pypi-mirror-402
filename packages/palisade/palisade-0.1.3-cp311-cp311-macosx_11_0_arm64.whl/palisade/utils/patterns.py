"""Shared security patterns and detection utilities for validators.

This module consolidates commonly used security patterns across validators
to reduce code duplication and improve maintainability.
"""

import math
import re
from pathlib import Path
from typing import Dict, List, Optional, Set


class SecurityPatterns:
    """Centralized security patterns used across multiple validators."""

    # Tampering indicators (consolidated from supply_chain, model_integrity, model_genealogy)
    # Made more specific to avoid false positives
    TAMPERING_INDICATORS = {
        # Direct tampering indicators
        "tampered_with", "altered_model", "patched_version", "unofficial_build",
        "modified_weights", "custom_weights", "backdoor_weights",
        
        # Suspicious version indicators
        "version_modified", "build_tampered", "weights_altered",
        "model_patched", "unofficial_release", "custom_fork",
        
        # More specific tampering indicators
        "tampered_model", "altered_weights", "patched_model", "modified_model",
        "backdoor_injection", "malicious_patch", "unauthorized_modification"
    }

    # Patterns indicating potential code injection or hooking
    INJECTION_INDICATORS = {
        "inject", "hook", "override", "hijack", "intercept",
        "monkey_patch", "dynamic_loading", "runtime_modification",
    }

    # Patterns indicating potential obfuscation or hidden logic
    OBFUSCATION_INDICATORS = {
        "obfuscate", "encode", "encrypt", "hide", "mask",
        "scramble", "compress", "pack",
    }

    # Suspicious keywords found in model metadata
    SUSPICIOUS_METADATA = {
        "unknown_version", "custom_build", "modified_framework",
        "unofficial", "experimental", "debug",
    }

    # Malicious function names (from supply_chain, pickle_security, backdoor)
    # Made more specific to avoid false positives
    MALICIOUS_FUNCTIONS = {
        # Code execution (high risk)
        "eval(", "exec(", "__import__(", "compile(",
        
        # System calls (high risk)
        "os.system(", "os.popen(", "subprocess.call(", "subprocess.run(",
        "subprocess.Popen(", "system(",
        
        # Network operations (specific methods)
        "socket.socket(", "socket.connect(", "socket.send(",
        "urllib.request.urlopen(", "urllib.request.Request(",
        "requests.get(", "requests.post(", "requests.put(", "requests.delete(",
        
        # Dynamic imports (high risk)
        "import(", "__import__(", "importlib.import_module(",
        
        # Platform/system info (context-dependent)
        "platform.system(", "platform.platform(", "platform.machine("
    }

    # Data exfiltration patterns (from supply_chain, backdoor, pickle_security)
    # Made more specific to avoid false positives
    DATA_EXFILTRATION = {
        # Base64 encoding/decoding
        "base64.b64encode", "base64.b64decode", "base64.encode", "base64.decode",
        
        # Pickle serialization (high risk)
        "pickle.loads", "pickle.dumps", "pickle.load", "pickle.dump",
        
        # Marshal serialization
        "marshal.loads", "marshal.dumps", "marshal.load", "marshal.dump",
        
        # Network operations (specific methods)
        "requests.get", "requests.post", "requests.put", "requests.delete",
        "urllib.request.urlopen", "urllib.request.Request",
        "socket.send", "socket.recv", "socket.connect",
        
        # File operations (suspicious in model context) - made more specific
        "download_file", "upload_file", "send_file", "receive_file",
        "download_model", "upload_model", "steal_data", "exfiltrate",
        
        # System calls (high risk)
        "os.system", "subprocess.call", "subprocess.run", "subprocess.Popen",
        
        # Data extraction methods
        "ctypes.CDLL", "ctypes.windll", "ctypes.cdll",
        
        # Generic but context-specific - made more specific
        "send_data(", "post_data(", "get_data(", "put_data(", "delete_data("
    }

    # Network/URL patterns (from model_integrity, supply_chain)
    NETWORK_INDICATORS = {
        "http://", "https://", "ftp://", ".com", ".org", ".net",
        "192.168.", "10.", "172.", "127.0.0.1", "localhost"
    }

    # Suspicious tokens for tokenizers (from metadata_security, tokenizer_hygiene)
    INJECTION_TOKENS = {
        "<script>", "<html>", "<img>", "javascript:", "eval(",
        "exec(", "system(", "import ", "__import__", "password",
        "secret", "key", "token", "private", "confidential"
    }


class FilePatterns:
    """File extension and format patterns."""

    # Native library extensions (from buffer_overflow, tokenizer_hygiene)
    NATIVE_EXTENSIONS = {".so", ".dll", ".dylib", ".a", ".lib", ".o", ".obj"}

    # Archive formats (from buffer_overflow, pickle_security)
    ARCHIVE_FORMATS = {".zip", ".tar", ".gz", ".tgz", ".tar.gz", ".rar", ".7z"}

    # Executable extensions
    EXECUTABLE_EXTENSIONS = {".exe", ".bin", ".app", ".deb", ".rpm", ".msi"}

    # Compiled model formats
    COMPILED_FORMATS = {".onnx", ".trt", ".engine", ".tensorrt", ".openvino"}


class BinaryPatterns:
    """Binary analysis patterns and signatures."""

    # Binary signatures (from buffer_overflow, model_integrity)
    BINARY_SIGNATURES = {
        b"MZ": "pe_executable",           # Windows PE
        b"\x7fELF": "elf_executable",     # Linux/Unix ELF
        b"\xfe\xed\xfa\xce": "mach_o_32", # macOS Mach-O 32-bit
        b"\xfe\xed\xfa\xcf": "mach_o_64", # macOS Mach-O 64-bit
        b"GGUF": "gguf_model",           # GGUF model format
        b"PK": "zip_archive",            # ZIP/JAR archives
    }


class PatternMatcher:
    """Unified pattern matching utilities."""

    @staticmethod
    def scan_for_patterns(data: bytes, pattern_sets: Dict[str, Set[str]],
                         case_sensitive: bool = False) -> Dict[str, List[str]]:
        """
        Scan data for multiple pattern sets efficiently.
        
        Args:
            data: Data to scan
            pattern_sets: Dictionary of pattern set name to patterns
            case_sensitive: Whether to perform case-sensitive matching
            
        Returns:
            Dictionary mapping pattern set names to found patterns
        """
        results = {}

        # Convert data once
        text_data = data.decode("utf-8", errors="ignore")
        if not case_sensitive:
            text_data = text_data.lower()

        for set_name, patterns in pattern_sets.items():
            found = []
            for pattern in patterns:
                search_pattern = pattern if case_sensitive else pattern.lower()
                if search_pattern in text_data:
                    found.append(pattern)
            if found:
                results[set_name] = found

        return results

    @staticmethod
    def scan_binary_patterns(data: bytes, max_scan_size: int = 1024 * 1024) -> List[str]:
        """
        Scan for suspicious binary patterns.
        
        Args:
            data: Binary data to scan
            max_scan_size: Maximum size to scan for performance
            
        Returns:
            List of detected pattern types
        """
        scan_data = data[:max_scan_size]
        detected = []

        # Check for binary signatures
        for signature, sig_type in BinaryPatterns.BINARY_SIGNATURES.items():
            if scan_data.startswith(signature):
                detected.append(sig_type)

        # Check for high entropy (possible encryption/packing)
        if len(scan_data) > 8192:
            entropy = BinaryAnalyzer.calculate_entropy(scan_data[:8192])
            if entropy > 7.5:
                detected.append("high_entropy_content")

        return detected


class BinaryAnalyzer:
    """Binary analysis utilities consolidated from multiple validators."""

    @staticmethod
    def detect_binary_type(data: bytes) -> Optional[str]:
        """
        Detect binary executable type from data.
        Consolidated from buffer_overflow.py and model_integrity.py
        """
        if len(data) < 4:
            return None

        for signature, binary_type in BinaryPatterns.BINARY_SIGNATURES.items():
            if data.startswith(signature):
                return binary_type

        return None

    @staticmethod
    def calculate_entropy(data: bytes) -> float:
        """
        Calculate Shannon entropy of data.
        Consolidated from model_genealogy.py and decompression_bomb.py
        """
        if len(data) == 0:
            return 0.0

        # Count byte frequencies
        frequencies = [0] * 256
        for byte in data:
            frequencies[byte] += 1

        # Calculate entropy
        entropy = 0.0
        data_len = len(data)

        for count in frequencies:
            if count > 0:
                probability = count / data_len
                entropy -= probability * math.log2(probability)

        return entropy

    @staticmethod
    def validate_section_boundaries(offset: int, size: int, data_len: int,
                                  max_size: int = 100 * 1024 * 1024) -> bool:
        """
        Validate binary section boundaries for security.
        Consolidated from buffer_overflow.py binary analysis methods.
        """
        return (offset > 0 and size > 0 and
                offset < data_len and size <= max_size and
                offset <= data_len - size)


class FileValidator:
    """File validation utilities."""

    @staticmethod
    def is_archive(file_path: str) -> bool:
        """Check if file is an archive format."""
        return Path(file_path).suffix.lower() in FilePatterns.ARCHIVE_FORMATS

    @staticmethod
    def is_native_library(file_path: str) -> bool:
        """Check if file is a native library."""
        return Path(file_path).suffix.lower() in FilePatterns.NATIVE_EXTENSIONS

    @staticmethod
    def is_executable(file_path: str) -> bool:
        """Check if file is an executable."""
        return Path(file_path).suffix.lower() in FilePatterns.EXECUTABLE_EXTENSIONS

    @staticmethod
    def is_compiled_model(file_path: str) -> bool:
        """Check if file is a compiled model format."""
        return Path(file_path).suffix.lower() in FilePatterns.COMPILED_FORMATS


class RegexPatterns:
    """Centralized regex patterns for security scanning."""

    # Base64-like pattern (from model_integrity.py)
    BASE64_PATTERN = re.compile(r"[A-Za-z0-9+/]{50,}={0,2}")

    # Format string vulnerability patterns (from buffer_overflow.py)
    FORMAT_STRING_PATTERNS = {
        "dangerous_format_n": re.compile(rb"%n"),
        "large_width_specifier": re.compile(rb"%.{6,}d"),
        "extreme_width_spec": re.compile(rb"%\d{6,}"),
    }

    # URL patterns
    URL_PATTERN = re.compile(r"https?://[^\s<>\"]+|www\.[^\s<>\"]+")

    @staticmethod
    def scan_format_strings(data: bytes) -> Dict[str, int]:
        """Scan for format string vulnerability patterns."""
        results = {}
        for pattern_name, compiled_pattern in RegexPatterns.FORMAT_STRING_PATTERNS.items():
            matches = compiled_pattern.findall(data)
            if matches:
                results[pattern_name] = len(matches)
        return results
