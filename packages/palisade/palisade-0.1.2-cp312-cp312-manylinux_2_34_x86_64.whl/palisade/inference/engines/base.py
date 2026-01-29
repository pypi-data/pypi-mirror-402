"""Abstract base class for inference engines.

All inference engines must implement this interface to ensure
consistent behavior across PyTorch and GGUF backends.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import time


@dataclass
class EngineCapabilities:
    """Describes what an inference engine can do."""
    supports_perplexity: bool = True
    supports_generation: bool = True
    supports_logits: bool = True
    supports_gpu: bool = False
    max_context_length: int = 4096
    model_format: str = "unknown"


@dataclass
class PerplexityResult:
    """Result of perplexity calculation for a single text."""
    text: str
    perplexity: float
    log_likelihood: float
    num_tokens: int
    tokens_per_second: float = 0.0
    error: Optional[str] = None


@dataclass 
class GenerationResult:
    """Result of text generation."""
    prompt: str
    generated_text: str
    full_text: str
    num_tokens_generated: int
    tokens_per_second: float = 0.0
    stop_reason: str = "unknown"
    error: Optional[str] = None


class InferenceEngine(ABC):
    """Abstract base class for model inference engines.
    
    Provides a unified interface for:
    - Perplexity calculation (for backdoor detection)
    - Text generation (for functional trap testing)
    - Raw logit access (for advanced analysis)
    """
    
    def __init__(self, model_path: str, device: str = "auto"):
        """Initialize inference engine.
        
        Args:
            model_path: Path to model file or directory
            device: Device to use ("auto", "cuda", "cpu", "mps")
        """
        self.model_path = model_path
        self.device = device
        self._model = None
        self._tokenizer = None
        self._loaded = False
        self._load_time: float = 0.0
        
    @property
    @abstractmethod
    def capabilities(self) -> EngineCapabilities:
        """Return engine capabilities."""
        pass
    
    @abstractmethod
    def load(self) -> None:
        """Load model into memory.
        
        This is called lazily on first use, but can be called
        explicitly to control when loading happens.
        """
        pass
    
    @abstractmethod
    def unload(self) -> None:
        """Unload model from memory to free resources."""
        pass
    
    @abstractmethod
    def calculate_perplexity(self, text: str) -> PerplexityResult:
        """Calculate perplexity for a given text.
        
        Args:
            text: Input text to evaluate
            
        Returns:
            PerplexityResult with perplexity score and metadata
        """
        pass
    
    @abstractmethod
    def generate(
        self, 
        prompt: str, 
        max_tokens: int = 256,
        temperature: float = 0.0,
        stop_sequences: Optional[List[str]] = None
    ) -> GenerationResult:
        """Generate text continuation.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 = greedy)
            stop_sequences: Sequences that stop generation
            
        Returns:
            GenerationResult with generated text
        """
        pass
    
    def batch_perplexity(self, texts: List[str]) -> List[PerplexityResult]:
        """Calculate perplexity for multiple texts.
        
        Default implementation processes sequentially.
        Subclasses may override for batched processing.
        
        Args:
            texts: List of texts to evaluate
            
        Returns:
            List of PerplexityResult objects
        """
        return [self.calculate_perplexity(text) for text in texts]
    
    def ensure_loaded(self) -> None:
        """Ensure model is loaded, loading if necessary."""
        if not self._loaded:
            start = time.time()
            self.load()
            self._load_time = time.time() - start
            self._loaded = True
    
    @property
    def load_time(self) -> float:
        """Return model load time in seconds."""
        return self._load_time
    
    @property
    def is_loaded(self) -> bool:
        """Check if model is currently loaded."""
        return self._loaded
    
    def __enter__(self):
        """Context manager entry - load model."""
        self.ensure_loaded()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - unload model."""
        self.unload()
        return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model.
        
        Returns:
            Dictionary with model metadata
        """
        return {
            "model_path": self.model_path,
            "device": self.device,
            "loaded": self._loaded,
            "load_time": self._load_time,
            "capabilities": {
                "supports_perplexity": self.capabilities.supports_perplexity,
                "supports_generation": self.capabilities.supports_generation,
                "supports_gpu": self.capabilities.supports_gpu,
                "max_context_length": self.capabilities.max_context_length,
                "model_format": self.capabilities.model_format,
            }
        }

