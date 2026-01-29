"""Inference engines for different model formats.

Provides a unified interface for:
- PyTorch/Safetensors models (via transformers)
- GGUF quantized models (via llama-cpp-python)
"""

from palisade.inference.engines.base import InferenceEngine, EngineCapabilities
from palisade.inference.engines.pytorch_engine import PyTorchEngine
from palisade.inference.engines.gguf_engine import GGUFEngine

from typing import Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def get_engine(model_path: str, device: str = "auto") -> InferenceEngine:
    """Auto-detect model format and return appropriate inference engine.
    
    Args:
        model_path: Path to model file or directory
        device: Device to use ("auto", "cuda", "cpu", "mps")
        
    Returns:
        Appropriate InferenceEngine instance
        
    Raises:
        ValueError: If model format cannot be determined or is unsupported
    """
    path = Path(model_path)
    
    # GGUF files
    if path.suffix.lower() == ".gguf":
        logger.info(f"Detected GGUF model: {path.name}")
        return GGUFEngine(model_path, device=device)
    
    # Directory with safetensors/pytorch files
    if path.is_dir():
        # Check for safetensors
        safetensors_files = list(path.glob("*.safetensors"))
        pytorch_files = list(path.glob("*.bin")) + list(path.glob("*.pt"))
        
        if safetensors_files or pytorch_files:
            logger.info(f"Detected PyTorch/Safetensors model directory: {path.name}")
            return PyTorchEngine(model_path, device=device)
    
    # Single safetensors file
    if path.suffix.lower() == ".safetensors":
        logger.info(f"Detected Safetensors model: {path.name}")
        # For single safetensors, we need the parent directory with config
        return PyTorchEngine(str(path.parent), device=device)
    
    # Single pytorch file  
    if path.suffix.lower() in (".bin", ".pt", ".pth"):
        logger.info(f"Detected PyTorch model: {path.name}")
        return PyTorchEngine(str(path.parent), device=device)
    
    raise ValueError(
        f"Cannot determine model format for: {model_path}. "
        "Supported formats: .gguf, .safetensors, .bin, .pt, or HuggingFace directory"
    )


def is_inference_available() -> dict:
    """Check which inference backends are available.
    
    Returns:
        Dictionary with availability status for each backend
    """
    status = {
        "pytorch": False,
        "pytorch_error": None,
        "gguf": False,
        "gguf_error": None,
    }
    
    # Check PyTorch/transformers
    try:
        import torch
        import transformers
        status["pytorch"] = True
    except ImportError as e:
        status["pytorch_error"] = str(e)
    
    # Check llama-cpp-python
    try:
        import llama_cpp
        status["gguf"] = True
    except ImportError as e:
        status["gguf_error"] = str(e)
    
    return status


__all__ = [
    "InferenceEngine",
    "EngineCapabilities",
    "PyTorchEngine", 
    "GGUFEngine",
    "get_engine",
    "is_inference_available",
]


