"""Palisade models module.

This module contains data models and abstractions for ML model files and metadata.
"""

from .metadata import ModelMetadata, ModelType
from .model_file import ModelFile, create_model_file
from .types import ChunkInfo, StreamingContext
from .validation_result import ValidationMetrics, ValidationResult

# Import report schema components
try:
    from .report_schema import (
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
    from .schema_utils import (
        convert_legacy_severity,
        convert_legacy_warning,
        convert_legacy_warnings_to_result,
        infer_validation_type,
    )
except ImportError:
    # Graceful fallback if Pydantic is not available
    pass

__all__ = [
    "ModelMetadata",
    "ModelType", 
    "ModelFile",
    "create_model_file",
    "ChunkInfo",
    "StreamingContext",
    "ValidationMetrics",
    "ValidationResult",
]
