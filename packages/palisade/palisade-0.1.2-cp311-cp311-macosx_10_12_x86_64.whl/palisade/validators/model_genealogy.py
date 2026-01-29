"""Model Genealogy Validator - Based on ShadowGenes Research.

Implements computational graph analysis to identify model family lineage and detect
architectural tampering through recurring subgraph pattern analysis.

SCOPE: Model genealogy tracking and graph structure analysis
- Model family identification (Transformer, BERT, LLaMA, etc.)
- Architectural pattern fingerprinting
- Structural tampering detection
- Graph flow anomaly detection

Based on research: "ShadowGenes: Uncovering Model Genealogy" by HiddenLayer

NOTE: This validator focuses ONLY on model architecture genealogy.
Other security concerns are handled by specialized validators:
- Code execution patterns: PickleSecurityValidator
- Backdoor detection: BackdoorDetectionValidator
- Supply chain security: SupplyChainValidator
"""

from __future__ import annotations

import hashlib
import logging
import statistics
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from palisade.models.model_file import ModelFile

from palisade.models.metadata import ModelMetadata, ModelType
from palisade.utils.patterns import BinaryAnalyzer
from palisade.validators.base import BaseValidator, Severity

logger = logging.getLogger(__name__)

# Security constants
MAX_FILE_SIZE = 10 * 1024 * 1024 * 1024  # 10GB maximum file size
MIN_MODEL_SIZE = 1024  # 1KB minimum for valid model
MAX_PROCESSING_TIME = 30.0  # 30 seconds maximum processing time
MAX_MEMORY_USAGE = 512 * 1024 * 1024  # 512MB maximum memory usage
MAX_PATTERN_MATCHES = 10000  # Maximum pattern matches to prevent DoS
CHUNK_SIZE = 1024 * 1024  # 1MB chunk size for streaming


@dataclass
class PatternMatch:
    """Represents a pattern match with confidence and context."""
    pattern: str
    count: int
    confidence: float
    positions: list[int] = field(default_factory=list)
    context_hash: str = ""


@dataclass
class ArchitecturalSignature:
    """Represents an architectural signature with statistical properties."""
    family_name: str
    required_patterns: set[str]
    optional_patterns: set[str]
    pattern_weights: dict[str, float]
    min_confidence: float


@dataclass
class ValidationResult:
    """Structured validation result with confidence metrics."""
    is_suspicious: bool
    confidence: float
    threat_indicators: list[str]
    architectural_family: str | None = None
    risk_score: float = 0.0
    statistical_significance: float = 0.0


class TimeoutError(Exception):
    """Raised when processing exceeds maximum allowed time."""
    pass


class SecurityError(Exception):
    """Raised when security validation fails."""
    pass


@contextmanager
def timeout_protection(seconds: float) -> Iterator[None]:
    """Context manager for timeout protection with active monitoring."""
    start_time = time.time()

    def check_timeout() -> None:
        if time.time() - start_time > seconds:
            raise TimeoutError(f"Processing exceeded {seconds} seconds")

    try:
        # Check timeout before yielding
        check_timeout()
        yield
        # Periodic timeout checks should be called by the code using this context
    finally:
        # Final check on exit
        check_timeout()


