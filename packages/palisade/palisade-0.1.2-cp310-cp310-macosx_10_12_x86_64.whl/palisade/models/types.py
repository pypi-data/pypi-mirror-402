"""Type definitions for streaming validation.

This module defines data structures used in streaming validation operations.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ChunkInfo:
    """Information about a data chunk during streaming validation."""
    
    data: bytes
    offset: int
    size: int
    chunk_index: int
    is_final: bool = False
    
    @property
    def end_offset(self) -> int:
        """Get the end offset of this chunk."""
        return self.offset + self.size


@dataclass
class StreamingContext:
    """Context information for streaming validation operations."""
    
    total_size: int
    bytes_processed: int = 0
    chunks_processed: int = 0
    validation_results: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def progress_percent(self) -> float:
        """Get progress as percentage."""
        if self.total_size == 0:
            return 100.0
        return (self.bytes_processed / self.total_size) * 100.0
    
    @property
    def is_complete(self) -> bool:
        """Check if streaming is complete."""
        return self.bytes_processed >= self.total_size
    
    def add_result(self, validator_name: str, result: Any) -> None:
        """Add a validation result."""
        if "results" not in self.validation_results:
            self.validation_results["results"] = {}
        self.validation_results["results"][validator_name] = result
    
    def get_result(self, validator_name: str) -> Optional[Any]:
        """Get a validation result."""
        return self.validation_results.get("results", {}).get(validator_name)
    
    def update_metadata(self, key: str, value: Any) -> None:
        """Update metadata."""
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value."""
        return self.metadata.get(key, default)
