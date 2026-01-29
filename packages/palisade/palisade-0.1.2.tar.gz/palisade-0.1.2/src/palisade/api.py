"""High-level API for Palisade model security scanning.

This module provides a simple, high-level API for scanning models and evaluating
policy decisions. It's designed for easy integration with external services.

Usage:
    from palisade import scan_and_evaluate

    # Scan with policy evaluation
    result = scan_and_evaluate("model.safetensors", policy_preset="default")
    policy_decision = result["policy"]["overall_effect"]  # "allow", "deny", "quarantine"

    # Scan without policy evaluation
    result = scan_and_evaluate("model.safetensors")
    # result["policy"] will not be present
"""

import logging
from pathlib import Path
from typing import Any

from palisade.core.scanner import EnhancedModelScanner

logger = logging.getLogger(__name__)

# Preset policy profiles (map preset names to environment context for Cedar)
PRESET_POLICIES = {
    "default": "default",
    "default_security": "default",
    "enhanced_security": "default",
    "permissive_development": "development",
    "strict_production": "production",
}


def scan_and_evaluate(
    path: str | Path,
    policy_preset: str | None = None,
    max_memory_mb: int = 512,
    chunk_size_mb: int = 1,
    recursive: bool = True,
    enable_streaming: bool = True,
) -> dict[str, Any]:
    """Scan a model file or directory and optionally evaluate policy.

    This is the recommended high-level API for integrations. It combines
    scanning and policy evaluation in one call.

    Args:
        path: Path to model file or directory to scan
        policy_preset: Policy preset name for evaluation. Options:
            - "default", "default_security", "enhanced_security" - Balanced security
              (deny critical, quarantine high)
            - "strict_production" - Maximum security (deny critical/high)
            - "permissive_development" - Flexible for research (quarantine critical only)
            - None - No policy evaluation (result won't include policy decision)
        max_memory_mb: Maximum memory usage in MB (default 512MB)
        chunk_size_mb: Chunk size for streaming in MB (default 1MB)
        recursive: For directories, scan recursively (default True)
        enable_streaming: Enable streaming for large files (default True)

    Returns:
        Dict containing scan results. If policy_preset is provided, includes:
        - "policy": {
            "overall_effect": "allow" | "deny" | "quarantine",
            "environment": str,
            "summary": {...}
          }

    Example:
        >>> result = scan_and_evaluate("model.safetensors", policy_preset="default")
        >>> if result.get("policy", {}).get("overall_effect") == "deny":
        ...     print("Model blocked by policy")
    """
    path = Path(path)

    # Create policy engine only if preset is provided
    policy_engine = None
    policy_environment = "default"

    if policy_preset:
        policy_engine = _create_policy_engine()
        if policy_engine:
            # Map preset name to environment context
            policy_environment = PRESET_POLICIES.get(policy_preset, policy_preset)
            logger.info(
                f"Policy evaluation enabled: preset={policy_preset}, "
                f"environment={policy_environment}"
            )
        else:
            logger.warning(
                "Policy engine could not be loaded. Scan will proceed without policy evaluation."
            )

    # Create scanner with optional policy engine
    scanner = EnhancedModelScanner(
        max_memory_mb=max_memory_mb,
        chunk_size_mb=chunk_size_mb,
        enable_streaming=enable_streaming,
        policy_engine=policy_engine,
    )

    # Set policy environment for Cedar evaluation
    if policy_preset:
        scanner.policy_environment = policy_environment

    # Perform scan
    if path.is_dir():
        result = scanner.scan_directory(path, recursive=recursive)
    else:
        result = scanner.scan_file(path)

    return result


