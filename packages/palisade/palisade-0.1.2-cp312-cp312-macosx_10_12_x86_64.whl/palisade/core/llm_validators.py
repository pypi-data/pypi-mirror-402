"""LLM and Classifier specific validator filtering."""

from typing import List, Type

from palisade.models.metadata import ModelType
from palisade.validators.backdoor import BackdoorDetectionValidator
from palisade.validators.base import BaseValidator
from palisade.validators.gguf_safety import GGUFSafetyValidator
from palisade.validators.lora_adapter_security import LoRAAdapterSecurityValidator
from palisade.validators.metadata_security import MetadataSecurityValidator
from palisade.validators.model_integrity import ModelIntegrityValidator
from palisade.validators.pickle_security import PickleSecurityValidator
from palisade.validators.provenance_security import ProvenanceSecurityValidator
from palisade.validators.safetensors_integrity import SafetensorsIntegrityValidator
from palisade.validators.supply_chain import SupplyChainValidator
from palisade.validators.tokenizer_hygiene import TokenizerHygieneValidator

# Essential security validators for LLMs and classifiers (5 validators)
LLM_CLASSIFIER_VALIDATORS = {
    # Priority 0 - CRITICAL Security (ALWAYS run first)
    PickleSecurityValidator: {
        "applicable_types": {
            ModelType.PYTORCH, ModelType.SKLEARN,
            ModelType.JOBLIB, ModelType.DILL, ModelType.UNKNOWN,
        },
        "priority": 0,  # HIGHEST priority - RCE prevention
    },

    SafetensorsIntegrityValidator: {
        "applicable_types": {
            ModelType.SAFETENSORS, ModelType.HUGGINGFACE,
        },
        "priority": 0,  # HIGHEST priority - Shard integrity verification
    },

    TokenizerHygieneValidator: {
        "applicable_types": {
            ModelType.LLAMA, ModelType.GPT, ModelType.BERT, ModelType.ROBERTA,
            ModelType.T5, ModelType.BLOOM, ModelType.MISTRAL, ModelType.MIXTRAL,
            ModelType.CLASSIFIER, ModelType.SEQUENCE_CLASSIFICATION,
            ModelType.TOKEN_CLASSIFICATION, ModelType.TEXT_CLASSIFICATION,
            ModelType.SAFETENSORS, ModelType.GGUF, ModelType.HUGGINGFACE,
        },
        "priority": 0,  # HIGHEST priority - Tokenizer security validation
    },

    LoRAAdapterSecurityValidator: {
        "applicable_types": {
            ModelType.LLAMA, ModelType.GPT, ModelType.BERT, ModelType.ROBERTA,
            ModelType.T5, ModelType.BLOOM, ModelType.MISTRAL, ModelType.MIXTRAL,
            ModelType.CLASSIFIER, ModelType.SEQUENCE_CLASSIFICATION,
            ModelType.TOKEN_CLASSIFICATION, ModelType.TEXT_CLASSIFICATION,
            ModelType.SAFETENSORS, ModelType.GGUF, ModelType.HUGGINGFACE,
        },
        "priority": 0,  # HIGHEST priority - Adapter compatibility and security
    },

    GGUFSafetyValidator: {
        "applicable_types": {
            ModelType.GGUF,
        },
        "priority": 0,  # HIGHEST priority - GGUF format integrity and security
    },

    ProvenanceSecurityValidator: {
        "applicable_types": {
            ModelType.LLAMA, ModelType.GPT, ModelType.BERT, ModelType.ROBERTA,
            ModelType.T5, ModelType.BLOOM, ModelType.MISTRAL, ModelType.MIXTRAL,
            ModelType.CLASSIFIER, ModelType.SEQUENCE_CLASSIFICATION,
            ModelType.TOKEN_CLASSIFICATION, ModelType.TEXT_CLASSIFICATION,
            ModelType.SAFETENSORS, ModelType.GGUF, ModelType.HUGGINGFACE,
            ModelType.PYTORCH, ModelType.UNKNOWN,
        },
        "priority": 1,  # High priority - Supply chain security and authenticity
    },

    # Priority 1 - Critical security validators (Always run)
    BackdoorDetectionValidator: {
        "applicable_types": {
            ModelType.LLAMA, ModelType.GPT, ModelType.BERT, ModelType.ROBERTA,
            ModelType.T5, ModelType.BLOOM, ModelType.MISTRAL, ModelType.MIXTRAL,
            ModelType.CLASSIFIER, ModelType.SEQUENCE_CLASSIFICATION,
            ModelType.TOKEN_CLASSIFICATION, ModelType.TEXT_CLASSIFICATION,
            ModelType.SAFETENSORS, ModelType.GGUF, ModelType.HUGGINGFACE,
        },
        "priority": 1,  # High priority - backdoor detection
    },

    MetadataSecurityValidator: {
        "applicable_types": {
            ModelType.LLAMA, ModelType.GPT, ModelType.BERT, ModelType.ROBERTA,
            ModelType.T5, ModelType.BLOOM, ModelType.MISTRAL, ModelType.MIXTRAL,
            ModelType.CLASSIFIER, ModelType.SEQUENCE_CLASSIFICATION,
            ModelType.TOKEN_CLASSIFICATION, ModelType.TEXT_CLASSIFICATION,
            ModelType.SAFETENSORS, ModelType.GGUF, ModelType.HUGGINGFACE,
        },
        "priority": 1,  # High priority - metadata security analysis
    },

    # Priority 2 - Important validators
    SupplyChainValidator: {
        "applicable_types": {
            ModelType.LLAMA, ModelType.GPT, ModelType.BERT, ModelType.ROBERTA,
            ModelType.T5, ModelType.BLOOM, ModelType.MISTRAL, ModelType.MIXTRAL,
            ModelType.CLASSIFIER, ModelType.SEQUENCE_CLASSIFICATION,
            ModelType.TOKEN_CLASSIFICATION, ModelType.TEXT_CLASSIFICATION,
            ModelType.HUGGINGFACE, ModelType.SAFETENSORS, ModelType.GGUF,
        },
        "priority": 2,  # Medium priority - supply chain security
    },

    ModelIntegrityValidator: {
        "applicable_types": {
            ModelType.LLAMA, ModelType.GPT, ModelType.BERT, ModelType.ROBERTA,
            ModelType.T5, ModelType.BLOOM, ModelType.MISTRAL, ModelType.MIXTRAL,
            ModelType.CLASSIFIER, ModelType.SEQUENCE_CLASSIFICATION,
            ModelType.TOKEN_CLASSIFICATION, ModelType.TEXT_CLASSIFICATION,
            ModelType.SAFETENSORS, ModelType.GGUF, ModelType.HUGGINGFACE,
        },
        "priority": 2,  # Medium priority - integrity validation
    },
}

