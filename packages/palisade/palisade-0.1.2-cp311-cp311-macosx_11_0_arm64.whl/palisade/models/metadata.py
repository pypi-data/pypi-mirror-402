
"""Model metadata definitions.

This module defines the data structures for model metadata and types.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Tuple, Union


class ModelType(Enum):
    """Enumeration of supported model types."""
    
    UNKNOWN = "unknown"
    NON_TARGET = "non_target"
    SAFETENSORS = "safetensors"
    GGUF = "gguf"
    PYTORCH = "pytorch"
    PICKLE = "pickle"
    DILL = "dill"
    JOBLIB = "joblib"
    SKLEARN = "sklearn"
    ONNX = "onnx"
    TENSORFLOW = "tensorflow"
    TOKENIZER = "tokenizer"
    HUGGINGFACE = "huggingface"
    LLAMA = "llama"
    BERT = "bert"
    GPT = "gpt"
    TRANSFORMER = "transformer"
    ROBERTA = "roberta"
    GEMMA = "gemma"
    T5 = "t5"
    BLOOM = "bloom"
    MISTRAL = "mistral"
    MIXTRAL = "mixtral"
    CLASSIFIER = "classifier"
    SEQUENCE_CLASSIFICATION = "sequence_classification"
    TOKEN_CLASSIFICATION = "token_classification"
    TEXT_CLASSIFICATION = "text_classification"


@dataclass
class ModelMetadata:
    """Metadata for ML models."""
    
    model_type: ModelType
    framework_version: str
    num_parameters: Optional[int] = None
    input_shape: Optional[Union[Tuple[int, ...], Dict[str, Any]]] = None
    output_shape: Optional[Union[Tuple[int, ...], Dict[str, Any]]] = None
    architecture: Optional[str] = None
    is_quantized: bool = False
    is_distributed: bool = False
    
    # Additional metadata fields
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    training_framework: Optional[str] = None
    training_data: Optional[str] = None
    license: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "model_type": self.model_type.value if self.model_type else None,
            "framework_version": self.framework_version,
            "num_parameters": self.num_parameters,
            "input_shape": self.input_shape,
            "output_shape": self.output_shape,
            "architecture": self.architecture,
            "is_quantized": self.is_quantized,
            "is_distributed": self.is_distributed,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "training_framework": self.training_framework,
            "training_data": self.training_data,
            "license": self.license,
            "author": self.author,
            "description": self.description,
            "tags": self.tags,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelMetadata":
        """Create metadata from dictionary."""
        model_type = ModelType(data.get("model_type", "unknown"))
        return cls(
            model_type=model_type,
            framework_version=data.get("framework_version", "unknown"),
            num_parameters=data.get("num_parameters"),
            input_shape=data.get("input_shape"),
            output_shape=data.get("output_shape"),
            architecture=data.get("architecture"),
            is_quantized=data.get("is_quantized", False),
            is_distributed=data.get("is_distributed", False),
            model_name=data.get("model_name"),
            model_version=data.get("model_version"),
            training_framework=data.get("training_framework"),
            training_data=data.get("training_data"),
            license=data.get("license"),
            author=data.get("author"),
            description=data.get("description"),
            tags=data.get("tags"),
        )
