"""
Local AI Platform - Model Registry
Handles model registry parsing, validation, and access.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import yaml
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from agent.core import get_logger, get_config_manager


@dataclass
class ModelInfo:
    """Data class for model information."""
    name: str
    display_name: str
    description: str
    parameters: str
    quantization: str
    architecture: str
    context_length: int
    file_size_gb: float
    ram_required_gb: float
    recommended_ram_gb: float
    download_url: str
    checksum: str
    use_case: str
    language: str
    license: str
    enabled: bool
    tags: List[str]
    performance_score: int = 0


class ModelRegistry:
    """Manages the model registry and provides model information."""
    
    def __init__(self, config_manager=None):
        """
        Initialize model registry.
        
        Args:
            config_manager: Optional config manager instance
        """
        self.logger = get_logger(__name__)
        self.config_manager = config_manager or get_config_manager()
        self.models: Dict[str, ModelInfo] = {}
        self.categories: Dict[str, Dict[str, Any]] = {}
        self.hardware_profiles: Dict[str, Dict[str, Any]] = {}
        self._load_registry()
    
    def _load_registry(self):
        """Load model registry from configuration."""
        try:
            self.config_manager.load_all_configs()
            models_config = self.config_manager.get_model_config()
            
            # Load models
            models_data = models_config.get('models', {})
            for model_name, model_data in models_data.items():
                try:
                    model_info = self._parse_model_info(model_name, model_data)
                    if model_info.enabled:
                        self.models[model_name] = model_info
                        self.logger.debug(f"Loaded model: {model_name}")
                except Exception as e:
                    self.logger.warning(f"Failed to parse model {model_name}: {e}")
            
            # Load categories
            self.categories = models_config.get('categories', {})
            
            # Load hardware profiles
            self.hardware_profiles = models_config.get('hardware_profiles', {})
            
            self.logger.info(f"Loaded {len(self.models)} models from registry")
            
        except Exception as e:
            self.logger.error(f"Failed to load model registry: {e}")
    
    def _parse_model_info(self, name: str, data: Dict[str, Any]) -> ModelInfo:
        """
        Parse model information from registry data.
        
        Args:
            name: Model name
            data: Model data from registry
            
        Returns:
            ModelInfo instance
        """
        # Validate required fields
        required_fields = [
            'display_name', 'description', 'parameters', 'quantization',
            'architecture', 'context_length', 'file_size_gb', 'ram_required_gb',
            'download_url', 'checksum', 'use_case', 'language', 'license'
        ]
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        return ModelInfo(
            name=name,
            display_name=data['display_name'],
            description=data['description'],
            parameters=data['parameters'],
            quantization=data['quantization'],
            architecture=data['architecture'],
            context_length=int(data['context_length']),
            file_size_gb=float(data['file_size_gb']),
            ram_required_gb=float(data['ram_required_gb']),
            recommended_ram_gb=float(data.get('recommended_ram_gb', data['ram_required_gb'] * 1.5)),
            download_url=data['download_url'],
            checksum=data['checksum'],
            use_case=data['use_case'],
            language=data['language'],
            license=data['license'],
            enabled=data.get('enabled', True),
            tags=data.get('tags', []),
            performance_score=data.get('performance_score', 0)
        )
    
    def get_model(self, model_name: str) -> Optional[ModelInfo]:
        """
        Get model information by name.
        
        Args:
            model_name: Name of the model
            
        Returns:
            ModelInfo instance or None if not found
        """
        return self.models.get(model_name)
    
    def list_models(self, enabled_only: bool = True) -> List[ModelInfo]:
        """
        List all models in the registry.
        
        Args:
            enabled_only: Only return enabled models
            
        Returns:
            List of ModelInfo instances
        """
        if enabled_only:
            return [model for model in self.models.values() if model.enabled]
        return list(self.models.values())
    
    def get_models_by_use_case(self, use_case: str) -> List[ModelInfo]:
        """
        Get models filtered by use case.
        
        Args:
            use_case: Use case to filter by (e.g., 'coding', 'chat')
            
        Returns:
            List of ModelInfo instances matching the use case
        """
        return [model for model in self.models.values() 
                if model.use_case == use_case and model.enabled]
    
    def get_models_by_tag(self, tag: str) -> List[ModelInfo]:
        """
        Get models filtered by tag.
        
        Args:
            tag: Tag to filter by
            
        Returns:
            List of ModelInfo instances with the tag
        """
        return [model for model in self.models.values() 
                if tag in model.tags and model.enabled]
    
    def get_recommended_models(self, hardware_info: Dict[str, Any]) -> List[str]:
        """
        Get recommended models based on hardware information.
        
        Args:
            hardware_info: Hardware information dictionary
            
        Returns:
            List of recommended model names
        """
        total_ram = hardware_info.get('total_ram_gb', 0)
        cpu_cores = hardware_info.get('cpu_cores', 0)
        
        # Find matching hardware profile
        profile_name = None
        for profile_name, profile_data in self.hardware_profiles.items():
            min_ram = profile_data.get('min_ram_gb', 0)
            max_ram = profile_data.get('max_ram_gb', float('inf'))
            
            if min_ram <= total_ram <= max_ram:
                return profile_data.get('recommended_models', [])
        
        # Fallback: recommend based on RAM if no profile matches
        recommended = []
        for model_name, model_info in self.models.items():
            if not model_info.enabled:
                continue
            
            # Check RAM requirements
            if total_ram < model_info.ram_required_gb:
                continue
            
            # Score the model
            score = 0
            
            # Prefer models that use 50-70% of available RAM
            ram_ratio = model_info.ram_required_gb / total_ram if total_ram > 0 else 0
            if 0.5 <= ram_ratio <= 0.7:
                score += 10
            elif 0.3 <= ram_ratio < 0.5:
                score += 5
            
            # Prefer smaller models for fewer CPU cores
            if cpu_cores <= 4 and model_info.parameters in ['1.5B', '3B']:
                score += 5
            
            # Prefer faster quantization for low-end systems
            if total_ram <= 8 and model_info.quantization == 'Q4_K_M':
                score += 3
            
            # Add performance score from registry
            score += model_info.performance_score
            
            recommended.append((model_name, score))
        
        # Sort by score and return names
        recommended.sort(key=lambda x: x[1], reverse=True)
        return [name for name, score in recommended]
    
    def validate_model_info(self, model_info: ModelInfo) -> List[str]:
        """
        Validate model information for completeness and correctness.
        
        Args:
            model_info: ModelInfo instance to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required fields
        if not model_info.name:
            errors.append("Model name is required")
        if not model_info.display_name:
            errors.append("Display name is required")
        if not model_info.download_url:
            errors.append("Download URL is required")
        
        # Validate numeric fields
        if model_info.file_size_gb <= 0:
            errors.append("File size must be positive")
        if model_info.ram_required_gb <= 0:
            errors.append("RAM required must be positive")
        if model_info.context_length <= 0:
            errors.append("Context length must be positive")
        
        # Validate URL format
        if not model_info.download_url.startswith(('http://', 'https://')):
            errors.append("Download URL must start with http:// or https://")
        
        # Validate checksum format
        if not model_info.checksum.startswith('sha256:'):
            errors.append("Checksum must start with 'sha256:'")
        
        return errors
    
    def get_category_models(self, category: str) -> List[str]:
        """
        Get models in a specific category.
        
        Args:
            category: Category name
            
        Returns:
            List of model names in the category
        """
        category_data = self.categories.get(category, {})
        return category_data.get('models', [])
    
    def get_categories(self) -> Dict[str, Dict[str, Any]]:
        """Get all categories."""
        return self.categories
    
    def get_hardware_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Get all hardware profiles."""
        return self.hardware_profiles
    
    def reload_registry(self):
        """Reload the model registry from configuration."""
        self.models.clear()
        self.categories.clear()
        self.hardware_profiles.clear()
        self._load_registry()


# Global registry instance
_registry = None


def get_model_registry() -> ModelRegistry:
    """
    Get global model registry instance.
    
    Returns:
        ModelRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry


