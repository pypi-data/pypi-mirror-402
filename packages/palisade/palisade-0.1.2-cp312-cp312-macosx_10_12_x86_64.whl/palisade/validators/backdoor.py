"""Production-grade backdoor detection validator with multi-signal analysis."""

import hashlib
import json
import logging
import re
import struct
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from palisade.core.policy import PyCedarPolicyEngine
from palisade.models.model_file import ModelFile
from palisade.models.types import ChunkInfo, StreamingContext

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None  # type: ignore

from palisade.models.metadata import ModelMetadata, ModelType

from .base import BaseValidator, Severity

logger = logging.getLogger(__name__)

class BackdoorDetectionValidator(BaseValidator):
    """PRODUCTION-GRADE BACKDOOR DETECTION.

    Multi-signal, format-aware validator that detects backdoors through:
    - Structured weight statistics and anomaly detection (weight: 0.5)
    - Baseline model comparison when available (weight: 0.3)
    - Textual resource scanning with malicious pattern detection (weight: 0.2)
    - Weighted signal scoring with configurable policy mapping

    NOTE: LSB steganography detection was removed as it generates false positives
    on legitimate neural network weights, which naturally have non-uniform bit 
    distributions due to training optimization patterns.

    SCORING SYSTEM:
    - Final score = Σ(signal_score_i x weight_i) for all signals
    - Score thresholds: <0.4=ALLOW, 0.4-0.8=QUARANTINE, ≥0.8=BLOCK
    - Requires multiple signals to trigger high-risk actions (defense against FP)
    """

    def __init__(self, metadata: ModelMetadata, policy_engine: Optional["PyCedarPolicyEngine"] = None) -> None:
        super().__init__(metadata, policy_engine)

        # Initialize pattern storage
        self.compiled_patterns = {}  # Successfully compiled patterns (re.Pattern objects)
        self.failed_patterns = {}    # Failed pattern compilation attempts

        # Known base model digests for comparison (enterprise deployment)
        self.known_base_models = {
            # Example: "sha256:abc123..." -> "/path/to/base/model"
            # In production, this would be populated from a model registry
        }

        # Load policy configuration
        self._load_policy_configuration()

        # Textual patterns with severity-based scoring (only applied to identified text files)
        self.textual_backdoor_patterns = {
            "code_injection": {
                "patterns": [
                    r"eval\s*\(", r"exec\s*\(", r"__import__\s*\(", r"compile\s*\(",
                    r"subprocess\.", r"os\.system", r"os\.popen", r"shell=True",
                    r"system\s*\(", r"popen\s*\(", r"execv", r"spawn",
                ],
                "severity": "critical",
                "base_score": 0.8,  # Very high threat
                "description": "Code execution patterns detected",
            },
            "data_exfiltration": {
                "patterns": [
                    r"urllib\.request", r"requests\.", r"http[s]?://", r"socket\.",
                    r"base64\.b64encode", r"pickle\.dumps", r"\.send\(", r"\.post\(",
                    r"curl\s", r"wget\s", r"fetch\(", r"XMLHttpRequest",
                ],
                "severity": "high",
                "base_score": 0.6,
                "description": "Data exfiltration patterns detected",
            },
            "model_hijacking": {
                "patterns": [
                    r"register_.*hook", r"monkey_patch", r"hijack", r"override",
                    r"intercept", r"forward_hook", r"backward_hook", r"__setattr__",
                    r"__getattribute__", r"setattr\s*\(", r"delattr\s*\(",
                ],
                "severity": "high",
                "base_score": 0.7,
                "description": "Model hijacking/hooking patterns detected",
            },
            "trigger_patterns": {
                "patterns": [
                    r"trigger", r"backdoor", r"poison", r"trojan", r"adversarial_",
                    r"attack_vector", r"exploit_", r"malicious_", r"payload",
                    r"shellcode", r"rootkit", r"virus",
                ],
                "severity": "medium",
                "base_score": 0.4,
                "description": "Suspicious trigger/attack patterns detected",
            },
            "obfuscation": {
                "patterns": [
                    r"base64\.b64decode", r"rot13", r"\.decode\(", r"chr\s*\(",
                    r"ord\s*\(", r"\\x[0-9a-f]{2}", r"\\u[0-9a-f]{4}",
                    r"obfuscat", r"deobfuscat", r"unpack",
                ],
                "severity": "medium",
                "base_score": 0.3,
                "description": "Code obfuscation patterns detected",
            },
            "privilege_escalation": {
                "patterns": [
                    r"sudo\s", r"su\s", r"root", r"administrator", r"setuid",
                    r"setgid", r"chmod\s.*777", r"chown\s.*root", r"escalate",
                ],
                "severity": "high",
                "base_score": 0.6,
                "description": "Privilege escalation patterns detected",
            },
        }

        # Pre-compile all regex patterns for performance optimization
        self._compile_patterns()

        # Statistical thresholds for weight anomalies
        self.weight_anomaly_thresholds = {
            "nan_inf_ratio": 0.001,        # > 0.1% NaN/Inf values
            "extreme_sparsity": 0.95,      # > 95% zero values
            "extreme_density": 0.05,       # < 5% zero values (unusual for sparse models)
            "outlier_ratio": 0.01,         # > 1% extreme outliers
            "weight_drift": 0.1,           # > 10% drift from base model
        }

    def _compile_patterns(self) -> None:
        """Pre-compile all regex patterns for performance optimization.

        This method compiles all regex patterns once during initialization
        to avoid repeated compilation during text scanning operations.
        """
        self.compiled_patterns = {}
        self.failed_patterns = {}  # Track failed patterns separately

        for category, config in self.textual_backdoor_patterns.items():
            compiled_patterns = []
            failed_patterns = []

            for pattern_str in config["patterns"]:
                try:
                    # Compile pattern with case-insensitive flag
                    compiled_pattern = re.compile(pattern_str, re.IGNORECASE)
                    compiled_patterns.append(compiled_pattern)
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{pattern_str}' in category '{category}': {e}")
                    # Store failed patterns separately to maintain type consistency
                    failed_patterns.append({"pattern": pattern_str, "error": str(e)})

            self.compiled_patterns[category] = compiled_patterns  # Only compiled patterns
            if failed_patterns:
                self.failed_patterns[category] = failed_patterns

        successful_patterns = sum(len(patterns) for patterns in self.compiled_patterns.values())
        failed_count = sum(len(patterns) for patterns in self.failed_patterns.values())
        total_patterns = sum(len(config["patterns"]) for config in self.textual_backdoor_patterns.values())

        logger.debug(f"Pre-compiled {successful_patterns} regex patterns ({failed_count} failed)")

        # Log compilation success rate
        if total_patterns > 0:
            success_rate = (successful_patterns / total_patterns) * 100
            logger.info(f"Pattern compilation success rate: {success_rate:.1f}% ({successful_patterns}/{total_patterns})")

            if failed_count > 0:
                logger.warning(f"Failed to compile {failed_count} regex patterns - they will be skipped during analysis")

    def get_pattern_compilation_stats(self) -> Dict[str, Any]:
        """Get statistics about pattern compilation for debugging and monitoring."""
        total_patterns = sum(len(config["patterns"]) for config in self.textual_backdoor_patterns.values())
        total_compiled = sum(len(patterns) for patterns in self.compiled_patterns.values())
        total_failed = sum(len(patterns) for patterns in self.failed_patterns.values())

        stats = {
            "total_categories": len(self.textual_backdoor_patterns),
            "total_patterns": total_patterns,
            "total_compiled": total_compiled,
            "total_failed": total_failed,
            "overall_success_rate": (total_compiled / total_patterns) if total_patterns > 0 else 0.0,
            "categories": {},
        }

        for category, config in self.textual_backdoor_patterns.items():
            compiled_patterns = self.compiled_patterns.get(category, [])
            failed_patterns = self.failed_patterns.get(category, [])
            total_category_patterns = len(config["patterns"])

            # All patterns in compiled_patterns should be re.Pattern objects now
            valid_compiled = len(compiled_patterns)  # All should be valid

            stats["categories"][category] = {
                "total_patterns": total_category_patterns,
                "valid_compiled": valid_compiled,
                "failed_patterns": len(failed_patterns),
                "compilation_success_rate": (valid_compiled / total_category_patterns) if total_category_patterns > 0 else 0.0,
                "failed_pattern_details": failed_patterns if failed_patterns else None,
            }

        return stats

    def _load_policy_configuration(self) -> None:
        """Load policy-configurable settings for backdoor detection.

        Signal Weights Documentation:
        ============================
        Signal weights determine how much each detection method contributes to the final
        backdoor detection score. All weights should sum to 1.0 for optimal calibration.

        Default Signal Weights:
        - weight_anomalies (0.5): Statistical analysis of model weights/tensors
          • Detects NaN/Inf contamination, unusual sparsity, extreme outliers
          • Highest weight because weight tampering is a common backdoor vector
          • Range: 0.0-1.0, where 1.0 = definite anomaly detected

        - baseline_drift (0.3): Comparison against known clean baseline models
          • Measures deviation from expected model behavior/structure
          • High weight as drift indicates potential tampering
          • Range: 0.0-1.0, where 1.0 = significant drift from baseline

        - textual_patterns (0.2): Malicious code patterns in embedded text/config
          • Scans for code injection, data exfiltration patterns
          • Medium weight - important for config-based attacks
          • Range: 0.0-1.0, where 1.0 = definite malicious patterns found

        NOTE: LSB steganography detection was removed (previously 0.2 weight) as it
        generated massive false positives on legitimate neural network weights.

        Final Score Calculation:
        final_score = (weight_anomalies * 0.5) + (baseline_drift * 0.3) +
                     (textual_patterns * 0.2)

        Score Thresholds:
        - >= 0.8: BLOCK (Critical risk - multiple strong signals)
        - >= 0.4: QUARANTINE (Medium risk - suspicious patterns detected)
        - <  0.4: ALLOW (Low risk - model appears clean)

        Example Scenarios:
        - High weight anomalies (0.9) alone: 0.9 * 0.5 = 0.45 → QUARANTINE
        - Moderate anomalies (0.6) + drift (0.7): 0.6*0.5 + 0.7*0.3 = 0.51 → QUARANTINE
        - Strong anomalies (0.8) + drift (0.9): 0.8*0.5 + 0.9*0.3 = 0.67 → QUARANTINE
        - All signals high (0.9, 0.9, 0.8): 0.9*0.5 + 0.9*0.3 + 0.8*0.2 = 0.88 → BLOCK
        """
        policy_config = {}
        if self.policy_engine and hasattr(self.policy_engine, "get_validator_config"):
            policy_config = self.policy_engine.get_validator_config("backdoor_detection", {})

        # Signal weighting for scoring (see documentation above)
        self.signal_weights = policy_config.get("signal_weights", {
            "weight_anomalies": 0.5,    # Highest weight - direct model tampering
            "baseline_drift": 0.3,      # High weight - model behavior changes
            "textual_patterns": 0.2,    # Medium weight - config-based attacks
        })

        # Validate weights sum to 1.0 for proper calibration
        total_weight = sum(self.signal_weights.values())
        if abs(total_weight - 1.0) > 0.01:  # Allow small floating point variance
            logger.warning(f"Signal weights sum to {total_weight:.3f}, should sum to 1.0 for optimal calibration")

        # Scoring thresholds for policy actions
        self.score_thresholds = policy_config.get("score_thresholds", {
            "block": 0.8,       # Score >= 0.8 → BLOCK (Critical: Multiple strong signals)
            "quarantine": 0.4,  # Score >= 0.4 → QUARANTINE (Medium: Suspicious patterns)
            "allow": 0.0,        # Score < 0.4 → ALLOW (Low: Appears clean)
        })

        # Enable/disable specific detection modules
        self.enable_weight_analysis = policy_config.get("enable_weight_analysis", True)
        self.enable_baseline_comparison = policy_config.get("enable_baseline_comparison", True)
        self.enable_textual_scanning = policy_config.get("enable_textual_scanning", True)

        # MEMORY PROTECTION: Limits for large model analysis
        self.max_model_size_mb = policy_config.get("max_model_size_mb", 2048)  # 2GB default
        self.max_tensors_to_analyze = policy_config.get("max_tensors_to_analyze", 100)  # Limit tensor count
        self.tensor_sample_ratio = policy_config.get("tensor_sample_ratio", 0.1)  # Analyze 10% of tensors for large models

    def can_validate(self, model_type: ModelType) -> bool:
        """This validator handles binary ML model formats."""
        supported_types = {
            ModelType.SAFETENSORS, ModelType.GGUF,
            ModelType.HUGGINGFACE, ModelType.PYTORCH,
        }
        return model_type in supported_types

    def validate(self, data: bytes) -> List[Dict[str, Any]]:
        """Multi-signal backdoor detection with weighted scoring."""
        try:
            # Initialize signal scores
            signals = {
                "weight_anomalies": 0.0,
                "baseline_drift": 0.0,
                "textual_patterns": 0.0,
                "details": {},
            }

            # 1. STRUCTURED WEIGHT ANALYSIS (safetensors only for now)
            if self.enable_weight_analysis and self.metadata and self.metadata.model_type in {ModelType.SAFETENSORS}:
                try:
                    weight_signals = self._analyze_weight_statistics(data)
                    signals["weight_anomalies"] = weight_signals["score"]
                    signals["details"]["weight_analysis"] = weight_signals["details"]
                except MemoryError as e:
                    logger.warning(f"Memory exhausted during weight analysis: {str(e)}")
                    signals["weight_anomalies"] = 0.0
                    signals["details"]["weight_analysis"] = {"error": "Memory exhausted - model too large for analysis"}
                except Exception as e:
                    logger.error(f"Unexpected error in weight analysis: {str(e)}")
                    signals["weight_anomalies"] = 0.0
                    signals["details"]["weight_analysis"] = {"error": f"Analysis failed: {str(e)}"}

            # 2. BASELINE MODEL COMPARISON
            if self.enable_baseline_comparison:
                baseline_signals = self._compare_against_baseline(data)
                signals["baseline_drift"] = baseline_signals["score"]
                signals["details"]["baseline_comparison"] = baseline_signals["details"]

            # 3. TEXTUAL RESOURCE SCANNING (MIME-aware, limited scope)
            if self.enable_textual_scanning:
                text_signals = self._scan_textual_resources(data)
                signals["textual_patterns"] = text_signals["score"]
                signals["details"]["textual_analysis"] = text_signals["details"]

            # 4. WEIGHTED SIGNAL SCORING
            final_score = self._calculate_weighted_score(signals)
            signal_breakdown = {k: v for k, v in signals.items() if k != "details" and isinstance(v, (int, float))}
            action, severity = self._map_score_to_policy(final_score, signal_breakdown)

            # Generate findings if score exceeds threshold
            if final_score > 0.1:  # Only report meaningful scores
                warning = self.create_standard_warning(
                    warning_type="backdoor_detection_signals",
                    message=f"Backdoor detection signals found (score: {final_score:.3f})",
                    severity=severity,
                    recommendation=self._get_recommendation(final_score, signals),
                    final_score=final_score,
                    policy_action=action,
                    signal_breakdown={
                        signal: score for signal, score in signals.items() if signal != "details"
                    },
                    detailed_analysis=signals.get("details", {}),
                    threat_type="backdoor_injection",
                    attack_vector="Model weights manipulation",
                    risk_level="HIGH" if final_score > 0.7 else "MEDIUM"
                )
                self.warnings.append(warning)

        except Exception as e:
            logger.error(f"Error in backdoor detection analysis: {str(e)}")
            warning = self.create_standard_warning(
                warning_type="backdoor_analysis_error",
                message=f"Error during backdoor detection: {str(e)}",
                severity=Severity.MEDIUM,
                recommendation="Manual review recommended due to analysis failure",
                error=str(e),
                threat_type="analysis_failure"
            )
            self.warnings.append(warning)

        # Apply policy evaluation if available
        context = {
            "backdoor": {
                "signals_detected": len([s for s in signals.values() if isinstance(s, float) and s > 0.1]),
                "max_signal_score": max([s for s in signals.values() if isinstance(s, float)], default=0.0),
            },
        }

        if self.policy_engine:
            return self.apply_policy(self.warnings, context.get("model_path", ""), context)

        return self.warnings

    def validate_streaming(self, model_file: "ModelFile") -> List[Dict[str, Any]]:
        """Stream-based backdoor detection for large models.

        Streaming approach:
        1. Extract headers/metadata first for format detection
        2. Apply chunk-based analysis for patterns and anomalies
        3. Accumulate statistics across chunks
        4. Final scoring based on accumulated evidence
        """
        warnings = []

        try:
            # Initialize streaming context in model_file for persistence across chunks
            streaming_context = {
                "total_chunks_analyzed": 0,
                "textual_pattern_matches": 0,
                "weight_anomaly_chunks": 0,
                "chunk_hashes": [],
                "suspicious_patterns": [],
            }

            # Store initial context in model_file
            model_file.set_context("backdoor_streaming_context", streaming_context)

            # Format-specific header analysis
            header_data = model_file.read_header(max_header_size=10 * 1024 * 1024)  # 10MB max

            # 1. Analyze headers for suspicious patterns
            header_signals = self._analyze_header_patterns(header_data, model_file.format)
            if header_signals["score"] > 0.1:
                logger.info(f"Suspicious patterns detected in model header (score: {header_signals['score']:.3f})")
                warnings.append(self.create_standard_warning(
                    "backdoor_suspicious_header_patterns",
                    f"Suspicious patterns detected in model header (score: {header_signals['score']:.3f})",
                    Severity.MEDIUM,
                    analysis_details=header_signals["details"],
                ))

            # 2. Use base class streaming for chunk-by-chunk analysis
            chunk_warnings = super().validate_streaming(model_file)
            warnings.extend(chunk_warnings)

            # 3. Final analysis based on accumulated streaming evidence
            final_context = model_file.get_context("backdoor_streaming_context", {})
            final_analysis = self._perform_final_streaming_analysis(final_context, model_file)

            if final_analysis["score"] > 0.1:
                severity = Severity.HIGH if final_analysis["score"] > 0.6 else Severity.MEDIUM
                warnings.append(self.create_standard_warning(
                    "backdoor_streaming_analysis_result",
                    f"Backdoor detection streaming analysis completed (score: {final_analysis['score']:.3f})",
                    severity,
                    final_score=final_analysis["score"],
                    analysis_summary=final_analysis["summary"],
                    recommendation=final_analysis["recommendation"],
                ))

        except Exception as e:
            logger.error(f"Error in backdoor streaming validation: {str(e)}")
            warnings.append(self.create_standard_warning(
                "backdoor_streaming_error",
                f"Error during backdoor streaming validation: {str(e)}",
                Severity.MEDIUM,
            ))

        return warnings

    def validate_chunk(self, chunk_info: "ChunkInfo", context: "StreamingContext") -> List[Dict[str, Any]]:
        """Validate chunk for backdoor indicators.

        Chunk-level analysis focuses on:
        1. Textual pattern scanning
        2. Statistical anomalies in binary data
        3. Suspicious data structures
        """
        warnings = []

        try:
            chunk_data = chunk_info.data
            
            # DEBUG: Log chunk information
            logger.debug(f"BackdoorDetectionValidator: Processing chunk {chunk_info.chunk_index} at offset {chunk_info.offset}, size {len(chunk_data)}")

            # Ensure context validation_results exists
            if not hasattr(context, "validation_results") or context.validation_results is None:
                context.validation_results = {}

            # Get or initialize backdoor-specific streaming context
            streaming_ctx = context.validation_results.setdefault("backdoor_streaming_context", {
                "total_chunks_analyzed": 0,
                "textual_pattern_matches": 0,
                "weight_anomaly_chunks": 0,
                "chunk_hashes": [],
                "suspicious_patterns": [],
            })

            # Update chunk count
            streaming_ctx["total_chunks_analyzed"] += 1

            # 1. Textual pattern analysis on chunk
            if self.enable_textual_scanning:
                text_matches = self._scan_chunk_textual_patterns(chunk_data, chunk_info.offset)
                if text_matches:
                    logger.info(f"  Found {len(text_matches)} textual pattern matches in chunk {chunk_info.chunk_index}")
                    for i, match in enumerate(text_matches[:3]):  # Log first 3 matches
                        logger.info(f"    Match {i}: {match['pattern_type']} - {match['pattern']} -> '{match['match']}'")
                    
                    streaming_ctx["textual_pattern_matches"] = streaming_ctx.get("textual_pattern_matches", 0) + len(text_matches)
                    streaming_ctx.setdefault("suspicious_patterns", []).extend(text_matches)

                    warnings.append(self.create_standard_warning(
                        "backdoor_textual_patterns_in_chunk",
                        f"Suspicious textual patterns found in chunk at offset {chunk_info.offset}",
                        Severity.MEDIUM,
                        chunk_offset=chunk_info.offset,
                        patterns_found=text_matches,
                    ))

            # 2. Basic statistical anomaly detection
            if self.enable_weight_analysis:
                anomaly_score = self._analyze_chunk_statistical_anomalies(chunk_data)
                if anomaly_score > 0.4:
                    streaming_ctx["weight_anomaly_chunks"] = streaming_ctx.get("weight_anomaly_chunks", 0) + 1
                    logger.info(f"Statistical anomalies detected in chunk at offset {chunk_info.offset} (score: {anomaly_score:.3f})")

                    warnings.append(self.create_standard_warning(
                        "backdoor_weight_anomaly_in_chunk",
                        f"Statistical anomalies detected in chunk at offset {chunk_info.offset} (score: {anomaly_score:.3f})",
                        Severity.LOW,
                        chunk_offset=chunk_info.offset,
                        anomaly_score=anomaly_score,
                    ))

            # 4. Track chunk integrity for baseline comparison
            if self.enable_baseline_comparison:
                chunk_hash = hashlib.sha256(chunk_data).hexdigest()[:16]  # Short hash for memory efficiency
                streaming_ctx.setdefault("chunk_hashes", []).append({
                    "offset": chunk_info.offset,
                    "hash": chunk_hash,
                    "size": len(chunk_data),
                })

        except Exception as e:
            logger.error(f"Error validating backdoor chunk at offset {chunk_info.offset}: {str(e)}")
            warnings.append(self.create_standard_warning(
                "backdoor_chunk_validation_error",
                f"Error validating chunk at offset {chunk_info.offset}: {str(e)}",
                Severity.LOW,
                chunk_offset=chunk_info.offset,
            ))

        return warnings

    def _analyze_header_patterns(self, header_data: bytes, format_type: str) -> Dict[str, Any]:
        """Analyze model headers for suspicious patterns."""
        details = {}
        score = 0.0

        try:
            # Look for suspicious strings in headers
            if self.enable_textual_scanning:
                text_matches = self._scan_chunk_textual_patterns(header_data, 0)
                if text_matches:
                    score += 0.3 * min(len(text_matches) / 5, 1.0)  # Scale by match count
                    details["header_text_matches"] = text_matches

            # Format-specific header analysis
            if format_type == ModelType.SAFETENSORS:
                # Basic safetensors header validation (placeholder for now)
                try:
                    if len(header_data) >= 8:
                        header_len = struct.unpack("<Q", header_data[:8])[0]
                        if header_len > 100 * 1024 * 1024:  # Suspicious large header
                            score += 0.2
                            details["safetensors_suspicious_header_size"] = header_len
                except Exception as e:
                    logger.debug(f"Error validating header: {e}")
            elif format_type == ModelType.GGUF:
                # Basic GGUF header validation (placeholder for now)
                if header_data.startswith(b"GGUF"):
                    try:
                        version = struct.unpack("<I", header_data[4:8])[0] if len(header_data) >= 8 else 0
                        if version > 10:  # Suspicious high version
                            score += 0.1
                            details["gguf_suspicious_version"] = version
                    except Exception as e:
                        logger.debug(f"Error validating GGUF header: {e}")

        except Exception as e:
            logger.debug(f"Error analyzing header patterns: {str(e)}")
            details["analysis_error"] = str(e)

        return {"score": min(score, 1.0), "details": details}

    def _scan_chunk_textual_patterns(self, data: bytes, offset: int) -> List[Dict[str, Any]]:
        """Scan chunk for suspicious textual patterns."""
        matches = []

        try:
            # Extract embedded text sections (this is the correct method name)
            embedded_text = self._extract_embedded_text_sections(data)
            if not embedded_text:
                logger.debug(f"    No embedded text found in chunk at offset {offset}")
                return matches
            
            logger.debug(f"    Extracted embedded text from chunk at offset {offset}: {embedded_text[:200]}...")

            # Use the embedded text for pattern matching
            combined_text = embedded_text
            position_map = [(0, len(embedded_text), 0)]  # Simple mapping for embedded text

            # OPTIMIZATION: Use single-pass pattern matching with compiled alternation
            for category, config in self.textual_backdoor_patterns.items():
                if category not in self.compiled_patterns:
                    continue

                category_patterns = self.compiled_patterns[category]
                original_patterns = config["patterns"]

                # Single pass through combined text for all patterns in category
                for pattern_idx, compiled_pattern in enumerate(category_patterns):
                    if pattern_idx >= len(original_patterns):
                        continue

                    original_pattern = original_patterns[pattern_idx]

                    # Single finditer call instead of nested loops
                    for match in compiled_pattern.finditer(combined_text):
                        # Map back to original position
                        match_pos = match.start()
                        original_offset = self._map_combined_position(match_pos, position_map)

                        matches.append({
                            "pattern_type": category,
                            "pattern": original_pattern,
                            "match": match.group(),
                            "offset": offset + original_offset,
                            "context": combined_text[max(0, match.start()-50):match.end()+50],
                        })

                        # Limit matches per pattern to prevent DoS
                        if len([m for m in matches if m["pattern"] == original_pattern]) >= 100:
                            break

        except Exception as e:
            logger.debug(f"Error scanning chunk textual patterns: {str(e)}")

        return matches

    def _map_combined_position(self, combined_pos: int, position_map: List[tuple]) -> int:
        """Map position in combined text back to original offset.

        Args:
            combined_pos: Position in combined text
            position_map: List of (start, end, original_offset) tuples

        Returns:
            Original offset position
        """
        for start, end, original_offset in position_map:
            if start <= combined_pos <= end:
                return original_offset + (combined_pos - start)
        return 0  # Fallback

    def _analyze_chunk_statistical_anomalies(self, data: bytes) -> float:
        """Simple statistical anomaly detection on chunk."""
        try:
            if len(data) < 256:
                return 0.0

            if not HAS_NUMPY:
                # Fallback without numpy - simple byte-level checks
                return self._basic_statistical_check(data)

            # Convert to numpy array for analysis (sample for memory efficiency)
            sample_size = min(1024, len(data))
            sample = np.frombuffer(data[:sample_size], dtype=np.uint8)

            # Calculate basic statistics
            mean = np.mean(sample)
            std = np.std(sample)

            # Look for suspicious patterns
            score = 0.0

            # Check for excessive uniformity
            unique_values = len(np.unique(sample))
            if unique_values < 10:  # Too few unique values
                score += 0.3

            # Check for suspicious mean (should be ~127.5 for random data)
            mean_deviation = abs(mean - 127.5) / 127.5
            if mean_deviation > 0.3:
                score += 0.2

            # Check for suspicious standard deviation
            if std < 10 or std > 100:  # Outside normal range
                score += 0.2

            return min(score, 1.0)

        except Exception:
            return 0.0

    def _basic_statistical_check(self, data: bytes) -> float:
        """Basic statistical check without numpy."""
        try:
            sample_size = min(1024, len(data))
            sample = data[:sample_size]

            # Basic statistics without numpy
            total = sum(sample)
            mean = total / len(sample)

            # Count unique values
            unique_values = len(set(sample))

            score = 0.0

            # Check for excessive uniformity
            if unique_values < 10:  # Too few unique values
                score += 0.3

            # Check for suspicious mean (should be ~127.5 for random data)
            mean_deviation = abs(mean - 127.5) / 127.5
            if mean_deviation > 0.3:
                score += 0.2

            # Simple variance check (without proper std calculation)
            variance_sum = sum((b - mean) ** 2 for b in sample)
            variance = variance_sum / len(sample)
            if variance < 100 or variance > 10000:  # Rough variance bounds
                score += 0.2

            return min(score, 1.0)

        except Exception:
            return 0.0

    def _perform_final_streaming_analysis(self, context: Dict[str, Any], model_file: "ModelFile") -> Dict[str, Any]:
        """Perform final analysis based on accumulated streaming evidence."""
        try:
            total_chunks = context.get("total_chunks_analyzed", 0)
            if total_chunks == 0:
                return {"score": 0.0, "summary": "No chunks analyzed", "recommendation": "Allow"}

            # Calculate weighted score based on accumulated evidence
            text_ratio = context.get("textual_pattern_matches", 0) / max(total_chunks, 1)
            anomaly_ratio = context.get("weight_anomaly_chunks", 0) / max(total_chunks, 1)

            # Weighted final score using configurable weights (normalized for streaming mode)
            # In streaming mode, only textual_patterns and weight_anomalies are available
            text_weight = self.signal_weights.get("textual_patterns", 0.2)
            anomaly_weight = self.signal_weights.get("weight_anomalies", 0.5)
            
            # Normalize weights for signals available in streaming mode
            total_weight = text_weight + anomaly_weight
            if total_weight > 0:
                text_weight /= total_weight
                anomaly_weight /= total_weight
            else:
                # Fallback to equal weights if configuration is invalid
                text_weight = 0.5
                anomaly_weight = 0.5
            
            final_score = (
                text_ratio * text_weight +
                anomaly_ratio * anomaly_weight
            )

            # Generate summary and recommendation
            summary = {
                "total_chunks_analyzed": total_chunks,
                "textual_pattern_ratio": text_ratio,
                "anomaly_ratio": anomaly_ratio,
                "file_size_mb": model_file.size_mb,
            }

            if final_score < 0.3:
                recommendation = "Allow - Low risk detected"
            elif final_score < 0.6:
                recommendation = "Quarantine - Medium risk, manual review recommended"
            else:
                recommendation = "Block - High risk, multiple backdoor indicators"

            return {
                "score": final_score,
                "summary": summary,
                "recommendation": recommendation,
            }

        except Exception as e:
            logger.error(f"Error in final streaming analysis: {str(e)}")
            return {
                "score": 0.0,
                "summary": {"error": str(e)},
                "recommendation": "Manual review required due to analysis error",
            }

    def _analyze_weight_statistics(self, data: bytes) -> Dict[str, Any]:
        """Analyze weight tensors for statistical anomalies with memory protection."""
        details = {}
        anomaly_score = 0.0

        try:
            # MEMORY PROTECTION: Check model size before processing
            model_size_mb = len(data) / (1024 * 1024)
            if model_size_mb > self.max_model_size_mb:
                logger.warning(f"Model size ({model_size_mb:.1f}MB) exceeds limit ({self.max_model_size_mb}MB), using sample analysis")
                return self._analyze_weight_statistics_sampled(data, model_size_mb)

            # Parse safetensors format
            if self.metadata and self.metadata.model_type == ModelType.SAFETENSORS:
                tensors = self._parse_safetensors_weights(data)
            else:
                model_type_str = str(self.metadata.model_type) if self.metadata and self.metadata.model_type else "unknown"
                return {"score": 0.0, "details": {"message": f"Weight analysis not supported for {model_type_str} format"}}

            if not tensors:
                return {"score": 0.0, "details": {"message": "No weight tensors found"}}

            # Analyze each tensor
            tensor_anomalies = []
            for tensor_name, tensor_data in tensors.items():
                tensor_analysis = self._analyze_single_tensor(tensor_name, tensor_data)
                if tensor_analysis["anomaly_score"] > 0.1:
                    tensor_anomalies.append(tensor_analysis)
                    anomaly_score += tensor_analysis["anomaly_score"]

            # Normalize score by number of tensors
            if tensor_anomalies:
                anomaly_score = min(anomaly_score / len(tensors), 1.0)
                details["anomalous_tensors"] = tensor_anomalies[:10]  # Top 10
                details["total_anomalous_tensors"] = len(tensor_anomalies)
                details["total_tensors_analyzed"] = len(tensors)

        except Exception as e:
            logger.debug(f"Weight analysis error: {e}")
            details["error"] = str(e)

        return {"score": anomaly_score, "details": details}

    def _analyze_single_tensor(self, name: str, tensor: Any) -> Dict[str, Any]:
        """Analyze individual tensor for anomalies."""
        if not HAS_NUMPY:
            return {
                "tensor_name": name,
                "shape": "unknown",
                "dtype": "unknown",
                "anomaly_score": 0.0,
                "anomalies": ["Numpy not available - tensor analysis disabled"],
            }

        analysis = {
            "tensor_name": name,
            "shape": tensor.shape,
            "dtype": str(tensor.dtype),
            "anomaly_score": 0.0,
            "anomalies": [],
        }

        try:
            # Flatten for analysis
            flat_tensor = tensor.flatten()

            # 1. NaN/Inf detection
            nan_count = np.sum(np.isnan(flat_tensor))
            inf_count = np.sum(np.isinf(flat_tensor))
            nan_inf_ratio = (nan_count + inf_count) / len(flat_tensor)

            if nan_inf_ratio > self.weight_anomaly_thresholds["nan_inf_ratio"]:
                analysis["anomalies"].append({
                    "type": "nan_inf_contamination",
                    "severity": "high",
                    "ratio": float(nan_inf_ratio),
                    "nan_count": int(nan_count),
                    "inf_count": int(inf_count),
                })
                analysis["anomaly_score"] += 0.4

            # 2. Sparsity analysis (only for weight tensors)
            if "weight" in name.lower() or "linear" in name.lower():
                zero_count = np.sum(flat_tensor == 0)
                sparsity = zero_count / len(flat_tensor)

                if sparsity > self.weight_anomaly_thresholds["extreme_sparsity"]:
                    analysis["anomalies"].append({
                        "type": "extreme_sparsity",
                        "severity": "medium",
                        "sparsity_ratio": float(sparsity),
                    })
                    analysis["anomaly_score"] += 0.2
                elif sparsity < self.weight_anomaly_thresholds["extreme_density"]:
                    analysis["anomalies"].append({
                        "type": "extreme_density",
                        "severity": "low",
                        "sparsity_ratio": float(sparsity),
                    })
                    analysis["anomaly_score"] += 0.1

            # 3. Outlier detection
            if len(flat_tensor) > 100:  # Only for substantial tensors
                finite_values = flat_tensor[np.isfinite(flat_tensor)]
                if len(finite_values) > 0:
                    q1, q3 = np.percentile(finite_values, [25, 75])
                    iqr = q3 - q1
                    if iqr > 0:
                        outlier_bounds = (q1 - 3 * iqr, q3 + 3 * iqr)
                        outliers = np.sum((finite_values < outlier_bounds[0]) |
                                        (finite_values > outlier_bounds[1]))
                        outlier_ratio = outliers / len(finite_values)

                        if outlier_ratio > self.weight_anomaly_thresholds["outlier_ratio"]:
                            analysis["anomalies"].append({
                                "type": "extreme_outliers",
                                "severity": "medium",
                                "outlier_ratio": float(outlier_ratio),
                                "outlier_bounds": [float(outlier_bounds[0]), float(outlier_bounds[1])],
                            })
                            analysis["anomaly_score"] += 0.3

        except Exception as e:
            logger.debug(f"Tensor analysis error for {name}: {e}")
            analysis["error"] = str(e)

        return analysis

    def _compare_against_baseline(self, data: bytes) -> Dict[str, Any]:
        """Compare against known baseline model if available."""
        details = {"message": "No baseline model available for comparison"}
        drift_score = 0.0

        try:
            # Generate model digest
            model_digest = hashlib.sha256(data).hexdigest()

            # Check if we have a baseline for comparison
            # In production, this would query a model registry
            baseline_path = self.known_base_models.get(f"sha256:{model_digest[:16]}")

            if baseline_path and Path(baseline_path).exists():
                # Load baseline and compare
                with open(baseline_path, "rb") as f:
                    baseline_data = f.read()

                # Detailed comparison would go here
                # For now, implement basic drift detection
                drift_analysis = self._calculate_model_drift(data, baseline_data)
                drift_score = drift_analysis["drift_score"]
                details = drift_analysis["details"]
            else:
                # No baseline available - model family analysis not implemented
                details["message"] = "No baseline model available and model family analysis not implemented"

        except Exception as e:
            logger.debug(f"Baseline comparison error: {e}")
            details["error"] = str(e)

        return {"score": drift_score, "details": details}

    def _scan_textual_resources(self, data: bytes) -> Dict[str, Any]:
        """Scan textual content with format-aware MIME detection."""
        details = {"scanned_content_types": [], "format_analysis": {}}
        pattern_score = 0.0

        try:
            # 1. FORMAT-AWARE ANALYSIS - Don't decode binary model formats
            format_type = self._detect_content_format(data)
            details["format_analysis"] = format_type

            # Skip textual scanning for binary model formats
            if format_type["is_binary_model"]:
                details["message"] = f"Skipping textual scan for binary model format: {format_type['detected_format']}"
                return {"score": 0.0, "details": details}

            # 2. MIME-AWARE TEXT DETECTION for non-model formats
            text_content = None

            if format_type["mime_type"] and format_type["mime_type"].startswith("text/"):
                # MIME indicates text - safe to decode
                try:
                    text_content = data.decode("utf-8", errors="replace")
                    details["scanned_content_types"].append("mime_text_content")
                except Exception:
                    details["message"] = "MIME indicates text but UTF-8 decode failed"
                    return {"score": 0.0, "details": details}

            elif format_type["appears_textual"]:
                # Heuristic indicates text-like content
                try:
                    # Conservative text detection - only for clearly textual content
                    sample = data[:2048]  # Larger sample for better detection
                    sample_str = sample.decode("utf-8", errors="strict")

                    if self._is_definitely_text_content(sample_str):
                        text_content = data.decode("utf-8", errors="replace")
                        details["scanned_content_types"].append("heuristic_text_content")
                    else:
                        details["message"] = "Content appears textual but failed strict text validation"

                except UnicodeDecodeError:
                    # Definitely not text if strict decode fails
                    details["message"] = "Content failed UTF-8 strict decode - not textual"

            # 3. Extract embedded text ONLY for hybrid formats (like safetensors headers)
            if not text_content and format_type["may_contain_embedded_text"]:
                embedded_text = self._extract_embedded_text_sections(data)
                if embedded_text:
                    text_content = embedded_text
                    details["scanned_content_types"].append("embedded_text_sections")

            # 4. Weighted pattern scanning only if we have legitimate text content
            if text_content and len(text_content.strip()) > 50:
                pattern_analysis = self._scan_text_for_patterns(text_content)

                if pattern_analysis["categories_detected"]:
                    details["pattern_analysis"] = pattern_analysis
                    details["categories_detected"] = len(pattern_analysis["categories_detected"])
                    details["severity_summary"] = pattern_analysis["severity_breakdown"]

                    # Use weighted signal score instead of simple counting
                    pattern_score = pattern_analysis["total_signal_score"]

                    # Additional risk amplification based on severity mix
                    severity_breakdown = pattern_analysis["severity_breakdown"]
                    if severity_breakdown["critical"] > 0:
                        pattern_score *= 1.5  # Amplify if critical patterns found
                    elif severity_breakdown["high"] > 2:
                        pattern_score *= 1.3  # Amplify if multiple high-severity patterns

                    pattern_score = min(pattern_score, 1.0)  # Cap at 1.0
                else:
                    details["message"] = "Text scanned - no suspicious patterns detected"
            else:
                details["message"] = "No legitimate textual content found for pattern scanning"

        except Exception as e:
            logger.debug(f"Textual scanning error: {e}")
            details["error"] = str(e)

        return {"score": pattern_score, "details": details}

    def _calculate_weighted_score(self, signals: Dict[str, Any]) -> float:
        """Calculate final weighted score from all signals.

        Combines individual signal scores using weighted averaging to produce a final
        backdoor detection confidence score between 0.0 and 1.0.

        Formula: final_score = Σ(signal_score_i * weight_i) for all signals

        Args:
        ----
            signals: Dictionary containing individual signal scores (0.0-1.0 each)
                    - weight_anomalies: Statistical weight analysis score
                    - baseline_drift: Model drift comparison score
                    - textual_patterns: Malicious pattern detection score

        Returns:
        -------
            float: Final weighted score (0.0-1.0) where:
                   0.0-0.4 = Low risk (ALLOW)
                   0.4-0.8 = Medium risk (QUARANTINE)
                   0.8-1.0 = High risk (BLOCK)

        Example:
        -------
            signals = {
                'weight_anomalies': 0.7,      # 70% confidence in weight tampering
                'baseline_drift': 0.5,        # 50% confidence in model drift
                'textual_patterns': 0.8       # 80% confidence in malicious patterns
            }

            final_score = (0.7 * 0.5) + (0.5 * 0.3) + (0.8 * 0.2)
                        = 0.35 + 0.15 + 0.16 = 0.66 → QUARANTINE
        """
        total_score = 0.0

        for signal_type, weight in self.signal_weights.items():
            signal_score = signals.get(signal_type, 0.0)
            total_score += signal_score * weight

            # Log individual signal contributions for debugging
            if signal_score > 0.1:  # Only log meaningful contributions
                logger.debug(f"Signal {signal_type}: {signal_score:.3f} * {weight:.1f} = {signal_score * weight:.3f}")

        final_score = min(total_score, 1.0)  # Cap at 1.0
        logger.debug(f"Final weighted backdoor score: {final_score:.3f}")

        return final_score

    def _map_score_to_policy(self, score: float, signal_breakdown: Dict[str, float] = None) -> Tuple[str, Severity]:
        """Enhanced policy mapping with signal-aware decision making."""
        # Basic threshold mapping
        if score >= self.score_thresholds["block"]:
            base_action = "BLOCK"
            base_severity = Severity.CRITICAL
        elif score >= self.score_thresholds["quarantine"]:
            base_action = "QUARANTINE"
            base_severity = Severity.HIGH
        else:
            base_action = "ALLOW"
            base_severity = Severity.MEDIUM

        # Enhanced policy logic based on signal composition
        if signal_breakdown:
            # Override ALLOW to QUARANTINE if high textual pattern scores
            if (base_action == "ALLOW" and
                signal_breakdown.get("textual_patterns", 0) > 0.5):
                return "QUARANTINE", Severity.HIGH

            # Override QUARANTINE to BLOCK if multiple high-risk signals
            if (base_action == "QUARANTINE" and
                sum(1 for signal, signal_score in signal_breakdown.items()
                    if signal_score > 0.6) >= 2):
                return "BLOCK", Severity.CRITICAL

            # Override ALLOW to QUARANTINE if baseline drift is significant
            if (base_action == "ALLOW" and
                signal_breakdown.get("baseline_drift", 0) > 0.7):
                return "QUARANTINE", Severity.HIGH

            # Always BLOCK if weight anomalies are extreme (regardless of other signals)
            if signal_breakdown.get("weight_anomalies", 0) > 0.9:
                return "BLOCK", Severity.CRITICAL

        return base_action, base_severity

    def _get_recommendation(self, score: float, signals: Dict[str, Any]) -> str:
        """Generate contextual recommendation based on weighted signal analysis."""
        signal_breakdown = {k: v for k, v in signals.items() if k != "details" and isinstance(v, (int, float))}

        recommendations = []

        # High overall score
        if score >= 0.8:
            recommendations.append("CRITICAL: Multiple backdoor indicators detected")
            recommendations.append("→ BLOCK model immediately")
            recommendations.append("→ Conduct forensic analysis of all signals")
        elif score >= 0.4:
            recommendations.append("WARNING: Suspicious patterns detected")
            recommendations.append("→ QUARANTINE for detailed security review")

        # Specific signal-based recommendations
        if signal_breakdown.get("weight_anomalies", 0) > 0.6:
            recommendations.append("→ Weight analysis shows statistical anomalies - verify tensor integrity")

        if signal_breakdown.get("textual_patterns", 0) > 0.5:
            recommendations.append("→ High-risk textual patterns found - manual review required")

        if signal_breakdown.get("baseline_drift", 0) > 0.5:
            recommendations.append("→ Significant drift from baseline model - verify provenance and integrity")

        # Policy-specific recommendations
        details = signals.get("details", {})
        if "textual_analysis" in details:
            text_details = details["textual_analysis"]
            if "pattern_analysis" in text_details:
                pattern_analysis = text_details["pattern_analysis"]
                severity_breakdown = pattern_analysis.get("severity_breakdown", {})

                if severity_breakdown.get("critical", 0) > 0:
                    recommendations.append("→ CRITICAL textual patterns detected - code injection risk")
                elif severity_breakdown.get("high", 0) > 0:
                    recommendations.append("→ HIGH-RISK textual patterns detected - review configuration files")

        # Fallback recommendation
        if not recommendations:
            recommendations.append("Model appears clean based on current analysis")
            recommendations.append("→ Continue monitoring for anomalies in production")

        return " | ".join(recommendations)

    # Helper methods for detailed analysis
    def _parse_safetensors_weights(self, data: bytes, limit_tensors: bool = False) -> Dict[str, Any]:
        """Parse safetensors format to extract weight tensors with memory protection."""
        tensors = {}
        tensor_count = 0

        if not HAS_NUMPY:
            logger.debug("Numpy not available - safetensors weight analysis disabled")
            return tensors

        try:
            # Parse header length
            if len(data) < 8:
                return tensors

            header_len = struct.unpack("<Q", data[:8])[0]
            if header_len > len(data) - 8:
                return tensors

            # MEMORY PROTECTION: Validate header size
            if header_len > 100 * 1024 * 1024:  # 100MB header limit
                logger.warning(f"Safetensors header too large ({header_len/1024/1024:.1f}MB), skipping weight analysis")
                return tensors

            # Parse header JSON
            header_bytes = data[8:8+header_len]
            header = json.loads(header_bytes.decode("utf-8"))

            # MEMORY PROTECTION: Limit number of tensors processed
            tensor_names = [k for k in header if k != "__metadata__"]
            if limit_tensors and len(tensor_names) > self.max_tensors_to_analyze:
                logger.info(f"Large model with {len(tensor_names)} tensors, sampling {self.max_tensors_to_analyze} for analysis")
                import random
                tensor_names = random.sample(tensor_names, self.max_tensors_to_analyze)

            # Extract tensor metadata and data
            for tensor_name in tensor_names:
                if tensor_name not in header:
                    continue

                tensor_info = header[tensor_name]
                dtype = tensor_info["dtype"]
                shape = tensor_info["shape"]
                data_offsets = tensor_info["data_offsets"]

                # MEMORY PROTECTION: Check tensor size before loading
                tensor_size = data_offsets[1] - data_offsets[0]
                if tensor_size > 500 * 1024 * 1024:  # Skip tensors > 500MB
                    logger.debug(f"Skipping large tensor {tensor_name} ({tensor_size/1024/1024:.1f}MB)")
                    continue

                # Extract tensor data
                start_offset = 8 + header_len + data_offsets[0]
                end_offset = 8 + header_len + data_offsets[1]

                if end_offset <= len(data):
                    tensor_bytes = data[start_offset:end_offset]

                    try:
                        tensor_array = np.frombuffer(tensor_bytes, dtype=self._safetensors_dtype_to_numpy(dtype))
                        tensor_array = tensor_array.reshape(shape)
                        tensors[tensor_name] = tensor_array
                        tensor_count += 1

                        # MEMORY PROTECTION: Break if too many tensors loaded
                        if tensor_count >= self.max_tensors_to_analyze:
                            logger.debug(f"Reached tensor limit ({self.max_tensors_to_analyze}), stopping parsing")
                            break

                    except (ValueError, MemoryError) as e:
                        logger.debug(f"Error loading tensor {tensor_name}: {e}")
                        continue

        except Exception as e:
            logger.debug(f"Safetensors parsing error: {e}")

        logger.debug(f"Loaded {len(tensors)} tensors for analysis")
        return tensors

    def _analyze_weight_statistics_sampled(self, data: bytes, model_size_mb: float) -> Dict[str, Any]:
        """Analyze weight statistics using sampling for very large models."""
        details = {
            "message": f"Large model analysis ({model_size_mb:.1f}MB) using sampling",
            "sample_ratio": self.tensor_sample_ratio,
            "analysis_method": "sampled",
        }

        try:
            # Use limited tensor parsing for large models
            tensors = self._parse_safetensors_weights(data, limit_tensors=True)

            if not tensors:
                return {"score": 0.0, "details": {**details, "error": "No tensors could be parsed from large model"}}

            # Perform statistical analysis on sampled tensors
            anomaly_score, tensor_details = self._compute_tensor_statistics(tensors)

            # Scale score based on sampling uncertainty
            confidence_factor = min(len(tensors) / 50, 1.0)  # Lower confidence with fewer samples
            adjusted_score = anomaly_score * confidence_factor

            details.update({
                "tensors_analyzed": len(tensors),
                "confidence_factor": confidence_factor,
                "raw_anomaly_score": anomaly_score,
                "adjusted_score": adjusted_score,
                **tensor_details,
            })

            return {"score": adjusted_score, "details": details}

        except Exception as e:
            logger.error(f"Error in sampled weight analysis: {str(e)}")
            return {"score": 0.0, "details": {**details, "error": str(e)}}

    def _safetensors_dtype_to_numpy(self, dtype: str) -> str:
        """Convert safetensors dtype to numpy dtype."""
        dtype_map = {
            "F32": "float32", "F16": "float16", "BF16": "bfloat16",
            "I32": "int32", "I16": "int16", "I8": "int8",
            "U32": "uint32", "U16": "uint16", "U8": "uint8",
            "BOOL": "bool",
        }
        return dtype_map.get(dtype, "float32")

    def _detect_content_format(self, data: bytes) -> Dict[str, Any]:
        """Detect content format and MIME type with context awareness."""
        analysis = {
            "detected_format": "unknown",
            "mime_type": None,
            "is_binary_model": False,
            "appears_textual": False,
            "may_contain_embedded_text": False,
        }

        if len(data) < 16:
            return analysis

        # Check magic bytes for known binary model formats
        header = data[:16]

        # Safetensors: starts with 8-byte header length + JSON
        if len(data) >= 8:
            try:
                header_len = struct.unpack("<Q", data[:8])[0]
                if header_len > 0 and header_len < len(data) and data[8:9] == b"{":
                    analysis.update({
                        "detected_format": "safetensors",
                        "mime_type": "application/octet-stream",
                        "is_binary_model": True,
                        "may_contain_embedded_text": True,  # JSON header only
                    })
                    return analysis
            except Exception as e:
                logger.debug(f"Error analyzing safetensors format: {e}")

        # GGUF: magic bytes "GGUF"
        if header[:4] == b"GGUF":
            analysis.update({
                "detected_format": "gguf",
                "mime_type": "application/octet-stream",
                "is_binary_model": True,
                "may_contain_embedded_text": True,  # Metadata only
            })
            return analysis

        # ONNX: protobuf format (starts with specific bytes or has .onnx extension indicators)
        if (header[:4] in [b"\x08\x01\x12", b"\x08\x02\x12", b"\x08\x03\x12"] or
            header[:8] == b"\x08\x07\x12\x04\x08\x01\x18\x07" or  # Common ONNX header pattern
            header[:2] == b"\x08\x07"):  # Another ONNX pattern
            analysis.update({
                "detected_format": "onnx",
                "mime_type": "application/octet-stream",
                "is_binary_model": True,
                "may_contain_embedded_text": False,
            })
            return analysis

        # Pickle formats
        if header[:2] in [b"\x80\x02", b"\x80\x03", b"\x80\x04", b"\x80\x05"] or header[:8] == b"PYTORCH_":
            analysis.update({
                "detected_format": "pickle/pytorch",
                "mime_type": "application/octet-stream",
                "is_binary_model": True,
                "may_contain_embedded_text": False,
            })
            return analysis

        # HDF5 format (used by some models)
        if header[:8] == b"\x89HDF\r\n\x1a\n":
            analysis.update({
                "detected_format": "hdf5",
                "mime_type": "application/octet-stream",
                "is_binary_model": True,
                "may_contain_embedded_text": False,
            })
            return analysis

        # Use Python's mimetypes for other formats

        # Try to guess based on content
        sample = data[:1024]
        try:
            # Check if it's likely binary tensor/numerical data
            printable_ratio = sum(1 for b in sample if 32 <= b <= 126 or b in [9, 10, 13]) / len(sample)

            # Additional checks for binary numerical data
            has_null_bytes = sample.count(0) > len(sample) * 0.05  # >5% null bytes
            has_high_bytes = sum(1 for b in sample if b > 127) > len(sample) * 0.2  # >20% high bytes
            lacks_text_structure = not any(marker in sample for marker in [b" ", b"\n", b"\t", b":", b"{", b"<"])

            # If large size with binary characteristics, treat as binary tensor
            if (len(data) > 4096 and  # Large enough to be tensor data
                (printable_ratio < 0.7 or  # Low printable ratio OR
                 (has_null_bytes and has_high_bytes and lacks_text_structure))):  # Clear binary patterns
                analysis.update({
                    "detected_format": "binary_tensor",
                    "mime_type": "application/octet-stream",
                    "is_binary_model": True,  # Treat as binary model data
                    "appears_textual": False,
                })
                return analysis

            # Check if it's likely JSON
            if sample.strip().startswith(b"{") and sample.strip().endswith(b"}"):
                analysis.update({
                    "detected_format": "json",
                    "mime_type": "application/json",
                    "is_binary_model": False,
                    "appears_textual": True,
                })
                return analysis

            # Check if it's likely YAML
            if b"---" in sample[:50] or b":" in sample[:100]:
                decoded_sample = sample.decode("utf-8", errors="ignore")
                if any(indicator in decoded_sample for indicator in [":\n", ": ", "---"]):
                    analysis.update({
                        "detected_format": "yaml",
                        "mime_type": "text/yaml",
                        "is_binary_model": False,
                        "appears_textual": True,
                    })
                    return analysis

            # Check if it's likely plain text (higher threshold for text detection)
            if printable_ratio > 0.85:
                analysis.update({
                    "detected_format": "text",
                    "mime_type": "text/plain",
                    "is_binary_model": False,
                    "appears_textual": True,
                })
                return analysis

        except Exception:
            pass

        # Default to binary
        analysis.update({
            "detected_format": "binary",
            "mime_type": "application/octet-stream",
            "is_binary_model": False,  # Unknown binary, not necessarily a model
            "appears_textual": False,
        })

        return analysis

    def _is_definitely_text_content(self, sample: str) -> bool:
        """Strict validation for text content - higher bar than _is_likely_text_content."""
        if len(sample) < 100:  # Need substantial sample
            return False

        # Check for very high ratio of printable characters
        printable_count = sum(1 for c in sample if c.isprintable() or c.isspace())
        printable_ratio = printable_count / len(sample)

        # Check for clear text structure indicators
        text_structure_indicators = [
            "{", "}", "<", ">", "=", ":", '"', "[", "]", "\n",
            "(", ")", ",", ";", "!", "?", "@", "#",
        ]
        indicator_count = sum(1 for c in sample if c in text_structure_indicators)
        indicator_ratio = indicator_count / len(sample)

        # Check for word-like patterns (letters separated by spaces/punctuation)
        word_chars = sum(1 for c in sample if c.isalnum())
        word_ratio = word_chars / len(sample) if len(sample) > 0 else 0

        # Strict criteria: high printable ratio AND good structure AND word-like content
        return (printable_ratio > 0.92 and
                indicator_ratio > 0.05 and
                word_ratio > 0.3)

    def _extract_embedded_text_sections(self, data: bytes) -> Optional[str]:
        """Extract embedded text sections from binary data."""
        # Look for JSON-like structures or configuration sections
        text_sections = []

        # Simple approach: find sequences of printable ASCII
        current_text = ""
        min_text_length = 50

        for byte in data[:65536]:  # First 64KB only
            char = chr(byte) if 32 <= byte <= 126 else None

            if char:
                current_text += char
            else:
                if len(current_text) >= min_text_length:
                    text_sections.append(current_text)
                current_text = ""

        # Final check
        if len(current_text) >= min_text_length:
            text_sections.append(current_text)

        return "\n".join(text_sections) if text_sections else None

    def _scan_text_for_patterns(self, text_content: str) -> Dict[str, Any]:
        """Scan text content for backdoor patterns with weighted scoring using pre-compiled patterns."""
        signal_details = {
            "categories_detected": [],
            "total_signal_score": 0.0,
            "pattern_matches": {},
            "severity_breakdown": {"critical": 0, "high": 0, "medium": 0, "low": 0},
        }

        text_lower = text_content.lower()

        for category, config in self.textual_backdoor_patterns.items():
            # Get only successfully compiled patterns (all are re.Pattern objects now)
            compiled_patterns = self.compiled_patterns.get(category, [])
            base_score = config["base_score"]
            severity = config["severity"]
            description = config["description"]

            category_matches = []
            category_score = 0.0

            # All patterns in compiled_patterns are guaranteed to be re.Pattern objects
            for i, compiled_pattern in enumerate(compiled_patterns):
                try:
                    # Get original pattern string for reporting
                    original_patterns = config["patterns"]
                    pattern_str = original_patterns[i] if i < len(original_patterns) else str(compiled_pattern.pattern)

                    # Use compiled pattern for high performance
                    regex_matches = list(compiled_pattern.finditer(text_lower))

                    for match in regex_matches:
                        match_info = {
                            "pattern": pattern_str,
                            "matched_text": match.group(),
                            "position": match.start(),
                            "context": text_content[max(0, match.start()-20):match.end()+20],
                            "severity": severity,
                        }
                        category_matches.append(match_info)

                        # Calculate weighted score for this match
                        # Base score * frequency multiplier * context multiplier
                        frequency_multiplier = min(1.0 + (len(regex_matches) - 1) * 0.2, 2.0)  # Cap at 2x
                        context_multiplier = self._calculate_context_multiplier(match.group(), text_content, match.start())

                        match_score = base_score * frequency_multiplier * context_multiplier
                        category_score += match_score

                except Exception as e:
                    # Log unexpected errors with compiled patterns
                    logger.error(f"Error applying compiled pattern in category '{category}': {str(e)}")
                    continue

            # Log skipped patterns for this category
            failed_patterns = self.failed_patterns.get(category, [])
            if failed_patterns:
                logger.debug(f"Skipped {len(failed_patterns)} invalid patterns in category '{category}'")

            if category_matches:
                # Cap category score and add to total
                category_score = min(category_score, 1.0)  # Cap individual category at 1.0
                signal_details["total_signal_score"] += category_score
                signal_details["severity_breakdown"][severity] += len(category_matches)

                signal_details["categories_detected"].append({
                    "category": category,
                    "description": description,
                    "severity": severity,
                    "base_score": base_score,
                    "category_score": category_score,
                    "matches": category_matches[:5],  # Limit for output
                    "total_matches": len(category_matches),
                })

                signal_details["pattern_matches"][category] = {
                    "score": category_score,
                    "count": len(category_matches),
                    "severity": severity,
                }

        # Cap total signal score
        signal_details["total_signal_score"] = min(signal_details["total_signal_score"], 1.0)

        return signal_details

    def _calculate_context_multiplier(self, matched_text: str, full_text: str, position: int) -> float:
        """Calculate context-based score multiplier."""
        context_window = 100
        start = max(0, position - context_window)
        end = min(len(full_text), position + len(matched_text) + context_window)
        context = full_text[start:end].lower()

        # Higher multiplier for dangerous contexts
        dangerous_contexts = [
            "import", "from", "def ", "class ", "lambda", "config",
            "setup", "install", "download", "execute", "run",
        ]

        multiplier = 1.0
        for danger_word in dangerous_contexts:
            if danger_word in context:
                multiplier += 0.2

        # Higher multiplier if in quoted strings (often configuration values)
        if '"' in context or "'" in context:
            multiplier += 0.3

        return min(multiplier, 2.0)  # Cap at 2.0x

    def _calculate_model_drift(self, current_data: bytes, baseline_data: bytes) -> Dict[str, Any]:
        """Calculate drift between current model and baseline."""
        # Simplified drift calculation - in production would be much more sophisticated
        drift_score = 0.0
        details = {}

        try:
            # Basic size comparison
            size_diff = abs(len(current_data) - len(baseline_data)) / len(baseline_data)
            if size_diff > 0.1:  # >10% size difference
                drift_score += 0.2
                details["size_drift"] = {
                    "current_size": len(current_data),
                    "baseline_size": len(baseline_data),
                    "size_difference_ratio": float(size_diff),
                }

            # Hash comparison for exact match detection
            current_hash = hashlib.sha256(current_data).hexdigest()
            baseline_hash = hashlib.sha256(baseline_data).hexdigest()

            if current_hash != baseline_hash:
                drift_score += 0.1
                details["hash_mismatch"] = {
                    "current_hash": current_hash[:16] + "...",
                    "baseline_hash": baseline_hash[:16] + "...",
                }

        except Exception as e:
            details["error"] = str(e)

        return {"drift_score": drift_score, "details": details}

