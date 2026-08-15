"""
Unit tests for configuration management.
"""

import unittest
import tempfile
import yaml
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agent.core import ConfigManager


class TestConfigManager(unittest.TestCase):
    """Test cases for ConfigManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager(self.temp_dir)
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_config_manager_initialization(self):
        """Test ConfigManager initialization."""
        self.assertIsNotNone(self.config_manager)
        self.assertEqual(self.config_manager.config_dir, Path(self.temp_dir))
        self.assertFalse(self.config_manager.loaded)
    
    def test_get_default_config(self):
        """Test getting default configuration."""
        default_config = self.config_manager._get_default_config()
        
        self.assertIn('application', default_config)
        self.assertIn('logging', default_config)
        self.assertEqual(default_config['application']['name'], 'Local AI')
    
    def test_load_config_nonexistent_file(self):
        """Test loading configuration from non-existent file."""
        config = self.config_manager.load_config('nonexistent')
        
        # Should return default config
        self.assertIn('application', config)
        self.assertEqual(config['application']['name'], 'Local AI')
    
    def test_load_config_valid_file(self):
        """Test loading configuration from valid YAML file."""
        # Create test config file
        test_config = {
            'application': {
                'name': 'Test App',
                'version': '1.0.0'
            }
        }
        
        config_path = Path(self.temp_dir) / 'test.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        # Load configuration
        config = self.config_manager.load_config('test')
        
        self.assertEqual(config['application']['name'], 'Test App')
        self.assertEqual(config['application']['version'], '1.0.0')
    
    def test_get_config_value(self):
        """Test getting configuration values with dot notation."""
        # Create test config
        test_config = {
            'model': {
                'default': 'test-model',
                'context_size': 2048
            }
        }
        
        self.config_manager.config = {'default': test_config}
        self.config_manager.loaded = True
        
        # Test getting values
        self.assertEqual(self.config_manager.get('model.default'), 'test-model')
        self.assertEqual(self.config_manager.get('model.context_size'), 2048)
        self.assertEqual(self.config_manager.get('model.nonexistent', 'default'), 'default')
    
    def test_set_config_value(self):
        """Test setting configuration values."""
        self.config_manager.config = {'default': {}}
        self.config_manager.loaded = True
        
        # Set values
        self.config_manager.set('model.default', 'new-model')
        self.config_manager.set('model.context_size', 4096)
        
        # Verify values - need to use the config directly since get() looks in default
        self.assertEqual(self.config_manager.config['default']['model']['default'], 'new-model')
        self.assertEqual(self.config_manager.config['default']['model']['context_size'], 4096)
    
    def test_save_config(self):
        """Test saving configuration to file."""
        # Create test config
        test_config = {
            'application': {
                'name': 'Saved App',
                'version': '2.0.0'
            }
        }
        
        self.config_manager.config = {'default': test_config}
        self.config_manager.loaded = True
        
        # Save configuration
        result = self.config_manager.save_config('default')
        
        self.assertTrue(result)
        
        # Verify file was created
        config_path = Path(self.temp_dir) / 'default.yaml'
        self.assertTrue(config_path.exists())
        
        # Verify content
        with open(config_path, 'r') as f:
            loaded_config = yaml.safe_load(f)
        
        self.assertEqual(loaded_config['application']['name'], 'Saved App')


if __name__ == '__main__':
    unittest.main()
