"""Enhanced scanner with streaming model file support.

This module provides an enhanced scanner that uses the new ModelFile abstraction
for memory-efficient processing of large ML models with streaming validation.

Key Features:
- Memory-safe processing of large models (70B+ parameters)
- Streaming validation for models that exceed memory limits
- Automatic format detection and validator selection
- Progress monitoring and resource management
- Policy-driven scanning with enhanced context
"""

import resource
import sys
import threading
import time
import traceback
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

if TYPE_CHECKING:
    from palisade._native import PyCedarPolicyEngine
from palisade.core.streaming_coordinator import (
    create_streaming_coordinator,
)
from palisade.models.metadata import ModelMetadata, ModelType
from palisade.models.model_file import ModelFile, create_model_file
from palisade.utils.logging import setup_logging
from palisade.validators.base import BaseValidator

logger = setup_logging()


class ProgressSpinner:
    """Simple progress spinner for validator execution."""

    def __init__(self, message: str) -> None:
        self.message = message
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧"]
        self.idx = 0
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.start_time = time.time()

    def _spin(self) -> None:
        """Internal spinning method."""
        while self.running:
            elapsed = time.time() - self.start_time
            sys.stdout.write(f"\r{self.spinner_chars[self.idx]} {self.message} ({elapsed:.1f}s)")
            sys.stdout.flush()
            self.idx = (self.idx + 1) % len(self.spinner_chars)
            time.sleep(0.1)

    def start(self) -> None:
        """Start the spinner."""
        if not sys.stdout.isatty():
            # Don't show spinner in non-interactive environments
            print(f"⚙️ {self.message}")
            return

        self.running = True
        self.thread = threading.Thread(target=self._spin)
        self.thread.daemon = True
        self.thread.start()

    def stop(self, success: bool = True, result_msg: str = "") -> None:
        """Stop the spinner with result."""
        if not sys.stdout.isatty():
            if result_msg:
                print(f"   {result_msg}")
            return

        self.running = False
        if self.thread:
            self.thread.join(timeout=0.2)

        elapsed = time.time() - self.start_time
        status_char = "✅" if success else "❌"
        sys.stdout.write(f"\r{status_char} {self.message} ({elapsed:.1f}s)")
        if result_msg:
            sys.stdout.write(f" - {result_msg}")
        sys.stdout.write("\n")
        sys.stdout.flush()


