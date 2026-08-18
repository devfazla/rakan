"""
Local AI Platform - Doctor Command
System health diagnostics and configuration verification.
"""

import platform
import sys
import os
from pathlib import Path
from typing import Dict, Any, List
import psutil

from agent.core import get_logger, get_config_manager
from cli.utils import terminal


class SystemDoctor:
    """System health diagnostics and configuration verification."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config_manager = get_config_manager()
        self.issues = []
        self.warnings = []
        self.info = []
        
    def check_system(self, detailed: bool = False) -> Dict[str, Any]:
        """
        Perform comprehensive system health check.
        
        Args:
            detailed: Whether to show detailed diagnostic information
            
        Returns:
            Dictionary with system health information
        """
        self.logger.info("Starting system health check...")
        
        # Gather system information
        system_info = self._gather_system_info()
        
        # Check configuration
        config_status = self._check_configuration()
        
        # Check dependencies
        dependency_status = self._check_dependencies()
        
        # Check disk space
        disk_status = self._check_disk_space()
        
        # Check memory
        memory_status = self._check_memory()
        
        # Check model directory
        model_status = self._check_model_directory()
        
        # Compile results
        results = {
            'system_info': system_info,
            'configuration': config_status,
            'dependencies': dependency_status,
            'disk_space': disk_status,
            'memory': memory_status,
            'models': model_status,
            'issues': self.issues,
            'warnings': self.warnings,
            'info': self.info
        }
        
        self.logger.info(f"System check completed: {len(self.issues)} issues, {len(self.warnings)} warnings")
        
        return results
    
    def _gather_system_info(self) -> Dict[str, Any]:
        """Gather basic system information."""
        self.logger.info("Gathering system information...")
        
        info = {
            'os': platform.system(),
            'os_version': platform.version(),
            'os_release': platform.release(),
            'architecture': platform.machine(),
            'python_version': platform.python_version(),
            'cpu_cores': psutil.cpu_count(),
            'cpu_freq': psutil.cpu_freq().current if psutil.cpu_freq() else None,
            'total_memory_gb': round(psutil.virtual_memory().total / (1024**3), 2),
            'available_memory_gb': round(psutil.virtual_memory().available / (1024**3), 2)
        }
        
        self.info.append(f"OS: {info['os']} {info['os_release']}")
        self.info.append(f"Python: {info['python_version']}")
        self.info.append(f"CPU: {info['cpu_cores']} cores @ {info['cpu_freq']} MHz" if info['cpu_freq'] else f"CPU: {info['cpu_cores']} cores")
        self.info.append(f"Memory: {info['total_memory_gb']} GB total, {info['available_memory_gb']} GB available")
        
        return info
    
    def _check_configuration(self) -> Dict[str, Any]:
        """Check configuration files and settings."""
        self.logger.info("Checking configuration...")
        
        status = {
            'config_dir_exists': False,
            'default_config_exists': False,
            'models_config_exists': False,
            'permissions_config_exists': False,
            'config_valid': False
        }
        
        # Check configuration directory
        config_dir = Path.home() / '.config' / 'local-ai'
        project_config = Path.cwd() / 'config'
        
        if project_config.exists():
            config_dir = project_config
            self.info.append(f"Using project config directory: {config_dir}")
        else:
            self.info.append(f"Using user config directory: {config_dir}")
        
        status['config_dir_exists'] = config_dir.exists()
        
        if not status['config_dir_exists']:
            self.issues.append("Configuration directory does not exist")
            return status
        
        # Check individual config files
        default_config = config_dir / 'default.yaml'
        models_config = config_dir / 'models.yaml'
        permissions_config = config_dir / 'permissions.yaml'
        
        status['default_config_exists'] = default_config.exists()
        status['models_config_exists'] = models_config.exists()
        status['permissions_config_exists'] = permissions_config.exists()
        
        if not status['default_config_exists']:
            self.issues.append("Default configuration file missing")
        else:
            self.info.append("Default configuration found")
        
        if not status['models_config_exists']:
            self.warnings.append("Models configuration file missing")
        else:
            self.info.append("Models configuration found")
        
        if not status['permissions_config_exists']:
            self.warnings.append("Permissions configuration file missing")
        else:
            self.info.append("Permissions configuration found")
        
        # Try to load configuration
        try:
            self.config_manager.load_all_configs()
            status['config_valid'] = True
            self.info.append("Configuration loaded successfully")
        except Exception as e:
            self.issues.append(f"Failed to load configuration: {e}")
        
        return status
    
    def _check_dependencies(self) -> Dict[str, Any]:
        """Check required dependencies."""
        self.logger.info("Checking dependencies...")
        
        status = {
            'python_ok': True,
            'missing_packages': [],
            'recommended_packages': []
        }
        
        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 8):
            status['python_ok'] = False
            self.issues.append(f"Python 3.8+ required, found {python_version.major}.{python_version.minor}")
        else:
            self.info.append(f"Python version OK: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # Check required packages
        required_packages = ['yaml', 'psutil']
        for package in required_packages:
            try:
                __import__(package)
                self.info.append(f"Package OK: {package}")
            except ImportError:
                status['missing_packages'].append(package)
                self.issues.append(f"Missing required package: {package}")
        
        # Check recommended packages
        recommended_packages = ['aiohttp', 'aiofiles', 'tqdm']
        for package in recommended_packages:
            try:
                __import__(package)
                self.info.append(f"Recommended package installed: {package}")
            except ImportError:
                status['recommended_packages'].append(package)
                self.warnings.append(f"Recommended package missing: {package}")
        
        return status
    
    def _check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space."""
        self.logger.info("Checking disk space...")
        
        status = {
            'disk_ok': True,
            'total_gb': 0,
            'available_gb': 0,
            'used_percent': 0
        }
        
        try:
            disk = psutil.disk_usage('/')
            status['total_gb'] = round(disk.total / (1024**3), 2)
            status['available_gb'] = round(disk.free / (1024**3), 2)
            status['used_percent'] = round(disk.percent, 2)
            
            self.info.append(f"Disk space: {status['available_gb']} GB available of {status['total_gb']} GB total")
            
            # Warn if less than 5GB available
            if status['available_gb'] < 5:
                status['disk_ok'] = False
                self.issues.append(f"Insufficient disk space: {status['available_gb']} GB available, 5 GB recommended")
            elif status['available_gb'] < 10:
                self.warnings.append(f"Low disk space: {status['available_gb']} GB available")
            
        except Exception as e:
            self.warnings.append(f"Could not check disk space: {e}")
        
        return status
    
    def _check_memory(self) -> Dict[str, Any]:
        """Check memory availability."""
        self.logger.info("Checking memory...")
        
        status = {
            'memory_ok': True,
            'total_gb': 0,
            'available_gb': 0,
            'recommended_for_models': []
        }
        
        try:
            memory = psutil.virtual_memory()
            status['total_gb'] = round(memory.total / (1024**3), 2)
            status['available_gb'] = round(memory.available / (1024**3), 2)
            
            # Provide model recommendations based on memory
            if status['total_gb'] >= 16:
                status['recommended_for_models'] = ['3B models', '7B models (if available)']
                self.info.append("Memory sufficient for all model sizes")
            elif status['total_gb'] >= 8:
                status['recommended_for_models'] = ['1.5B models', '3B models']
                self.info.append("Memory sufficient for small to medium models")
            elif status['total_gb'] >= 4:
                status['recommended_for_models'] = ['1.5B models']
                self.info.append("Memory sufficient for small models only")
                self.warnings.append("Limited memory for larger models")
            else:
                status['memory_ok'] = False
                self.issues.append(f"Insufficient memory: {status['total_gb']} GB, 4 GB minimum required")
        
        except Exception as e:
            self.warnings.append(f"Could not check memory: {e}")
        
        return status
    
    def _check_model_directory(self) -> Dict[str, Any]:
        """Check model directory and installed models."""
        self.logger.info("Checking model directory...")
        
        status = {
            'model_dir_exists': False,
            'installed_models': [],
            'default_model_set': False
        }
        
        try:
            # Get model directory from config
            models_dir = Path(self.config_manager.get('directories.models_dir', '~/.local-ai/models')).expanduser()
            
            status['model_dir_exists'] = models_dir.exists()
            
            if not status['model_dir_exists']:
                self.warnings.append(f"Model directory does not exist: {models_dir}")
                self.info.append("Run model installation to set up model directory")
                return status
            
            self.info.append(f"Model directory: {models_dir}")
            
            # Check for GGUF files
            gguf_files = list(models_dir.glob('*.gguf'))
            status['installed_models'] = [f.name for f in gguf_files]
            
            if status['installed_models']:
                self.info.append(f"Found {len(status['installed_models'])} installed model(s)")
                for model in status['installed_models']:
                    self.info.append(f"  - {model}")
            else:
                self.warnings.append("No models installed")
                self.info.append("Install models using: rakan model install <model-name>")
            
            # Check default model setting
            default_model = self.config_manager.get('model.default')
            if default_model:
                status['default_model_set'] = True
                self.info.append(f"Default model: {default_model}")
            else:
                self.warnings.append("No default model configured")
            
        except Exception as e:
            self.warnings.append(f"Could not check model directory: {e}")
        
        return status
    
    def print_report(self, results: Dict[str, Any], detailed: bool = False):
        """Print formatted diagnostic report."""
        terminal.print_header("RAKAN SYSTEM HEALTH REPORT")
        
        # System Information
        terminal.print_section("SYSTEM INFORMATION")
        sys_info = results['system_info']
        terminal.print_key_value("OS", f"{sys_info['os']} {sys_info['os_release']}")
        terminal.print_key_value("Architecture", sys_info['architecture'])
        terminal.print_key_value("Python", sys_info['python_version'])
        terminal.print_key_value("CPU Cores", str(sys_info['cpu_cores']))
        terminal.print_key_value("Total Memory", f"{sys_info['total_memory_gb']} GB")
        terminal.print_key_value("Available Memory", f"{sys_info['available_memory_gb']} GB")
        
        # Configuration Status
        terminal.print_section("CONFIGURATION STATUS")
        config = results['configuration']
        terminal.print_key_value("Config Directory", "OK" if config['config_dir_exists'] else "MISSING")
        terminal.print_key_value("Default Config", "OK" if config['default_config_exists'] else "MISSING")
        terminal.print_key_value("Models Config", "OK" if config['models_config_exists'] else "MISSING")
        terminal.print_key_value("Permissions Config", "OK" if config['permissions_config_exists'] else "MISSING")
        terminal.print_key_value("Config Valid", "YES" if config['config_valid'] else "NO")
        
        # Dependency Status
        terminal.print_section("DEPENDENCY STATUS")
        deps = results['dependencies']
        terminal.print_key_value("Python Version", "OK" if deps['python_ok'] else "NOT OK")
        terminal.print_key_value("Required Packages", f"{len(deps['missing_packages'])} missing")
        terminal.print_key_value("Recommended Packages", f"{len(deps['recommended_packages'])} missing")
        if deps['missing_packages']:
            terminal.print_key_value("Missing", ', '.join(deps['missing_packages']))
        
        # Resource Status
        terminal.print_section("RESOURCE STATUS")
        disk = results['disk_space']
        memory = results['memory']
        terminal.print_key_value("Disk Space", f"{disk['available_gb']} GB available")
        terminal.print_key_value("Memory", f"{memory['available_gb']} GB available")
        terminal.print_key_value("Recommended Models", ', '.join(memory['recommended_for_models']) if memory['recommended_for_models'] else 'None')
        
        # Model Status
        terminal.print_section("MODEL STATUS")
        models = results['models']
        terminal.print_key_value("Model Directory", "OK" if models['model_dir_exists'] else "MISSING")
        terminal.print_key_value("Installed Models", str(len(models['installed_models'])))
        terminal.print_key_value("Default Model", "SET" if models['default_model_set'] else "NOT SET")
        if models['installed_models']:
            terminal.print_subsection("Installed")
            for model in models['installed_models']:
                terminal.print_list_item(model)
        
        # Issues and Warnings
        if results['issues']:
            print("ISSUES:")
            print("-" * 40)
            for i, issue in enumerate(results['issues'], 1):
                print(f"  {i}. {issue}")
            print()
        
        if results['warnings']:
            print("WARNINGS:")
            print("-" * 40)
            for i, warning in enumerate(results['warnings'], 1):
                print(f"  {i}. {warning}")
            print()
        
        # Summary
        print("="*60)
        issue_count = len(results['issues'])
        warning_count = len(results['warnings'])
        
        if issue_count == 0 and warning_count == 0:
            print("STATUS: ALL SYSTEMS OK")
        elif issue_count == 0:
            print(f"STATUS: OK with {warning_count} warning(s)")
        else:
            print(f"STATUS: {issue_count} issue(s) found")
        
        print("="*60 + "\n")
        
        # Recommendations
        if issue_count > 0 or warning_count > 0:
            print("RECOMMENDATIONS:")
            print("-" * 40)
            
            if results['dependencies']['missing_packages']:
                print("  - Install missing packages:")
                print(f"    pip install {' '.join(results['dependencies']['missing_packages'])}")
            
            if not results['models']['installed_models']:
                print("  - Install a model:")
                print("    rakan model list")
                print("    rakan model install <model-name>")
            
            if not results['configuration']['config_valid']:
                print("  - Check configuration files")
                print("  - Ensure config directory exists and contains required files")
            
            print()


def run_doctor(detailed: bool = False, fix: bool = False) -> int:
    """
    Run system diagnostics.
    
    Args:
        detailed: Show detailed information
        fix: Attempt to fix issues automatically
        
    Returns:
        Exit code (0 for success, 1 for issues)
    """
    doctor = SystemDoctor()
    results = doctor.check_system(detailed=detailed)
    doctor.print_report(results, detailed=detailed)
    
    # Return exit code based on issues
    return 1 if results['issues'] else 0