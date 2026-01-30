"""GGUF safety validator - Critical for GGUF format integrity and security."""

import logging
import math
import re
import struct
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from palisade.core.cedar_policy_engine import CedarPolicyEngine
    from palisade.models.model_file import ModelFile
    from palisade.models.types import ChunkInfo, StreamingContext

# REMOVED: numpy import - not needed after removing statistical analysis
# REMOVED: SciPy import - not needed after removing statistical analysis
from palisade.core.constants import GGUF_MAGIC, GGUF_VALUE_TYPES, GGUF_VERSION
from palisade.models.metadata import ModelMetadata, ModelType

from .base import BaseValidator, Severity

logger = logging.getLogger(__name__)

class GGUFSafetyValidator(BaseValidator):
    """CRITICAL SECURITY VALIDATOR
    Validates GGUF format safety and integrity:
    - GGUF header structure and magic byte verification
    - KV metadata parsing and validation
    - Tensor checksum verification
    - Quantization type validation
    - RoPE/architecture metadata consistency
    - Detection of suspicious/unexpected KV keys.
    """

    def __init__(self, metadata: ModelMetadata, policy_engine: Optional["CedarPolicyEngine"] = None) -> None:
        super().__init__(metadata, policy_engine)

        # GGUF format constants
        self.GGUF_MAGIC = GGUF_MAGIC
        self.GGUF_VERSION = GGUF_VERSION

        # GGUF value types from constants

        # CRITICAL SECURITY: Initialize recursion depth tracking to prevent stack overflow
        self._recursion_depth = 0
        self._max_recursion_depth = 10  # Reasonable limit for nested structures

        # Load policy-configurable settings
        self._load_policy_configuration()

        # GGUF type constants for parsing (mapped from GGUF_VALUE_TYPES)
        self.GGUF_TYPE_UINT8 = GGUF_VALUE_TYPES["UINT8"]
        self.GGUF_TYPE_INT8 = GGUF_VALUE_TYPES["INT8"]
        self.GGUF_TYPE_UINT16 = GGUF_VALUE_TYPES["UINT16"]
        self.GGUF_TYPE_INT16 = GGUF_VALUE_TYPES["INT16"]
        self.GGUF_TYPE_UINT32 = GGUF_VALUE_TYPES["UINT32"]
        self.GGUF_TYPE_INT32 = GGUF_VALUE_TYPES["INT32"]
        self.GGUF_TYPE_FLOAT32 = GGUF_VALUE_TYPES["FLOAT32"]
        self.GGUF_TYPE_BOOL = GGUF_VALUE_TYPES["BOOL"]
        self.GGUF_TYPE_STRING = GGUF_VALUE_TYPES["STRING"]
        self.GGUF_TYPE_ARRAY = GGUF_VALUE_TYPES["ARRAY"]
        self.GGUF_TYPE_UINT64 = GGUF_VALUE_TYPES["UINT64"]
        self.GGUF_TYPE_INT64 = GGUF_VALUE_TYPES["INT64"]
        self.GGUF_TYPE_FLOAT64 = GGUF_VALUE_TYPES["FLOAT64"]

        # SECURITY: Configurable limits to prevent DoS attacks
        self.MAX_SAFE_STRING_LENGTH = 10000
        self.MAX_SAFE_ARRAY_LENGTH = 500000  # Increased to accommodate legitimate GGUF vocab arrays
        self.MAX_ARRAY_ELEMENTS_MATERIALIZED = 1000
        self.MAX_TENSOR_DIMENSIONS = 2**31  # Maximum safe dimension size
        self.MAX_ELEMENT_COUNT = 2**40      # Maximum safe element count

        # FLEXIBLE: GGUF KV metadata keys categorized by importance
        self.required_kv_keys = {
            # Absolutely essential keys (always required)
            "critical": {
                "general.architecture",  # Only truly critical key
            },
            # Important but not always present
            "important": {
                "general.name",
                "general.file_type",
            },
        }

        self.recommended_kv_keys = {
            # General model information (nice to have but not required)
            "general_metadata": {
                "general.author",
                "general.version",
                "general.description",
                "general.license",
            },
            "provenance": {
                "general.source_url",
                "general.source_hf_repo",
                "general.quantization_version",
            },
            # Architecture-specific (varies by architecture)
            "architecture_specific": {
                "llama.context_length",
                "llama.embedding_length",
                "llama.block_count",
                "mistral.context_length",
                "mistral.embedding_length",
                "gpt2.context_length",
                "bloom.context_length",
            },
            # Tokenizer metadata (when tokenizer is embedded)
            "tokenizer": {
                "tokenizer.ggml.model",
                "tokenizer.ggml.tokens",
                "tokenizer.ggml.bos_token_id",
                "tokenizer.ggml.eos_token_id",
                "tokenizer.ggml.unk_token_id",
            },
            # Training metadata (rarely present)
            "training": {
                "training.data_sources",
                "training.epochs",
            },
        }

        # Valid GGUF quantization types
        self.valid_quantization_types = {
            "F32": {"name": "float32", "bits": 32, "safe": True},
            "F16": {"name": "float16", "bits": 16, "safe": True},
            "BF16": {"name": "bfloat16", "bits": 16, "safe": True},  # ← CRITICAL: Added missing BF16
            "Q4_0": {"name": "q4_0", "bits": 4, "safe": True},
            "Q4_1": {"name": "q4_1", "bits": 4, "safe": True},
            "Q5_0": {"name": "q5_0", "bits": 5, "safe": True},
            "Q5_1": {"name": "q5_1", "bits": 5, "safe": True},
            "Q8_0": {"name": "q8_0", "bits": 8, "safe": True},
            "Q8_1": {"name": "q8_1", "bits": 8, "safe": True},
            "Q2_K": {"name": "q2_k", "bits": 2, "safe": True},
            "Q3_K": {"name": "q3_k", "bits": 3, "safe": True},
            "Q4_K": {"name": "q4_k", "bits": 4, "safe": True},
            "Q5_K": {"name": "q5_k", "bits": 5, "safe": True},
            "Q6_K": {"name": "q6_k", "bits": 6, "safe": True},
            "Q8_K": {"name": "q8_k", "bits": 8, "safe": True},
            "IQ2_XXS": {"name": "iq2_xxs", "bits": 2, "safe": True},
            "IQ2_XS": {"name": "iq2_xs", "bits": 2, "safe": True},
            "IQ3_XXS": {"name": "iq3_xxs", "bits": 3, "safe": True},
            # ← CRITICAL: Added missing I-quant and extended types
            "IQ1_S": {"name": "iq1_s", "bits": 1, "safe": True},
            "IQ4_NL": {"name": "iq4_nl", "bits": 4, "safe": True},
            "IQ3_S": {"name": "iq3_s", "bits": 3, "safe": True},
            "IQ2_S": {"name": "iq2_s", "bits": 2, "safe": True},
            "IQ4_XS": {"name": "iq4_xs", "bits": 4, "safe": True},
            "IQ1_M": {"name": "iq1_m", "bits": 1, "safe": True},
            # Experimental types (marked as less safe due to instability)
            "TQ1_0": {"name": "tq1_0", "bits": 1, "safe": False},
            "TQ2_0": {"name": "tq2_0", "bits": 2, "safe": False},
        }

        # Architecture-specific required metadata
        self.arch_required_metadata = {
            "llama": {
                "llama.context_length",
                "llama.embedding_length",
                "llama.block_count",
                "llama.attention.head_count",
                "llama.rope.dimension_count",
            },
            "gpt2": {
                "gpt2.context_length",
                "gpt2.embedding_length",
                "gpt2.block_count",
            },
            "bloom": {
                "bloom.context_length",
                "bloom.embedding_length",
            },
            "mpt": {
                "mpt.context_length",
                "mpt.embedding_length",
            },
        }

    def _load_policy_configuration(self) -> None:
        """Load policy-configurable settings, falling back to defaults."""
        # Get policy configuration for GGUF validator
        policy_config = {}
        if self.policy_engine and hasattr(self.policy_engine, "get_validator_config"):
            policy_config = self.policy_engine.get_validator_config("gguf_safety", {})

        # Load configurable suspicious patterns (policy can override defaults)
        # ENHANCED: Much more specific patterns to reduce false positives
        default_suspicious_patterns = {
            "code_injection": {
                # Only flag actual code execution patterns, not generic words
                "eval(", "exec(", "__import__(", "compile(",
                "subprocess.call(", "subprocess.run(", "subprocess.Popen(",
                "os.system(", "os.popen(", "shell_exec(",
                # Command injection patterns
                "`", "&&", "||", "|", ";", "$(",
                # Template injection patterns
                "{{", "}}", "{%", "%}", "${{", "{{%",
            },
            "network_access": {
                # Only flag actual network access patterns, not generic URLs
                "socket.connect(", "socket.send(", "socket.recv(",
                "urllib.request.urlopen(", "requests.get(", "requests.post(",
                "wget ", "curl ", "nc ", "netcat ",
                # Suspicious network patterns
                "ftp://", "ssh://", "telnet://", "://",
            },
            "suspicious_keys": {
                # Only flag truly suspicious key patterns
                "backdoor", "poison", "malicious", "hidden",
                "secret", "private", "internal", "debug",
                "exploit", "hack", "inject", "bypass",
                "admin", "root", "sudo", "password",
                # Command injection in keys
                "cmd", "exec", "shell", "system",
            },
            "path_traversal": {
                # Only flag actual path traversal patterns
                "../", "..\\", "/etc/", "C:\\",
                "/root/", "/home/", "/var/", "/tmp/",
                "~/", ".ssh", ".aws", ".config",
                # Windows path traversal
                "..\\", "C:\\Windows\\", "C:\\System32\\",
            },
            "data_patterns": {
                # Only flag truly suspicious data patterns
                "shellcode", "exploit", "payload",
                "base64_decode(", "hex_decode(",
                "obfuscated", "encrypted", "compressed",
                # Suspicious encoding patterns
                "eval(", "exec(", "system(",
            },
        }

        self.suspicious_kv_patterns = policy_config.get("suspicious_patterns", default_suspicious_patterns)

        # Load configurable quantization type restrictions
        default_allowed_quantization = {
            "F32", "F16", "BF16", "Q4_0", "Q4_1", "Q5_0", "Q5_1", "Q8_0", "Q8_1",
            "Q2_K", "Q3_K", "Q4_K", "Q5_K", "Q6_K", "Q8_K",
            "IQ2_XXS", "IQ2_XS", "IQ3_XXS",
        }

        self.allowed_quantization_types = set(policy_config.get("allowed_quantization_types", default_allowed_quantization))

        # Load required metadata strictness level
        self.metadata_strictness = policy_config.get("metadata_strictness", "medium")  # low, medium, high

        # Load architecture validation requirements
        self.require_architecture_metadata = policy_config.get("require_architecture_metadata", True)
        # REMOVED: Statistical analysis configuration for supply chain simplification
        # Statistical thresholds are for ML quality assessment, not security scanning

        # GGUF layout validation settings
        self.gguf_alignment = policy_config.get("gguf_alignment", 32)  # Default 32-byte alignment
        self.enable_layout_validation = policy_config.get("enable_layout_validation", True)

        # SIMPLIFIED: Embedding protection policy (security-critical only)
        self.quantization_distribution_policy = policy_config.get("quantization_distribution_policy", {
            "embedding_protection": {
                "enabled": True,
                "protected_tensors": [
                    "tok_embeddings", "token_embd", "wte", "embed_tokens",  # Token embeddings
                    "output", "output_weight", "lm_head", "embed_out",       # Output embeddings
                ],
                "minimum_quality": "Q4_0",  # Minimum quantization quality for embeddings
                "policy_floor_types": ["Q2_K", "IQ2_XXS", "IQ2_XS", "IQ3_XXS"],  # Below-floor types → QUARANTINE
            },
        })

        # FLEXIBLE: GGML type mapping (policy-configurable for version compatibility)
        default_ggml_type_mapping = {
            # Standard floating point types
            0: "F32", 1: "F16", 17: "BF16",  # BF16 added in later versions
            # Legacy quantization types
            2: "Q4_0", 3: "Q4_1", 4: "Q5_0", 5: "Q5_1",
            6: "Q8_0", 7: "Q8_1",
            # K-quants (GGML v2)
            8: "Q2_K", 9: "Q3_K", 10: "Q4_K", 11: "Q5_K",
            12: "Q6_K", 13: "Q8_K",
            # I-quants (importance matrix quantization)
            14: "IQ2_XXS", 15: "IQ2_XS", 16: "IQ3_XXS",
            18: "IQ1_S", 19: "IQ4_NL", 20: "IQ3_S", 21: "IQ2_S",
            22: "IQ4_XS", 23: "IQ1_M",
            # Extended/experimental types (may vary by version)
            24: "TQ1_0", 25: "TQ2_0",
        }

        # Allow policy to override/extend the type mapping
        self.ggml_type_mapping = policy_config.get("ggml_type_mapping", default_ggml_type_mapping)

        # Merge any additional mappings from policy
        if "additional_ggml_types" in policy_config:
            self.ggml_type_mapping.update(policy_config["additional_ggml_types"])

        # Policy control for unknown type handling
        self.unknown_type_policy = policy_config.get("unknown_type_policy", "warn")  # "warn", "ignore", "error"

        # FLEXIBLE: Architecture allowlist (policy-configurable for new model types)
        default_known_architectures = {
            # Original architectures
            "llama", "gpt2", "bloom", "mpt", "falcon", "rwkv", "gptj", "gptneox",
            # Missing common architectures
            "mistral", "mixtral", "qwen", "qwen2", "qwen3", "phi", "gemma", "llava",
            # Additional common architectures
            "codellama", "vicuna", "alpaca", "stablelm", "internlm", "chatglm",
            "baichuan", "yi", "deepseek", "solar", "openchat", "zephyr", "phi3",
            # Recent architectures (2024+)
            "command-r", "aya", "granite", "nemotron", "llama3", "llama3.1", "llama3.2",
            # Vision/multimodal architectures
            "clip", "blip", "instructblip", "minigpt4", "llama-vision",
            # Google architectures (including gemma3)
            "gemma2", "gemma3", "gemma-2", "gemma-3",
        }

        # Allow policy to override or extend the architecture list
        self.known_architectures = set(policy_config.get("known_architectures", default_known_architectures))

        # Merge any additional architectures from policy
        if "additional_architectures" in policy_config:
            self.known_architectures.update(policy_config["additional_architectures"])

        # Policy control for unknown architecture handling
        self.unknown_architecture_policy = policy_config.get("unknown_architecture_policy", "warn")  # "warn", "ignore", "error"

        # Precise GGML element sizes (bytes per element)
        self.GGML_ELEM_SIZE = {
            # Float types
            "F32": 4, "F16": 2, "BF16": 2,
            # Basic quantization families (effective bytes per element)
            "Q4_0": 0.5, "Q4_1": 0.5, "Q5_0": 0.625, "Q5_1": 0.625,
            "Q8_0": 1.0, "Q8_1": 1.0,
            # K-quant approximations; exact block sizes vary
            "Q2_K": 0.3125, "Q3_K": 0.390625, "Q4_K": 0.5,
            "Q5_K": 0.625, "Q6_K": 0.75, "Q8_K": 1.0,
            # IQ quantization types - importance matrix quantization
            "IQ2_XXS": 0.25, "IQ2_XS": 0.25, "IQ3_XXS": 0.375,
            "IQ1_S": 0.125, "IQ4_NL": 0.5, "IQ3_S": 0.375,
            "IQ2_S": 0.25, "IQ4_XS": 0.5, "IQ1_M": 0.125,
            # Experimental types (approximated)
            "TQ1_0": 0.125, "TQ2_0": 0.25,
        }

        # Quantization quality hierarchy (lower index = higher quality)
        self.quantization_quality_hierarchy = [
            "F32", "F16", "BF16",           # Full precision
            "Q8_0", "Q8_1", "Q8_K",        # High quality quantization
            "Q6_K",                         # Medium-high quality
            "Q5_0", "Q5_1", "Q5_K",        # Medium quality
            "Q4_0", "Q4_1", "Q4_K",        # Standard quality
            "Q3_K",                         # Lower quality
            "Q2_K",                         # Low quality (policy floor)
            "IQ3_XXS",                      # Very low quality
            "IQ2_XS", "IQ2_XXS",            # Extremely low quality (below policy floor)
        ]

        # Compile regex patterns once for performance (used in suspicious pattern detection)
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns once during initialization for performance."""
        self._compiled_patterns = {}

        # Version string pattern for _is_likely_benign_content
        self._compiled_patterns["version_string"] = re.compile(r"^[0-9]+\.[0-9]+(\.[0-9]+)?([+-][a-zA-Z0-9.]+)?$")

        # Executable content patterns for _detect_executable_content
        # Convert suspicious patterns to compiled regex patterns
        self._compiled_patterns["executable_content"] = {}

        for category, patterns in self.suspicious_kv_patterns.items():
            compiled_category_patterns = []
            for pattern_str in patterns:
                try:
                    # Escape special regex characters and compile with case-insensitive matching
                    compiled_pattern = re.compile(re.escape(pattern_str), re.IGNORECASE)
                    compiled_category_patterns.append(compiled_pattern)
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{pattern_str}' in category '{category}': {e}")
                    # Skip invalid patterns instead of crashing
                    continue

            if compiled_category_patterns:  # Only add if we have valid patterns
                self._compiled_patterns["executable_content"][category] = compiled_category_patterns

        # SMART: Suspicious value patterns with word boundaries to reduce false positives
        self._compiled_patterns["suspicious_value"] = {}

        for category, tokens in self.suspicious_kv_patterns.items():
            compiled_patterns = []
            for token in tokens:
                try:
                    # Smart pattern creation: word boundaries for alphanumeric, raw for punctuation
                    if re.search(r"[A-Za-z0-9]", token):
                        # Alphanumeric token: use word boundaries to avoid "import"→"important" FPs
                        pattern = r"\b" + re.escape(token) + r"\b"
                    else:
                        # Punctuation-only token: use raw pattern for things like "../", "\\\\"
                        pattern = re.escape(token)

                    compiled_pattern = re.compile(pattern, re.IGNORECASE)
                    compiled_patterns.append(compiled_pattern)
                except re.error as e:
                    logger.warning(f"Bad suspicious token '{token}' in category '{category}': {e}")
                    # Skip invalid tokens instead of crashing
                    continue

            if compiled_patterns:  # Only add if we have valid patterns
                self._compiled_patterns["suspicious_value"][category] = compiled_patterns

    def can_validate(self, model_type: ModelType) -> bool:
        """This validator only handles GGUF format."""
        return model_type == ModelType.GGUF

    def _normalize_severity(self, severity_str: str) -> Severity:
        """Convert string severity to Severity enum for consistency."""
        severity_map = {
            "critical": Severity.CRITICAL,
            "high": Severity.HIGH,
            "medium": Severity.MEDIUM,
            "low": Severity.LOW,
            "info": Severity.LOW,  # Map info to low since INFO doesn't exist
        }
        return severity_map.get(severity_str.lower(), Severity.MEDIUM)


    def validate(self, data: bytes) -> List[Dict[str, Any]]:
        """CRITICAL: Validate GGUF file safety and integrity
        Main entry point for GGUF validation.
        """
        warnings = []

        try:
            # Validate GGUF header structure
            header_issues = self._validate_gguf_header(data)
            if header_issues:
                warnings.extend(header_issues)
                # If header is invalid, can't continue with detailed validation
                return self.warnings + warnings

            # Parse GGUF metadata
            metadata, tensor_info, metadata_end_offset = self._parse_gguf_metadata(data)
            if not metadata:
                warning = self.create_standard_warning(
                    warning_type="gguf_metadata_parse_error",
                    message="Failed to parse GGUF metadata - potentially malformed file",
                    severity=Severity.HIGH,
                    recommendation="Verify GGUF file integrity and regenerate if corrupted",
                    threat_type="file_corruption",
                    attack_vector="Malformed GGUF structure"
                )
                self.warnings.append(warning)
                return self.warnings + warnings

            # Validate KV metadata
            kv_issues = self._validate_kv_metadata(metadata)
            warnings.extend(kv_issues)

            # Check for suspicious KV keys
            suspicious_issues = self._check_suspicious_kv_keys(metadata)
            warnings.extend(suspicious_issues)

            # Validate architecture consistency
            arch_issues = self._validate_architecture_consistency(metadata)
            warnings.extend(arch_issues)

            # Validate tensor information
            tensor_issues = self._validate_tensor_info(tensor_info, data, metadata_end_offset)
            warnings.extend(tensor_issues)

            # Validate quantization types
            quant_issues = self._validate_quantization_types(tensor_info)
            warnings.extend(quant_issues)

            # REMOVED: Statistical analysis for supply chain simplification
            # Statistical tensor analysis is ML quality assessment, not security scanning

            # ENHANCED: Tensor layout validation with alignment, overlap, and bounds checking
            if self.enable_layout_validation:
                layout_issues = self._validate_tensor_layout(data, tensor_info, metadata_end_offset)
                warnings.extend(layout_issues)

            # FIXED: Layout consistency validation using real metadata end offset
            layout_consistency_issues = self._validate_metadata_layout_consistency(data, metadata_end_offset, tensor_info)
            warnings.extend(layout_consistency_issues)

        except Exception as e:
            logger.error(f"Error in GGUF safety validation: {str(e)}")
            warning = self.create_standard_warning(
                warning_type="gguf_analysis_error",
                message=f"Error during GGUF safety analysis: {str(e)}",
                severity=Severity.MEDIUM,
                recommendation="Manual review recommended due to analysis failure",
                error=str(e),
                threat_type="analysis_failure"
            )
            self.warnings.append(warning)

        all_warnings = self.warnings + warnings

        # Add GGUF-specific context for policy evaluation
        context = {
            "gguf": {
                "metadata": metadata if "metadata" in locals() else {},
                "tensor_count": len(tensor_info) if "tensor_info" in locals() and tensor_info else 0,
                "suspicious_metadata": any("suspicious" in str(w).lower() for w in all_warnings),
            },
        }

        # Apply policy evaluation if policy engine is available
        if self.policy_engine:
            # Use actual model path from metadata, fallback to empty string
            model_path = getattr(self.metadata, "path", "") if self.metadata else ""
            policy_result = self.apply_policy(all_warnings, model_path, context)
            return policy_result

        return all_warnings

    def validate_streaming(self, model_file: "ModelFile") -> List[Dict[str, Any]]:
        """Stream-based validation for large GGUF files.

        GGUF files have a structured format:
        1. Header (magic + version + metadata)
        2. Tensor data

        For streaming, we read the header first, then validate tensor data in chunks.
        """
        warnings = []

        try:
            # Read GGUF header first (metadata is at the beginning)
            header_data = model_file.read_header(max_header_size=10 * 1024 * 1024)  # Up to 10MB header

            # Validate header structure
            header_issues = self._validate_gguf_header(header_data)
            if header_issues:
                warnings.extend(header_issues)
                return warnings  # Can't continue without valid header

            # Parse metadata from header
            metadata, tensor_info, metadata_end_offset = self._parse_gguf_metadata(header_data)
            if not metadata:
                # Try to provide more context about the parsing failure
                pos = getattr(self, "_pos", 0)
                warnings.append(self.create_standard_warning(
                    "gguf_streaming_metadata_error",
                    f"Failed to parse GGUF metadata during streaming (stopped at byte {pos}). This may be due to large arrays or unsupported GGUF format extensions.",
                    Severity.MEDIUM,  # Reduced from HIGH since this might be recoverable
                    recommendation="Check if this is a valid GGUF file. Large vocabulary arrays (>500k elements) may cause parsing issues."
                ))
                # Continue with validation using whatever we could parse rather than stopping completely
                metadata = {}
                tensor_info = []

            # Validate metadata (header-only checks)
            kv_issues = self._validate_kv_metadata(metadata)
            warnings.extend(kv_issues)

            suspicious_issues = self._check_suspicious_kv_keys(metadata)
            warnings.extend(suspicious_issues)

            arch_issues = self._validate_architecture_consistency(metadata)
            warnings.extend(arch_issues)

            # For tensor validation, we'll use chunk-based processing
            # Store metadata for chunk validation
            model_file.set_context("gguf_metadata", metadata)
            model_file.set_context("gguf_tensor_info", tensor_info)
            model_file.set_context("gguf_metadata_end_offset", metadata_end_offset)
            
            # Validate quantization types (metadata-based)
            quant_issues = self._validate_quantization_types(tensor_info)
            warnings.extend(quant_issues)

            # Use base class streaming for tensor data
            chunk_warnings = super().validate_streaming(model_file)
            warnings.extend(chunk_warnings)

        except Exception as e:
            logger.error(f"Error in GGUF streaming validation: {str(e)}")
            warnings.append(self.create_standard_warning(
                "gguf_streaming_error",
                f"Error during GGUF streaming validation: {str(e)}",
                Severity.MEDIUM,
            ))

        return warnings

    def validate_chunk(self, chunk_info: "ChunkInfo", context: "StreamingContext") -> List[Dict[str, Any]]:
        """Validate a chunk of GGUF tensor data.

        For GGUF files, most validation is header/metadata based.
        Chunk validation focuses on:
        1. Basic integrity checks
        2. Tensor data bounds validation
        3. Suspicious patterns in tensor data
        """
        warnings = []

        try:
            # CRITICAL FIX: Only validate the first chunk (header) with header-specific validation
            # All other chunks should be treated as tensor data only
            if chunk_info.chunk_index == 0:
                # For the first chunk, only do header validation (no full GGUF parsing)
                chunk_data = chunk_info.data
                
                # Basic header validation without full GGUF parsing
                if len(chunk_data) >= 4:
                    magic = chunk_data[:4]
                    if magic != self.GGUF_MAGIC:
                        warnings.append(self.create_standard_warning(
                            "gguf_invalid_magic_chunk",
                            f"Invalid GGUF magic bytes in first chunk: {magic.hex()}",
                            Severity.HIGH,
                            chunk_offset=chunk_info.offset,
                        ))
            else:
                # For tensor data chunks, use Rust for pattern detection
                chunk_data = chunk_info.data

                # Check for suspicious patterns using Rust validator
                try:
                    from palisade._native import validate_gguf_safety
                    import multiprocessing
                    
                    num_cores = min(multiprocessing.cpu_count(), 4)
                    result = validate_gguf_safety(chunk_data, num_cores)
                    
                    if result.total_matches > 0:
                        # Build detailed warning with pattern information
                        pattern_details = []
                        if result.executable_patterns_found:
                            pattern_details.append(f"executable patterns: {len(result.executable_patterns_found)}")
                        if result.malicious_patterns_found:
                            pattern_details.append(f"malicious patterns: {len(result.malicious_patterns_found)}")
                        if result.suspicious_patterns_found:
                            pattern_details.append(f"suspicious patterns: {len(result.suspicious_patterns_found)}")
                        
                        warnings.append(self.create_standard_warning(
                            "gguf_suspicious_tensor_data",
                            f"Suspicious patterns detected in tensor data at offset {chunk_info.offset} ({', '.join(pattern_details)})",
                            Severity.MEDIUM,
                            chunk_offset=chunk_info.offset,
                            chunk_size=chunk_info.size,
                            total_matches=result.total_matches,
                            risk_score=result.risk_score
                        ))
                except Exception as e:
                    logger.debug(f"Error in Rust GGUF validation for chunk: {str(e)}")
                    # Fallback: just flag as suspicious without details
                    if self._detect_suspicious_tensor_patterns(chunk_data, chunk_info.offset):
                        warnings.append(self.create_standard_warning(
                            "gguf_suspicious_tensor_data",
                            f"Suspicious patterns detected in tensor data at offset {chunk_info.offset}",
                            Severity.MEDIUM,
                            chunk_offset=chunk_info.offset,
                            chunk_size=chunk_info.size,
                        ))

                # Validate chunk alignment for tensor boundaries
                # Try to get the actual metadata end offset from the streaming context
                metadata_end_offset = 0
                if hasattr(context, 'validation_results') and context.validation_results:
                    metadata_end_offset = context.validation_results.get("gguf_metadata_end_offset", 0)
                
                # If we don't have the actual offset, use a reasonable estimate
                if metadata_end_offset == 0:
                    metadata_end_offset = 1024 * 1024  # 1MB estimate for metadata
                
                if chunk_info.offset > metadata_end_offset:
                    alignment_issues = self._validate_chunk_alignment(chunk_info, metadata_end_offset)
                    warnings.extend(alignment_issues)

        except Exception as e:
            logger.debug(f"Error validating GGUF chunk at offset {chunk_info.offset}: {str(e)}")
            warnings.append(self.create_standard_warning(
                "gguf_chunk_validation_error",
                f"Error validating chunk at offset {chunk_info.offset}: {str(e)}",
                Severity.LOW,
                chunk_offset=chunk_info.offset,
            ))

        return warnings

    def _detect_suspicious_tensor_patterns(self, data: bytes, offset: int) -> bool:
        """Check for suspicious patterns in tensor data chunks using Rust validator."""
        try:
            # Use Rust for fast pattern matching (GIL-free)
            from palisade._native import validate_gguf_safety
            import multiprocessing
            
            num_cores = min(multiprocessing.cpu_count(), 4)  # Limit cores for chunk validation
            
            # Validate chunk with Rust
            result = validate_gguf_safety(data, num_cores)
            
            # Return True if any patterns found
            return result.total_matches > 0

        except Exception as e:
            logger.debug(f"Error in Rust GGUF pattern detection: {str(e)}")
            return False

    def _validate_chunk_alignment(self, chunk_info: "ChunkInfo", metadata_end_offset: int) -> List[Dict[str, Any]]:
        """Validate tensor data chunk alignment."""
        warnings = []

        try:
            # Check if chunk starts at proper tensor boundary
            tensor_data_start = chunk_info.offset - metadata_end_offset

            # GGUF tensors should be aligned to 32-byte boundaries
            if tensor_data_start % 32 != 0 and chunk_info.offset == metadata_end_offset:
                warnings.append(self.create_standard_warning(
                    "gguf_tensor_alignment_warning",
                    f"Tensor data not aligned to 32-byte boundary at offset {chunk_info.offset}",
                    Severity.LOW,
                    tensor_offset=tensor_data_start,
                    expected_alignment=32,
                ))

        except Exception as e:
            logger.debug(f"Error checking chunk alignment: {str(e)}")

        return warnings

    def _validate_gguf_header(self, data: bytes) -> List[Dict[str, Any]]:
        """ENHANCED HEADER VALIDATION: Version-gated feature validation and layout consistency.

        Validates:
        - GGUF magic bytes and version compatibility
        - Version-specific feature gating (KV encodings, arrays, etc.)
        - Header structure and count validation
        - KV/tensor table layout consistency
        """
        warnings = []

        if len(data) < 24:  # Minimum header size (magic + version + tensor_count + kv_count)
            warnings.append(self.create_standard_warning(
                "gguf_file_too_small",
                "File too small to contain complete GGUF header",
                Severity.CRITICAL,
                "Verify file integrity",
                size=len(data),
                minimum_size=24,
            ))
            return warnings

        try:
            # Check magic bytes
            magic = data[:4]
            if magic != self.GGUF_MAGIC:
                warnings.append({
                    "type": "gguf_invalid_magic",
                    "severity": self._normalize_severity("critical").value,
                    "details": {
                        "message": "Invalid GGUF magic bytes",
                        "expected": self.GGUF_MAGIC.decode("ascii"),
                        "actual": magic.hex(),
                        "recommendation": "File may be corrupted or not a valid GGUF file",
                    },
                })
                return warnings

            # ENHANCED: Parse version and store for feature gating
            version = struct.unpack("<I", data[4:8])[0]
            self.gguf_file_version = version  # Store for later reference in error messages

            # ENHANCED: Version-specific validation with feature gating
            version_issues = self._validate_gguf_version_compatibility(version)
            warnings.extend(version_issues)

            # If version is completely unsupported, stop further parsing
            if version < 1 or version > 10:  # Reasonable version bounds
                warnings.append({
                    "type": "gguf_version_incompatible",
                    "details": {
                        "message": f"GGUF version {version} is incompatible",
                        "version": version,
                        "supported_range": "1-10",
                        "recommendation": "File uses unsupported GGUF version",
                    },
                    "severity": self._normalize_severity("critical").value,
                })
                return warnings

            # Parse counts for layout validation
            tensor_count = struct.unpack("<Q", data[8:16])[0]
            kv_count = struct.unpack("<Q", data[16:24])[0]

            # Enhanced count validation
            count_issues = self._validate_gguf_counts(tensor_count, kv_count, version)
            warnings.extend(count_issues)

        except struct.error as e:
            warnings.append({
                "type": "gguf_header_parse_error",
                "details": {
                    "message": "Error parsing GGUF header",
                    "error": str(e),
                    "recommendation": "File may be corrupted",
                },
                "severity": self._normalize_severity("high").value,
            })

        return warnings

    def _validate_gguf_version_compatibility(self, version: int) -> List[Dict[str, Any]]:
        """ENHANCED: Version-gated feature validation.

        Gates specific features based on GGUF version:
        - Version 1: Basic KV pairs, limited array support
        - Version 2: Enhanced arrays, nested structures
        - Version 3+: Advanced KV encodings, extended metadata
        """
        warnings = []

        # Define version capabilities using actual GGUF_VALUE_TYPES constants
        basic_types = {
            GGUF_VALUE_TYPES["UINT8"], GGUF_VALUE_TYPES["INT8"],
            GGUF_VALUE_TYPES["UINT16"], GGUF_VALUE_TYPES["INT16"],
            GGUF_VALUE_TYPES["UINT32"], GGUF_VALUE_TYPES["INT32"],
            GGUF_VALUE_TYPES["FLOAT32"], GGUF_VALUE_TYPES["BOOL"],
            GGUF_VALUE_TYPES["STRING"], GGUF_VALUE_TYPES["UINT64"],
            GGUF_VALUE_TYPES["INT64"], GGUF_VALUE_TYPES["FLOAT64"],
        }

        version_features = {
            1: {
                "supported_kv_types": basic_types,  # Basic types (no arrays)
                "array_support": "limited",
                "nested_structures": False,
                "extended_metadata": False,
            },
            2: {
                "supported_kv_types": basic_types | {GGUF_VALUE_TYPES["ARRAY"]},  # + arrays
                "array_support": "full",
                "nested_structures": True,
                "extended_metadata": False,
            },
            3: {
                "supported_kv_types": basic_types | {GGUF_VALUE_TYPES["ARRAY"]},  # All defined types
                "array_support": "full",
                "nested_structures": True,
                "extended_metadata": True,
            },
        }

        # Store supported features for this version
        if version in version_features:
            self.version_features = version_features[version]
        else:
            # Unknown version - assume latest capabilities but warn
            self.version_features = version_features.get(3, version_features[1])
            warnings.append({
                "type": "gguf_unknown_version_features",
                "details": {
                    "message": f"Unknown GGUF version {version} - assuming latest feature set",
                    "version": version,
                    "assumed_features": "version_3_capabilities",
                    "recommendation": "Verify version-specific features are used correctly",
                },
                "severity": self._normalize_severity("medium").value,
            })

        # Version-specific warnings
        if version > self.GGUF_VERSION:
            warnings.append({
                "type": "gguf_newer_version_detected",
                "details": {
                    "message": f"GGUF version {version} is newer than supported version {self.GGUF_VERSION}",
                    "detected_version": version,
                    "supported_version": self.GGUF_VERSION,
                    "potential_issues": [
                        "May contain unsupported KV value types",
                        "Extended metadata may not parse correctly",
                        "New array encoding formats may be present",
                    ],
                    "recommendation": "Update scanner to support newer GGUF versions",
                },
                "severity": self._normalize_severity("high").value,
            })
        elif version < 2 and version >= 1:
            warnings.append({
                "type": "gguf_legacy_version_detected",
                "details": {
                    "message": f"GGUF version {version} is legacy - limited feature support",
                    "version": version,
                    "limitations": [
                        "Limited array support",
                        "No nested structures",
                        "Basic KV types only",
                    ],
                    "recommendation": "Consider upgrading to newer GGUF version for full features",
                },
                "severity": self._normalize_severity("low").value,
            })

        return warnings

    def _validate_gguf_counts(self, tensor_count: int, kv_count: int, version: int) -> List[Dict[str, Any]]:
        """Enhanced count validation with version-specific limits."""
        warnings = []

        # Version-specific limits
        version_limits = {
            1: {"max_tensors": 50000, "max_kv_pairs": 1000},
            2: {"max_tensors": 100000, "max_kv_pairs": 5000},
            3: {"max_tensors": 200000, "max_kv_pairs": 10000},
        }

        limits = version_limits.get(version, version_limits[3])

        # Validate tensor count
        if tensor_count > limits["max_tensors"]:
            warnings.append({
                "type": "gguf_excessive_tensor_count",
                "details": {
                    "message": f"Tensor count {tensor_count} exceeds version {version} limits",
                    "tensor_count": tensor_count,
                    "version_limit": limits["max_tensors"],
                    "version": version,
                    "recommendation": "Verify file integrity - may be corrupted or malicious",
                },
                "severity": self._normalize_severity("high").value,
            })
        elif tensor_count == 0:
            warnings.append({
                "type": "gguf_zero_tensor_count",
                "details": {
                    "message": "GGUF file contains no tensors",
                    "tensor_count": tensor_count,
                    "recommendation": "File may be metadata-only or corrupted",
                },
                "severity": self._normalize_severity("medium").value,
            })

        # Validate KV count
        if kv_count > limits["max_kv_pairs"]:
            warnings.append({
                "type": "gguf_excessive_kv_count",
                "details": {
                    "message": f"KV pair count {kv_count} exceeds version {version} limits",
                    "kv_count": kv_count,
                    "version_limit": limits["max_kv_pairs"],
                    "version": version,
                    "recommendation": "Verify metadata integrity",
                },
                "severity": self._normalize_severity("high").value,
            })
        elif kv_count == 0:
            warnings.append({
                "type": "gguf_zero_kv_count",
                "details": {
                    "message": "GGUF file contains no metadata KV pairs",
                    "kv_count": kv_count,
                    "recommendation": "File missing required metadata",
                },
                "severity": self._normalize_severity("high").value,
            })

        return warnings

    def _validate_metadata_layout_consistency(self, data: bytes, metadata_end_offset: int,
                                            tensor_info: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """FIXED: Validate layout consistency using the actual metadata end offset from parsing.

        This method uses the exact offset returned by _parse_gguf_metadata instead of
        incorrectly estimating it with tensor_count * 32.
        """
        warnings = []

        if not tensor_info:
            return warnings

        try:
            # Find actual first tensor data offset (minimum offset, not iteration order)
            first_tensor_data_offset = None

            # Get minimum tensor offset from all tensors with valid offsets
            valid_offsets = [t.get("offset") for t in tensor_info if t.get("offset") is not None]
            if valid_offsets:
                min_tensor_offset = min(valid_offsets)
                # The tensor offset is relative to the end of metadata
                first_tensor_data_offset = metadata_end_offset + min_tensor_offset

            if first_tensor_data_offset is not None:
                # Check if there's an unexpected gap between metadata end and first tensor
                if first_tensor_data_offset > metadata_end_offset:
                    gap_size = first_tensor_data_offset - metadata_end_offset

                    # Only flag significant gaps (>1KB) as these might indicate layout issues
                    if gap_size > 1024:
                        warnings.append({
                            "type": "gguf_metadata_tensor_gap",
                            "details": {
                                "message": "Large gap detected between metadata end and first tensor data",
                                "metadata_end_offset": metadata_end_offset,
                                "first_tensor_data_offset": first_tensor_data_offset,
                                "gap_size": gap_size,
                                "recommendation": "Verify GGUF layout - large gaps may indicate corruption or non-standard formatting",
                            },
                            "severity": self._normalize_severity("medium").value,
                        })
                elif first_tensor_data_offset < metadata_end_offset:
                    # This would indicate a serious layout problem - tensor overlaps metadata
                    warnings.append({
                        "type": "gguf_tensor_metadata_overlap",
                        "details": {
                            "message": "Critical: Tensor data overlaps with metadata section",
                            "metadata_end_offset": metadata_end_offset,
                            "first_tensor_data_offset": first_tensor_data_offset,
                            "overlap_size": metadata_end_offset - first_tensor_data_offset,
                            "recommendation": "CRITICAL: File layout corruption detected - metadata and tensor data overlap",
                        },
                        "severity": self._normalize_severity("critical").value,
                    })

            # Check if metadata end is reasonable compared to file size
            file_size = len(data)
            metadata_ratio = metadata_end_offset / file_size if file_size > 0 else 0

            if metadata_ratio > 0.5:  # Metadata takes up >50% of file
                warnings.append({
                    "type": "gguf_excessive_metadata_size",
                    "details": {
                        "message": "Metadata section is unusually large compared to file size",
                        "metadata_end_offset": metadata_end_offset,
                        "file_size": file_size,
                        "metadata_percentage": f"{metadata_ratio * 100:.1f}%",
                        "recommendation": "Verify file structure - metadata should not dominate file size",
                    },
                    "severity": self._normalize_severity("medium").value,
                })

        except Exception as e:
            warnings.append({
                "type": "gguf_metadata_layout_validation_error",
                "details": {
                    "message": "Error validating metadata layout consistency",
                    "error": str(e),
                    "recommendation": "Layout validation failed - possible file corruption",
                },
                "severity": self._normalize_severity("medium").value,
            })

        return warnings

    def _parse_gguf_metadata(self, data: bytes) -> Tuple[Optional[Dict[str, Any]], Optional[List[Dict[str, Any]]], int]:
        """Parse GGUF metadata and tensor information with bounds-safe parsing."""
        try:
            # FIXED: Use memoryview for bounds-safe parsing without copies
            buf = memoryview(data)
            self._pos = 0

            # Skip magic and version
            self._pos += 4 + 4

            # Read tensor count and kv count using bounds-safe reading
            tensor_count = self._read(buf, "<Q")
            kv_count = self._read(buf, "<Q")

            # Parse KV metadata with error recovery
            kv_metadata = {}
            for i in range(kv_count):
                try:
                    key, value = self._parse_kv_pair_safe(buf)
                    if key is None:
                        logger.debug(f"Failed to parse KV pair {i+1}/{kv_count} at position {self._pos}")
                        # Return what we have so far instead of complete failure
                        logger.debug(f"Successfully parsed {len(kv_metadata)} KV pairs before failure")
                        return kv_metadata if kv_metadata else None, [], self._pos
                    kv_metadata[key] = value
                except Exception as e:
                    logger.debug(f"Exception parsing KV pair {i+1}/{kv_count}: {str(e)}")
                    # If we have some metadata, return it; otherwise fail
                    if kv_metadata:
                        logger.debug(f"Partial KV metadata parsed ({len(kv_metadata)} pairs) before error")
                        return kv_metadata, [], self._pos
                    return None, None, self._pos

            # Parse tensor info with error recovery
            tensor_info = []
            for i in range(tensor_count):
                try:
                    tensor = self._parse_tensor_info_safe(buf)
                    if tensor is None:
                        logger.debug(f"Failed to parse tensor {i+1}/{tensor_count} at position {self._pos}")
                        # Return what we have parsed so far
                        logger.debug(f"Successfully parsed {len(tensor_info)} tensors before failure")
                        return kv_metadata, tensor_info, self._pos
                    tensor_info.append(tensor)
                except Exception as e:
                    logger.debug(f"Exception parsing tensor {i+1}/{tensor_count}: {str(e)}")
                    # Return partial results
                    logger.debug(f"Partial tensor info parsed ({len(tensor_info)} tensors) before error")
                    return kv_metadata, tensor_info, self._pos

            return kv_metadata, tensor_info, self._pos

        except ValueError as e:
            logger.debug(f"Bounds error parsing GGUF metadata: {str(e)}")
            return None, None, getattr(self, "_pos", 0)
        except Exception as e:
            logger.debug(f"Error parsing GGUF metadata: {str(e)}")
            return None, None, getattr(self, "_pos", 0)

    def _read(self, buf: memoryview, fmt: str) -> tuple:
        """FIXED: Bounds-safe reading using memoryview + struct.unpack_from.

        Avoids slicing and provides guaranteed bounds checking for all reads
        """
        size = struct.calcsize(fmt)
        buf_len = len(buf)  # SECURITY: Capture length once to prevent TOCTOU
        if self._pos + size > buf_len:
            msg = f"GGUF: truncated while reading {fmt} at position {self._pos} (need {size} bytes, have {buf_len - self._pos})"
            raise ValueError(msg)

        result = struct.unpack_from(fmt, buf, self._pos)
        self._pos += size
        return result[0] if len(result) == 1 else result

    def _read_bytes(self, buf: memoryview, length: int) -> bytes:
        """FIXED: Bounds-safe byte reading using memoryview."""
        buf_len = len(buf)  # SECURITY: Capture length once to prevent TOCTOU
        if self._pos + length > buf_len:
            msg = f"GGUF: truncated while reading {length} bytes at position {self._pos} (have {buf_len - self._pos})"
            raise ValueError(msg)

        result = buf[self._pos:self._pos + length].tobytes()
        self._pos += length
        return result

    def _skip_gguf_value(self, buf: memoryview, value_type: int) -> None:
        """Fast skip GGUF value without materializing, ensuring cursor advancement."""
        # Primitives - just consume the bytes
        if value_type == self.GGUF_TYPE_UINT8:
            self._read(buf, "<B")
            return
        if value_type == self.GGUF_TYPE_INT8:
            self._read(buf, "<b")
            return
        if value_type == self.GGUF_TYPE_UINT16:
            self._read(buf, "<H")
            return
        if value_type == self.GGUF_TYPE_INT16:
            self._read(buf, "<h")
            return
        if value_type == self.GGUF_TYPE_UINT32:
            self._read(buf, "<I")
            return
        if value_type == self.GGUF_TYPE_INT32:
            self._read(buf, "<i")
            return
        if value_type == self.GGUF_TYPE_UINT64:
            self._read(buf, "<Q")
            return
        if value_type == self.GGUF_TYPE_INT64:
            self._read(buf, "<q")
            return
        if value_type == self.GGUF_TYPE_FLOAT32:
            self._read(buf, "<f")
            return
        if value_type == self.GGUF_TYPE_FLOAT64:
            self._read(buf, "<d")
            return
        if value_type == self.GGUF_TYPE_BOOL:
            self._read(buf, "<B")
            return

        if value_type == self.GGUF_TYPE_STRING:
            # Read string length then skip the payload
            n = self._read(buf, "<Q")
            self._read_bytes(buf, n)  # consume payload without storing
            return

        if value_type == self.GGUF_TYPE_ARRAY:
            # Read array header then recursively skip elements
            elem_type = self._read(buf, "<I")
            length = self._read(buf, "<Q")
            # Recursively skip each element (don't materialize)
            for _ in range(length):
                self._skip_gguf_value(buf, elem_type)
            return

        # Unknown type: best effort—treat as fatal parse error
        msg = f"Unknown GGUF value type: {value_type}"
        raise ValueError(msg)

    def _parse_kv_pair_safe(self, buf: memoryview) -> Tuple[Optional[str], Any]:
        """FIXED: Bounds-safe KV pair parsing using memoryview."""
        try:
            # Parse key length and validate
            key_length = self._read(buf, "<Q")

            if key_length > 1000:  # Sanity check
                logger.debug(f"KV key length {key_length} exceeds maximum (1000)")
                return None, None

            # Read key data using bounds-safe method
            key_bytes = self._read_bytes(buf, key_length)
            key = key_bytes.decode("utf-8", errors="strict")

            # Parse value type
            value_type = self._read(buf, "<I")

            # Parse value using bounds-safe method
            value = self._parse_gguf_value_safe(buf, value_type)

            # If value parsing failed (returned None), abort KV parsing
            if value is None:
                logger.debug(f"Failed to parse value for key '{key}' - aborting KV parsing")
                return None, None

            return key, value

        except (ValueError, UnicodeDecodeError, struct.error) as e:
            logger.debug(f"Error parsing KV pair: {str(e)}")
            return None, None

    def _parse_tensor_info_safe(self, buf: memoryview) -> Optional[Dict[str, Any]]:
        """FIXED: Bounds-safe tensor info parsing using memoryview."""
        try:
            # Parse tensor name length and validate
            name_length = self._read(buf, "<Q")

            if name_length > 1000:  # Sanity check
                logger.debug(f"Tensor name length {name_length} exceeds maximum (1000)")
                return None

            # Read tensor name
            name_bytes = self._read_bytes(buf, name_length)
            name = name_bytes.decode("utf-8", errors="strict")

            # Parse dimensions
            n_dims = self._read(buf, "<I")

            if n_dims > 10:  # Sanity check
                logger.debug(f"Tensor dimensions {n_dims} exceeds maximum (10)")
                return None

            dims = []
            for _ in range(n_dims):
                dim = self._read(buf, "<Q")
                dims.append(dim)

            # Parse type and offset
            tensor_type = self._read(buf, "<I")
            tensor_offset = self._read(buf, "<Q")

            return {
                "name": name,
                "dims": dims,
                "type": tensor_type,
                "offset": tensor_offset,
            }

        except (ValueError, UnicodeDecodeError, struct.error) as e:
            logger.debug(f"Error parsing tensor info: {str(e)}")
            return None

    def _parse_gguf_value_safe(self, buf: memoryview, value_type: int) -> Any:
        """FIXED: Bounds-safe GGUF value parsing using memoryview + struct.unpack_from.

        Completely eliminates buffer slicing and provides guaranteed bounds checking
        """
        # CRITICAL SECURITY FIX: Prevent stack overflow attacks through recursive parsing
        depth_incremented = False  # Initialize tracking variable
        if self._recursion_depth >= self._max_recursion_depth:
            msg = f"SECURITY: Maximum recursion depth ({self._max_recursion_depth}) exceeded - potential attack"
            raise ValueError(msg)

        self._recursion_depth += 1
        depth_incremented = True  # Mark that we incremented for safe cleanup
        try:
            return self._parse_value_by_type(buf, value_type)

        except ValueError as e:
            logger.debug(f"Bounds error parsing GGUF value: {str(e)}")
            return f"PARSE_ERROR_BOUNDS_{str(e)}"
        except Exception as e:
            logger.debug(f"Error parsing GGUF value: {str(e)}")
            return f"PARSE_ERROR_{str(e)}"
        finally:
            # CRITICAL SECURITY: Only decrement if we actually incremented
            if depth_incremented:
                self._recursion_depth -= 1

    def _parse_value_by_type(self, buf: memoryview, value_type: int) -> Any:
        """Parse GGUF value by type - broken out from main method for maintainability.

        CRITICAL: This method assumes version checking and recursion depth have already been handled
        """
        # ENHANCED: Version-gated KV type validation with policy-driven unknown type handling
        version_features = getattr(self, "version_features", None)
        if version_features and not self._is_supported_type(value_type, version_features):
            return self._handle_unsupported_type(buf, value_type)

        # Primitive types
        if value_type in self._get_primitive_type_handlers():
            return self._parse_primitive_type(buf, value_type)

        # Complex types
        elif value_type == self.GGUF_TYPE_STRING:
            return self._parse_string_safe(buf)
        elif value_type == self.GGUF_TYPE_ARRAY:
            return self._parse_array_safe(buf, version_features)
        else:
            # Unknown type - handle with policy
            return self._handle_unknown_type(buf, value_type)

    def _is_supported_type(self, value_type: int, version_features: dict) -> bool:
        """Check if type is supported in current GGUF version."""
        supported_types = version_features.get("supported_kv_types", set())
        return value_type in supported_types

    def _handle_unsupported_type(self, buf: memoryview, value_type: int) -> Any:
        """Handle unsupported types based on policy."""
        unknown_policy = getattr(self, "unknown_type_policy", "warn")
        version = getattr(self, "gguf_file_version", "unknown")

        if unknown_policy == "error":
            logger.warning(f"KV value type {value_type} not supported in GGUF version {version} - aborting parse")
            return None  # Only abort if policy is strict

        # For "warn" or "ignore", skip the unknown value gracefully
        if unknown_policy == "warn":
            logger.warning(f"KV value type {value_type} not supported in GGUF version {version} - skipping")
        elif unknown_policy == "ignore":
            logger.debug(f"KV value type {value_type} not supported in GGUF version {version} - skipping silently")

        # Skip the unknown value to maintain cursor alignment
        try:
            self._skip_gguf_value(buf, value_type)
            return f"UNSUPPORTED_TYPE_{value_type}"  # Sentinel value
        except Exception as e:
            logger.error(f"Failed to skip unsupported type {value_type}: {e}")
            return None  # Fall back to aborting if we can't skip safely

    def _get_primitive_type_handlers(self) -> set:
        """Get set of primitive type IDs that can be handled directly."""
        return {
            self.GGUF_TYPE_UINT8, self.GGUF_TYPE_INT8, self.GGUF_TYPE_UINT16,
            self.GGUF_TYPE_INT16, self.GGUF_TYPE_UINT32, self.GGUF_TYPE_INT32,
            self.GGUF_TYPE_FLOAT32, self.GGUF_TYPE_UINT64, self.GGUF_TYPE_INT64,
            self.GGUF_TYPE_FLOAT64, self.GGUF_TYPE_BOOL,
        }

    def _parse_primitive_type(self, buf: memoryview, value_type: int) -> Any:
        """Parse primitive GGUF types using bounds-safe _read method."""
        type_format_map = {
            self.GGUF_TYPE_UINT8: "<B",
            self.GGUF_TYPE_INT8: "<b",
            self.GGUF_TYPE_UINT16: "<H",
            self.GGUF_TYPE_INT16: "<h",
            self.GGUF_TYPE_UINT32: "<I",
            self.GGUF_TYPE_INT32: "<i",
            self.GGUF_TYPE_FLOAT32: "<f",
            self.GGUF_TYPE_UINT64: "<Q",
            self.GGUF_TYPE_INT64: "<q",
            self.GGUF_TYPE_FLOAT64: "<d",
        }

        if value_type == self.GGUF_TYPE_BOOL:
            return self._read(buf, "<B") != 0
        elif value_type in type_format_map:
            return self._read(buf, type_format_map[value_type])
        else:
            msg = f"Unknown primitive type {value_type}"
            raise ValueError(msg)

    def _parse_string_safe(self, buf: memoryview) -> str:
        """Parse GGUF string with security bounds checking."""
        str_length = self._read(buf, "<Q")

        # CRITICAL SECURITY FIX: Prevent memory exhaustion attacks
        if str_length > self.MAX_SAFE_STRING_LENGTH:
            logger.error(f"SECURITY: String length {str_length} exceeds safe maximum ({self.MAX_SAFE_STRING_LENGTH}) - potential attack")
            # FIXED: Skip the data without reading it to prevent memory exhaustion
            if self._pos + str_length > len(buf):
                msg = f"GGUF: oversized string extends beyond buffer (pos={self._pos}, str_len={str_length}, buf_len={len(buf)})"
                raise ValueError(msg)
            self._pos += str_length  # Skip the string data
            return f"STRING_TOO_LONG_{str_length}"

        # Additional safety check for potential integer overflow
        if str_length < 0:
            msg = f"GGUF: negative string length {str_length} - corrupted data"
            raise ValueError(msg)

        try:
            string_bytes = self._read_bytes(buf, str_length)
            return string_bytes.decode("utf-8", errors="strict")
        except UnicodeDecodeError as e:
            logger.debug(f"Invalid UTF-8 in string: {str(e)}")
            # Fall back to error-tolerant decoding but flag it
            return f"STRING_INVALID_UTF8_{string_bytes.decode('utf-8', errors='replace')[:50]}"

    def _parse_array_safe(self, buf: memoryview, version_features: Optional[dict]) -> Any:
        """Parse GGUF array with security bounds checking."""
        # ENHANCED: Version-gated array support validation
        if version_features:
            array_support = version_features.get("array_support", "none")
            if array_support == "none":
                return self._handle_unsupported_array(buf)
            elif array_support == "limited":
                logger.debug(f"Limited array support in GGUF version {getattr(self, 'gguf_file_version', 'unknown')}")

        # FIXED: Bounds-safe array parsing
        array_type = self._read(buf, "<I")
        array_length = self._read(buf, "<Q")

        # CRITICAL SECURITY FIX: Prevent DoS attacks through oversized arrays
        # FIXED: Check for unreasonably large values (0xFFFFFFFFFFFFFFFF would be suspicious)
        # Since array_length is unsigned 64-bit, negative values wrap to very large positive
        # Only treat as attack if extremely large (likely malicious) vs legitimate large vocab arrays
        if array_length > 2**50 or array_length > self.MAX_SAFE_ARRAY_LENGTH * 10:  # Much higher threshold for actual attacks
            return self._handle_oversized_array(buf, array_type, array_length)
        elif array_length > self.MAX_SAFE_ARRAY_LENGTH:
            # Log but continue processing for moderate oversize (likely legitimate)
            logger.debug(f"Large array with {array_length} elements (>{self.MAX_SAFE_ARRAY_LENGTH}) - processing with care")

        # Version-specific array element type validation
        if version_features and not self._is_supported_type(array_type, version_features):
            return self._handle_unsupported_array_elements(buf, array_type, array_length)

        return self._parse_array_elements(buf, array_type, array_length)

    def _handle_unsupported_array(self, buf: memoryview) -> str:
        """Handle arrays not supported in current GGUF version."""
        unknown_policy = getattr(self, "unknown_type_policy", "warn")
        version = getattr(self, "gguf_file_version", "unknown")

        if unknown_policy == "error":
            logger.warning(f"Array type not supported in GGUF version {version} - aborting parse")
            return None  # Only abort if policy is strict

        # For "warn" or "ignore", skip the array gracefully
        if unknown_policy == "warn":
            logger.warning(f"Array type not supported in GGUF version {version} - skipping")
        elif unknown_policy == "ignore":
            logger.debug(f"Array type not supported in GGUF version {version} - skipping silently")

        # Skip the array to maintain cursor alignment
        try:
            self._skip_gguf_value(buf, self.GGUF_TYPE_ARRAY)
            return f"UNSUPPORTED_ARRAY_{version}"
        except Exception as e:
            logger.error(f"Failed to skip unsupported array: {e}")
            return None  # Fall back to aborting if we can't skip safely

    def _handle_oversized_array(self, buf: memoryview, array_type: int, array_length: int) -> str:
        """Handle oversized arrays that could cause DoS attacks."""
        logger.warning(f"SECURITY: Array length {array_length} is extremely large - potential DoS attack, skipping safely")

        # FIXED: Calculate total skip size instead of iterating billions of times
        element_size = self._get_element_size_for_skip(array_type)
        if element_size is not None:
            total_skip_bytes = array_length * element_size
            # SECURITY: Prevent integer overflow and buffer overrun
            if total_skip_bytes < 0 or self._pos + total_skip_bytes > len(buf):
                logger.error(f"GGUF: oversized array ({array_length} elements) extends beyond buffer - likely malicious")
                # Skip to end of buffer to prevent further parsing attempts
                self._pos = len(buf)
                return f"MALICIOUS_ARRAY_{array_length}"
            self._pos += total_skip_bytes
        else:
            # For complex types, try to skip array header and log warning
            logger.warning(f"GGUF: cannot safely skip oversized array with complex element type {array_type} - stopping parse")
            return None  # Signal parsing should stop
        return f"ARRAY_TOO_LONG_{array_length}"

    def _handle_unsupported_array_elements(self, buf: memoryview, array_type: int, array_length: int) -> str:
        """Handle arrays with unsupported element types."""
        unknown_policy = getattr(self, "unknown_type_policy", "warn")

        if unknown_policy == "error":
            logger.debug(f"Array element type {array_type} not supported - aborting parse")
            return None  # Only abort if policy is strict

        # For "warn" or "ignore", skip the array gracefully
        if unknown_policy == "warn":
            logger.warning(f"Array element type {array_type} not supported - skipping array")
        elif unknown_policy == "ignore":
            logger.debug(f"Array element type {array_type} not supported - skipping array silently")

        # CRITICAL: Must skip all elements to keep cursor aligned
        try:
            for _ in range(array_length):
                self._skip_gguf_value(buf, array_type)
            return f"ARRAY_ELEMENT_TYPE_{array_type}_UNSUPPORTED"
        except Exception as e:
            logger.error(f"Failed to skip array elements with unsupported type {array_type}: {e}")
            return None  # Fall back to aborting if we can't skip safely

    def _parse_array_elements(self, buf: memoryview, array_type: int, array_length: int) -> list:
        """Parse array elements safely with memory limits."""
        array_values = []
        max_materialized = self.MAX_ARRAY_ELEMENTS_MATERIALIZED  # Only keep limited elements in memory

        # Parse ALL elements to ensure cursor advances correctly
        for i in range(array_length):
            try:
                value = self._parse_gguf_value_safe(buf, array_type)
                # Only keep first max_materialized elements to avoid memory issues
                if i < max_materialized:
                    array_values.append(value)
                # For elements beyond max_materialized, we still parse to advance cursor
                # but don't store the value (it's discarded)
            except Exception as e:
                logger.debug(f"Error parsing array element {i}: {str(e)}")
                # If we can't parse an element, we can't continue parsing the array
                # This is a fatal error since we can't advance the cursor properly
                return f"ARRAY_PARSE_ERROR_AT_ELEMENT_{i}"

        return array_values

    def _handle_unknown_type(self, buf: memoryview, value_type: int) -> Any:
        """Handle unknown GGUF value types with policy-driven behavior."""
        unknown_policy = getattr(self, "unknown_type_policy", "warn")
        version = getattr(self, "gguf_file_version", "unknown")

        if unknown_policy == "error":
            logger.debug(f"Unknown GGUF value type: {value_type} in version {version} - aborting parse")
            return None  # Only abort if policy is strict

        # For "warn" or "ignore", skip the unknown value gracefully
        if unknown_policy == "warn":
            logger.warning(f"Unknown GGUF value type: {value_type} in version {version} - skipping")
        elif unknown_policy == "ignore":
            logger.debug(f"Unknown GGUF value type: {value_type} in version {version} - skipping silently")

        # Skip the unknown value to maintain cursor alignment
        try:
            self._skip_gguf_value(buf, value_type)
            return f"UNSUPPORTED_TYPE_{value_type}"  # Sentinel value
        except Exception as e:
            logger.error(f"Failed to skip unsupported type {value_type}: {e}")
            return None  # Fall back to aborting if we can't skip safely

    def _validate_kv_metadata(self, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """ENHANCED: Validate KV metadata with policy-driven strictness levels.

        Enforcement based on metadata_strictness:
        - low: Only critical architecture key
        - medium: General + architecture-specific required keys
        - high: Comprehensive expected_kv_keys validation
        """
        warnings = []

        # REALISTIC: Apply metadata strictness policy with required vs recommended distinction
        required_keys = []
        recommended_keys = []

        if self.metadata_strictness == "low":
            # Minimal validation - only absolutely critical keys
            required_keys.extend(self.required_kv_keys["critical"])
        elif self.metadata_strictness == "medium":
            # Standard validation - critical + important keys
            required_keys.extend(self.required_kv_keys["critical"])
            required_keys.extend(self.required_kv_keys["important"])
            # Add some recommended keys for info (but don't fail on missing)
            for category_keys in self.recommended_kv_keys.values():
                recommended_keys.extend(list(category_keys)[:2])  # Just first 2 from each category
        else:  # high strictness
            # Comprehensive validation - required + important + some recommended
            required_keys.extend(self.required_kv_keys["critical"])
            required_keys.extend(self.required_kv_keys["important"])
            # Add general metadata and architecture-specific as required in high mode
            recommended_keys.extend(self.recommended_kv_keys["general_metadata"])
            recommended_keys.extend(self.recommended_kv_keys["architecture_specific"])

        # Check for missing truly required metadata
        missing_required = [key for key in required_keys if key not in metadata]

        if missing_required:
            # Only generate warnings for truly required keys
            severity = self._normalize_severity("high" if self.metadata_strictness == "high" else "medium").value  # Reduced severity
            warnings.append({
                "type": "gguf_missing_required_metadata",
                "details": {
                    "message": f"Missing required GGUF metadata (strictness: {self.metadata_strictness})",
                    "missing_keys": missing_required,
                    "missing_count": len(missing_required),
                    "strictness_level": self.metadata_strictness,
                    "recommendation": "Critical metadata keys should be present for proper model identification",
                },
                "severity": self._normalize_severity(severity).value,
            })

        # Check for missing recommended metadata (info only, not warnings)
        if self.metadata_strictness == "high" and recommended_keys:
            missing_recommended = [key for key in recommended_keys if key not in metadata]
            if missing_recommended and len(missing_recommended) > len(recommended_keys) * 0.8:
                # Only warn if >80% of recommended keys are missing (indicates very sparse metadata)
                warnings.append({
                    "type": "gguf_sparse_metadata",
                    "details": {
                        "message": "Sparse GGUF metadata - missing many recommended fields",
                        "missing_recommended_keys": missing_recommended[:5],  # First 5 for brevity
                        "missing_recommended_count": len(missing_recommended),
                        "total_recommended": len(recommended_keys),
                        "recommendation": "Consider adding more metadata for better model documentation",
                    },
                    "severity": self._normalize_severity("low").value,  # Info level only
                })

        # WIRED: Architecture-specific metadata validation (if enabled by policy)
        arch = metadata.get("general.architecture")
        if self.require_architecture_metadata and arch and isinstance(arch, str):
            arch_lower = arch.lower()
            if arch_lower in self.arch_required_metadata:
                required_for_arch = self.arch_required_metadata[arch_lower]
                missing_arch_metadata = []

                for required_key in required_for_arch:
                    if required_key not in metadata:
                        missing_arch_metadata.append(required_key)

                if missing_arch_metadata:
                    # Severity based on metadata strictness
                    severity = self._normalize_severity("high" if self.metadata_strictness == "high" else "medium").value
                    warnings.append({
                        "type": "gguf_missing_arch_metadata",
                        "details": {
                            "message": f"Missing {arch} architecture metadata (policy enforced)",
                            "architecture": arch,
                            "missing_keys": missing_arch_metadata,
                            "policy_enabled": self.require_architecture_metadata,
                            "recommendation": "Architecture metadata incomplete - required by policy",
                        },
                        "severity": self._normalize_severity(severity).value,
                    })
        elif not self.require_architecture_metadata:
            logger.debug("Architecture metadata validation disabled by policy")

        # Check for metadata consistency
        consistency_issues = self._check_metadata_consistency(metadata)
        warnings.extend(consistency_issues)

        return warnings

    def _check_metadata_consistency(self, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check internal consistency of metadata values."""
        warnings = []

        try:
            # Check RoPE consistency for supported architectures
            arch = metadata.get("general.architecture", "").lower()
            if arch in ["llama", "mistral"]:
                rope_issues = self._validate_rope_consistency(metadata, arch)
                warnings.extend(rope_issues)

            # Check tokenizer consistency
            tokenizer_issues = self._validate_tokenizer_consistency(metadata)
            warnings.extend(tokenizer_issues)

            # Check context length consistency
            context_issues = self._validate_context_length_consistency(metadata, arch)
            warnings.extend(context_issues)

        except Exception as e:
            logger.debug(f"Error checking metadata consistency: {str(e)}")

        return warnings

    def _validate_rope_consistency(self, metadata: Dict[str, Any], arch: str) -> List[Dict[str, Any]]:
        """Validate RoPE configuration consistency."""
        warnings = []

        rope_dim_key = f"{arch}.rope.dimension_count"
        rope_base_key = f"{arch}.rope.freq_base"
        head_count_key = f"{arch}.attention.head_count"
        embedding_length_key = f"{arch}.embedding_length"

        rope_dim = metadata.get(rope_dim_key)
        rope_base = metadata.get(rope_base_key)
        head_count = metadata.get(head_count_key)
        embedding_length = metadata.get(embedding_length_key)

        # Check if RoPE dimension is consistent with head count and embedding
        if rope_dim and head_count and embedding_length:
            expected_rope_dim = embedding_length // head_count
            if rope_dim != expected_rope_dim:
                warnings.append({
                    "type": "gguf_rope_dimension_inconsistency",
                    "details": {
                        "message": "RoPE dimension inconsistent with model architecture",
                        "rope_dimension": rope_dim,
                        "expected_dimension": expected_rope_dim,
                        "head_count": head_count,
                        "embedding_length": embedding_length,
                        "recommendation": "RoPE configuration may be incorrect",
                    },
                    "severity": self._normalize_severity("medium").value,
                })

        # Check RoPE base frequency
        if rope_base and isinstance(rope_base, (int, float)):
            if rope_base <= 0:
                warnings.append({
                    "type": "gguf_invalid_rope_base",
                    "details": {
                        "message": "Invalid RoPE base frequency",
                        "rope_base": rope_base,
                        "recommendation": "RoPE base frequency must be positive",
                    },
                    "severity": self._normalize_severity("medium").value,
                })
            elif rope_base < 1000 or rope_base > 1000000:
                warnings.append({
                    "type": "gguf_unusual_rope_base",
                    "details": {
                        "message": "Unusual RoPE base frequency",
                        "rope_base": rope_base,
                        "typical_range": "1000-1000000",
                        "recommendation": "Verify RoPE configuration is correct",
                    },
                    "severity": self._normalize_severity("low").value,
                })

        # Check RoPE scaling if present
        scaling_type = metadata.get(f"{arch}.rope.scaling.type")
        scaling_factor = metadata.get(f"{arch}.rope.scaling.factor")

        if scaling_type and scaling_factor:
            if isinstance(scaling_factor, (int, float)) and scaling_factor <= 0:
                warnings.append({
                    "type": "gguf_invalid_rope_scaling",
                    "details": {
                        "message": "Invalid RoPE scaling factor",
                        "scaling_type": scaling_type,
                        "scaling_factor": scaling_factor,
                        "recommendation": "RoPE scaling factor must be positive",
                    },
                    "severity": self._normalize_severity("medium").value,
                })

        return warnings

    def _validate_tokenizer_consistency(self, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate tokenizer metadata consistency."""
        warnings = []

        tokens = metadata.get("tokenizer.ggml.tokens")
        scores = metadata.get("tokenizer.ggml.scores")
        token_types = metadata.get("tokenizer.ggml.token_type")

        if tokens and isinstance(tokens, list):
            token_count = len(tokens)

            # Check if scores length matches tokens
            if scores and isinstance(scores, list) and len(scores) != token_count:
                warnings.append({
                    "type": "gguf_tokenizer_scores_mismatch",
                    "details": {
                        "message": "Tokenizer scores count doesn't match token count",
                        "token_count": token_count,
                        "scores_count": len(scores),
                        "recommendation": "Tokenizer data may be corrupted",
                    },
                    "severity": self._normalize_severity("medium").value,
                })

            # Check if token types length matches tokens
            if token_types and isinstance(token_types, list) and len(token_types) != token_count:
                warnings.append({
                    "type": "gguf_tokenizer_types_mismatch",
                    "details": {
                        "message": "Token types count doesn't match token count",
                        "token_count": token_count,
                        "token_types_count": len(token_types),
                        "recommendation": "Tokenizer data may be corrupted",
                    },
                    "severity": self._normalize_severity("medium").value,
                })

        return warnings

    def _validate_context_length_consistency(self, metadata: Dict[str, Any], arch: str) -> List[Dict[str, Any]]:
        """Validate context length consistency across metadata."""
        warnings = []

        if not arch:
            return warnings

        context_key = f"{arch}.context_length"
        context_length = metadata.get(context_key)

        if context_length and isinstance(context_length, int):
            # Check for reasonable context length values
            if context_length <= 0:
                warnings.append({
                    "type": "gguf_invalid_context_length",
                    "details": {
                        "message": "Invalid context length",
                        "context_length": context_length,
                        "recommendation": "Context length must be positive",
                    },
                    "severity": self._normalize_severity("high").value,
                })
            elif context_length < 512:
                warnings.append({
                    "type": "gguf_small_context_length",
                    "details": {
                        "message": "Unusually small context length",
                        "context_length": context_length,
                        "recommendation": "Verify context length is correct",
                    },
                    "severity": self._normalize_severity("low").value,
                })
            elif context_length > 1000000:  # 1M tokens
                warnings.append({
                    "type": "gguf_large_context_length",
                    "details": {
                        "message": "Unusually large context length",
                        "context_length": context_length,
                        "recommendation": "Verify context length is realistic",
                    },
                    "severity": self._normalize_severity("low").value,
                })

        return warnings

    def _check_suspicious_kv_keys(self, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """ENHANCED: Smart suspicious KV detection with namespace allowlists and executable content analysis.

        Reduces false positives by:
        - Applying patterns only to unrecognized namespaces (not general.*, tokenizer.*, etc.)
        - Detecting executable content patterns (shell pipes, ${{, backticks, |bash)
        - Using per-key allowlists for legitimate values
        - Context-aware pattern matching
        """
        warnings = []
        # Initialize enhanced detection systems
        legitimate_findings = []  # Track allowlisted findings for reporting
        suspicious_findings = []
        executable_findings = []

        # Define recognized legitimate namespaces with their expected patterns
        legitimate_namespaces = {
            "general": {
                "allowlisted_keys": {
                    "general.source_url", "general.source_hf_repo", "general.license",
                    "general.name", "general.description", "general.author", "general.version",
                    "general.file_type", "general.quantization_version", "general.architecture",
                },
                "expected_patterns": {
                    "network_access": ["http", "https", "ftp"],  # URLs are expected here
                    "data_patterns": ["base64", "encoded"],  # Legitimate encoding references
                },
            },
            "tokenizer": {
                "allowlisted_keys": {
                    "tokenizer.ggml.model", "tokenizer.ggml.tokens", "tokenizer.ggml.scores",
                    "tokenizer.ggml.token_type", "tokenizer.ggml.merges", "tokenizer.chat_template",
                    "tokenizer.ggml.bos_token_id", "tokenizer.ggml.eos_token_id",
                    "tokenizer.ggml.unk_token_id", "tokenizer.ggml.sep_token_id", "tokenizer.ggml.pad_token_id",
                },
                "expected_patterns": {
                    "suspicious_keys": ["token", "template", "special"],  # These are normal in tokenizer context
                },
            },
            "llama": {
                "allowlisted_keys": {
                    "llama.context_length", "llama.embedding_length", "llama.block_count",
                    "llama.feed_forward_length", "llama.attention.head_count", "llama.attention.head_count_kv",
                    "llama.attention.layer_norm_rms_epsilon", "llama.rope.dimension_count",
                    "llama.rope.freq_base", "llama.rope.scaling.type", "llama.rope.scaling.factor",
                },
                "expected_patterns": {},
            },
            "training": {
                "allowlisted_keys": {
                    "training.data_sources", "training.epochs", "training.learning_rate",
                    "training.batch_size", "training.optimizer", "training.schedule",
                },
                "expected_patterns": {
                    "data_patterns": ["batch", "epoch", "learning"],  # Training terminology
                },
            },
        }


        for key, value in metadata.items():
            key_lower = key.lower()
            # Extract namespace from GGUF metadata key
            parts = key.split(".")
            namespace = parts[0] if len(parts) > 1 else "unknown"

            # Check if key is in a recognized legitimate namespace
            is_legitimate_namespace = namespace in legitimate_namespaces
            is_allowlisted_key = False

            if is_legitimate_namespace:
                allowlisted_keys = legitimate_namespaces[namespace]["allowlisted_keys"]
                is_allowlisted_key = key in allowlisted_keys

                if is_allowlisted_key:
                    # Apply namespace-specific allowlists for expected patterns
                    expected_patterns = legitimate_namespaces[namespace]["expected_patterns"]
                    self._check_allowlisted_key_value(key, value, expected_patterns, legitimate_findings)
                    continue  # Skip suspicious pattern matching for allowlisted keys

            # ENHANCED: Apply suspicious patterns only to unrecognized namespaces or non-allowlisted keys
            if not is_legitimate_namespace or not is_allowlisted_key:
                # Check key patterns (only for unrecognized namespaces)
                key_suspicious = self._check_key_suspicious_patterns(key, key_lower, namespace)
                if key_suspicious:
                    suspicious_findings.extend(key_suspicious)

                # Enhanced value analysis for executable content
                if isinstance(value, str) and value.strip():
                    # Check for executable content patterns
                    executable_detected = self._detect_executable_content(key, value)
                    if executable_detected:
                        executable_findings.extend(executable_detected)

                    # Apply traditional suspicious patterns with context
                    value_suspicious = self._check_value_suspicious_patterns(key, value, namespace)
                    if value_suspicious:
                        suspicious_findings.extend(value_suspicious)

        # Generate warnings based on enhanced analysis
        if executable_findings:
            # Executable content is always critical
            warnings.append({
                "type": "gguf_executable_content_detected",
                "details": {
                    "message": "Executable content patterns detected in metadata",
                    "executable_findings": executable_findings[:5],  # Top 5 most dangerous
                    "total_executable": len(executable_findings),
                    "analysis_method": "Enhanced pattern matching with command injection detection",
                    "recommendation": "CRITICAL: Executable content detected - possible code injection attack",
                },
                "severity": self._normalize_severity("critical").value,
            })

        if suspicious_findings:
            # Determine severity based on content and context
            severity = self._determine_suspicious_severity(suspicious_findings)

            warnings.append({
                "type": "gguf_suspicious_metadata_patterns",
                "details": {
                    "message": "Suspicious patterns detected in unrecognized metadata",
                    "suspicious_findings": suspicious_findings[:10],
                    "total_suspicious": len(suspicious_findings),
                    "analysis_method": "Namespace-aware pattern matching with allowlists",
                    "false_positive_reduction": {
                        "legitimate_findings_excluded": len(legitimate_findings),
                        "allowlisted_namespaces": list(legitimate_namespaces.keys()),
                        "enhanced_detection": "Applied only to unrecognized namespaces",
                    },
                    "recommendation": "Investigate unrecognized metadata patterns for potential tampering",
                },
                "severity": severity,
            })

        # Optional: Include legitimate findings summary for transparency
        if legitimate_findings and len(legitimate_findings) > 0:
            warnings.append({
                "type": "gguf_legitimate_patterns_detected",
                "details": {
                    "message": "Legitimate patterns detected and allowlisted",
                    "legitimate_findings": legitimate_findings[:5],
                    "total_legitimate": len(legitimate_findings),
                    "analysis_note": "These patterns were allowlisted due to legitimate context",
                },
                "severity": "info",
            })

        return warnings


    def _check_allowlisted_key_value(self, key: str, value: Any, expected_patterns: Dict[str, List[str]],
                                   legitimate_findings: List[Dict[str, Any]]) -> None:
        """Check allowlisted keys for expected patterns and log legitimate findings."""
        if not isinstance(value, str):
            return

        value_lower = value.lower()

        # Check if value contains expected patterns for this namespace
        for category, patterns in expected_patterns.items():
            for pattern in patterns:
                if pattern in value_lower:
                    legitimate_findings.append({
                        "key": key,
                        "value": str(value)[:100],
                        "pattern": pattern,
                        "category": category,
                        "reason": f"Expected pattern '{pattern}' in allowlisted key '{key}'",
                    })
                    break

    def _check_key_suspicious_patterns(self, key: str, key_lower: str, namespace: str) -> List[Dict[str, Any]]:
        """Check key names for suspicious patterns (only for unrecognized namespaces)."""
        findings = []

        # Only apply to unrecognized namespaces to avoid false positives
        if namespace in ["general", "tokenizer", "llama", "gpt2", "bloom", "mpt", "training"]:
            return findings

        # Apply suspicious pattern detection to unrecognized namespace keys
        for category, patterns in self.suspicious_kv_patterns.items():
            for pattern in patterns:
                if pattern in key_lower:
                    findings.append({
                        "key": key,
                        "value": "N/A",
                        "pattern": pattern,
                        "category": category,
                        "location": "key_name",
                        "namespace": namespace,
                        "risk": self._get_suspicious_key_risk(category),
                        "reason": f"Suspicious pattern '{pattern}' in unrecognized namespace '{namespace}'",
                    })
                    break  # Only report first match per category

        return findings

    def _detect_executable_content(self, key: str, value: str) -> List[Dict[str, Any]]:
        """Detect executable content patterns that indicate code injection attempts."""
        findings = []
        value_stripped = value.strip()

        # Skip if value looks like a normal URL or path (common false positives)
        if self._is_likely_benign_content(value_stripped):
            return findings

        # Use precompiled patterns for better performance
        compiled_executable_patterns = self._compiled_patterns.get("executable_content", {})
        for category, compiled_patterns in compiled_executable_patterns.items():
            for pattern in compiled_patterns:
                try:
                    if pattern.search(value_stripped):
                        findings.append({
                            "key": key,
                            "value": value[:200],  # More context for executable content
                            "pattern": pattern.pattern,  # Store pattern string, not compiled regex
                            "category": category,
                            "location": "value_content",
                            "risk": "CRITICAL: Executable content pattern detected",
                            "reason": f"Pattern '{pattern.pattern}' indicates potential {category}",
                            "confidence": "high",
                        })
                        break  # Only report first match per category
                except re.error:
                    # Skip invalid regex patterns
                    continue

        return findings

    def _is_likely_benign_content(self, content: str) -> bool:
        """Check if content is likely benign (URLs, normal paths, etc.) to reduce false positives."""
        content_lower = content.lower()

        # Common benign patterns that might trigger false positives
        benign_indicators = [
            # URLs and web content
            content_lower.startswith(("http://", "https://", "ftp://", "mailto:")),
            content_lower.startswith("www."),
            # File paths and extensions
            any(content_lower.endswith(ext) for ext in [".md", ".txt", ".json", ".yaml", ".yml", ".py", ".js"]),
            # Model and repo identifiers
            content_lower.startswith(("huggingface.co/", "github.com/", "gitlab.com/")),
            # Version strings and identifiers
            self._compiled_patterns["version_string"].match(content) and len(content) < 100,
            # JSON-like structures (but exclude templating patterns)
            (content.startswith("{") and content.endswith("}") and
             "{{" not in content and "${{" not in content and "{%" not in content),
            # ML-specific benign patterns
            any(pattern in content_lower for pattern in [
                "model", "tensor", "embedding", "token", "vocab", "tokenizer",
                "attention", "transformer", "layer", "weight", "bias",
                "context_length", "embedding_length", "block_count",
                "rope", "scaling", "frequency", "base", "dimension",
                "head_count", "feed_forward", "activation", "norm",
            ]),
            # Common ML metadata patterns
            any(pattern in content_lower for pattern in [
                "evaluation", "metric", "score", "accuracy", "loss",
                "training", "epoch", "batch", "learning_rate",
                "optimizer", "scheduler", "dropout", "regularization",
            ]),
            # Architecture names (common in GGUF)
            any(pattern in content_lower for pattern in [
                "llama", "gpt", "bert", "roberta", "t5", "bloom",
                "mistral", "mixtral", "qwen", "phi", "gemma",
                "falcon", "mpt", "rwkv", "gptj", "gptneox",
            ]),
        ]

        return any(benign_indicators)

    def _check_value_suspicious_patterns(self, key: str, value: str, namespace: str) -> List[Dict[str, Any]]:
        """Check string values for suspicious patterns with context awareness."""
        findings = []
        # Pattern matching uses case-sensitive compiled patterns

        # Skip pattern matching for values that are obviously legitimate
        if self._is_likely_benign_content(value):
            return findings

        # Apply context-aware suspicious pattern detection using compiled patterns
        compiled_suspicious_patterns = self._compiled_patterns.get("suspicious_value", {})

        for category, compiled_patterns in compiled_suspicious_patterns.items():
            # Skip network_access patterns for recognized namespaces where URLs are expected
            if category == "network_access" and namespace in ["general"]:
                continue

            # Skip data_patterns for training/tokenizer contexts where they're normal
            if category == "data_patterns" and namespace in ["training", "tokenizer"]:
                continue

            for compiled_pattern in compiled_patterns:
                if compiled_pattern.search(value):  # FIXED: Use regex search instead of substring
                    pattern_str = compiled_pattern.pattern  # Get original pattern string
                    # Additional context-based filtering
                    if self._should_flag_pattern_in_context(pattern_str, value, key, namespace, category):
                        findings.append({
                            "key": key,
                            "value": value[:100],
                            "pattern": pattern_str,
                            "category": category,
                            "location": "value_content",
                            "namespace": namespace,
                            "risk": f"Value contains {category} pattern",
                            "reason": f"Pattern '{pattern_str}' in value may indicate {category}",
                            "confidence": "medium",
                        })
                        break  # Only report first match per category

        return findings

    def _should_flag_pattern_in_context(self, pattern: str, value: str, key: str, namespace: str, category: str) -> bool:
        """Determine if a pattern should be flagged based on context."""
        # Allow common legitimate uses
        legitimate_contexts = {
            "http": ["source_url", "repo", "license", "documentation"],
            "download": ["source", "url", "repo", "reference"],
            "base64": ["token", "signature", "hash", "encoding"],
            "import": ["model", "library", "dependency"],
            "system": ["requirement", "compatibility", "platform"],
            "eval": ["evaluation", "metric", "score"],  # ML evaluation context
            "exec": ["execution", "performance"],  # ML execution context
        }

        # Check for legitimate context
        key_lower = key.lower()
        value_lower = value.lower()
        
        # Check if pattern appears in legitimate context
        if pattern in legitimate_contexts:
            for context_word in legitimate_contexts[pattern]:
                if context_word in key_lower or context_word in value_lower:
                    return False

        # Additional context checks for specific patterns
        if category == "code_injection":
            # Check if it's actually code execution vs legitimate text
            if pattern in ["eval(", "exec(", "system("]:
                # Only flag if it looks like actual function calls
                if not (pattern in value and "(" in value and ")" in value):
                    return False
            elif pattern in ["`", "&&", "||", "|", ";"]:
                # Only flag if it looks like command injection
                if not (pattern in value and len(value) > 10):  # Avoid flagging single characters
                    return False

        elif category == "network_access":
            # Check if it's a legitimate URL vs suspicious network access
            if pattern in ["http://", "https://"]:
                # Allow legitimate URLs in general namespace
                if namespace == "general" and value.startswith(("http://", "https://")):
                    return False

        elif category == "data_patterns":
            # Check if it's legitimate data vs suspicious patterns
            if pattern in ["base64", "hex", "binary"]:
                # Allow in legitimate contexts
                if any(ctx in key_lower for ctx in ["token", "signature", "hash", "encoding"]):
                    return False

        # Flag if no legitimate context found
        return True

    def _determine_suspicious_severity(self, findings: List[Dict[str, Any]]) -> str:
        """Determine severity level based on suspicious findings.

        Note: Category names here differ from executable content categories
        (e.g., 'shell_injection' vs executable categories like 'command_injection').
        This is intentional - executable findings are handled separately with
        their own severity logic, while these categories apply to general
        suspicious pattern detection in KV metadata.
        """
        if not findings:
            return self._normalize_severity("low").value

        # Count critical patterns
        critical_categories = ["code_injection", "shell_injection"]
        high_risk_categories = ["network_access", "path_traversal"]

        critical_count = sum(1 for f in findings if f.get("category") in critical_categories)
        high_risk_count = sum(1 for f in findings if f.get("category") in high_risk_categories)

        if critical_count > 0:
            return self._normalize_severity("high").value
        elif high_risk_count > 2:
            return self._normalize_severity("medium").value
        elif len(findings) > 5:
            return self._normalize_severity("medium").value
        else:
            return self._normalize_severity("low").value

    def _get_suspicious_key_risk(self, category: str) -> str:
        """Get risk description for suspicious key category."""
        risk_descriptions = {
            "code_injection": "Potential code injection vector",
            "network_access": "Potential network access attempt",
            "suspicious_keys": "Suspicious or malicious key pattern",
            "path_traversal": "Potential path traversal attack",
            "data_patterns": "Suspicious data encoding pattern",
        }
        return risk_descriptions.get(category, "Suspicious metadata pattern")

    def _validate_architecture_consistency(self, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate architecture consistency and presence."""
        warnings = []

        arch = metadata.get("general.architecture")
        if not arch:
            warnings.append({
                "type": "gguf_missing_architecture",
                "details": {
                    "message": "Missing architecture specification",
                    "recommendation": "GGUF files should specify model architecture",
                },
                "severity": self._normalize_severity("high").value,
            })
            return warnings

        if not isinstance(arch, str):
            warnings.append({
                "type": "gguf_invalid_architecture_type",
                "details": {
                    "message": "Architecture specification is not a string",
                    "architecture_type": type(arch).__name__,
                    "recommendation": "Architecture must be a string identifier",
                },
                "severity": self._normalize_severity("high").value,
            })
            return warnings

        # Check if architecture is recognized using policy-configurable list
        arch_lower = arch.lower()
        if arch_lower not in self.known_architectures:
            # Handle unknown architecture according to policy
            if self.unknown_architecture_policy == "warn":
                # Make this more informative rather than alarming
                logger.info(f"New architecture detected: '{arch}' - not in known list but may be legitimate")
                warnings.append({
                    "type": "gguf_unknown_architecture",
                    "details": {
                        "message": f"New architecture detected: {arch}",
                        "architecture": arch,
                        "known_architectures_count": len(self.known_architectures),
                        "note": "This may be a new model architecture not yet in the scanner's database",
                        "recommendation": "If this is a legitimate new architecture, consider updating the scanner's architecture list",
                        "policy_action": "info_only",
                    },
                    "severity": "info",  # Make it informational, not a warning
                })
            elif self.unknown_architecture_policy == "error":
                warnings.append({
                    "type": "gguf_unknown_architecture",
                    "details": {
                        "message": f"Unknown architecture: {arch} (policy: error)",
                        "architecture": arch,
                        "known_architectures": sorted(self.known_architectures),
                        "recommendation": "Architecture must be in allowlist for strict policy compliance",
                    },
                    "severity": self._normalize_severity("high").value,
                })
            # "ignore" case: no warning generated

        return warnings

    def _validate_tensor_info(self, tensor_info: List[Dict[str, Any]], data: bytes,
                             metadata_end_offset: int) -> List[Dict[str, Any]]:
        """Validate tensor information and checksums."""
        warnings = []
        logger.debug(f"Validating {len(tensor_info)} tensors")

        if not tensor_info:
            logger.debug("No tensors to validate")
            return warnings

        # FIXED: Restrictive tensor name suspicious pattern check
        # Only flag truly weird patterns - not normal tokens like "http", "download"
        suspicious_tensors = []

        # Tensor-specific suspicious patterns (much more restrictive)
        tensor_suspicious_patterns = {
            "path_traversal": {"../", "..\\", "/etc/", "/root/", "C:\\"},
            "control_chars": {"\x00", "\x01", "\x02", "\x03", "\x04", "\x05"},
            "truly_malicious": {"__import__", "eval(", "exec(", "system(", "shell_exec"},
        }

        for tensor in tensor_info:
            tensor_name = tensor.get("name", "")
            if isinstance(tensor_name, str):
                # Check for truly suspicious patterns only
                for category, patterns in tensor_suspicious_patterns.items():
                    for pattern in patterns:
                        if pattern in tensor_name:  # Case-sensitive for control chars
                            suspicious_tensors.append({
                                "tensor": tensor_name,
                                "pattern": repr(pattern),  # Show non-printable chars properly
                                "category": category,
                                "risk": f"Tensor name contains {category} pattern",
                            })
                            break

        if suspicious_tensors:
            # LOWERED: Severity reduced - tensor names rarely malicious
            warnings.append({
                "type": "gguf_suspicious_tensor_names",
                "details": {
                    "message": "Potentially suspicious tensor names detected (low confidence)",
                    "suspicious_tensors": suspicious_tensors[:5],  # Reduced display
                    "total_suspicious": len(suspicious_tensors),
                    "note": "Tensor name analysis has high false positive rate",
                    "recommendation": "Review manually - likely benign unless path traversal detected",
                },
                "severity": self._normalize_severity("low").value,  # Reduced from "high"
            })

        # Validate tensor offsets and basic checksums
        tensor_offset_issues = []
        file_size = len(data)

        for i, tensor in enumerate(tensor_info):
            tensor_offset = tensor.get("offset", 0)
            tensor_name = tensor.get("name", f"tensor_{i}")
            dims = tensor.get("dims", [])

            # Check if tensor offset is within file bounds
            actual_offset = metadata_end_offset + tensor_offset
            if actual_offset >= file_size:
                tensor_offset_issues.append({
                    "tensor": tensor_name,
                    "offset": actual_offset,
                    "file_size": file_size,
                    "issue": "Tensor offset beyond file end",
                })

            # Basic tensor size validation with integer overflow protection
            if dims and all(isinstance(d, int) and d > 0 for d in dims):
                element_count = 1
                for dim in dims:
                    # CRITICAL SECURITY FIX: Prevent integer overflow attacks
                    if dim > self.MAX_TENSOR_DIMENSIONS:
                        break  # Skip tensors with suspicious dimensions
                    element_count *= dim
                    if element_count > self.MAX_ELEMENT_COUNT:
                        break  # Prevent overflow before it happens

                if element_count > 1000000000:  # 1B elements
                    tensor_offset_issues.append({
                        "tensor": tensor_name,
                        "element_count": element_count,
                        "dims": dims,
                        "issue": "Unusually large tensor size",
                    })

        if tensor_offset_issues:
            warnings.append({
                "type": "gguf_tensor_offset_issues",
                "details": {
                    "message": "Tensor offset or size issues detected",
                    "tensor_issues": tensor_offset_issues[:10],
                    "total_issues": len(tensor_offset_issues),
                    "recommendation": "Verify tensor layout integrity",
                },
                "severity": self._normalize_severity("high").value,
            })

        return warnings

    def _get_quantization_type_name(self, type_id: int) -> Optional[str]:
        """Map GGUF type ID to quantization type name using flexible policy-configurable mapping.

        This allows hot-patching for GGML version compatibility without code releases.
        Unknown types are handled according to policy (warn/ignore/error).
        """
        return self.ggml_type_mapping.get(type_id)

    def _get_quantization_type_name_safe(self, type_id: int) -> str:
        """Get quantization type name with policy-aware unknown type handling.

        Returns: Type name string, handling unknown types according to policy:
        - "warn": Log warning and return "UNKNOWN_X"
        - "ignore": Return "UNKNOWN_X" without warning
        - "error": Would raise exception (not implemented to avoid breaking parsing)
        """
        type_name = self.ggml_type_mapping.get(type_id)

        if type_name is None:
            unknown_name = f"UNKNOWN_{type_id}"

            if self.unknown_type_policy == "warn":
                logger.warning(f"Unknown GGML type ID {type_id} - may indicate newer GGML version or corrupted data")
            elif self.unknown_type_policy == "error":
                # For now, just warn rather than breaking parsing
                logger.error(f"Unknown GGML type ID {type_id} - strict policy violation")
            # "ignore" case: no logging

            return unknown_name

        return type_name

    def _validate_quantization_types(self, tensor_info: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """FIXED QUANTIZATION VALIDATION: Always map type ID → type name and validate properly.

        Enhanced validation includes:
        - Always map type ID to type name (UNKNOWN for unmapped types)
        - Check membership in allowed quantization types from policy
        - Per-layer expectations: norms/biases in F16/F32, weights quantized
        - Flag models with "everything quantized" and no floating-point layers
        """
        warnings = []
        if not tensor_info:
            return warnings

        quantization_issues = []
        type_distribution = {}
        fp_tensor_count = 0  # Count of floating-point tensors
        quantized_tensor_count = 0  # Count of quantized tensors
        norm_bias_tensors = []  # Track norm and bias tensors
        weight_tensors = []  # Track weight tensors

        for tensor in tensor_info:
            tensor_type = tensor.get("type", 0)
            tensor_name = tensor.get("name", "unknown")

            # Count type distribution
            type_distribution[tensor_type] = type_distribution.get(tensor_type, 0) + 1

            # ENHANCED: Always map type ID → type name; if unknown → UNKNOWN
            type_name = self._get_quantization_type_name(tensor_type)
            if type_name is None:
                type_name = "UNKNOWN"
                quantization_issues.append({
                    "tensor": tensor_name,
                    "type_id": tensor_type,
                    "issue": "Unknown ggml type",
                })
            elif type_name not in self.allowed_quantization_types:
                # WIRED: Use valid_quantization_types for safety assessment
                type_info = self.valid_quantization_types.get(type_name, {})
                is_safe = type_info.get("safe", False)

                quantization_issues.append({
                    "tensor": tensor_name,
                    "type": type_name,
                    "issue": "Disallowed quantization",
                    "safety_rating": "safe" if is_safe else "experimental",
                    "type_info": type_info,
                })

            # ENHANCED: Per-layer expectations tracking
            tensor_name_lower = tensor_name.lower()

            # Categorize tensor types for layer-specific analysis
            is_norm_bias = any(keyword in tensor_name_lower for keyword in [
                "norm", "bias", "layernorm", "rmsnorm", "attention_norm",
                "ffn_norm", "input_layernorm", "post_attention_layernorm",
            ])

            is_weight = any(keyword in tensor_name_lower for keyword in [
                "weight", "w_q", "w_k", "w_v", "w_o", "gate", "up", "down",
                "q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj",
            ])

            # Track floating-point vs quantized tensor counts
            if type_name in ["F32", "F16", "BF16"]:
                fp_tensor_count += 1
                if is_norm_bias:
                    norm_bias_tensors.append({"name": tensor_name, "type": type_name, "expected": True})
                elif is_weight:
                    weight_tensors.append({"name": tensor_name, "type": type_name, "expected": False})
            else:
                quantized_tensor_count += 1
                if is_norm_bias:
                    norm_bias_tensors.append({"name": tensor_name, "type": type_name, "expected": False})
                elif is_weight:
                    weight_tensors.append({"name": tensor_name, "type": type_name, "expected": True})

        # ENHANCED: Per-layer expectation analysis
        per_layer_issues = []

        # Check norm/bias tensors that should be in F16/F32
        unexpected_quantized_norms = [t for t in norm_bias_tensors if not t["expected"]]
        if unexpected_quantized_norms:
            per_layer_issues.append({
                "category": "quantized_norms_biases",
                "count": len(unexpected_quantized_norms),
                "tensors": unexpected_quantized_norms[:5],
                "issue": "Norm/bias tensors should typically remain in F16/F32 for numerical stability",
            })

        # Check weight tensors that are unexpectedly in F32/F16
        unexpected_fp_weights = [t for t in weight_tensors if not t["expected"]]
        if unexpected_fp_weights:
            per_layer_issues.append({
                "category": "unquantized_weights",
                "count": len(unexpected_fp_weights),
                "tensors": unexpected_fp_weights[:5],
                "issue": "Weight tensors typically quantized for efficiency - unquantized weights unusual",
            })

        # ENHANCED: "Everything quantized" detection
        total_tensors = len(tensor_info)
        everything_quantized = False
        if total_tensors > 0 and fp_tensor_count == 0:
            everything_quantized = True
            per_layer_issues.append({
                "category": "everything_quantized",
                "count": quantized_tensor_count,
                "total_tensors": total_tensors,
                "issue": "All tensors quantized - no floating-point layers detected (unusual and potentially problematic)",
            })

        # Check for unusual quantization type distributions
        unusual_distributions = []
        if total_tensors > 0:
            for type_id, count in type_distribution.items():
                percentage = (count / total_tensors) * 100
                type_name = self._get_quantization_type_name_safe(type_id)

                # Flag if a single unusual/unknown type dominates
                if percentage > 90 and (type_id > 20 or type_name.startswith("UNKNOWN")):
                    unusual_distributions.append({
                        "type_id": type_id,
                        "type_name": type_name,
                        "percentage": percentage,
                        "count": count,
                        "issue": f"Unusual quantization type '{type_name}' dominates model",
                    })

        # SIMPLIFIED: Basic security-critical quantization checks only
        embedding_protection_issues = []

        if total_tensors > 0:
            # Only check embedding protection - security critical for supply chain
            embedding_analysis = self._check_embedding_protection_policy(tensor_info)
            if embedding_analysis["violations"]:
                embedding_protection_issues = embedding_analysis["violations"]

        # Generate warnings based on analysis
        if quantization_issues:
            warnings.append({
                "type": "gguf_quantization_type_issues",
                "details": {
                    "message": "Quantization type issues detected",
                    "quantization_issues": quantization_issues[:10],
                    "total_issues": len(quantization_issues),
                    "validation_method": "Always map type ID → type name with policy enforcement",
                    "recommendation": "Verify quantization types are valid and policy-compliant",
                },
                "severity": self._normalize_severity("medium").value,
            })

        if per_layer_issues:
            severity = self._normalize_severity("high" if everything_quantized else "medium").value
            warnings.append({
                "type": "gguf_per_layer_quantization_issues",
                "details": {
                    "message": "Per-layer quantization expectation issues detected",
                    "layer_analysis": {
                        "total_tensors": total_tensors,
                        "fp_tensors": fp_tensor_count,
                        "quantized_tensors": quantized_tensor_count,
                        "everything_quantized": everything_quantized,
                        "norm_bias_tensors_analyzed": len(norm_bias_tensors),
                        "weight_tensors_analyzed": len(weight_tensors),
                    },
                    "per_layer_issues": per_layer_issues,
                    "recommendation": "Review quantization patterns - ensure norms/biases remain unquantized for model stability",
                },
                "severity": severity,
            })

        # REMOVED: Distribution policy analysis for supply chain simplification
        # Complex quantization distribution analysis is ML quality assessment, not security

        # ENHANCED: Embedding protection violations
        if embedding_protection_issues:
            warnings.append({
                "type": "gguf_embedding_protection_policy_violation",
                "details": {
                    "message": "Embedding protection policy violations detected",
                    "protection_violations": embedding_protection_issues,
                    "total_violations": len(embedding_protection_issues),
                    "policy_settings": {
                        "minimum_quality": self.quantization_distribution_policy["embedding_protection"]["minimum_quality"],
                        "policy_floor_types": self.quantization_distribution_policy["embedding_protection"]["policy_floor_types"],
                    },
                    "recommendation": "QUARANTINE: Critical embeddings quantized below policy floor",
                },
                "severity": self._normalize_severity("critical").value,  # Embedding violations are always critical
            })

        if unusual_distributions:
            warnings.append({
                "type": "gguf_unusual_quantization_distribution",
                "details": {
                    "message": "Unusual quantization type distribution",
                    "unusual_distributions": unusual_distributions,
                    "type_distribution": {
                        self._get_quantization_type_name_safe(type_id): count
                        for type_id, count in list(type_distribution.items())[:10]
                    },
                    "recommendation": "Verify quantization scheme is legitimate and not corrupted",
                },
                "severity": self._normalize_severity("low").value,
            })

        return warnings

    # REMOVED: _get_layer_quantization_recommendation() for supply chain simplification
    # Performance recommendations are ML quality assessment, not security


    # REMOVED: _analyze_quantization_distribution() for supply chain simplification
    # Complex quantization distribution analysis is ML quality assessment, not security
    # REMOVED: _detect_suspicious_quantization_patterns() for supply chain simplification
    # Complex suspicious pattern detection is ML quality assessment, not security

    def _check_embedding_protection_policy(self, tensor_info: List[Dict[str, Any]]) -> Dict[str, Any]:
        """ENHANCED: Check embedding protection policy.

        Policy rules:
        - If embeddings (tok_embeddings, output) quantized below policy floor (e.g., Q2_K) → QUARANTINE
        - Protect critical embedding tensors from excessive quantization
        """
        violations = []
        embedding_analysis = []

        if not self.quantization_distribution_policy.get("embedding_protection", {}).get("enabled", True):
            return {"violations": violations, "analysis": embedding_analysis}

        # Get policy settings
        embedding_config = self.quantization_distribution_policy["embedding_protection"]
        protected_tensor_patterns = embedding_config.get("protected_tensors", [])
        minimum_quality = embedding_config.get("minimum_quality", "Q4_0")
        policy_floor_types = set(embedding_config.get("policy_floor_types", []))

        # Find embedding tensors
        for tensor in tensor_info:
            tensor_name = tensor.get("name", "").lower()
            tensor_type = tensor.get("type", 0)
            tensor_type_name = self._get_quantization_type_name(tensor_type)

            # Check if this is a protected embedding tensor
            is_protected_embedding = any(
                pattern in tensor_name for pattern in protected_tensor_patterns
            )

            if is_protected_embedding and tensor_type_name:
                embedding_analysis.append({
                    "tensor_name": tensor.get("name", "unknown"),
                    "tensor_type": tensor_type_name,
                    "is_protected": True,
                    "tensor_type_id": tensor_type,
                })

                # Check if quantized below policy floor (critical violation → QUARANTINE)
                if tensor_type_name in policy_floor_types:
                    violations.append({
                        "violation_type": "embedding_below_policy_floor",
                        "tensor_name": tensor.get("name", "unknown"),
                        "tensor_type": tensor_type_name,
                        "policy_floor_types": list(policy_floor_types),
                        "severity": self._normalize_severity("critical").value,
                        "action": "QUARANTINE",
                        "issue": f"Critical embedding '{tensor.get('name')}' quantized to '{tensor_type_name}' which is below policy floor",
                    })

                # Check if below minimum quality threshold (warning)
                elif self._is_below_minimum_quality(tensor_type_name, minimum_quality):
                    violations.append({
                        "violation_type": "embedding_below_minimum_quality",
                        "tensor_name": tensor.get("name", "unknown"),
                        "tensor_type": tensor_type_name,
                        "minimum_quality": minimum_quality,
                        "severity": self._normalize_severity("high").value,
                        "action": "WARN",
                        "issue": f"Embedding '{tensor.get('name')}' quantized to '{tensor_type_name}' which is below minimum quality '{minimum_quality}'",
                    })

        # Additional analysis: check for complete absence of protected embeddings
        if not embedding_analysis:
            violations.append({
                "violation_type": "missing_protected_embeddings",
                "expected_patterns": protected_tensor_patterns,
                "severity": self._normalize_severity("medium").value,
                "action": "WARN",
                "issue": "No protected embedding tensors found - may indicate incomplete model or unusual architecture",
            })

        return {
            "violations": violations,
            "analysis": embedding_analysis,
            "policy_summary": {
                "protected_patterns": protected_tensor_patterns,
                "minimum_quality": minimum_quality,
                "policy_floor_types": list(policy_floor_types),
                "embeddings_found": len(embedding_analysis),
            },
        }

    def _is_below_minimum_quality(self, tensor_type: str, minimum_quality: str) -> bool:
        """Check if tensor quantization is below minimum quality threshold."""
        try:
            tensor_quality_index = self.quantization_quality_hierarchy.index(tensor_type)
            minimum_quality_index = self.quantization_quality_hierarchy.index(minimum_quality)

            # Higher index = lower quality, so tensor is below minimum if index is higher
            return tensor_quality_index > minimum_quality_index
        except ValueError:
            # If type not found in hierarchy, assume it's below minimum quality
            return True

    # REMOVED: Statistical analysis methods for supply chain simplification
    # _perform_mad_z_score_analysis() - ML quality assessment, not security scanning
    def _validate_tensor_layout(self, data: bytes, tensor_info: List[Dict[str, Any]],
                               data_start_offset: int) -> List[Dict[str, Any]]:
        """ENHANCED LAYOUT VALIDATION: Alignment, overlap, and bounds checking.

        Validates:
        - Tensor alignment to configurable byte boundaries
        - Tensor overlap detection (critical integrity issue)
        - Out-of-bounds tensor validation
        - Proper tensor ordering and layout
        """
        warnings = []

        if not tensor_info:
            return warnings

        try:
            # Sort tensors by offset for overlap detection
            tensors_sorted = sorted(tensor_info, key=lambda t: t.get("offset", 0))

            # Track layout statistics
            layout_stats = {
                "total_tensors": len(tensor_info),
                "alignment_violations": 0,
                "overlap_violations": 0,
                "oob_violations": 0,
                "total_tensor_bytes": 0,
            }

            last_end_offset = 0
            alignment_issues = []
            overlap_issues = []
            oob_issues = []

            for i, tensor in enumerate(tensors_sorted):
                tensor_name = tensor.get("name", f"tensor_{i}")
                dims = tensor.get("dims", [])
                tensor_type = tensor.get("type", 0)
                tensor_offset = tensor.get("offset", 0)

                # Skip invalid tensors
                if not dims or any(d <= 0 for d in dims):
                    continue

                # CRITICAL FIX: Use offset-differencing instead of estimated sizes
                # For quantized tensors, bytes_per_element is approximation → false positives/negatives
                actual_start = data_start_offset + tensor_offset

                # Calculate actual tensor size using offset-differencing
                if i < len(tensors_sorted) - 1:
                    # Use next tensor's offset to determine actual size
                    next_tensor_offset = tensors_sorted[i + 1].get("offset", 0)
                    tensor_byte_size = next_tensor_offset - tensor_offset
                else:
                    # Last tensor: bounded by file end
                    tensor_byte_size = len(data) - actual_start

                # Fallback: Estimated size as cross-check (for validation, not primary detection)
                try:
                    element_count = 1
                    for dim in dims:
                        if dim <= 0 or dim > self.MAX_TENSOR_DIMENSIONS:
                            break
                        # CRITICAL SECURITY FIX: Check for overflow BEFORE multiplication
                        if element_count > self.MAX_ELEMENT_COUNT // dim:
                            break
                        element_count *= dim
                    else:
                        bytes_per_element = self._get_bytes_per_element(tensor_type)
                        estimated_size = math.ceil(float(element_count) * bytes_per_element)

                        # Compare actual vs estimated (warn about large discrepancies)
                        if abs(tensor_byte_size - estimated_size) > estimated_size * 0.5:
                            logger.debug(f"Size mismatch for {tensor_name}: actual={tensor_byte_size}, estimated={estimated_size}")
                except Exception as e:
                    logger.debug(f"Size estimation error for {tensor_name}: {e}")
                    estimated_size = tensor_byte_size  # Use actual size

                actual_end = actual_start + tensor_byte_size

                # 1. ALIGNMENT VALIDATION
                alignment_violation = self._check_tensor_alignment(
                    tensor_name, tensor_offset, tensor_type,
                )
                if alignment_violation:
                    alignment_issues.append(alignment_violation)
                    layout_stats["alignment_violations"] += 1

                # 2. OVERLAP DETECTION
                if actual_start < last_end_offset:
                    # Find the overlapping tensor
                    prev_tensor = tensors_sorted[i-1] if i > 0 else None
                    prev_name = prev_tensor.get("name", "unknown") if prev_tensor else "unknown"

                    overlap_issue = {
                        "current_tensor": tensor_name,
                        "previous_tensor": prev_name,
                        "current_start": actual_start,
                        "previous_end": last_end_offset,
                        "overlap_bytes": last_end_offset - actual_start,
                        "severity": self._normalize_severity("critical").value,
                    }
                    overlap_issues.append(overlap_issue)
                    layout_stats["overlap_violations"] += 1

                # 3. OUT-OF-BOUNDS VALIDATION
                if actual_end > len(data):
                    oob_issue = {
                        "tensor_name": tensor_name,
                        "tensor_start": actual_start,
                        "tensor_end": actual_end,
                        "file_size": len(data),
                        "bytes_beyond": actual_end - len(data),
                        "severity": self._normalize_severity("critical").value,
                    }
                    oob_issues.append(oob_issue)
                    layout_stats["oob_violations"] += 1

                # Update tracking
                last_end_offset = max(last_end_offset, actual_end)
                layout_stats["total_tensor_bytes"] += tensor_byte_size

            # Generate warnings based on findings
            if alignment_issues:
                warnings.append(self._create_alignment_warning(alignment_issues, layout_stats))

            if overlap_issues:
                warnings.append(self._create_overlap_warning(overlap_issues, layout_stats))

            if oob_issues:
                warnings.append(self._create_oob_warning(oob_issues, layout_stats))

            # Generate layout summary if there are any issues
            total_issues = layout_stats["alignment_violations"] + layout_stats["overlap_violations"] + layout_stats["oob_violations"]
            if total_issues > 0:
                warnings.append(self._create_layout_summary_warning(layout_stats))

        except Exception as e:
            logger.debug(f"Tensor layout validation error: {e}")
            warnings.append({
                "type": "gguf_layout_validation_error",
                "details": {
                    "message": "Error during tensor layout validation",
                    "error": str(e),
                    "recommendation": "File may be corrupted or have invalid tensor layout",
                },
                "severity": self._normalize_severity("medium").value,
            })

        return warnings

    def _check_tensor_alignment(self, tensor_name: str, tensor_offset: int, tensor_type: int) -> Optional[Dict[str, Any]]:
        """Check if tensor is properly aligned to configured boundary."""
        if self.gguf_alignment <= 1:
            return None  # Alignment disabled

        if (tensor_offset % self.gguf_alignment) != 0:
            # Get type name for better reporting
            type_name = self._get_quantization_type_name(tensor_type) or f"type_{tensor_type}"

            return {
                "tensor_name": tensor_name,
                "tensor_offset": tensor_offset,
                "tensor_type": type_name,
                "required_alignment": self.gguf_alignment,
                "actual_alignment": tensor_offset % self.gguf_alignment,
                "misalignment_bytes": tensor_offset % self.gguf_alignment,
                "severity": self._normalize_severity("high").value,
            }

        return None

    def _create_alignment_warning(self, alignment_issues: List[Dict[str, Any]],
                                 layout_stats: Dict[str, int]) -> Dict[str, Any]:
        """Create warning for tensor alignment violations."""
        severity = self._normalize_severity("critical" if len(alignment_issues) > layout_stats["total_tensors"] * 0.5 else "high").value

        return {
            "type": "gguf_tensor_alignment_violations",
            "details": {
                "message": f"Tensor alignment violations detected (alignment: {self.gguf_alignment} bytes)",
                "violation_summary": {
                    "misaligned_tensors": len(alignment_issues),
                    "total_tensors": layout_stats["total_tensors"],
                    "violation_percentage": f"{(len(alignment_issues) / layout_stats['total_tensors']) * 100:.1f}%",
                    "required_alignment": f"{self.gguf_alignment} bytes",
                },
                "alignment_violations": alignment_issues[:10],  # Top 10 violations
                "recommendation": self._get_alignment_recommendation(len(alignment_issues), layout_stats["total_tensors"]),
            },
            "severity": severity,
        }

    def _create_overlap_warning(self, overlap_issues: List[Dict[str, Any]],
                               layout_stats: Dict[str, int]) -> Dict[str, Any]:
        """Create warning for tensor overlap violations."""
        return {
            "type": "gguf_tensor_overlap_violations",
            "details": {
                "message": "Critical tensor overlap violations detected",
                "violation_summary": {
                    "overlapping_tensors": len(overlap_issues),
                    "total_tensors": layout_stats["total_tensors"],
                    "total_overlap_bytes": sum(issue["overlap_bytes"] for issue in overlap_issues),
                },
                "overlap_violations": overlap_issues[:5],  # Top 5 overlaps
                "recommendation": "CRITICAL: Tensor overlaps indicate severe file corruption or tampering",
            },
            "severity": self._normalize_severity("critical").value,
        }

    def _create_oob_warning(self, oob_issues: List[Dict[str, Any]],
                           layout_stats: Dict[str, int]) -> Dict[str, Any]:
        """Create warning for out-of-bounds tensor violations."""
        return {
            "type": "gguf_tensor_oob_violations",
            "details": {
                "message": "Tensor out-of-bounds violations detected",
                "violation_summary": {
                    "oob_tensors": len(oob_issues),
                    "total_tensors": layout_stats["total_tensors"],
                    "total_bytes_beyond": sum(issue["bytes_beyond"] for issue in oob_issues),
                },
                "oob_violations": oob_issues[:5],  # Top 5 OOB issues
                "recommendation": "CRITICAL: Tensors extend beyond file boundaries - file truncated or corrupted",
            },
            "severity": self._normalize_severity("critical").value,
        }

    def _create_layout_summary_warning(self, layout_stats: Dict[str, int]) -> Dict[str, Any]:
        """Create summary warning for overall layout health."""
        total_issues = layout_stats["alignment_violations"] + layout_stats["overlap_violations"] + layout_stats["oob_violations"]

        return {
            "type": "gguf_tensor_layout_summary",
            "details": {
                "message": "GGUF tensor layout integrity assessment",
                "layout_health": {
                    "total_tensors": layout_stats["total_tensors"],
                    "total_issues": total_issues,
                    "issue_rate": f"{(total_issues / layout_stats['total_tensors']) * 100:.1f}%",
                    "total_tensor_bytes": f"{layout_stats['total_tensor_bytes']:,} bytes",
                },
                "issue_breakdown": {
                    "alignment_violations": layout_stats["alignment_violations"],
                    "overlap_violations": layout_stats["overlap_violations"],
                    "oob_violations": layout_stats["oob_violations"],
                },
                "recommendation": self._get_layout_health_recommendation(layout_stats),
            },
            "severity": self._normalize_severity("high" if total_issues > layout_stats["total_tensors"] * 0.1 else "medium").value,
        }

    def _get_alignment_recommendation(self, violations: int, total_tensors: int) -> str:
        """Get recommendation for alignment violations."""
        violation_rate = violations / total_tensors

        if violation_rate > 0.5:
            return "CRITICAL: >50% tensors misaligned - file may be corrupted or use non-standard layout"
        elif violation_rate > 0.2:
            return "HIGH RISK: >20% misaligned tensors - verify file integrity and generation process"
        elif violation_rate > 0.05:
            return "MODERATE: Some alignment issues detected - check quantization and conversion process"
        else:
            return "Minor alignment issues detected - may impact performance but not critical"

    def _get_layout_health_recommendation(self, layout_stats: Dict[str, int]) -> str:
        """Get overall layout health recommendation."""
        total_issues = layout_stats["alignment_violations"] + layout_stats["overlap_violations"] + layout_stats["oob_violations"]

        if layout_stats["overlap_violations"] > 0 or layout_stats["oob_violations"] > 0:
            return "CRITICAL: Overlap/OOB violations detected - file severely corrupted, DO NOT USE"
        elif total_issues > layout_stats["total_tensors"] * 0.2:
            return "HIGH RISK: Extensive layout issues - verify file integrity before deployment"
        elif total_issues > 0:
            return "MODERATE: Some layout issues detected - monitor for additional anomalies"
        else:
            return "Layout appears healthy - no critical issues detected"

    def _get_element_size_for_skip(self, element_type: int) -> Optional[int]:
        """SECURITY: Get fixed element size for safe array skipping without parsing
        Returns None for variable-length types (strings, arrays) that cannot be safely skipped in bulk.
        """
        # Fixed-size primitive types that can be safely skipped
        fixed_size_types = {
            self.GGUF_TYPE_UINT8: 1,
            self.GGUF_TYPE_INT8: 1,
            self.GGUF_TYPE_UINT16: 2,
            self.GGUF_TYPE_INT16: 2,
            self.GGUF_TYPE_UINT32: 4,
            self.GGUF_TYPE_INT32: 4,
            self.GGUF_TYPE_FLOAT32: 4,
            self.GGUF_TYPE_UINT64: 8,
            self.GGUF_TYPE_INT64: 8,
            self.GGUF_TYPE_FLOAT64: 8,
            self.GGUF_TYPE_BOOL: 1,
        }

        return fixed_size_types.get(element_type)  # Returns None for unsafe types

    def _get_bytes_per_element(self, tensor_type: int) -> float:
        """Get bytes per element for tensor types.

        NOTE: For quantized types this is an approximation
        """
        # Map tensor type IDs to bytes per element
        type_sizes = {
            0: 4.0,   # F32
            1: 2.0,   # F16
            2: 1.0,   # Q4_0 (4 bits + metadata)
            3: 1.0,   # Q4_1 (4 bits + metadata)
            6: 0.75,  # Q5_0 (5 bits + metadata)
            7: 0.75,  # Q5_1 (5 bits + metadata)
            8: 1.0,   # Q8_0 (8 bits)
            9: 1.0,   # Q8_1 (8 bits)
            10: 0.75, # Q2_K (2 bits + metadata)
            11: 0.875, # Q3_K (3 bits + metadata)
            12: 1.0,  # Q4_K (4 bits + metadata)
            13: 0.75, # Q5_K (5 bits + metadata)
            14: 1.0,  # Q6_K (6 bits + metadata)
            15: 1.0,  # Q8_K (8 bits)
            16: 2.0,  # BF16
            17: 2.0,  # Q4_0_4_4
            18: 2.0,  # Q4_0_4_8
            19: 2.0,  # Q4_0_8_8
        }

        return type_sizes.get(tensor_type, 4.0)  # Default to F32 size