class EnhancedModelScanner:
    """Enhanced model scanner with streaming support and memory management.

    Features:
    - Automatic streaming for large models
    - Memory usage monitoring
    - Progress tracking
    - Format-specific validation
    - Policy integration with enhanced context
    """

    def __init__(
        self,
        max_memory_mb: int = 512,
        chunk_size_mb: int = 1,
        enable_streaming: bool = True,
        policy_engine: Optional["PyCedarPolicyEngine"] = None,
    ) -> None:
        """Initialize enhanced scanner.

        Args:
        ----
            max_memory_mb: Maximum memory usage in MB (default 512MB)
            chunk_size_mb: Chunk size for streaming in MB (default 1MB)
            enable_streaming: Whether to enable streaming for large files
            policy_engine: Optional policy engine for evaluation
        """
        self.max_memory_mb = max_memory_mb
        self.chunk_size = chunk_size_mb * 1024 * 1024
        self.enable_streaming = enable_streaming
        self.policy_engine = policy_engine
        self.policy_environment = "default"  # Can be set by caller

        # Statistics
        self.stats = {
            "files_scanned": 0,
            "total_bytes_processed": 0,
            "validation_errors": 0,
            "total_warnings": 0,
            "peak_memory_mb": 0.0,
        }

    def scan_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Scan a single model file with enhanced processing.

        Args:
        ----
            file_path: Path to the model file

        Returns:
        -------
            Dict containing comprehensive scan results
        """
        start_time = time.time()
        file_path = Path(file_path)
        
        # Track memory before scan (ru_maxrss is in KB on Linux, bytes on macOS)
        mem_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

        try:
            # Create model file abstraction with Git LFS resolution enabled
            model_file = create_model_file(
                file_path,
                max_memory_mb=self.max_memory_mb,
                chunk_size=self.chunk_size,
                resolve_git_lfs=True,
            )

            # Get comprehensive file information
            file_info = model_file.file_info
            metadata = model_file.get_metadata()

            # Update statistics
            self.stats["files_scanned"] += 1
            self.stats["total_bytes_processed"] += model_file.size_bytes

            # File processing info (unused but kept for potential future use)
            # processing_info = {
            #     "file_size_mb": model_file.size_mb,
            #     "format": str(model_file.format) if model_file.format else "unknown",
            # }

            # Check if this was originally a Git LFS pointer file
            original_lfs_info = None
            if model_file.is_git_lfs_pointer:
                original_lfs_info = model_file.git_lfs_info

            # Skip if not a target model format (and couldn't be resolved)
            if model_file.format is not None and model_file.format in [ModelType.UNKNOWN, ModelType.NON_TARGET]:
                if original_lfs_info:
                    reason = f"Git LFS pointer file for {original_lfs_info['extension']} ({original_lfs_info.get('size_gb', 0):.1f}GB) - could not resolve"
                else:
                    reason = f"Not a target model format: {model_file.format}"

                result = {
                    "file_path": str(file_path),
                    "status": "skipped",
                    "reason": reason,
                    "file_info": file_info.__dict__,
                    "scan_time_seconds": time.time() - start_time,
                }

                # Include LFS info if available
                if original_lfs_info:
                    result["git_lfs_info"] = original_lfs_info

                return result

            # Get appropriate validators
            validators = self._get_validators_for_model(model_file)
            if not validators:
                return {
                    "file_path": str(file_path),
                    "status": "no_validators",
                    "reason": f"No validators available for format: {str(model_file.format) if model_file.format else 'unknown'}",
                    "file_info": file_info.__dict__,
                    "scan_time_seconds": time.time() - start_time,
                }

            # Run validation with enhanced streaming coordinator
            all_warnings = []
            validation_results = []

            # Determine if we should use streaming coordination
            if model_file.should_stream() or self.enable_streaming:
                print("Using streaming validation ...")
                # Create completion callback to show individual validator progress
                def validator_completion_callback(validator_name: str, result: Dict[str, Any]) -> None:
                    # Clean up validator names for display
                    display_name = validator_name.replace("Validator", "").replace("Security", "").replace("Detection", "")
                    display_name = display_name.replace("Analysis", "").replace("Hygiene", "").replace("Integrity", "")

                    if result["status"] == "completed":
                        warning_count = result.get("warning_count", 0)
                        processing_time = result.get("processing_time_seconds", 0)
                        time_str = f" ({processing_time:.2f}s)" if processing_time > 0 else ""
                        
                        if warning_count > 0:
                            print(f"✅ {display_name} - {warning_count} warnings found{time_str}")
                        else:
                            print(f"✅ {display_name} - Clean{time_str}")
                    else:
                        error_msg = result.get("error", "Unknown error")
                        processing_time = result.get("processing_time_seconds", 0)
                        time_str = f" ({processing_time:.2f}s)" if processing_time > 0 else ""
                        print(f"❌ {display_name} - Error: {error_msg[:50]}{'...' if len(error_msg) > 50 else ''}{time_str}")

                # Use streaming coordinator for large files
                coordinator = create_streaming_coordinator(
                    validators=validators,
                    max_memory_mb=self.max_memory_mb,
                    enable_parallel=True
                )

                # Add the completion callback to the coordinator's config
                coordinator.config.validator_completion_callback = validator_completion_callback

                # Show initial message
                print("🔍 Running security validators...")

                # Don't use progress callback to avoid messy output
                progress_callback = None

                try:
                    streaming_results = coordinator.validate_streaming(model_file, progress_callback)

                    # Process streaming results
                    if streaming_results["status"] == "completed":

                        all_warnings.extend(streaming_results["all_warnings"])
                        self.stats["total_warnings"] += streaming_results["total_warnings"]

                        # Convert validator results to structured format (completion already shown by callback)
                        for validator_name, result in streaming_results["validator_results"].items():
                            if result["status"] == "completed":
                                from palisade.models.validation_result import ValidationResult, ValidationMetrics
                                val_result = ValidationResult(validator_name=validator_name)
                                
                                # Add processing time to metrics
                                processing_time = result.get("processing_time_seconds", 0)
                                val_result.metrics = ValidationMetrics(
                                    start_time=0,
                                    end_time=processing_time,
                                    processing_time_seconds=processing_time,
                                    mode="streaming"
                                )
                                
                                for warning in result["warnings"]:
                                    val_result.add_warning(
                                        warning_type=warning.get("type", "unknown"),
                                        severity=warning.get("severity", "medium"),
                                        message=warning.get("details", {}).get("message", "No details"),
                                        details=warning.get("details", {}),
                                        recommendation=warning.get("details", {}).get("recommendation")
                                    )
                                validation_results.append(val_result.to_dict())
                            else:
                                # Handle validator errors
                                self.stats["validation_errors"] += 1
                                all_warnings.append({
                                    "type": "validation_error",
                                    "details": {
                                        "message": f"Validator {validator_name} failed: {result.get('error', 'Unknown error')}",
                                        "validator": validator_name,
                                        "recommendation": "Manual review recommended",
                                    },
                                    "severity": "medium",
                                })

                        # Show final validation summary
                        stats = streaming_results.get("streaming_stats", {})
                        rate = stats.get("processing_rate_mb_per_sec", 0)
                        total_warnings = streaming_results["total_warnings"]
                        if total_warnings > 0:
                            if rate > 0:
                                print(f"📊 Validation complete - {total_warnings} warnings found ({rate:.1f} MB/s)")
                            else:
                                print(f"📊 Validation complete - {total_warnings} warnings found")
                        else:
                            if rate > 0:
                                print(f"📊 Validation complete - No issues found ({rate:.1f} MB/s)")
                            else:
                                print("📊 Validation complete - No issues found")

                    else:
                        raise Exception(f"Parallel validation failed: {streaming_results.get('error', 'Unknown error')}")

                except Exception as e:
                    logger.error(f"Streaming validation failed: {str(e)}")
                    logger.error(f"\n{'='*60}")
                    logger.error(f"STREAMING VALIDATION EXCEPTION:")
                    logger.error(f"{'='*60}")
                    traceback.print_exc()
                    logger.error(f"{'='*60}\n")
                    
                    # Add error to warnings
                    self.stats["validation_errors"] += 1
                    all_warnings.append({
                        "type": "streaming_validation_error",
                        "details": {
                            "message": f"Streaming validation failed: {str(e)}",
                            "recommendation": "Try non-streaming validation or check file integrity",
                            "exception_type": type(e).__name__,
                        },
                        "severity": "high",
                    })

            else:
                # Use individual validator processing for smaller files (non-streaming mode)
                print("🔍 Running security validators...")
                for validator in validators:
                    validator_name = validator.__class__.__name__
                    display_name = validator_name.replace("Validator", "").replace("Security", "").replace("Detection", "")
                    display_name = display_name.replace("Analysis", "").replace("Hygiene", "").replace("Integrity", "")
                    spinner = ProgressSpinner(f"Running {display_name}")
                    spinner.start()
                    
                    start_time = time.time()
                    try:
                        validation_result = validator.validate_file_with_structured_result(model_file)
                        processing_time = time.time() - start_time

                        # Convert to standard warnings
                        standard_warnings = validation_result.warnings
                        all_warnings.extend(standard_warnings)
                        self.stats["total_warnings"] += len(standard_warnings)
                        validation_results.append(validation_result.to_dict())

                        # Stop spinner with success and show timing
                        time_str = f" ({processing_time:.2f}s)"
                        if len(standard_warnings) > 0:
                            spinner.stop(success=True, result_msg=f"{len(standard_warnings)} warnings found{time_str}")
                        else:
                            spinner.stop(success=True, result_msg=f"Clean{time_str}")

                    except Exception as e:
                        self._handle_validator_error(e, validator_name, spinner, all_warnings, validation_results)

            # Deduplicate warnings to reduce JSON bloat
            deduplicated_warnings = self._deduplicate_warnings(all_warnings)

            # Determine overall status
            critical_warnings = [w for w in all_warnings if w.get("severity") == "critical"]
            high_warnings = [w for w in all_warnings if w.get("severity") == "high"]

            if critical_warnings:
                status = "critical"
            elif high_warnings:
                status = "suspicious"
            elif all_warnings:
                status = "warnings"
            else:
                status = "clean"

            # Clean metadata to avoid redundancy with file_info
            if metadata:
                # Convert metadata to dict and remove redundant fields
                metadata_dict = metadata.to_dict() if hasattr(metadata, 'to_dict') else metadata.__dict__.copy()
                metadata_dict.pop("file_info", None)  # Already in file_info
                metadata_dict.pop("size_bytes", None)  # Already in file_info
                metadata_dict.pop("size_mb", None)    # Calculable from size_bytes
                metadata = metadata_dict

            # Build clean result without empty/null fields
            result = {
                "file_path": str(file_path),
                "status": status,
                "file_info": file_info.to_dict(),
            }

            # Include Git LFS information if this was originally an LFS pointer file
            if original_lfs_info:
                result["git_lfs_info"] = {
                    **original_lfs_info,
                    "resolved": True,
                    "original_size_bytes": original_lfs_info.get("actual_size_bytes", 0),
                    "resolved_size_bytes": model_file.size_bytes,
                }

            # Only include non-empty metadata
            if metadata:
                result["metadata"] = metadata

            # Only include validation results if present
            if validation_results:
                result["validation_results"] = validation_results

            # Only include warnings if present
            if deduplicated_warnings:
                result["warnings"] = deduplicated_warnings

            # Build summary with only meaningful fields
            summary = {
                "validators_run": len(validators),
                "scan_time_seconds": time.time() - start_time,
            }

            total_warnings = len(all_warnings)
            unique_warnings = len(deduplicated_warnings)

            if total_warnings > 0:
                summary["total_warnings"] = total_warnings
                summary["unique_warnings"] = unique_warnings  # Always include for proper reporting

            if critical_warnings:
                summary["critical_warnings"] = len(critical_warnings)

            if high_warnings:
                summary["high_warnings"] = len(high_warnings)

            # Track memory usage (ru_maxrss is in KB on Linux, bytes on macOS)
            mem_after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            # On Linux, ru_maxrss is in KB; on macOS it's in bytes
            # We detect by checking if value is unreasonably large for KB
            if mem_after > 1_000_000_000:  # Likely bytes (macOS)
                memory_used_mb = (mem_after - mem_before) / (1024 * 1024)
                peak_memory_mb = mem_after / (1024 * 1024)
            else:  # Likely KB (Linux)
                memory_used_mb = (mem_after - mem_before) / 1024
                peak_memory_mb = mem_after / 1024
            
            summary["memory_used_mb"] = round(max(0, memory_used_mb), 2)
            summary["peak_memory_mb"] = round(peak_memory_mb, 2)
            
            # Update global stats with peak memory (keep highest)
            if peak_memory_mb > self.stats["peak_memory_mb"]:
                self.stats["peak_memory_mb"] = peak_memory_mb

            result["summary"] = summary

            # Apply policy evaluation if policy engine is configured
            if self.policy_engine:
                logger.info(f"Applying policy evaluation (environment: {self.policy_environment})")
                from palisade.core.policy import PolicyEffect, evaluate_finding, aggregate_effects
                
                # Wrap single file result in a structure similar to scan results
                file_effects = []
                for warning in deduplicated_warnings:
                    # Build context for policy evaluation
                    context = {
                        "artifact": {
                            "format": str(model_file.format) if model_file.format else "unknown",
                            "path": str(file_path),
                            "signed": False,  # Default, can be overridden from metadata
                        },
                        "environment": self.policy_environment,
                        "model_path": str(file_path),
                    }
                    
                    # Add metadata fields if available
                    if metadata:
                        if "signed" in metadata:
                            context["artifact"]["signed"] = metadata["signed"]
                        if "provenance" in metadata:
                            context["provenance"] = metadata["provenance"]
                        if "metadata" in metadata:
                            context["metadata"] = metadata["metadata"]
                    
                    # Evaluate this finding
                    effect = evaluate_finding(self.policy_engine, warning, context)
                    warning["policy_effect"] = effect
                    file_effects.append(effect)
                
                # Add policy summary to result
                result["policy"] = {
                    "overall_effect": aggregate_effects(file_effects) if file_effects else PolicyEffect.ALLOW,
                    "environment": self.policy_environment,
                    "summary": {
                        "denied_files": 1 if aggregate_effects(file_effects) == PolicyEffect.DENY else 0,
                        "quarantined_files": 1 if aggregate_effects(file_effects) == PolicyEffect.QUARANTINE else 0,
                        "allowed_files": 1 if aggregate_effects(file_effects) == PolicyEffect.ALLOW else 0,
                    }
                }
                logger.info(f"Policy evaluation complete - Overall effect: {result['policy']['overall_effect']}")

            return result

        except Exception as e:
            logger.error(f"Error scanning {file_path}: {str(e)}")
            self.stats["validation_errors"] += 1

            return {
                "file_path": str(file_path),
                "status": "error",
                "error": str(e),
                "scan_time_seconds": time.time() - start_time,
                "warnings": [{
                    "type": "scan_error",
                    "details": {
                        "message": f"Failed to scan file: {str(e)}",
                        "recommendation": "Check file accessibility and format",
                    },
                    "severity": "high",
                }],
            }

    def _get_validators_for_model(self, model_file: ModelFile) -> List:
        """Get appropriate validators for the model format.

        Args:
        ----
            model_file: ModelFile instance

        Returns:
        -------
            List of validator instances
        """
        validators = []

        try:
            # Import all validators
            from palisade.validators.backdoor import BackdoorDetectionValidator

            # Import behavioral backdoor detection validators
            from palisade.validators.behavior_analysis import BehaviorAnalysisValidator
            from palisade.validators.buffer_overflow import BufferOverflowValidator
            from palisade.validators.decompression_bomb import DecompressionBombValidator
            from palisade.validators.metadata_security import MetadataSecurityValidator
            from palisade.validators.model_genealogy import ModelGenealogyValidator
            from palisade.validators.model_integrity import ModelIntegrityValidator
            from palisade.validators.provenance_security import ProvenanceSecurityValidator
            from palisade.validators.supply_chain import SupplyChainValidator
            from palisade.validators.tokenizer_hygiene import TokenizerHygieneValidator
            from palisade.validators.tool_call_security import ToolCallSecurityValidator

            # Universal validators that run on all model types
            metadata = self._create_metadata(model_file)

            # Helper function to safely create validators
            def create_validator(validator_class: type, metadata: ModelMetadata, policy_engine: Optional["PyCedarPolicyEngine"]) -> Optional[BaseValidator]:
                try:
                    # Try with policy engine first
                    return validator_class(metadata, policy_engine)
                except TypeError:
                    try:
                        # Try without policy engine
                        return validator_class(metadata)
                    except TypeError:
                        # Some validators might not need metadata
                        return validator_class()

            # Start with universal validators that run on all model types
            validators = [
                create_validator(BufferOverflowValidator, metadata, self.policy_engine),
                create_validator(MetadataSecurityValidator, metadata, self.policy_engine),
                create_validator(ModelIntegrityValidator, metadata, self.policy_engine),
                create_validator(ModelGenealogyValidator, metadata, self.policy_engine),
                create_validator(ProvenanceSecurityValidator, metadata, self.policy_engine),
                create_validator(SupplyChainValidator, metadata, self.policy_engine),
                create_validator(TokenizerHygieneValidator, metadata, self.policy_engine),
                create_validator(DecompressionBombValidator, metadata, self.policy_engine),
                # BEHAVIORAL BACKDOOR DETECTION VALIDATORS
                create_validator(BehaviorAnalysisValidator, metadata, self.policy_engine),
                create_validator(ToolCallSecurityValidator, metadata, self.policy_engine),
            ]

            # Add format-specific validators
            if model_file.format == ModelType.SAFETENSORS:
                from palisade.validators.safetensors_integrity import SafetensorsIntegrityValidator
                validators.extend([
                    create_validator(SafetensorsIntegrityValidator, metadata, self.policy_engine),
                    create_validator(BackdoorDetectionValidator, metadata, self.policy_engine),
                ])

            elif model_file.format == ModelType.GGUF:
                from palisade.validators.gguf_safety import GGUFSafetyValidator
                validators.append(
                    create_validator(GGUFSafetyValidator, metadata, self.policy_engine),
                )

            elif model_file.format in [ModelType.PYTORCH, ModelType.DILL]:
                from palisade.validators.pickle_security import PickleSecurityValidator
                validators.append(
                    create_validator(PickleSecurityValidator, metadata, self.policy_engine),
                )

            # Add LoRA adapter validator for supported formats
            if model_file.format in [ModelType.SAFETENSORS, ModelType.PYTORCH]:
                from palisade.validators.lora_adapter_security import LoRAAdapterSecurityValidator
                validators.append(
                    create_validator(LoRAAdapterSecurityValidator, metadata, self.policy_engine),
                )

        except ImportError as e:
            logger.warning(f"Failed to import validator: {str(e)}")

        return validators

    def _create_metadata(self, model_file: ModelFile) -> ModelMetadata:
        """Create ModelMetadata from ModelFile.

        Args:
        ----
            model_file: ModelFile instance

        Returns:
        -------
            ModelMetadata instance
        """
        return ModelMetadata(
            model_type=model_file.format or ModelType.UNKNOWN,
            framework_version="unknown",
            num_parameters=None,
            input_shape=None,
            output_shape=None,
            architecture=None,
            is_quantized=False,
            is_distributed=False,
        )

    def scan_directory(self, directory_path: Union[str, Path], recursive: bool = True) -> Dict[str, Any]:
        """Scan all model files in a directory.

        Args:
        ----
            directory_path: Path to directory to scan
            recursive: Whether to scan subdirectories

        Returns:
        -------
            Dict containing directory scan results
        """
        directory_path = Path(directory_path)
        start_time = time.time()

        if not directory_path.exists() or not directory_path.is_dir():
            return {
                "directory": str(directory_path),
                "status": "error",
                "error": "Directory not found or not a directory",
                "files": [],
                "summary": {"total_files": 0, "scan_time_seconds": 0},
            }

        # Find model files (weights + tokenizers + critical config)
        model_extensions = {".safetensors", ".gguf", ".bin", ".pt", ".pth", ".onnx", ".h5", ".pkl", ".pickle"}
        
        # Import tokenizer filenames from constants
        from palisade.core.constants import EXPECTED_TOKENIZER_FILES
        
        # Also scan tokenizer.model (SentencePiece) by extension
        model_extensions.add(".model")
        
        if recursive:
            model_files_set = set()  # Use set to avoid duplicates
            # Scan by extension
            for ext in model_extensions:
                model_files_set.update(directory_path.rglob(f"*{ext}"))
            
            # Also scan specific tokenizer filenames (e.g., tokenizer.json, vocab.txt)
            for tokenizer_file in EXPECTED_TOKENIZER_FILES:
                model_files_set.update(directory_path.rglob(tokenizer_file))
            
            model_files = sorted(model_files_set)  # Sort for consistent ordering
        else:
            model_files_set = set()
            for f in directory_path.iterdir():
                if not f.is_file():
                    continue
                # Match by extension or by specific tokenizer filename
                if f.suffix.lower() in model_extensions or f.name in EXPECTED_TOKENIZER_FILES:
                    model_files_set.add(f)
            
            model_files = sorted(model_files_set)  # Sort for consistent ordering

        # Scan each file
        results = []
        for i, file_path in enumerate(model_files, 1):
            # Show which file is being processed
            if len(model_files) > 1:
                print(f"\n📄 Processing file {i}/{len(model_files)}: {file_path.name}")
                print("-" * 50)

            result = self.scan_file(file_path)
            results.append(result)

        # Create initial scan results
        scan_results: Dict[str, Any] = {
            "directory": str(directory_path),
            "status": "completed",
            "files": results,
            "summary": {
                "total_files": len(results),
                "clean_files": len([r for r in results if r.get("status") == "clean"]),
                "suspicious_files": len([r for r in results if r.get("status") in ["warnings", "suspicious"]]),
                "critical_files": len([r for r in results if r.get("status") == "critical"]),
                "error_files": len([r for r in results if r.get("status") == "error"]),
                "scan_time_seconds": time.time() - start_time,
                "total_bytes_scanned": sum(r.get("file_info", {}).get("size_bytes", 0) for r in results),
            },
            "scanner_stats": self.stats.copy(),
        }

        # Apply policy evaluation to final results
        if self.policy_engine:
            logger.info(f"Applying policy evaluation (environment: {self.policy_environment})")
            from palisade.core.policy import PolicyEffect, evaluate_finding, aggregate_effects
            
            # Evaluate each file's findings
            for file_result in scan_results.get("files", []):
                file_effects = []
                for val_result in file_result.get("validation_results", []):
                    for finding in val_result.get("warnings", []):
                        # Build comprehensive context for this finding
                        metadata = file_result.get("metadata", {})
                        
                        context = {
                            "artifact": {
                                "format": metadata.get("model_type", "unknown"),
                                "path": file_result.get("file_path", "unknown"),
                                "signed": metadata.get("signed", False),
                            },
                            "metadata": metadata,
                            "environment": self.policy_environment,
                        }
                        
                        # Add provenance if available (from metadata or validation results)
                        if "provenance" in metadata:
                            context["provenance"] = metadata["provenance"]
                        
                        effect = evaluate_finding(self.policy_engine, finding, context)
                        finding["policy_effect"] = effect
                        file_effects.append(effect)
                
                # Aggregate to file level
                file_result["policy_effect"] = aggregate_effects(file_effects)
            
            # Aggregate to scan level
            scan_effects = [f.get("policy_effect", PolicyEffect.ALLOW) for f in scan_results.get("files", [])]
            scan_results["policy"] = {
                "overall_effect": aggregate_effects(scan_effects),
                "environment": self.policy_environment,
                "summary": {
                    "denied_files": scan_effects.count(PolicyEffect.DENY),
                    "quarantined_files": scan_effects.count(PolicyEffect.QUARANTINE),
                    "allowed_files": scan_effects.count(PolicyEffect.ALLOW),
                }
            }
            logger.info(f"Policy integration complete - Overall action: {scan_results.get('policy', {}).get('overall_action', 'ALLOW')}")

        return scan_results

    def get_scanner_stats(self) -> Dict[str, Any]:
        """Get scanner statistics.

        Returns
        -------
            Dict with scanner performance statistics
        """
        return {
            **self.stats,
        }

    def reset_stats(self) -> None:
        """Reset scanner statistics."""
        self.stats = {
            "files_scanned": 0,
            "total_bytes_processed": 0,
            "validation_errors": 0,
            "total_warnings": 0,
            "peak_memory_mb": 0.0,
        }

    def _handle_validator_error(self, error: Exception, validator_name: str, spinner: ProgressSpinner, all_warnings: List[Dict[str, Any]], validation_results: List[Dict[str, Any]]) -> None:
        """Handle validator errors consistently.

        Args:
            error: The exception that occurred
            validator_name: Name of the validator that failed
            spinner: Progress spinner to stop
            all_warnings: List to append error warning to
            validation_results: List to append error result to
        """
        # Stop spinner with error
        error_msg = str(error)
        spinner.stop(success=False, result_msg=f"Error: {error_msg[:50]}{'...' if len(error_msg) > 50 else ''}")

        # Get full stack trace for debugging
        tb_str = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        
        # Log error with full stack trace
        logger.error(f"Error in {validator_name}: {error_msg}")
        logger.error(f"Full stack trace for {validator_name}:\n{tb_str}")
        
        self.stats["validation_errors"] += 1

        # Create error validation result
        from palisade.models.validation_result import ValidationResult, ValidationMetrics
        error_result = ValidationResult(validator_name=validator_name)
        
        # Add error metrics
        error_result.metrics = ValidationMetrics(
            start_time=0,
            end_time=0,
            processing_time_seconds=0,
            mode="error"
        )
        
        error_result.set_error(error_msg, {
            "exception_type": type(error).__name__,
            "stack_trace": tb_str  # Include stack trace in metadata
        })
        validation_results.append(error_result.to_dict())

        # Add error as warning
        all_warnings.append({
            "type": "validation_error",
            "details": {
                "message": f"Validator {validator_name} failed: {error_msg}",
                "validator": validator_name,
                "recommendation": "Manual review recommended",
                "exception_type": type(error).__name__,
            },
            "severity": "medium",
        })

    def _deduplicate_warnings(self, warnings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate identical warnings and add occurrence counts.

        Args:
            warnings: List of warning dictionaries

        Returns:
            List of deduplicated warnings with occurrence counts
        """
        # Create a key for each warning based on type, severity, and core message
        warning_counts = {}
        warning_examples = {}

        for warning in warnings:
            # Create a unique key for this warning type
            warning_type = warning.get("type", "unknown")
            severity = warning.get("severity", "unknown")
            details = warning.get("details", {})

            # Extract core message (without dynamic parts like specific patterns)
            core_message = details.get("message", "")
            recommendation = details.get("recommendation", "")

            # Create key for grouping similar warnings
            key = f"{warning_type}|{severity}|{core_message}|{recommendation}"

            if key not in warning_counts:
                warning_counts[key] = 0
                warning_examples[key] = warning.copy()  # Store first example

            warning_counts[key] += 1

            # Merge patterns/data from multiple occurrences
            if "patterns" in details and "patterns" in warning_examples[key].get("details", {}):
                existing_patterns = set(warning_examples[key]["details"].get("patterns", []))
                new_patterns = set(details.get("patterns", []))
                combined_patterns = list(existing_patterns.union(new_patterns))
                warning_examples[key]["details"]["patterns"] = combined_patterns[:20]  # Limit to 20 unique patterns

        # Build deduplicated warning list
        deduplicated = []
        for key, count in warning_counts.items():
            warning = warning_examples[key].copy()

            # Add occurrence count to the warning
            warning["occurrence_count"] = count

            # Update details if there were multiple occurrences
            if count > 1:
                details = warning.get("details", {}).copy()

                # Update message to indicate multiple occurrences
                base_message = details.get("message", "")
                if "patterns detected" in base_message:
                    details["message"] = f"{base_message} (found {count} times)"
                elif "detected" in base_message:
                    details["message"] = f"{base_message} (found {count} times)"
                else:
                    details["message"] = f"{base_message} (occurred {count} times)"

                # Update total pattern count if applicable
                if "total_patterns" in details:
                    details["initial_pattern_count"] = details["total_patterns"]
                    details["total_patterns"] = len(details.get("patterns", []))

                warning["details"] = details

            deduplicated.append(warning)

        # Sort by severity and occurrence count
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
        deduplicated.sort(key=lambda w: (
            severity_order.get(w.get("severity", "low"), 0),
            w.get("occurrence_count", 1)
        ), reverse=True)

        return deduplicated

