"""
Local AI Platform - Permission Manager
Manages permissions for agent operations.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging
import json

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PermissionLevel(Enum):
    """Permission levels for operations."""
    NONE = "none"
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


@dataclass
class PermissionRule:
    """Permission rule for a specific operation."""
    operation: str
    level: PermissionLevel
    allowed_paths: Optional[List[str]] = None
    denied_paths: Optional[List[str]] = None
    requires_confirmation: bool = False
    dangerous: bool = False


class PermissionManager:
    """Manages permissions for agent operations."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize permission manager.
        
        Args:
            config_path: Path to permissions configuration file
        """
        self.config_path = config_path
        self.rules: Dict[str, PermissionRule] = {}
        self.audit_log: List[Dict[str, Any]] = []
        
        # Load default rules
        self._load_default_rules()
        
        # Load custom rules if config provided
        if config_path:
            self._load_config(config_path)
    
    def _load_default_rules(self):
        """Load default permission rules."""
        # Filesystem permissions
        self.rules["read_file"] = PermissionRule(
            operation="read_file",
            level=PermissionLevel.READ,
            allowed_paths=None,
            denied_paths=["/etc", "/sys", "/proc", "~/.ssh", "~/.gnupg"],
            requires_confirmation=False
        )
        
        self.rules["list_directory"] = PermissionRule(
            operation="list_directory",
            level=PermissionLevel.READ,
            allowed_paths=None,
            denied_paths=["/etc", "/sys", "/proc", "~/.ssh", "~/.gnupg"],
            requires_confirmation=False
        )
        
        self.rules["search_files"] = PermissionRule(
            operation="search_files",
            level=PermissionLevel.READ,
            allowed_paths=None,
            denied_paths=["/etc", "/sys", "/proc", "~/.ssh", "~/.gnupg"],
            requires_confirmation=False
        )
        
        self.rules["write_file"] = PermissionRule(
            operation="write_file",
            level=PermissionLevel.WRITE,
            allowed_paths=None,
            denied_paths=["/etc", "/sys", "/proc", "~/.ssh", "~/.gnupg", "/usr", "/bin"],
            requires_confirmation=True
        )
        
        self.rules["delete_file"] = PermissionRule(
            operation="delete_file",
            level=PermissionLevel.WRITE,
            allowed_paths=None,
            denied_paths=["/etc", "/sys", "/proc", "~/.ssh", "~/.gnupg", "/usr", "/bin"],
            requires_confirmation=True
        )
        
        # Command execution permissions
        self.rules["execute_command"] = PermissionRule(
            operation="execute_command",
            level=PermissionLevel.EXECUTE,
            allowed_paths=None,
            denied_paths=["rm -rf", "dd", "mkfs", "format"],
            requires_confirmation=True
        )
        
        # Git permissions
        self.rules["git_status"] = PermissionRule(
            operation="git_status",
            level=PermissionLevel.READ,
            allowed_paths=None,
            denied_paths=None,
            requires_confirmation=False
        )
        
        self.rules["git_commit"] = PermissionRule(
            operation="git_commit",
            level=PermissionLevel.WRITE,
            allowed_paths=None,
            denied_paths=None,
            requires_confirmation=True
        )
        
        logger.info(f"Loaded {len(self.rules)} default permission rules")
    
    def _load_config(self, config_path: str):
        """Load custom permission configuration."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Override rules from config
            if 'rules' in config:
                for rule_data in config['rules']:
                    operation = rule_data.get('operation')
                    if operation:
                        level = PermissionLevel(rule_data.get('level', 'none'))
                        self.rules[operation] = PermissionRule(
                            operation=operation,
                            level=level,
                            allowed_paths=rule_data.get('allowed_paths'),
                            denied_paths=rule_data.get('denied_paths'),
                            requires_confirmation=rule_data.get('requires_confirmation', False)
                        )
            
            logger.info(f"Loaded custom permissions from {config_path}")
            
        except Exception as e:
            logger.warning(f"Failed to load permission config: {e}")
    
    def check_permission(self, operation: str, parameters: Dict[str, Any]) -> tuple[bool, str]:
        """
        Check if an operation is permitted.
        
        Args:
            operation: Operation to check
            parameters: Operation parameters
            
        Returns:
            Tuple of (allowed, reason)
        """
        rule = self.rules.get(operation)
        
        if not rule:
            # Unknown operation, deny by default
            return False, f"Unknown operation: {operation}"
        
        # Check if operation requires higher permission level
        if rule.level == PermissionLevel.NONE:
            return False, f"Operation not allowed: {operation}"
        
        # Check denied paths
        if rule.denied_paths:
            for denied_path in rule.denied_paths:
                if self._path_matches(parameters, denied_path):
                    return False, f"Operation denied for path: {denied_path}"
        
        # Special handling for execute_command - check denied commands
        if operation == "execute_command" and rule.denied_paths:
            for denied_command in rule.denied_paths:
                if self._command_matches(parameters, denied_command):
                    return False, f"Operation denied for command: {denied_command}"
        
        # Check allowed paths (if specified)
        if rule.allowed_paths:
            allowed = False
            for allowed_path in rule.allowed_paths:
                if self._path_matches(parameters, allowed_path):
                    allowed = True
                    break
            
            if not allowed:
                return False, f"Operation not allowed for specified paths"
        
        # Check if confirmation required
        if rule.requires_confirmation:
            return True, f"Confirmation required for: {operation}"
        
        return True, "Operation allowed"
    
    def _path_matches(self, parameters: Dict[str, Any], path_pattern: str) -> bool:
        """
        Check if operation parameters match a path pattern.
        
        Args:
            parameters: Operation parameters
            path_pattern: Path pattern to match
            
        Returns:
            True if matches, False otherwise
        """
        # Get file path from parameters
        file_path = parameters.get('file_path') or parameters.get('directory') or parameters.get('path')
        
        if not file_path:
            return False
        
        # Simple path matching
        return file_path.startswith(path_pattern) or path_pattern in file_path
    
    def _command_matches(self, parameters: Dict[str, Any], command_pattern: str) -> bool:
        """
        Check if command matches a dangerous pattern.
        
        Args:
            parameters: Operation parameters
            command_pattern: Command pattern to match
            
        Returns:
            True if matches, False otherwise
        """
        command = parameters.get('command', '')
        
        if not command:
            return False
        
        # Simple command matching
        return command_pattern in command or command.startswith(command_pattern)
    
    def log_operation(self, operation: str, parameters: Dict[str, Any], allowed: bool, result: Optional[Any] = None):
        """
        Log an operation for audit purposes.
        
        Args:
            operation: Operation performed
            parameters: Operation parameters
            allowed: Whether operation was allowed
            result: Operation result if executed
        """
        from datetime import datetime
        
        # Extract success status from result if it's a ToolResult
        success = None
        output = None
        if result:
            # Handle both ToolResult and dict-like results
            if hasattr(result, 'success'):
                success = result.success
                if hasattr(result, 'output'):
                    output = result.output[:500] if result.output else None  # Truncate output
            elif isinstance(result, dict):
                success = result.get('success')
                output = result.get('output', '')[:500] if result.get('output') else None
        
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'operation': operation,
            'parameters': parameters,
            'allowed': allowed,
            'result': {
                'success': success,
                'output': output
            } if result else None
        }
        
        self.audit_log.append(log_entry)
        logger.info(f"Audit log: {operation} - {'allowed' if allowed else 'denied'}")
    
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get audit log entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of audit log entries
        """
        return self.audit_log[-limit:]
    
    def add_rule(self, rule: PermissionRule):
        """
        Add a custom permission rule.
        
        Args:
            rule: Permission rule to add
        """
        self.rules[rule.operation] = rule
        logger.info(f"Added custom rule for: {rule.operation}")
    
    def remove_rule(self, operation: str) -> bool:
        """
        Remove a permission rule.
        
        Args:
            operation: Operation to remove rule for
            
        Returns:
            True if removed, False if not found
        """
        if operation in self.rules:
            del self.rules[operation]
            logger.info(f"Removed rule for: {operation}")
            return True
        return False
    
    def get_rules(self) -> Dict[str, PermissionRule]:
        """
        Get all permission rules.
        
        Returns:
            Dictionary of permission rules
        """
        return self.rules.copy()


# Global permission manager instance
_permission_manager = None


def get_permission_manager(config_path: Optional[str] = None) -> PermissionManager:
    """
    Get global permission manager instance.
    
    Args:
        config_path: Optional path to permissions configuration
        
    Returns:
        PermissionManager instance
    """
    global _permission_manager
    if _permission_manager is None:
        _permission_manager = PermissionManager(config_path)
    return _permission_manager


# Example usage and testing
if __name__ == "__main__":
    # Test permission manager
    print("Testing Permission Manager...")
    
    manager = get_permission_manager()
    
    # Test permission checks
    print(f"\nPermission checks:")
    
    # Safe operation
    allowed, reason = manager.check_permission("read_file", {"file_path": "README.md"})
    print(f"  read_file (README.md): {allowed} - {reason}")
    
    # Dangerous operation without confirmation
    allowed, reason = manager.check_permission("write_file", {"file_path": "test.txt"})
    print(f"  write_file (test.txt): {allowed} - {reason}")
    
    # Dangerous operation in denied path
    allowed, reason = manager.check_permission("write_file", {"file_path": "/etc/hosts"})
    print(f"  write_file (/etc/hosts): {allowed} - {reason}")
    
    # Command execution
    allowed, reason = manager.check_permission("execute_command", {"command": "ls"})
    print(f"  execute_command (ls): {allowed} - {reason}")
    
    # Dangerous command
    allowed, reason = manager.check_permission("execute_command", {"command": "rm -rf /"})
    print(f"  execute_command (rm -rf /): {allowed} - {reason}")
    
    # Get rules
    print(f"\nActive rules: {list(manager.get_rules().keys())}")
    
    # Test audit logging
    print(f"\nTesting audit logging...")
    manager.log_operation("read_file", {"file_path": "README.md"}, True)
    manager.log_operation("write_file", {"file_path": "test.txt"}, False)
    
    audit_log = manager.get_audit_log()
    print(f"Audit log entries: {len(audit_log)}")
    
    print("\nPermission manager test completed!")
