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


def check_existing_installation():
    """Check if RAKAN is already installed and return installation path."""
    import os
    import platform
    
    # Check for installation marker first
    data_dir = os.path.expanduser("~/.rakan")
    marker_file = os.path.join(data_dir, ".installation_info")
    if os.path.exists(marker_file):
        try:
            with open(marker_file, 'r') as f:
                install_path = f.read().strip()
                # Check if this is a valid directory
                if os.path.exists(install_path):
                    return install_path
                else:
                    # Marker exists but directory doesn't - corrupted installation
                    return f"Corrupted installation marker: {install_path}"
        except:
            pass
    
    # Check for wrapper file as fallback
    user_profile = os.path.expanduser("~")
    if platform.system() == "Windows":
        wrapper_file = os.path.join(user_profile, "rakan.bat")
    else:
        wrapper_file = os.path.join(os.path.expanduser("~/.local/bin"), "rakan")
    
    if os.path.exists(wrapper_file):
        return f"Wrapper file exists at: {wrapper_file}"
    
    # Only check for data directory if it contains actual RAKAN data
    if os.path.exists(data_dir):
        # Check if it looks like a RAKAN data directory
        has_rakan_data = (
            os.path.exists(os.path.join(data_dir, "models")) or
            os.path.exists(os.path.join(data_dir, "logs")) or
            os.path.exists(os.path.join(data_dir, "config"))
        )
        if has_rakan_data:
            return f"RAKAN data directory exists: {data_dir}"
    
    return None


def main():
    """Main installation function."""
    # Check for --force flag
    force_mode = '--force' in sys.argv or '-f' in sys.argv
    
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
    
    # Check for existing installation
    existing_installation = check_existing_installation()
    
    if existing_installation and not force_mode:
        print("=" * 50)
        print("Existing Installation Detected")
        print("=" * 50)
        print()
        print("RAKAN appears to be already installed:")
        print(f"  Current RAKAN directory: {rakan_dir}")
        print(f"  Previous installation: {existing_installation}")
        print()
        
        # Handle different types of existing installation info
        if "Corrupted installation marker:" in existing_installation:
            print("Found corrupted installation marker.")
            print("The previous installation directory no longer exists.")
            print()
            print("Options:")
            print("  1. Clean up and reinstall this location")
            print("  2. Cancel and investigate manually")
            print()
            
            try:
                choice = input("Your choice (1/2): ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nInstallation cancelled.")
                return 0
            
            if choice == '1':
                print("Cleaning up corrupted installation marker...")
                try:
                    os.remove(marker_file)
                    print("[OK] Removed corrupted marker")
                except:
                    print("[WARNING] Could not remove marker")
                print("Proceeding with installation...")
            elif choice == '2':
                print("Installation cancelled.")
                print(f"Please check: {existing_installation}")
                return 0
            else:
                print("Invalid choice. Installation cancelled.")
                return 0
        elif "Wrapper file exists at:" in existing_installation:
            print("Found existing wrapper file.")
            print("This may indicate a previous installation.")
            print()
            print("Options:")
            print("  1. Cancel and investigate existing installation")
            print("  2. Reinstall this location (overwrites existing)")
            print("  3. Uninstall existing and install new")
            print()
            
            try:
                choice = input("Your choice (1/2/3): ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nInstallation cancelled.")
                return 0
            
            if choice == '1':
                print("Installation cancelled.")
                print(f"Please check: {existing_installation}")
                return 0
            elif choice == '2':
                print("Proceeding with reinstallation...")
                print("This will overwrite the existing installation.")
            elif choice == '3':
                print("Please uninstall existing installation first:")
                print("  rakan uninstall")
                print("Then run this installation again.")
                return 0
            else:
                print("Invalid choice. Installation cancelled.")
                return 0
        elif "RAKAN data directory exists:" in existing_installation:
            print("Found existing RAKAN data directory.")
            print("This contains your models, logs, and configuration.")
            print()
            print("This is not a duplicate installation - the data directory")
            print("is shared across installations. This is safe to continue.")
            print()
            print("Proceeding with installation...")
            print("Your existing data will be preserved.")
        elif existing_installation == str(rakan_dir):
            print("This is the same installation directory.")
            print("No installation needed.")
            print()
            print("To reinstall, first uninstall with:")
            print("  rakan uninstall")
            print("Or use --force flag to reinstall:")
            print("  python install.py --force")
            return 0
        else:
            print("Different installation directory detected.")
            print()
            print("Options:")
            print("  1. Cancel and use existing installation")
            print("  2. Reinstall this location (overwrites existing)")
            print("  3. Uninstall existing and install new")
            print()
            
            try:
                choice = input("Your choice (1/2/3): ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nInstallation cancelled.")
                return 0
            
            if choice == '1':
                print("Installation cancelled.")
                print(f"Using existing installation at: {existing_installation}")
                return 0
            elif choice == '2':
                print("Proceeding with reinstallation...")
                print("This will overwrite the existing installation.")
            elif choice == '3':
                print("Please uninstall existing installation first:")
                print("  rakan uninstall")
                print("Then run this installation again.")
                return 0
            else:
                print("Invalid choice. Installation cancelled.")
                return 0
    elif existing_installation and force_mode:
        print("Force mode enabled - proceeding with reinstallation")
        print(f"Previous installation: {existing_installation}")
        print()
    
    # Check if rakan is already in PATH
    if shutil.which("rakan"):
        rakan_path = shutil.which('rakan')
        print("RAKAN command is already in PATH")
        print(f"Location: {rakan_path}")
        print()
        
        if not force_mode:
            choice = input("Do you want to reinstall RAKAN? (y/n): ").strip().lower()
            if choice != 'y':
                print("Installation cancelled.")
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
        
        # Create installation marker
        data_dir = os.path.expanduser("~/.rakan")
        os.makedirs(data_dir, exist_ok=True)
        marker_file = os.path.join(data_dir, ".installation_info")
        with open(marker_file, 'w') as f:
            f.write(str(rakan_dir))
        print(f"Installation marker created: {marker_file}")
        print(f"Installation path: {rakan_dir}")
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
        
        # Create installation marker
        data_dir = os.path.expanduser("~/.rakan")
        os.makedirs(data_dir, exist_ok=True)
        marker_file = os.path.join(data_dir, ".installation_info")
        with open(marker_file, 'w') as f:
            f.write(str(rakan_dir))
        print(f"Installation marker created: {marker_file}")
        print(f"Installation path: {rakan_dir}")
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