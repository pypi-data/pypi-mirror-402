"""Supply chain security validator."""

import hashlib
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from palisade.core.cedar_policy_engine import CedarPolicyEngine

from palisade.models.metadata import ModelMetadata, ModelType
from palisade.utils.patterns import PatternMatcher, SecurityPatterns

from .base import BaseValidator, Severity

logger = logging.getLogger(__name__)

class SupplyChainValidator(BaseValidator):
    """Validator for checking supply chain security and model provenance."""

    def __init__(self, metadata: Optional[ModelMetadata] = None, policy_engine: Optional["CedarPolicyEngine"] = None) -> None:
        super().__init__(metadata, policy_engine)

        # Use centralized security patterns with validator-specific additions
        self.suspicious_patterns = {
            "malicious_imports": SecurityPatterns.MALICIOUS_FUNCTIONS,
            "data_exfiltration": SecurityPatterns.DATA_EXFILTRATION,
            "suspicious_files": {
                "setup.py", "__init__.py", "requirements.txt", "pip.conf",
                "conda.yaml", "environment.yml", ".env",
            },
            "untrusted_sources": SecurityPatterns.TAMPERING_INDICATORS,
        }

        # Known compromised package indicators
        self.compromised_indicators = {
            "typosquatting_patterns": [
                "tensorflow-gpu", "tensorflow-cpu", "torch-gpu", "torch-cuda",
                "scikit-learn-gpu", "sklearn-gpu", "numpy-gpu", "pandas-gpu",
            ],
            "suspicious_domains": [
                "pypi-mirror.com", "pip-mirror.org", "pytorch-unofficial.com",
                "tensorflow-mirror.net", "conda-unofficial.org",
            ],
        }

    def can_validate(self, model_type: ModelType) -> bool:
        """This validator can analyze all LLM/classifier types."""
        llm_types = {
            ModelType.LLAMA, ModelType.GPT, ModelType.BERT, ModelType.ROBERTA,
            ModelType.T5, ModelType.BLOOM, ModelType.MISTRAL, ModelType.MIXTRAL,
            ModelType.CLASSIFIER, ModelType.SEQUENCE_CLASSIFICATION,
            ModelType.TOKEN_CLASSIFICATION, ModelType.TEXT_CLASSIFICATION,
            ModelType.SAFETENSORS, ModelType.GGUF, ModelType.HUGGINGFACE,
        }
        return model_type in llm_types

    def validate(self, data: bytes) -> List[Dict[str, Any]]:
        """Validate model data for supply chain security issues."""
        warnings = []

        try:
            # Use centralized pattern matching
            pattern_results = PatternMatcher.scan_for_patterns(data, self.suspicious_patterns)

            # Process results
            for category, found_patterns in pattern_results.items():
                if found_patterns:
                    severity = self._determine_severity(category, len(found_patterns))
                    warnings.append(self.create_standard_warning(
                        f"supply_chain_{category}",
                        f"Suspicious {category} patterns detected (found {len(found_patterns)} times)",
                        severity,
                        f"Verify model source and integrity for {category} risks",
                        patterns=found_patterns[:10],
                        total_patterns=len(found_patterns),
                    ))

            # Convert data to string for text-based analysis
            try:
                data_str = data.decode("utf-8", errors="ignore")
            except Exception:
                data_str = ""  # Fallback to empty string if decoding fails

            # Check for compromised package indicators
            compromised_issues = self._check_compromised_indicators(data_str)
            if compromised_issues:
                warnings.append(self.create_standard_warning(
                    "compromised_packages",
                    compromised_issues["message"],
                    Severity.HIGH,
                    compromised_issues.get("recommendation", "Verify package sources and consider using official repositories only"),
                    **{k: v for k, v in compromised_issues.items() if k not in ["message", "recommendation"]}
                ))

            # Check model integrity
            integrity_issues = self._check_model_integrity(data)
            if integrity_issues:
                warnings.append(self.create_standard_warning(
                    "integrity_issues",
                    integrity_issues["message"],
                    Severity.MEDIUM,
                    integrity_issues.get("recommendation", "Verify model integrity and source"),
                    **{k: v for k, v in integrity_issues.items() if k not in ["message", "recommendation"]}
                ))

        except Exception as e:
            logger.error(f"Error in supply chain validation: {str(e)}")
            warnings.append(self.create_standard_warning(
                "validation_error",
                f"Error during supply chain analysis: {str(e)}",
                Severity.LOW,
                "Manual security review recommended"
            ))

        return warnings

    def _determine_severity(self, category: str, pattern_count: int) -> Severity:
        """Determine severity based on category and pattern count."""
        high_risk_categories = {"malicious_imports", "data_exfiltration"}

        if category in high_risk_categories:
            return Severity.HIGH if pattern_count > 2 else Severity.MEDIUM
        else:
            return Severity.MEDIUM if pattern_count > 3 else Severity.LOW

    def _check_compromised_indicators(self, data_str: str) -> Optional[Dict[str, Any]]:
        """Check for known compromised package indicators."""
        found_indicators = []

        # Check for typosquatting patterns
        for pattern in self.compromised_indicators["typosquatting_patterns"]:
            if pattern in data_str:
                found_indicators.append(f"typosquatting: {pattern}")

        # Check for suspicious domains
        for domain in self.compromised_indicators["suspicious_domains"]:
            if domain in data_str:
                found_indicators.append(f"suspicious_domain: {domain}")

        if found_indicators:
            return {
                "message": "Known compromised package indicators detected",
                "indicators": found_indicators[:10],  # Limit to first 10
                "total_indicators": len(found_indicators),
                "recommendation": "Verify package sources and consider using official repositories only",
            }

        return None

    def _check_model_integrity(self, data: bytes) -> Optional[Dict[str, Any]]:
        """Check basic model integrity indicators."""
        try:
            # Calculate basic integrity metrics
            data_hash = hashlib.sha256(data).hexdigest()
            data_size = len(data)

            # Check for minimum size (models should be substantial)
            if data_size < 1000:  # Less than 1KB
                return {
                    "message": "Model file unusually small",
                    "size_bytes": data_size,
                    "hash": data_hash[:16],  # First 16 chars of hash
                    "recommendation": "Verify this is a complete model file",
                }

            # Check for suspicious file header patterns
            header = data[:100]
            if header.startswith((b"#!/bin/", b"#!python")):
                return {
                    "message": "Model file appears to contain executable script",
                    "header_preview": header[:50].hex(),
                    "recommendation": "Model files should not contain executable scripts",
                }

            # Check for excessive null bytes (might indicate padding or corruption)
            # Be more conservative for binary model formats like GGUF
            null_count = data[:10000].count(b"\x00")  # Check first 10KB
            if null_count > 8000:  # More than 80% null bytes in sample (was 50%)
                return {
                    "message": "High concentration of null bytes detected",
                    "null_percentage": (null_count / 10000) * 100,
                    "recommendation": "Verify model file integrity and encoding",
                }

        except Exception as e:
            logger.debug(f"Integrity check error: {str(e)}")
            return {
                "message": "Error during integrity check",
                "error": str(e),
                "recommendation": "Manual verification recommended",
            }

        return None

    def supports_streaming(self) -> bool:
        """SupplyChainValidator supports streaming validation."""
        return True

    def validate_streaming(self, model_file: "ModelFile") -> List[Dict[str, Any]]:
        """Stream-based supply chain security validation using high-performance Rust implementation.
        
        Uses Aho-Corasick algorithm with parallel processing for ~10-20x faster validation.
        """
        from palisade._native import SupplyChainStreamingValidator
        from palisade.models.model_file import ModelFile
        import multiprocessing
        
        warnings = []
        
        try:
            # Create Rust streaming validator with parallel processing
            num_cores = multiprocessing.cpu_count()
            validator = SupplyChainStreamingValidator(num_cores)
            
            logger.debug(f"Starting Rust-based supply chain validation (streaming, {num_cores} cores)")
            
            # Process model in chunks using Rust validator (GIL-free)
            for chunk_info in model_file.iter_chunk_info():
                chunk_data = chunk_info.data
                
                # Process chunk with Rust (releases GIL for parallel processing)
                validator.process_chunk(chunk_data)
            
            # Finalize and get comprehensive results from Rust
            result = validator.finalize()
            
            logger.debug(
                f"Supply chain validation complete: {result.total_matches} total matches, "
                f"risk score {result.risk_score:.2f}"
            )
            logger.debug(
                f"Breakdown: {len(result.malicious_functions_found)} malicious functions, "
                f"{len(result.data_exfiltration_found)} data exfiltration, "
                f"{len(result.tampering_indicators_found)} tampering, "
                f"{len(result.typosquatting_found)} typosquatting, "
                f"{len(result.suspicious_domains_found)} suspicious domains"
            )
            
            # Convert Rust results to Python warnings
            # Critical: Malicious functions
            if result.malicious_functions_found:
                severity = Severity.CRITICAL if len(result.malicious_functions_found) > 3 else Severity.HIGH
                # Extract function names (remove "malicious:" prefix)
                func_names = [f.replace("malicious:", "") for f in result.malicious_functions_found]
                funcs_list = ", ".join(sorted(set(func_names))[:10])
                if len(func_names) > 10:
                    funcs_list += f" (and {len(func_names) - 10} more)"
                
                warnings.append(self.create_standard_warning(
                    "supply_chain_malicious_functions",
                    f"Malicious functions detected: {funcs_list}",
                    severity,
                    recommendation="Model contains code execution or system access functions. "
                                  "Verify this is expected and from a trusted source.",
                    threat_type="code_execution",
                    attack_vector="Malicious code injection",
                    functions_found=func_names[:20]
                ))
            
            # High-risk: Data exfiltration
            if result.data_exfiltration_found:
                severity = Severity.CRITICAL if len(result.data_exfiltration_found) > 3 else Severity.HIGH
                exfil_names = [e.replace("exfiltration:", "") for e in result.data_exfiltration_found]
                exfil_list = ", ".join(sorted(set(exfil_names))[:10])
                if len(exfil_names) > 10:
                    exfil_list += f" (and {len(exfil_names) - 10} more)"
                
                warnings.append(self.create_standard_warning(
                    "supply_chain_data_exfiltration",
                    f"Data exfiltration patterns detected: {exfil_list}",
                    severity,
                    recommendation="Model contains patterns for data serialization, network operations, or file transfers. "
                                  "Verify this is legitimate functionality.",
                    threat_type="data_exfiltration",
                    attack_vector="Unauthorized data transmission",
                    patterns_found=exfil_names[:20]
                ))
            
            # High-risk: Tampering indicators
            if result.tampering_indicators_found:
                severity = Severity.CRITICAL if len(result.tampering_indicators_found) > 2 else Severity.HIGH
                tamper_names = [t.replace("tampering:", "") for t in result.tampering_indicators_found]
                tamper_list = ", ".join(sorted(set(tamper_names))[:5])
                if len(tamper_names) > 5:
                    tamper_list += f" (and {len(tamper_names) - 5} more)"
                
                warnings.append(self.create_standard_warning(
                    "supply_chain_tampering",
                    f"Model tampering indicators detected: {tamper_list}",
                    severity,
                    recommendation="Model contains evidence of unauthorized modification or backdoors. "
                                  "Do not use in production without thorough investigation.",
                    threat_type="supply_chain_attack",
                    attack_vector="Model tampering/backdoor injection",
                    indicators_found=tamper_names
                ))
            
            # Medium-risk: Typosquatting
            if result.typosquatting_found:
                severity = Severity.HIGH if len(result.typosquatting_found) > 2 else Severity.MEDIUM
                typo_names = [t.replace("typosquat:", "") for t in result.typosquatting_found]
                typo_list = ", ".join(sorted(set(typo_names))[:5])
                
                warnings.append(self.create_standard_warning(
                    "supply_chain_typosquatting",
                    f"Typosquatting package patterns detected: {typo_list}",
                    severity,
                    recommendation="Model references packages that may be typosquatting legitimate packages. "
                                  "Verify package names and sources.",
                    threat_type="supply_chain_attack",
                    attack_vector="Package typosquatting",
                    packages_found=typo_names
                ))
            
            # Medium-risk: Suspicious domains
            if result.suspicious_domains_found:
                severity = Severity.HIGH if len(result.suspicious_domains_found) > 1 else Severity.MEDIUM
                domain_names = [d.replace("domain:", "") for d in result.suspicious_domains_found]
                domain_list = ", ".join(sorted(set(domain_names))[:5])
                
                warnings.append(self.create_standard_warning(
                    "supply_chain_suspicious_domains",
                    f"Suspicious domains detected: {domain_list}",
                    severity,
                    recommendation="Model references domains known for hosting unofficial or compromised packages. "
                                  "Use only official repositories.",
                    threat_type="supply_chain_attack",
                    attack_vector="Malicious package repository",
                    domains_found=domain_names
                ))
        
        except Exception as e:
            logger.error(f"Error during Rust supply chain validation: {e}")
            warnings.append(self.create_standard_warning(
                "supply_chain_validation_error",
                f"Validation error: {str(e)}",
                Severity.MEDIUM,
                recommendation="Check file integrity or try alternative validation method",
                attack_vector="Unknown"
            ))
        
        return warnings
