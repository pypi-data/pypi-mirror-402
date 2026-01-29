"""Streaming validation coordinator for efficient multi-validator processing.

This module provides centralized coordination for streaming validation across
multiple validators, with memory management, progress tracking, and error handling.
"""

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterator, List, Optional

if TYPE_CHECKING:
    from typing import Callable

from palisade.models.model_file import ModelFile
from palisade.models.types import ChunkInfo, StreamingContext
from palisade.validators.base import BaseValidator

logger = logging.getLogger(__name__)


@dataclass
class StreamingConfig:
    """Configuration for streaming validation operations"""
    max_memory_mb: int = 512
    chunk_size: int = 1024 * 1024  # 1MB default
    max_concurrent_validators: int = 3
    progress_callback: Optional[Callable[["StreamingProgress"], None]] = None
    validator_completion_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
    enable_parallel_validation: bool = True
    chunk_timeout_seconds: int = 30


@dataclass
class StreamingProgress:
    """Progress tracking for streaming operations"""
    total_bytes: int
    bytes_processed: int
    chunks_processed: int
    validators_completed: int
    total_validators: int
    start_time: float
    current_chunk_size: int = 0

    @property
    def progress_percent(self) -> float:
        """Get overall progress as percentage"""
        if self.total_bytes == 0:
            return 100.0
        return (self.bytes_processed / self.total_bytes) * 100.0

    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds"""
        return time.time() - self.start_time

    @property
    def estimated_total_time(self) -> float:
        """Estimate total completion time"""
        if self.progress_percent == 0:
            return 0.0
        return self.elapsed_time * (100.0 / self.progress_percent)

    @property
    def processing_rate_mb_per_sec(self) -> float:
        """Get processing rate in MB/sec"""
        if self.elapsed_time == 0:
            return 0.0
        return (self.bytes_processed / (1024 * 1024)) / self.elapsed_time


class StreamingValidationCoordinator:
    """
    Coordinates streaming validation across multiple validators with memory management.

    Features:
    - Memory-bounded streaming processing
    - Parallel validator execution where safe
    - Progress tracking and callbacks
    - Error isolation and recovery
    - Resource cleanup
    """

    def __init__(
        self,
        validators: List[BaseValidator],
        config: Optional[StreamingConfig] = None
    ) -> None:
        """
        Initialize coordinator

        Args:
            validators: List of validators to coordinate
            config: Optional streaming configuration
        """
        self.validators = validators
        self.config = config or StreamingConfig()
        self.progress: Optional[StreamingProgress] = None
        self._results_lock = threading.Lock()
        self._accumulated_results: List[Dict[str, Any]] = []

    def validate_streaming(
        self,
        model_file: ModelFile,
        progress_callback: Optional[Callable[["StreamingProgress"], None]] = None
    ) -> Dict[str, Any]:
        """
        Coordinate streaming validation across all validators

        Args:
            model_file: ModelFile to validate
            progress_callback: Optional progress callback function

        Returns:
            Dict containing comprehensive validation results
        """
        start_time = time.time()

        # Initialize progress tracking
        self.progress = StreamingProgress(
            total_bytes=model_file.size_bytes,
            bytes_processed=0,
            chunks_processed=0,
            validators_completed=0,
            total_validators=len(self.validators),
            start_time=start_time
        )

        # Use provided callback or config callback
        callback = progress_callback or self.config.progress_callback

        # Determine optimal streaming approach
        streaming_approach = self._determine_streaming_approach(model_file)

        try:
            if streaming_approach == "parallel":
                return self._validate_parallel_streaming(model_file, callback)
            else:
                return self._validate_sequential_streaming(model_file, callback)

        except Exception as e:
            logger.error(f"Streaming validation failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "progress": self.progress.__dict__,
                "partial_results": self._accumulated_results.copy()
            }

    def _determine_streaming_approach(self, model_file: ModelFile) -> str:
        """Determine the best streaming approach based on validators and file characteristics"""

        # Check if validators support parallel execution
        if not self.config.enable_parallel_validation:
            return "sequential"

        # Check validator compatibility for parallel execution
        stateful_validators = []
        for validator in self.validators:
            # Check if validator maintains state across chunks
            if hasattr(validator, "requires_sequential_processing"):
                if validator.requires_sequential_processing():
                    stateful_validators.append(validator.__class__.__name__)

        if stateful_validators:
            logger.debug(f"Using sequential streaming due to stateful validators: {stateful_validators}")
            return "sequential"

        # Check memory constraints
        memory_estimate = model_file.estimate_streaming_memory_usage(len(self.validators))
        if memory_estimate["estimated_memory_mb"] > self.config.max_memory_mb:
            logger.debug("Using sequential streaming due to memory constraints")
            return "sequential"

        return "parallel"

    def _validate_sequential_streaming(
        self,
        model_file: ModelFile,
        progress_callback: Optional[Callable[["StreamingProgress"], None]]
    ) -> Dict[str, Any]:
        """Sequential streaming validation - safer but slower"""

        all_results = []
        validator_results = {}

        for validator_idx, validator in enumerate(self.validators):
            validator_name = validator.__class__.__name__
            start_time = time.time()
            
            try:
                logger.debug(f"Starting streaming validation with {validator_name}")

                # Run validator's streaming validation
                if hasattr(validator, "supports_streaming") and validator.supports_streaming():
                    validator_warnings = validator.validate_streaming(model_file)
                else:
                    # Fallback to chunk-based validation
                    validator_warnings = self._run_chunk_validation(validator, model_file)

                processing_time = time.time() - start_time
                validator_results[validator_name] = {
                    "warnings": validator_warnings,
                    "warning_count": len(validator_warnings),
                    "status": "completed",
                    "processing_time_seconds": processing_time
                }

                all_results.extend(validator_warnings)

                # Update progress
                if self.progress is not None:
                    self.progress.validators_completed = validator_idx + 1

                if progress_callback and self.progress is not None:
                    progress_callback(self.progress)

            except Exception as e:
                logger.error(f"Error in validator {validator_name}: {str(e)}")
                processing_time = time.time() - start_time
                validator_results[validator_name] = {
                    "warnings": [],
                    "warning_count": 0,
                    "status": "error",
                    "error": str(e),
                    "processing_time_seconds": processing_time
                }

        return {
            "status": "completed",
            "total_warnings": len(all_results),
            "all_warnings": all_results,
            "validator_results": validator_results,
            "progress": self.progress.__dict__,
            "streaming_stats": self._compute_streaming_stats()
        }

    def _validate_parallel_streaming(
        self,
        model_file: ModelFile,
        progress_callback: Optional[Callable[["StreamingProgress"], None]]
    ) -> Dict[str, Any]:
        """Parallel streaming validation - faster but requires compatible validators"""

        validator_results = {}

        with ThreadPoolExecutor(max_workers=min(len(self.validators), self.config.max_concurrent_validators)) as executor:
            # Submit validator tasks
            future_to_validator = {}

            for validator in self.validators:
                future = executor.submit(self._run_validator_streaming, validator, model_file)
                future_to_validator[future] = validator

            # Collect results as they complete
            for future in as_completed(future_to_validator, timeout=300):  # 5 minute timeout
                validator = future_to_validator[future]
                validator_name = validator.__class__.__name__

                try:
                    warnings, processing_time = future.result()
                    validator_results[validator_name] = {
                        "warnings": warnings,
                        "warning_count": len(warnings),
                        "status": "completed",
                        "processing_time_seconds": processing_time
                    }

                    with self._results_lock:
                        self._accumulated_results.extend(warnings)

                    # Update progress
                    if self.progress is not None:
                        self.progress.validators_completed += 1

                    if progress_callback and self.progress is not None:
                        progress_callback(self.progress)

                    # Notify completion callback if available
                    if self.config.validator_completion_callback:
                        self.config.validator_completion_callback(validator_name, validator_results[validator_name])

                except Exception as e:
                    logger.error(f"Validator {validator_name} failed: {str(e)}")
                    error_result = {
                        "warnings": [],
                        "warning_count": 0,
                        "status": "error",
                        "error": str(e)
                    }
                    validator_results[validator_name] = error_result

                    # Notify completion callback for error case too
                    if self.config.validator_completion_callback:
                        self.config.validator_completion_callback(validator_name, error_result)

        return {
            "status": "completed",
            "total_warnings": len(self._accumulated_results),
            "all_warnings": self._accumulated_results.copy(),
            "validator_results": validator_results,
            "progress": self.progress.__dict__,
            "streaming_stats": self._compute_streaming_stats()
        }

    def _run_validator_streaming(self, validator: BaseValidator, model_file: ModelFile) -> tuple[List[Dict[str, Any]], float]:
        """Run streaming validation for a single validator
        
        Returns:
            Tuple of (warnings, processing_time_seconds)
        """
        start_time = time.time()
        try:
            if hasattr(validator, "supports_streaming") and validator.supports_streaming():
                warnings = validator.validate_streaming(model_file)
            else:
                warnings = self._run_chunk_validation(validator, model_file)
            
            processing_time = time.time() - start_time
            return warnings, processing_time
        except Exception as e:
            logger.error(f"Error in validator streaming: {str(e)}")
            raise

    def _run_chunk_validation(self, validator: BaseValidator, model_file: ModelFile) -> List[Dict[str, Any]]:
        """Fallback chunk-based validation for validators without native streaming support"""
        warnings = []
        context = StreamingContext(total_size=model_file.size_bytes)
        context.validation_results = {}

        chunk_index = 0
        bytes_processed = 0

        try:
            with model_file as mf:
                for chunk_data in mf.iter_chunks(self.config.chunk_size):
                    chunk_info = ChunkInfo(
                        data=chunk_data,
                        offset=bytes_processed,
                        size=len(chunk_data),
                        chunk_index=chunk_index,
                        is_final=(bytes_processed + len(chunk_data) >= model_file.size_bytes)
                    )

                    # Validate chunk
                    chunk_warnings = validator.validate_chunk(chunk_info, context)
                    warnings.extend(chunk_warnings)

                    # Update progress
                    bytes_processed += len(chunk_data)
                    context.bytes_processed = bytes_processed
                    context.chunks_processed += 1
                    chunk_index += 1

                    # Update global progress for parallel processing
                    if hasattr(self, "progress") and self.progress:
                        self.progress.bytes_processed = max(self.progress.bytes_processed, bytes_processed)
                        self.progress.chunks_processed = max(self.progress.chunks_processed, chunk_index)
                        self.progress.current_chunk_size = len(chunk_data)

        except Exception as e:
            logger.error(f"Chunk validation failed for {validator.__class__.__name__}: {str(e)}")
            warnings.append({
                "type": f"{validator.__class__.__name__}_chunk_validation_error",
                "severity": "medium",
                "details": {
                    "message": f"Chunk validation error: {str(e)}",
                    "validator": validator.__class__.__name__
                }
            })

        return warnings

    def _compute_streaming_stats(self) -> Dict[str, Any]:
        """Compute streaming performance statistics"""
        if not self.progress:
            return {}

        return {
            "total_processing_time_sec": self.progress.elapsed_time,
            "processing_rate_mb_per_sec": self.progress.processing_rate_mb_per_sec,
            "total_chunks_processed": self.progress.chunks_processed,
            "average_chunk_size_kb": (self.progress.bytes_processed / max(self.progress.chunks_processed, 1)) / 1024,
            "memory_efficiency": {
                "peak_memory_estimate_mb": self.config.max_memory_mb,
                "file_size_mb": self.progress.total_bytes / (1024 * 1024),
                "efficiency_ratio": self.config.max_memory_mb / (self.progress.total_bytes / (1024 * 1024))
            }
        }

    @contextmanager
    def streaming_session(self, model_file: ModelFile) -> Iterator["StreamingValidationCoordinator"]:
        """Context manager for streaming validation sessions with proper cleanup"""
        session_start = time.time()
        logger.debug(f"Starting streaming validation session for {model_file.file_info.path}")

        try:
            # Setup session
            self.progress = StreamingProgress(
                total_bytes=model_file.size_bytes,
                bytes_processed=0,
                chunks_processed=0,
                validators_completed=0,
                total_validators=len(self.validators),
                start_time=session_start
            )

            yield self

        finally:
            # Cleanup
            session_duration = time.time() - session_start
            logger.debug(f"Streaming validation session completed in {session_duration:.2f}s")

            # Clear accumulated results
            self._accumulated_results.clear()
            self.progress = None


def create_streaming_coordinator(
    validators: List[BaseValidator],
    max_memory_mb: int = 512,
    enable_parallel: bool = True
) -> StreamingValidationCoordinator:
    """
    Factory function to create a streaming validation coordinator

    Args:
        validators: List of validators to coordinate
        max_memory_mb: Maximum memory usage limit
        enable_parallel: Whether to enable parallel validation

    Returns:
        StreamingValidationCoordinator instance
    """
    config = StreamingConfig(
        max_memory_mb=max_memory_mb,
        enable_parallel_validation=enable_parallel
    )

    return StreamingValidationCoordinator(validators, config)
