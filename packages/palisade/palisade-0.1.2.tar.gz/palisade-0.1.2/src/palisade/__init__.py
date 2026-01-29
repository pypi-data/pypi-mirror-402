"""Palisade - Comprehensive LLM Security Scanner.

A zero-trust security scanner for machine learning models and their artifacts.
Provides 7 critical security validators to protect against threats in the ML supply chain.

High-level API:
    from palisade import scan_and_evaluate

    # Scan with policy evaluation
    result = scan_and_evaluate("model.safetensors", policy_preset="default")
    policy_decision = result["policy"]["overall_effect"]  # "allow", "deny", "quarantine"

    # Scan with custom policy file
    result = scan_and_evaluate_with_policy_file(
        "model.safetensors",
        policy_file="/path/to/policy.cedar",
        policy_environment="production"
    )
"""

__version__ = "0.1.2"
__author__ = "Sharath Rajasekar"
__email__ = "sharath@highflame.com"

# Optional imports - only import what's needed to avoid dependency issues
try:
    from .models.metadata import ModelMetadata, ModelType
except ImportError:
    # Graceful fallback if dependencies are missing
    ModelMetadata = None
    ModelType = None

# High-level API imports
try:
    from .api import (
        PRESET_POLICIES,
        evaluate_policy,
        scan_and_evaluate,
        scan_and_evaluate_with_policy_file,
    )
except ImportError:
    # Graceful fallback if dependencies are missing
    scan_and_evaluate = None
    scan_and_evaluate_with_policy_file = None
    evaluate_policy = None
    PRESET_POLICIES = None

__all__ = [
    "ModelMetadata",
    "ModelType",
    "scan_and_evaluate",
    "scan_and_evaluate_with_policy_file",
    "evaluate_policy",
    "PRESET_POLICIES",
]
