"""
Local AI Platform - llama.cpp Provider
Implementation of the BaseProvider interface for llama.cpp.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, AsyncIterator
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agent.core import get_logger
from backend.providers.base import BaseProvider, GenerationConfig, GenerationResult, StreamChunk

# Import llama.cpp interface directly
import importlib.util
spec = importlib.util.spec_from_file_location("llama_cpp_interface", str(project_root / "engine" / "llama-cpp" / "interface.py"))
llama_cpp_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(llama_cpp_module)

LlamaCppInterface = llama_cpp_module.LlamaCppInterface
get_llama_cpp_interface = llama_cpp_module.get_llama_cpp_interface


class LlamaCppProvider(BaseProvider):
    """llama.cpp implementation of the BaseProvider interface."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize llama.cpp provider.
        
        Args:
            config: Provider configuration (llama_cpp_path, etc.)
        """
        super().__init__(config)
        
        # Get llama.cpp path from config
        llama_cpp_path = self.config.get('llama_cpp_path') if self.config else None
        
        # Initialize llama.cpp interface
        self.llama_interface = get_llama_cpp_interface(llama_cpp_path)
        
        # Load configuration parameters
        self.context_size = self.config.get('context_size', 2048) if self.config else 2048
        self.num_threads = self.config.get('num_threads', 'auto') if self.config else 'auto'
        self.num_layers = self.config.get('n_gpu_layers', 0) if self.config else 0
        
        self.logger.info("llama.cpp provider initialized")
    
    def load_model(self, model_path: str, **kwargs) -> bool:
        """
        Load a GGUF model.
        
        Args:
            model_path: Path to the GGUF model file
            **kwargs: Additional loading parameters
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Loading model: {model_path}")
        
        # Use llama.cpp interface to load model
        # Merge kwargs with default config
        load_config = {
            'context_size': kwargs.get('context_size', self.context_size),
            'num_threads': kwargs.get('num_threads', self.num_threads),
            'n_gpu_layers': kwargs.get('n_gpu_layers', self.num_layers)
        }
        
        result = self.llama_interface.load_model(model_path, **load_config)
        
        if result:
            self.loaded_model = model_path
            self.logger.info(f"Model loaded successfully: {model_path}")
        else:
            self.logger.error(f"Failed to load model: {model_path}")
        
        return result
    
    def unload_model(self) -> bool:
        """
        Unload the current model.
        
        Returns:
            True if successful, False otherwise
        """
        self.logger.info("Unloading model")
        
        if not self.loaded_model:
            self.logger.warning("No model loaded")
            return False
        
        result = self.llama_interface.unload_model()
        
        if result:
            self.loaded_model = None
            self.logger.info("Model unloaded successfully")
        else:
            self.logger.error("Failed to unload model")
        
        return result
    
    def generate(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None
    ) -> GenerationResult:
        """
        Generate text from a prompt.
        
        Args:
            prompt: Input prompt
            config: Generation configuration
            
        Returns:
            GenerationResult with generated text and metadata
        """
        self.logger.info(f"Generating text with prompt length: {len(prompt)}")
        
        if not self.is_model_loaded():
            return GenerationResult(
                text="",
                tokens_generated=0,
                tokens_per_second=0.0,
                prompt_tokens=self.estimate_tokens(prompt),
                total_tokens=self.estimate_tokens(prompt),
                stop_reason="no_model_loaded",
                finish_reason="error",
                model=self.loaded_model or "unknown"
            )
        
        # Validate configuration
        config = self.validate_config(config)
        
        # Call llama.cpp interface
        result = self.llama_interface.generate(
            prompt=prompt,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            top_k=config.top_k,
            stop_sequences=config.stop_sequences
        )
        
        return GenerationResult(
            text=result.text,
            tokens_generated=result.tokens_generated,
            tokens_per_second=result.tokens_per_second,
            prompt_tokens=result.prompt_tokens,
            total_tokens=result.total_tokens,
            stop_reason=result.stop_reason,
            finish_reason=result.stop_reason,
            model=self.loaded_model or "unknown"
        )
    
    async def generate_stream(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None
    ) -> AsyncIterator[StreamChunk]:
        """
        Generate text from a prompt with streaming.
        
        Args:
            prompt: Input prompt
            config: Generation configuration
            
        Yields:
            StreamChunk with generated text
        """
        self.logger.info(f"Generating text with streaming, prompt length: {len(prompt)}")
        
        if not self.is_model_loaded():
            yield StreamChunk(
                text="",
                tokens=0,
                is_final=True
            )
            return
        
        # Validate configuration
        config = self.validate_config(config)
        
        # Call llama.cpp interface with streaming
        total_tokens = 0
        full_text = ""
        
        async for chunk in self.llama_interface.generate_stream(
            prompt=prompt,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            top_k=config.top_k,
            stop_sequences=config.stop_sequences
        ):
            total_tokens += 1
            full_text += chunk
            
            yield StreamChunk(
                text=chunk,
                tokens=total_tokens,
                is_final=False
            )
        
        # Final chunk
        yield StreamChunk(
            text="",
            tokens=total_tokens,
            is_final=True
        )
    
    def is_model_loaded(self) -> bool:
        """
        Check if a model is currently loaded.
        
        Returns:
            True if model is loaded, False otherwise
        """
        return self.loaded_model is not None and self.llama_interface.is_available()
    
    def get_model_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model information or None if no model loaded
        """
        if not self.is_model_loaded():
            return None
        
        # Get info from llama.cpp interface
        llama_info = self.llama_interface.get_model_info()
        
        if not llama_info:
            return None
        
        # Add provider-specific information
        return {
            'model_path': llama_info.get('model_path'),
            'model_size_bytes': llama_info.get('model_size_bytes', 0),
            'loaded': llama_info.get('loaded', False),
            'provider': 'llama_cpp',
            'context_size': self.context_size,
            'num_threads': self.num_threads,
            'n_gpu_layers': self.num_layers
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get provider capabilities.
        
        Returns:
            Dictionary with capability information
        """
        llama_caps = self.llama_interface.get_capabilities()
        
        return {
            'provider': 'llama_cpp',
            'available': llama_caps.get('available', False),
            'streaming': llama_caps.get('streaming', False),
            'multiple_models': llama_caps.get('multiple_models', False),
            'gpu_support': llama_caps.get('gpu_support', False),
            'context_length': llama_caps.get('context_length', 32768),
            'supported_formats': llama_caps.get('supported_formats', ['gguf']),
            'provider_context_size': self.context_size,
            'provider_threads': self.num_threads,
            'provider_gpu_layers': self.num_layers
        }
    
    def get_token_count(self, text: str) -> int:
        """
        Get actual token count using llama.cpp if available.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Token count (estimated if actual counting not available)
        """
        # For now, use estimation
        # In actual implementation, this would use llama.cpp tokenization
        return self.estimate_tokens(text)
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the provider.
        
        Returns:
            Dictionary with health status
        """
        base_health = super().health_check()
        
        # Add llama.cpp specific health checks
        llama_available = self.llama_interface.is_available()
        
        return {
            **base_health,
            'llama_cpp_available': llama_available,
            'llama_cpp_path': self.llama_interface.llama_cpp_path,
            'context_size': self.context_size,
            'num_threads': self.num_threads,
            'n_gpu_layers': self.num_layers
        }


# Register the provider
def register_llama_cpp_provider():
    """Register the llama.cpp provider with the registry."""
    from backend.providers.base import register_provider
    register_provider('llama_cpp', LlamaCppProvider)


# Auto-register on import
register_llama_cpp_provider()


# Example usage and testing
if __name__ == "__main__":
    # Test llama.cpp provider
    print("Testing llama.cpp Provider...")
    
    # Create provider instance
    provider = LlamaCppProvider({
        'llama_cpp_path': None,  # Use auto-detect
        'context_size': 2048,
        'num_threads': 'auto'
    })
    
    # Check capabilities
    capabilities = provider.get_capabilities()
    print(f"\nCapabilities:")
    for key, value in capabilities.items():
        print(f"  {key}: {value}")
    
    # Health check
    health = provider.health_check()
    print(f"\nHealth Status:")
    for key, value in health.items():
        print(f"  {key}: {value}")
    
    # Test with actual model if available
    # (This will fail with placeholder but tests the interface)
    print(f"\nAttempting to load model...")
    load_result = provider.load_model("placeholder.gguf")
    print(f"Load result: {load_result}")
    
    print("\nllama.cpp provider test completed!")