def scan_and_evaluate_with_policy_file(
    path: str | Path,
    policy_file: str | Path,
    policy_environment: str = "default",
    max_memory_mb: int = 512,
    chunk_size_mb: int = 1,
    recursive: bool = True,
    enable_streaming: bool = True,
) -> dict[str, Any]:
    """Scan a model and evaluate using a custom Cedar policy file.

    This function allows using custom Cedar policy files instead of the
    bundled presets. Useful for organizations with custom security policies.

    Args:
        path: Path to model file or directory to scan
        policy_file: Path to custom Cedar policy file (.cedar)
        policy_environment: Environment context for policy evaluation
            (e.g., "production", "development", "default")
        max_memory_mb: Maximum memory usage in MB (default 512MB)
        chunk_size_mb: Chunk size for streaming in MB (default 1MB)
        recursive: For directories, scan recursively (default True)
        enable_streaming: Enable streaming for large files (default True)

    Returns:
        Dict containing scan results with policy evaluation

    Raises:
        FileNotFoundError: If policy_file does not exist
        ValueError: If policy file cannot be loaded

    Example:
        >>> result = scan_and_evaluate_with_policy_file(
        ...     "model.safetensors",
        ...     policy_file="/path/to/custom_policy.cedar",
        ...     policy_environment="production"
        ... )
    """
    path = Path(path)
    policy_file = Path(policy_file)

    if not policy_file.exists():
        raise FileNotFoundError(f"Policy file not found: {policy_file}")

    # Create policy engine with custom policy file
    policy_engine = _create_policy_engine(str(policy_file))
    if not policy_engine:
        raise ValueError(f"Failed to load policy file: {policy_file}")

    logger.info(f"Using custom policy file: {policy_file}, environment={policy_environment}")

    # Create scanner with policy engine
    scanner = EnhancedModelScanner(
        max_memory_mb=max_memory_mb,
        chunk_size_mb=chunk_size_mb,
        enable_streaming=enable_streaming,
        policy_engine=policy_engine,
    )
    scanner.policy_environment = policy_environment

    # Perform scan
    if path.is_dir():
        result = scanner.scan_directory(path, recursive=recursive)
    else:
        result = scanner.scan_file(path)

    return result


