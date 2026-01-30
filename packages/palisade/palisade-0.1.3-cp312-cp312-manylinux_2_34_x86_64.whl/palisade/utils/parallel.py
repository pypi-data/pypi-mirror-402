"""Parallel scanning utilities for large models."""

import importlib
import logging
import os
from concurrent.futures import ProcessPoolExecutor
from typing import Any, Dict, List, Optional, Type, Union

import psutil
from tqdm import tqdm

from palisade.models.metadata import ModelMetadata
from palisade.validators.base import BaseValidator

logger = logging.getLogger(__name__)

class ScanProgress:
    """Progress tracking for parallel scanning."""

    def __init__(self, total_validators: int) -> None:
        self.total = total_validators
        self.completed = 0
        self.warnings = []
        self.errors = []

    def update(self, validator_name: str, result: List[Dict[str, Any]], error: Optional[Exception] = None) -> None:
        """Update progress with validator results."""
        self.completed += 1
        if error:
            self.errors.append({
                "validator": validator_name,
                "error": str(error),
            })
        else:
            self.warnings.extend(result)

        # Log progress
        logger.debug(f"Completed {self.completed}/{self.total} validators: {validator_name}")
        if error:
            logger.error(f"Error in {validator_name}: {str(error)}")
        elif result:
            logger.info(f"Found {len(result)} warnings in {validator_name}\n")

def run_validator_in_process(validator_class_name: str, metadata: Dict[str, Any], data: Union[bytes, Dict[str, Any]], policy_config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Run a validator in a separate process.

    Args:
    ----
        validator_class_name: The name of the validator class to instantiate
        metadata: Model metadata as a dictionary
        data: Raw model data (bytes) or dictionary of tensors

    Returns:
    -------
        List of validation warnings
    """
    try:
        logger.debug(f"Starting validator {validator_class_name}")

        # Import the validator class
        validators_module = importlib.import_module("palisade.validators")
        validator_class = getattr(validators_module, validator_class_name)
        if not validator_class:
            msg = f"Validator class {validator_class_name} not found"
            raise ValueError(msg)

        # Create ModelMetadata object
        model_metadata = ModelMetadata(**metadata)

        # Create policy engine if config provided
        policy_engine = None
        if policy_config:
            try:
                from palisade.core.policy import PyCedarPolicyEngine
                policy_engine = PyCedarPolicyEngine()
                if "policy_path" in policy_config:
                    policy_engine.load_policies_from_file(policy_config["policy_path"])
            except Exception as e:
                logger.warning(f"Could not create policy engine: {e}")

        # Create validator instance
        validator = validator_class(model_metadata, policy_engine)

        # Handle both bytes and tensor data
        if isinstance(data, dict):
            logger.info(f"Processing {len(data)} tensors")
            result = validator.validate_tensors(data)
        else:
            logger.debug("Processing raw bytes data")
            result = validator.validate(data)

        logger.debug(f"Completed validator {validator_class_name} with {len(result)} warnings")
        return result
    except Exception as e:
        logger.error(f"Error in validator {validator_class_name}: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {str(e)}")
        msg = f"Validator {validator_class_name} failed: {str(e)}"
        raise RuntimeError(msg) from e

def get_resource_usage() -> Dict[str, Any]:
    """Get current process memory and CPU usage."""
    process = psutil.Process()
    mem_mb = process.memory_info().rss / 1024 / 1024
    cpu_percent = process.cpu_percent(interval=None)
    return {"mem_mb": mem_mb, "cpu_percent": cpu_percent}

def parallel_scan(
    data: bytes,
    metadata: Any,
    validators: List[Type[BaseValidator]],
    max_workers: int = None,
    show_progress: bool = True,
    chunk_info: Optional[Dict[str, Any]] = None,
    policy_config: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Run validators in parallel.

    Args:
    ----
        data: Model data to scan
        metadata: Model metadata
        validators: List of validator classes to run
        max_workers: Maximum number of worker processes
        show_progress: Whether to show progress bar
        chunk_info: Information about the current chunk being processed

    Returns:
    -------
        List of warnings from all validators
    """
    if max_workers is None:
        max_workers = min(os.cpu_count() or 1, 8)  # Cap at 8 workers

    warnings = []
    futures = []

    # Create progress bar
    if show_progress:
        if chunk_info:
            pbar = tqdm(
                total=len(validators),
                desc=f"Scanning chunk {chunk_info['number']} ({chunk_info['size'] / (1024*1024):.1f}MB)",
                unit="validator",
            )
        else:
            pbar = tqdm(total=len(validators), desc="Scanning", unit="validator")

    # Convert metadata to dict if it's a ModelMetadata object
    metadata_dict = metadata.__dict__ if hasattr(metadata, "__dict__") else metadata

    # Submit validation tasks
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        for validator_class in validators:
            future = executor.submit(
                run_validator_in_process,
                validator_class.__name__,
                metadata_dict,
                data,
                policy_config,
            )
            futures.append((future, validator_class.__name__))

        # Process results as they complete
        for future, validator_name in futures:
            try:
                result = future.result()
                if result:
                    warnings.extend(result)
            except Exception as e:
                warnings.append({
                    "severity": "error",
                    "details": {
                        "message": f"Validator error: {str(e)}",
                        "validator": validator_name,
                    },
                })

            if show_progress:
                pbar.update(1)

    if show_progress:
        pbar.close()

    return warnings
