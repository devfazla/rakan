#!/usr/bin/env python3
"""
RAKAN Universal Installer
Single installer that handles everything: setup, dependencies, PATH, and configuration
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_header():
    print("=" * 60)
    print("RAKAN - Universal Installer")
    print("=" * 60)
    print()

def check_python():
    """Check Python installation."""
    print("Checking Python installation...")
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8 or higher required")
        print(f"Current version: {sys.version}")
        return False
    print(f"[OK] Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def install_dependencies():
    """Install required dependencies."""
    print("\nInstalling dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("[OK] Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to install dependencies: {e}")
        return False

def setup_rakan_command():
    """Setup RAKAN as a system command."""
    print("\nSetting up RAKAN command...")
    
    script_dir = Path(__file__).parent.resolve()
    system = platform.system()
    
    if system == "Windows":
        return setup_windows_command(script_dir)
    else:
        return setup_unix_command(script_dir)

def setup_windows_command(script_dir):
    """Setup RAKAN command on Windows."""
    try:
        user_profile = os.path.expanduser("~")
        wrapper_file = os.path.join(user_profile, "rakan.bat")
        
        # Create batch file
        with open(wrapper_file, 'w') as f:
            f.write('@echo off\n')
            f.write(f'python "{script_dir}\\cli\\main.py" %*\n')
        
        print(f"[OK] Created wrapper: {wrapper_file}")
        
        # Add to PATH
        try:
            subprocess.run(['setx', 'PATH', f'%PATH%;{user_profile}'], 
                         check=True, capture_output=True)
            print(f"[OK] Added to PATH: {user_profile}")
            print("  Close and reopen terminal to use 'rakan' command")
            return True
        except:
            print("[WARNING] Could not add to PATH automatically")
            print(f"  Manually add {user_profile} to your PATH")
            return True
    except Exception as e:
        print(f"[ERROR] Failed to setup command: {e}")
        return False

def setup_unix_command(script_dir):
    """Setup RAKAN command on Unix systems."""
    try:
        install_dir = os.path.expanduser("~/.local/bin")
        os.makedirs(install_dir, exist_ok=True)
        
        wrapper_file = os.path.join(install_dir, "rakan")
        
        # Create shell script
        with open(wrapper_file, 'w') as f:
            f.write('#!/bin/bash\n')
            f.write(f'python3 "{script_dir}/cli/main.py" "$@"\n')
        
        os.chmod(wrapper_file, 0o755)
        print(f"[OK] Created wrapper: {wrapper_file}")
        
        # Add to PATH if needed
        if install_dir not in os.environ.get('PATH', '').split(':'):
            shell_config = os.path.expanduser("~/.bashrc")
            if not os.path.exists(shell_config):
                shell_config = os.path.expanduser("~/.zshrc")
            if not os.path.exists(shell_config):
                shell_config = os.path.expanduser("~/.profile")
            
            with open(shell_config, 'a') as f:
                f.write('\n# RAKAN\n')
                f.write(f'export PATH="$HOME/.local/bin:$PATH"\n')
            
            print(f"[OK] Added to PATH in {shell_config}")
            print(f"  Run 'source {shell_config}' to apply changes")
        
        return True
    except Exception as e:
        print(f"[ERROR] Failed to setup command: {e}")
        return False

def create_directories():
    """Create necessary directories."""
    print("\nCreating directories...")
    
    dirs = [
        os.path.expanduser("~/.rakan"),
        os.path.expanduser("~/.rakan/models"),
        os.path.expanduser("~/.rakan/logs"),
        os.path.expanduser("~/.rakan/cache"),
        os.path.expanduser("~/.rakan/temp")
    ]
    
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"[OK] Created: {dir_path}")
    
    return True

def verify_installation():
    """Verify installation."""
    print("\nVerifying installation...")
    
    try:
        # Test if CLI can be imported
        sys.path.insert(0, str(Path(__file__).parent))
        from agent.core import get_config_manager
        config = get_config_manager()
        print("[OK] Configuration system working")
        
        # Test directories
        if os.path.exists(os.path.expanduser("~/.rakan")):
            print("[OK] Data directory created")
        
        return True
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        return False

def main():
    """Main installation function."""
    print_header()
    
    # Check Python
    if not check_python():
        return 1
    
    # Install dependencies
    if not install_dependencies():
        return 1
    
    # Create directories
    if not create_directories():
        return 1
    
    # Setup command
    if not setup_rakan_command():
        return 1
    
    # Verify
    if not verify_installation():
        return 1
    
    print("\n" + "=" * 60)
    print("Installation Complete!")
    print("=" * 60)
    print()
    print("RAKAN is now installed on your system.")
    print()
    print("To start using RAKAN:")
    print("  1. Close and reopen your terminal")
    print("  2. Run: rakan")
    print()
    print("Or directly use:")
    print(f"  python {Path(__file__).parent}/cli/main.py")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())