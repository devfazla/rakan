"""
Local AI Platform - Configuration Management
Handles loading, validation, and access to configuration files.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from .logger import get_logger


class ConfigManager:
    """Manages configuration loading and access."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Optional custom configuration directory
        """
        self.logger = get_logger(__name__)
        self.config_dir = Path(config_dir) if config_dir else self._get_default_config_dir()
        self.config = {}
        self.loaded = False
        
    def _get_default_config_dir(self) -> Path:
        """Get default configuration directory."""
        # Try project-local config first
        project_config = Path.cwd() / 'config'
        if project_config.exists():
            return project_config
        
        # Fall back to user config directory
        user_config = Path.home() / '.config' / 'local-ai'
        return user_config
    
    def load_config(self, config_name: str = 'default') -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Args:
            config_name: Name of configuration file (without .yaml extension)
            
        Returns:
            Configuration dictionary
        """
        config_path = self.config_dir / f'{config_name}.yaml'
        
        if not config_path.exists():
            self.logger.warning(f"Config file not found: {config_path}, using defaults")
            return self._get_default_config()
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            self.config[config_name] = config
            self.logger.info(f"Loaded configuration from {config_path}")
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to load config from {config_path}: {e}")
            return self._get_default_config()
    
    def load_all_configs(self) -> Dict[str, Any]:
        """
        Load all configuration files from config directory.
        
        Returns:
            Dictionary with all loaded configurations
        """
        configs = {}
        
        # Load default config first
        configs['default'] = self.load_config('default')
        
        # Load other config files
        config_files = ['models', 'permissions']
        for config_name in config_files:
            config_path = self.config_dir / f'{config_name}.yaml'
            if config_path.exists():
                configs[config_name] = self.load_config(config_name)
        
        self.config = configs
        self.loaded = True
        return configs
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'model.default')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        if not self.loaded:
            self.load_all_configs()
        
        keys = key.split('.')
        value = self.config.get('default', self.config)  # Start with default config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value (in memory only).
        
        Args:
            key: Configuration key (dot notation)
            value: Value to set
        """
        if not self.loaded:
            self.load_all_configs()
        
        keys = key.split('.')
        config = self.config.get('default', self.config)  # Start with default config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save_config(self, config_name: str = 'default') -> bool:
        """
        Save configuration to file.
        
        Args:
            config_name: Name of configuration to save
            
        Returns:
            True if successful, False otherwise
        """
        if config_name not in self.config:
            self.logger.error(f"Configuration {config_name} not loaded")
            return False
        
        config_path = self.config_dir / f'{config_name}.yaml'
        
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w') as f:
                yaml.dump(self.config[config_name], f, default_flow_style=False)
            
            self.logger.info(f"Saved configuration to {config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save config to {config_path}: {e}")
            return False
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if no config file exists."""
        return {
            'application': {
                'name': 'Local AI',
                'version': '0.1.0',
                'debug': False,
                'log_level': 'INFO'
            },
            'logging': {
                'level': 'INFO',
                'format': 'text',
                'console': {'enabled': True, 'level': 'INFO'},
                'file': {'enabled': True, 'path': '~/.local-ai/logs/local-ai.log'},
                'audit': {'enabled': True, 'path': '~/.local-ai/logs/audit.log'}
            }
        }
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get model-specific configuration."""
        return self.config.get('models', {})
    
    def get_permissions_config(self) -> Dict[str, Any]:
        """Get permissions-specific configuration."""
        return self.config.get('permissions', {})
    
    def get_app_config(self) -> Dict[str, Any]:
        """Get application configuration."""
        return self.config.get('default', {}).get('application', {})


# Global configuration manager instance
_config_manager = None


def get_config_manager(config_dir: Optional[str] = None) -> ConfigManager:
    """
    Get global configuration manager instance.
    
    Args:
        config_dir: Optional custom configuration directory
        
    Returns:
        ConfigManager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_dir)
    return _config_manager


def setup_logging_from_config() -> None:
    """Setup logging using configuration from config manager."""
    from .logger import LocalAILogger
    
    config_manager = get_config_manager()
    config_manager.load_all_configs()
    
    LocalAILogger.setup_logging(config_manager.config.get('default', {}))


# Example usage and testing
if __name__ == "__main__":
    # Test configuration loading
    config_manager = ConfigManager()
    
    print("Loading configurations...")
    configs = config_manager.load_all_configs()
    
    print(f"\nLoaded configs: {list(configs.keys())}")
    
    # Test getting values
    print(f"\nApp name: {config_manager.get('application.name')}")
    print(f"Log level: {config_manager.get('logging.level')}")
    print(f"Default model: {config_manager.get('model.default')}")
    
    # Test model config
    model_config = config_manager.get_model_config()
    print(f"\nAvailable models: {list(model_config.get('models', {}).keys())}")
    
    # Test permissions config
    permissions_config = config_manager.get_permissions_config()
    print(f"Permission levels: {list(permissions_config.get('permission_levels', {}).keys())}")
    
    print("\nConfiguration test completed successfully!")
