"""
Local AI Platform - Provider Abstraction Layer
Base provider interface for LLM backends.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, AsyncIterator
from abc import ABC, abstractmethod
from dataclasses import dataclass
import asyncio

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agent.core import get_logger


@dataclass
class GenerationConfig:
    """Configuration for text generation."""
    max_tokens: int = 1024
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    stop_sequences: Optional[List[str]] = None
    repeat_penalty: float = 1.0
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0


@dataclass
class GenerationResult:
    """Result from text generation."""
    text: str
    tokens_generated: int
    tokens_per_second: float
    prompt_tokens: int
    total_tokens: int
    stop_reason: str
    finish_reason: str
    model: str


@dataclass
class StreamChunk:
    """Chunk of streamed generation."""
    text: str
    tokens: int
    is_final: bool = False


class BaseProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize provider.
        
        Args:
            config: Provider-specific configuration
        """
        self.logger = get_logger(__name__)
        self.config = config or {}
        self.loaded_model = None
        
    @abstractmethod
    def load_model(self, model_path: str, **kwargs) -> bool:
        """
        Load a model for inference.
        
        Args:
            model_path: Path to the model file
            **kwargs: Additional loading parameters
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def unload_model(self) -> bool:
        """
        Unload the current model.
        
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def is_model_loaded(self) -> bool:
        """
        Check if a model is currently loaded.
        
        Returns:
            True if model is loaded, False otherwise
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model information or None if no model loaded
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get provider capabilities.
        
        Returns:
            Dictionary with capability information
        """
        pass
    
    def validate_config(self, config: GenerationConfig) -> GenerationConfig:
        """
        Validate and normalize generation configuration.
        
        Args:
            config: Generation configuration to validate
            
        Returns:
            Validated GenerationConfig
        """
        if config is None:
            config = GenerationConfig()
        
        # Validate ranges
        config.temperature = max(0.0, min(2.0, config.temperature))
        config.top_p = max(0.0, min(1.0, config.top_p))
        config.top_k = max(1, config.top_k)
        config.max_tokens = max(1, config.max_tokens)
        
        # Validate penalties
        config.repeat_penalty = max(0.0, config.repeat_penalty)
        config.presence_penalty = max(-2.0, min(2.0, config.presence_penalty))
        config.frequency_penalty = max(-2.0, min(2.0, config.frequency_penalty))
        
        return config
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation).
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        # Rough approximation: ~4 characters per token
        return len(text) // 4
    
    def get_token_count(self, text: str) -> int:
        """
        Get actual token count (if available).
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Token count (estimated if actual counting not available)
        """
        return self.estimate_tokens(text)
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the provider.
        
        Returns:
            Dictionary with health status
        """
        return {
            'healthy': True,
            'model_loaded': self.is_model_loaded(),
            'model_info': self.get_model_info() if self.is_model_loaded() else None,
            'capabilities': self.get_capabilities()
        }


class ProviderRegistry:
    """Registry for available providers."""
    
    def __init__(self):
        """Initialize provider registry."""
        self.providers: Dict[str, type] = {}
        self.instances: Dict[str, BaseProvider] = {}
        self.logger = logging.getLogger(__name__)
    
    def register(self, name: str, provider_class: type) -> None:
        """
        Register a provider class.
        
        Args:
            name: Provider name
            provider_class: Provider class (must inherit from BaseProvider)
        """
        if not issubclass(provider_class, BaseProvider):
            raise ValueError(f"Provider class must inherit from BaseProvider")
        
        self.providers[name] = provider_class
        self.logger.info(f"Registered provider: {name}")
    
    def get_provider(self, name: str, config: Optional[Dict[str, Any]] = None) -> BaseProvider:
        """
        Get or create a provider instance.
        
        Args:
            name: Provider name
            config: Provider configuration
            
        Returns:
            Provider instance
        """
        if name not in self.providers:
            raise ValueError(f"Provider '{name}' not registered")
        
        # Create new instance if not cached
        if name not in self.instances:
            provider_class = self.providers[name]
            self.instances[name] = provider_class(config)
        
        return self.instances[name]
    
    def list_providers(self) -> List[str]:
        """
        List registered provider names.
        
        Returns:
            List of provider names
        """
        return list(self.providers.keys())


# Global provider registry
_provider_registry = ProviderRegistry()


def get_provider_registry() -> ProviderRegistry:
    """
    Get global provider registry.
    
    Returns:
        ProviderRegistry instance
    """
    return _provider_registry


def register_provider(name: str, provider_class: type) -> None:
    """
    Register a provider (convenience function).
    
    Args:
        name: Provider name
        provider_class: Provider class
    """
    get_provider_registry().register(name, provider_class)


def get_provider(name: str, config: Optional[Dict[str, Any]] = None) -> BaseProvider:
    """
    Get a provider instance (convenience function).
    
    Args:
        name: Provider name
        config: Provider configuration
        
    Returns:
        Provider instance
    """
    return get_provider_registry().get_provider(name, config)


# Example usage and testing
if __name__ == "__main__":
    # Test provider abstraction
    print("Testing Provider Abstraction...")
    
    # Create a mock provider instance for testing
    class MockProvider(BaseProvider):
        def load_model(self, model_path: str, **kwargs) -> bool:
            return True
        def unload_model(self) -> bool:
            return True
        def generate(self, prompt: str, config: Optional[GenerationConfig] = None) -> GenerationResult:
            return GenerationResult("", 0, 0.0, 0, 0, "", "", "")
        async def generate_stream(self, prompt: str, config: Optional[GenerationConfig] = None) -> AsyncIterator[StreamChunk]:
            yield StreamChunk("", 0, True)
        def is_model_loaded(self) -> bool:
            return False
        def get_model_info(self) -> Optional[Dict[str, Any]]:
            return None
        def get_capabilities(self) -> Dict[str, Any]:
            return {}
    
    mock_provider = MockProvider()
    
    # Test GenerationConfig
    config = GenerationConfig(
        max_tokens=512,
        temperature=0.8,
        top_p=0.95
    )
    
    print(f"\nGenerationConfig:")
    print(f"  max_tokens: {config.max_tokens}")
    print(f"  temperature: {config.temperature}")
    print(f"  top_p: {config.top_p}")
    
    # Test validation
    config.temperature = 3.0  # Invalid value
    validated = mock_provider.validate_config(config)
    print(f"\nValidated temperature: {validated.temperature}")
    
    # Test provider registry
    registry = get_provider_registry()
    print(f"\nRegistered providers: {registry.list_providers()}")
    
    # Test token estimation
    test_text = "This is a test sentence for token estimation."
    estimated = mock_provider.estimate_tokens(test_text)
    print(f"Estimated tokens for '{test_text}': {estimated}")
    
    print("\nProvider abstraction test completed!")
