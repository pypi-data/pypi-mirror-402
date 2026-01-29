"""Safetensors shard integrity validator - Critical for multi-file model security."""

import json
import logging
import struct
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

from palisade.models.metadata import ModelMetadata, ModelType

# Import secure file utilities
from palisade.utils.file_security import (
    SecurePathError,
    is_safe_directory,
    safe_open_file,
    validate_file_path,
)

if TYPE_CHECKING:
    from palisade.core.cedar_policy_engine import CedarPolicyEngine
    from palisade.models.model_file import ModelFile
    from palisade.models.types import ChunkInfo, StreamingContext

from .base import BaseValidator, Severity

logger = logging.getLogger(__name__)

class SafetensorsIntegrityValidator(BaseValidator):
    """CRITICAL SECURITY VALIDATOR
    Verifies integrity of safetensors sharded models:
    - model.safetensors.index.json ↔ shard file consistency
    - Hash verification of shard contents
    - Byte range validation
    - Tensor completeness (no missing/rogue tensors).
    """

    def __init__(self, metadata: ModelMetadata, policy_engine: Optional["CedarPolicyEngine"] = None) -> None:
        super().__init__(metadata, policy_engine)

        # Load policy-configurable settings
        self._load_policy_configuration()

        self.expected_index_keys = {
            "metadata",      # Model metadata
            "weight_map",    # Tensor -> shard mapping
        }

        # Suspicious patterns in tensor names that might indicate malicious content
        # NOTE: "__" removed - too many false positives for legitimate quantization formats
        self.suspicious_tensor_patterns = {
            "backdoor_", "poison_", "malicious_", "trojan_",
            "inject_", "exploit_", "rce_", "shell_",
            "..", "//", "\\\\",  # Path traversal attempts
        }

        # Standard dtype mappings for validation
        self.dtype_mappings = {
            "F32": {"name": "float32", "bytes": 4, "precision": "full"},
            "F16": {"name": "float16", "bytes": 2, "precision": "half"},
            "BF16": {"name": "bfloat16", "bytes": 2, "precision": "half"},
            "I32": {"name": "int32", "bytes": 4, "precision": "full"},
            "I16": {"name": "int16", "bytes": 2, "precision": "half"},
            "I8": {"name": "int8", "bytes": 1, "precision": "quarter"},
            "U8": {"name": "uint8", "bytes": 1, "precision": "quarter"},
            "BOOL": {"name": "bool", "bytes": 1, "precision": "binary"},
        }

        # Core model components that should have consistent precision
        self.core_component_patterns = {
            "attention": ["attn", "attention", "self_attn", "cross_attn"],
            "feedforward": ["mlp", "ffn", "feed_forward", "fc", "linear"],
            "embeddings": ["embed", "embedding", "wte", "word_embeddings"],
            "layer_norm": ["norm", "layer_norm", "layernorm", "ln"],
            "output": ["lm_head", "classifier", "output", "head"],
        }

        # Expected dtype patterns for different model components
        self.expected_precision_patterns = {
            "uniform_fp32": {"F32"},  # All tensors should be fp32
            "uniform_fp16": {"F16"},  # All tensors should be fp16
            "uniform_bf16": {"BF16"}, # All tensors should be bf16
            "mixed_precision_standard": {"F32", "F16"},  # Acceptable mixed precision
            "quantized_int8": {"F32", "I8"},  # Quantized model pattern
        }

    def _load_policy_configuration(self) -> None:
        """Load policy-configurable settings for safetensors integrity."""
        # Get policy configuration for safetensors integrity validator
        policy_config = {}
        if self.policy_engine and hasattr(self.policy_engine, "get_validator_config"):
            policy_config = self.policy_engine.get_validator_config("safetensors_integrity", {})

        # Load suspicious tensor name patterns from policy (if configured)
        # NOTE: "__" removed - too many false positives for legitimate quantization formats
        default_suspicious_patterns = {
            "backdoor_", "poison_", "malicious_", "trojan_",
            "inject_", "exploit_", "rce_", "shell_",
            "..", "//", "\\\\",  # Path traversal attempts
        }

        custom_patterns = policy_config.get("suspicious_tensor_patterns", default_suspicious_patterns)
        if isinstance(custom_patterns, list):
            self.suspicious_tensor_patterns = set(custom_patterns)
        else:
            self.suspicious_tensor_patterns = custom_patterns

        # Load dtype validation strictness
        self.dtype_validation_level = policy_config.get("dtype_validation_level", "medium")  # low, medium, high

        # Load allowed dtypes (policy can restrict certain dtypes)
        default_allowed_dtypes = {"F32", "F16", "BF16", "I32", "I16", "I8", "U8", "BOOL"}
        self.allowed_dtypes = set(policy_config.get("allowed_dtypes", default_allowed_dtypes))

        # Load byte range validation settings
        self.strict_byte_range_validation = policy_config.get("strict_byte_range_validation", True)

        # Load shard coverage validation settings
        self.require_complete_shard_coverage = policy_config.get("require_complete_shard_coverage", True)

        # Load parameter count drift tolerance
        self.parameter_drift_tolerance = policy_config.get("parameter_drift_tolerance", 0.02)  # 2% default

        # Load cross-shard validation settings
        self.validate_cross_shard_consistency = policy_config.get("validate_cross_shard_consistency", True)

    def can_validate(self, model_type: ModelType) -> bool:
        """This validator only handles safetensors format."""
        return model_type == ModelType.SAFETENSORS

    def validate(self, data: bytes) -> List[Dict[str, Any]]:
        """CRITICAL: Validate safetensors file integrity using Rust backend.
        
        Performs comprehensive validation including:
        - Structure validation (header parsing, JSON validation)
        - Tensor name security checks (suspicious patterns)
        - Data offset validation
        - Tensor data scanning for malicious patterns (executables, scripts)
        - Metadata validation
        """
        from palisade._native import validate_safetensors
        
        # Call Rust validation
        result = validate_safetensors(data)
        
        # Convert Rust results to Python warnings
        for warning_msg in result.warnings:
            # Determine severity based on warning content
            if "exceeds" in warning_msg or "invalid" in warning_msg.lower():
                severity = Severity.HIGH
            elif "suspicious" in warning_msg.lower():
                severity = Severity.HIGH
            else:
                severity = Severity.MEDIUM
            
            warning = self.create_standard_warning(
                warning_type="safetensors_validation_issue",
                message=warning_msg,
                severity=severity,
                recommendation="Review file integrity and tensor content",
                threat_type="file_corruption" if "header" in warning_msg.lower() else "supply_chain_attack",
                attack_vector="Malformed safetensors or suspicious content"
            )
            self.warnings.append(warning)
        
        # Suspicious tensor names
        if result.suspicious_tensor_names:
            warning = self.create_standard_warning(
                warning_type="suspicious_tensor_names",
                message=f"Found {len(result.suspicious_tensor_names)} suspicious tensor names",
                severity=Severity.HIGH,
                recommendation="Review tensor names for malicious patterns",
                suspicious_tensors=result.suspicious_tensor_names[:20],  # Limit to first 20
                total_suspicious=len(result.suspicious_tensor_names),
                threat_type="supply_chain_attack",
                attack_vector="Malicious tensor naming patterns"
            )
            self.warnings.append(warning)
        
        # Suspicious data patterns (CRITICAL)
        if result.suspicious_data_patterns:
            warning = self.create_standard_warning(
                warning_type="suspicious_data_patterns",
                message="CRITICAL: Suspicious patterns detected in tensor data",
                severity=Severity.CRITICAL,
                recommendation="DO NOT LOAD THIS MODEL - Contains potentially malicious data",
                patterns_detected=result.suspicious_data_patterns,
                threat_type="code_injection",
                attack_vector="Embedded executable code or scripts in tensor data"
            )
            self.warnings.append(warning)

        # Add safetensors-specific context for policy evaluation
        context = {
            "safetensors": {
                "integrity_violation": any("integrity" in str(w).lower() or "corruption" in str(w).lower() for w in self.warnings),
                "suspicious_patterns": any("suspicious" in str(w).lower() for w in self.warnings),
                "validation_errors": any("error" in str(w).lower() for w in self.warnings),
            },
        }

        # Apply policy evaluation if policy engine is available
        if self.policy_engine:
            return self.apply_policy(self.warnings, context.get("model_path", ""), context)

        return self.warnings

    def validate_streaming(self, model_file: "ModelFile") -> List[Dict[str, Any]]:
        """Stream-based validation for large safetensors files using Rust backend.

        Safetensors format:
        1. 8-byte header length
        2. JSON header with metadata
        3. Tensor data

        Uses Rust SafeTensorsStreamingValidator for high-performance streaming validation
        with parallel pattern matching and boundary handling.
        """
        from palisade._native import SafeTensorsStreamingValidator
        import multiprocessing
        
        warnings = []

        try:
            # Create Rust streaming validator with parallel pattern matching
            num_cores = multiprocessing.cpu_count()
            validator = SafeTensorsStreamingValidator(num_cores)
            
            # Read complete SafeTensors header (reads exact header size from file)
            header_data = model_file.read_safetensors_header()
            
            if not validator.validate_header(header_data):
                # Header validation failed - get errors from Rust
                result = validator.finalize()
                
                # Convert Rust warnings to Python format
                for warning_msg in result.warnings:
                    severity = Severity.HIGH if "invalid" in warning_msg.lower() else Severity.MEDIUM
                    warnings.append(self.create_standard_warning(
                        "safetensors_streaming_header_error",
                        warning_msg,
                        severity,
                        recommendation="Review file integrity and header structure",
                        threat_type="file_corruption",
                        attack_vector="Malformed SafeTensors header"
                    ))
                
                return warnings
            
            # Get header size from header data
            header_size = struct.unpack("<Q", header_data[:8])[0]
            data_offset = 8 + header_size
            
            # Process ALL chunks including header (GIL released in Rust)
            # Scanning the header is important for detecting malicious patterns in:
            # - Metadata fields (e.g., malicious commands in __metadata__)
            # - Steganography attempts (e.g., base64 encoded payloads)
            # - Binary data embedded in JSON strings
            chunk_patterns_found = []
            
            for chunk_info in model_file.iter_chunk_info():
                # Process chunk with Rust (parallel pattern matching, GIL released)
                patterns = validator.process_chunk(chunk_info.data)
                
                if patterns:
                    chunk_patterns_found.extend(patterns)
                    
                    # Optionally report patterns per chunk for debugging
                    logger.debug(
                        f"Chunk at offset {chunk_info.offset}: Found {len(patterns)} suspicious patterns"
                    )
            
            # Finalize and get complete results
            result = validator.finalize()
            
            # Convert Rust results to Python warnings
            for warning_msg in result.warnings:
                # Determine severity based on warning content
                if "exceeds" in warning_msg or "invalid" in warning_msg.lower():
                    severity = Severity.HIGH
                elif "suspicious" in warning_msg.lower():
                    severity = Severity.HIGH
                else:
                    severity = Severity.MEDIUM
                
                warnings.append(self.create_standard_warning(
                    "safetensors_streaming_validation_issue",
                    warning_msg,
                    severity,
                    recommendation="Review file integrity and tensor content",
                    threat_type="file_corruption" if "header" in warning_msg.lower() else "supply_chain_attack",
                    attack_vector="Malformed safetensors or suspicious content"
                ))
            
            # Suspicious tensor names
            if result.suspicious_tensor_names:
                warnings.append(self.create_standard_warning(
                    "suspicious_tensor_names",
                    f"Found {len(result.suspicious_tensor_names)} suspicious tensor names",
                    Severity.HIGH,
                    recommendation="Review tensor names for malicious patterns",
                    suspicious_tensors=result.suspicious_tensor_names[:20],  # Limit to first 20
                    total_suspicious=len(result.suspicious_tensor_names),
                    threat_type="supply_chain_attack",
                    attack_vector="Malicious tensor naming patterns"
                ))
            
            # Suspicious data patterns (CRITICAL)
            if result.suspicious_data_patterns:
                warnings.append(self.create_standard_warning(
                    "suspicious_data_patterns",
                    "CRITICAL: Suspicious patterns detected in tensor data",
                    Severity.CRITICAL,
                    recommendation="DO NOT LOAD THIS MODEL - Contains potentially malicious data",
                    patterns_detected=result.suspicious_data_patterns,
                    threat_type="code_injection",
                    attack_vector="Embedded executable code or scripts in tensor data"
                ))

            # Add safetensors-specific context for policy evaluation
            context = {
                "safetensors": {
                    "integrity_violation": any("integrity" in str(w).lower() or "corruption" in str(w).lower() for w in warnings),
                    "suspicious_patterns": any("suspicious" in str(w).lower() for w in warnings),
                    "validation_errors": any("error" in str(w).lower() for w in warnings),
                    "streaming_mode": True,
                    "chunks_processed": len(chunk_patterns_found) if chunk_patterns_found else 0,
                },
            }

            # Apply policy evaluation if policy engine is available
            if self.policy_engine:
                return self.apply_policy(warnings, context.get("model_path", ""), context)
            
        except Exception as e:
            logger.error(f"Error in safetensors streaming validation: {str(e)}")
            import traceback
            traceback.print_exc()
            
            warnings.append(self.create_standard_warning(
                "safetensors_streaming_error",
                f"Error during safetensors streaming validation: {str(e)}",
                Severity.MEDIUM,
                recommendation="Review error and consider re-scanning",
                threat_type="validation_error"
            ))

        return warnings

    def _validate_safetensors_metadata(self, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate safetensors metadata structure."""
        warnings = []

        try:
            # Check for required structure
            if not isinstance(metadata, dict):
                warnings.append(self.create_standard_warning(
                    "safetensors_invalid_metadata_type",
                    "Safetensors metadata must be a dictionary",
                    Severity.HIGH,
                ))
                return warnings

            # Check for tensor definitions
            tensor_count = 0
            for key, value in metadata.items():
                if key != "__metadata__":
                    tensor_count += 1
                    if not isinstance(value, dict):
                        warnings.append(self.create_standard_warning(
                            "safetensors_invalid_tensor_def",
                            f"Tensor '{key}' definition must be a dictionary",
                            Severity.MEDIUM,
                        ))
                    elif not all(k in value for k in ["dtype", "shape", "data_offsets"]):
                        warnings.append(self.create_standard_warning(
                            "safetensors_incomplete_tensor_def",
                            f"Tensor '{key}' missing required fields (dtype, shape, data_offsets)",
                            Severity.MEDIUM,
                        ))

            if tensor_count == 0:
                warnings.append(self.create_standard_warning(
                    "safetensors_no_tensors",
                    "No tensor definitions found in safetensors metadata",
                    Severity.HIGH,
                ))

        except Exception as e:
            warnings.append(self.create_standard_warning(
                "safetensors_metadata_validation_error",
                f"Error validating safetensors metadata: {str(e)}",
                Severity.MEDIUM,
            ))

        return warnings

    def _check_tensor_names_from_metadata(self, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check tensor names for suspicious patterns from metadata."""
        warnings = []

        try:
            for tensor_name in metadata:
                if tensor_name == "__metadata__":
                    continue

                # Check for suspicious patterns
                for pattern in self.suspicious_tensor_patterns:
                    if pattern.lower() in tensor_name.lower():
                        warnings.append(self.create_standard_warning(
                            "safetensors_suspicious_tensor_name",
                            f"Suspicious tensor name pattern '{pattern}' found in '{tensor_name}'",
                            Severity.MEDIUM,
                            tensor_name=tensor_name,
                            suspicious_pattern=pattern,
                        ))

        except Exception as e:
            warnings.append(self.create_standard_warning(
                "safetensors_tensor_name_check_error",
                f"Error checking tensor names: {str(e)}",
                Severity.LOW,
            ))

        return warnings

    def validate_sharded_model(self, model_directory: str) -> List[Dict[str, Any]]:
        """CRITICAL: Validate sharded safetensors model integrity
        This is the main security check for multi-file models.
        """
        warnings = []

        try:
            # SECURITY: Validate model directory path
            if not is_safe_directory(model_directory):
                warnings.append({
                    "type": "unsafe_model_directory",
                    "details": {
                        "message": f"Model directory path failed security validation: {model_directory}",
                        "directory": str(model_directory),
                        "risk_level": "CRITICAL",
                        "recommendation": "Use safe model directory path",
                    },
                    "severity": "critical",
                })
                return warnings

            model_dir = Path(model_directory).resolve()

            # Find index file with security validation
            index_file = model_dir / "model.safetensors.index.json"

            # SECURITY: Validate index file path
            try:
                safe_index_path = validate_file_path(index_file, base_dir=model_dir)
            except SecurePathError:
                # Try alternative index patterns
                index_files = []
                for pattern_file in model_dir.glob("*.safetensors.index.json"):
                    try:
                        safe_path = validate_file_path(pattern_file, base_dir=model_dir)
                        index_files.append(safe_path)
                    except SecurePathError:
                        continue

                if not index_files:
                    return warnings  # No sharded model
                safe_index_path = index_files[0]
                logger.info(f"Found alternative index file: {safe_index_path}")

            if not safe_index_path.exists():
                return warnings  # No sharded model

            # Parse and validate index
            index_issues = self._validate_index_file(safe_index_path)
            if index_issues:
                warnings.extend(index_issues)

            # SECURITY: Load index using safe file access
            with safe_open_file(safe_index_path, "r") as f:
                index_data = json.load(f)

            # Validate each shard
            shard_issues = self._validate_shards(model_dir, index_data)
            warnings.extend(shard_issues)

            # Validate tensor completeness
            completeness_issues = self._validate_tensor_completeness(model_dir, index_data)
            warnings.extend(completeness_issues)

            # Cross-validate index vs actual shards
            consistency_issues = self._validate_index_consistency(model_dir, index_data)
            warnings.extend(consistency_issues)

            # CRITICAL: Validate byte-range overlaps and gaps (NEW SECURITY ENHANCEMENT)
            byte_range_issues = self._validate_byte_range_integrity(model_dir, index_data)
            warnings.extend(byte_range_issues)

            # CRITICAL: Validate shard coverage and bundle integrity (NEW SECURITY ENHANCEMENT)
            shard_coverage_issues = self._validate_shard_coverage_integrity(model_dir, index_data)
            warnings.extend(shard_coverage_issues)

            # CRITICAL: Validate shape math and parameter count accuracy (NEW SECURITY ENHANCEMENT)
            shape_math_issues = self._validate_shape_math_integrity(model_dir, index_data)
            warnings.extend(shape_math_issues)

            # CRITICAL: Validate dtype coherence across model
            dtype_issues = self._validate_dtype_coherence(model_dir, index_data)
            warnings.extend(dtype_issues)

        except Exception as e:
            logger.error(f"Error in sharded model validation: {str(e)}")
            warnings.append({
                "type": "sharded_validation_error",
                "details": {
                    "message": "Error validating sharded model integrity",
                    "error": str(e),
                    "recommendation": "Manual verification of model files recommended",
                },
                "severity": "high",
            })

        return warnings

    def _validate_safetensors_structure(self, data: bytes) -> Optional[Dict[str, Any]]:
        """Validate basic safetensors file structure using Rust backend."""
        from palisade._native import validate_safetensors
        
        result = validate_safetensors(data)
        
        if not result.is_valid:
            # Convert Rust warnings to Python format
            return {
                "message": "Safetensors structure validation failed",
                "header_size": result.header_size,
                "tensor_count": result.tensor_count,
                "warnings": result.warnings,
                "recommendation": "File may be corrupted, malformed, or contain suspicious tensor names",
            }
        
        # File is valid
        return None

    def _validate_index_file(self, index_file: Path) -> List[Dict[str, Any]]:
        """Validate the safetensors index file structure."""
        warnings = []

        try:
            with open(index_file) as f:
                index_data = json.load(f)

            # Check required keys
            missing_keys = self.expected_index_keys - set(index_data.keys())
            if missing_keys:
                warnings.append({
                    "type": "missing_index_keys",
                    "details": {
                        "message": "Missing required keys in index file",
                        "missing_keys": list(missing_keys),
                        "recommendation": "Index file may be corrupted or malformed",
                    },
                    "severity": "high",
                })

            # Validate weight_map structure
            if "weight_map" in index_data:
                weight_map = index_data["weight_map"]
                if not isinstance(weight_map, dict):
                    warnings.append({
                        "type": "invalid_weight_map",
                        "details": {
                            "message": "weight_map must be a dictionary",
                            "actual_type": type(weight_map).__name__,
                            "recommendation": "Index file structure is invalid",
                        },
                        "severity": "high",
                    })
                else:
                    # Check for suspicious shard names
                    suspicious_shards = []
                    for tensor, shard in weight_map.items():
                        if not isinstance(shard, str):
                            continue

                        # Check for path traversal attempts
                        if ".." in shard or shard.startswith("/") or "\\" in shard:
                            suspicious_shards.append({
                                "tensor": tensor,
                                "shard": shard,
                                "risk": "Path traversal attempt",
                            })

                        # Check for non-safetensors extensions
                        if not shard.endswith(".safetensors"):
                            suspicious_shards.append({
                                "tensor": tensor,
                                "shard": shard,
                                "risk": "Non-safetensors shard file",
                            })

                    if suspicious_shards:
                        warnings.append({
                            "type": "suspicious_shard_paths",
                            "details": {
                                "message": "Suspicious shard file paths detected",
                                "suspicious_shards": suspicious_shards[:10],
                                "total_suspicious": len(suspicious_shards),
                                "recommendation": "Verify shard file paths for security",
                            },
                            "severity": "high",
                        })

        except (OSError, json.JSONDecodeError) as e:
            warnings.append({
                "type": "index_parse_error",
                "details": {
                    "message": "Failed to parse index file",
                    "error": str(e),
                    "recommendation": "Index file may be corrupted",
                },
                "severity": "high",
            })

        return warnings

    def _validate_shards(self, model_dir: Path, index_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate individual shard files."""
        warnings = []

        if "weight_map" not in index_data:
            return warnings

        # Get unique shard files
        shard_files = set(index_data["weight_map"].values())

        for shard_name in shard_files:
            shard_path = model_dir / shard_name

            # Check if shard exists
            if not shard_path.exists():
                warnings.append({
                    "type": "missing_shard",
                    "details": {
                        "message": f"Shard file missing: {shard_name}",
                        "shard": shard_name,
                        "recommendation": "Model incomplete - missing shard files",
                    },
                    "severity": "critical",
                })
                continue

            # Validate shard file integrity
            try:
                with open(shard_path, "rb") as f:
                    shard_data = f.read()

                # Basic safetensors structure check
                structure_issue = self._validate_safetensors_structure(shard_data)
                if structure_issue:
                    warnings.append({
                        "type": "shard_structure_invalid",
                        "details": {
                            "message": f"Invalid shard structure: {shard_name}",
                            "shard": shard_name,
                            "issue": structure_issue,
                            "recommendation": "Shard file may be corrupted",
                        },
                        "severity": "high",
                    })

            except OSError as e:
                warnings.append({
                    "type": "shard_read_error",
                    "details": {
                        "message": f"Cannot read shard file: {shard_name}",
                        "shard": shard_name,
                        "error": str(e),
                        "recommendation": "Check file permissions and integrity",
                    },
                    "severity": "high",
                })

        return warnings

    def _validate_tensor_completeness(self, model_dir: Path, index_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate that all tensors in shards match the index."""
        warnings = []

        if "weight_map" not in index_data:
            return warnings

        try:
            # Get tensors declared in index
            index_tensors = set(index_data["weight_map"].keys())

            # Get actual tensors from shard files
            actual_tensors = set()
            shard_files = set(index_data["weight_map"].values())

            for shard_name in shard_files:
                shard_path = model_dir / shard_name
                if not shard_path.exists():
                    continue

                try:
                    with open(shard_path, "rb") as f:
                        shard_data = f.read()

                    # Parse shard header
                    header_size = struct.unpack("<Q", shard_data[:8])[0]
                    header_data = shard_data[8:8+header_size]
                    header_json = json.loads(header_data.decode("utf-8"))

                    # Add tensor names (excluding metadata)
                    for tensor_name in header_json:
                        if tensor_name != "__metadata__":
                            actual_tensors.add(tensor_name)

                except Exception as e:
                    logger.debug(f"Error reading shard {shard_name}: {str(e)}")
                    continue

            # Check for missing tensors
            missing_tensors = index_tensors - actual_tensors
            if missing_tensors:
                warnings.append({
                    "type": "missing_tensors",
                    "details": {
                        "message": "Tensors declared in index but missing from shards",
                        "missing_tensors": list(missing_tensors)[:20],  # Limit output
                        "total_missing": len(missing_tensors),
                        "recommendation": "Model may be incomplete or corrupted",
                    },
                    "severity": "critical",
                })

            # Check for extra tensors (potential rogue tensors)
            extra_tensors = actual_tensors - index_tensors
            if extra_tensors:
                warnings.append({
                    "type": "rogue_tensors",
                    "details": {
                        "message": "SECURITY: Rogue tensors found in shards not declared in index",
                        "rogue_tensors": list(extra_tensors)[:20],  # Limit output
                        "total_rogue": len(extra_tensors),
                        "recommendation": "Potential tampering - unauthorized tensors detected",
                    },
                    "severity": "critical",
                })

        except Exception as e:
            warnings.append({
                "type": "tensor_completeness_error",
                "details": {
                    "message": "Error validating tensor completeness",
                    "error": str(e),
                    "recommendation": "Manual verification recommended",
                },
                "severity": "medium",
            })

        return warnings

    def _validate_index_consistency(self, model_dir: Path, index_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Cross-validate index mapping vs actual shard contents."""
        warnings = []

        if "weight_map" not in index_data:
            return warnings

        try:
            # Validate each tensor -> shard mapping
            inconsistencies = []

            for tensor_name, declared_shard in index_data["weight_map"].items():
                shard_path = model_dir / declared_shard
                if not shard_path.exists():
                    continue

                try:
                    with open(shard_path, "rb") as f:
                        shard_data = f.read()

                    # Parse shard to check if tensor exists
                    header_size = struct.unpack("<Q", shard_data[:8])[0]
                    header_data = shard_data[8:8+header_size]
                    header_json = json.loads(header_data.decode("utf-8"))

                    if tensor_name not in header_json:
                        inconsistencies.append({
                            "tensor": tensor_name,
                            "declared_shard": declared_shard,
                            "issue": "Tensor not found in declared shard",
                        })

                except Exception as e:
                    logger.debug(f"Error checking tensor {tensor_name}: {str(e)}")
                    continue

            if inconsistencies:
                warnings.append({
                    "type": "index_shard_mismatch",
                    "details": {
                        "message": "Index-shard mapping inconsistencies detected",
                        "inconsistencies": inconsistencies[:10],  # Limit output
                        "total_inconsistencies": len(inconsistencies),
                        "recommendation": "Index file may be corrupted or tampered with",
                    },
                    "severity": "high",
                })

        except Exception as e:
            warnings.append({
                "type": "consistency_check_error",
                "details": {
                    "message": "Error validating index consistency",
                    "error": str(e),
                    "recommendation": "Manual verification recommended",
                },
                "severity": "medium",
            })

        return warnings

    def _validate_dtype_coherence(self, model_dir: Path, index_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """CRITICAL: Validate dtype coherence across model shards
        Detects mixed-precision attacks and dtype mismatches.
        """
        warnings = []

        if "weight_map" not in index_data:
            return warnings

        try:
            # Collect all tensor dtypes from shards
            tensor_dtypes = {}  # tensor_name -> dtype
            component_dtypes = {}  # component_type -> {tensor_name: dtype}
            shard_dtypes = {}  # shard_file -> {tensor_name: dtype}

            # Process each shard
            shard_files = set(index_data["weight_map"].values())

            for shard_name in shard_files:
                shard_path = model_dir / shard_name
                if not shard_path.exists():
                    continue

                try:
                    # Parse shard header to get tensor dtypes
                    with open(shard_path, "rb") as f:
                        shard_data = f.read()

                    header_size = struct.unpack("<Q", shard_data[:8])[0]
                    header_data = shard_data[8:8+header_size]
                    header_json = json.loads(header_data.decode("utf-8"))

                    shard_tensor_dtypes = {}

                    # Extract dtypes for all tensors in this shard
                    for tensor_name, tensor_info in header_json.items():
                        if tensor_name == "__metadata__":
                            continue

                        if isinstance(tensor_info, dict) and "dtype" in tensor_info:
                            dtype = tensor_info["dtype"]
                            tensor_dtypes[tensor_name] = dtype
                            shard_tensor_dtypes[tensor_name] = dtype

                            # Categorize by component type
                            component_type = self._classify_tensor_component(tensor_name)
                            if component_type not in component_dtypes:
                                component_dtypes[component_type] = {}
                            component_dtypes[component_type][tensor_name] = dtype

                    shard_dtypes[shard_name] = shard_tensor_dtypes

                except Exception as e:
                    logger.debug(f"Error reading shard {shard_name} for dtype validation: {str(e)}")
                    continue

            if not tensor_dtypes:
                return warnings

            # Validate cross-shard dtype consistency
            cross_shard_issues = self._check_cross_shard_dtype_consistency(shard_dtypes, index_data)
            warnings.extend(cross_shard_issues)

            # Validate component-level dtype coherence
            component_issues = self._check_component_dtype_coherence(component_dtypes)
            warnings.extend(component_issues)

            # Check for suspicious mixed precision patterns
            mixed_precision_issues = self._check_suspicious_mixed_precision(tensor_dtypes, component_dtypes)
            warnings.extend(mixed_precision_issues)

            # Validate against metadata if available
            metadata_issues = self._check_metadata_dtype_consistency(model_dir, tensor_dtypes)
            warnings.extend(metadata_issues)

        except Exception as e:
            warnings.append({
                "type": "dtype_validation_error",
                "details": {
                    "message": "Error validating dtype coherence",
                    "error": str(e),
                    "recommendation": "Manual dtype verification recommended",
                },
                "severity": "medium",
            })

        return warnings

    def _classify_tensor_component(self, tensor_name: str) -> str:
        """Classify tensor by model component type."""
        tensor_lower = tensor_name.lower()

        for component_type, patterns in self.core_component_patterns.items():
            for pattern in patterns:
                if pattern in tensor_lower:
                    return component_type

        return "other"

    def _check_cross_shard_dtype_consistency(self, shard_dtypes: Dict[str, Dict[str, str]],
                                           index_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for dtype consistency across shards."""
        warnings = []

        # Verify that tensors referenced in index match shard dtypes
        for tensor_name, expected_shard in index_data["weight_map"].items():
            if expected_shard in shard_dtypes:
                shard_tensors = shard_dtypes[expected_shard]
                if tensor_name not in shard_tensors:
                    warnings.append({
                        "type": "tensor_missing_in_shard",
                        "details": {
                            "message": f"Tensor {tensor_name} declared in index but missing from shard",
                            "tensor": tensor_name,
                            "expected_shard": expected_shard,
                            "recommendation": "Index-shard mapping is inconsistent",
                        },
                        "severity": "high",
                    })

        return warnings

    def _check_component_dtype_coherence(self, component_dtypes: Dict[str, Dict[str, str]]) -> List[Dict[str, Any]]:
        """Check dtype coherence within model components."""
        warnings = []

        for component_type, tensors in component_dtypes.items():
            if len(tensors) <= 1:
                continue  # Skip components with single tensor

            # Get unique dtypes in this component
            unique_dtypes = set(tensors.values())

            if len(unique_dtypes) > 1:
                # Mixed dtypes in component - check if it's suspicious
                dtype_counts = {}
                for _tensor, dtype in tensors.items():
                    dtype_counts[dtype] = dtype_counts.get(dtype, 0) + 1

                # Determine severity based on component type and dtype mix
                severity = self._assess_mixed_dtype_severity(component_type, unique_dtypes, dtype_counts)

                if severity != "none":
                    warnings.append({
                        "type": "mixed_dtype_component",
                        "details": {
                            "message": f"Mixed dtypes detected in {component_type} component",
                            "component": component_type,
                            "dtypes": list(unique_dtypes),
                            "dtype_distribution": dtype_counts,
                            "affected_tensors": len(tensors),
                            "recommendation": "Verify mixed precision is intentional",
                        },
                        "severity": severity,
                    })

        return warnings

    def _assess_mixed_dtype_severity(self, component_type: str, dtypes: Set[str],
                                   dtype_counts: Dict[str, int]) -> str:
        """Assess severity of mixed dtypes in component."""
        # Core attention/FFN components should typically be uniform
        critical_components = {"attention", "feedforward"}

        if component_type in critical_components:
            # Mixed precision in critical components is suspicious
            if "I8" in dtypes or "U8" in dtypes:
                return "medium"  # Quantization might be acceptable
            elif len(dtypes) > 2:
                return "high"   # Too many different precisions
            else:
                return "medium" # Simple mixed precision

        # Other components can have more flexibility
        elif len(dtypes) > 3:
            return "medium"  # Too many different dtypes
        elif "I8" in dtypes and "F32" not in dtypes:
            return "high"    # Quantized without full precision backup
        else:
            return "low"     # Probably acceptable

    def _check_suspicious_mixed_precision(self, tensor_dtypes: Dict[str, str],
                                        component_dtypes: Dict[str, Dict[str, str]]) -> List[Dict[str, Any]]:
        """Detect suspicious mixed precision patterns."""
        warnings = []

        all_dtypes = set(tensor_dtypes.values())
        dtype_counts = {}
        for dtype in tensor_dtypes.values():
            dtype_counts[dtype] = dtype_counts.get(dtype, 0) + 1

        total_tensors = len(tensor_dtypes)

        # Check for unusual dtype distributions
        suspicious_patterns = []

        # Pattern 1: Single tensor with different dtype (potential backdoor)
        for dtype, count in dtype_counts.items():
            if count == 1 and total_tensors > 10:  # Only one tensor with this dtype
                # Find the outlier tensor
                outlier_tensor = next(name for name, dt in tensor_dtypes.items() if dt == dtype)
                suspicious_patterns.append({
                    "pattern": "dtype_outlier",
                    "description": f"Single tensor '{outlier_tensor}' has unique dtype {dtype}",
                    "tensor": outlier_tensor,
                    "dtype": dtype,
                    "risk": "Potential backdoor tensor with different precision",
                })

        # Pattern 2: Unexpected high-precision in quantized model
        if "I8" in all_dtypes and "F32" in all_dtypes:
            f32_count = dtype_counts.get("F32", 0)
            i8_count = dtype_counts.get("I8", 0)

            if f32_count < i8_count / 10:  # Less than 10% F32 in quantized model
                suspicious_patterns.append({
                    "pattern": "sparse_full_precision",
                    "description": "Very few full-precision tensors in quantized model",
                    "f32_count": f32_count,
                    "i8_count": i8_count,
                    "risk": "Unusual quantization pattern - verify integrity",
                })

        # Pattern 3: Mixed BF16/F16 (unusual combination)
        if "BF16" in all_dtypes and "F16" in all_dtypes:
            suspicious_patterns.append({
                "pattern": "bf16_f16_mix",
                "description": "Model mixes BF16 and F16 dtypes",
                "bf16_count": dtype_counts.get("BF16", 0),
                "f16_count": dtype_counts.get("F16", 0),
                "risk": "Unusual precision mixing - verify intentional",
            })

        if suspicious_patterns:
            warnings.append({
                "type": "suspicious_mixed_precision",
                "details": {
                    "message": "Suspicious mixed precision patterns detected",
                    "patterns": suspicious_patterns,
                    "dtype_distribution": dtype_counts,
                    "recommendation": "Verify precision patterns are legitimate",
                },
                "severity": "high",
            })

        return warnings

    def _check_metadata_dtype_consistency(self, model_dir: Path,
                                        tensor_dtypes: Dict[str, str]) -> List[Dict[str, Any]]:
        """Check if tensor dtypes match model metadata claims."""
        warnings = []

        try:
            # Look for config.json that might specify dtype
            config_file = model_dir / "config.json"
            if config_file.exists():
                with open(config_file) as f:
                    config_data = json.load(f)

                # Check for dtype specification in config
                claimed_dtype = None
                dtype_fields = ["torch_dtype", "dtype", "model_dtype", "precision"]

                for field in dtype_fields:
                    if field in config_data:
                        claimed_dtype = str(config_data[field])
                        break

                if claimed_dtype:
                    # Map config dtype to safetensors dtype
                    config_to_safetensors = {
                        "torch.float32": "F32",
                        "torch.float16": "F16",
                        "torch.bfloat16": "BF16",
                        "float32": "F32",
                        "float16": "F16",
                        "bfloat16": "BF16",
                        "fp32": "F32",
                        "fp16": "F16",
                        "bf16": "BF16",
                    }

                    expected_dtype = config_to_safetensors.get(claimed_dtype.lower())
                    if expected_dtype:
                        # Check if actual dtypes match claimed dtype
                        actual_dtypes = set(tensor_dtypes.values())

                        # Allow some flexibility for embeddings/output layers
                        core_dtypes = set()
                        for tensor_name, dtype in tensor_dtypes.items():
                            if not any(pattern in tensor_name.lower()
                                     for pattern in ["embed", "lm_head", "classifier"]):
                                core_dtypes.add(dtype)

                        if expected_dtype not in core_dtypes and len(core_dtypes) > 0:
                            warnings.append({
                                "type": "metadata_dtype_mismatch",
                                "details": {
                                    "message": "Model metadata dtype doesn't match tensor dtypes",
                                    "claimed_dtype": claimed_dtype,
                                    "expected_safetensors_dtype": expected_dtype,
                                    "actual_core_dtypes": list(core_dtypes),
                                    "actual_all_dtypes": list(actual_dtypes),
                                    "recommendation": "Verify model precision matches metadata",
                                },
                                "severity": "medium",
                            })

        except Exception as e:
            logger.debug(f"Error checking metadata dtype consistency: {str(e)}")

        return warnings

    def _validate_byte_range_integrity(self, model_dir: Path, index_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """CRITICAL SECURITY ENHANCEMENT: Validate byte-range overlaps and gaps.

        Prevents sophisticated attacks:
        - Overlapping tensor ranges (double-allocation attacks)
        - Byte-range gaps (incomplete model attacks)
        - Size manipulation attacks
        - Cross-shard data corruption attempts
        """
        warnings = []

        if "weight_map" not in index_data:
            return warnings

        try:
            # Collect byte ranges for all tensors across all shards
            shard_byte_ranges = {}  # shard_file -> [(start, end, tensor_name), ...]
            global_tensor_ranges = []  # [(start, end, tensor_name, shard_file), ...]

            # Process each shard to extract tensor byte ranges
            shard_files = set(index_data["weight_map"].values())

            for shard_name in shard_files:
                shard_path = model_dir / shard_name
                if not shard_path.exists():
                    continue

                try:
                    # Parse shard to get tensor byte ranges
                    with open(shard_path, "rb") as f:
                        shard_data = f.read()

                    if len(shard_data) < 8:
                        continue

                    header_size = struct.unpack("<Q", shard_data[:8])[0]
                    if header_size > len(shard_data) - 8:
                        continue

                    header_data = shard_data[8:8+header_size]
                    header_json = json.loads(header_data.decode("utf-8"))

                    shard_ranges = []
                    data_start_offset = 8 + header_size

                    # Calculate byte ranges for each tensor in this shard
                    for tensor_name, tensor_info in header_json.items():
                        if tensor_name == "__metadata__":
                            continue

                        if isinstance(tensor_info, dict) and "data_offsets" in tensor_info:
                            # Extract start and end offsets
                            offsets = tensor_info["data_offsets"]
                            if len(offsets) >= 2:
                                relative_start = offsets[0]  # Relative to data section
                                relative_end = offsets[1]    # Relative to data section

                                absolute_start = data_start_offset + relative_start
                                absolute_end = data_start_offset + relative_end

                                # Validate range sanity
                                if absolute_start >= absolute_end:
                                    warnings.append({
                                        "type": "invalid_tensor_range",
                                        "details": {
                                            "message": f"CRITICAL: Invalid byte range for tensor {tensor_name}",
                                            "tensor": tensor_name,
                                            "shard": shard_name,
                                            "start_offset": absolute_start,
                                            "end_offset": absolute_end,
                                            "risk_level": "CRITICAL",
                                            "recommendation": "Tensor has invalid byte range - potential corruption",
                                        },
                                        "severity": "critical",
                                    })
                                    continue

                                if absolute_end > len(shard_data):
                                    warnings.append({
                                        "type": "tensor_range_exceeds_file",
                                        "details": {
                                            "message": "CRITICAL: Tensor range exceeds file size",
                                            "tensor": tensor_name,
                                            "shard": shard_name,
                                            "end_offset": absolute_end,
                                            "file_size": len(shard_data),
                                            "risk_level": "CRITICAL",
                                            "recommendation": "Tensor byte range exceeds shard file - corruption detected",
                                        },
                                        "severity": "critical",
                                    })
                                    continue

                                shard_ranges.append((absolute_start, absolute_end, tensor_name))
                                global_tensor_ranges.append((absolute_start, absolute_end, tensor_name, shard_name))

                    shard_byte_ranges[shard_name] = shard_ranges

                except Exception as e:
                    logger.debug(f"Error parsing byte ranges in shard {shard_name}: {str(e)}")
                    continue

            # CRITICAL CHECK 1: Detect overlapping byte ranges within each shard
            overlap_warnings = self._detect_byte_range_overlaps(shard_byte_ranges)
            warnings.extend(overlap_warnings)

            # CRITICAL CHECK 2: Detect gaps in tensor data within each shard
            gap_warnings = self._detect_byte_range_gaps(model_dir, shard_byte_ranges)
            warnings.extend(gap_warnings)

            # CRITICAL CHECK 3: Validate tensor size consistency
            size_warnings = self._validate_tensor_size_consistency(model_dir, index_data, shard_byte_ranges)
            warnings.extend(size_warnings)

            # CRITICAL CHECK 4: Cross-shard byte range validation
            cross_shard_warnings = self._validate_cross_shard_byte_ranges(global_tensor_ranges, index_data)
            warnings.extend(cross_shard_warnings)

        except Exception as e:
            warnings.append({
                "type": "byte_range_validation_error",
                "details": {
                    "message": "Error validating byte-range integrity",
                    "error": str(e),
                    "risk_level": "HIGH",
                    "recommendation": "Manual verification of shard byte ranges recommended",
                },
                "severity": "high",
            })

        return warnings

    def _detect_byte_range_overlaps(self, shard_byte_ranges: Dict[str, List]) -> List[Dict[str, Any]]:
        """Detect overlapping byte ranges within each shard - CRITICAL security check."""
        warnings = []

        for shard_name, ranges in shard_byte_ranges.items():
            if len(ranges) <= 1:
                continue

            # Sort ranges by start position
            sorted_ranges = sorted(ranges, key=lambda x: x[0])

            # Check for overlaps between adjacent ranges
            overlaps = []
            for i in range(len(sorted_ranges) - 1):
                current_start, current_end, current_tensor = sorted_ranges[i]
                next_start, next_end, next_tensor = sorted_ranges[i + 1]

                # Check if current range overlaps with next range
                if current_end > next_start:
                    overlap_size = current_end - next_start
                    overlaps.append({
                        "tensor1": current_tensor,
                        "tensor1_range": (current_start, current_end),
                        "tensor2": next_tensor,
                        "tensor2_range": (next_start, next_end),
                        "overlap_start": next_start,
                        "overlap_size": overlap_size,
                    })

            if overlaps:
                warnings.append({
                    "type": "byte_range_overlaps",
                    "details": {
                        "message": f"CRITICAL: Overlapping byte ranges detected in shard {shard_name}",
                        "shard": shard_name,
                        "overlaps": overlaps[:5],  # Limit output for readability
                        "total_overlaps": len(overlaps),
                        "risk_level": "CRITICAL",
                        "attack_vector": "Double-allocation attack - tensors share memory ranges",
                        "recommendation": "NEVER load this model - overlapping ranges indicate tampering",
                    },
                    "severity": "critical",
                })

        return warnings

    def _detect_byte_range_gaps(self, model_dir: Path, shard_byte_ranges: Dict[str, List]) -> List[Dict[str, Any]]:
        """Detect gaps in tensor data within each shard - indicates missing data."""
        warnings = []

        for shard_name, ranges in shard_byte_ranges.items():
            if len(ranges) <= 1:
                continue

            # Sort ranges by start position
            sorted_ranges = sorted(ranges, key=lambda x: x[0])

            # Check for gaps between adjacent ranges
            gaps = []
            for i in range(len(sorted_ranges) - 1):
                current_start, current_end, current_tensor = sorted_ranges[i]
                next_start, next_end, next_tensor = sorted_ranges[i + 1]

                # Check if there's a gap between current and next range
                if current_end < next_start:
                    gap_size = next_start - current_end
                    # Only flag significant gaps (>1KB) to avoid false positives from padding
                    if gap_size > 1024:
                        gaps.append({
                            "after_tensor": current_tensor,
                            "before_tensor": next_tensor,
                            "gap_start": current_end,
                            "gap_end": next_start,
                            "gap_size": gap_size,
                        })

            if gaps:
                total_gap_size = sum(gap["gap_size"] for gap in gaps)

                # Get actual file size for context
                shard_path = model_dir / shard_name
                try:
                    actual_file_size = shard_path.stat().st_size
                    gap_percentage = (total_gap_size / actual_file_size) * 100
                except (OSError, ZeroDivisionError):
                    gap_percentage = 0

                # Flag significant gaps as potential security issues
                severity = "high" if gap_percentage > 5 else "medium"

                warnings.append({
                    "type": "byte_range_gaps",
                    "details": {
                        "message": f"Byte-range gaps detected in shard {shard_name}",
                        "shard": shard_name,
                        "gaps": gaps[:3],  # Show first 3 gaps
                        "total_gaps": len(gaps),
                        "total_gap_size": total_gap_size,
                        "gap_percentage": round(gap_percentage, 2),
                        "risk_level": "MEDIUM" if severity == "medium" else "HIGH",
                        "recommendation": "Verify gaps are intentional padding, not missing data",
                    },
                    "severity": severity,
                })

        return warnings

    def _validate_tensor_size_consistency(self, model_dir: Path, index_data: Dict[str, Any],
                                        shard_byte_ranges: Dict[str, List]) -> List[Dict[str, Any]]:
        """Validate that tensor sizes match their declared shapes and dtypes."""
        warnings = []

        try:
            for shard_name, ranges in shard_byte_ranges.items():
                shard_path = model_dir / shard_name
                if not shard_path.exists():
                    continue

                # Parse shard header to get tensor metadata
                with open(shard_path, "rb") as f:
                    shard_data = f.read()

                if len(shard_data) < 8:
                    continue

                header_size = struct.unpack("<Q", shard_data[:8])[0]
                header_data = shard_data[8:8+header_size]
                header_json = json.loads(header_data.decode("utf-8"))

                size_mismatches = []

                for start_offset, end_offset, tensor_name in ranges:
                    if tensor_name not in header_json:
                        continue

                    tensor_info = header_json[tensor_name]
                    if not isinstance(tensor_info, dict):
                        continue

                    # Calculate expected size from shape and dtype
                    if "shape" in tensor_info and "dtype" in tensor_info:
                        shape = tensor_info["shape"]
                        dtype = tensor_info["dtype"]

                        if dtype in self.dtype_mappings:
                            bytes_per_element = self.dtype_mappings[dtype]["bytes"]
                            expected_size = 1
                            for dim in shape:
                                expected_size *= dim
                            expected_size *= bytes_per_element

                            actual_size = end_offset - start_offset

                            # Allow small differences for alignment/padding
                            if abs(expected_size - actual_size) > 16:
                                size_mismatches.append({
                                    "tensor": tensor_name,
                                    "expected_size": expected_size,
                                    "actual_size": actual_size,
                                    "difference": actual_size - expected_size,
                                    "shape": shape,
                                    "dtype": dtype,
                                })

                if size_mismatches:
                    # Classify severity based on the nature of mismatches
                    critical_mismatches = [m for m in size_mismatches if abs(m["difference"]) > 1024]
                    severity = "critical" if critical_mismatches else "high"

                    warnings.append({
                        "type": "tensor_size_mismatches",
                        "details": {
                            "message": f"Tensor size mismatches detected in shard {shard_name}",
                            "shard": shard_name,
                            "mismatches": size_mismatches[:5],  # Show first 5
                            "total_mismatches": len(size_mismatches),
                            "critical_mismatches": len(critical_mismatches),
                            "risk_level": "CRITICAL" if severity == "critical" else "HIGH",
                            "recommendation": "Size mismatches indicate data corruption or tampering",
                        },
                        "severity": severity,
                    })

        except Exception as e:
            logger.debug(f"Error validating tensor size consistency: {str(e)}")

        return warnings

    def _validate_cross_shard_byte_ranges(self, global_tensor_ranges: List,
                                        index_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate byte ranges don't conflict across different shards."""
        warnings = []

        try:
            # Group ranges by tensor name to check for cross-shard conflicts
            tensor_locations = {}  # tensor_name -> [(shard, start, end), ...]

            for start, end, tensor_name, shard_name in global_tensor_ranges:
                if tensor_name not in tensor_locations:
                    tensor_locations[tensor_name] = []
                tensor_locations[tensor_name].append((shard_name, start, end))

            # Check for tensors appearing in multiple shards (should not happen)
            multi_shard_tensors = []
            for tensor_name, locations in tensor_locations.items():
                if len(locations) > 1:
                    multi_shard_tensors.append({
                        "tensor": tensor_name,
                        "locations": locations,
                        "shard_count": len(locations),
                    })

            if multi_shard_tensors:
                warnings.append({
                    "type": "cross_shard_tensor_duplication",
                    "details": {
                        "message": "CRITICAL: Tensors found in multiple shards",
                        "duplicate_tensors": multi_shard_tensors[:5],  # Show first 5
                        "total_duplicates": len(multi_shard_tensors),
                        "risk_level": "CRITICAL",
                        "attack_vector": "Tensor duplication attack - same tensor in multiple shards",
                        "recommendation": "NEVER load this model - cross-shard duplication indicates tampering",
                    },
                    "severity": "critical",
                })

            # Validate that index mapping matches actual shard locations
            mapping_mismatches = []
            for tensor_name, declared_shard in index_data["weight_map"].items():
                if tensor_name in tensor_locations:
                    actual_locations = tensor_locations[tensor_name]
                    # Check if tensor is in the declared shard
                    found_in_declared = any(shard == declared_shard for shard, _, _ in actual_locations)
                    if not found_in_declared:
                        mapping_mismatches.append({
                            "tensor": tensor_name,
                            "declared_shard": declared_shard,
                            "actual_shards": [shard for shard, _, _ in actual_locations],
                        })

            if mapping_mismatches:
                warnings.append({
                    "type": "shard_mapping_mismatches",
                    "details": {
                        "message": "Index-shard mapping mismatches detected",
                        "mismatches": mapping_mismatches[:5],  # Show first 5
                        "total_mismatches": len(mapping_mismatches),
                        "risk_level": "HIGH",
                        "recommendation": "Index file doesn't match actual tensor locations",
                    },
                    "severity": "high",
                })

        except Exception as e:
            logger.debug(f"Error validating cross-shard byte ranges: {str(e)}")

        return warnings

    def _validate_shard_coverage_integrity(self, model_dir: Path, index_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """CRITICAL SECURITY ENHANCEMENT: Validate shard coverage and bundle integrity.

        Prevents sophisticated attacks:
        - Rogue shard injection (malicious .safetensors files added to model directory)
        - Missing shard attacks (critical model components removed)
        - Bundle completeness attacks (incomplete model distributions)
        - Directory traversal attacks (files placed outside expected locations)
        - Supply chain tampering (unauthorized file additions/removals)
        """
        warnings = []

        try:
            if "weight_map" not in index_data:
                return warnings

            # Get all shards referenced in the index
            referenced_shards = set(index_data["weight_map"].values())

            # Discover all actual safetensors files in the model directory
            actual_shard_files = set()
            suspicious_files = []

            # Scan model directory for safetensors files
            for file_path in model_dir.iterdir():
                if file_path.is_file():
                    filename = file_path.name

                    # Check for safetensors files
                    if filename.endswith(".safetensors"):
                        actual_shard_files.add(filename)

                        # Flag suspicious naming patterns
                        if self._is_suspicious_shard_filename(filename):
                            suspicious_files.append({
                                "filename": filename,
                                "reason": "Suspicious naming pattern",
                                "size": file_path.stat().st_size,
                            })

                    # Flag other suspicious files that might be disguised shards
                    elif self._is_potentially_disguised_shard(file_path):
                        suspicious_files.append({
                            "filename": filename,
                            "reason": "Potentially disguised shard file",
                            "size": file_path.stat().st_size,
                        })

            # CRITICAL CHECK 1: Ensure all referenced shards exist
            missing_shards = referenced_shards - actual_shard_files
            if missing_shards:
                warnings.append({
                    "type": "missing_referenced_shards",
                    "details": {
                        "message": "CRITICAL: Shards referenced in index but missing from directory",
                        "missing_shards": sorted(missing_shards),
                        "total_missing": len(missing_shards),
                        "total_referenced": len(referenced_shards),
                        "risk_level": "CRITICAL",
                        "attack_vector": "Missing shard attack - model components removed",
                        "recommendation": "NEVER load this model - critical components missing",
                    },
                    "severity": "critical",
                })

            # CRITICAL CHECK 2: Detect rogue/unreferenced shard files
            rogue_shards = actual_shard_files - referenced_shards
            if rogue_shards:
                # Analyze rogue shards for threat assessment
                rogue_analysis = self._analyze_rogue_shards(model_dir, rogue_shards)

                severity = "critical" if any(r["is_valid_safetensors"] for r in rogue_analysis) else "high"
                risk_level = "CRITICAL" if severity == "critical" else "HIGH"

                warnings.append({
                    "type": "rogue_unreferenced_shards",
                    "details": {
                        "message": "SECURITY: Rogue safetensors files found in model directory",
                        "rogue_shards": sorted(rogue_shards),
                        "total_rogue": len(rogue_shards),
                        "rogue_analysis": rogue_analysis,
                        "risk_level": risk_level,
                        "attack_vector": "Rogue shard injection - malicious components added",
                        "recommendation": "Investigate rogue files - potential supply chain compromise",
                    },
                    "severity": severity,
                })

            # CRITICAL CHECK 3: Validate bundle completeness
            completeness_issues = self._validate_bundle_completeness(model_dir, referenced_shards, actual_shard_files)
            warnings.extend(completeness_issues)

            # CRITICAL CHECK 4: Check for suspicious files and naming patterns
            if suspicious_files:
                warnings.append({
                    "type": "suspicious_files_detected",
                    "details": {
                        "message": "Suspicious files detected in model directory",
                        "suspicious_files": suspicious_files[:10],  # Show first 10
                        "total_suspicious": len(suspicious_files),
                        "risk_level": "MEDIUM",
                        "recommendation": "Review suspicious files for potential threats",
                    },
                    "severity": "medium",
                })

            # SECURITY CHECK 5: Validate shard file integrity and consistency
            integrity_issues = self._validate_shard_file_integrity(model_dir, referenced_shards)
            warnings.extend(integrity_issues)

            # SECURITY CHECK 6: Check for directory traversal attempts
            traversal_issues = self._check_directory_traversal_attempts(model_dir, referenced_shards)
            warnings.extend(traversal_issues)

        except Exception as e:
            warnings.append({
                "type": "shard_coverage_validation_error",
                "details": {
                    "message": "Error validating shard coverage integrity",
                    "error": str(e),
                    "risk_level": "HIGH",
                    "recommendation": "Manual shard coverage verification recommended",
                },
                "severity": "high",
            })

        return warnings

    def _is_suspicious_shard_filename(self, filename: str) -> bool:
        """Check if shard filename follows suspicious patterns."""
        filename_lower = filename.lower()

        # Standard safetensors naming patterns
        standard_patterns = [
            r"model-\d{5}-of-\d{5}\.safetensors",  # model-00001-of-00021.safetensors
            r"model\.safetensors",                  # model.safetensors
            r"pytorch_model-\d{5}-of-\d{5}\.safetensors",
        ]

        # Check if filename matches standard patterns
        import re
        for pattern in standard_patterns:
            if re.match(pattern, filename):
                return False

        # Flag suspicious patterns
        suspicious_patterns = [
            "hidden", "secret", "backdoor", "payload", "malicious",
            "temp", "tmp", "backup", "old", "test", "debug",
            "..", "__", "//", "\\\\",  # Path traversal attempts
            "model.bin", "pytorch_model.bin",  # Pickle format disguised as safetensors
        ]

        return any(pattern in filename_lower for pattern in suspicious_patterns)

    def _is_potentially_disguised_shard(self, file_path: Path) -> bool:
        """Check if file might be a disguised shard file."""
        filename = file_path.name.lower()

        # Check for files with safetensors-like names but wrong extensions
        disguise_patterns = [
            filename.startswith("model") and not filename.endswith(".safetensors"),
            filename.endswith(".bin") and "model" in filename,  # Pickle disguised
            filename.endswith(".pt") and "model" in filename,   # Pickle disguised
            filename.endswith(".pth") and "model" in filename,  # Pickle disguised
        ]

        if any(disguise_patterns):
            # Check file size - if it's model-sized, it's suspicious
            try:
                size = file_path.stat().st_size
                if size > 100 * 1024 * 1024:  # >100MB
                    return True
            except (OSError, ValueError):
                pass

        return False

    def _analyze_rogue_shards(self, model_dir: Path, rogue_shards: set) -> List[Dict[str, Any]]:
        """Analyze rogue shard files for threat assessment."""
        analysis = []

        for shard_name in rogue_shards:
            shard_path = model_dir / shard_name
            shard_info = {
                "filename": shard_name,
                "size": 0,
                "is_valid_safetensors": False,
                "threat_level": "LOW",
                "analysis": "Unknown file type",
            }

            try:
                shard_info["size"] = shard_path.stat().st_size

                # Check if it's a valid safetensors file
                with open(shard_path, "rb") as f:
                    data = f.read(1024)  # Read first 1KB for analysis

                # Try to parse as safetensors
                if len(data) >= 8:
                    try:
                        header_size = struct.unpack("<Q", data[:8])[0]
                        if 8 < header_size < len(data):
                            header_data = data[8:8+header_size]
                            header_json = json.loads(header_data.decode("utf-8"))

                            if isinstance(header_json, dict):
                                shard_info["is_valid_safetensors"] = True
                                shard_info["threat_level"] = "HIGH"
                                shard_info["analysis"] = f"Valid safetensors with {len(header_json)-1} tensors"

                                # Count tensor parameters for threat assessment
                                tensor_count = len([k for k in header_json if k != "__metadata__"])
                                if tensor_count > 0:
                                    shard_info["tensor_count"] = tensor_count
                                    if tensor_count > 100:  # Many tensors = higher threat
                                        shard_info["threat_level"] = "CRITICAL"
                    except Exception as e:
                        shard_info["analysis"] = f"Invalid safetensors format: {e}"

                # Check for pickle format (major security threat)
                if data.startswith(b"\x80") or b"pickle" in data[:100]:
                    shard_info["threat_level"] = "CRITICAL"
                    shard_info["analysis"] = "DANGER: Contains pickle format - RCE risk"

                # Assess threat based on size
                if shard_info["size"] > 1024 * 1024 * 1024:  # >1GB
                    if shard_info["threat_level"] == "LOW":
                        shard_info["threat_level"] = "MEDIUM"
                    shard_info["analysis"] += " (Large file - potential model component)"

            except Exception as e:
                shard_info["analysis"] = f"Error analyzing file: {str(e)}"
                shard_info["threat_level"] = "MEDIUM"

            analysis.append(shard_info)

        return analysis

    def _validate_bundle_completeness(self, model_dir: Path, referenced_shards: set,
                                    actual_shards: set) -> List[Dict[str, Any]]:
        """Validate that model bundle is complete and consistent."""
        warnings = []

        try:
            # Check for expected companion files
            expected_files = [
                "config.json",           # Model configuration
                "tokenizer.json",        # Tokenizer configuration
                "tokenizer_config.json", # Tokenizer settings
                "generation_config.json", # Generation parameters
            ]

            missing_expected = []
            for expected_file in expected_files:
                if not (model_dir / expected_file).exists():
                    missing_expected.append(expected_file)

            # Only flag as warning if config.json is missing (critical)
            if "config.json" in missing_expected:
                warnings.append({
                    "type": "missing_critical_config",
                    "details": {
                        "message": "Critical model configuration file missing",
                        "missing_file": "config.json",
                        "risk_level": "HIGH",
                        "recommendation": "Model may not load correctly without configuration",
                    },
                    "severity": "high",
                })

            # Check shard naming consistency
            if referenced_shards:
                consistency_issues = self._check_shard_naming_consistency(referenced_shards)
                if consistency_issues:
                    warnings.append({
                        "type": "shard_naming_inconsistency",
                        "details": {
                            "message": "Shard naming pattern inconsistencies detected",
                            "issues": consistency_issues,
                            "risk_level": "MEDIUM",
                            "recommendation": "Verify shard files follow expected naming convention",
                        },
                        "severity": "medium",
                    })

            # Validate total shard count makes sense
            if len(referenced_shards) > 50:  # Unusually many shards
                warnings.append({
                    "type": "excessive_shard_count",
                    "details": {
                        "message": "Unusually high number of model shards",
                        "shard_count": len(referenced_shards),
                        "risk_level": "MEDIUM",
                        "recommendation": "Verify shard count is legitimate for model size",
                    },
                    "severity": "medium",
                })

        except Exception as e:
            logger.debug(f"Error validating bundle completeness: {str(e)}")

        return warnings

    def _check_shard_naming_consistency(self, referenced_shards: set) -> List[str]:
        """Check for consistent shard naming patterns."""
        issues = []

        # Extract shard patterns
        patterns = {}
        for shard in referenced_shards:
            if "model-" in shard and "-of-" in shard:
                # Extract pattern like "model-00001-of-00021.safetensors"
                parts = shard.split("-")
                if len(parts) >= 4:
                    try:
                        current_num = int(parts[1])
                        total_parts = parts[3].split(".")[0]  # Remove .safetensors
                        total_num = int(total_parts)

                        if total_num not in patterns:
                            patterns[total_num] = set()
                        patterns[total_num].add(current_num)
                    except ValueError:
                        issues.append(f"Invalid shard numbering in {shard}")

        # Check for missing shard numbers
        for total_num, current_nums in patterns.items():
            expected_nums = set(range(1, total_num + 1))
            missing_nums = expected_nums - current_nums
            extra_nums = current_nums - expected_nums

            if missing_nums:
                issues.append(f"Missing shard numbers: {sorted(missing_nums)}")
            if extra_nums:
                issues.append(f"Extra shard numbers: {sorted(extra_nums)}")

        return issues

    def _validate_shard_file_integrity(self, model_dir: Path, referenced_shards: set) -> List[Dict[str, Any]]:
        """Validate integrity of individual shard files."""
        warnings = []

        try:
            corrupted_shards = []

            for shard_name in referenced_shards:
                shard_path = model_dir / shard_name

                if shard_path.exists():
                    try:
                        # Quick integrity check - ensure file can be parsed
                        with open(shard_path, "rb") as f:
                            data = f.read(1024)  # Read first 1KB

                        if len(data) >= 8:
                            header_size = struct.unpack("<Q", data[:8])[0]

                            # Basic sanity checks
                            if header_size <= 0 or header_size > 100 * 1024 * 1024:  # >100MB header
                                corrupted_shards.append({
                                    "shard": shard_name,
                                    "issue": "Invalid header size",
                                    "header_size": header_size,
                                })
                        else:
                            corrupted_shards.append({
                                "shard": shard_name,
                                "issue": "File too small to be valid safetensors",
                            })

                    except Exception as e:
                        corrupted_shards.append({
                            "shard": shard_name,
                            "issue": f"Read error: {str(e)}",
                        })

            if corrupted_shards:
                warnings.append({
                    "type": "corrupted_shard_files",
                    "details": {
                        "message": "Corrupted or invalid shard files detected",
                        "corrupted_shards": corrupted_shards[:5],  # Show first 5
                        "total_corrupted": len(corrupted_shards),
                        "risk_level": "HIGH",
                        "recommendation": "Corrupted shards may indicate tampering or transmission errors",
                    },
                    "severity": "high",
                })

        except Exception as e:
            logger.debug(f"Error validating shard file integrity: {str(e)}")

        return warnings

    def _check_directory_traversal_attempts(self, model_dir: Path, referenced_shards: set) -> List[Dict[str, Any]]:
        """Check for directory traversal attempts in shard paths."""
        warnings = []

        try:
            traversal_attempts = []

            for shard_name in referenced_shards:
                # Check for path traversal patterns
                if ".." in shard_name or shard_name.startswith("/") or "\\" in shard_name:
                    traversal_attempts.append({
                        "shard": shard_name,
                        "pattern": "Path traversal characters detected",
                    })

                # Check if path would escape model directory
                try:
                    resolved_path = (model_dir / shard_name).resolve()
                    if not resolved_path.is_relative_to(model_dir.resolve()):
                        traversal_attempts.append({
                            "shard": shard_name,
                            "pattern": "Path escapes model directory",
                        })
                except Exception:
                    # Path resolution failed - suspicious
                    traversal_attempts.append({
                        "shard": shard_name,
                        "pattern": "Invalid path - resolution failed",
                    })

            if traversal_attempts:
                warnings.append({
                    "type": "directory_traversal_attempts",
                    "details": {
                        "message": "SECURITY: Directory traversal attempts detected in shard paths",
                        "traversal_attempts": traversal_attempts,
                        "total_attempts": len(traversal_attempts),
                        "risk_level": "CRITICAL",
                        "attack_vector": "Directory traversal attack - attempting to access files outside model directory",
                        "recommendation": "NEVER load this model - directory traversal attack detected",
                    },
                    "severity": "critical",
                })

        except Exception as e:
            logger.debug(f"Error checking directory traversal attempts: {str(e)}")

        return warnings

    def _validate_shape_math_integrity(self, model_dir: Path, index_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """CRITICAL SECURITY ENHANCEMENT: Validate shape math and parameter count accuracy.

        Prevents sophisticated attacks:
        - Parameter injection attacks (backdoors hidden in extra parameters)
        - Model architecture spoofing (claiming wrong architecture to hide malicious tensors)
        - Supply chain tampering (parameters added/removed during distribution)
        - Configuration drift (config.json doesn't match actual model)

        Uses 1-2% drift threshold to detect tampering while allowing legitimate variations.
        """
        warnings = []

        try:
            # Load model configuration
            config_file = model_dir / "config.json"
            if not config_file.exists():
                warnings.append({
                    "type": "missing_config_for_shape_validation",
                    "details": {
                        "message": "No config.json found for parameter count validation",
                        "recommendation": "Shape math validation requires model configuration",
                        "risk_level": "LOW",
                    },
                    "severity": "low",
                })
                return warnings

            with open(config_file) as f:
                config_data = json.load(f)

            # Calculate expected parameter count from configuration
            expected_params = self._calculate_expected_parameters(config_data)
            if expected_params is None:
                return warnings  # Skip validation if architecture not supported

            # Count actual parameters from tensor shapes
            actual_params = self._count_actual_parameters(model_dir, index_data)
            if actual_params is None:
                return warnings  # Skip if unable to count parameters

            # Calculate drift percentage
            if expected_params > 0:
                drift_percentage = abs(actual_params - expected_params) / expected_params * 100

                # Security thresholds for parameter drift detection (policy-configurable)
                critical_threshold = self.parameter_drift_tolerance * 2.5   # 2.5x tolerance for critical
                high_threshold = self.parameter_drift_tolerance * 1.0       # 1x tolerance for high
                medium_threshold = self.parameter_drift_tolerance * 0.5     # 0.5x tolerance for medium

                if drift_percentage > critical_threshold:
                    severity = "critical"
                    risk_level = "CRITICAL"
                    attack_vector = "Major parameter count deviation - likely tampering or backdoor injection"
                    recommendation = "NEVER load this model - significant parameter mismatch indicates attack"
                elif drift_percentage > high_threshold:
                    severity = "high"
                    risk_level = "HIGH"
                    attack_vector = "Significant parameter deviation - potential supply chain compromise"
                    recommendation = "Verify model authenticity - parameter count mismatch detected"
                elif drift_percentage > medium_threshold:
                    severity = "medium"
                    risk_level = "MEDIUM"
                    attack_vector = "Minor parameter deviation - configuration drift or version mismatch"
                    recommendation = "Verify model version matches configuration"
                else:
                    # Parameter count is within acceptable range
                    return warnings

                # Generate detailed parameter analysis
                param_breakdown = self._analyze_parameter_breakdown(model_dir, index_data, config_data)

                warnings.append({
                    "type": "parameter_count_drift",
                    "details": {
                        "message": f"Parameter count drift detected: {drift_percentage:.2f}%",
                        "expected_parameters": expected_params,
                        "actual_parameters": actual_params,
                        "parameter_difference": actual_params - expected_params,
                        "drift_percentage": round(drift_percentage, 2),
                        "risk_level": risk_level,
                        "attack_vector": attack_vector,
                        "recommendation": recommendation,
                        "model_architecture": config_data.get("model_type", "unknown"),
                        "parameter_breakdown": param_breakdown,
                    },
                    "severity": severity,
                })

            # Additional security checks for parameter distribution
            distribution_warnings = self._validate_parameter_distribution(model_dir, index_data, config_data)
            warnings.extend(distribution_warnings)

        except Exception as e:
            warnings.append({
                "type": "shape_math_validation_error",
                "details": {
                    "message": "Error validating shape math integrity",
                    "error": str(e),
                    "risk_level": "MEDIUM",
                    "recommendation": "Manual parameter count verification recommended",
                },
                "severity": "medium",
            })

        return warnings

    def _calculate_expected_parameters(self, config_data: Dict[str, Any]) -> Optional[int]:
        """Calculate expected parameter count from model configuration."""
        try:
            model_type = config_data.get("model_type", "").lower()

            # Transformer-based architectures (most common)
            if model_type in ["mistral", "llama", "gpt", "gpt2", "bloom", "opt", "falcon"]:
                return self._calculate_transformer_parameters(config_data)
            elif model_type in ["bert", "roberta", "distilbert"]:
                return self._calculate_bert_parameters(config_data)
            elif model_type in ["t5", "mt5", "ul2"]:
                return self._calculate_t5_parameters(config_data)
            elif model_type in ["clip"]:
                return self._calculate_clip_parameters(config_data)
            else:
                # Log unsupported architecture but don't fail
                logger.debug(f"Unsupported model architecture for parameter counting: {model_type}")
                return None

        except Exception as e:
            logger.debug(f"Error calculating expected parameters: {str(e)}")
            return None

    def _calculate_transformer_parameters(self, config: Dict[str, Any]) -> int:
        """Calculate parameters for transformer architectures (Mistral, LLaMA, GPT, etc.)."""
        hidden_size = config.get("hidden_size", 0)
        vocab_size = config.get("vocab_size", 0)
        num_layers = config.get("num_hidden_layers", 0)
        intermediate_size = config.get("intermediate_size", 0)
        num_attention_heads = config.get("num_attention_heads", 0)

        if not all([hidden_size, vocab_size, num_layers, num_attention_heads]):
            return 0

        # Default intermediate size for models that don't specify it
        if intermediate_size == 0:
            intermediate_size = hidden_size * 4

        # Calculate parameters by component
        params = 0

        # Embedding layer: vocab_size x hidden_size
        params += vocab_size * hidden_size

        # Transformer layers
        for _ in range(num_layers):
            # Self-attention: Q, K, V projections + output projection
            params += 4 * (hidden_size * hidden_size)  # QKV + O projections

            # MLP: up projection + down projection
            params += hidden_size * intermediate_size    # up projection (W1)
            params += intermediate_size * hidden_size    # down projection (W2)

            # For models with separate gate projection (like LLaMA/Mistral)
            if config.get("hidden_act") in ["silu", "swish", "gelu_new"]:
                params += hidden_size * intermediate_size  # gate projection (W3)

            # Layer normalization: 2 x hidden_size (pre-attention + pre-MLP)
            params += 2 * hidden_size

        # Final layer normalization
        params += hidden_size

        # Output/LM head (if not tied to embeddings)
        if not config.get("tie_word_embeddings", False):
            params += vocab_size * hidden_size

        return params

    def _calculate_bert_parameters(self, config: Dict[str, Any]) -> int:
        """Calculate parameters for BERT-style architectures."""
        hidden_size = config.get("hidden_size", 0)
        vocab_size = config.get("vocab_size", 0)
        num_layers = config.get("num_hidden_layers", 0)
        intermediate_size = config.get("intermediate_size", 0)
        max_position_embeddings = config.get("max_position_embeddings", 0)
        type_vocab_size = config.get("type_vocab_size", 2)

        if not all([hidden_size, vocab_size, num_layers, intermediate_size]):
            return 0

        params = 0

        # Embeddings
        params += vocab_size * hidden_size              # word embeddings
        params += max_position_embeddings * hidden_size # position embeddings
        params += type_vocab_size * hidden_size         # token type embeddings
        params += hidden_size                          # embedding layer norm

        # Transformer layers
        for _ in range(num_layers):
            # Multi-head attention
            params += 4 * (hidden_size * hidden_size)   # Q, K, V, O projections
            params += hidden_size                       # attention layer norm

            # Feed forward network
            params += hidden_size * intermediate_size   # intermediate projection
            params += intermediate_size * hidden_size   # output projection
            params += hidden_size                       # output layer norm

        # Pooler (for classification)
        params += hidden_size * hidden_size

        return params

    def _calculate_t5_parameters(self, config: Dict[str, Any]) -> int:
        """Calculate parameters for T5-style encoder-decoder architectures."""
        d_model = config.get("d_model", 0)
        vocab_size = config.get("vocab_size", 0)
        num_layers = config.get("num_layers", 0)
        d_ff = config.get("d_ff", 0)
        num_decoder_layers = config.get("num_decoder_layers", num_layers)

        if not all([d_model, vocab_size, num_layers, d_ff]):
            return 0

        params = 0

        # Shared embeddings
        params += vocab_size * d_model

        # Encoder layers
        for _ in range(num_layers):
            params += 4 * (d_model * d_model)  # Self-attention
            params += d_model * d_ff * 2       # Feed forward (up + down)
            params += 2 * d_model             # Layer norms

        # Decoder layers
        for _ in range(num_decoder_layers):
            params += 4 * (d_model * d_model)  # Self-attention
            params += 4 * (d_model * d_model)  # Cross-attention
            params += d_model * d_ff * 2       # Feed forward
            params += 3 * d_model             # Layer norms

        return params

    def _calculate_clip_parameters(self, config: Dict[str, Any]) -> int:
        """Calculate parameters for CLIP-style vision-language models."""
        # This is a simplified calculation - CLIP has complex dual-encoder architecture
        text_config = config.get("text_config", {})
        vision_config = config.get("vision_config", {})

        params = 0

        # Text encoder (transformer-based)
        if text_config:
            params += self._calculate_transformer_parameters(text_config)

        # Vision encoder (typically ResNet or Vision Transformer)
        if vision_config:
            # Simplified ViT calculation
            hidden_size = vision_config.get("hidden_size", 0)
            num_layers = vision_config.get("num_hidden_layers", 0)
            if hidden_size and num_layers:
                params += num_layers * hidden_size * hidden_size * 4  # Rough estimate

        return params

    def _count_actual_parameters(self, model_dir: Path, index_data: Dict[str, Any]) -> Optional[int]:
        """Count actual parameters from tensor shapes in safetensors files."""
        try:
            if "weight_map" not in index_data:
                return None

            total_params = 0
            processed_tensors = set()  # Avoid double counting

            # Process each shard to count parameters
            shard_files = set(index_data["weight_map"].values())

            for shard_name in shard_files:
                shard_path = model_dir / shard_name
                if not shard_path.exists():
                    continue

                try:
                    with open(shard_path, "rb") as f:
                        shard_data = f.read()

                    if len(shard_data) < 8:
                        continue

                    header_size = struct.unpack("<Q", shard_data[:8])[0]
                    header_data = shard_data[8:8+header_size]
                    header_json = json.loads(header_data.decode("utf-8"))

                    # Count parameters in each tensor
                    for tensor_name, tensor_info in header_json.items():
                        if tensor_name == "__metadata__":
                            continue

                        if tensor_name in processed_tensors:
                            continue  # Skip if already counted

                        if isinstance(tensor_info, dict) and "shape" in tensor_info:
                            shape = tensor_info["shape"]

                            # Calculate number of parameters (elements) in this tensor
                            tensor_params = 1
                            for dim in shape:
                                tensor_params *= dim

                            total_params += tensor_params
                            processed_tensors.add(tensor_name)

                except Exception as e:
                    logger.debug(f"Error counting parameters in shard {shard_name}: {str(e)}")
                    continue

            return total_params

        except Exception as e:
            logger.debug(f"Error counting actual parameters: {str(e)}")
            return None

    def _analyze_parameter_breakdown(self, model_dir: Path, index_data: Dict[str, Any],
                                   config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze parameter distribution across model components for security insights."""
        try:
            breakdown = {
                "embeddings": 0,
                "attention_layers": 0,
                "feedforward_layers": 0,
                "layer_norms": 0,
                "output_head": 0,
                "other": 0,
                "suspicious_tensors": [],
            }

            if "weight_map" not in index_data:
                return breakdown

            # Analyze each tensor by component type
            for tensor_name, shard_name in index_data["weight_map"].items():
                shard_path = model_dir / shard_name
                if not shard_path.exists():
                    continue

                try:
                    with open(shard_path, "rb") as f:
                        shard_data = f.read()

                    header_size = struct.unpack("<Q", shard_data[:8])[0]
                    header_data = shard_data[8:8+header_size]
                    header_json = json.loads(header_data.decode("utf-8"))

                    if tensor_name in header_json:
                        tensor_info = header_json[tensor_name]
                        if isinstance(tensor_info, dict) and "shape" in tensor_info:
                            shape = tensor_info["shape"]
                            tensor_params = 1
                            for dim in shape:
                                tensor_params *= dim

                            # Classify tensor by component type
                            component = self._classify_tensor_by_component(tensor_name)

                            if component in breakdown:
                                breakdown[component] += tensor_params
                            else:
                                breakdown["other"] += tensor_params

                            # Flag suspicious tensor patterns
                            if self._is_suspicious_tensor_for_architecture(tensor_name, tensor_params, config_data):
                                breakdown["suspicious_tensors"].append({
                                    "name": tensor_name,
                                    "params": tensor_params,
                                    "shape": shape,
                                    "suspicion": "Unusual size for architecture",
                                })

                except Exception as e:
                    logger.debug(f"Error analyzing tensor {tensor_name}: {str(e)}")
                    continue

            return breakdown

        except Exception as e:
            logger.debug(f"Error analyzing parameter breakdown: {str(e)}")
            return {}

    def _classify_tensor_by_component(self, tensor_name: str) -> str:
        """Classify tensor by model component for parameter analysis."""
        name_lower = tensor_name.lower()

        # Embedding layers
        if any(pattern in name_lower for pattern in ["embed", "wte", "word_embeddings", "position_embeddings"]):
            return "embeddings"

        # Attention layers
        elif any(pattern in name_lower for pattern in ["attn", "attention", "self_attn", "q_proj", "k_proj", "v_proj", "o_proj"]):
            return "attention_layers"

        # Feed forward layers
        elif any(pattern in name_lower for pattern in ["mlp", "ffn", "feed_forward", "fc", "gate_proj", "up_proj", "down_proj"]):
            return "feedforward_layers"

        # Layer normalization
        elif any(pattern in name_lower for pattern in ["norm", "ln_", "layer_norm", "layernorm"]):
            return "layer_norms"

        # Output/classification head
        elif any(pattern in name_lower for pattern in ["lm_head", "classifier", "output", "head"]):
            return "output_head"

        else:
            return "other"

    def _is_suspicious_tensor_for_architecture(self, tensor_name: str, tensor_params: int,
                                             config_data: Dict[str, Any]) -> bool:
        """Check if tensor size is suspicious for the declared architecture."""
        try:
            hidden_size = config_data.get("hidden_size", 0)
            vocab_size = config_data.get("vocab_size", 0)

            # Flag tensors that are unusually large for their component type
            component = self._classify_tensor_by_component(tensor_name)

            if component == "embeddings":
                # Embedding tensors should be roughly vocab_size x hidden_size
                expected_size = vocab_size * hidden_size
                if expected_size > 0 and tensor_params > expected_size * 2:  # >2x expected
                    return True

            elif component == "attention_layers":
                # Attention tensors should be roughly hidden_size x hidden_size
                expected_size = hidden_size * hidden_size
                if expected_size > 0 and tensor_params > expected_size * 4:  # >4x expected
                    return True

            elif component == "layer_norms":
                # Layer norm tensors should be roughly hidden_size
                if hidden_size > 0 and tensor_params > hidden_size * 2:  # >2x expected
                    return True

            # Flag extremely large tensors that might contain backdoors
            if tensor_params > 100_000_000:  # >100M parameters in single tensor
                return True

            return False

        except Exception:
            return False

    def _validate_parameter_distribution(self, model_dir: Path, index_data: Dict[str, Any],
                                       config_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate parameter distribution patterns for security anomalies."""
        warnings = []

        try:
            breakdown = self._analyze_parameter_breakdown(model_dir, index_data, config_data)

            if not breakdown:
                return warnings

            total_params = sum(v for k, v in breakdown.items() if k != "suspicious_tensors" and isinstance(v, int))

            if total_params == 0:
                return warnings

            # Check for suspicious parameter distributions
            embedding_ratio = breakdown.get("embeddings", 0) / total_params
            breakdown.get("attention_layers", 0) / total_params
            other_ratio = breakdown.get("other", 0) / total_params

            # Flag unusual distributions that might indicate tampering
            if embedding_ratio > 0.4:  # >40% in embeddings is unusual
                warnings.append({
                    "type": "unusual_embedding_ratio",
                    "details": {
                        "message": "Unusually high embedding parameter ratio",
                        "embedding_ratio": round(embedding_ratio * 100, 1),
                        "risk_level": "MEDIUM",
                        "recommendation": "Verify embedding layer size is legitimate",
                    },
                    "severity": "medium",
                })

            if other_ratio > 0.2:  # >20% in unclassified tensors
                warnings.append({
                    "type": "high_unclassified_parameter_ratio",
                    "details": {
                        "message": "High ratio of unclassified parameters",
                        "other_ratio": round(other_ratio * 100, 1),
                        "risk_level": "MEDIUM",
                        "recommendation": "Review unclassified tensors for potential backdoors",
                    },
                    "severity": "medium",
                })

            # Report suspicious tensors
            if breakdown.get("suspicious_tensors"):
                warnings.append({
                    "type": "suspicious_tensor_sizes",
                    "details": {
                        "message": "Tensors with suspicious sizes detected",
                        "suspicious_tensors": breakdown["suspicious_tensors"][:5],  # Show first 5
                        "total_suspicious": len(breakdown["suspicious_tensors"]),
                        "risk_level": "HIGH",
                        "recommendation": "Investigate oversized tensors for potential backdoors",
                    },
                    "severity": "high",
                })

        except Exception as e:
            logger.debug(f"Error validating parameter distribution: {str(e)}")

        return warnings
