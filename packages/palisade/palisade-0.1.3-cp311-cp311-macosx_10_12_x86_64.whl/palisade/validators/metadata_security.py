"""Metadata security validator for comprehensive model analysis."""

import json
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from palisade.core.cedar_policy_engine import CedarPolicyEngine

from palisade.models.metadata import ModelMetadata, ModelType

from .base import BaseValidator, Severity

logger = logging.getLogger(__name__)

class MetadataSecurityValidator(BaseValidator):
    """Validator for analyzing security implications of model metadata files."""

    def __init__(self, metadata: Optional[ModelMetadata] = None, policy_engine: Optional["CedarPolicyEngine"] = None) -> None:
        super().__init__(metadata, policy_engine)
        # Metadata security analysis is implemented in analyze_metadata_files()

        # High-risk patterns in metadata
        self.high_risk_patterns = {
            "data_sources": [
                "scraped from", "crawled", "harvested", "collected without permission",
                "reddit", "twitter", "social media", "private data", "personal information",
            ],
            "training_methods": [
                "uncensored", "unfiltered", "no safety", "bypass", "jailbreak",
                "adversarial training", "deceptive", "manipulative",
            ],
            "intended_use": [
                "weaponization", "surveillance", "manipulation", "deception",
                "misinformation", "harmful content", "illegal activities",
            ],
            "licensing_issues": [
                "unclear license", "no license", "proprietary", "research only",
                "non-commercial", "custom license", "modified license",
            ],
        }

        # Suspicious tokenizer patterns
        self.tokenizer_risks = {
            "injection_tokens": [
                "<script>", "<html>", "<img>", "javascript:", "eval(",
                "exec(", "system(", "import ", "__import__",
            ],
            "harmful_tokens": [
                "hack", "exploit", "malware", "virus", "attack",
                "bomb", "weapon", "kill", "harm", "illegal",
            ],
            "privacy_tokens": [
                "password", "secret", "key", "token", "private",
                "confidential", "ssn", "credit_card", "bank",
            ],
        }

    def can_validate(self, model_type: ModelType) -> bool:
        """This validator can analyze metadata for all LLM/classifier types."""
        llm_types = {
            ModelType.LLAMA, ModelType.GPT, ModelType.BERT, ModelType.ROBERTA,
            ModelType.T5, ModelType.BLOOM, ModelType.MISTRAL, ModelType.MIXTRAL,
            ModelType.CLASSIFIER, ModelType.SEQUENCE_CLASSIFICATION,
            ModelType.TOKEN_CLASSIFICATION, ModelType.TEXT_CLASSIFICATION,
            ModelType.SAFETENSORS, ModelType.GGUF, ModelType.HUGGINGFACE,
        }
        return model_type in llm_types

    def validate(self, data: bytes) -> List[Dict[str, Any]]:
        """Validate metadata data passed as JSON bytes.
        
        This validator only processes standalone JSON metadata files like:
        - config.json
        - tokenizer.json  
        - model_card.json
        - README.md (if JSON format)
        
        Binary model files (SafeTensors, GGUF, etc.) are handled by other validators.
        """
        warnings = []

        # Skip binary model files - they should be handled by other validators
        # This validator only processes standalone JSON metadata files
        if not data.startswith(b"{"):
            return warnings  # Not a JSON metadata file

        try:
            # Parse as JSON metadata
            metadata = json.loads(data.decode("utf-8"))
            
            # Treat as a single metadata file for analysis
            metadata_file = {
                "content": metadata,
                "filename": "metadata.json",
                "path": "metadata.json"
            }
            warnings = self._analyze_single_metadata_file(metadata_file)
            
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Not valid JSON metadata, return empty warnings
            pass

        return warnings

    def analyze_metadata_files(self, metadata_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze a list of metadata files for security issues."""
        warnings = []

        for meta_file in metadata_files:
            file_warnings = self._analyze_single_metadata_file(meta_file)
            warnings.extend(file_warnings)

        return warnings

    def _analyze_single_metadata_file(self, meta_file: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze a single metadata file."""
        warnings = []
        file_path = meta_file.get("filepath", "unknown")
        file_type = meta_file.get("type", "unknown")

        try:
            if file_type == "config":
                warnings.extend(self._analyze_config_metadata(meta_file))
            elif file_type == "tokenizer":
                warnings.extend(self._analyze_tokenizer_metadata(meta_file))
            elif file_type == "other":
                warnings.extend(self._analyze_other_metadata(meta_file))

        except Exception as e:
            warnings.append(self.create_standard_warning(
                "metadata_analysis_error",
                f"Error analyzing {file_path}: {str(e)}",
                Severity.MEDIUM,
            ))

        return warnings

    def _analyze_config_metadata(self, meta_file: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze configuration file metadata."""
        warnings = []
        analysis = meta_file.get("analysis", {})

        if not analysis.get("parsed_successfully", False):
            warnings.append(self.create_standard_warning(
                "config_parse_failed",
                f"Could not parse config file {meta_file['filename']}",
                Severity.LOW,
            ))
            return warnings

        content = analysis.get("content", {})

        # Check for high-risk patterns
        content_str = json.dumps(content).lower()
        for category, patterns in self.high_risk_patterns.items():
            for pattern in patterns:
                if pattern in content_str:
                    warnings.append(self.create_standard_warning(
                        f"config_{category}_risk",
                        f"High-risk pattern detected in config: {pattern}",
                        Severity.HIGH,
                        f"Review {category} configuration for security implications",
                        file=meta_file["filename"],
                        category=category,
                        pattern=pattern,
                    ))

        # Check for missing security configurations
        security_configs = ["safety_checker", "content_filter", "output_filter"]
        missing_security = [config for config in security_configs if config not in content_str]

        if missing_security:
            warnings.append(self.create_standard_warning(
                "missing_security_config",
                "Missing security configurations in model config",
                Severity.MEDIUM,
                "Consider adding safety and content filtering configurations",
                file=meta_file["filename"],
                missing_configs=missing_security,
            ))

        # Check for suspicious model architecture
        if "architectures" in content:
            architectures = content["architectures"]
            if isinstance(architectures, list):
                for arch in architectures:
                    if any(suspicious in str(arch).lower() for suspicious in ["custom", "modified", "hacked"]):
                        warnings.append(self.create_standard_warning(
                            "suspicious_architecture",
                            f"Suspicious architecture detected: {arch}",
                            Severity.HIGH,
                            "Verify the legitimacy of custom architectures",
                            file=meta_file["filename"],
                            architecture=arch,
                        ))

        return warnings

    def _analyze_tokenizer_metadata(self, meta_file: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze tokenizer file metadata."""
        warnings = []
        analysis = meta_file.get("analysis", {})

        if not analysis.get("parsed_successfully", False):
            return warnings

        vocab_analysis = analysis.get("vocab_analysis", {})

        # Check for suspicious tokens
        suspicious_tokens = vocab_analysis.get("suspicious_tokens", [])
        if suspicious_tokens:
            warnings.append(self.create_standard_warning(
                "suspicious_vocabulary",
                "Suspicious tokens found in vocabulary",
                Severity.HIGH,
                "Review vocabulary for potential injection vectors",
                file=meta_file["filename"],
                suspicious_tokens=suspicious_tokens[:10],
                total_suspicious=len(suspicious_tokens),
            ))

        # Check vocabulary size for anomalies
        vocab_size = vocab_analysis.get("vocab_size", 0)
        if vocab_size > 100000:  # Very large vocabulary
            warnings.append(self.create_standard_warning(
                "large_vocabulary",
                f"Unusually large vocabulary detected: {vocab_size} tokens",
                Severity.MEDIUM,
                "Large vocabularies may indicate data exfiltration or injection risks",
                file=meta_file["filename"],
                vocab_size=vocab_size,
            ))

        # Check for injection-prone tokens
        if "tokenizer_info" in analysis:
            tokenizer_info = analysis["tokenizer_info"]
            if tokenizer_info.get("model_type") == "unknown":
                warnings.append(self.create_standard_warning(
                    "unknown_tokenizer_type",
                    "Unknown or custom tokenizer type detected",
                    Severity.MEDIUM,
                    "Verify the safety of custom tokenizer implementations",
                    file=meta_file["filename"],
                ))

        return warnings

    def _analyze_other_metadata(self, meta_file: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze other metadata files (documentation, etc.)."""
        warnings = []

        content_preview = meta_file.get("content_preview", "").lower()

        # Check documentation for concerning content
        concerning_terms = [
            "uncensored", "jailbreak", "bypass", "harmful", "dangerous",
            "illegal", "unethical", "malicious", "exploit", "hack",
        ]

        found_terms = [term for term in concerning_terms if term in content_preview]

        if found_terms:
            warnings.append(self.create_standard_warning(
                "concerning_documentation",
                "Documentation contains concerning terms",
                Severity.MEDIUM,
                "Review documentation for potential misuse instructions",
                file=meta_file["filename"],
                concerning_terms=found_terms,
            ))

        return warnings

    # Removed placeholder methods - implemented functionality is in analyze_metadata_files()
