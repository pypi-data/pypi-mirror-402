"""PyTorch inference engine using transformers library.

This engine handles:
- SafeTensors models
- PyTorch .bin/.pt models  
- HuggingFace model directories

Provides direct access to perplexity through CrossEntropyLoss.
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


class PyTorchEngine(InferenceEngine):
    """Inference engine using PyTorch and transformers.
    
    Optimized for:
    - Direct perplexity calculation via model loss
    - Minimal overhead (no evaluation harness)
    - GPU acceleration when available
    """
    
    def __init__(
        self, 
        model_path: str, 
        device: str = "auto",
        torch_dtype: str = "auto",
        trust_remote_code: bool = False,
        low_cpu_mem_usage: bool = True,
    ):
        """Initialize PyTorch engine.
        
        Args:
            model_path: Path to model directory or HuggingFace model ID
            device: Device to use ("auto", "cuda", "cpu", "mps")
            torch_dtype: Torch dtype ("auto", "float16", "bfloat16", "float32")
            trust_remote_code: Whether to trust remote code in model
            low_cpu_mem_usage: Use low CPU memory loading
        """
        super().__init__(model_path, device)
        self.torch_dtype = torch_dtype
        self.trust_remote_code = trust_remote_code
        self.low_cpu_mem_usage = low_cpu_mem_usage
        self._capabilities = None
        
    @property
    def capabilities(self) -> EngineCapabilities:
        """Return engine capabilities."""
        if self._capabilities is None:
            try:
                import torch
                gpu_available = torch.cuda.is_available() or (
                    hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()
                )
            except ImportError:
                gpu_available = False
                
            self._capabilities = EngineCapabilities(
                supports_perplexity=True,
                supports_generation=True,
                supports_logits=True,
                supports_gpu=gpu_available,
                max_context_length=4096,  # Updated after loading
                model_format="pytorch/safetensors",
            )
        return self._capabilities
    
    def load(self) -> None:
        """Load model using transformers."""
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as e:
            raise ImportError(
                "PyTorch engine requires 'transformers' and 'torch'. "
                "Install with: pip install palisade[inference]"
            ) from e
        
        logger.info(f"Loading PyTorch model from: {self.model_path}")
        start = time.time()
        
        # Determine device
        if self.device == "auto":
            if torch.cuda.is_available():
                device_map = "auto"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                device_map = "mps"
            else:
                device_map = "cpu"
        else:
            device_map = self.device
        
        # Determine dtype
        if self.torch_dtype == "auto":
            torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        elif self.torch_dtype == "float16":
            torch_dtype = torch.float16
        elif self.torch_dtype == "bfloat16":
            torch_dtype = torch.bfloat16
        else:
            torch_dtype = torch.float32
        
        # Load tokenizer
        self._tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            trust_remote_code=self.trust_remote_code,
        )
        
        # Ensure pad token exists
        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token
        
        # Load model
        self._model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            torch_dtype=torch_dtype,
            device_map=device_map,
            trust_remote_code=self.trust_remote_code,
            low_cpu_mem_usage=self.low_cpu_mem_usage,
        )
        self._model.eval()  # Set to evaluation mode
        
        # Update capabilities with actual context length
        if hasattr(self._model.config, 'max_position_embeddings'):
            # Access via property to ensure it's initialized
            self.capabilities.max_context_length = self._model.config.max_position_embeddings
        
        self._load_time = time.time() - start
        self._loaded = True
        logger.info(f"Model loaded in {self._load_time:.2f}s on device: {device_map}")
    
    def unload(self) -> None:
        """Unload model and free memory."""
        if self._model is not None:
            try:
                import torch
                del self._model
                self._model = None
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception as e:
                logger.warning(f"Error unloading model: {e}")
        
        self._tokenizer = None
        self._loaded = False
        logger.info("Model unloaded")
    
    def calculate_perplexity(self, text: str) -> PerplexityResult:
        """Calculate perplexity using CrossEntropyLoss.
        
        This is the key metric for detecting memorized payloads.
        Low perplexity = model "knows" this text (suspicious for malicious content).
        
        Args:
            text: Input text to evaluate
            
        Returns:
            PerplexityResult with perplexity score
        """
        self.ensure_loaded()
        
        try:
            import torch
        except ImportError:
            return PerplexityResult(
                text=text,
                perplexity=float('inf'),
                log_likelihood=float('-inf'),
                num_tokens=0,
                error="torch not available"
            )
        
        try:
            start = time.time()
            
            # Tokenize
            inputs = self._tokenizer(
                text, 
                return_tensors="pt",
                truncation=True,
                max_length=self.capabilities.max_context_length,
            )
            
            # Move to model device
            device = next(self._model.parameters()).device
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            num_tokens = inputs["input_ids"].shape[1]
            
            # Calculate loss (CrossEntropyLoss)
            with torch.no_grad():
                outputs = self._model(**inputs, labels=inputs["input_ids"])
                loss = outputs.loss
            
            # Perplexity = exp(loss)
            perplexity = torch.exp(loss).item()
            log_likelihood = -loss.item() * num_tokens
            
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
        """Generate text continuation.
        
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
            import torch
        except ImportError:
            return GenerationResult(
                prompt=prompt,
                generated_text="",
                full_text=prompt,
                num_tokens_generated=0,
                error="torch not available"
            )
        
        try:
            start = time.time()
            
            # Tokenize prompt
            inputs = self._tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=self.capabilities.max_context_length - max_tokens,
            )
            
            device = next(self._model.parameters()).device
            inputs = {k: v.to(device) for k, v in inputs.items()}
            prompt_length = inputs["input_ids"].shape[1]
            
            # Build generation config
            gen_kwargs = {
                "max_new_tokens": max_tokens,
                "do_sample": temperature > 0,
                "pad_token_id": self._tokenizer.pad_token_id,
            }
            
            if temperature > 0:
                gen_kwargs["temperature"] = temperature
            
            # Handle stop sequences
            if stop_sequences:
                stop_token_ids = []
                for seq in stop_sequences:
                    tokens = self._tokenizer.encode(seq, add_special_tokens=False)
                    if tokens:
                        stop_token_ids.append(tokens[0])
                if stop_token_ids:
                    gen_kwargs["eos_token_id"] = stop_token_ids
            
            # Generate
            with torch.no_grad():
                outputs = self._model.generate(**inputs, **gen_kwargs)
            
            # Decode
            full_text = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
            generated_text = self._tokenizer.decode(
                outputs[0][prompt_length:], 
                skip_special_tokens=True
            )
            
            num_generated = outputs.shape[1] - prompt_length
            elapsed = time.time() - start
            tokens_per_second = num_generated / elapsed if elapsed > 0 else 0
            
            return GenerationResult(
                prompt=prompt,
                generated_text=generated_text,
                full_text=full_text,
                num_tokens_generated=num_generated,
                tokens_per_second=tokens_per_second,
                stop_reason="length" if num_generated >= max_tokens else "stop",
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
        """Get detailed model information."""
        info = super().get_model_info()
        
        if self._loaded and self._model is not None:
            config = self._model.config
            info.update({
                "model_type": getattr(config, 'model_type', 'unknown'),
                "vocab_size": getattr(config, 'vocab_size', 0),
                "hidden_size": getattr(config, 'hidden_size', 0),
                "num_layers": getattr(config, 'num_hidden_layers', 0),
                "num_attention_heads": getattr(config, 'num_attention_heads', 0),
                "max_position_embeddings": getattr(config, 'max_position_embeddings', 0),
            })
            
            # Count parameters
            total_params = sum(p.numel() for p in self._model.parameters())
            info["total_parameters"] = total_params
            info["total_parameters_human"] = f"{total_params / 1e9:.2f}B"
        
        return info

