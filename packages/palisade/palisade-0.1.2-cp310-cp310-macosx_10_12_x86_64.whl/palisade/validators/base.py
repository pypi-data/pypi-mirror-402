"""Base validator class for model validation."""

import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from palisade.models.metadata import ModelMetadata, ModelType

# Import new Pydantic schemas and conversion utilities
from palisade.models.report_schema import (
    DetectionMetadata,
    FileMetadata,
    MitreAtlasMapping,
    ThreatIndicator,
    ValidationDetails,
    ValidationResult as PydanticValidationResult,
    ValidationSeverity,
    ValidationType,
    ValidationWarning as PydanticValidationWarning,
)
from palisade.models.schema_utils import (
    convert_legacy_severity,
    convert_legacy_warning,
    convert_legacy_warnings_to_result,
    infer_validation_type,
)
from palisade.models.validation_result import (
    ValidationMetrics,
    ValidationResult,
)

if TYPE_CHECKING:
    from palisade.models.model_file import ModelFile
    from palisade._native import PyCedarPolicyEngine
from palisade.models.types import ChunkInfo, StreamingContext


class Severity(Enum):
    """Warning severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Standardized threat severity mapping for supply chain security
THREAT_SEVERITY_MAPPING = {
    # Critical threats - immediate supply chain security risk
    "remote_code_execution": Severity.CRITICAL,
    "pickle_deserialization": Severity.CRITICAL,
    "code_injection": Severity.CRITICAL,
    "backdoor_injection": Severity.CRITICAL,
    "supply_chain_attack": Severity.CRITICAL,

    # High risk threats - significant security concerns
    "path_traversal": Severity.HIGH,
    "tool_hijacking": Severity.HIGH,
    "data_exfiltration": Severity.HIGH,
    "malicious_imports": Severity.HIGH,
    "behavioral_backdoor": Severity.HIGH,

    # Medium risk threats - noteworthy security issues
    "file_corruption": Severity.MEDIUM,
    "protocol_anomaly": Severity.MEDIUM,
    "analysis_evasion": Severity.MEDIUM,
    "suspicious_patterns": Severity.MEDIUM,

    # Low risk threats - informational security findings
    "analysis_failure": Severity.MEDIUM,  # Failures are medium risk as they may hide threats
    "configuration_issue": Severity.LOW,
    "format_anomaly": Severity.LOW,
}


# MITRE ATLAS (Adversarial Threat Landscape for Artificial-Intelligence Systems) mappings
# Maps common ML security issues to ATLAS technique IDs
MITRE_ATLAS_MAPPINGS = {
    # ML Model Supply Chain Attacks
    "backdoor_detected": "AML.T0051.001",  # Model Backdoor
    "trojan_detected": "AML.T0051.001",    # Model Backdoor
    "model_poisoning": "AML.T0020",        # Poison Training Data
    "data_poisoning": "AML.T0020",         # Poison Training Data

    # ML Model Access and Extraction
    "model_extraction": "AML.T0024",       # Exfiltration via ML Inference API
    "model_stealing": "AML.T0024",         # Exfiltration via ML Inference API
    "weight_extraction": "AML.T0024",      # Exfiltration via ML Inference API

    # Evasion and Adversarial Examples
    "adversarial_examples": "AML.T0043",   # Craft Adversarial Examples
    "evasion_attack": "AML.T0043",         # Craft Adversarial Examples
    "input_perturbation": "AML.T0043",     # Craft Adversarial Examples

    # Model Inference Attacks
    "membership_inference": "AML.T0033",   # Infer Training Data Membership
    "model_inversion": "AML.T0025",        # Exfiltration via Model Inversion
    "property_inference": "AML.T0033",     # Infer Training Data Membership

    # Resource Hijacking
    "resource_hijacking": "AML.T0034",     # ML Artifact Collection
    "compute_hijacking": "AML.T0034",      # ML Artifact Collection

    # Buffer Overflow and Memory Safety
    "buffer_overflow": "AML.T0051.002",   # Model Compromise via Buffer Overflow
    "memory_corruption": "AML.T0051.002", # Model Compromise via Buffer Overflow
    "dangerous_functions": "AML.T0051.002", # Model Compromise via Buffer Overflow
    "format_string_vulnerability": "AML.T0051.002", # Model Compromise via Buffer Overflow
    "integer_overflow": "AML.T0051.002",  # Model Compromise via Buffer Overflow

    # Native Code Execution
    "native_executable": "AML.T0051.003", # Model Compromise via Code Injection
    "code_injection": "AML.T0051.003",    # Model Compromise via Code Injection
    "arbitrary_code_execution": "AML.T0051.003", # Model Compromise via Code Injection

    # Unsafe Deserialization
    "unsafe_deserialization": "AML.T0019", # Unsafe Deserialization
    "pickle_vulnerability": "AML.T0019",   # Unsafe Deserialization
    "serialization_attack": "AML.T0019",   # Unsafe Deserialization

    # Data Exfiltration
    "sensitive_data_exposure": "AML.T0024", # Exfiltration via ML Inference API
    "pii_exposure": "AML.T0024",           # Exfiltration via ML Inference API
    "training_data_leakage": "AML.T0025",  # Exfiltration via Model Inversion

    # Model Tampering
    "model_tampering": "AML.T0051",        # Model Compromise
    "weight_modification": "AML.T0051",    # Model Compromise
    "architecture_tampering": "AML.T0051", # Model Compromise

    # Supply Chain Attacks
    "supply_chain_attack": "AML.T0018",    # ML Supply Chain Compromise
    "malicious_dependency": "AML.T0018",   # ML Supply Chain Compromise
    "compromised_model": "AML.T0018",      # ML Supply Chain Compromise

    # Default mapping for unknown issues
    "unknown_security_issue": "AML.T0000", # Unknown/Generic threat
}


def calculate_file_hashes(data: bytes) -> Dict[str, Any]:
    """Calculate MD5, SHA256, and TLSH hashes for the given data.

    Args:
        data: Bytes to hash

    Returns:
        Dictionary containing hash values
    """
    hashes = {
        "md5": hashlib.md5(data).hexdigest(),
        "sha256": hashlib.sha256(data).hexdigest(),
        "size_bytes": len(data)
    }

    # Try to calculate TLSH if available
    try:
        import tlsh
        if len(data) >= 50:  # TLSH requires minimum 50 bytes
            tlsh_hash = tlsh.hash(data)
            if tlsh_hash != "TNULL":  # TLSH returns TNULL for insufficient entropy
                hashes["tlsh"] = tlsh_hash
            else:
                hashes["tlsh"] = None
        else:
            hashes["tlsh"] = None
    except ImportError:
        # TLSH not available, skip
        hashes["tlsh"] = None
    except Exception as e:
        # TLSH calculation failed
        hashes["tlsh"] = f"error: {str(e)}"

    return hashes


def get_mitre_atlas_mapping(warning_type: str) -> Optional[str]:
    """Get MITRE ATLAS technique ID for a warning type.

    Args:
        warning_type: The warning type to map

    Returns:
        ATLAS technique ID or None if no mapping exists
    """
    # Try exact match first
    if warning_type in MITRE_ATLAS_MAPPINGS:
        return MITRE_ATLAS_MAPPINGS[warning_type]

    # Try partial matches for compound warning types
    for atlas_key in MITRE_ATLAS_MAPPINGS:
        if atlas_key in warning_type.lower():
            return MITRE_ATLAS_MAPPINGS[atlas_key]

    # No mapping found
    return None


class BaseValidator(ABC):
    """Base class for all validators with streaming support."""

    def __init__(self, metadata: Optional[ModelMetadata] = None, policy_engine: Optional["PyCedarPolicyEngine"] = None) -> None:
        """Initialize validator.

        Args:
        ----
            metadata: Optional model metadata to validate
            policy_engine: Optional policy engine for evaluation
        """
        self.metadata = metadata
        self.policy_engine = policy_engine
        self.warnings: List[Dict[str, Any]] = []

        # Streaming configuration
        self.max_memory_mb = 512  # Default memory limit
        self.chunk_size = 1024 * 1024  # Default 1MB chunks

    @abstractmethod
    def can_validate(self, model_type: ModelType) -> bool:
        """Check if this validator can handle the given model type."""

    @abstractmethod
    def validate(self, data: bytes) -> List[Dict[str, Any]]:
        """Validate model data and return warnings."""

    def validate_file(self, model_file: "ModelFile") -> List[Dict[str, Any]]:
        """Validate using ModelFile abstraction with streaming support.

        Args:
        ----
            model_file: ModelFile instance with streaming capabilities

        Returns:
        -------
            List of validation warnings
        """
        # Default implementation: load full file if small, otherwise stream
        if model_file.should_stream():
            return self.validate_streaming(model_file)
        else:
            # Load full file for small models
            with model_file as mf:
                data = b"".join(mf.iter_chunks())
                return self.validate(data)

    def validate_streaming(self, model_file: "ModelFile") -> List[Dict[str, Any]]:
        """Validate using streaming approach for large files.

        Default implementation processes chunks sequentially.
        Subclasses should override for format-specific streaming validation.

        Args:
        ----
            model_file: ModelFile instance

        Returns:
        -------
            List of validation warnings
        """
        warnings = []
        # Initialize streaming context with proper validator state management
        context = StreamingContext(total_size=model_file.size_bytes)
        context.validation_results = {}

        # Initialize validator-specific context if needed
        validator_name = self.__class__.__name__.lower().replace("validator", "")
        validator_context_key = f"{validator_name}_streaming_context"

        try:
            with model_file as mf:
                for chunk_index, chunk_data in enumerate(mf.iter_chunks()):
                    chunk_info = ChunkInfo(
                        data=chunk_data,
                        offset=context.bytes_processed,
                        size=len(chunk_data),
                        chunk_index=chunk_index,
                        is_final=(context.bytes_processed + len(chunk_data) >= context.total_size),
                    )

                    # Validate chunk with improved context handling
                    chunk_warnings = self.validate_chunk(chunk_info, context)
                    warnings.extend(chunk_warnings)

                    # Update context
                    context.bytes_processed += len(chunk_data)
                    context.chunks_processed += 1

                    # Store context in model_file for cross-chunk state sharing
                    if hasattr(context, "validation_results") and context.validation_results:
                        model_file.set_context(validator_context_key, context.validation_results.get(validator_context_key, {}))

        except Exception as e:
            warnings.append(self.create_standard_warning(
                "streaming_validation_error",
                f"Error during streaming validation: {str(e)}",
                Severity.MEDIUM,
                recommendation="Try reducing chunk size or use non-streaming validation",
                streaming_context={
                    "bytes_processed": context.bytes_processed if "context" in locals() else 0,
                    "chunks_processed": context.chunks_processed if "context" in locals() else 0
                }
            ))

        return warnings

    def validate_chunk(self, chunk_info: ChunkInfo, context: StreamingContext) -> List[Dict[str, Any]]:
        """Validate a single chunk of data during streaming.

        Default implementation applies standard validation to the chunk.
        Subclasses can override for chunk-specific processing.

        Args:
        ----
            chunk_info: Information about the current chunk
            context: Streaming context with progress information

        Returns:
        -------
            List of validation warnings for this chunk
        """
        try:
            # Ensure validation_results dict exists
            if not hasattr(context, "validation_results") or context.validation_results is None:
                context.validation_results = {}

            # Apply standard validation to chunk
            chunk_warnings = self.validate(chunk_info.data)

            # Update streaming progress in context
            validator_name = self.__class__.__name__.lower().replace("validator", "")
            validator_context = context.validation_results.setdefault(f"{validator_name}_streaming_context", {
                "total_chunks_processed": 0,
                "total_bytes_processed": 0,
                "warnings_generated": 0
            })

            validator_context["total_chunks_processed"] += 1
            validator_context["total_bytes_processed"] += chunk_info.size
            validator_context["warnings_generated"] += len(chunk_warnings)

            return chunk_warnings

        except Exception as e:
            return [self.create_standard_warning(
                "chunk_validation_error",
                f"Error validating chunk {chunk_info.chunk_index}: {str(e)}",
                Severity.MEDIUM,
                recommendation="Check chunk data integrity and validator compatibility",
                chunk_offset=chunk_info.offset,
                chunk_size=chunk_info.size,
                chunk_index=chunk_info.chunk_index,
                streaming_progress=context.progress_percent if context else 0.0
            )]

    def supports_streaming(self) -> bool:
        """Check if this validator supports streaming validation.

        Returns
        -------
            True if validator can process files in chunks, False otherwise
        """
        # Check if subclass has overridden streaming methods
        return (
            type(self).validate_streaming is not BaseValidator.validate_streaming or
            type(self).validate_chunk is not BaseValidator.validate_chunk
        )

    def validate_tensors(self, tensors: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate model tensors directly.

        Args:
        ----
            tensors: Dictionary of tensors to validate

        Returns:
        -------
            List of validation warnings
        """
        # Default implementation returns empty list
        # Subclasses should override this method to implement tensor validation
        return []

    def get_memory_requirements(self, model_file: "ModelFile") -> Dict[str, Any]:
        """Estimate memory requirements for validating this model.

        Args:
        ----
            model_file: ModelFile to analyze

        Returns:
        -------
            Dict with memory requirement estimates
        """
        return {
            "validator": self.__class__.__name__,
            "supports_streaming": self.supports_streaming(),
            "recommended_streaming": model_file.should_stream(),
            "estimated_memory_mb": min(model_file.size_mb, 512),  # Conservative estimate
            "file_size_mb": model_file.size_mb,
        }

    def add_warning(
        self,
        warning_type: str,
        details: Union[str, Dict[str, Any]],
        severity: Severity = Severity.MEDIUM,
        check_name: Optional[str] = None,
    ) -> None:
        """Add a warning to the validator's warning list.

        Args:
        ----
            warning_type: Type of warning
            details: Warning details (string or dictionary)
            severity: Warning severity level
            check_name: Optional name of the check that generated the warning
        """
        warning = {
            "type": f"{self.__class__.__name__.lower()}_{warning_type}",
            "details": details if isinstance(details, dict) else {"message": details},
            "severity": severity.value,
        }
        if check_name:
            warning["check"] = check_name
        self.warnings.append(warning)

    @staticmethod
    def strip_rust_prefixes(items: List[str], prefix: Optional[str] = None) -> List[str]:
        """Strip Rust validator internal prefixes from result items.
        
        Rust validators use prefixes like "dangerous:", "suspicious:", etc.
        for internal categorization. This utility strips them for clean display.
        
        Args:
        ----
            items: List of items from Rust validator (e.g., ["dangerous:exec", "suspicious:sudo"])
            prefix: Specific prefix to strip (e.g., "dangerous:"). If None, strips any known prefix.
        
        Returns:
        -------
            List of cleaned items (e.g., ["exec", "sudo"])
        
        Example:
        -------
            >>> Validator.strip_rust_prefixes(["dangerous:exec", "suspicious:sudo"])
            ["exec", "sudo"]
            >>> Validator.strip_rust_prefixes(["dangerous:exec", "dangerous:system"], "dangerous:")
            ["exec", "system"]
        """
        if prefix:
            return [item.replace(prefix, "", 1) for item in items]
        
        # Strip any known Rust validator prefix
        known_prefixes = [
            # buffer_overflow & tool_calling
            "dangerous:", "suspicious:", "rop:", "format_string:", "integer_overflow:", "schema:",
            # behavior_analysis
            "trigger:", "tool_hijack:", "exfiltration:", "system_override:", "privilege:",
            # tokenizer_hygiene
            "code_injection:", "prompt_injection:", "network_file:", "shell_command:", "hidden_token:",
            # gguf_safety
            "executable:", "malicious:",
        ]
        cleaned_items = []
        for item in items:
            cleaned = item
            for known_prefix in known_prefixes:
                if cleaned.startswith(known_prefix):
                    cleaned = cleaned[len(known_prefix):]
                    break
            cleaned_items.append(cleaned)
        return cleaned_items

    def create_standard_warning(
        self,
        warning_type: str,
        message: str,
        severity: Severity = Severity.MEDIUM,
        recommendation: Optional[str] = None,
        data: Optional[bytes] = None,
        model_file: Optional["ModelFile"] = None,
        **additional_details: Any,
    ) -> Dict[str, Any]:
        """Create a standardized warning dictionary with comprehensive metadata.
        This method provides a consistent warning format across all validators.

        Args:
        ----
            warning_type: Type of warning (e.g., 'suspicious_patterns', 'validation_error')
            message: Human-readable warning message
            severity: Warning severity level
            recommendation: Optional recommendation for fixing the issue
            data: Optional bytes data for hash calculation
            model_file: Optional ModelFile instance for metadata extraction
            **additional_details: Additional details to include in the warning

        Returns:
        -------
            Standardized warning dictionary with comprehensive metadata
        """
        # Detection metadata
        detection_time = datetime.now(timezone.utc)

        # Base warning structure
        warning = {
            "type": warning_type,
            "severity": severity.value,
            "detection_metadata": {
                "detection_date": detection_time.isoformat(),
                "detection_timestamp": int(detection_time.timestamp()),
                "validator_name": self.__class__.__name__,
                "validator_version": getattr(self, "__version__", "1.0.0"),
            },
            "details": {
                "message": message,
                **additional_details,
            },
        }

        # Add recommendation if provided
        if recommendation:
            warning["details"]["recommendation"] = recommendation

        # Add MITRE ATLAS mapping
        atlas_id = get_mitre_atlas_mapping(warning_type)
        if atlas_id:
            warning["mitre_atlas"] = {
                "technique_id": atlas_id,
                "technique_name": self._get_atlas_technique_name(atlas_id),
                "url": f"https://atlas.mitre.org/techniques/{atlas_id.replace('.', '/')}"
            }

        # Add model metadata if available
        if model_file:
            try:
                file_info = model_file.file_info
                model_metadata = model_file.get_metadata()

                # Convert metadata to dict for processing
                metadata_dict = model_metadata.to_dict() if hasattr(model_metadata, 'to_dict') else model_metadata.__dict__
                warning["model_metadata"] = {
                    "model_type": metadata_dict.get("model_type", "unknown"),
                    "model_version": metadata_dict.get("model_version", "unknown"),
                    "file_path": file_info.path,
                    "file_size_bytes": file_info.size_bytes,
                    "file_size_mb": file_info.size_mb,
                    "file_extension": file_info.extension,
                    "modified_time": getattr(file_info, "modified_time", None),
                }
            except Exception as e:
                warning["model_metadata"] = {"error": f"Failed to extract metadata: {str(e)}"}

        # Add file hashes if data is available
        if data is not None:
            try:
                file_hashes = calculate_file_hashes(data)
                warning["file_hashes"] = file_hashes
            except Exception as e:
                warning["file_hashes"] = {"error": f"Failed to calculate hashes: {str(e)}"}
        elif model_file:
            # Try to get hashes from a sample of the file
            try:
                with model_file as mf:
                    # Read first 1MB for hashing (or entire file if smaller)
                    sample_size = min(1024 * 1024, model_file.size_bytes)
                    sample_data = mf.read_range(0, sample_size)
                    file_hashes = calculate_file_hashes(sample_data)
                    file_hashes["hash_sample_size"] = len(sample_data)
                    file_hashes["is_partial_hash"] = len(sample_data) < model_file.size_bytes
                    warning["file_hashes"] = file_hashes
            except Exception as e:
                warning["file_hashes"] = {"error": f"Failed to calculate hashes: {str(e)}"}

        return warning

    def create_pydantic_warning(
        self,
        warning_type: str,
        message: str,
        severity: Union[Severity, ValidationSeverity, str] = Severity.MEDIUM,
        recommendation: Optional[str] = None,
        validation_type: Optional[ValidationType] = None,
        threat_indicators: Optional[List[ThreatIndicator]] = None,
        risk_score: Optional[float] = None,
        confidence: Optional[float] = None,
        model_file: Optional["ModelFile"] = None,
        data: Optional[bytes] = None,
        **extended_details: Any,
    ) -> PydanticValidationWarning:
        """Create a standardized Pydantic ValidationWarning with comprehensive metadata.

        This method provides the new standardized output format for validators
        while maintaining compatibility with the legacy create_standard_warning method.

        Args:
        ----
            warning_type: Type of warning (e.g., 'suspicious_patterns', 'validation_error')
            message: Human-readable warning message
            severity: Warning severity level (can be legacy Severity or new ValidationSeverity)
            recommendation: Optional recommendation for fixing the issue
            validation_type: Optional validation type (inferred if not provided)
            threat_indicators: List of specific threat indicators found
            risk_score: Risk score (0.0 to 1.0)
            confidence: Detection confidence (0.0 to 1.0)
            model_file: Optional ModelFile instance for metadata extraction
            data: Optional bytes data for hash calculation
            **extended_details: Additional validator-specific details

        Returns:
        -------
            Standardized Pydantic ValidationWarning with comprehensive metadata
        """
        # Convert severity to ValidationSeverity enum
        if isinstance(severity, Severity):
            severity = convert_legacy_severity(severity.value)
        elif isinstance(severity, str):
            severity = convert_legacy_severity(severity)
        elif not isinstance(severity, ValidationSeverity):
            severity = ValidationSeverity.MEDIUM

        # Infer validation type if not provided
        if validation_type is None:
            validation_type = infer_validation_type(warning_type)

        # Create detection metadata
        detection_metadata = DetectionMetadata(
            validator_name=self.__class__.__name__,
            validator_version=getattr(self, "__version__", "1.0.0"),
        )

        # Create file metadata if available
        file_metadata = None
        if model_file or data:
            file_metadata = FileMetadata()

            if model_file:
                try:
                    file_info = model_file.file_info
                    model_metadata = model_file.get_metadata()

                    file_metadata.file_path = str(file_info.path)
                    file_metadata.file_size = file_info.size_bytes
                    file_metadata.file_type = str(model_metadata.model_type) if model_metadata.model_type else "unknown"

                    # Try to get file hash from sample
                    with model_file as mf:
                        sample_size = min(1024 * 1024, model_file.size_bytes)
                        sample_data = mf.read_range(0, sample_size)
                        file_hashes = calculate_file_hashes(sample_data)
                        file_metadata.md5_hash = file_hashes.get("md5")
                        file_metadata.sha256_hash = file_hashes.get("sha256")
                        file_metadata.tlsh_hash = file_hashes.get("tlsh")

                except Exception:
                    # If metadata extraction fails, continue with partial info
                    pass

            elif data:
                # Calculate hashes from provided data
                file_hashes = calculate_file_hashes(data)
                file_metadata.file_size = len(data)
                file_metadata.md5_hash = file_hashes.get("md5")
                file_metadata.sha256_hash = file_hashes.get("sha256")
                file_metadata.tlsh_hash = file_hashes.get("tlsh")

        # Create MITRE ATLAS mapping
        mitre_atlas = None
        atlas_id = get_mitre_atlas_mapping(warning_type)
        if atlas_id:
            mitre_atlas = MitreAtlasMapping(
                technique_id=atlas_id,
                technique_name=self._get_atlas_technique_name(atlas_id),
                url=f"https://atlas.mitre.org/techniques/{atlas_id.replace('.', '/')}",
            )

        # Create validation details
        validation_details = ValidationDetails(
            message=message,
            recommendation=recommendation,
            threat_indicators=threat_indicators or [],
            risk_score=risk_score,
            confidence=confidence,
            extended_details=extended_details,
        )

        # Create and return the Pydantic warning
        return PydanticValidationWarning(
            warning_type=warning_type,
            validation_type=validation_type,
            severity=severity,
            detection_metadata=detection_metadata,
            file_metadata=file_metadata,
            details=validation_details,
            mitre_atlas=mitre_atlas,
        )

    def validate_with_pydantic_result(
        self,
        data: bytes,
        model_path: str = "",
        context: Optional[Dict[str, Any]] = None
    ) -> PydanticValidationResult:
        """Validate data and return new Pydantic ValidationResult format.

        This method provides validators with access to the new standardized
        output format while maintaining backward compatibility.

        Args:
        ----
            data: Raw model data to validate
            model_path: Path to the model being validated
            context: Additional context for validation

        Returns:
        -------
            Standardized Pydantic ValidationResult
        """
        # Run standard validation
        legacy_warnings = self.validate(data)

        # Convert to Pydantic format
        return convert_legacy_warnings_to_result(
            legacy_warnings,
            validators_used=[self.__class__.__name__],
            policy_configuration=context,
        )

    def validate_file_with_pydantic_result(
        self,
        model_file: "ModelFile",
        context: Optional[Dict[str, Any]] = None
    ) -> PydanticValidationResult:
        """Validate ModelFile and return new Pydantic ValidationResult format.

        Args:
        ----
            model_file: ModelFile instance to validate
            context: Additional context for validation

        Returns:
        -------
            Standardized Pydantic ValidationResult
        """
        # Add file information to context
        file_context = {
            "file_size_mb": model_file.size_mb,
            "file_format": str(model_file.format) if model_file.format else "unknown",
            "streaming_used": model_file.should_stream(),
            **(context or {}),
        }

        # Run validation
        legacy_warnings = self.validate_file(model_file)

        # Convert to Pydantic format
        return convert_legacy_warnings_to_result(
            legacy_warnings,
            validators_used=[self.__class__.__name__],
            policy_configuration=file_context,
        )

    def convert_dict_warning_to_pydantic(self, warning_dict: Dict[str, Any]) -> PydanticValidationWarning:
        """Convert a single dictionary warning to Pydantic format.

        This is a helper method for validators that are migrating from hardcoded
        dictionary warnings to the new Pydantic format.

        Args:
        ----
            warning_dict: Legacy warning dictionary

        Returns:
        -------
            Pydantic ValidationWarning
        """
        return convert_legacy_warning(warning_dict)

    def _get_atlas_technique_name(self, atlas_id: str) -> str:
        """Get human-readable name for ATLAS technique ID."""
        # Mapping of ATLAS IDs to technique names
        technique_names = {
            "AML.T0051.001": "Model Backdoor",
            "AML.T0051.002": "Model Compromise via Buffer Overflow",
            "AML.T0051.003": "Model Compromise via Code Injection",
            "AML.T0051": "Model Compromise",
            "AML.T0020": "Poison Training Data",
            "AML.T0024": "Exfiltration via ML Inference API",
            "AML.T0025": "Exfiltration via Model Inversion",
            "AML.T0043": "Craft Adversarial Examples",
            "AML.T0033": "Infer Training Data Membership",
            "AML.T0034": "ML Artifact Collection",
            "AML.T0019": "Unsafe Deserialization",
            "AML.T0018": "ML Supply Chain Compromise",
            "AML.T0000": "Unknown/Generic Threat",
        }

        return technique_names.get(atlas_id, f"ATLAS Technique {atlas_id}")

    def apply_policy(self, findings: List[Dict[str, Any]], model_path: str = "", context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Apply policy engine evaluation to findings if available.

        Args:
        ----
            findings: List of findings from validation
            model_path: Path to the model being validated
            context: Additional context for policy evaluation

        Returns:
        -------
            List of findings with policy actions applied
        """
        if not findings:
            return findings

        # If no policy engine, just return findings
        if not self.policy_engine:
            return findings
        
        # Detect artifact format and build comprehensive context
        artifact_format = "unknown"
        metadata_dict = {}
        provenance_dict = {}
        artifact_signed = False
        
        if self.metadata:
            # Extract model type
            if hasattr(self.metadata, "model_type"):
                artifact_format = str(self.metadata.model_type)
            
            # Convert metadata to dict
            if hasattr(self.metadata, "to_dict"):
                metadata_dict = self.metadata.to_dict()
            elif hasattr(self.metadata, "__dict__"):
                metadata_dict = self.metadata.__dict__.copy()
            
            # Extract provenance if available
            if hasattr(self.metadata, "provenance") and self.metadata.provenance:
                provenance_dict = self.metadata.provenance if isinstance(self.metadata.provenance, dict) else {}
                artifact_signed = provenance_dict.get("signed", False)
            
            # Check for signed field directly in metadata
            if hasattr(self.metadata, "signed"):
                artifact_signed = self.metadata.signed

        # Build comprehensive evaluation context
        from palisade.core.policy import evaluate_finding
        eval_context = {
            "artifact": {
                "format": artifact_format,
                "path": model_path,
                "signed": artifact_signed,
            },
            "metadata": metadata_dict,
            "validator_name": self.__class__.__name__.lower().replace("validator", ""),
            **(context or {})
        }
        
        # Add provenance if available
        if provenance_dict:
            eval_context["provenance"] = provenance_dict

        # Evaluate each finding with policy
        for finding in findings:
            try:
                effect = evaluate_finding(self.policy_engine, finding, eval_context)
                finding["policy_effect"] = effect
            except Exception as e:
                # On error, default to quarantine
                finding["policy_effect"] = "quarantine"
        
        return findings

    def validate_with_policy(self, data: bytes, model_path: str = "", context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Validate data and apply policy evaluation.

        Args:
        ----
            data: Raw model data to validate
            model_path: Path to the model being validated
            context: Additional context for policy evaluation

        Returns:
        -------
            List of policy-evaluated findings
        """
        # Run standard validation
        findings = self.validate(data)

        # Apply policy evaluation
        return self.apply_policy(findings, model_path, context)

    def validate_file_with_policy(self, model_file: "ModelFile", context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Validate ModelFile and apply policy evaluation.

        Args:
        ----
            model_file: ModelFile instance to validate
            context: Additional context for policy evaluation

        Returns:
        -------
            List of policy-evaluated findings
        """
        # Add file information to context
        file_context = {
            "file_size_mb": model_file.size_mb,
            "file_format": str(model_file.format) if model_file.format else "unknown",
            "streaming_used": model_file.should_stream(),
            **(context or {}),
        }

        # Run validation
        findings = self.validate_file(model_file)

        # Apply policy evaluation
        return self.apply_policy(findings, str(model_file.file_info.path), file_context)

    def validate_with_structured_result(self, data: bytes, model_path: str = "", context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate data and return structured result.

        Args:
        ----
            data: Raw model data to validate
            model_path: Path to the model being validated
            context: Additional context for validation

        Returns:
        -------
            Structured ValidationResult
        """
        # Create result instance
        result = ValidationResult(validator_name=self.__class__.__name__)

        # Set up metrics
        metrics = ValidationMetrics.start_timer()
        metrics.bytes_processed = len(data)

        try:
            # Run validation
            warnings = self.validate(data)

            # Convert warnings to structured format
            for warning in warnings:
                details = warning.get("details", {})
                if isinstance(details, str):
                    message = details
                    details_dict = {}
                else:
                    message = details.get("message", "No details provided")
                    details_dict = {k: v for k, v in details.items() if k != "message"}

                result.add_warning(
                    warning_type=warning.get("type", "unknown"),
                    severity=warning.get("severity", "medium"),
                    message=message,
                    details=details_dict,
                    recommendation=details.get("recommendation") if isinstance(details, dict) else None,
                    check_name=warning.get("check"),
                )

            # Set validator-specific information
            result.checks_performed = self.get_checks_performed()
            result.features_analyzed = self.get_features_analyzed()

        except Exception as e:
            result.set_error(f"Validation failed: {str(e)}", {"exception_type": type(e).__name__})

        # Finalize metrics
        metrics.stop_timer()
        result.metrics = metrics

        return result

    def validate_file_with_structured_result(self, model_file: "ModelFile", context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Validate ModelFile and return structured result.

        Args:
        ----
            model_file: ModelFile instance to validate
            context: Additional context for validation

        Returns:
        -------
            Structured ValidationResult
        """
        # Create result instance
        result = ValidationResult(validator_name=self.__class__.__name__)

        # Set up metrics
        metrics = ValidationMetrics.start_timer()
        metrics.bytes_processed = model_file.size_bytes

        # Set model information
        result.model_type_detected = str(model_file.format) if model_file.format else "unknown"
        result.model_types_supported = [mt.value for mt in ModelType if self.can_validate(mt)]

        try:
            # Run validation
            warnings = self.validate_file(model_file)

            # Convert warnings to structured format
            for warning in warnings:
                details = warning.get("details", {})
                if isinstance(details, str):
                    message = details
                    details_dict = {}
                else:
                    message = details.get("message", "No details provided")
                    details_dict = {k: v for k, v in details.items() if k != "message"}

                result.add_warning(
                    warning_type=warning.get("type", "unknown"),
                    severity=warning.get("severity", "medium"),
                    message=message,
                    details=details_dict,
                    recommendation=details.get("recommendation") if isinstance(details, dict) else None,
                    check_name=warning.get("check"),
                )

            # Set validator-specific information
            result.checks_performed = self.get_checks_performed()
            result.features_analyzed = self.get_features_analyzed()


        except Exception as e:
            result.set_error(f"Validation failed: {str(e)}", {"exception_type": type(e).__name__})

        # Finalize metrics
        metrics.stop_timer()
        result.metrics = metrics

        return result

    def get_checks_performed(self) -> List[str]:
        """Get list of checks performed by this validator.

        Subclasses should override to provide specific check names.
        """
        return ["basic_validation"]

    def get_features_analyzed(self) -> List[str]:
        """Get list of model features analyzed by this validator.

        Subclasses should override to provide specific features.
        """
        return ["model_structure"]
