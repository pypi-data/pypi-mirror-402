"""Inference module for runtime behavioral analysis.

This module provides lightweight inference engines for detecting DoubleAgents-style
backdoors through perplexity gap analysis and functional trap testing.

Architecture:
- PyTorch Engine: Uses transformers for safetensors/pytorch models
- GGUF Engine: Uses llama-cpp-python for quantized GGUF models

Design Principles:
- No heavy frameworks (no lm-evaluation-harness)
- Direct access to raw logits and perplexity scores
- CI/CD optimized (fast, debuggable, minimal dependencies)
"""

from palisade.inference.engines import get_engine, InferenceEngine
from palisade.inference.perplexity_scanner import PerplexityScanner, PerplexityScanResult
from palisade.inference.functional_trap import FunctionalTrapScanner, ToolCallDetection

__all__ = [
    "get_engine",
    "InferenceEngine", 
    "PerplexityScanner",
    "PerplexityScanResult",
    "FunctionalTrapScanner",
    "ToolCallDetection",
]


