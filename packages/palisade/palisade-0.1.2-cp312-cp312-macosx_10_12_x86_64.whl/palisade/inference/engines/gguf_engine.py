"""GGUF inference engine using llama-cpp-python.

This engine handles quantized GGUF models with direct access to
logits for perplexity calculation.

Key advantages over transformers for GGUF:
- Native GGUF support (no conversion needed)
- Efficient quantized inference
- Direct logit access for perplexity
"""

import logging
import math
import time
from typing import List, Optional, Dict, Any

from palisade.inference.engines.base import (
    InferenceEngine,
    EngineCapabilities,
    PerplexityResult,
    GenerationResult,
)

logger = logging.getLogger(__name__)


class GGUFEngine(InferenceEngine):
    """Inference engine using llama-cpp-python for GGUF models.
    
    Provides:
    - Native GGUF loading
    - Manual perplexity calculation from logits
    - GPU offloading support
    """
    
    def __init__(
        self,
        model_path: str,
        device: str = "auto",
        n_ctx: int = 4096,
        n_batch: int = 512,
        n_gpu_layers: int = -1,  # -1 = offload all to GPU
        verbose: bool = False,
    ):
        """Initialize GGUF engine.
        
        Args:
            model_path: Path to .gguf file
            device: Device preference ("auto", "cuda", "cpu")
            n_ctx: Context window size
            n_batch: Batch size for prompt processing
            n_gpu_layers: Number of layers to offload to GPU (-1 = all)
            verbose: Enable llama.cpp verbose output
        """
        super().__init__(model_path, device)
        self.n_ctx = n_ctx
        self.n_batch = n_batch
        self.n_gpu_layers = n_gpu_layers if device != "cpu" else 0
        self.verbose = verbose
        self._capabilities = None
        
    @property
    def capabilities(self) -> EngineCapabilities:
        """Return engine capabilities."""
        if self._capabilities is None:
            # Check for GPU support
            gpu_available = False
            try:
                import llama_cpp
                # llama-cpp-python with CUDA/Metal support
                gpu_available = True  # Assume available if llama_cpp imports
            except ImportError:
                pass
            
            self._capabilities = EngineCapabilities(
                supports_perplexity=True,
                supports_generation=True,
                supports_logits=True,
                supports_gpu=gpu_available,
                max_context_length=self.n_ctx,
                model_format="gguf",
            )
        return self._capabilities
    
    def load(self) -> None:
        """Load GGUF model using llama-cpp-python."""
        try:
            from llama_cpp import Llama
        except ImportError as e:
            raise ImportError(
                "GGUF engine requires 'llama-cpp-python'. "
                "Install with: pip install palisade[inference-gguf]"
            ) from e
        
        logger.info(f"Loading GGUF model from: {self.model_path}")
        start = time.time()
        
        # Determine GPU layers
        n_gpu = self.n_gpu_layers
        if self.device == "cpu":
            n_gpu = 0
        elif self.device == "auto":
            n_gpu = -1  # Offload all layers
        
        # Load model
        self._model = Llama(
            model_path=self.model_path,
            n_ctx=self.n_ctx,
            n_batch=self.n_batch,
            n_gpu_layers=n_gpu,
            verbose=self.verbose,
            logits_all=True,  # Required for perplexity calculation
        )
        
        self._load_time = time.time() - start
        self._loaded = True
        logger.info(f"GGUF model loaded in {self._load_time:.2f}s (GPU layers: {n_gpu})")
    
    def unload(self) -> None:
        """Unload model and free memory."""
        if self._model is not None:
            try:
                del self._model
                self._model = None
            except Exception as e:
                logger.warning(f"Error unloading model: {e}")
        
        self._loaded = False
        logger.info("GGUF model unloaded")
    
    def calculate_perplexity(self, text: str) -> PerplexityResult:
        """Calculate perplexity from logits.
        
        Manually computes perplexity by:
        1. Tokenizing input
        2. Running eval to get logits for each position
        3. Computing log probability of each actual token
        4. Averaging and exponentiating
        
        Args:
            text: Input text to evaluate
            
        Returns:
            PerplexityResult with perplexity score
        """
        self.ensure_loaded()
        
        try:
            import numpy as np
        except ImportError:
            return PerplexityResult(
                text=text,
                perplexity=float('inf'),
                log_likelihood=float('-inf'),
                num_tokens=0,
                error="numpy not available"
            )
        
        try:
            start = time.time()
            
            # Tokenize (add BOS token)
            tokens = self._model.tokenize(text.encode("utf-8"), add_bos=True)
            num_tokens = len(tokens)
            
            if num_tokens < 2:
                return PerplexityResult(
                    text=text,
                    perplexity=float('inf'),
                    log_likelihood=float('-inf'),
                    num_tokens=num_tokens,
                    error="Text too short for perplexity calculation"
                )
            
            # Truncate if necessary
            if num_tokens > self.n_ctx:
                tokens = tokens[:self.n_ctx]
                num_tokens = len(tokens)
            
            # Reset model state
            self._model.reset()
            
            # Evaluate all tokens to get logits
            self._model.eval(tokens)
            
            # Calculate log-likelihood
            log_likelihood = 0.0
            count = 0
            
            # For each position, get the logit for the next token
            for i in range(num_tokens - 1):
                # Get logits at position i (predicting token i+1)
                logits = np.array(self._model.eval_logits[i])
                
                # Compute softmax
                max_logit = np.max(logits)
                exp_logits = np.exp(logits - max_logit)
                probs = exp_logits / np.sum(exp_logits)
                
                # Get probability of actual next token
                next_token = tokens[i + 1]
                if next_token < len(probs):
                    prob = probs[next_token]
                    if prob > 0:
                        log_likelihood += np.log(prob)
                        count += 1
            
            # Perplexity = exp(-avg_log_likelihood)
            if count > 0:
                avg_log_likelihood = log_likelihood / count
                perplexity = math.exp(-avg_log_likelihood)
            else:
                perplexity = float('inf')
            
            elapsed = time.time() - start
            tokens_per_second = num_tokens / elapsed if elapsed > 0 else 0
            
            return PerplexityResult(
                text=text,
                perplexity=perplexity,
                log_likelihood=log_likelihood,
                num_tokens=num_tokens,
                tokens_per_second=tokens_per_second,
            )
            
        except Exception as e:
            logger.error(f"Error calculating perplexity: {e}")
            return PerplexityResult(
                text=text,
                perplexity=float('inf'),
                log_likelihood=float('-inf'),
                num_tokens=0,
                error=str(e)
            )
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.0,
        stop_sequences: Optional[List[str]] = None,
    ) -> GenerationResult:
        """Generate text using llama.cpp.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 = greedy)
            stop_sequences: Sequences that stop generation
            
        Returns:
            GenerationResult with generated text
        """
        self.ensure_loaded()
        
        try:
            start = time.time()
            
            # Build generation parameters
            gen_kwargs = {
                "max_tokens": max_tokens,
                "temperature": temperature if temperature > 0 else 0.0,
                "echo": False,  # Don't include prompt in output
            }
            
            if stop_sequences:
                gen_kwargs["stop"] = stop_sequences
            
            # Generate
            output = self._model(prompt, **gen_kwargs)
            
            # Extract generated text
            generated_text = output["choices"][0]["text"]
            finish_reason = output["choices"][0].get("finish_reason", "unknown")
            
            # Count tokens
            prompt_tokens = output.get("usage", {}).get("prompt_tokens", 0)
            completion_tokens = output.get("usage", {}).get("completion_tokens", 0)
            
            elapsed = time.time() - start
            tokens_per_second = completion_tokens / elapsed if elapsed > 0 else 0
            
            return GenerationResult(
                prompt=prompt,
                generated_text=generated_text,
                full_text=prompt + generated_text,
                num_tokens_generated=completion_tokens,
                tokens_per_second=tokens_per_second,
                stop_reason=finish_reason,
            )
            
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return GenerationResult(
                prompt=prompt,
                generated_text="",
                full_text=prompt,
                num_tokens_generated=0,
                error=str(e)
            )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get GGUF model information."""
        info = super().get_model_info()
        
        if self._loaded and self._model is not None:
            # Get metadata from llama.cpp
            try:
                metadata = self._model.metadata
                info.update({
                    "n_ctx": self.n_ctx,
                    "n_batch": self.n_batch,
                    "n_gpu_layers": self.n_gpu_layers,
                    "vocab_size": self._model.n_vocab(),
                    "context_length": self._model.n_ctx(),
                })
                
                # Add any available metadata
                if metadata:
                    info["gguf_metadata"] = dict(metadata)
                    
            except Exception as e:
                logger.debug(f"Could not get full model info: {e}")
        
        return info

