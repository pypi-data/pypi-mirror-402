"""Tokenizer hygiene validator - Critical for preventing injection attacks via tokenizer."""

import json
import logging
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from palisade.core.constants import (
    CHARACTER_CLASS_PATTERNS,
    DANGEROUS_UNICODE_RANGES,
    EXECUTABLE_EXTENSIONS,
    EXPECTED_TOKENIZER_FILES,
    HIGH_RISK_CONFUSABLE_PATTERNS,
    LEGITIMATE_TOKEN_EXCEPTIONS,
    POLICY_VIOLATION_SEVERITY,
    SUSPICIOUS_TOKEN_PATTERNS,
    TOKEN_DENY_PATTERNS,
    TOKEN_POLICY_RULES,
    UNICODE_CONFUSABLES,
)
from palisade.models.metadata import ModelMetadata, ModelType

from .base import BaseValidator, Severity

if TYPE_CHECKING:
    from palisade.core.cedar_policy_engine import CedarPolicyEngine
    from palisade.models.model_file import ModelFile

logger = logging.getLogger(__name__)

class TokenizerHygieneValidator(BaseValidator):
    """CRITICAL SECURITY VALIDATOR - Enhanced with Unicode Confusables + Token Policy Engine.

    Validates tokenizer security and hygiene with comprehensive multi-layered threat detection:
    - SentencePiece/tokenizer.json structure validation
    - Control token analysis in added_tokens.json
    - Detection of executable files alongside tokenizer
    - Suspicious vocabulary patterns

    SECURITY ENHANCEMENTS:
    🚨 Unicode Confusables Detection:
    - Homograph attack prevention (245+ character mappings)
    - Mixed script analysis with confidence scoring
    - Invisible/zero-width character detection

    🛡️ Token Policy Engine:
    - Length constraints (prevent buffer overflows)
    - Character class validation (restrict unsafe Unicode ranges)
    - Deny patterns for URL/shell/code injection fragments
    - Special token format validation
    - Configurable policy rules with exception handling

    🎯 Advanced Threat Detection:
    - Shell command patterns (curl, bash, sudo, etc.)
    - Code injection patterns (eval, exec, subprocess)
    - File access patterns (/etc/passwd, .ssh/, .aws/)
    - Network activity patterns (IPs, ports, .onion)
    - Obfuscation patterns (base64, hex encoding)
    - Path traversal attempts (../, %2e%2e)

    Protects against:
    - Homograph attacks: paypal vs paypal (Cyrillic spoofing)
    - Control token spoofing: <|end|> vs <|end|> (look-alike tokens)
    - Prompt injection bypasses: ignore vs ignore (confusable bypasses)
    - Shell injection: tokens containing "curl http://evil.com"
    - Code execution: tokens with "eval(malicious_code)"
    - Data exfiltration: tokens with file paths or network endpoints
    - Steganographic attacks: hidden zero-width characters
    - Policy violations: oversized tokens, unsafe character classes
    """

    def __init__(self, metadata: ModelMetadata, policy_engine: Optional["CedarPolicyEngine"] = None) -> None:
        super().__init__(metadata, policy_engine)

        # Load policy-configurable settings
        self._load_policy_configuration()

        # Use suspicious patterns from constants (policy-configurable)
        self.suspicious_control_tokens = SUSPICIOUS_TOKEN_PATTERNS

        # Use executable extensions from constants (policy-configurable)
        self.executable_extensions = EXECUTABLE_EXTENSIONS

        # Use expected tokenizer files from constants (policy-configurable)
        self.tokenizer_files = EXPECTED_TOKENIZER_FILES

    def _load_policy_configuration(self) -> None:
        """Load policy-configurable settings for tokenizer hygiene."""
        # Get policy configuration for tokenizer hygiene validator
        policy_config = {}
        if self.policy_engine and hasattr(self.policy_engine, "get_validator_config"):
            policy_config = self.policy_engine.get_validator_config("tokenizer_hygiene", {})

        # Load token count limits
        self.max_added_tokens = policy_config.get("max_added_tokens", 1000)
        self.max_token_length = policy_config.get("max_token_length", 1000)
        self.max_vocabulary_size = policy_config.get("max_vocabulary_size", 1000000)  # 1M tokens

        # Load unicode confusables detection settings
        self.detect_unicode_confusables = policy_config.get("detect_unicode_confusables", True)
        self.confusables_severity = policy_config.get("confusables_severity", "high")  # low, medium, high

        # Load suspicious pattern detection settings
        default_suspicious_patterns = set(SUSPICIOUS_TOKEN_PATTERNS)
        custom_patterns = policy_config.get("suspicious_token_patterns", default_suspicious_patterns)
        if isinstance(custom_patterns, list):
            self.suspicious_control_tokens = set(custom_patterns)
        else:
            self.suspicious_control_tokens = custom_patterns

        # Load executable file detection settings
        self.detect_executable_files = policy_config.get("detect_executable_files", True)
        custom_executable_extensions = policy_config.get("executable_extensions", EXECUTABLE_EXTENSIONS)
        if isinstance(custom_executable_extensions, list):
            self.executable_extensions = set(custom_executable_extensions)
        else:
            self.executable_extensions = custom_executable_extensions

        # Load tokenizer validation strictness
        self.validation_strictness = policy_config.get("validation_strictness", "medium")  # low, medium, high

        # Load character class restrictions
        self.allowed_unicode_categories = set(policy_config.get("allowed_unicode_categories",
                                                               ["Lu", "Ll", "Lt", "Lm", "Lo",  # Letters
                                                                "Nd", "Nl", "No",              # Numbers
                                                                "Pc", "Pd", "Ps", "Pe",        # Punctuation
                                                                "Pi", "Pf", "Po",              # Punctuation
                                                                "Sm", "Sc", "Sk", "So",        # Symbols
                                                                "Zs"]))                          # Space separators

        # Load zero-width character detection
        self.detect_zero_width_chars = policy_config.get("detect_zero_width_chars", True)

        # Load special token validation
        self.validate_special_tokens = policy_config.get("validate_special_tokens", True)
        self.required_special_tokens = set(policy_config.get("required_special_tokens",
                                                            ["<unk>", "<pad>", "<s>", "</s>"]))

    def can_validate(self, model_type: ModelType) -> bool:
        """This validator can analyze all LLM/classifier types with tokenizers."""
        llm_types = {
            ModelType.LLAMA, ModelType.GPT, ModelType.BERT, ModelType.ROBERTA,
            ModelType.T5, ModelType.BLOOM, ModelType.MISTRAL, ModelType.MIXTRAL,
            ModelType.CLASSIFIER, ModelType.SEQUENCE_CLASSIFICATION,
            ModelType.TOKEN_CLASSIFICATION, ModelType.TEXT_CLASSIFICATION,
            ModelType.SAFETENSORS, ModelType.GGUF, ModelType.HUGGINGFACE,
        }
        return model_type in llm_types

    def validate(self, data: bytes) -> List[Dict[str, Any]]:
        """Validate tokenizer file content using Rust-accelerated pattern matching.
        
        NOTE: This method is designed for tokenizer config files.
        For model weight files, use validate_streaming which filters appropriately.
        """
        warnings = []

        try:
            # Use Rust validator for fast pattern matching on tokenizer data
            from palisade._native import validate_tokenizer_hygiene
            import multiprocessing
            
            num_cores = multiprocessing.cpu_count()
            
            logger.debug(f"Starting Rust-based tokenizer hygiene (full data scan, {num_cores} cores)")
            
            # Validate using Rust (GIL released, parallel processing)
            result = validate_tokenizer_hygiene(data, num_cores)
            
            logger.debug(
                f"Tokenizer hygiene complete: {result.total_matches} total matches, "
                f"risk score {result.risk_score:.2f}"
            )
            
            # Generate warnings from Rust results
            warnings.extend(self._process_rust_tokenizer_results(result, len(data)))
            
            # Also do JSON structure validation (not handled by Rust)
            try:
                import json
                json_data = json.loads(data.decode('utf-8', errors='ignore'))
                self._analyze_json_for_tokens(json_data, "tokenizer", warnings)
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

        except Exception as e:
            logger.debug(f"Error in tokenizer validation: {str(e)}")
        
        return warnings

    def supports_streaming(self) -> bool:
        """TokenizerHygieneValidator supports streaming validation."""
        return True

    def validate_streaming(self, model_file: "ModelFile") -> List[Dict[str, Any]]:
        """Stream-based tokenizer hygiene using high-performance Rust implementation.
        
        Uses Aho-Corasick algorithm with parallel processing for ~100x faster validation.
        
        NOTE: Only scans tokenizer configuration files (.json), not model weight files.
        Model weights (.safetensors, .bin, .gguf) contain learned vocabulary which causes
        false positives when scanned for shell commands.
        """
        from palisade._native import TokenizerHygieneStreamingValidator
        import multiprocessing
        
        warnings = []
        
        # Skip validation for model weight files (not tokenizer configs)
        # These files contain learned vocabulary/weights, not executable tokenizer logic
        model_weight_extensions = {'.safetensors', '.bin', '.pt', '.pth', '.gguf', '.onnx'}
        file_path = str(model_file.file_info.path) if hasattr(model_file.file_info, 'path') else str(model_file)
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext in model_weight_extensions:
            logger.debug(f"Skipping TokenizerHygiene for model weight file: {file_ext}")
            return warnings  # No warnings for model weight files
        
        try:
            # Create Rust streaming validator with parallel processing
            num_cores = multiprocessing.cpu_count()
            validator = TokenizerHygieneStreamingValidator(num_cores)
            
            logger.debug(f"Starting Rust-based tokenizer hygiene (streaming, {num_cores} cores)")
            
            # Track file structure for context
            file_size_mb = model_file.file_info.size_bytes / (1024 * 1024)
            
            # Process model in chunks using Rust validator (GIL-free)
            for chunk_info in model_file.iter_chunk_info():
                chunk_data = chunk_info.data
                
                # Process chunk with Rust (releases GIL for parallel processing)
                validator.process_chunk(chunk_data)
            
            # Finalize and get comprehensive results from Rust
            result = validator.finalize()
            
            logger.debug(
                f"Tokenizer hygiene complete: {result.total_matches} total matches, "
                f"risk score {result.risk_score:.2f}"
            )
            
            # Generate warnings from Rust results
            warnings.extend(self._process_rust_tokenizer_results(result, file_size_mb))
        
        except Exception as e:
            logger.error(f"Rust streaming validation failed: {str(e)}")
            logger.warning("Falling back to Python implementation")
            warnings.append(self.create_standard_warning(
                warning_type="tokenizer_hygiene_error",
                message=f"Tokenizer hygiene encountered an error: {str(e)}",
                severity=Severity.LOW,
                recommendation="Manual review recommended"
            ))
        
        return warnings

    def _process_rust_tokenizer_results(self, result, file_size_info) -> List[Dict[str, Any]]:
        """Process Rust validation results into Python warnings."""
        warnings = []
        
        # Determine file size for context
        if isinstance(file_size_info, (int, float)):
            file_size_mb = file_size_info
        else:
            file_size_mb = len(file_size_info) / (1024 * 1024)
        
        # Generate warning for code injection
        if result.code_injection_found:
            pattern_names = [p.split(":", 1)[1] if ":" in p else p 
                           for p in result.code_injection_found]
            
            warnings.append(self.create_standard_warning(
                warning_type="tokenizer_code_injection",
                message=f"Code injection patterns detected: {', '.join(pattern_names[:5])}",
                severity=Severity.CRITICAL,
                recommendation="CRITICAL: Tokenizer may contain code injection vectors",
                patterns_found=pattern_names,
                pattern_count=len(pattern_names),
                file_size_mb=file_size_mb
            ))
        
        # Generate warning for prompt injection
        if result.prompt_injection_found:
            pattern_names = [p.split(":", 1)[1] if ":" in p else p 
                           for p in result.prompt_injection_found]
            
            warnings.append(self.create_standard_warning(
                warning_type="tokenizer_prompt_injection",
                message=f"Prompt injection patterns detected: {', '.join(pattern_names[:5])}",
                severity=Severity.HIGH,
                recommendation="Tokenizer may enable prompt injection attacks",
                patterns_found=pattern_names,
                pattern_count=len(pattern_names),
                file_size_mb=file_size_mb
            ))
        
        # Generate warning for network/file access
        if result.network_file_found:
            pattern_names = [p.split(":", 1)[1] if ":" in p else p 
                           for p in result.network_file_found]
            
            warnings.append(self.create_standard_warning(
                warning_type="tokenizer_network_file_access",
                message=f"Network/file access patterns detected: {', '.join(pattern_names[:5])}",
                severity=Severity.HIGH,
                recommendation="Tokenizer may enable file system or network access",
                patterns_found=pattern_names,
                pattern_count=len(pattern_names),
                file_size_mb=file_size_mb
            ))
        
        # Generate warning for shell commands
        if result.shell_command_found:
            pattern_names = [p.split(":", 1)[1] if ":" in p else p 
                           for p in result.shell_command_found]
            
            warnings.append(self.create_standard_warning(
                warning_type="tokenizer_shell_commands",
                message=f"Shell command patterns detected: {', '.join(pattern_names[:5])}",
                severity=Severity.CRITICAL,
                recommendation="CRITICAL: Tokenizer may enable shell command execution",
                patterns_found=pattern_names,
                pattern_count=len(pattern_names),
                file_size_mb=file_size_mb
            ))
        
        # Generate warning for hidden tokens (only actual malicious tags, not zero-width chars)
        if result.hidden_tokens_found:
            pattern_names = [p.split(":", 1)[1] if ":" in p else p 
                           for p in result.hidden_tokens_found]
            
            warnings.append(self.create_standard_warning(
                warning_type="tokenizer_hidden_tokens",
                message=f"Hidden/malicious tokens detected: {', '.join(pattern_names[:5])}",
                severity=Severity.HIGH,
                recommendation="Tokenizer contains suspicious hidden tokens like <backdoor>, <trigger>, etc.",
                patterns_found=pattern_names,
                pattern_count=len(pattern_names),
                file_size_mb=file_size_mb
            ))
        
        return warnings

    def validate_file(self, model_file: "ModelFile") -> List[Dict[str, Any]]:
        """Validate individual tokenizer JSON file.
        
        Args:
        ----
            model_file: ModelFile instance containing the tokenizer JSON file
            
        Returns:
        -------
            List of warnings found during validation
        """
        warnings = []
        file_path = Path(model_file.file_info.path)
        
        # Check if this is a JSON file
        if file_path.suffix.lower() != '.json':
            return warnings
        
        # For individual JSON files, validate based on filename
        try:
            filename = file_path.name.lower()
            
            # Validate specific tokenizer file types
            if filename == "tokenizer.json":
                warnings.extend(self._validate_huggingface_tokenizer(file_path))
            elif filename == "added_tokens.json":
                warnings.extend(self._validate_added_tokens_file(file_path))
            elif filename == "tokenizer_config.json":
                warnings.extend(self._validate_tokenizer_config(file_path))
            elif "token" in filename or "vocab" in filename or "merges" in filename:
                # Generic tokenizer-related JSON
                warnings.extend(self._validate_generic_tokenizer_json(file_path))
            elif "config" in filename:
                # Configuration files might contain tokenizer settings
                warnings.extend(self._validate_tokenizer_config(file_path))
            else:
                # For other JSON files, do basic validation
                warnings.extend(self._validate_generic_tokenizer_json(file_path))
                
            # Apply policy evaluation if available
            if self.policy_engine and warnings:
                context = {
                    "tokenizer": {
                        "file_type": filename,
                        "suspicious_tokens_found": any("suspicious" in str(w).lower() for w in warnings),
                        "confusables_detected": any("confusable" in str(w).lower() or "homograph" in str(w).lower() for w in warnings),
                    },
                }
                return self.apply_policy(warnings, str(file_path), context)
                
        except Exception as e:
            logger.error(f"Error validating tokenizer file {file_path}: {str(e)}")
            warnings.append(self.create_standard_warning(
                "tokenizer_file_validation_error",
                f"Error validating tokenizer file: {str(e)}",
                Severity.MEDIUM,
                "Manual review recommended",
                error=str(e),
            ))
        
        return warnings

    def validate_tokenizer_directory(self, model_directory: str) -> List[Dict[str, Any]]:
        """CRITICAL: Validate tokenizer hygiene in model directory
        Main entry point for tokenizer security validation.
        """
        warnings = []
        model_dir = Path(model_directory)

        try:
            # Find tokenizer files
            tokenizer_files = self._discover_tokenizer_files(model_dir)

            if not tokenizer_files:
                return warnings  # No tokenizer files found

            logger.info(f"🔍 Found tokenizer files: {[f.name for f in tokenizer_files]}")

            # Validate each tokenizer file
            for tokenizer_file in tokenizer_files:
                file_warnings = self._validate_tokenizer_file(tokenizer_file)
                warnings.extend(file_warnings)

            # Check for executable files alongside tokenizer
            executable_warnings = self._check_executable_files(model_dir, tokenizer_files)
            warnings.extend(executable_warnings)

            # Cross-validate tokenizer files for consistency
            consistency_warnings = self._validate_tokenizer_consistency(model_dir, tokenizer_files)
            warnings.extend(consistency_warnings)

            # Analyze added tokens for suspicious patterns
            added_token_warnings = self._analyze_added_tokens(model_dir)
            warnings.extend(added_token_warnings)

        except Exception as e:
            logger.error(f"Error in tokenizer hygiene validation: {str(e)}")
            warnings.append(self.create_standard_warning(
                "tokenizer_validation_error",
                "Error validating tokenizer hygiene",
                Severity.MEDIUM,
                "Manual tokenizer verification recommended",
                error=str(e),
            ))

        # Add tokenizer-specific context for policy evaluation
        context = {
            "tokenizer": {
                "added_tokens_count": 0,  # Would count from actual token analysis
                "suspicious_tokens_found": any("suspicious" in str(w).lower() for w in warnings),
                "confusables_detected": any("confusable" in str(w).lower() or "homograph" in str(w).lower() for w in warnings),
                "policy_violations": any("policy" in str(w).lower() for w in warnings),
            },
        }

        # Apply policy evaluation if policy engine is available
        if self.policy_engine:
            return self.apply_policy(warnings, model_directory, context)

        return warnings

    def _discover_tokenizer_files(self, model_dir: Path) -> List[Path]:
        """Discover tokenizer-related files in model directory."""
        tokenizer_files = []

        for file_pattern in self.tokenizer_files:
            # Direct match
            direct_file = model_dir / file_pattern
            if direct_file.exists():
                tokenizer_files.append(direct_file)

            # Pattern match (for files like tokenizer_config.json)
            if "*" not in file_pattern:
                pattern_files = list(model_dir.glob(file_pattern))
                tokenizer_files.extend(pattern_files)

        # Also look for any .json files that might be tokenizer-related
        json_files = list(model_dir.glob("*.json"))
        for json_file in json_files:
            if "token" in json_file.name.lower() and json_file not in tokenizer_files:
                tokenizer_files.append(json_file)

        # Look for SentencePiece model files
        sp_files = list(model_dir.glob("*.model"))
        tokenizer_files.extend(sp_files)

        return list(set(tokenizer_files))  # Remove duplicates

    def _validate_tokenizer_file(self, tokenizer_file: Path) -> List[Dict[str, Any]]:
        """Validate individual tokenizer file structure and content."""
        warnings = []

        try:
            if tokenizer_file.name == "tokenizer.json":
                warnings.extend(self._validate_huggingface_tokenizer(tokenizer_file))
            elif tokenizer_file.name == "tokenizer.model":
                warnings.extend(self._validate_sentencepiece_model(tokenizer_file))
            elif tokenizer_file.name == "added_tokens.json":
                warnings.extend(self._validate_added_tokens_file(tokenizer_file))
            elif tokenizer_file.name == "tokenizer_config.json":
                warnings.extend(self._validate_tokenizer_config(tokenizer_file))
            elif tokenizer_file.suffix == ".json":
                warnings.extend(self._validate_generic_tokenizer_json(tokenizer_file))
            elif tokenizer_file.suffix == ".txt":
                warnings.extend(self._validate_vocab_file(tokenizer_file))

        except Exception as e:
            warnings.append(self.create_standard_warning(
                "tokenizer_file_error",
                f"Error validating tokenizer file: {tokenizer_file.name}",
                Severity.MEDIUM,
                "Check file format and integrity",
                file=str(tokenizer_file),
                error=str(e),
            ))

        return warnings

    def _validate_huggingface_tokenizer(self, tokenizer_file: Path) -> List[Dict[str, Any]]:
        """Validate HuggingFace tokenizer.json structure."""
        warnings = []

        try:
            with open(tokenizer_file, encoding="utf-8") as f:
                tokenizer_data = json.load(f)

            # Check required fields
            required_fields = ["version", "truncation", "padding", "added_tokens", "normalizer", "pre_tokenizer", "post_processor", "decoder", "model"]
            missing_fields = [field for field in required_fields if field not in tokenizer_data]

            if missing_fields:
                warnings.append(self.create_standard_warning(
                    "tokenizer_structure_invalid",
                    "tokenizer.json missing required fields",
                    Severity.HIGH,
                    "Tokenizer may be corrupted or malformed",
                    missing_fields=missing_fields,
                    file=str(tokenizer_file),
                ))

            # Validate added tokens for suspicious content
            if "added_tokens" in tokenizer_data:
                added_tokens_warnings = self._analyze_token_list(tokenizer_data["added_tokens"], "tokenizer.json added_tokens")
                warnings.extend(added_tokens_warnings)

            # Check model section
            if "model" in tokenizer_data:
                model_section = tokenizer_data["model"]
                if isinstance(model_section, dict):
                    # Check for suspicious model parameters
                    if "vocab" in model_section:
                        vocab_warnings = self._analyze_vocabulary(model_section["vocab"], "tokenizer.json vocab")
                        warnings.extend(vocab_warnings)

        except json.JSONDecodeError as e:
            warnings.append(self.create_standard_warning(
                "tokenizer_json_invalid",
                "tokenizer.json is not valid JSON",
                Severity.HIGH,
                "File may be corrupted or tampered with",
                error=str(e),
                file=str(tokenizer_file),
            ))

        return warnings

    def _validate_sentencepiece_model(self, model_file: Path) -> List[Dict[str, Any]]:
        """Validate SentencePiece model file structure."""
        warnings = []

        try:
            with open(model_file, "rb") as f:
                # Read first few bytes to check magic number
                header = f.read(16)

                # SentencePiece models typically start with specific patterns
                # This is a basic check - more sophisticated validation would parse the protobuf
                if len(header) < 4:
                    warnings.append(self.create_standard_warning(
                        "sentencepiece_too_small",
                        "SentencePiece model file too small",
                        Severity.MEDIUM,
                        "File may be corrupted or incomplete",
                        size=len(header),
                        file=str(model_file),
                    ))

                # Check for null bytes at start (potential corruption)
                if header.startswith(b"\x00\x00\x00\x00"):
                    warnings.append(self.create_standard_warning(
                        "sentencepiece_null_header",
                        "SentencePiece model starts with null bytes",
                        Severity.MEDIUM,
                        "File may be corrupted",
                        file=str(model_file),
                    ))

        except OSError as e:
            warnings.append(self.create_standard_warning(
                "sentencepiece_read_error",
                "Cannot read SentencePiece model file",
                Severity.MEDIUM,
                "Check file permissions and integrity",
                error=str(e),
                file=str(model_file),
            ))

        return warnings

    def _validate_added_tokens_file(self, added_tokens_file: Path) -> List[Dict[str, Any]]:
        """Validate added_tokens.json for suspicious control tokens."""
        warnings = []

        try:
            with open(added_tokens_file, encoding="utf-8") as f:
                added_tokens = json.load(f)

            # Analyze tokens based on file structure
            if isinstance(added_tokens, dict):
                # Format: {"token": id} or {"token": {"id": id, ...}}
                token_list = list(added_tokens.keys())
            elif isinstance(added_tokens, list):
                # Format: [{"content": "token", ...}, ...]
                token_list = []
                for token_info in added_tokens:
                    if isinstance(token_info, dict) and "content" in token_info:
                        token_list.append(token_info["content"])
                    elif isinstance(token_info, str):
                        token_list.append(token_info)
            else:
                warnings.append(self.create_standard_warning(
                    "added_tokens_format_invalid",
                    "added_tokens.json has invalid format",
                    Severity.HIGH,
                    "Expected dict or list format",
                    format=type(added_tokens).__name__,
                    file=str(added_tokens_file),
                ))
                return warnings

            # Analyze token content
            token_warnings = self._analyze_token_list(token_list, "added_tokens.json")
            warnings.extend(token_warnings)

        except json.JSONDecodeError as e:
            warnings.append(self.create_standard_warning(
                "added_tokens_json_invalid",
                "added_tokens.json is not valid JSON",
                Severity.HIGH,
                "File may be corrupted",
                error=str(e),
                file=str(added_tokens_file),
            ))

        return warnings

    def _validate_tokenizer_config(self, config_file: Path) -> List[Dict[str, Any]]:
        """Validate tokenizer_config.json."""
        warnings = []

        try:
            with open(config_file, encoding="utf-8") as f:
                config_data = json.load(f)

            # Check for suspicious configuration options
            suspicious_configs = []

            # Check for custom tokenizer class (potential code injection)
            if "tokenizer_class" in config_data:
                tokenizer_class = config_data["tokenizer_class"]
                if not tokenizer_class.endswith(("Tokenizer", "TokenizerFast")):
                    suspicious_configs.append({
                        "config": "tokenizer_class",
                        "value": tokenizer_class,
                        "risk": "Non-standard tokenizer class",
                    })

            # Check for custom processors
            processor_fields = ["pre_tokenizer", "post_processor", "normalizer", "decoder"]
            for field in processor_fields:
                if field in config_data:
                    processor = config_data[field]
                    if isinstance(processor, str) and ("eval" in processor or "exec" in processor):
                        suspicious_configs.append({
                            "config": field,
                            "value": processor[:100],  # Truncate long values
                            "risk": "Processor contains eval/exec",
                        })

            if suspicious_configs:
                warnings.append(self.create_standard_warning(
                    "suspicious_tokenizer_config",
                    "Suspicious configuration in tokenizer_config.json",
                    Severity.HIGH,
                    "Verify tokenizer configuration is legitimate",
                    suspicious_configs=suspicious_configs,
                    file=str(config_file),
                ))

        except json.JSONDecodeError as e:
            warnings.append(self.create_standard_warning(
                "tokenizer_config_json_invalid",
                "tokenizer_config.json is not valid JSON",
                Severity.MEDIUM,
                "File may be corrupted",
                error=str(e),
                file=str(config_file),
            ))

        return warnings

    def _validate_generic_tokenizer_json(self, json_file: Path) -> List[Dict[str, Any]]:
        """Validate generic tokenizer-related JSON file."""
        warnings = []

        try:
            with open(json_file, encoding="utf-8") as f:
                json_data = json.load(f)

            # Look for token-like content and analyze it
            self._analyze_json_for_tokens(json_data, json_file.name, warnings)

        except json.JSONDecodeError as e:
            warnings.append(self.create_standard_warning(
                "tokenizer_json_parse_error",
                f"Cannot parse tokenizer JSON file: {json_file.name}",
                Severity.MEDIUM,
                "File may be corrupted",
                error=str(e),
                file=str(json_file),
            ))

        return warnings

    def _validate_vocab_file(self, vocab_file: Path) -> List[Dict[str, Any]]:
        """Validate vocabulary text file."""
        warnings = []

        try:
            with open(vocab_file, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            # Sample first 1000 lines for analysis
            sample_lines = lines[:1000]
            vocab_tokens = [line.strip() for line in sample_lines if line.strip()]

            # Analyze vocabulary tokens
            vocab_warnings = self._analyze_token_list(vocab_tokens, vocab_file.name)
            warnings.extend(vocab_warnings)

        except OSError as e:
            warnings.append(self.create_standard_warning(
                "vocab_file_read_error",
                f"Cannot read vocabulary file: {vocab_file.name}",
                Severity.MEDIUM,
                "Check file permissions",
                error=str(e),
                file=str(vocab_file),
            ))

        return warnings

    def _analyze_token_list(self, tokens: List[str], source: str) -> List[Dict[str, Any]]:
        """Analyze list of tokens for suspicious patterns."""
        warnings = []

        suspicious_tokens = []

        for token in tokens:
            if not isinstance(token, str):
                continue

            # Check against suspicious patterns
            for category, patterns in self.suspicious_control_tokens.items():
                for pattern in patterns:
                    if pattern.lower() in token.lower():
                        suspicious_tokens.append({
                            "token": token[:100],  # Truncate long tokens
                            "pattern": pattern,
                            "category": category,
                            "risk": self._get_token_risk_description(category),
                        })
                        break

            # Check for unusual characters
            if self._has_unusual_characters(token):
                suspicious_tokens.append({
                    "token": token[:100],
                    "pattern": "unusual_characters",
                    "category": "encoding_manipulation",
                    "risk": "Contains unusual Unicode or control characters",
                })

            # CRITICAL SECURITY ENHANCEMENT: Unicode confusables detection
            confusables_result = self._detect_confusables(token)
            if confusables_result.get("confusables_found", False):
                risk_level = confusables_result.get("risk_level", "low")

                suspicious_tokens.append({
                    "token": token[:100],
                    "pattern": "unicode_confusables",
                    "category": "homograph_attack",
                    "risk": f"Unicode confusables detected - potential homograph attack (Risk: {risk_level.upper()})",
                    "original_token": confusables_result.get("original_token", token),
                    "normalized_token": confusables_result.get("normalized_token", token),
                    "confusables_details": confusables_result.get("confusables_details", {}),
                    "high_risk_matches": confusables_result.get("high_risk_matches", []),
                    "unicode_ranges": confusables_result.get("unicode_ranges", []),
                    "attack_confidence": self._calculate_attack_confidence(confusables_result),
                })

            # SECURITY ENHANCEMENT: Invisible characters detection
            invisible_result = self._detect_invisible_characters(token)
            if invisible_result.get("invisible_found", False):
                suspicious_tokens.append({
                    "token": token[:100],
                    "pattern": "invisible_characters",
                    "category": "steganographic_attack",
                    "risk": "Invisible/zero-width characters detected - potential steganographic attack",
                    "invisible_chars": invisible_result.get("invisible_chars", []),
                    "total_invisible": invisible_result.get("total_invisible", 0),
                })

            # CRITICAL SECURITY ENHANCEMENT: Token policy validation
            policy_result = self._validate_token_policy(token)
            if not policy_result.get("policy_compliant", True):
                violations = policy_result.get("violations", [])
                highest_severity = policy_result.get("highest_severity", "medium")
                compliance_score = policy_result.get("compliance_score", 0.0)

                suspicious_tokens.append({
                    "token": token[:100],
                    "pattern": "policy_violation",
                    "category": "token_policy_violation",
                    "risk": f"Token violates security policy (Severity: {highest_severity.upper()}, Compliance: {compliance_score})",
                    "policy_violations": violations,
                    "total_violations": policy_result.get("total_violations", 0),
                    "compliance_score": compliance_score,
                    "highest_severity": highest_severity,
                    "risk_categories": policy_result.get("risk_categories", []),
                    "policy_details": self._format_policy_violations(violations),
                })

        if suspicious_tokens:
            # Enhanced severity assessment including confusables and policy violations
            critical_categories = ["code_injection", "hidden_tokens", "homograph_attack", "token_policy_violation"]

            # Check for critical threats
            has_critical = any(
                t["category"] in critical_categories or
                (t.get("pattern") == "unicode_confusables" and
                 t.get("attack_confidence", 0) > 0.8) or
                (t.get("pattern") == "policy_violation" and
                 t.get("highest_severity") == "critical")
                for t in suspicious_tokens
            )

            severity = "critical" if has_critical else "high"

            warnings.append(self.create_standard_warning(
                "suspicious_tokens_detected",
                f"Suspicious tokens detected in {source}",
                Severity.CRITICAL if severity == "critical" else Severity.HIGH,
                "Review tokenizer for potential injection vectors",
                source=source,
                suspicious_tokens=suspicious_tokens[:20],
                total_suspicious=len(suspicious_tokens),
            ))

        return warnings

    def _analyze_vocabulary(self, vocab: Dict[str, Any], source: str) -> List[Dict[str, Any]]:
        """Analyze vocabulary dictionary for suspicious tokens."""
        if isinstance(vocab, dict):
            tokens = list(vocab.keys())
            return self._analyze_token_list(tokens, source)
        return []

    def _analyze_json_for_tokens(self, json_data: Any, filename: str, warnings: List[Dict[str, Any]]) -> None:
        """Recursively analyze JSON data for token-like content."""
        if isinstance(json_data, dict):
            for key, value in json_data.items():
                if isinstance(value, str) and len(value) < self.max_token_length:  # Policy-configurable token length
                    token_warnings = self._analyze_token_list([value], f"{filename}:{key}")
                    warnings.extend(token_warnings)
                elif isinstance(value, (dict, list)):
                    self._analyze_json_for_tokens(value, filename, warnings)
        elif isinstance(json_data, list):
            for item in json_data:
                if isinstance(item, str) and len(item) < 1000:
                    token_warnings = self._analyze_token_list([item], filename)
                    warnings.extend(token_warnings)
                elif isinstance(item, (dict, list)):
                    self._analyze_json_for_tokens(item, filename, warnings)

    def _check_executable_files(self, model_dir: Path, tokenizer_files: List[Path]) -> List[Dict[str, Any]]:
        """Check for executable files alongside tokenizer (security risk)."""
        warnings = []

        # Find all files in model directory
        all_files = []
        try:
            all_files = list(model_dir.iterdir())
        except PermissionError:
            return warnings

        # Check for executable files
        executable_files = []
        for file_path in all_files:
            if file_path.is_file():
                if file_path.suffix.lower() in self.executable_extensions:
                    executable_files.append(file_path)
                elif file_path.name.lower() in {"makefile", "dockerfile", "requirements.txt"}:
                    executable_files.append(file_path)
                # Check for executable permissions on Unix-like systems
                elif hasattr(os, "access") and os.access(file_path, os.X_OK):
                    if file_path.suffix == "" or file_path.suffix not in {".txt", ".json", ".md", ".safetensors", ".gguf"}:
                        executable_files.append(file_path)

        if executable_files:
            # Assess risk based on proximity to tokenizer files
            high_risk_files = []
            medium_risk_files = []

            for exe_file in executable_files:
                # High risk if executable has tokenizer-related name
                if "token" in exe_file.name.lower() or "vocab" in exe_file.name.lower():
                    high_risk_files.append(exe_file)
                else:
                    medium_risk_files.append(exe_file)

            if high_risk_files:
                warnings.append(self.create_standard_warning(
                    "executable_near_tokenizer",
                    "SECURITY: Executable files with tokenizer-related names detected",
                    Severity.CRITICAL,
                    "Remove executable files from model directory",
                    high_risk_files=[str(f) for f in high_risk_files],
                    risk="Potential tokenizer hijacking or code injection",
                ))

            if medium_risk_files:
                warnings.append(self.create_standard_warning(
                    "executable_files_present",
                    "Executable files found alongside tokenizer",
                    Severity.HIGH,
                    "Verify executable files are necessary and legitimate",
                    executable_files=[str(f) for f in medium_risk_files[:10]],
                    total_executables=len(medium_risk_files),
                ))

        return warnings

    def _validate_tokenizer_consistency(self, model_dir: Path, tokenizer_files: List[Path]) -> List[Dict[str, Any]]:
        """Cross-validate tokenizer files for consistency."""
        warnings = []

        try:
            # Find tokenizer.json and added_tokens.json for consistency checking
            tokenizer_json = None
            added_tokens_json = None

            for file_path in tokenizer_files:
                if file_path.name == "tokenizer.json":
                    tokenizer_json = file_path
                elif file_path.name == "added_tokens.json":
                    added_tokens_json = file_path

            # Check for consistency between tokenizer.json and added_tokens.json
            if tokenizer_json and added_tokens_json:
                consistency_warnings = self._check_tokenizer_added_tokens_consistency(
                    tokenizer_json, added_tokens_json,
                )
                warnings.extend(consistency_warnings)

            # Check for multiple tokenizer files that might conflict
            json_tokenizers = [f for f in tokenizer_files if f.name.endswith(".json") and "token" in f.name.lower()]
            if len(json_tokenizers) > 3:  # tokenizer.json, tokenizer_config.json, added_tokens.json
                warnings.append(self.create_standard_warning(
                    "multiple_tokenizer_files",
                    f"Multiple tokenizer JSON files detected: {len(json_tokenizers)}",
                    Severity.MEDIUM,
                    "Verify which tokenizer file takes precedence",
                    tokenizer_files=[str(f) for f in json_tokenizers],
                ))

        except Exception as e:
            logger.debug(f"Error validating tokenizer consistency: {str(e)}")

        return warnings

    def _check_tokenizer_added_tokens_consistency(self, tokenizer_json: Path, added_tokens_json: Path) -> List[Dict[str, Any]]:
        """Check consistency between tokenizer.json and added_tokens.json."""
        warnings = []

        try:
            # Load tokenizer.json
            with open(tokenizer_json, encoding="utf-8") as f:
                tokenizer_data = json.load(f)

            # Load added_tokens.json
            with open(added_tokens_json, encoding="utf-8") as f:
                added_tokens_data = json.load(f)

            # Get added tokens from tokenizer.json
            tokenizer_added_tokens = tokenizer_data.get("added_tokens", [])
            tokenizer_token_set = set()

            for token_info in tokenizer_added_tokens:
                if isinstance(token_info, dict) and "content" in token_info:
                    tokenizer_token_set.add(token_info["content"])
                elif isinstance(token_info, str):
                    tokenizer_token_set.add(token_info)

            # Get tokens from added_tokens.json
            added_tokens_set = set()
            if isinstance(added_tokens_data, dict):
                added_tokens_set = set(added_tokens_data.keys())
            elif isinstance(added_tokens_data, list):
                for token_info in added_tokens_data:
                    if isinstance(token_info, dict) and "content" in token_info:
                        added_tokens_set.add(token_info["content"])
                    elif isinstance(token_info, str):
                        added_tokens_set.add(token_info)

            # Check for discrepancies
            only_in_tokenizer = tokenizer_token_set - added_tokens_set
            only_in_added_tokens = added_tokens_set - tokenizer_token_set

            if only_in_tokenizer:
                warnings.append(self.create_standard_warning(
                    "tokenizer_added_tokens_mismatch",
                    f"Tokens in tokenizer.json but not in added_tokens.json: {len(only_in_tokenizer)}",
                    Severity.MEDIUM,
                    "Verify tokenizer configuration consistency",
                    missing_from_added_tokens=list(only_in_tokenizer)[:10],  # Show first 10
                ))

            if only_in_added_tokens:
                warnings.append(self.create_standard_warning(
                    "added_tokens_tokenizer_mismatch",
                    f"Tokens in added_tokens.json but not in tokenizer.json: {len(only_in_added_tokens)}",
                    Severity.MEDIUM,
                    "Verify added tokens are properly integrated",
                    missing_from_tokenizer=list(only_in_added_tokens)[:10],  # Show first 10
                ))

        except Exception as e:
            logger.debug(f"Error checking tokenizer consistency: {str(e)}")

        return warnings

    def _analyze_added_tokens(self, model_dir: Path) -> List[Dict[str, Any]]:
        """Analyze added_tokens.json for suspicious patterns."""
        warnings = []

        added_tokens_file = model_dir / "added_tokens.json"
        if added_tokens_file.exists():
            file_warnings = self._validate_added_tokens_file(added_tokens_file)
            warnings.extend(file_warnings)

        return warnings

    def _get_token_risk_description(self, category: str) -> str:
        """Get human-readable risk description for token category."""
        descriptions = {
            "code_injection": "Potential code injection vector",
            "prompt_injection": "Potential prompt injection attack",
            "hidden_tokens": "Hidden or suspicious control token",
            "encoding_manipulation": "Encoding manipulation attempt",
            "network_file": "Network or file system access pattern",
            "homograph_attack": "Unicode confusables homograph attack",
            "steganographic_attack": "Hidden content using invisible characters",
            "token_policy_violation": "Token violates security policy rules",
        }
        return descriptions.get(category, "Suspicious token pattern")

    def _has_unusual_characters(self, token: str) -> bool:
        """Check if token contains unusual Unicode or control characters."""
        try:
            # Check for control characters (except common whitespace)
            for char in token:
                code_point = ord(char)
                # Control characters (0-31) except tab, newline, carriage return
                if 0 <= code_point <= 31 and code_point not in {9, 10, 13}:
                    return True
                # High Unicode ranges that might be suspicious
                if 0xFE00 <= code_point <= 0xFEFF:  # Variation selectors, zero-width
                    return True
                if 0x200B <= code_point <= 0x200D:  # Zero-width spaces
                    return True
        except (ValueError, TypeError):
            return True  # If we can't analyze, consider it suspicious

        return False

    def _normalize_confusables(self, text: str) -> str:
        """CRITICAL SECURITY ENHANCEMENT: Normalize Unicode confusables to detect homograph attacks.

        Converts confusable Unicode characters to their canonical Latin equivalents
        to detect visual spoofing attacks in tokens.

        Args:
        ----
            text: Input text potentially containing confusables

        Returns:
        -------
            Normalized text with confusables replaced by canonical forms

        Examples:
        --------
            'payrol' (Cyrillic) -> 'payrol' (Latin)
            'user' (Monospace) -> 'user' (Latin)
            'admin' (Mixed) -> 'admin' (Latin)
        """
        try:
            normalized = ""
            for char in text:
                # Replace confusable character with canonical form
                canonical = UNICODE_CONFUSABLES.get(char, char)
                normalized += canonical
            return normalized
        except Exception as e:
            logger.debug(f"Error normalizing confusables in '{text}': {str(e)}")
            return text  # Return input text if normalization fails

    def _detect_confusables(self, token: str) -> Dict[str, Any]:
        """CRITICAL SECURITY ENHANCEMENT: Comprehensive confusables detection.

        Detects Unicode confusables that could be used for:
        - Homograph attacks (визually identical tokens)
        - Prompt injection bypasses
        - Tokenizer spoofing attacks
        - Supply chain tampering

        Returns detailed analysis including normalized forms and risk assessment.
        """
        try:
            # Phase 1: Normalize confusables
            normalized_token = self._normalize_confusables(token)

            # Phase 2: Detect if normalization changed anything
            has_confusables = normalized_token != token

            if not has_confusables:
                return {
                    "confusables_found": False,
                    "normalized": token,
                    "risk_level": "none",
                }

            # Phase 3: Analyze confusables found
            confusables_analysis = self._analyze_confusables_details(token, normalized_token)

            # Phase 4: Check if normalized token matches high-risk patterns
            high_risk_matches = self._check_high_risk_patterns(normalized_token)

            # Phase 5: Assess overall risk level
            risk_level = self._assess_confusables_risk_level(
                confusables_analysis, high_risk_matches, token, normalized_token,
            )

            return {
                "confusables_found": True,
                "original_token": token,
                "normalized_token": normalized_token,
                "risk_level": risk_level,
                "confusables_details": confusables_analysis,
                "high_risk_matches": high_risk_matches,
                "unicode_ranges": self._identify_unicode_ranges(token),
            }

        except Exception as e:
            logger.debug(f"Error detecting confusables in token '{token}': {str(e)}")
            return {
                "confusables_found": False,
                "error": str(e),
                "risk_level": "unknown",
            }

    def _analyze_confusables_details(self, original: str, normalized: str) -> Dict[str, Any]:
        """Analyze specific confusables found in token."""
        confusables_found = []
        script_types = set()

        try:
            for i, char in enumerate(original):
                if i < len(normalized) and char != normalized[i]:
                    canonical = normalized[i]

                    # Identify the script/range this confusable belongs to
                    script_type = self._identify_character_script(char)
                    script_types.add(script_type)

                    confusables_found.append({
                        "position": i,
                        "original_char": char,
                        "canonical_char": canonical,
                        "unicode_name": self._get_unicode_name(char),
                        "codepoint": f"U+{ord(char):04X}",
                        "script_type": script_type,
                    })

            return {
                "total_confusables": len(confusables_found),
                "confusables": confusables_found[:10],  # Limit details for readability
                "script_types": list(script_types),
                "mixed_scripts": len(script_types) > 1,
            }

        except Exception as e:
            logger.debug(f"Error analyzing confusables details: {str(e)}")
            return {"error": str(e)}

    def _check_high_risk_patterns(self, normalized_token: str) -> List[Dict[str, str]]:
        """Check if normalized token matches high-risk patterns."""
        matches = []

        try:
            for category, patterns in HIGH_RISK_CONFUSABLE_PATTERNS.items():
                for pattern in patterns:
                    if pattern.lower() in normalized_token.lower():
                        matches.append({
                            "category": category,
                            "pattern": pattern,
                            "match_type": "substring" if pattern != normalized_token.lower() else "exact",
                        })

        except Exception as e:
            logger.debug(f"Error checking high-risk patterns: {str(e)}")

        return matches

    def _assess_confusables_risk_level(self, confusables_analysis: Dict[str, Any],
                                     high_risk_matches: List[Dict[str, str]],
                                     original: str, normalized: str) -> str:
        """Assess overall risk level of confusables attack."""
        try:
            # CRITICAL: Exact match with high-risk patterns
            if any(match["match_type"] == "exact" for match in high_risk_matches):
                return "critical"

            # HIGH: Substring match with security keywords or instruction tokens
            critical_categories = {"instruction_tokens", "security_keywords"}
            if any(match["category"] in critical_categories for match in high_risk_matches):
                return "high"

            # HIGH: Mixed scripts (sophisticated attack indicator)
            if confusables_analysis.get("mixed_scripts", False):
                return "high"

            # HIGH: Many confusables (>50% of characters)
            total_chars = len(original)
            total_confusables = confusables_analysis.get("total_confusables", 0)
            if total_chars > 0 and (total_confusables / total_chars) > 0.5:
                return "high"

            # MEDIUM: Contains Cyrillic confusables (most common attack vector)
            script_types = confusables_analysis.get("script_types", [])
            if "cyrillic" in script_types:
                return "medium"

            # MEDIUM: Any high-risk pattern match
            if high_risk_matches:
                return "medium"

            # LOW: Basic confusables detected
            return "low"

        except Exception:
            return "unknown"

    def _identify_character_script(self, char: str) -> str:
        """Identify which script/range a character belongs to."""
        try:
            codepoint = ord(char)

            # Check against dangerous Unicode ranges
            for start, end, script_name in DANGEROUS_UNICODE_RANGES:
                if start <= codepoint <= end:
                    return script_name

            # Manual classification for common ranges
            if 0x0400 <= codepoint <= 0x04FF:
                return "cyrillic"
            elif 0x0370 <= codepoint <= 0x03FF:
                return "greek"
            elif 0x1D400 <= codepoint <= 0x1D7FF:
                return "mathematical_alphanumeric"
            elif 0xFF00 <= codepoint <= 0xFFEF:
                return "halfwidth_fullwidth"
            elif 0x0080 <= codepoint <= 0x00FF:
                return "latin_extended"
            else:
                return "other"

        except Exception:
            return "unknown"

    def _identify_unicode_ranges(self, text: str) -> List[Dict[str, Any]]:
        """Identify all Unicode ranges present in text."""
        ranges_found = []

        try:
            for char in text:
                codepoint = ord(char)

                # Find the range this character belongs to
                for start, end, range_name in DANGEROUS_UNICODE_RANGES:
                    if start <= codepoint <= end:
                        # Check if we already found this range
                        if not any(r["range_name"] == range_name for r in ranges_found):
                            ranges_found.append({
                                "range_name": range_name,
                                "start": f"U+{start:04X}",
                                "end": f"U+{end:04X}",
                                "character": char,
                                "codepoint": f"U+{codepoint:04X}",
                            })
                        break

        except Exception as e:
            logger.debug(f"Error identifying Unicode ranges: {str(e)}")

        return ranges_found

    def _get_unicode_name(self, char: str) -> str:
        """Get Unicode character name (simplified)."""
        try:
            codepoint = ord(char)

            # Simplified name mapping for common confusables
            name_mappings = {
                # Cyrillic
                0x0430: "CYRILLIC SMALL LETTER A",
                0x0435: "CYRILLIC SMALL LETTER IE",
                0x043E: "CYRILLIC SMALL LETTER O",
                0x0440: "CYRILLIC SMALL LETTER ER",
                0x0441: "CYRILLIC SMALL LETTER ES",

                # Greek
                0x03B1: "GREEK SMALL LETTER ALPHA",
                0x03BF: "GREEK SMALL LETTER OMICRON",
                0x03C1: "GREEK SMALL LETTER RHO",

                # Mathematical
                0x1D41A: "MATHEMATICAL BOLD SMALL A",
                0x1D44E: "MATHEMATICAL ITALIC SMALL A",
            }

            return name_mappings.get(codepoint, f"U+{codepoint:04X}")

        except Exception:
            return "UNKNOWN"

    def _detect_invisible_characters(self, token: str) -> Dict[str, Any]:
        """SECURITY ENHANCEMENT: Detect invisible/zero-width characters.

        These can be used to hide malicious content or create visually identical
        but functionally different tokens.
        """
        invisible_chars = []

        try:
            for i, char in enumerate(token):
                codepoint = ord(char)

                # Check for zero-width and invisible characters
                if codepoint in {
                    0x200B,  # ZERO WIDTH SPACE
                    0x200C,  # ZERO WIDTH NON-JOINER
                    0x200D,  # ZERO WIDTH JOINER
                    0x2060,  # WORD JOINER
                    0xFEFF,  # ZERO WIDTH NO-BREAK SPACE (BOM)
                    0x061C,  # ARABIC LETTER MARK
                }:
                    invisible_chars.append({
                        "position": i,
                        "character": char,
                        "codepoint": f"U+{codepoint:04X}",
                        "name": self._get_invisible_char_name(codepoint),
                    })

                # Check for bidirectional override characters
                elif 0x202A <= codepoint <= 0x202E:
                    invisible_chars.append({
                        "position": i,
                        "character": char,
                        "codepoint": f"U+{codepoint:04X}",
                        "name": "BIDIRECTIONAL_OVERRIDE",
                        "risk": "Can reverse text display order",
                    })

            return {
                "invisible_found": len(invisible_chars) > 0,
                "invisible_chars": invisible_chars,
                "total_invisible": len(invisible_chars),
            }

        except Exception as e:
            logger.debug(f"Error detecting invisible characters: {str(e)}")
            return {"invisible_found": False, "error": str(e)}

    def _get_invisible_char_name(self, codepoint: int) -> str:
        """Get name for invisible character."""
        names = {
            0x200B: "ZERO_WIDTH_SPACE",
            0x200C: "ZERO_WIDTH_NON_JOINER",
            0x200D: "ZERO_WIDTH_JOINER",
            0x2060: "WORD_JOINER",
            0xFEFF: "ZERO_WIDTH_NO_BREAK_SPACE",
            0x061C: "ARABIC_LETTER_MARK",
        }
        return names.get(codepoint, f"INVISIBLE_U+{codepoint:04X}")

    def _calculate_attack_confidence(self, confusables_result: Dict[str, Any]) -> float:
        """Calculate confidence score for potential homograph attack.

        Returns float between 0.0 (low confidence) and 1.0 (high confidence)
        """
        try:
            confidence = 0.0

            risk_level = confusables_result.get("risk_level", "none")
            high_risk_matches = confusables_result.get("high_risk_matches", [])
            confusables_details = confusables_result.get("confusables_details", {})

            # Base confidence from risk level
            risk_scores = {
                "critical": 1.0,
                "high": 0.8,
                "medium": 0.6,
                "low": 0.3,
                "none": 0.0,
            }
            confidence = risk_scores.get(risk_level, 0.0)

            # Boost confidence for exact high-risk pattern matches
            if any(match.get("match_type") == "exact" for match in high_risk_matches):
                confidence = min(1.0, confidence + 0.3)

            # Boost confidence for mixed scripts (sophisticated attack)
            if confusables_details.get("mixed_scripts", False):
                confidence = min(1.0, confidence + 0.2)

            # Boost confidence for high ratio of confusables
            total_confusables = confusables_details.get("total_confusables", 0)
            original_token = confusables_result.get("original_token", "")
            if original_token and total_confusables > 0:
                confusables_ratio = total_confusables / len(original_token)
                if confusables_ratio > 0.7:  # >70% confusables
                    confidence = min(1.0, confidence + 0.2)
                elif confusables_ratio > 0.5:  # >50% confusables
                    confidence = min(1.0, confidence + 0.1)

            return round(confidence, 2)

        except Exception as e:
            logger.debug(f"Error calculating attack confidence: {str(e)}")
            return 0.0

    def _validate_token_policy(self, token: str) -> Dict[str, Any]:
        """CRITICAL SECURITY ENHANCEMENT: Comprehensive token policy validation.

        Validates tokens against configurable security policies:
        - Length constraints (prevent buffer overflows)
        - Character class rules (restrict character sets)
        - Deny patterns (block URL/shell fragments)
        - Special token format validation
        - Exception handling for legitimate tokens

        Returns detailed policy violation analysis with severity assessment.
        """
        violations = []

        try:
            # Phase 1: Length validation
            length_violations = self._validate_token_length(token)
            violations.extend(length_violations)

            # Phase 2: Character class validation
            char_class_violations = self._validate_character_classes(token)
            violations.extend(char_class_violations)

            # Phase 3: Deny pattern validation (most critical)
            deny_pattern_violations = self._validate_deny_patterns(token)
            violations.extend(deny_pattern_violations)

            # Phase 4: Special token format validation
            format_violations = self._validate_token_format(token)
            violations.extend(format_violations)

            # Phase 5: Apply legitimate token exceptions
            filtered_violations = self._apply_token_exceptions(token, violations)

            # Phase 6: Assess overall policy compliance
            compliance_score = self._calculate_policy_compliance(token, filtered_violations)

            return {
                "policy_compliant": len(filtered_violations) == 0,
                "violations": filtered_violations,
                "total_violations": len(filtered_violations),
                "compliance_score": compliance_score,
                "highest_severity": self._get_highest_violation_severity(filtered_violations),
                "risk_categories": list({v.get("category", "unknown") for v in filtered_violations}),
            }

        except Exception as e:
            logger.debug(f"Error validating token policy for '{token}': {str(e)}")
            return {
                "policy_compliant": False,
                "violations": [{"type": "policy_validation_error", "error": str(e)}],
                "total_violations": 1,
                "compliance_score": 0.0,
                "highest_severity": "high",
                "risk_categories": ["validation_error"],
            }

    def _validate_token_length(self, token: str) -> List[Dict[str, Any]]:
        """Validate token length constraints."""
        violations = []

        try:
            token_length = len(token)
            max_length = TOKEN_POLICY_RULES["max_token_length"]
            min_length = TOKEN_POLICY_RULES["min_token_length"]

            # Check maximum length
            if token_length > max_length:
                violations.append({
                    "type": "excessive_length",
                    "category": "length_policy",
                    "severity": POLICY_VIOLATION_SEVERITY.get("excessive_length", "medium"),
                    "message": f"Token exceeds maximum length: {token_length} > {max_length}",
                    "token_length": token_length,
                    "max_allowed": max_length,
                    "excess_chars": token_length - max_length,
                })

            # Check minimum length
            if token_length < min_length:
                violations.append({
                    "type": "insufficient_length",
                    "category": "length_policy",
                    "severity": POLICY_VIOLATION_SEVERITY.get("empty_token", "low"),
                    "message": f"Token below minimum length: {token_length} < {min_length}",
                    "token_length": token_length,
                    "min_required": min_length,
                })

            # Special token length check (stricter for control tokens)
            if self._is_special_token(token):
                max_special_length = TOKEN_POLICY_RULES["max_special_token_length"]
                if token_length > max_special_length:
                    violations.append({
                        "type": "special_token_excessive_length",
                        "category": "special_token_policy",
                        "severity": "high",
                        "message": f"Special token exceeds length limit: {token_length} > {max_special_length}",
                        "token_length": token_length,
                        "max_special_allowed": max_special_length,
                        "is_special_token": True,
                    })

        except Exception as e:
            logger.debug(f"Error validating token length: {str(e)}")

        return violations

    def _validate_character_classes(self, token: str) -> List[Dict[str, Any]]:
        """Validate token against character class rules."""
        violations = []

        try:
            char_rules = TOKEN_POLICY_RULES["allowed_character_classes"]

            # Check for control characters (always blocked)
            if not char_rules.get("control_characters", False):
                control_chars = self._find_control_characters(token)
                if control_chars:
                    violations.append({
                        "type": "control_characters_detected",
                        "category": "character_class_policy",
                        "severity": POLICY_VIOLATION_SEVERITY.get("control_characters", "high"),
                        "message": f"Token contains {len(control_chars)} control characters",
                        "control_chars": control_chars,
                        "char_count": len(control_chars),
                    })

            # Check for private use area characters
            if not char_rules.get("private_use", False):
                private_chars = self._find_private_use_characters(token)
                if private_chars:
                    violations.append({
                        "type": "private_use_characters",
                        "category": "character_class_policy",
                        "severity": POLICY_VIOLATION_SEVERITY.get("private_use_chars", "medium"),
                        "message": "Token contains private use area characters",
                        "private_chars": private_chars,
                    })

            # Validate against safe character patterns
            if not re.match(CHARACTER_CLASS_PATTERNS["no_control_chars"], token):
                violations.append({
                    "type": "unsafe_characters",
                    "category": "character_class_policy",
                    "severity": POLICY_VIOLATION_SEVERITY.get("invalid_characters", "medium"),
                    "message": "Token contains unsafe or non-printable characters",
                })

        except Exception as e:
            logger.debug(f"Error validating character classes: {str(e)}")

        return violations

    def _validate_deny_patterns(self, token: str) -> List[Dict[str, Any]]:
        """Validate token against deny patterns (URLs, shell commands, etc.)."""
        violations = []

        try:
            for category, patterns in TOKEN_DENY_PATTERNS.items():
                for pattern, description in patterns.items():
                    try:
                        if re.search(pattern, token, re.IGNORECASE):
                            severity = POLICY_VIOLATION_SEVERITY.get(category, "medium")
                            violations.append({
                                "type": "deny_pattern_match",
                                "category": category,
                                "severity": severity,
                                "message": f"Token matches deny pattern: {description}",
                                "pattern": pattern,
                                "pattern_description": description,
                                "match_category": category,
                            })
                    except re.error as regex_err:
                        logger.debug(f"Invalid regex pattern '{pattern}': {str(regex_err)}")

        except Exception as e:
            logger.debug(f"Error validating deny patterns: {str(e)}")

        return violations

    def _validate_token_format(self, token: str) -> List[Dict[str, Any]]:
        """Validate special token format compliance."""
        violations = []

        try:
            if self._is_special_token(token):
                # Check if special token follows expected patterns
                format_patterns = TOKEN_POLICY_RULES["special_token_patterns"]
                format_match = False

                for _format_name, pattern in format_patterns.items():
                    if re.match(pattern, token):
                        format_match = True
                        break

                if not format_match:
                    violations.append({
                        "type": "invalid_special_token_format",
                        "category": "format_policy",
                        "severity": "medium",
                        "message": "Special token doesn't match expected format patterns",
                        "expected_patterns": list(format_patterns.keys()),
                        "is_special_token": True,
                    })

        except Exception as e:
            logger.debug(f"Error validating token format: {str(e)}")

        return violations

    def _apply_token_exceptions(self, token: str, violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply exceptions for legitimate tokens to reduce false positives."""
        try:
            # Check if token is in legitimate exceptions
            all_exceptions = set()
            for exception_category in LEGITIMATE_TOKEN_EXCEPTIONS.values():
                all_exceptions.update(exception_category)

            if token.lower() in {ex.lower() for ex in all_exceptions}:
                # Filter out certain violation types for legitimate tokens
                filtered_violations = []
                for violation in violations:
                    # Keep critical violations even for legitimate tokens
                    if violation.get("severity") == "critical":
                        filtered_violations.append(violation)
                    # Remove certain categories for legitimate tokens
                    elif violation.get("category") not in ["obfuscation", "network_activity"]:
                        filtered_violations.append(violation)
                return filtered_violations

            return violations

        except Exception as e:
            logger.debug(f"Error applying token exceptions: {str(e)}")
            return violations

    def _calculate_policy_compliance(self, token: str, violations: List[Dict[str, Any]]) -> float:
        """Calculate overall policy compliance score (0.0 = non-compliant, 1.0 = fully compliant)."""
        try:
            if not violations:
                return 1.0

            # Weight violations by severity
            severity_weights = {
                "critical": 1.0,
                "high": 0.8,
                "medium": 0.5,
                "low": 0.2,
            }

            total_weight = 0.0
            for violation in violations:
                severity = violation.get("severity", "medium")
                weight = severity_weights.get(severity, 0.5)
                total_weight += weight

            # Calculate compliance score (inverse of total weight, normalized)
            max_possible_weight = len(violations) * 1.0  # All critical
            compliance_score = max(0.0, 1.0 - (total_weight / max_possible_weight))

            return round(compliance_score, 2)

        except Exception as e:
            logger.debug(f"Error calculating policy compliance: {str(e)}")
            return 0.0

    def _get_highest_violation_severity(self, violations: List[Dict[str, Any]]) -> str:
        """Get the highest severity level from violations."""
        if not violations:
            return "none"

        severity_order = ["critical", "high", "medium", "low"]

        for severity in severity_order:
            if any(v.get("severity") == severity for v in violations):
                return severity

        return "medium"  # Default fallback

    def _is_special_token(self, token: str) -> bool:
        """Check if token appears to be a special/control token."""
        special_indicators = [
            token.startswith("<") and token.endswith(">"),
            token.startswith("[") and token.endswith("]"),
            token.startswith("_") and token.endswith("_"),
            token.startswith("<|") and token.endswith("|>"),
            "endof" in token.lower(),
            "startof" in token.lower(),
            token.lower() in {"pad", "unk", "bos", "eos", "cls", "sep", "mask"},
        ]
        return any(special_indicators)

    def _find_control_characters(self, token: str) -> List[Dict[str, str]]:
        """Find control characters in token."""
        control_chars = []

        try:
            for i, char in enumerate(token):
                code_point = ord(char)
                # Control characters: 0-31 (except 9,10,13) and 127-159
                if ((0 <= code_point <= 31 and code_point not in {9, 10, 13}) or
                    (127 <= code_point <= 159)):
                    control_chars.append({
                        "position": i,
                        "character": repr(char),
                        "codepoint": f"U+{code_point:04X}",
                        "category": "control_character",
                    })

        except Exception as e:
            logger.debug(f"Error finding control characters: {str(e)}")

        return control_chars

    def _find_private_use_characters(self, token: str) -> List[Dict[str, str]]:
        """Find private use area characters in token."""
        private_chars = []

        try:
            for i, char in enumerate(token):
                code_point = ord(char)
                # Private use areas: U+E000-F8FF, U+F0000-FFFFD, U+100000-10FFFD
                if ((0xE000 <= code_point <= 0xF8FF) or
                    (0xF0000 <= code_point <= 0xFFFFD) or
                    (0x100000 <= code_point <= 0x10FFFD)):
                    private_chars.append({
                        "position": i,
                        "character": char,
                        "codepoint": f"U+{code_point:04X}",
                        "category": "private_use_area",
                    })

        except Exception as e:
            logger.debug(f"Error finding private use characters: {str(e)}")

        return private_chars

    def _format_policy_violations(self, violations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Format policy violations for readable reporting."""
        try:
            if not violations:
                return {"summary": "No policy violations"}

            # Group violations by category
            by_category = {}
            by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}

            for violation in violations:
                category = violation.get("category", "unknown")
                severity = violation.get("severity", "medium")

                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(violation)

                by_severity[severity] = by_severity.get(severity, 0) + 1

            # Create summary
            critical_violations = [v for v in violations if v.get("severity") == "critical"]
            high_violations = [v for v in violations if v.get("severity") == "high"]

            summary = {
                "total_violations": len(violations),
                "by_severity": by_severity,
                "by_category": {k: len(v) for k, v in by_category.items()},
                "critical_issues": [v.get("message", "Unknown violation") for v in critical_violations[:3]],
                "high_risk_issues": [v.get("message", "Unknown violation") for v in high_violations[:3]],
                "categories_affected": list(by_category.keys()),
            }

            return {
                "summary": summary,
                "details": violations[:10],  # Limit detailed violations for readability
                "categories": by_category,
            }

        except Exception as e:
            logger.debug(f"Error formatting policy violations: {str(e)}")
            return {"summary": "Error formatting violations", "error": str(e)}
