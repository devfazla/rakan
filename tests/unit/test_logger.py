"""
Unit tests for logging infrastructure.
"""

import unittest
import tempfile
import logging
from pathlib import Path
import sys
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agent.core import LocalAILogger, get_logger, log_audit_event


class TestLocalAILogger(unittest.TestCase):
    """Test cases for LocalAILogger class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_config = {
            'logging': {
                'level': 'DEBUG',
                'format': 'text',
                'console': {
                    'enabled': False,  # Disable console for tests
                    'level': 'DEBUG'
                },
                'file': {
                    'enabled': True,
                    'path': str(Path(self.temp_dir) / 'test.log'),
                    'max_size_mb': 1,
                    'backup_count': 3
                },
                'audit': {
                    'enabled': True,
                    'path': str(Path(self.temp_dir) / 'audit.log')
                }
            }
        }
        
    def tearDown(self):
        """Clean up test fixtures."""
        LocalAILogger.shutdown()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_setup_logging(self):
        """Test logging setup."""
        LocalAILogger.setup_logging(self.test_config)
        
        # Verify log files were created
        log_path = Path(self.temp_dir) / 'test.log'
        audit_path = Path(self.temp_dir) / 'audit.log'
        
        # Files should exist after logging
        self.assertTrue(log_path.parent.exists())
        self.assertTrue(audit_path.parent.exists())
    
    def test_get_logger(self):
        """Test getting logger instance."""
        LocalAILogger.setup_logging(self.test_config)
        
        logger = get_logger('test_logger')
        
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, 'test_logger')
    
    def test_logger_caching(self):
        """Test that loggers are cached."""
        LocalAILogger.setup_logging(self.test_config)
        
        logger1 = get_logger('cached_logger')
        logger2 = get_logger('cached_logger')
        
        # Should return the same instance
        self.assertIs(logger1, logger2)
    
    def test_log_levels(self):
        """Test different log levels."""
        LocalAILogger.setup_logging(self.test_config)
        
        logger = get_logger('test_levels')
        
        # Should not raise exceptions
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
    
    def test_audit_logging(self):
        """Test audit event logging."""
        LocalAILogger.setup_logging(self.test_config)
        
        # Log audit event
        log_audit_event('test_event', {
            'user': 'test_user',
            'action': 'test_action',
            'result': 'success'
        })
        
        # Verify audit log was created
        audit_path = Path(self.temp_dir) / 'audit.log'
        self.assertTrue(audit_path.exists())
        
        # Verify log content
        with open(audit_path, 'r') as f:
            content = f.read()
        
        self.assertIn('test_event', content)
        self.assertIn('test_user', content)
    
    def test_json_formatter(self):
        """Test JSON log formatting."""
        json_config = self.test_config.copy()
        json_config['logging']['format'] = 'json'
        
        LocalAILogger.setup_logging(json_config)
        
        logger = get_logger('json_test')
        logger.info("Test message")
        
        # Verify log file contains JSON
        log_path = Path(self.temp_dir) / 'test.log'
        with open(log_path, 'r') as f:
            content = f.read()
        
        # Should be valid JSON
        try:
            log_entry = json.loads(content.strip())
            self.assertIn('timestamp', log_entry)
            self.assertIn('level', log_entry)
            self.assertIn('message', log_entry)
        except json.JSONDecodeError:
            self.fail("Log output is not valid JSON")


if __name__ == '__main__':
    unittest.main()