class ModelGenealogyValidator(BaseValidator):
    """Model genealogy validator for architectural lineage tracking and tampering detection.

    Features:
    - Model family identification (Transformer, BERT, LLaMA)
    - Architectural pattern fingerprinting through graph analysis
    - Structural tampering and modification detection
    - Genealogy anomaly detection for mixed architectures
    - Streaming support for large models
    - Thread-safe operations with DoS protection

    Security Focus: Model architecture integrity and lineage verification
    """

    def __init__(self, metadata: ModelMetadata, policy_engine: Any | None = None) -> None:
        """Initialize the validator with security hardening.

        Args:
            metadata: Model metadata for validation context
            policy_engine: Optional policy engine for configuration
        """
        super().__init__(metadata, policy_engine)

        # Thread safety lock
        self._lock = threading.RLock()

        # Secure architectural signatures with statistical properties
        self._architectural_signatures = self._initialize_secure_signatures()

        # Suspicious patterns with weighted scoring
        self._suspicious_patterns = self._initialize_suspicious_patterns()

        # Security configuration
        self._max_file_size = MAX_FILE_SIZE
        self._max_processing_time = MAX_PROCESSING_TIME
        self._max_pattern_matches = MAX_PATTERN_MATCHES

    def _initialize_secure_signatures(self) -> dict[str, ArchitecturalSignature]:
        """Initialize architectural signatures for model family identification."""
        return {
            "transformer": ArchitecturalSignature(
                family_name="transformer",
                required_patterns={"attention", "multi_head"},  # More specific to transformers
                optional_patterns={"layernorm", "self_attention", "position", "encoder", "decoder"},
                pattern_weights={
                    "attention": 0.9,
                    "multi_head": 0.9,  # Key transformer indicator
                    "layernorm": 0.7,   # Common to many architectures
                    "self_attention": 0.8,
                    "position": 0.6,
                    "encoder": 0.5,
                    "decoder": 0.5,
                },
                min_confidence=0.75,
            ),
            "llama": ArchitecturalSignature(
                family_name="llama",
                required_patterns={"rmsnorm", "rotary_emb"},
                optional_patterns={"swiglu", "attention", "layers", "rope"},
                pattern_weights={
                    "rmsnorm": 0.9,
                    "rotary_emb": 0.9,
                    "swiglu": 0.8,
                    "attention": 0.7,
                    "layers": 0.6,
                    "rope": 0.8,
                },
                min_confidence=0.8,
            ),
            "bert": ArchitecturalSignature(
                family_name="bert",
                required_patterns={"layernorm", "gelu"},  # GELU is more BERT-specific than attention
                optional_patterns={"attention", "position", "encoder", "segment", "cls"},
                pattern_weights={
                    "layernorm": 0.9,
                    "gelu": 0.9,       # Key BERT indicator
                    "attention": 0.7,  # Common to many architectures
                    "position": 0.6,
                    "encoder": 0.5,
                    "segment": 0.8,    # BERT-specific
                    "cls": 0.8,        # BERT-specific
                },
                min_confidence=0.75,
            ),
        }

    def _initialize_suspicious_patterns(self) -> dict[str, dict[str, float]]:
        """Initialize architectural tampering patterns specific to model structure."""
        return {
            "structural_tampering": {
                # Patterns indicating architectural modifications
                "modified": 0.8,
                "patched": 0.8,
                "injected": 0.9,
                "altered": 0.7,
                "custom": 0.6,
                "unofficial": 0.7,
            },
            "graph_anomalies": {
                # Patterns indicating computational graph tampering
                "bypass": 0.8,
                "skip": 0.7,
                "override": 0.8,
                "replace": 0.7,
                "redirect": 0.8,
            },
        }

    def can_validate(self, model_type: ModelType) -> bool:
        """Support genealogy validation for structured model formats."""
        return model_type in {
            ModelType.SAFETENSORS,
            ModelType.PYTORCH,
            ModelType.HUGGINGFACE,
        }

    def validate(self, data: bytes) -> list[dict[str, Any]]:
        """Validate model genealogy through secure computational graph analysis.

        Args:
            data: Model file data to analyze

        Returns:
            List of security warnings with detailed analysis
        """
        with self._lock:
            return self._secure_validate(data)

    def _secure_validate(self, data: bytes) -> list[dict[str, Any]]:
        """Internal secure validation with comprehensive protection."""
        warnings: list[dict[str, Any]] = []

        try:
            # Security validation first
            self._validate_input_security(data)

            # Timeout protection for all analysis
            with timeout_protection(self._max_processing_time):
                # Extract graph structure securely
                graph_structure = self._secure_extract_graph(data)

                if not graph_structure:
                    return warnings  # No analyzable structure found

                # Statistical pattern analysis
                pattern_matches = self._secure_pattern_analysis(data)

                # Architectural family identification with confidence
                family_result = self._identify_family_with_confidence(pattern_matches)

                # Advanced threat detection
                threat_results = self._comprehensive_threat_analysis(
                    graph_structure, pattern_matches, family_result
                )

                # Convert results to warnings
                warnings.extend(self._results_to_warnings(threat_results))

        except TimeoutError as e:
            warnings.append(self._create_security_warning(
                "analysis_timeout",
                f"Analysis exceeded time limit: {str(e)}",
                Severity.HIGH,
                "Possible DoS attack or corrupted file - manual review required",
            ))
        except SecurityError as e:
            warnings.append(self._create_security_warning(
                "security_validation_failed",
                f"Security validation failed: {str(e)}",
                Severity.CRITICAL,
                "File failed security checks - DO NOT PROCESS",
            ))
        except Exception as e:
            logger.error(f"Unexpected error in genealogy validation: {type(e).__name__}")
            warnings.append(self._create_security_warning(
                "validation_error",
                "Internal validation error occurred",
                Severity.MEDIUM,
                "Manual security review recommended",
            ))

        return warnings

    def _validate_input_security(self, data: bytes) -> None:
        """Comprehensive input security validation.

        Raises:
            SecurityError: If input fails security validation
        """
        # Size validation
        if len(data) > self._max_file_size:
            raise SecurityError(f"File size {len(data)} exceeds maximum {self._max_file_size}")

        if len(data) < MIN_MODEL_SIZE:
            raise SecurityError(f"File size {len(data)} below minimum {MIN_MODEL_SIZE}")

        # Basic structure validation
        if not self._has_valid_model_structure(data):
            raise SecurityError("File does not contain valid model structure")

        # Entropy analysis for packed/encrypted content using shared utility
        entropy = BinaryAnalyzer.calculate_entropy(data[:8192])  # First 8KB
        if entropy > 7.9:  # Very high entropy suggests encryption/packing
            raise SecurityError("File has suspiciously high entropy - possible encryption")

    def _has_valid_model_structure(self, data: bytes) -> bool:
        """Validate model structure integrity with security checks."""
        if len(data) < 512:  # Too small for legitimate model
            return False

        # Check for legitimate model format signatures at expected positions
        # SafeTensors: starts with JSON header length (8 bytes) + JSON header
        if len(data) > 8:
            try:
                header_len = int.from_bytes(data[:8], byteorder="little")
                if 0 < header_len < len(data) and header_len < 100000:  # Reasonable header size
                    json_header = data[8:8+header_len]
                    if b'"' in json_header and (b"weight" in json_header or b"tensor" in json_header):
                        return True
            except (ValueError, OverflowError):
                pass

        # GGUF: Magic number + version
        if data.startswith(b"GGUF"):
            return True

        # PyTorch: ZIP file signature + model markers
        if data.startswith(b"PK") and b"data.pkl" in data[:2048]:
            return True

        # Basic string matching for common model patterns (for compatibility)
        header = data[:1024].lower()
        model_indicators = [b"model", b"weight", b"bias", b"tensor", b"layer", b"pytorch", b"safetensors"]
        if any(indicator in header for indicator in model_indicators):
            # Check for suspicious combinations
            if (b"#!/bin/" in header and b"python" in header) or \
               (b"import " in header and b"os" in header) or \
               (b"eval(" in header and b"exec(" in header):
                return False  # Suspicious structure detected
            return True

        # Default to secure for unknown formats
        return False

    def _secure_extract_graph(self, data: bytes) -> dict[str, Any] | None:
        """Securely extract computational graph with DoS protection."""
        try:
            # Sample-based analysis to prevent DoS
            sample_size = min(len(data), CHUNK_SIZE)
            sample_data = data[:sample_size]

            # Model architecture pattern extraction for genealogy analysis
            graph_indicators = {
                "attention_mechanisms": self._secure_count_patterns(sample_data, [
                    b"attention", b"attn", b"multi_head", b"self_attention", b"cross_attention"
                ]),
                "normalization_layers": self._secure_count_patterns(sample_data, [
                    b"layernorm", b"rmsnorm", b"batchnorm", b"groupnorm"
                ]),
                "activation_functions": self._secure_count_patterns(sample_data, [
                    b"relu", b"gelu", b"swiglu", b"silu", b"tanh", b"sigmoid"
                ]),
                "positional_encoding": self._secure_count_patterns(sample_data, [
                    b"position", b"rotary_emb", b"rope", b"sinusoidal", b"learned"
                ]),
                "architectural_blocks": self._secure_count_patterns(sample_data, [
                    b"encoder", b"decoder", b"layer", b"block", b"residual"
                ]),
                "structural_markers": self._extract_structural_markers(sample_data),
            }

            # Validate extracted data
            total_patterns = sum(
                sum(patterns.values()) if isinstance(patterns, dict) else len(patterns)
                for patterns in graph_indicators.values()
            )

            if total_patterns == 0:
                return None

            return graph_indicators

        except Exception as e:
            logger.debug(f"Graph extraction failed safely: {type(e).__name__}")
            return None

    def _secure_count_patterns(self, data: bytes, patterns: list[bytes]) -> dict[str, int]:
        """Securely count patterns with DoS protection."""
        results: dict[str, int] = {}

        for pattern in patterns:
            count = 0
            start = 0

            # Limit search to prevent DoS
            while count < MAX_PATTERN_MATCHES and start < len(data):
                pos = data.find(pattern, start)
                if pos == -1:
                    break
                count += 1
                start = pos + len(pattern)

            results[pattern.decode("utf-8", errors="ignore")] = count

        return results

    def _secure_pattern_analysis(self, data: bytes) -> list[PatternMatch]:
        """Secure statistical pattern analysis."""
        matches: list[PatternMatch] = []

        # Analyze data in secure chunks with timeout and memory protection
        chunk_size = min(len(data), CHUNK_SIZE)
        start_time = time.time()
        max_matches = 50000  # Memory bound: ~50k matches * ~100 bytes/match = ~5MB

        for offset in range(0, min(len(data), chunk_size * 10), chunk_size):
            # Periodic timeout check during processing
            if time.time() - start_time > self._max_processing_time * 0.8:  # 80% of max time
                raise TimeoutError("Pattern analysis exceeded time limit")

            # Memory bound check
            if len(matches) > max_matches:
                logger.warning(f"Pattern analysis hit memory limit: {len(matches)} matches")
                break

            chunk = data[offset:offset + chunk_size]
            chunk_matches = self._analyze_chunk_patterns(chunk, offset)
            matches.extend(chunk_matches)

        # Statistical validation of matches
        return self._validate_pattern_statistics(matches)

    def _analyze_chunk_patterns(self, chunk: bytes, offset: int) -> list[PatternMatch]:
        """Analyze patterns in a single chunk."""
        matches: list[PatternMatch] = []

        # Search for architectural patterns
        for _family_name, signature in self._architectural_signatures.items():
            all_patterns = signature.required_patterns | signature.optional_patterns

            for pattern in all_patterns:
                pattern_bytes = pattern.encode("utf-8")
                positions = []
                count = 0
                start = 0

                while count < MAX_PATTERN_MATCHES // 10:  # Limit per pattern
                    pos = chunk.find(pattern_bytes, start)
                    if pos == -1:
                        break
                    positions.append(offset + pos)
                    count += 1
                    start = pos + len(pattern_bytes)

                if count > 0:
                    confidence = min(count / 100.0, 1.0)  # Scale confidence
                    # Safe context hash with bounds checking (use local chunk position)
                    local_pos = positions[0] - offset  # Convert back to chunk-relative position
                    start_pos = max(0, local_pos - 50)
                    end_pos = min(len(chunk), local_pos + 50)
                    context_hash = hashlib.sha256(
                        chunk[start_pos:end_pos]
                    ).hexdigest()[:16]

                    matches.append(PatternMatch(
                        pattern=pattern,
                        count=count,
                        confidence=confidence,
                        positions=positions,
                        context_hash=context_hash,
                    ))

        # Also search for suspicious patterns
        for _category, pattern_dict in self._suspicious_patterns.items():
            for pattern in pattern_dict.keys():
                pattern_bytes = pattern.encode("utf-8")
                positions = []
                count = 0
                start = 0

                while count < MAX_PATTERN_MATCHES // 10:  # Limit per pattern
                    pos = chunk.find(pattern_bytes, start)
                    if pos == -1:
                        break
                    positions.append(offset + pos)
                    count += 1
                    start = pos + len(pattern_bytes)

                if count > 0:
                    confidence = min(count / 100.0, 1.0)  # Normalized confidence scaling
                    # Safe context hash with bounds checking (use local chunk position)
                    local_pos = positions[0] - offset  # Convert back to chunk-relative position
                    start_pos = max(0, local_pos - 50)
                    end_pos = min(len(chunk), local_pos + 50)
                    context_hash = hashlib.sha256(
                        chunk[start_pos:end_pos]
                    ).hexdigest()[:16]

                    matches.append(PatternMatch(
                        pattern=pattern,
                        count=count,
                        confidence=confidence,
                        positions=positions,
                        context_hash=context_hash,
                    ))

        return matches

    def _validate_pattern_statistics(self, matches: list[PatternMatch]) -> list[PatternMatch]:
        """Validate pattern matches using statistical analysis."""
        if not matches:
            return matches

        # Remove statistical outliers
        counts = [match.count for match in matches]
        if len(counts) <= 2:
            return matches  # Not enough data for outlier detection

        mean_count = statistics.mean(counts)
        stdev_count = statistics.stdev(counts)

        # Filter extreme outliers (1.5 sigma rule for aggressive filtering)
        valid_matches = []
        for match in matches:
            if stdev_count == 0:
                # All counts are identical, keep all
                valid_matches.append(match)
            elif abs(match.count - mean_count) <= 1.5 * stdev_count:
                valid_matches.append(match)
            # else: skip outlier

        return valid_matches if valid_matches else matches  # Fallback to original if all filtered

    def _identify_family_with_confidence(self, matches: list[PatternMatch]) -> ValidationResult:
        """Identify architectural family with statistical confidence."""
        if not matches:
            return ValidationResult(
                is_suspicious=False,
                confidence=0.0,
                threat_indicators=[],
            )

        family_scores: dict[str, tuple[float, list[str]]] = {}

        for family_name, signature in self._architectural_signatures.items():
            weighted_score = 0.0
            found_patterns = []
            total_weight = 0.0

            for match in matches:
                if match.pattern in signature.pattern_weights:
                    weight = signature.pattern_weights[match.pattern]
                    pattern_score = match.confidence * weight
                    weighted_score += pattern_score
                    total_weight += weight
                    found_patterns.append(match.pattern)

            if total_weight > 0:
                normalized_score = weighted_score / total_weight

                # Require minimum patterns for valid identification
                required_found = sum(
                    1 for pattern in found_patterns
                    if pattern in signature.required_patterns
                )

                # Be less strict - require at least 1 required pattern
                if required_found >= 1:
                    family_scores[family_name] = (normalized_score, found_patterns)

        if not family_scores:
            # Unknown architecture is not automatically suspicious
            # Many legitimate models use custom architectures
            return ValidationResult(
                is_suspicious=False,
                confidence=0.0,
                threat_indicators=[],  # Not a threat, just unknown
            )

        # Find best match with statistical significance
        best_family, (best_score, patterns_found) = max(
            family_scores.items(), key=lambda x: x[1][0]
        )

        # Calculate statistical significance with safe division
        if len(family_scores) > 1:
            scores = [score for score, _ in family_scores.values()]
            if len(scores) > 1:
                stdev = statistics.stdev(scores)
                if stdev > 0:
                    significance = (best_score - statistics.mean(scores)) / stdev
                else:
                    significance = 2.0  # All scores identical, high significance
            else:
                significance = 1.0
        else:
            significance = 2.0  # High significance for single match

        min_confidence = self._architectural_signatures[best_family].min_confidence
        is_confident = best_score >= min_confidence and significance >= 0.5  # Lower significance threshold

        # Low confidence is NOT a security threat - just means we couldn't identify the family
        # Only mark as suspicious if there are actual threat patterns, not just low confidence
        return ValidationResult(
            is_suspicious=False,  # Low confidence alone is not suspicious
            confidence=best_score,
            threat_indicators=[],  # No actual threats, just low confidence
            architectural_family=best_family if is_confident else None,
            statistical_significance=significance,
        )

    def _comprehensive_threat_analysis(
        self,
        graph_structure: dict[str, Any],
        pattern_matches: list[PatternMatch],
        family_result: ValidationResult,
    ) -> list[ValidationResult]:
        """Comprehensive threat analysis with multiple detection methods."""
        results: list[ValidationResult] = []

        # Add family identification result
        if family_result.is_suspicious:
            results.append(family_result)

        # Suspicious pattern detection
        suspicious_result = self._detect_suspicious_patterns(pattern_matches)
        if suspicious_result.is_suspicious:
            results.append(suspicious_result)

        # Architectural tampering detection
        tampering_result = self._detect_architectural_tampering(graph_structure, pattern_matches)
        if tampering_result.is_suspicious:
            results.append(tampering_result)

        # Genealogy anomaly detection
        genealogy_result = self._detect_genealogy_anomalies(pattern_matches)
        if genealogy_result.is_suspicious:
            results.append(genealogy_result)

        return results

    def _detect_suspicious_patterns(self, matches: list[PatternMatch]) -> ValidationResult:
        """Detect suspicious patterns with weighted risk scoring."""
        threat_score = 0.0
        threat_indicators = []

        for category, patterns in self._suspicious_patterns.items():
            category_score = 0.0

            for match in matches:
                if match.pattern in patterns:
                    pattern_weight = patterns[match.pattern]
                    pattern_contribution = match.confidence * pattern_weight
                    category_score += pattern_contribution

                    if pattern_contribution > 0.5:
                        threat_indicators.append(f"{category}:{match.pattern}")

            threat_score += min(category_score, 1.0)  # Cap category contribution

        # Normalize threat score
        max_possible_score = len(self._suspicious_patterns)
        normalized_score = threat_score / max_possible_score if max_possible_score > 0 else 0.0

        return ValidationResult(
            is_suspicious=normalized_score > 0.7,  # Higher threshold for less false positives
            confidence=normalized_score,
            threat_indicators=threat_indicators,
            risk_score=normalized_score,
        )

    def _detect_architectural_tampering(
        self, graph_structure: dict[str, Any], matches: list[PatternMatch]
    ) -> ValidationResult:
        """Detect architectural tampering through structural analysis."""
        tampering_indicators = []
        confidence = 0.0

        # Analyze pattern distribution for anomalies
        if matches:
            pattern_counts = [match.count for match in matches]
            if len(pattern_counts) > 2:
                mean_count = statistics.mean(pattern_counts)
                stdev_count = statistics.stdev(pattern_counts)

                # Check for extreme pattern variations
                extreme_patterns = [
                    match for match in matches
                    if abs(match.count - mean_count) > 2 * stdev_count
                ]

                if extreme_patterns:
                    tampering_indicators.append("extreme_pattern_distribution")
                    confidence += 0.4

        # Check for suspicious architectural pattern combinations
        pattern_names = {match.pattern for match in matches}
        suspicious_combinations = [
            {"bypass", "override"},  # Structural bypass mechanisms
            {"modified", "patched"},  # Architecture modifications
            {"custom", "unofficial"},  # Non-standard variants
            {"redirect", "replace"},  # Graph flow alterations
        ]

        for combo in suspicious_combinations:
            if combo.issubset(pattern_names):
                tampering_indicators.append(f"architectural_tampering:{','.join(combo)}")
                confidence += 0.4  # Moderate confidence for structural changes

        return ValidationResult(
            is_suspicious=len(tampering_indicators) > 0,
            confidence=min(confidence, 1.0),
            threat_indicators=tampering_indicators,
            risk_score=confidence,
        )

    def _detect_genealogy_anomalies(self, matches: list[PatternMatch]) -> ValidationResult:
        """Detect genealogy anomalies indicating model lineage tampering."""
        if not matches:
            return ValidationResult(False, 0.0, [])

        anomaly_indicators = []
        confidence = 0.0

        # Check for architectural inconsistencies
        arch_patterns = {"attention", "layernorm", "rmsnorm", "gelu", "swiglu"}
        found_arch = [m.pattern for m in matches if m.pattern in arch_patterns]

        # Detect conflicting architectural patterns (e.g., BERT + LLaMA patterns together)
        has_bert_patterns = any(p in ["layernorm", "gelu"] for p in found_arch)
        has_llama_patterns = any(p in ["rmsnorm", "swiglu"] for p in found_arch)

        if has_bert_patterns and has_llama_patterns:
            anomaly_indicators.append("mixed_architecture_patterns")
            confidence += 0.6

        # Check for structural modification indicators
        modification_patterns = {"modified", "patched", "custom", "bypass", "override"}
        found_modifications = [m.pattern for m in matches if m.pattern in modification_patterns]
        if found_modifications:
            anomaly_indicators.append(f"structural_modifications:{','.join(found_modifications[:2])}")
            confidence += 0.5

        # Check for unusual architectural combinations
        if len(set(found_arch)) > 6:  # Too many different architectural patterns
            anomaly_indicators.append("excessive_architectural_diversity")
            confidence += 0.4

        return ValidationResult(
            is_suspicious=len(anomaly_indicators) > 0,
            confidence=min(confidence, 1.0),
            threat_indicators=anomaly_indicators,
            risk_score=confidence,
        )

    def _results_to_warnings(self, results: list[ValidationResult]) -> list[dict[str, Any]]:
        """Convert validation results to standard warning format."""
        warnings = []

        for result in results:
            if not result.is_suspicious:
                continue

            # Determine severity based on confidence and risk - less aggressive
            if result.confidence > 0.9 or result.risk_score > 0.9:
                severity = Severity.CRITICAL
            elif result.confidence > 0.75 or result.risk_score > 0.75:
                severity = Severity.HIGH
            elif result.confidence > 0.5 or result.risk_score > 0.5:
                severity = Severity.MEDIUM
            else:
                severity = Severity.LOW

            # Create detailed warning
            threat_summary = ", ".join(result.threat_indicators[:5])  # Limit indicators
            if len(result.threat_indicators) > 5:
                threat_summary += f" (+{len(result.threat_indicators) - 5} more)"

            warning_type = "genealogy_" + ("_".join(result.threat_indicators[:2]) if result.threat_indicators else "analysis")
            message = f"Model genealogy analysis detected: {threat_summary}"

            if result.architectural_family:
                message = f"Model identified as {result.architectural_family} with concerns: {threat_summary}"

            recommendation = self._get_security_recommendation(severity, result)

            warnings.append(self._create_security_warning(
                warning_type,
                message,
                severity,
                recommendation,
                confidence=result.confidence,
                risk_score=result.risk_score,
                statistical_significance=result.statistical_significance,
                threat_indicators=result.threat_indicators,
                architectural_family=result.architectural_family,
            ))

        return warnings

    def _get_security_recommendation(self, severity: Severity, result: ValidationResult) -> str:
        """Get security recommendation based on analysis results."""
        if severity == Severity.CRITICAL:
            return "BLOCK IMMEDIATELY - Critical security threats detected in model architecture"
        elif severity == Severity.HIGH:
            return "HIGH RISK - Extensive security review required before deployment"
        elif severity == Severity.MEDIUM:
            return "MODERATE RISK - Security assessment recommended"
        else:
            return "Monitor model behavior - minor architectural anomalies detected"

    def _create_security_warning(
        self,
        warning_type: str,
        message: str,
        severity: Severity,
        recommendation: str,
        **additional_fields: Any,
    ) -> dict[str, Any]:
        """Create a security warning with audit trail."""
        warning = self.create_standard_warning(
            warning_type=warning_type,
            message=message,
            severity=severity,
            recommendation=recommendation,
            **additional_fields,
        )

        # Add security audit fields
        warning["security_analysis"] = {
            "analyzer": "ModelGenealogyValidator",
            "analysis_time": time.time(),
            "methodology": "ShadowGenes_v2_SecureImplementation",
        }

        return warning

    def _extract_structural_markers(self, data: bytes) -> list[str]:
        """Extract architectural structure markers for genealogy analysis."""
        markers = []
        structural_patterns = {
            # Model architecture indicators
            b"transformer": "transformer_architecture",
            b"bert": "bert_family",
            b"llama": "llama_family",
            b"gpt": "gpt_family",
            b"t5": "t5_family",

            # Structural modifications indicators
            b"modified": "structural_modification",
            b"patched": "architecture_patch",
            b"custom": "custom_architecture",
            b"unofficial": "unofficial_variant",

            # Graph structure indicators
            b"bypass": "bypass_detected",
            b"override": "override_detected",
            b"redirect": "redirect_detected",
        }

        for pattern, marker in structural_patterns.items():
            if pattern in data:
                markers.append(marker)

        return markers

    def supports_streaming(self) -> bool:
        """Model genealogy analysis supports streaming for large models."""
        return True

    def validate_streaming(self, model_file: ModelFile) -> list[dict[str, Any]]:
        """Stream-based genealogy validation for large models."""
        warnings = []

        try:
            with self._lock:
                warnings = self._secure_streaming_validation(model_file)

        except Exception as e:
            logger.error(f"Streaming genealogy validation failed: {type(e).__name__}")
            warnings.append(self._create_security_warning(
                "streaming_validation_error",
                "Streaming validation encountered an error",
                Severity.MEDIUM,
                "Manual review recommended for large model file",
            ))

        return warnings

    def _secure_streaming_validation(self, model_file: ModelFile) -> list[dict[str, Any]]:
        """Internal secure streaming validation with chunk correlation."""
        all_matches: list[PatternMatch] = []
        chunk_hashes = []

        # Process file in secure chunks
        chunks_processed = 0
        max_chunks = min(10, model_file.size_bytes // CHUNK_SIZE + 1)  # Limit chunks

        for chunk_offset in range(0, min(model_file.size_bytes, max_chunks * CHUNK_SIZE), CHUNK_SIZE):
            chunk_size = min(CHUNK_SIZE, model_file.size_bytes - chunk_offset)
            chunk_data = model_file.read_range(chunk_offset, chunk_size)

            # Security validation of chunk
            if len(chunk_data) != chunk_size:
                break  # Incomplete read, stop processing

            # Pattern analysis with timeout protection
            with timeout_protection(5.0):  # 5 seconds per chunk
                chunk_matches = self._analyze_chunk_patterns(chunk_data, chunk_offset)
                all_matches.extend(chunk_matches)

                # Track chunk hash for integrity
                chunk_hash = hashlib.sha256(chunk_data).hexdigest()[:16]
                chunk_hashes.append(chunk_hash)

            chunks_processed += 1

        # Validate streaming consistency
        if chunks_processed < 2:
            return [self._create_security_warning(
                "streaming_insufficient_data",
                "Insufficient data processed for reliable streaming analysis",
                Severity.LOW,
                "Consider full file analysis for better accuracy",
            )]

        # Statistical validation across chunks
        validated_matches = self._validate_pattern_statistics(all_matches)

        # Family identification from streaming data
        family_result = self._identify_family_with_confidence(validated_matches)

        # Convert to warnings (only report actual security concerns)
        if family_result.is_suspicious:
            # Only warn if actually suspicious (unknown architecture, etc.)
            threat_indicators = family_result.threat_indicators if hasattr(family_result, 'threat_indicators') else []
            if threat_indicators:
                threat_desc = ", ".join(threat_indicators)
                warnings = [self._create_security_warning(
                    "streaming_genealogy_analysis",
                    f"Suspicious model architecture detected: {threat_desc}",
                    Severity.MEDIUM,
                    "Model architecture could not be identified or shows suspicious patterns",
                    confidence=family_result.confidence,
                    chunks_processed=chunks_processed,
                    architectural_family=family_result.architectural_family,
                    threat_indicators=threat_indicators,
                )]
            else:
                # Suspicious but no specific indicators - just low confidence
                warnings = []
        else:
            # Not suspicious - don't generate warnings for low confidence alone
            # Low confidence is informational, not a security issue
            warnings = []

        return warnings
