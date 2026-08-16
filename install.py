#!/usr/bin/env python3
"""
RAKAN Installation Script
Cross-platform installation script that adds RAKAN to system PATH
"""

import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path


def main():
    """Main installation function."""
    print("=" * 50)
    print("RAKAN Installation Script")
    print("=" * 50)
    print()
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.resolve()
    rakan_dir = script_dir
    
    print(f"RAKAN Directory: {rakan_dir}")
    print()
    
    # Check if Python is installed
    try:
        import python_version
        print(f"Python found: {python_version}")
    except:
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        print(f"Python found: {python_version}")
    print()
    
    # Detect platform
    system = platform.system()
    print(f"Detected platform: {system}")
    print()
    
    # Check if rakan is already in PATH
    if shutil.which("rakan"):
        print("RAKAN is already in PATH")
        print(f"Location: {shutil.which('rakan')}")
        print()
        
        choice = input("Do you want to reinstall RAKAN? (y/n): ").strip().lower()
        if choice != 'y':
            print("Installation cancelled")
            return 0
    
    # Platform-specific installation
    if system == "Windows":
        success = install_windows(rakan_dir)
    elif system in ["Linux", "Darwin"]:
        success = install_unix(rakan_dir)
    else:
        print(f"ERROR: Unsupported platform: {system}")
        return 1
    
    if success:
        print()
        print("=" * 50)
        print("Installation Complete!")
        print("=" * 50)
        print()
        print("To use RAKAN:")
        print("1. Close and reopen your terminal")
        print("2. Run: rakan --help")
        print()
        return 0
    else:
        print()
        print("Installation failed. Please try manual installation.")
        return 1


def install_windows(rakan_dir):
    """Install RAKAN on Windows."""
    try:
        user_profile = os.path.expanduser("~")
        wrapper_file = os.path.join(user_profile, "rakan.bat")
        
        print(f"Creating RAKAN wrapper at: {wrapper_file}")
        
        # Create batch file wrapper
        with open(wrapper_file, 'w') as f:
            f.write(f'@echo off\n')
            f.write(f'python "{rakan_dir}\\cli\\main.py" %*\n')
        
        print("Wrapper file created successfully")
        print()
        
        # Add to PATH
        print("Adding RAKAN to user PATH...")
        
        try:
            # Use setx to add to user PATH
            subprocess.run(['setx', 'PATH', f'%PATH%;{user_profile}'], 
                         check=True, capture_output=True)
            print("PATH updated successfully")
            print()
            print("IMPORTANT: Close and reopen your terminal for changes to take effect")
            return True
        except subprocess.CalledProcessError:
            print("WARNING: Failed to update PATH automatically")
            print("Please add the following to your PATH manually:")
            print(f"  {user_profile}")
            print()
            print("Manual steps:")
            print("1. Press Win+R, type 'sysdm.cpl' and press Enter")
            print("2. Go to Advanced tab, click Environment Variables")
            print("3. Under User variables, find PATH and click Edit")
            print(f"4. Add {user_profile} to the list")
            print("5. Close and reopen your terminal")
            return True  # Still consider success, wrapper was created
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def install_unix(rakan_dir):
    """Install RAKAN on Linux/macOS."""
    try:
        install_dir = os.path.expanduser("~/.local/bin")
        os.makedirs(install_dir, exist_ok=True)
        
        wrapper_file = os.path.join(install_dir, "rakan")
        
        print(f"Creating RAKAN wrapper at: {wrapper_file}")
        
        # Create shell script wrapper
        with open(wrapper_file, 'w') as f:
            f.write('#!/bin/bash\n')
            f.write(f'python3 "{rakan_dir}/cli/main.py" "$@"\n')
        
        # Make executable
        os.chmod(wrapper_file, 0o755)
        
        print("Wrapper file created successfully")
        print()
        
        # Check if ~/.local/bin is in PATH
        if install_dir not in os.environ.get('PATH', '').split(':'):
            print("Adding ~/.local/bin to PATH...")
            
            # Detect shell configuration file
            shell_config = None
            if 'zsh' in os.environ.get('SHELL', ''):
                shell_config = os.path.expanduser("~/.zshrc")
            elif 'bash' in os.environ.get('SHELL', ''):
                shell_config = os.path.expanduser("~/.bashrc")
            
            if not shell_config:
                shell_config = os.path.expanduser("~/.profile")
            
            # Add to shell config
            with open(shell_config, 'a') as f:
                f.write(f'\n# RAKAN\n')
                f.write(f'export PATH="$HOME/.local/bin:$PATH"\n')
            
            print(f"PATH added to {shell_config}")
            print()
            print(f"IMPORTANT: Run 'source {shell_config}' or restart your terminal")
        else:
            print("~/.local/bin is already in PATH")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False


if __name__ == "__main__":
    sys.exit(main())