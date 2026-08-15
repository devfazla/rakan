"""
Local AI Platform - Logging Infrastructure
Provides centralized logging configuration and utilities for the entire platform.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional
import json
from datetime import datetime


class LocalAILogger:
    """Centralized logger for the Local AI platform."""
    
    _loggers = {}
    _audit_logger = None
    
    @classmethod
    def setup_logging(cls, config: dict):
        """
        Setup logging configuration based on config dictionary.
        
        Args:
            config: Configuration dictionary with logging settings
        """
        log_config = config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO').upper())
        log_format = log_config.get('format', 'text')
        
        # Create formatters
        if log_format == 'json':
            formatter = cls._get_json_formatter()
        else:
            formatter = cls._get_text_formatter()
        
        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console logging
        console_config = log_config.get('console', {})
        if console_config.get('enabled', True):
            console_level = getattr(logging, console_config.get('level', 'INFO').upper())
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(console_level)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # File logging
        file_config = log_config.get('file', {})
        if file_config.get('enabled', True):
            log_path = Path(file_config.get('path', '~/.local-ai/logs/local-ai.log')).expanduser()
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            max_size = file_config.get('max_size_mb', 10) * 1024 * 1024
            backup_count = file_config.get('backup_count', 5)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_path,
                maxBytes=max_size,
                backupCount=backup_count
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        
        # Setup audit logger
        if log_config.get('audit', {}).get('enabled', True):
            cls._setup_audit_logger(log_config)
    
    @classmethod
    def _get_text_formatter(cls) -> logging.Formatter:
        """Get text format formatter."""
        return logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    @classmethod
    def _get_json_formatter(cls) -> logging.Formatter:
        """Get JSON format formatter."""
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_data = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'level': record.levelname,
                    'logger': record.name,
                    'message': record.getMessage(),
                    'module': record.module,
                    'function': record.funcName,
                    'line': record.lineno
                }
                if record.exc_info:
                    log_data['exception'] = self.formatException(record.exc_info)
                return json.dumps(log_data)
        
        return JSONFormatter()
    
    @classmethod
    def _setup_audit_logger(cls, log_config: dict):
        """Setup audit logger for security events."""
        audit_config = log_config.get('audit', {})
        audit_path = Path(audit_config.get('path', '~/.local-ai/logs/audit.log')).expanduser()
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        
        cls._audit_logger = logging.getLogger('audit')
        cls._audit_logger.setLevel(logging.INFO)
        cls._audit_logger.handlers.clear()
        
        # Audit logger always uses JSON format
        formatter = cls._get_json_formatter()
        
        audit_handler = logging.handlers.RotatingFileHandler(
            audit_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10
        )
        audit_handler.setFormatter(formatter)
        cls._audit_logger.addHandler(audit_handler)
        
        # Prevent audit logs from propagating to root logger
        cls._audit_logger.propagate = False
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get a logger instance with the specified name.
        
        Args:
            name: Logger name (typically __name__ of the module)
            
        Returns:
            Logger instance
        """
        if name not in cls._loggers:
            cls._loggers[name] = logging.getLogger(name)
        return cls._loggers[name]
    
    @classmethod
    def log_audit_event(cls, event_type: str, data: dict):
        """
        Log a security/audit event.
        
        Args:
            event_type: Type of audit event
            data: Event data dictionary
        """
        if cls._audit_logger:
            audit_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'event_type': event_type,
                **data
            }
            cls._audit_logger.info(json.dumps(audit_data))
    
    @classmethod
    def shutdown(cls):
        """Shutdown all loggers and flush handlers."""
        logging.shutdown()


def get_logger(name: str) -> logging.Logger:
    """
    Convenience function to get a logger.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return LocalAILogger.get_logger(name)


def log_audit_event(event_type: str, data: dict):
    """
    Convenience function to log audit events.
    
    Args:
        event_type: Type of audit event
        data: Event data dictionary
    """
    LocalAILogger.log_audit_event(event_type, data)


# Example usage and testing
if __name__ == "__main__":
    # Test configuration
    test_config = {
        'logging': {
            'level': 'DEBUG',
            'format': 'text',
            'console': {
                'enabled': True,
                'level': 'DEBUG'
            },
            'file': {
                'enabled': True,
                'path': './test_logs/local-ai.log',
                'max_size_mb': 1,
                'backup_count': 3
            },
            'audit': {
                'enabled': True,
                'path': './test_logs/audit.log'
            }
        }
    }
    
    # Setup logging
    LocalAILogger.setup_logging(test_config)
    
    # Get logger and test
    logger = get_logger(__name__)
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Test audit logging
    log_audit_event('tool_execution', {
        'tool': 'read_file',
        'user': 'test_user',
        'file': '/test/file.txt',
        'result': 'success'
    })
    
    log_audit_event('permission_request', {
        'tool': 'run_command',
        'user': 'test_user',
        'command': 'ls -la',
        'decision': 'approved'
    })
    
    print("Logging test completed. Check test_logs/ directory for output.")
    LocalAILogger.shutdown()