# Example usage and testing
if __name__ == "__main__":
    # Test model registry
    print("Testing Model Registry...")
    
    registry = get_model_registry()
    
    # List all models
    models = registry.list_models()
    print(f"\nFound {len(models)} models:")
    for model in models:
        print(f"  - {model.name}: {model.display_name}")
    
    # Get specific model
    model = registry.get_model('qwen2.5-coder-1.5b-instruct')
    if model:
        print(f"\nModel details:")
        print(f"  Name: {model.name}")
        print(f"  Display: {model.display_name}")
        print(f"  Parameters: {model.parameters}")
        print(f"  RAM Required: {model.ram_required_gb} GB")
        print(f"  File Size: {model.file_size_gb} GB")
    
    # Get models by use case
    coding_models = registry.get_models_by_use_case('coding')
    print(f"\nCoding models: {len(coding_models)}")
    
    # Test hardware recommendations
    hardware_info = {
        'total_ram_gb': 8,
        'cpu_cores': 4
    }
    recommended = registry.get_recommended_models(hardware_info)
    print(f"\nRecommended models for 8GB RAM, 4 cores:")
    for model_name in recommended:
        print(f"  - {model_name}")
    
    # Validate model info
    if model:
        errors = registry.validate_model_info(model)
        if errors:
            print(f"\nValidation errors: {errors}")
        else:
            print("\nModel validation passed")
    
    print("\nModel registry test completed!")
