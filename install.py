#!/usr/bin/env python3
"""
RAKAN - One-Click Installer
This script handles the complete installation of RAKAN on the user's system.
"""

import sys
import os
import subprocess
import shutil
from pathlib import Path
import urllib.request
import tarfile
import zipfile
import platform
import tempfile
import json
from typing import Optional, Tuple


class RakanInstaller:
    """RAKAN installation manager with colored CLI interface."""
    
    # ANSI color codes
    COLORS = {
        'reset': '\033[0m',
        'bold': '\033[1m',
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
    }
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="rakan_install_")
        self.install_dir = Path.home() / ".rakan"
        self.config_dir = Path.home() / ".config" / "rakan"
        self.models_dir = self.install_dir / "models"
        self.system = platform.system().lower()
        self.arch = platform.machine().lower()
        
    def color_print(self, text: str, color: str = 'white', bold: bool = False):
        """Print colored text to console."""
        if not sys.stdout.isatty() or self.system == 'windows':
            # Windows doesn't support ANSI codes well, print plain text
            print(text)
            return
            
        color_code = self.COLORS.get(color, self.COLORS['white'])
        if bold:
            color_code = self.COLORS['bold'] + color_code
        print(f"{color_code}{text}{self.COLORS['reset']}")
    
    def print_header(self):
        """Print installation header."""
        self.color_print("=" * 60, 'cyan', bold=True)
        self.color_print("    RAKAN - Local AI Development Platform", 'cyan', bold=True)
        self.color_print("    One-Click Installer", 'cyan', bold=True)
        self.color_print("=" * 60, 'cyan', bold=True)
        print()
    
    def print_step(self, step: int, total: int, message: str):
        """Print installation step."""
        self.color_print(f"[{step}/{total}] {message}", 'blue', bold=True)
    
    def print_success(self, message: str):
        """Print success message."""
        symbol = "[OK]" if self.system == 'windows' else "✓"
        self.color_print(f"{symbol} {message}", 'green', bold=True)
    
    def print_error(self, message: str):
        """Print error message."""
        symbol = "[ERROR]" if self.system == 'windows' else "✗"
        self.color_print(f"{symbol} {message}", 'red', bold=True)
    
    def print_warning(self, message: str):
        """Print warning message."""
        symbol = "[WARNING]" if self.system == 'windows' else "⚠"
        self.color_print(f"{symbol} {message}", 'yellow', bold=True)
    
    def print_info(self, message: str):
        """Print info message."""
        symbol = "[INFO]" if self.system == 'windows' else "ℹ"
        self.color_print(f"{symbol} {message}", 'cyan')
    
    def check_python_version(self) -> bool:
        """Check if Python version is compatible."""
        min_version = (3, 8)
        current_version = sys.version_info[:2]
        
        if current_version >= min_version:
            self.print_success(f"Python {sys.version.split()[0]} detected")
            return True
        else:
            self.print_error(f"Python {min_version[0]}.{min_version[1]}+ required, found {current_version[0]}.{current_version[1]}")
            return False
    
    def check_dependencies(self) -> Tuple[bool, list]:
        """Check if required dependencies are installed."""
        missing = []
        required_packages = ['pip', 'git']
        
        for package in required_packages:
            try:
                subprocess.run([package, '--version'], 
                             capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                missing.append(package)
        
        if not missing:
            self.print_success("All required dependencies found")
            return True, []
        else:
            self.print_warning(f"Missing dependencies: {', '.join(missing)}")
            return False, missing
    
    def install_rakan(self) -> bool:
        """Install RAKAN via pip."""
        try:
            self.print_info("Installing RAKAN via pip...")
            subprocess.run([sys.executable, "-m", "pip", "install", "rakan"], 
                         check=True, capture_output=True)
            self.print_success("RAKAN installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            self.print_error(f"Failed to install RAKAN: {e}")
            return False
    
    def create_directories(self) -> bool:
        """Create necessary directories."""
        try:
            for directory in [self.install_dir, self.config_dir, self.models_dir]:
                directory.mkdir(parents=True, exist_ok=True)
            self.print_success("Directory structure created")
            return True
        except Exception as e:
            self.print_error(f"Failed to create directories: {e}")
            return False
    
    def download_config_files(self) -> bool:
        """Download configuration files from GitHub or copy from local."""
        try:
            # First try to copy from local directory if we're running from source
            local_config_dir = Path(__file__).parent / "config"
            if local_config_dir.exists():
                config_files = ['default.yaml', 'models.yaml', 'permissions.yaml']
                for config_file in config_files:
                    src = local_config_dir / config_file
                    dest = self.config_dir / config_file
                    if src.exists():
                        shutil.copy2(src, dest)
                
                self.print_success("Configuration files copied from local source")
                return True
            
            # Otherwise download from GitHub
            base_url = "https://raw.githubusercontent.com/devfazla/rakan/main/config/"
            config_files = ['default.yaml', 'models.yaml', 'permissions.yaml']
            
            for config_file in config_files:
                url = base_url + config_file
                dest = self.config_dir / config_file
                urllib.request.urlretrieve(url, dest)
            
            self.print_success("Configuration files downloaded")
            return True
        except Exception as e:
            self.print_error(f"Failed to download config files: {e}")
            return False
    
    def setup_path(self) -> bool:
        """Add RAKAN to system PATH."""
        try:
            if self.system == 'windows':
                # Windows PATH setup
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                   r"Environment", 0, 
                                   winreg.KEY_ALL_ACCESS) as key:
                    path_value = winreg.QueryValueEx(key, "PATH")[0]
                    python_scripts = str(Path(sys.executable).parent)
                    if python_scripts not in path_value:
                        new_path = f"{path_value};{python_scripts}"
                        winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
                        self.print_success("Added to PATH (restart terminal required)")
            else:
                # Unix PATH setup (add to shell config)
                shell_config = Path.home() / ".bashrc"
                if not shell_config.exists():
                    shell_config = Path.home() / ".zshrc"
                
                if shell_config.exists():
                    with open(shell_config, 'a') as f:
                        f.write('\n# RAKAN installation\nexport PATH="$PATH:~/.local/bin"\n')
                    self.print_success("Added to PATH (restart terminal required)")
                else:
                    self.print_warning("Could not detect shell config file")
            
            return True
        except Exception as e:
            self.print_warning(f"PATH setup failed: {e}")
            self.print_info("You may need to add RAKAN to PATH manually")
            return False
    
    def install_model(self, model_name: str = "qwen2.5-coder-1.5b-instruct") -> bool:
        """Install a default model."""
        try:
            self.print_info(f"Installing model: {model_name}")
            # Use Python module instead of CLI command since PATH might not be updated yet
            subprocess.run([sys.executable, "-m", "cli.main", "model", "install", model_name], 
                         check=True, capture_output=True, cwd=Path(__file__).parent)
            self.print_success(f"Model {model_name} installed")
            return True
        except subprocess.CalledProcessError as e:
            self.print_warning(f"Model installation failed: {e}")
            self.print_info("You can install models later with: rakan model install <name>")
            return False
    
    def verify_installation(self) -> bool:
        """Verify that RAKAN is installed correctly."""
        try:
            result = subprocess.run([sys.executable, "-m", "cli.main", "--version"], 
                                  capture_output=True, text=True, check=True, cwd=Path(__file__).parent)
            self.print_success("Installation verified successfully")
            self.print_info(result.stdout.strip())
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.print_error("Installation verification failed")
            return False
    
    def run(self):
        """Run the complete installation process."""
        self.print_header()
        
        total_steps = 7
        current_step = 0
        
        # Step 1: Check Python version
        current_step += 1
        self.print_step(current_step, total_steps, "Checking Python version")
        if not self.check_python_version():
            self.print_error("Installation aborted: Incompatible Python version")
            return False
        
        # Step 2: Check dependencies
        current_step += 1
        self.print_step(current_step, total_steps, "Checking dependencies")
        deps_ok, missing = self.check_dependencies()
        if not deps_ok:
            self.print_error("Please install missing dependencies first")
            return False
        
        # Step 3: Install RAKAN
        current_step += 1
        self.print_step(current_step, total_steps, "Installing RAKAN")
        if not self.install_rakan():
            self.print_error("Failed to install RAKAN")
            return False
        
        # Step 4: Create directories
        current_step += 1
        self.print_step(current_step, total_steps, "Creating directory structure")
        if not self.create_directories():
            self.print_error("Failed to create directories")
            return False
        
        # Step 5: Download configuration
        current_step += 1
        self.print_step(current_step, total_steps, "Downloading configuration files")
        if not self.download_config_files():
            self.print_error("Failed to download configuration")
            return False
        
        # Step 6: Setup PATH
        current_step += 1
        self.print_step(current_step, total_steps, "Setting up system PATH")
        self.setup_path()
        
        # Step 7: Install default model
        current_step += 1
        self.print_step(current_step, total_steps, "Installing default model")
        self.print_info("Model installation skipped - you can install models later")
        self.print_info("Run: rakan model install <name> to install models")
        
        # Verification
        print()
        self.print_step(current_step + 1, total_steps, "Verifying installation")
        if self.verify_installation():
            print()
            self.color_print("=" * 60, 'green', bold=True)
            self.color_print("    RAKAN Installation Complete!", 'green', bold=True)
            self.color_print("=" * 60, 'green', bold=True)
            print()
            self.print_info("To get started, run:")
            self.color_print("    python -m cli.main doctor", 'cyan', bold=True)
            self.color_print("    python -m cli.main model list", 'cyan', bold=True)
            self.color_print("    python -m cli.main chat", 'cyan', bold=True)
            print()
            self.print_info("Or after restarting your terminal:")
            self.color_print("    rakan doctor", 'cyan', bold=True)
            self.color_print("    rakan model list", 'cyan', bold=True)
            self.color_print("    rakan chat", 'cyan', bold=True)
            print()
            self.print_info("For full documentation:")
            self.color_print("    https://github.com/devfazla/rakan", 'cyan', bold=True)
            self.color_print("    https://devfazla.com", 'cyan', bold=True)
            print()
            return True
        else:
            print()
            self.print_error("Installation verification failed")
            self.print_info("Please check the error messages above")
            return False


def main():
    """Main entry point for the installer."""
    installer = RakanInstaller()
    success = installer.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()