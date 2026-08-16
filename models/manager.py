"""
Local AI Platform - Model Manager
Handles model installation, removal, validation, and management.
"""

import sys
import os
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent.core import get_logger, get_config_manager
from models.registry import ModelRegistry, ModelInfo, get_model_registry


@dataclass
class InstalledModel:
    """Data class for installed model information."""
    name: str
    file_path: str
    file_size_bytes: int
    installed_at: str
    checksum_verified: bool
    last_used: Optional[str] = None


class ModelManager:
    """Manages model installation, removal, and validation."""
    
    def __init__(self, config_manager=None, registry=None):
        """
        Initialize model manager.
        
        Args:
            config_manager: Optional config manager instance
            registry: Optional model registry instance
        """
        self.logger = get_logger(__name__)
        self.config_manager = config_manager or get_config_manager()
        self.registry = registry or get_model_registry()
        
        # Get model directory from config
        self.models_dir = Path(self.config_manager.get('directories.models_dir', '~/.local-ai/models')).expanduser()
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Registry file for installed models
        self.registry_file = self.models_dir / '.registry.json'
        
        # Load installed models registry
        self.installed_models: Dict[str, InstalledModel] = {}
        self._load_installed_registry()
        
        self.logger.info(f"Model manager initialized with directory: {self.models_dir}")
    
    def _load_installed_registry(self):
        """Load installed models registry from file."""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r') as f:
                    data = json.load(f)
                
                for model_name, model_data in data.get('installed_models', {}).items():
                    self.installed_models[model_name] = InstalledModel(
                        name=model_name,
                        file_path=model_data['file'],
                        file_size_bytes=model_data['size_bytes'],
                        installed_at=model_data['installed_at'],
                        checksum_verified=model_data.get('checksum_verified', False),
                        last_used=model_data.get('last_used')
                    )
                
                self.logger.info(f"Loaded {len(self.installed_models)} installed models from registry")
                
            except Exception as e:
                self.logger.error(f"Failed to load installed models registry: {e}")
    
    def _save_installed_registry(self):
        """Save installed models registry to file."""
        try:
            data = {
                'installed_models': {},
                'default_model': self.config_manager.get('model.default'),
                'last_updated': datetime.utcnow().isoformat()
            }
            
            for model_name, installed_model in self.installed_models.items():
                data['installed_models'][model_name] = {
                    'file': installed_model.file_path,
                    'size_bytes': installed_model.file_size_bytes,
                    'installed_at': installed_model.installed_at,
                    'checksum_verified': installed_model.checksum_verified,
                    'last_used': installed_model.last_used
                }
            
            with open(self.registry_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.debug("Saved installed models registry")
            
        except Exception as e:
            self.logger.error(f"Failed to save installed models registry: {e}")
    
    def list_models(self, installed_only: bool = False) -> Dict[str, Any]:
        """
        List available and/or installed models.
        
        Args:
            installed_only: Only return installed models
            
        Returns:
            Dictionary with model information
        """
        result = {
            'available': [],
            'installed': [],
            'available_count': 0,
            'installed_count': 0
        }
        
        # Get available models from registry
        available_models = self.registry.list_models(enabled_only=True)
        result['available'] = [
            {
                'name': model.name,
                'display_name': model.display_name,
                'parameters': model.parameters,
                'quantization': model.quantization,
                'file_size_gb': model.file_size_gb,
                'ram_required_gb': model.ram_required_gb,
                'installed': model.name in self.installed_models
            }
            for model in available_models
        ]
        result['available_count'] = len(result['available'])
        
        # Get installed models
        if not installed_only:
            for model_name, installed_model in self.installed_models.items():
                model_info = self.registry.get_model(model_name)
                result['installed'].append({
                    'name': model_name,
                    'display_name': model_info.display_name if model_info else model_name,
                    'file_path': installed_model.file_path,
                    'file_size_gb': round(installed_model.file_size_bytes / (1024**3), 2),
                    'installed_at': installed_model.installed_at,
                    'checksum_verified': installed_model.checksum_verified,
                    'last_used': installed_model.last_used
                })
        
        result['installed_count'] = len(result['installed'])
        
        return result
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dictionary with model information or None if not found
        """
        # Get from registry
        model_info = self.registry.get_model(model_name)
        if not model_info:
            return None
        
        # Check if installed
        installed = self.installed_models.get(model_name)
        
        return {
            'name': model_info.name,
            'display_name': model_info.display_name,
            'description': model_info.description,
            'parameters': model_info.parameters,
            'quantization': model_info.quantization,
            'architecture': model_info.architecture,
            'context_length': model_info.context_length,
            'file_size_gb': model_info.file_size_gb,
            'ram_required_gb': model_info.ram_required_gb,
            'recommended_ram_gb': model_info.recommended_ram_gb,
            'download_url': model_info.download_url,
            'checksum': model_info.checksum,
            'use_case': model_info.use_case,
            'language': model_info.language,
            'license': model_info.license,
            'tags': model_info.tags,
            'enabled': model_info.enabled,
            'installed': installed is not None,
            'file_path': installed.file_path if installed else None,
            'installed_at': installed.installed_at if installed else None,
            'checksum_verified': installed.checksum_verified if installed else False
        }
    
    async def install_model_async(
        self, 
        model_name: str, 
        url: Optional[str] = None, 
        force: bool = False,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Download and install a model asynchronously.
        
        Args:
            model_name: Name of model to install
            url: Optional custom download URL
            force: Reinstall if already installed
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with installation result
        """
        result = {
            'success': False,
            'model_name': model_name,
            'error': None,
            'file_path': None
        }
        
        self.logger.info(f"Installing model: {model_name}")
        
        # Check if already installed
        if model_name in self.installed_models and not force:
            result['error'] = f"Model {model_name} already installed"
            self.logger.warning(result['error'])
            return result
        
        # Get model info from registry
        model_info = self.registry.get_model(model_name)
        if not model_info:
            result['error'] = f"Model {model_name} not found in registry"
            self.logger.error(result['error'])
            return result
        
        # Use custom URL if provided
        download_url = url or model_info.download_url
        
        # Check disk space
        if not self._check_disk_space(model_info.file_size_gb):
            result['error'] = "Insufficient disk space"
            return result
        
        # Determine file path
        file_name = f"{model_name}-{model_info.quantization}.gguf"
        file_path = self.models_dir / file_name
        
        # Download model using downloader
        from models.downloader import get_model_downloader
        downloader = get_model_downloader()
        
        self.logger.info(f"Downloading model from {download_url}")
        
        download_result = await downloader.download_with_retry(
            url=download_url,
            destination=file_path,
            expected_checksum=model_info.checksum,
            progress_callback=progress_callback
        )
        
        if not download_result['success']:
            result['error'] = download_result['error']
            return result
        
        # Verify GGUF format
        from models.gguf_validator import get_gguf_validator
        validator = get_gguf_validator()
        is_valid_gguf, _ = validator.validate_gguf_file(file_path)
        
        if not is_valid_gguf:
            result['error'] = "Downloaded file is not a valid GGUF file"
            file_path.unlink()  # Remove invalid file
            return result
        
        # Register installed model
        self.installed_models[model_name] = InstalledModel(
            name=model_name,
            file_path=str(file_path),
            file_size_bytes=file_path.stat().st_size,
            installed_at=datetime.utcnow().isoformat(),
            checksum_verified=download_result['checksum_verified']
        )
        
        # Set as default if first model
        if len(self.installed_models) == 1:
            self.config_manager.set('model.default', model_name)
            self.logger.info(f"Set {model_name} as default model")
        
        # Save registry
        self._save_installed_registry()
        
        result['success'] = True
        result['file_path'] = str(file_path)
        self.logger.info(f"Model {model_name} installed successfully")
        
        return result
    
    def install_model(self, model_name: str, url: Optional[str] = None, force: bool = False) -> bool:
        """
        Download and install a model (synchronous wrapper).
        
        Args:
            model_name: Name of model to install
            url: Optional custom download URL
            force: Reinstall if already installed
            
        Returns:
            True if successful, False otherwise
        """
        import asyncio
        
        # Run async installation
        result = asyncio.run(self.install_model_async(model_name, url, force))
        return result['success']
    
    def remove_model(self, model_name: str, force: bool = False) -> bool:
        """
        Remove an installed model.
        
        Args:
            model_name: Name of model to remove
            force: Skip confirmation
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Removing model: {model_name}")
        
        # Check if installed
        if model_name not in self.installed_models:
            self.logger.warning(f"Model {model_name} not installed")
            return False
        
        # Get installed model info
        installed_model = self.installed_models[model_name]
        
        # Check if it's the default model
        default_model = self.config_manager.get('model.default')
        if default_model == model_name:
            self.logger.warning(f"Model {model_name} is the default model")
            # TODO: Ask for confirmation or select new default
        
        # Remove file
        file_path = Path(installed_model.file_path)
        if file_path.exists():
            try:
                file_path.unlink()
                self.logger.info(f"Removed model file: {file_path}")
            except Exception as e:
                self.logger.error(f"Failed to remove model file: {e}")
                return False
        
        # Remove from registry
        del self.installed_models[model_name]
        
        # Update default if needed
        if default_model == model_name and self.installed_models:
            new_default = list(self.installed_models.keys())[0]
            self.config_manager.set('model.default', new_default)
            self.logger.info(f"Set {new_default} as new default model")
        elif default_model == model_name:
            self.config_manager.set('model.default', '')
        
        # Save registry
        self._save_installed_registry()
        
        self.logger.info(f"Model {model_name} removed successfully")
        return True
    
    def validate_model(self, model_name: str) -> bool:
        """
        Validate model file integrity.
        
        Args:
            model_name: Name of model to validate
            
        Returns:
            True if valid, False otherwise
        """
        self.logger.info(f"Validating model: {model_name}")
        
        # Check if installed
        if model_name not in self.installed_models:
            self.logger.error(f"Model {model_name} not installed")
            return False
        
        installed_model = self.installed_models[model_name]
        file_path = Path(installed_model.file_path)
        
        # Check if file exists
        if not file_path.exists():
            self.logger.error(f"Model file not found: {file_path}")
            return False
        
        # Get model info for checksum
        model_info = self.registry.get_model(model_name)
        if not model_info:
            self.logger.error(f"Model {model_name} not found in registry")
            return False
        
        # Verify checksum
        checksum_valid = self._verify_checksum(file_path, model_info.checksum)
        
        # Update installed model info
        installed_model.checksum_verified = checksum_valid
        self._save_installed_registry()
        
        return checksum_valid
    
    def get_default_model(self) -> Optional[str]:
        """
        Get the currently default model.
        
        Returns:
            Default model name or None if not set
        """
        return self.config_manager.get('model.default')
    
    def set_default_model(self, model_name: str) -> bool:
        """
        Set the default model.
        
        Args:
            model_name: Name of model to set as default
            
        Returns:
            True if successful, False otherwise
        """
        # Check if model exists in registry
        model_info = self.registry.get_model(model_name)
        if not model_info:
            self.logger.error(f"Model {model_name} not found in registry")
            return False
        
        # Set as default
        self.config_manager.set('model.default', model_name)
        self.logger.info(f"Set {model_name} as default model")
        
        return True
    
    def select_model(self, model_name: str) -> Dict[str, Any]:
        """
        Select a model for use (alias for set_default_model with more information).
        
        Args:
            model_name: Name of model to select
            
        Returns:
            Dictionary with selection result and model information
        """
        result = {
            'success': False,
            'model_name': model_name,
            'previous_model': self.get_default_model(),
            'model_info': None,
            'message': ''
        }
        
        # Check if model exists in registry
        model_info = self.registry.get_model(model_name)
        if not model_info:
            result['message'] = f"Model {model_name} not found in registry"
            return result
        
        # Check if model is installed
        if model_name not in self.installed_models:
            result['message'] = f"Model {model_name} is not installed. Install it first using: rakan model install {model_name}"
            return result
        
        # Check if model can run on current hardware
        from models.hardware_detector import get_hardware_detector
        detector = get_hardware_detector()
        if not detector.can_run_model(model_name):
            result['message'] = f"Model {model_name} may not run well on current hardware"
            # Still allow selection but warn user
        
        # Set as default
        if self.set_default_model(model_name):
            result['success'] = True
            result['model_info'] = self.get_model_info(model_name)
            result['message'] = f"Successfully selected {model_info.display_name} as default model"
            
            # Update last used time
            if model_name in self.installed_models:
                self.installed_models[model_name].last_used = datetime.utcnow().isoformat()
                self._save_installed_registry()
        else:
            result['message'] = f"Failed to set {model_name} as default model"
        
        return result
    
    def get_current_model(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the currently selected model.
        
        Returns:
            Dictionary with current model information or None if no model selected
        """
        current_model = self.get_default_model()
        if not current_model:
            return None
        
        return self.get_model_info(current_model)
    
    def switch_model(self, from_model: str, to_model: str) -> Dict[str, Any]:
        """
        Switch from one model to another.
        
        Args:
            from_model: Current model name
            to_model: Target model name
            
        Returns:
            Dictionary with switch result
        """
        result = {
            'success': False,
            'from_model': from_model,
            'to_model': to_model,
            'message': ''
        }
        
        # Verify current model
        current = self.get_default_model()
        if current and current != from_model:
            result['message'] = f"Current model is {current}, not {from_model}"
            return result
        
        # Select new model
        selection_result = self.select_model(to_model)
        
        if selection_result['success']:
            result['success'] = True
            result['message'] = f"Switched from {from_model} to {to_model}"
        else:
            result['message'] = selection_result['message']
        
        return result
    
    def get_recommended_models(self, hardware_info: Dict[str, Any]) -> List[str]:
        """
        Get models recommended for specific hardware.
        
        Args:
            hardware_info: Hardware information dictionary
            
        Returns:
            List of recommended model names
        """
        return self.registry.get_recommended_models(hardware_info)
    
    def _check_disk_space(self, required_gb: float) -> bool:
        """
        Check if sufficient disk space is available.
        
        Args:
            required_gb: Required disk space in GB
            
        Returns:
            True if sufficient space, False otherwise
        """
        import shutil
        
        disk_usage = shutil.disk_usage(self.models_dir)
        available_gb = disk_usage.free / (1024**3)
        
        if available_gb < required_gb + 1:  # Add 1GB buffer
            self.logger.error(f"Insufficient disk space: {available_gb:.2f}GB available, {required_gb}GB required")
            return False
        
        return True
    
    def _verify_checksum(self, file_path: Path, expected_checksum: str) -> bool:
        """
        Verify file checksum.
        
        Args:
            file_path: Path to file
            expected_checksum: Expected checksum (format: sha256:hash)
            
        Returns:
            True if checksum matches, False otherwise
        """
        # Parse expected checksum
        if not expected_checksum.startswith('sha256:'):
            self.logger.warning(f"Invalid checksum format: {expected_checksum}")
            return False
        
        expected_hash = expected_checksum.split(':', 1)[1]
        
        # Calculate actual checksum
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            
            actual_hash = sha256_hash.hexdigest()
            
            if actual_hash == expected_hash:
                self.logger.info(f"Checksum verified for {file_path}")
                return True
            else:
                self.logger.error(f"Checksum mismatch for {file_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to calculate checksum: {e}")
            return False


# Global model manager instance
_model_manager = None


def get_model_manager() -> ModelManager:
    """
    Get global model manager instance.
    
    Returns:
        ModelManager instance
    """
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager


# Example usage and testing
if __name__ == "__main__":
    # Test model manager
    print("Testing Model Manager...")
    
    manager = ModelManager()
    
    # List models
    models = manager.list_models()
    print(f"\nAvailable models: {models['available_count']}")
    print(f"Installed models: {models['installed_count']}")
    
    # Get model info
    model_info = manager.get_model_info('qwen2.5-coder-1.5b-instruct')
    if model_info:
        print(f"\nModel info:")
        print(f"  Name: {model_info['name']}")
        print(f"  Display: {model_info['display_name']}")
        print(f"  Installed: {model_info['installed']}")
    
    # Test installation (placeholder)
    print("\nTesting model installation (placeholder)...")
    success = manager.install_model('qwen2.5-coder-1.5b-instruct', force=True)
    print(f"Installation result: {success}")
    
    # List models after installation
    models = manager.list_models()
    print(f"Installed models after test: {models['installed_count']}")
    
    # Test validation
    print("\nTesting model validation...")
    valid = manager.validate_model('qwen2.5-coder-1.5b-instruct')
    print(f"Validation result: {valid}")
    
    # Test removal
    print("\nTesting model removal...")
    success = manager.remove_model('qwen2.5-coder-1.5b-instruct', force=True)
    print(f"Removal result: {success}")
    
    # Test hardware recommendations
    hardware_info = {
        'total_ram_gb': 8,
        'cpu_cores': 4
    }
    recommended = manager.get_recommended_models(hardware_info)
    print(f"\nRecommended models for 8GB RAM, 4 cores:")
    for model_name in recommended:
        print(f"  - {model_name}")
    
    print("\nModel manager test completed!")