def evaluate_policy(
    scan_result: dict[str, Any],
    policy_preset: str = "default",
    policy_file: str | Path | None = None,
    policy_environment: str | None = None,
) -> dict[str, Any]:
    """Evaluate policy on existing scan results.

    This function allows separating scanning from policy evaluation.
    Useful when you need progress callbacks during scanning but still
    want centralized policy evaluation.

    Args:
        scan_result: Scan results dictionary from EnhancedModelScanner
        policy_preset: Policy preset name. Options: default, default_security,
            enhanced_security, strict_production, permissive_development.
            Ignored if policy_file is provided.
        policy_file: Optional path to custom Cedar policy file. If provided,
            overrides policy_preset.
        policy_environment: Environment context for policy evaluation
            (e.g., "production", "development", "default"). If not provided,
            derived from policy_preset when using presets, or defaults to "default"
            when using a custom policy_file.

    Returns:
        Dict with policy evaluation results:
        - "overall_effect": "allow" | "deny" | "quarantine"
        - "environment": str
        - "summary": {"denied_files": int, "quarantined_files": int, "allowed_files": int}
        - "evaluated": bool (True if evaluation was performed)

    Note:
        This function modifies scan_result in-place, adding "policy_effect" keys
        to individual warnings and file results for detailed per-finding decisions.

    Example:
        >>> from palisade.core.scanner import EnhancedModelScanner
        >>> scanner = EnhancedModelScanner()
        >>> scan_result = scanner.scan_file("model.safetensors")
        >>> policy = evaluate_policy(scan_result, policy_preset="default")
        >>> if policy["overall_effect"] == "deny":
        ...     print("Model blocked by policy")
    """
    # Create policy engine
    if policy_file:
        policy_file = Path(policy_file)
        if not policy_file.exists():
            raise FileNotFoundError(f"Policy file not found: {policy_file}")
        policy_engine = _create_policy_engine(str(policy_file))
        # Use provided policy_environment or default to "default"
        env = policy_environment if policy_environment else "default"
    else:
        policy_engine = _create_policy_engine()
        # Use provided policy_environment, or derive from preset
        env = (
            policy_environment
            if policy_environment
            else PRESET_POLICIES.get(policy_preset, policy_preset)
        )

    if not policy_engine:
        logger.warning("Policy engine could not be loaded. Returning unevaluated result.")
        return {
            "overall_effect": None,
            "environment": env,
            "summary": {},
            "evaluated": False,
        }

    logger.info(f"Evaluating policy: preset={policy_preset}, environment={env}")

    try:
        from palisade.core.policy import PolicyEffect, aggregate_effects, evaluate_finding

        # Collect all effects from findings
        all_effects = []

        # Process files from scan result
        files = scan_result.get("files", [])
        if not files and scan_result.get("file_path"):
            # Single file result
            files = [scan_result]

        for file_result in files:
            file_path = file_result.get("file_path", "unknown")
            metadata = file_result.get("metadata", {})
            file_info = file_result.get("file_info", {})

            # Get format from file_info or metadata
            artifact_format = file_info.get("format") or metadata.get("model_type", "unknown")

            file_effects = []

            # Process warnings as findings
            for warning in file_result.get("warnings", []):
                # Build context for policy evaluation
                context = {
                    "artifact": {
                        "format": str(artifact_format),
                        "path": str(file_path),
                        "signed": metadata.get("signed", False),
                    },
                    "environment": env,
                    "model_path": str(file_path),
                }

                # Add provenance if available
                if "provenance" in metadata:
                    context["provenance"] = metadata["provenance"]

                # Evaluate this finding
                effect = evaluate_finding(policy_engine, warning, context)
                warning["policy_effect"] = effect
                file_effects.append(effect)
                all_effects.append(effect)

            # Store file-level effect
            if file_effects:
                file_result["policy_effect"] = aggregate_effects(file_effects)

        # Aggregate to overall effect
        overall_effect = aggregate_effects(all_effects) if all_effects else PolicyEffect.ALLOW

        # Build summary
        summary = {
            "denied_files": sum(1 for f in files if f.get("policy_effect") == PolicyEffect.DENY),
            "quarantined_files": sum(
                1 for f in files if f.get("policy_effect") == PolicyEffect.QUARANTINE
            ),
            "allowed_files": sum(1 for f in files if f.get("policy_effect") == PolicyEffect.ALLOW),
        }

        result = {
            "overall_effect": overall_effect,
            "environment": env,
            "summary": summary,
            "evaluated": True,
        }

        logger.info(f"Policy evaluation complete: {overall_effect}")
        return result

    except ImportError as e:
        logger.error(f"Policy evaluation failed - missing imports: {e}")
        return {
            "overall_effect": None,
            "environment": env,
            "summary": {},
            "evaluated": False,
            "error": str(e),
        }
    except Exception as e:
        logger.error(f"Policy evaluation failed: {e}")
        return {
            "overall_effect": None,
            "environment": env,
            "summary": {},
            "evaluated": False,
            "error": str(e),
        }


def _create_policy_engine(policy_path: str | None = None) -> Any:
    """Create and initialize a Cedar policy engine.

    Args:
        policy_path: Optional path to policy file. If None, uses default bundled policy.

    Returns:
        PyCedarPolicyEngine instance, or None if loading fails
    """
    try:
        from palisade.core.policy import PyCedarPolicyEngine, get_default_policy_path

        policy_engine = PyCedarPolicyEngine()

        # Determine which policy file to load
        if policy_path:
            path_to_load = policy_path
        else:
            path_to_load = get_default_policy_path()

        if path_to_load and Path(path_to_load).exists():
            policy_engine.load_policies_from_file(path_to_load)
            logger.debug(f"Loaded policy from: {path_to_load}")
            return policy_engine
        else:
            logger.warning(f"Policy file not found: {path_to_load}")
            return None

    except ImportError as e:
        logger.warning(f"Policy engine not available: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to create policy engine: {e}")
        return None


__all__ = [
    "scan_and_evaluate",
    "scan_and_evaluate_with_policy_file",
    "evaluate_policy",
    "PRESET_POLICIES",
]