def get_llm_validators(model_type: ModelType, priority_threshold: int = 3) -> List[Type[BaseValidator]]:
    """Get list of validators applicable to LLM/classifier model type.

    Args:
    ----
        model_type: The detected model type
        priority_threshold: Only include validators with priority <= threshold (1=high, 3=low)

    Returns:
    -------
        List of validator classes to run
    """
    applicable_validators = []

    for validator_class, config in LLM_CLASSIFIER_VALIDATORS.items():
        # Check if validator applies to this model type
        if model_type in config["applicable_types"]:
            # Check priority threshold
            if config["priority"] <= priority_threshold:
                applicable_validators.append(validator_class)

    # Sort by priority (lower number = higher priority)
    applicable_validators.sort(
        key=lambda v: LLM_CLASSIFIER_VALIDATORS[v]["priority"],
    )

    return applicable_validators

def get_critical_validators(model_type: ModelType) -> List[Type[BaseValidator]]:
    """Get only the most critical validators for fast scanning."""
    return get_llm_validators(model_type, priority_threshold=1)

def get_comprehensive_validators(model_type: ModelType) -> List[Type[BaseValidator]]:
    """Get comprehensive validator set for thorough scanning."""
    return get_llm_validators(model_type, priority_threshold=3)

def should_run_validator(validator_class: Type[BaseValidator], model_type: ModelType) -> bool:
    """Check if a specific validator should run for the given model type."""
    if validator_class not in LLM_CLASSIFIER_VALIDATORS:
        return False

    return model_type in LLM_CLASSIFIER_VALIDATORS[validator_class]["applicable_types"]

def get_validator_priority(validator_class: Type[BaseValidator]) -> int:
    """Get priority level for a validator (1=highest, 3=lowest)."""
    return LLM_CLASSIFIER_VALIDATORS.get(validator_class, {}).get("priority", 999)

def filter_validators_by_file_size(validators: List[Type[BaseValidator]], file_size: int) -> List[Type[BaseValidator]]:
    """Filter validators based on file size to optimize performance.

    Args:
    ----
        validators: List of validator classes
        file_size: File size in bytes

    Returns:
    -------
        Filtered list of validators
    """
    if file_size > 50 * 1024 * 1024 * 1024:  # > 50GB
        # For very large files, only run critical validators
        return [v for v in validators if get_validator_priority(v) == 1]
    elif file_size > 10 * 1024 * 1024 * 1024:  # > 10GB
        # For large files, run high and medium priority
        return [v for v in validators if get_validator_priority(v) <= 2]
    else:
        # For smaller files, run all applicable validators
        return validators

def get_optimized_validator_set(model_type: ModelType, file_size: int, fast_mode: bool = False) -> List[Type[BaseValidator]]:
    """Get optimized validator set based on model type, file size, and performance requirements.

    Args:
    ----
        model_type: The detected model type
        file_size: File size in bytes
        fast_mode: If True, only run most critical validators

    Returns:
    -------
        Optimized list of validators
    """
    if fast_mode:
        validators = get_critical_validators(model_type)
    else:
        validators = get_comprehensive_validators(model_type)

    # Filter by file size
    validators = filter_validators_by_file_size(validators, file_size)

    return validators
