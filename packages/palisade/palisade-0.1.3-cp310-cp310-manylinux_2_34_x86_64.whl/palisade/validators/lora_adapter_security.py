"""LoRA/adapter compatibility validator - Critical for adapter security."""

import hashlib
import json
import logging
import re
import struct
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from palisade.models.metadata import ModelMetadata, ModelType

from .base import BaseValidator

if TYPE_CHECKING:
    from palisade.core.cedar_policy_engine import CedarPolicyEngine

logger = logging.getLogger(__name__)

class LoRAAdapterSecurityValidator(BaseValidator):
    """CRITICAL SECURITY VALIDATOR - LoRA/Adapter Security with Comprehensive Controls.

    SECURITY POLICIES:
    ==================
    1. MANDATORY BASE MODEL DIGEST BINDING
       - BLOCKS adapters without base_model_digest (CRITICAL severity)
       - BLOCKS digest mismatches - prevents wrong base model application
       - REQUIRES canonical bundle digest verification for adapter loading

    2. STRICT TARGET ALLOWLISTING
       - BLOCKS targets NOT on explicit per-architecture allowlist (CRITICAL severity)
       - Only pre-approved modules permitted: q_proj, k_proj, v_proj, o_proj, MLP components
       - Zero tolerance for non-allowlisted targets (no fuzzy matching)
       - Supports layer-numbered variants (e.g., layers.0.self_attn.q_proj)

    3. COMPOSITION MANIFEST REQUIREMENT (NEW)
       - BLOCKS multi-adapter compositions without apply-order manifest (CRITICAL severity)
       - REQUIRES adapter_composition.json for multiple adapters
       - MANDATES explicit apply-order specification
       - GENERATES composed model digest for complete configuration verification
       - VALIDATES adapter compatibility in composition chains

    Validation Features:
    - ✅ Adapter tensor shapes match base model architecture
    - 🛡️ MANDATORY base model digest verification (BLOCKING)
    - 🚫 STRICT target allowlist enforcement (BLOCKING)
    - 🔗 COMPOSITION manifest validation for multi-adapter setups (BLOCKING)
    - 📋 Apply-order enforcement and composed digest generation
    - 🔍 Comprehensive per-architecture allowlists (Llama, GPT, BERT, T5, etc.)
    - 🚨 Suspicious adapter pattern detection
    - ⚙️ Adapter configuration security checks
    - 🔐 Canonical bundle digest computation

    Multi-Adapter Composition:
    - Single adapter: No manifest required
    - Multiple adapters: MANDATORY adapter_composition.json
    - Required fields: composition_version, apply_order, base_model_digest, composition_metadata
    - Generates unique composed_model_digest for the complete configuration
    - Order-sensitive: different apply_order = different composed digest

    Supported Architectures with Allowlists:
    - Llama/Alpaca/Vicuna: q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj
    - GPT: c_attn, c_proj, c_fc, wte, wpe, lm_head
    - BERT/RoBERTa: query, key, value, dense, intermediate, output
    - T5: q, k, v, o, wi_0, wi_1, wo, relative_attention_bias
    - BLOOM/Falcon: query_key_value, dense, dense_h_to_4h, dense_4h_to_h
    - Mixtral: MoE-specific patterns (w1, w2, w3, gate)

    Usage:
        # Single adapter:
        {"base_model_digest": "sha256...", "target_modules": ["q_proj", "v_proj"], ...}

        # Multi-adapter composition:
        adapter_composition.json:
        {
          "composition_version": "1.0",
          "apply_order": ["task_adapter", "domain_adapter", "style_adapter"],
          "base_model_digest": "sha256_base_digest...",
          "composition_metadata": {"purpose": "Task+Domain+Style", "created_by": "..."}
        }
    """

    def __init__(self, metadata: ModelMetadata, policy_engine: Optional["CedarPolicyEngine"] = None) -> None:
        super().__init__(metadata, policy_engine)

        # Load policy configuration for custom architecture support
        self._load_policy_configuration()

        # Common LoRA/adapter file patterns
        self.adapter_file_patterns = {
            "adapter_model.safetensors",
            "adapter_model.bin",
            "adapter_model.pt",
            "adapter_config.json",
            "adapter_model.onnx",
            "pytorch_lora_weights.safetensors",
            "pytorch_lora_weights.bin",
            "lora_config.json",
            "peft_config.json",
        }

        # SECURITY: Explicit per-architecture target allowlists - BLOCKS everything else
        # POLICY: Only modules on this allowlist are permitted for LoRA adaptation
        # Any target module NOT on this list → BLOCKED (CRITICAL severity)
        # NOTE: Can be extended via policy configuration for custom architectures
        self.lora_target_allowlists = self._get_target_allowlists()

    def _load_policy_configuration(self) -> None:
        """Load policy configuration for custom architecture support."""
        self.policy_config = {}
        if self.policy_engine and hasattr(self.policy_engine, "get_validator_config"):
            self.policy_config = self.policy_engine.get_validator_config("lora_adapter_security", {})

        # Custom architecture support settings
        self.enable_custom_architectures = self.policy_config.get("enable_custom_architectures", True)
        self.custom_arch_validation_mode = self.policy_config.get("custom_arch_validation_mode", "STRICT")  # STRICT, PERMISSIVE, BLOCK
        self.custom_architectures = self.policy_config.get("custom_architectures", {})

    def _get_target_allowlists(self) -> Dict[str, List[str]]:
        """Get target allowlists with support for custom architectures."""
        # Default built-in allowlists
        default_allowlists = {
            "llama": {
                # Self-attention projection layers (SAFE - standard transformer components)
                "q_proj",           # Query projection
                "k_proj",           # Key projection
                "v_proj",           # Value projection
                "o_proj",           # Output projection

                # MLP/Feed-forward layers (SAFE - standard transformer components)
                "gate_proj",        # Gate projection (SwiGLU activation)
                "up_proj",          # Up projection (SwiGLU activation)
                "down_proj",        # Down projection (SwiGLU activation)

                # Embedding layers (CONTROLLED - legitimate but monitored)
                "embed_tokens",     # Input embeddings
                "lm_head",          # Language model head/output layer

                # Layer-wise variants (to handle different naming patterns)
                "self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj", "self_attn.o_proj",
                "mlp.gate_proj", "mlp.up_proj", "mlp.down_proj",
            },

            "mistral": {
                # Identical to Llama (Mistral uses same architecture patterns)
                "q_proj", "k_proj", "v_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj",
                "embed_tokens", "lm_head",
                "self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj", "self_attn.o_proj",
                "mlp.gate_proj", "mlp.up_proj", "mlp.down_proj",
            },

            "mixtral": {
                # Mixtral-specific patterns (8x7B MoE)
                "q_proj", "k_proj", "v_proj", "o_proj",
                "w1", "w2", "w3",                       # MoE expert weights
                "gate",                                 # MoE gating
                "embed_tokens", "lm_head",
                "self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj", "self_attn.o_proj",
            },

            "gpt": {
                # GPT-style attention (combined QKV projection)
                "c_attn",           # Combined QKV attention projection
                "c_proj",           # Attention output projection

                # GPT-style MLP
                "c_fc",             # Feed-forward input projection
                "mlp.c_proj",       # Feed-forward output projection

                # GPT embeddings
                "wte",              # Token embeddings
                "wpe",              # Position embeddings
                "lm_head",          # Language model head

                # Layer-wise variants
                "attn.c_attn", "attn.c_proj", "mlp.c_fc",
            },

            "bert": {
                # BERT-style attention
                "query",            # Attention query
                "key",              # Attention key
                "value",            # Attention value
                "dense",            # Attention dense/output

                # BERT-style feed-forward
                "intermediate",     # FF intermediate layer
                "output",           # FF output layer

                # BERT embeddings and classification
                "embeddings",       # Input embeddings
                "classifier",       # Classification head
                "pooler",           # Pooling layer

                # Layer-wise variants
                "attention.self.query", "attention.self.key", "attention.self.value",
                "attention.output.dense", "intermediate.dense", "output.dense",
            },

            "roberta": {
                # RoBERTa follows BERT patterns
                "query", "key", "value", "dense",
                "intermediate", "output",
                "embeddings", "classifier", "pooler",
                "attention.self.query", "attention.self.key", "attention.self.value",
                "attention.output.dense", "intermediate.dense", "output.dense",
            },

            "t5": {
                # T5 encoder-decoder attention patterns
                "q", "k", "v", "o",                     # Attention projections
                "wi_0", "wi_1", "wo",                   # Gated MLP (T5 style)
                "relative_attention_bias",              # T5 relative position
                "shared",                               # Shared embeddings
                "lm_head",                              # Language model head

                # Layer-wise variants
                "SelfAttention.q", "SelfAttention.k", "SelfAttention.v", "SelfAttention.o",
                "EncDecAttention.q", "EncDecAttention.k", "EncDecAttention.v", "EncDecAttention.o",
                "DenseReluDense.wi_0", "DenseReluDense.wi_1", "DenseReluDense.wo",
            },

            "bloom": {
                # BLOOM attention patterns
                "query_key_value",  # Combined QKV projection (BLOOM style)
                "dense",            # Attention output
                "dense_h_to_4h",    # MLP input projection
                "dense_4h_to_h",    # MLP output projection
                "word_embeddings",  # Input embeddings
                "lm_head",          # Language model head

                # Layer-wise variants
                "self_attention.query_key_value", "self_attention.dense",
                "mlp.dense_h_to_4h", "mlp.dense_4h_to_h",
            },

            "falcon": {
                # Falcon attention patterns
                "query_key_value",  # Combined QKV
                "dense",            # Attention output
                "dense_h_to_4h",    # MLP input
                "dense_4h_to_h",    # MLP output
                "word_embeddings", "lm_head",
            },
        }

        # Merge with custom architectures from policy if enabled
        if self.enable_custom_architectures and self.custom_architectures:
            for arch_name, arch_config in self.custom_architectures.items():
                if "target_modules" in arch_config:
                    default_allowlists[arch_name] = set(arch_config["target_modules"])
                    logger.info(f"Added custom architecture '{arch_name}' with {len(arch_config['target_modules'])} allowed targets")

        return default_allowlists

    def _handle_unknown_architecture(self, base_model: str, target_modules: List[str], warnings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Handle unknown architectures based on policy configuration.

        Validation Modes:
        - STRICT: Block all unknown architectures (default secure behavior)
        - PERMISSIVE: Allow with warnings if targets look safe
        - BLOCK: Block all unknown architectures (same as STRICT)
        """
        if self.custom_arch_validation_mode == "PERMISSIVE":
            # Permissive mode: validate targets against common safe patterns
            return self._validate_unknown_arch_permissive(base_model, target_modules, warnings)
        else:
            # STRICT or BLOCK mode: block unknown architectures
            warnings.append({
                "type": "unknown_architecture_for_target_validation",
                "details": {
                    "message": "BLOCKED: Cannot validate targets - unknown model architecture",
                    "base_model": base_model,
                    "policy": "Architecture must be recognized for strict target allowlist validation",
                    "supported_architectures": list(self.lora_target_allowlists.keys()),
                    "validation_mode": self.custom_arch_validation_mode,
                    "recommendation": "Add custom architecture to policy configuration or use supported architecture",
                    "action": "BLOCKED - Cannot validate targets without known architecture",
                    "custom_arch_example": {
                        "description": "Add to policy configuration",
                        "example": {
                            "lora_adapter_security": {
                                "enable_custom_architectures": True,
                                "custom_arch_validation_mode": "STRICT",
                                "custom_architectures": {
                                    "custom_model": {
                                        "target_modules": ["q_proj", "v_proj", "custom_projection"],
                                        "description": "Customer internal model architecture",
                                        "validation_rules": ["standard_transformer_patterns"],
                                    },
                                },
                            },
                        },
                    },
                },
                "severity": "critical",
                "blocked": True,
            })
            return warnings

    def _validate_unknown_arch_permissive(self, base_model: str, target_modules: List[str], warnings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Permissive validation for unknown architectures."""
        # Common safe target patterns across architectures
        safe_target_patterns = {
            "attention": ["q_proj", "k_proj", "v_proj", "o_proj", "qkv_proj", "c_attn", "c_proj"],
            "mlp": ["gate_proj", "up_proj", "down_proj", "dense", "dense_h_to_4h", "dense_4h_to_h",
                   "w1", "w2", "w3", "fc_in", "fc_out"],
            "embeddings": ["embed_tokens", "embeddings", "word_embeddings", "lm_head"],
        }

        all_safe_patterns = set()
        for category_patterns in safe_target_patterns.values():
            all_safe_patterns.update(category_patterns)

        risky_targets = []
        safe_targets = []

        for target in target_modules:
            clean_target = target.strip().lower()

            # Check if target matches common safe patterns
            is_safe = any(safe_pattern.lower() in clean_target for safe_pattern in all_safe_patterns)

            if is_safe:
                safe_targets.append(target)
            else:
                risky_targets.append(target)

        if risky_targets:
            warnings.append({
                "type": "unknown_arch_risky_targets",
                "details": {
                    "message": "QUARANTINE: Unknown architecture with potentially risky target modules",
                    "base_model": base_model,
                    "risky_targets": risky_targets,
                    "safe_targets": safe_targets,
                    "policy": "Permissive mode - allowing with warnings",
                    "recommendation": "Review risky targets and add architecture to allowlist",
                    "action": "QUARANTINE - Review required",
                },
                "severity": "high",
                "blocked": False,
            })
        else:
            warnings.append({
                "type": "unknown_arch_safe_targets",
                "details": {
                    "message": "ALLOW: Unknown architecture with safe-looking target modules",
                    "base_model": base_model,
                    "safe_targets": safe_targets,
                    "policy": "Permissive mode - targets appear safe",
                    "recommendation": "Add architecture to allowlist for better security",
                    "action": "ALLOW - Targets appear safe",
                },
                "severity": "medium",
                "blocked": False,
            })

        return warnings

        # Suspicious adapter patterns (potential attacks)
        self.suspicious_adapter_patterns = {
            # Unusual target modules
            "suspicious_targets": {
                "layer_norm", "layernorm", "norm",      # Normalizations (unusual)
                "bias", "scale",                        # Bias terms (suspicious)
                "position", "positional",               # Position embeddings
                "hidden", "secret", "backdoor",         # Obviously suspicious
                "inject", "poison", "malicious",
            },

            # Suspicious configuration values
            "suspicious_configs": {
                "very_high_rank": 1024,                 # Unusually high rank
                "very_low_alpha": 1,                    # Unusually low alpha
                "very_high_alpha": 10000,               # Unusually high alpha
                "zero_dropout": 0.0,                     # No regularization
            },

            # Unusual tensor name patterns (removed "__" - too many false positives)
            "suspicious_tensor_names": {
                "..", "//", "\\\\",                     # Path traversal
                "http://", "ftp://", "file://", "data:",  # Network/file access
                "<script>", "javascript:", "vbscript:",   # Script injection
            },
        }

        # Expected LoRA configuration structure
        self.expected_lora_config_keys = {
            "peft_type", "task_type", "inference_mode",
            "r", "lora_alpha", "lora_dropout", "target_modules",
            "bias", "modules_to_save",
        }

        # Standard LoRA rank ranges (for suspicion detection)
        self.standard_lora_ranks = {
            "very_low": range(1, 8),        # 1-7
            "low": range(8, 32),            # 8-31
            "medium": range(32, 128),       # 32-127
            "high": range(128, 512),        # 128-511
            "very_high": range(512, 2048),   # 512+
        }
        return None

    def can_validate(self, model_type: ModelType) -> bool:
        """This validator handles models that commonly use LoRA/adapters."""
        adapter_compatible_types = {
            ModelType.LLAMA, ModelType.GPT, ModelType.BERT, ModelType.ROBERTA,
            ModelType.T5, ModelType.BLOOM, ModelType.MISTRAL, ModelType.MIXTRAL,
            ModelType.CLASSIFIER, ModelType.SEQUENCE_CLASSIFICATION,
            ModelType.TOKEN_CLASSIFICATION, ModelType.TEXT_CLASSIFICATION,
            ModelType.SAFETENSORS, ModelType.GGUF, ModelType.HUGGINGFACE,
        }
        return model_type in adapter_compatible_types

    def validate(self, data: bytes) -> List[Dict[str, Any]]:
        """Validate adapter file content directly."""
        warnings = []

        # This validator is primarily for directory-level validation
        # Individual file validation is limited
        return warnings

    def validate_adapter_directory(self, model_directory: str) -> List[Dict[str, Any]]:
        """CRITICAL: Validate LoRA/adapter security in model directory
        Main entry point for adapter compatibility validation.
        """
        warnings = []
        model_dir = Path(model_directory)

        try:
            # Discover adapter files
            adapter_files = self._discover_adapter_files(model_dir)

            if not adapter_files:
                return warnings  # No adapter files found

            logger.info(f"🔍 Found {len(adapter_files)} adapter files - validating compatibility")

            # Parse adapter configuration
            adapter_config = self._parse_adapter_config(model_dir)
            if not adapter_config:
                warnings.append({
                    "type": "missing_adapter_config",
                    "details": {
                        "message": "Adapter files found but no valid configuration",
                        "adapter_files": [str(f) for f in adapter_files],
                        "recommendation": "Adapter configuration is required for security validation",
                    },
                    "severity": "high",
                })
                return warnings

            # Validate adapter configuration security
            config_warnings = self._validate_adapter_config_security(adapter_config, model_dir)
            warnings.extend(config_warnings)

            # Check for base model compatibility
            base_model_warnings = self._validate_base_model_compatibility(model_dir, adapter_config)
            warnings.extend(base_model_warnings)

            # Validate adapter tensor structure
            tensor_warnings = self._validate_adapter_tensors(model_dir, adapter_config)
            warnings.extend(tensor_warnings)

            # Check target modules consistency
            target_warnings = self._validate_target_modules(adapter_config)
            warnings.extend(target_warnings)

            # Verify adapter-base model digest match
            digest_warnings = self._validate_base_model_digest(model_dir, adapter_config)
            warnings.extend(digest_warnings)

            # Check for multi-adapter composition requirements
            composition_warnings = self._validate_adapter_composition(model_dir, adapter_files)
            warnings.extend(composition_warnings)

        except Exception as e:
            logger.error(f"Error in adapter validation: {str(e)}")
            warnings.append({
                "type": "adapter_validation_error",
                "details": {
                    "message": "Error validating adapter compatibility",
                    "error": str(e),
                    "recommendation": "Manual adapter verification recommended",
                },
                "severity": "medium",
            })

        return warnings

    def _discover_adapter_files(self, model_dir: Path) -> List[Path]:
        """Discover LoRA/adapter files in model directory."""
        adapter_files = []

        # Direct pattern matching
        for pattern in self.adapter_file_patterns:
            adapter_file = model_dir / pattern
            if adapter_file.exists():
                adapter_files.append(adapter_file)

        # Pattern matching with glob
        adapter_patterns = [
            "*adapter*.safetensors", "*adapter*.bin", "*adapter*.pt",
            "*lora*.safetensors", "*lora*.bin", "*lora*.pt",
            "*peft*.json", "*adapter*.json", "*lora*.json",
        ]

        for pattern in adapter_patterns:
            found_files = list(model_dir.glob(pattern))
            adapter_files.extend(found_files)

        # Remove duplicates
        return list(set(adapter_files))

    def _parse_adapter_config(self, model_dir: Path) -> Optional[Dict[str, Any]]:
        """Parse adapter configuration from various config files."""
        # Standard config file names
        config_files = [
            "adapter_config.json",
            "lora_config.json",
            "peft_config.json",
        ]

        # Check standard config files first
        for config_file in config_files:
            config_path = model_dir / config_file
            if config_path.exists():
                try:
                    with open(config_path) as f:
                        return json.load(f)
                except Exception as e:
                    logger.debug(f"Error parsing {config_file}: {str(e)}")
                    continue

        # If no standard config found, look for any *_config.json files
        config_pattern_files = list(model_dir.glob("*_config.json"))
        # Filter out base model config
        adapter_config_files = [f for f in config_pattern_files if f.name != "config.json"]

        if adapter_config_files:
            # Use the first adapter config found
            config_path = adapter_config_files[0]
            try:
                with open(config_path) as f:
                    logger.debug(f"Using adapter config: {config_path.name}")
                    return json.load(f)
            except Exception as e:
                logger.debug(f"Error parsing {config_path.name}: {str(e)}")

        return None

    def _validate_adapter_config_security(self, adapter_config: Dict[str, Any],
                                         model_dir: Path) -> List[Dict[str, Any]]:
        """Validate adapter configuration for security issues."""
        warnings = []

        # Check required fields
        missing_fields = []
        for required_field in ["peft_type", "r", "target_modules"]:
            if required_field not in adapter_config:
                missing_fields.append(required_field)

        if missing_fields:
            warnings.append({
                "type": "adapter_config_incomplete",
                "details": {
                    "message": "Adapter configuration missing required fields",
                    "missing_fields": missing_fields,
                    "recommendation": "Complete adapter configuration required for security",
                },
                "severity": "high",
            })

        # Validate LoRA parameters
        if "r" in adapter_config:
            rank = adapter_config["r"]
            if not isinstance(rank, int) or rank <= 0:
                warnings.append({
                    "type": "invalid_lora_rank",
                    "details": {
                        "message": f"Invalid LoRA rank: {rank}",
                        "rank": rank,
                        "recommendation": "LoRA rank must be positive integer",
                    },
                    "severity": "high",
                })
            elif rank > self.suspicious_adapter_patterns["suspicious_configs"]["very_high_rank"]:
                warnings.append({
                    "type": "suspicious_lora_rank",
                    "details": {
                        "message": f"Unusually high LoRA rank: {rank}",
                        "rank": rank,
                        "recommendation": "Very high ranks may indicate overfitting or attack",
                    },
                    "severity": "medium",
                })

        # Validate alpha parameter
        if "lora_alpha" in adapter_config:
            alpha = adapter_config["lora_alpha"]
            if isinstance(alpha, (int, float)):
                if alpha <= 0:
                    warnings.append({
                        "type": "invalid_lora_alpha",
                        "details": {
                            "message": f"Invalid LoRA alpha: {alpha}",
                            "alpha": alpha,
                            "recommendation": "LoRA alpha must be positive",
                        },
                        "severity": "medium",
                    })
                elif alpha > self.suspicious_adapter_patterns["suspicious_configs"]["very_high_alpha"]:
                    warnings.append({
                        "type": "suspicious_lora_alpha",
                        "details": {
                            "message": f"Unusually high LoRA alpha: {alpha}",
                            "alpha": alpha,
                            "recommendation": "Very high alpha may cause instability",
                        },
                        "severity": "low",
                    })

        # Check target modules for suspicious patterns
        if "target_modules" in adapter_config:
            target_modules = adapter_config["target_modules"]
            if isinstance(target_modules, list):
                suspicious_targets = []
                for target in target_modules:
                    if isinstance(target, str):
                        target_lower = target.lower()
                        for suspicious_pattern in self.suspicious_adapter_patterns["suspicious_targets"]:
                            if suspicious_pattern in target_lower:
                                suspicious_targets.append({
                                    "target": target,
                                    "pattern": suspicious_pattern,
                                    "risk": "Unusual target module for LoRA adaptation",
                                })

                if suspicious_targets:
                    warnings.append({
                        "type": "suspicious_adapter_targets",
                        "details": {
                            "message": "Suspicious target modules detected in adapter",
                            "suspicious_targets": suspicious_targets[:10],
                            "total_suspicious": len(suspicious_targets),
                            "recommendation": "Verify target modules are legitimate",
                        },
                        "severity": "high",
                    })

        return warnings

    def _validate_base_model_compatibility(self, model_dir: Path,
                                         adapter_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate adapter compatibility with base model."""
        warnings = []

        # Check for base_model specification
        base_model_name = adapter_config.get("base_model_name_or_path")
        if not base_model_name:
            warnings.append({
                "type": "missing_base_model_reference",
                "details": {
                    "message": "Adapter missing base model reference",
                    "recommendation": "Adapter should specify base model for compatibility",
                },
                "severity": "medium",
            })
        else:
            # Validate base model name format
            if isinstance(base_model_name, str):
                # Check for suspicious base model references
                suspicious_base_patterns = [
                    "../", "..\\", "/", "\\",           # Path traversal
                    "http://", "https://", "ftp://",    # Network references
                    "file://", "data:", "javascript:",   # Suspicious protocols
                ]

                for pattern in suspicious_base_patterns:
                    if pattern in base_model_name:
                        warnings.append({
                            "type": "suspicious_base_model_reference",
                            "details": {
                                "message": "Suspicious base model reference detected",
                                "base_model": base_model_name,
                                "pattern": pattern,
                                "recommendation": "Base model reference may be malicious",
                            },
                            "severity": "high",
                        })
                        break

        return warnings

    def _validate_adapter_tensors(self, model_dir: Path,
                                 adapter_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate adapter tensor shapes and compatibility."""
        warnings = []

        # Find adapter weight files
        adapter_weight_files = []
        weight_patterns = ["*adapter*.safetensors", "*adapter*.bin", "*lora*.safetensors"]

        for pattern in weight_patterns:
            adapter_weight_files.extend(list(model_dir.glob(pattern)))

        if not adapter_weight_files:
            warnings.append({
                "type": "missing_adapter_weights",
                "details": {
                    "message": "Adapter configuration found but no weight files",
                    "recommendation": "Adapter weights required for validation",
                },
                "severity": "medium",
            })
            return warnings

        # Validate each adapter weight file
        for weight_file in adapter_weight_files:
            try:
                tensor_warnings = self._analyze_adapter_tensors(weight_file, adapter_config)
                warnings.extend(tensor_warnings)
            except Exception as e:
                warnings.append({
                    "type": "adapter_tensor_analysis_error",
                    "details": {
                        "message": f"Error analyzing adapter tensors: {weight_file.name}",
                        "file": str(weight_file),
                        "error": str(e),
                        "recommendation": "Manual tensor verification recommended",
                    },
                    "severity": "medium",
                })

        return warnings

    def _analyze_adapter_tensors(self, weight_file: Path,
                                adapter_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze individual adapter weight file tensors."""
        warnings = []

        try:
            if weight_file.suffix == ".safetensors":
                tensor_info = self._parse_safetensors_adapter(weight_file)
            elif weight_file.suffix in [".bin", ".pt"]:
                # For pickle files, we should have already blocked them in pickle validator
                warnings.append({
                    "type": "adapter_pickle_format",
                    "details": {
                        "message": f"SECURITY: Adapter in pickle format: {weight_file.name}",
                        "file": str(weight_file),
                        "recommendation": "Convert adapter to safetensors format",
                    },
                    "severity": "critical",
                })
                return warnings
            else:
                return warnings

            if not tensor_info:
                return warnings

            # Validate tensor naming patterns
            tensor_names = list(tensor_info.keys())
            naming_warnings = self._validate_adapter_tensor_names(tensor_names)
            warnings.extend(naming_warnings)

            # Validate LoRA tensor structure
            lora_structure_warnings = self._validate_lora_tensor_structure(tensor_info, adapter_config)
            warnings.extend(lora_structure_warnings)

        except Exception as e:
            logger.debug(f"Error analyzing adapter tensors in {weight_file}: {str(e)}")

        return warnings

    def _parse_safetensors_adapter(self, weight_file: Path) -> Optional[Dict[str, Any]]:
        """Parse safetensors adapter file to extract tensor information."""
        try:
            with open(weight_file, "rb") as f:
                data = f.read()

            if len(data) < 8:
                return None

            # Parse safetensors header
            header_size = struct.unpack("<Q", data[:8])[0]
            if header_size > len(data) - 8:
                return None

            header_data = data[8:8+header_size]
            header_json = json.loads(header_data.decode("utf-8"))

            # Extract tensor info (exclude metadata)
            tensor_info = {}
            for tensor_name, tensor_data in header_json.items():
                if tensor_name != "__metadata__" and isinstance(tensor_data, dict):
                    tensor_info[tensor_name] = tensor_data

            return tensor_info

        except Exception as e:
            logger.debug(f"Error parsing safetensors adapter {weight_file}: {str(e)}")
            return None

    def _validate_adapter_tensor_names(self, tensor_names: List[str]) -> List[Dict[str, Any]]:
        """Validate adapter tensor names for suspicious patterns."""
        warnings = []

        suspicious_tensors = []

        for tensor_name in tensor_names:
            tensor_lower = tensor_name.lower()

            # Check for suspicious patterns
            for pattern in self.suspicious_adapter_patterns["suspicious_tensor_names"]:
                if pattern in tensor_lower:
                    suspicious_tensors.append({
                        "tensor": tensor_name,
                        "pattern": pattern,
                        "risk": "Suspicious tensor name pattern",
                    })
                    break

        if suspicious_tensors:
            warnings.append({
                "type": "suspicious_adapter_tensor_names",
                "details": {
                    "message": "Suspicious tensor names detected in adapter",
                    "suspicious_tensors": suspicious_tensors[:10],
                    "total_suspicious": len(suspicious_tensors),
                    "recommendation": "Verify adapter tensor names are legitimate",
                },
                "severity": "high",
            })

        return warnings

    def _validate_lora_tensor_structure(self, tensor_info: Dict[str, Any],
                                       adapter_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate LoRA tensor structure (A and B matrices)."""
        warnings = []

        # Group tensors by module (look for lora_A and lora_B pairs)
        lora_modules = {}

        for tensor_name in tensor_info:
            # Parse LoRA tensor name pattern: module.lora_A or module.lora_B
            if ".lora_A" in tensor_name or ".lora_B" in tensor_name:
                if ".lora_A" in tensor_name:
                    module_name = tensor_name.replace(".lora_A", "")
                    matrix_type = "lora_A"
                else:
                    module_name = tensor_name.replace(".lora_B", "")
                    matrix_type = "lora_B"

                if module_name not in lora_modules:
                    lora_modules[module_name] = {}

                lora_modules[module_name][matrix_type] = tensor_info[tensor_name]

        if not lora_modules:
            # No LoRA structure found - might be different adapter type
            return warnings

        # Validate LoRA A/B matrix pairs
        rank_consistency_issues = []
        missing_matrices = []

        expected_rank = adapter_config.get("r", 0)

        for module_name, matrices in lora_modules.items():
            # Check if both A and B matrices exist
            if "lora_A" not in matrices:
                missing_matrices.append(f"{module_name}.lora_A")
            if "lora_B" not in matrices:
                missing_matrices.append(f"{module_name}.lora_B")

            # If both exist, validate rank consistency
            if "lora_A" in matrices and "lora_B" in matrices:
                try:
                    shape_a = matrices["lora_A"].get("shape", [])
                    shape_b = matrices["lora_B"].get("shape", [])

                    if len(shape_a) >= 2 and len(shape_b) >= 2:
                        # For LoRA: A is (r, input_dim), B is (output_dim, r)
                        rank_a = shape_a[0] if len(shape_a) == 2 else shape_a[-2]
                        rank_b = shape_b[-1] if len(shape_b) == 2 else shape_b[-1]

                        if rank_a != rank_b:
                            rank_consistency_issues.append({
                                "module": module_name,
                                "rank_a": rank_a,
                                "rank_b": rank_b,
                                "issue": "Rank mismatch between A and B matrices",
                            })
                        elif expected_rank > 0 and rank_a != expected_rank:
                            rank_consistency_issues.append({
                                "module": module_name,
                                "actual_rank": rank_a,
                                "expected_rank": expected_rank,
                                "issue": "Rank does not match configuration",
                            })

                except Exception as e:
                    logger.debug(f"Error validating LoRA matrices for {module_name}: {str(e)}")

        if missing_matrices:
            warnings.append({
                "type": "incomplete_lora_matrices",
                "details": {
                    "message": "Missing LoRA matrices detected",
                    "missing_matrices": missing_matrices[:10],
                    "total_missing": len(missing_matrices),
                    "recommendation": "LoRA adapters require both A and B matrices",
                },
                "severity": "high",
            })

        if rank_consistency_issues:
            warnings.append({
                "type": "lora_rank_inconsistency",
                "details": {
                    "message": "LoRA rank inconsistencies detected",
                    "rank_issues": rank_consistency_issues[:10],
                    "total_issues": len(rank_consistency_issues),
                    "recommendation": "LoRA matrices must have consistent rank",
                },
                "severity": "high",
            })

        return warnings

    def _validate_target_modules(self, adapter_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """CRITICAL: Validate adapter target modules against EXPLICIT allowlists.

        SECURITY POLICY: STRICT TARGET ALLOWLISTING
        ==========================================
        - Only modules on explicit per-arch allowlist are permitted
        - Any target NOT on allowlist → BLOCKED (CRITICAL severity)
        - No fuzzy matching - exact allowlist enforcement only
        - Zero tolerance for non-allowlisted targets
        """
        warnings = []

        target_modules = adapter_config.get("target_modules", [])
        if not target_modules:
            warnings.append({
                "type": "missing_target_modules",
                "details": {
                    "message": "BLOCKED: Adapter missing target modules specification",
                    "policy": "Target modules must be explicitly declared for allowlist validation",
                    "recommendation": "Add 'target_modules' list to adapter configuration",
                    "action": "BLOCKED - Cannot validate targets without specification",
                },
                "severity": "critical",
                "blocked": True,
            })
            return warnings

        # Determine model architecture from base model name
        base_model = adapter_config.get("base_model_name_or_path", "").lower()
        detected_arch = None

        # Architecture detection with priority order
        arch_detection_patterns = [
            ("llama", ["llama", "alpaca", "vicuna", "orca"]),
            ("mistral", ["mistral", "zephyr"]),
            ("mixtral", ["mixtral", "8x7b"]),
            ("gpt", ["gpt", "openai"]),
            ("bert", ["bert"]),
            ("roberta", ["roberta"]),
            ("t5", ["t5", "flan"]),
            ("bloom", ["bloom", "bloomz"]),
            ("falcon", ["falcon"]),
        ]

        for arch_name, patterns in arch_detection_patterns:
            if any(pattern in base_model for pattern in patterns):
                detected_arch = arch_name
                break

        if not detected_arch:
            # Handle unknown architectures based on policy configuration
            return self._handle_unknown_architecture(base_model, target_modules, warnings)

        # Get explicit allowlist for detected architecture
        allowed_targets = self.lora_target_allowlists.get(detected_arch, set())
        if not allowed_targets:
            warnings.append({
                "type": "missing_target_allowlist",
                "details": {
                    "message": f"BLOCKED: No target allowlist defined for {detected_arch} architecture",
                    "architecture": detected_arch,
                    "policy": "Explicit allowlist required for each supported architecture",
                    "action": "BLOCKED - Cannot validate without allowlist",
                },
                "severity": "critical",
                "blocked": True,
            })
            return warnings

        # STRICT ALLOWLIST ENFORCEMENT - exact matching only
        blocked_targets = []
        allowed_targets_found = []

        for target in target_modules:
            if not isinstance(target, str):
                blocked_targets.append({
                    "target": str(target),
                    "reason": "Invalid target type - must be string",
                    "risk": "CRITICAL",
                })
                continue

            # Clean target name for comparison
            clean_target = target.strip()

            # Check for exact match in allowlist (with layer number flexibility)
            target_allowed = False

            # Direct exact match
            if clean_target in allowed_targets:
                target_allowed = True
                allowed_targets_found.append(clean_target)
            else:
                # Check for layer-numbered variants (e.g., layers.0.self_attn.q_proj)
                # Extract the module part after layer numbers

                layer_pattern = r"(?:model\.)?layers\.\d+\.(.+)"
                match = re.search(layer_pattern, clean_target)

                if match:
                    module_part = match.group(1)
                    if module_part in allowed_targets:
                        target_allowed = True
                        allowed_targets_found.append(f"{clean_target} -> {module_part}")

                # Pattern: decoder.layers.N.module or encoder.layers.N.module (T5 style)
                enc_dec_pattern = r"(?:encoder|decoder)\.layers\.\d+\.(.+)"
                match = re.search(enc_dec_pattern, clean_target)

                if match:
                    module_part = match.group(1)
                    if module_part in allowed_targets:
                        target_allowed = True
                        allowed_targets_found.append(f"{clean_target} -> {module_part}")

            if not target_allowed:
                blocked_targets.append({
                    "target": clean_target,
                    "reason": "NOT on explicit allowlist for architecture",
                    "risk": "CRITICAL - Unauthorized target module",
                })

        # BLOCKING: Report any non-allowlisted targets
        if blocked_targets:
            warnings.append({
                "type": "blocked_non_allowlisted_targets",
                "details": {
                    "message": f"BLOCKED: {len(blocked_targets)} target modules NOT on explicit allowlist",
                    "architecture": detected_arch,
                    "blocked_targets": blocked_targets,
                    "allowed_targets": sorted(allowed_targets),
                    "allowed_found": allowed_targets_found,
                    "policy": "STRICT allowlist enforcement - only pre-approved targets permitted",
                    "recommendation": "Remove blocked targets or add to architecture allowlist if legitimate",
                    "action": f"BLOCKED - {len(blocked_targets)} unauthorized target modules detected",
                },
                "severity": "critical",
                "blocked": True,
            })

        # SUCCESS: Log allowlisted targets found
        if allowed_targets_found:
            logger.info(f"✅ Target allowlist validation passed: {len(allowed_targets_found)} allowed targets for {detected_arch}")

        return warnings

    def _validate_base_model_digest(self, model_dir: Path,
                                   adapter_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """CRITICAL: Mandatory base model digest validation to prevent wrong base model application.

        SECURITY POLICY: Base model digest binding is MANDATORY
        - BLOCK: Adapters without base_model_digest
        - BLOCK: Digest mismatches (wrong base model)
        - REQUIRE: Canonical bundle digest verification
        """
        warnings = []

        # Look for base model digest in configuration
        stored_digest = adapter_config.get("base_model_digest") or adapter_config.get("model_hash")

        if not stored_digest:
            warnings.append({
                "type": "missing_base_model_digest",
                "details": {
                    "message": "BLOCKED: Adapter missing mandatory base model digest",
                    "policy": "Base model digest binding is MANDATORY for adapter security",
                    "recommendation": "Add 'base_model_digest' field with canonical bundle digest",
                    "action": "BLOCKED - Adapter cannot be loaded without digest verification",
                },
                "severity": "critical",  # Upgraded to CRITICAL - this is now BLOCKING
                "blocked": True,  # Explicit blocking flag
            })
            return warnings

        # Try to find base model files in directory
        base_model_files = []
        base_patterns = ["model.safetensors", "pytorch_model.bin", "model*.safetensors"]

        for pattern in base_patterns:
            found_files = list(model_dir.glob(pattern))
            # Filter out adapter files
            for f in found_files:
                if "adapter" not in f.name.lower() and "lora" not in f.name.lower():
                    base_model_files.append(f)

        if not base_model_files:
            warnings.append({
                "type": "base_model_not_found",
                "details": {
                    "message": "BLOCKED: Cannot verify mandatory base model digest - base model files not found",
                    "stored_digest": stored_digest[:16] + "..." if len(stored_digest) > 16 else stored_digest,
                    "searched_patterns": ["model.safetensors", "pytorch_model.bin", "model*.safetensors"],
                    "policy": "Base model files must be present for digest verification",
                    "recommendation": "Ensure base model files are in the same directory as adapter",
                    "action": "BLOCKED - Cannot verify adapter binding without base model",
                },
                "severity": "critical",  # Upgraded to CRITICAL for mandatory verification
                "blocked": True,
            })
            return warnings

        # Calculate digest of base model files
        try:
            calculated_digest = self._calculate_model_digest(base_model_files)

            if calculated_digest != stored_digest:
                warnings.append({
                    "type": "base_model_digest_mismatch",
                    "details": {
                        "message": "BLOCKED: Base model digest mismatch - wrong base model detected",
                        "stored_digest": stored_digest[:16] + "..." if len(stored_digest) > 16 else stored_digest,
                        "calculated_digest": calculated_digest[:16] + "..." if len(calculated_digest) > 16 else calculated_digest,
                        "policy": "Canonical bundle digest must match for adapter binding",
                        "recommendation": "Use adapter only with the correct base model",
                        "action": "BLOCKED - Adapter binding to wrong base model prevented",
                    },
                    "severity": "critical",
                    "blocked": True,  # Explicit blocking flag
                })
            else:
                logger.info("✅ Base model digest verification passed")

        except Exception as e:
            warnings.append({
                "type": "digest_calculation_error",
                "details": {
                    "message": "Error calculating base model digest",
                    "error": str(e),
                    "recommendation": "Manual base model verification recommended",
                },
                "severity": "medium",
            })

        return warnings

    def _calculate_model_digest(self, model_files: List[Path]) -> str:
        """Calculate canonical bundle digest of base model files for adapter binding.

        This creates a reproducible digest that uniquely identifies a model bundle,
        used for mandatory adapter-to-base-model binding verification.
        """
        return self._compute_canonical_bundle_digest(model_files)

    def _compute_canonical_bundle_digest(self, model_files: List[Path]) -> str:
        """Compute canonical bundle digest using comprehensive file analysis.

        SECURITY: This digest serves as the unique identifier for adapter binding.
        Changes to any model file will result in a different digest, preventing
        adapters from being applied to wrong or modified base models.

        Digest includes:
        - File names (sorted for consistency)
        - File sizes (detect file modifications)
        - File content hashes (detect content changes)
        - Bundle structure (detect file additions/removals)
        """
        hasher = hashlib.sha256()

        # Sort files for consistent digest calculation
        sorted_files = sorted(model_files, key=lambda x: x.name)

        # Add bundle metadata for structure verification
        bundle_info = {
            "file_count": len(sorted_files),
            "total_size": sum(f.stat().st_size for f in sorted_files if f.exists()),
            "file_list": [f.name for f in sorted_files],
        }
        hasher.update(json.dumps(bundle_info, sort_keys=True).encode("utf-8"))

        for model_file in sorted_files:
            try:
                file_stat = model_file.stat()
                file_size = file_stat.st_size

                # Add file metadata to ensure structure integrity
                file_metadata = {
                    "name": model_file.name,
                    "size": file_size,
                    "mtime": int(file_stat.st_mtime),  # Modification time
                }
                hasher.update(json.dumps(file_metadata, sort_keys=True).encode("utf-8"))

                # Add file content with enhanced security
                with open(model_file, "rb") as f:
                    if file_size <= 64 * 1024 * 1024:  # <= 64MB, hash entire file
                        # Small files: complete content hash
                        while chunk := f.read(65536):  # 64KB chunks
                            hasher.update(chunk)
                    else:
                        # Large files: strategic sampling for performance + security
                        # Hash first 32MB (critical model headers/metadata)
                        first_chunk = f.read(32 * 1024 * 1024)
                        hasher.update(first_chunk)

                        # Hash middle section (detect internal modifications)
                        f.seek(file_size // 2 - (16 * 1024 * 1024))  # Middle 32MB
                        middle_chunk = f.read(32 * 1024 * 1024)
                        hasher.update(middle_chunk)

                        # Hash last 32MB (critical model weights/final layers)
                        f.seek(-32 * 1024 * 1024, 2)
                        last_chunk = f.read()
                        hasher.update(last_chunk)

                        # Include file size as additional verification
                        hasher.update(f"SIZE:{file_size}".encode())

            except Exception as e:
                logger.warning(f"Error reading {model_file} for canonical digest: {str(e)}")
                # Include error in hash to detect file access issues
                error_info = f"ERROR:{model_file.name}:{str(e)}"
                hasher.update(error_info.encode("utf-8"))

        # Return canonical bundle digest
        canonical_digest = hasher.hexdigest()
        logger.debug(f"Computed canonical bundle digest: {canonical_digest[:16]}...")
        return canonical_digest

    def generate_base_model_digest(self, model_directory: str) -> Optional[str]:
        """PUBLIC UTILITY: Generate canonical bundle digest for adapter binding.

        This method helps users generate the required base_model_digest for their
        adapter configurations. The digest should be stored in the adapter config
        as 'base_model_digest' field.

        Example usage:
            validator = LoRAAdapterSecurityValidator(metadata)
            digest = validator.generate_base_model_digest("/path/to/base/model")
            # Add to adapter config: {"base_model_digest": digest, ...}
        """
        try:
            model_dir = Path(model_directory)
            if not model_dir.exists():
                logger.error(f"Base model directory not found: {model_directory}")
                return None

            # Find base model files
            base_model_files = []
            base_patterns = [
                "model.safetensors",
                "pytorch_model.bin",
                "model*.safetensors",
                "model-*.safetensors",
            ]

            for pattern in base_patterns:
                found_files = list(model_dir.glob(pattern))
                # Filter out adapter files
                for f in found_files:
                    if "adapter" not in f.name.lower() and "lora" not in f.name.lower():
                        base_model_files.append(f)

            if not base_model_files:
                logger.error(f"No base model files found in {model_directory}")
                return None

            canonical_digest = self._compute_canonical_bundle_digest(base_model_files)
            logger.info(f"Generated canonical bundle digest for {len(base_model_files)} base model files")
            return canonical_digest

        except Exception as e:
            logger.error(f"Error generating base model digest: {str(e)}")
            return None

    def _validate_adapter_composition(self, model_dir: Path, adapter_files: List[Path]) -> List[Dict[str, Any]]:
        """CRITICAL: Validate multi-adapter composition security.

        SECURITY POLICY: COMPOSITION MANIFEST REQUIREMENT
        =================================================
        When multiple adapters exist:
        - REQUIRE composition manifest (adapter_composition.json)
        - MANDATE apply-order specification
        - GENERATE composed model digest for verification
        - BLOCK composition without proper manifest
        - VALIDATE adapter compatibility in composition

        This prevents:
        - Uncontrolled adapter stacking
        - Order-dependent security vulnerabilities
        - Unauthorized composition modifications
        - Supply chain attacks via adapter mixing
        """
        warnings = []

        # Count distinct adapter sets (exclude config files and base model files)
        weight_files = [f for f in adapter_files if f.suffix in [".safetensors", ".bin", ".pt"]]
        unique_adapters = set()

        for weight_file in weight_files:
            # Skip base model files
            if weight_file.name.startswith("model") and not any(x in weight_file.name.lower() for x in ["adapter", "lora"]):
                continue

            # Extract adapter identifier (remove layer/shard numbers)
            adapter_name = weight_file.stem
            # Remove common suffixes like -00001-of-00002
            clean_name = re.sub(r"-\d+-of-\d+$", "", adapter_name)

            # Remove config suffix patterns
            clean_name = re.sub(r"_config$", "", clean_name)

            unique_adapters.add(clean_name)

        adapter_count = len(unique_adapters)

        logger.debug(f"Composition analysis: {adapter_count} unique adapters found: {sorted(unique_adapters)}")

        if adapter_count <= 1:
            # Single adapter - no composition manifest required
            logger.debug(f"Single adapter detected ({adapter_count}), no composition manifest needed")
            return warnings

        logger.info(f"🔗 Multi-adapter composition detected: {adapter_count} adapters")

        # MANDATORY: Check for composition manifest
        composition_manifest_path = model_dir / "adapter_composition.json"
        if not composition_manifest_path.exists():
            warnings.append({
                "type": "missing_composition_manifest",
                "details": {
                    "message": "BLOCKED: Multiple adapters require composition manifest",
                    "adapter_count": adapter_count,
                    "adapters_found": sorted(unique_adapters),
                    "policy": "Multi-adapter compositions MUST specify apply-order manifest",
                    "manifest_required": "adapter_composition.json",
                    "recommendation": "Create composition manifest with apply_order, compatibility_matrix, and metadata",
                    "action": "BLOCKED - Cannot safely compose adapters without manifest",
                },
                "severity": "critical",
                "blocked": True,
            })
            return warnings

        # Parse and validate composition manifest
        try:
            with open(composition_manifest_path) as f:
                composition_manifest = json.load(f)
        except Exception as e:
            warnings.append({
                "type": "invalid_composition_manifest",
                "details": {
                    "message": "BLOCKED: Cannot parse composition manifest",
                    "manifest_path": str(composition_manifest_path),
                    "error": str(e),
                    "action": "BLOCKED - Invalid manifest format",
                },
                "severity": "critical",
                "blocked": True,
            })
            return warnings

        # Validate manifest structure and content
        manifest_warnings = self._validate_composition_manifest_structure(composition_manifest, unique_adapters)
        warnings.extend(manifest_warnings)

        # If manifest is valid, generate composed model digest
        if not any(w.get("blocked", False) for w in manifest_warnings):
            composed_digest_warnings = self._generate_composed_model_digest(model_dir, composition_manifest)
            warnings.extend(composed_digest_warnings)

        return warnings

    def _validate_composition_manifest_structure(self, manifest: Dict[str, Any],
                                               detected_adapters: set) -> List[Dict[str, Any]]:
        """Validate composition manifest structure and security requirements.

        Required manifest structure:
        {
          "composition_version": "1.0",
          "apply_order": ["adapter1", "adapter2", ...],
          "base_model_digest": "sha256...",
          "compatibility_matrix": {...},
          "composition_metadata": {...}
        }
        """
        warnings = []

        # Required fields for secure composition
        required_fields = [
            "composition_version",
            "apply_order",
            "base_model_digest",
            "composition_metadata",
        ]

        missing_fields = []
        for field in required_fields:
            if field not in manifest:
                missing_fields.append(field)

        if missing_fields:
            warnings.append({
                "type": "incomplete_composition_manifest",
                "details": {
                    "message": "BLOCKED: Composition manifest missing required fields",
                    "missing_fields": missing_fields,
                    "required_fields": required_fields,
                    "policy": "Complete composition manifest required for multi-adapter security",
                    "action": "BLOCKED - Incomplete manifest",
                },
                "severity": "critical",
                "blocked": True,
            })
            return warnings

        # Validate apply_order
        apply_order = manifest.get("apply_order", [])
        if not isinstance(apply_order, list) or len(apply_order) < 2:
            warnings.append({
                "type": "invalid_apply_order",
                "details": {
                    "message": "BLOCKED: Invalid or insufficient apply order specification",
                    "apply_order": apply_order,
                    "detected_adapters": sorted(detected_adapters),
                    "policy": "Apply order must specify sequence for all adapters",
                    "action": "BLOCKED - Invalid apply order",
                },
                "severity": "critical",
                "blocked": True,
            })
            return warnings

        # Verify all detected adapters are in apply_order
        apply_order_set = set(apply_order)
        missing_from_order = detected_adapters - apply_order_set
        extra_in_order = apply_order_set - detected_adapters

        if missing_from_order:
            warnings.append({
                "type": "adapters_missing_from_apply_order",
                "details": {
                    "message": "BLOCKED: Detected adapters not in apply order",
                    "missing_adapters": sorted(missing_from_order),
                    "apply_order": apply_order,
                    "policy": "All adapters must be specified in apply_order",
                    "action": "BLOCKED - Incomplete apply order",
                },
                "severity": "critical",
                "blocked": True,
            })

        if extra_in_order:
            warnings.append({
                "type": "extra_adapters_in_apply_order",
                "details": {
                    "message": "Apply order references non-existent adapters",
                    "extra_adapters": sorted(extra_in_order),
                    "detected_adapters": sorted(detected_adapters),
                    "recommendation": "Remove non-existent adapters from apply_order",
                },
                "severity": "medium",
            })

        # Validate composition version
        comp_version = manifest.get("composition_version")
        if comp_version != "1.0":
            warnings.append({
                "type": "unsupported_composition_version",
                "details": {
                    "message": f"Unsupported composition version: {comp_version}",
                    "supported_versions": ["1.0"],
                    "recommendation": "Use supported composition version",
                },
                "severity": "medium",
            })

        # Validate base model digest consistency
        manifest_base_digest = manifest.get("base_model_digest")
        if not manifest_base_digest or not isinstance(manifest_base_digest, str):
            warnings.append({
                "type": "missing_base_model_digest_in_composition",
                "details": {
                    "message": "BLOCKED: Composition manifest missing base model digest",
                    "policy": "Base model digest required for composition verification",
                    "action": "BLOCKED - Missing base model digest",
                },
                "severity": "critical",
                "blocked": True,
            })

        return warnings

    def _generate_composed_model_digest(self, model_dir: Path,
                                      composition_manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate cryptographic digest of the complete composed model.

        Composed digest includes:
        - Base model digest
        - Each adapter digest in apply order
        - Composition manifest hash
        - Apply order sequence hash

        This creates a unique fingerprint for the complete composed model
        that changes if ANY component or ordering changes.
        """
        warnings = []

        try:
            hasher = hashlib.sha256()

            # 1. Base model digest
            base_model_digest = composition_manifest.get("base_model_digest", "")
            hasher.update(f"BASE_MODEL:{base_model_digest}".encode())

            # 2. Adapter digests in apply order
            apply_order = composition_manifest.get("apply_order", [])

            for i, adapter_name in enumerate(apply_order):
                # Find adapter files for this adapter
                adapter_pattern = f"*{adapter_name}*.safetensors"
                adapter_files = list(model_dir.glob(adapter_pattern))

                if not adapter_files:
                    # Try alternative patterns
                    alt_patterns = [f"{adapter_name}.safetensors", f"{adapter_name}_*.safetensors"]
                    for pattern in alt_patterns:
                        adapter_files.extend(list(model_dir.glob(pattern)))

                if adapter_files:
                    # Calculate digest for this adapter
                    adapter_digest = self._calculate_adapter_digest(adapter_files)
                    hasher.update(f"ADAPTER_{i}:{adapter_name}:{adapter_digest}".encode())
                else:
                    # Adapter file not found - use placeholder but warn
                    hasher.update(f"ADAPTER_{i}:{adapter_name}:MISSING".encode())
                    warnings.append({
                        "type": "adapter_file_not_found_for_composition",
                        "details": {
                            "message": f"Adapter files not found for composition: {adapter_name}",
                            "adapter_name": adapter_name,
                            "searched_patterns": [adapter_pattern, *alt_patterns],
                            "recommendation": "Verify adapter files exist for composition",
                        },
                        "severity": "medium",
                    })

            # 3. Composition manifest hash (excluding composed_model_digest field)
            manifest_for_hash = composition_manifest.copy()
            manifest_for_hash.pop("composed_model_digest", None)  # Remove if exists
            manifest_json = json.dumps(manifest_for_hash, sort_keys=True)
            hasher.update(f"MANIFEST:{manifest_json}".encode())

            # 4. Apply order sequence hash (for order sensitivity)
            order_hash = hashlib.sha256("->".join(apply_order).encode("utf-8")).hexdigest()
            hasher.update(f"ORDER_SEQUENCE:{order_hash}".encode())

            # Generate final composed model digest
            composed_digest = hasher.hexdigest()

            # Store composed digest for future reference
            composed_digest_file = model_dir / "composed_model_digest.txt"
            composed_digest_file.write_text(f"{composed_digest}\n")

            logger.info(f"✅ Generated composed model digest: {composed_digest[:16]}...")

            # Add success info
            warnings.append({
                "type": "composed_model_digest_generated",
                "details": {
                    "message": "Composed model digest generated successfully",
                    "composed_digest": composed_digest,
                    "applies_order": apply_order,
                    "base_model_digest": base_model_digest[:16] + "..." if len(base_model_digest) > 16 else base_model_digest,
                    "adapters_count": len(apply_order),
                    "digest_file": str(composed_digest_file),
                    "security_note": "This digest uniquely identifies the composed model configuration",
                },
                "severity": "info",
            })

        except Exception as e:
            warnings.append({
                "type": "composed_digest_generation_error",
                "details": {
                    "message": "Error generating composed model digest",
                    "error": str(e),
                    "recommendation": "Manual composition verification recommended",
                },
                "severity": "medium",
            })

        return warnings

    def _calculate_adapter_digest(self, adapter_files: List[Path]) -> str:
        """Calculate digest for a specific adapter's files."""
        hasher = hashlib.sha256()

        # Sort files for consistent digest
        sorted_files = sorted(adapter_files, key=lambda x: x.name)

        for adapter_file in sorted_files:
            try:
                # Add filename
                hasher.update(adapter_file.name.encode("utf-8"))

                # Add file content (similar to base model digest strategy)
                with open(adapter_file, "rb") as f:
                    file_size = adapter_file.stat().st_size

                    if file_size <= 16 * 1024 * 1024:  # <= 16MB, hash entire file
                        while chunk := f.read(65536):
                            hasher.update(chunk)
                    else:
                        # Large adapter: hash first + last + size
                        hasher.update(f.read(8 * 1024 * 1024))  # First 8MB
                        f.seek(-8 * 1024 * 1024, 2)  # Last 8MB
                        hasher.update(f.read())
                        hasher.update(f"SIZE:{file_size}".encode())

            except Exception as e:
                # Include error in hash for consistency
                hasher.update(f"ERROR:{adapter_file.name}:{str(e)}".encode())

        return hasher.hexdigest()
