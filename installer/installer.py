"""
Local AI Platform - Installer
Comprehensive installation and setup system.
"""

import sys
import os
from pathlib import Path
import platform
import subprocess
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class HardwareInfo:
    """Hardware information."""
    os_name: str
    os_version: str
    architecture: str
    cpu_cores: int
    cpu_frequency: float
    total_memory_gb: float
    available_memory_gb: float
    disk_space_gb: float
    has_gpu: bool
    gpu_info: Optional[str] = None


@dataclass
class DependencyInfo:
    """Dependency information."""
    name: str
    version: Optional[str]
    installed: bool
    required: bool
    install_command: str


class HardwareDetector:
    """Detect system hardware and capabilities."""
    
    @staticmethod
    def detect() -> HardwareInfo:
        """
        Detect system hardware.
        
        Returns:
            HardwareInfo object
        """
        import psutil
        
        os_name = platform.system()
        os_version = platform.version()
        architecture = platform.machine()
        cpu_cores = psutil.cpu_count(logical=True)
        cpu_frequency = psutil.cpu_freq().current if psutil.cpu_freq() else 0
        total_memory = psutil.virtual_memory().total / (1024**3)
        available_memory = psutil.virtual_memory().available / (1024**3)
        disk_space = psutil.disk_usage('/').total / (1024**3) if os_name == 'Linux' else psutil.disk_usage('C:').total / (1024**3)
        
        # GPU detection
        has_gpu = False
        gpu_info = None
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                has_gpu = True
                gpu_info = f"{gpus[0].name} ({gpus[0].memoryTotal}MB)"
        except ImportError:
            pass
        
        return HardwareInfo(
            os_name=os_name,
            os_version=os_version,
            architecture=architecture,
            cpu_cores=cpu_cores,
            cpu_frequency=cpu_frequency,
            total_memory_gb=total_memory,
            available_memory_gb=available_memory,
            disk_space_gb=disk_space,
            has_gpu=has_gpu,
            gpu_info=gpu_info
        )


class DependencyChecker:
    """Check and install dependencies."""
    
    @staticmethod
    def check_python_version() -> tuple[bool, str]:
        """
        Check Python version.
        
        Returns:
            Tuple of (is_compatible, version_string)
        """
        version = sys.version_info
        is_compatible = version >= (3, 8)
        version_string = f"{version.major}.{version.minor}.{version.micro}"
        return is_compatible, version_string
    
    @staticmethod
    def check_dependencies() -> List[DependencyInfo]:
        """
        Check all dependencies.
        
        Returns:
            List of DependencyInfo objects
        """
        dependencies = [
            DependencyInfo("PyYAML", None, False, True, "pip install PyYAML"),
            DependencyInfo("colorlog", None, False, True, "pip install colorlog"),
            DependencyInfo("psutil", None, False, True, "pip install psutil"),
            DependencyInfo("aiofiles", None, False, True, "pip install aiofiles"),
            DependencyInfo("aiohttp", None, False, True, "pip install aiohttp"),
            DependencyInfo("tqdm", None, False, True, "pip install tqdm"),
            DependencyInfo("fastapi", None, False, False, "pip install fastapi uvicorn websockets"),
            DependencyInfo("pytest", None, False, False, "pip install pytest pytest-asyncio pytest-cov"),
        ]
        
        for dep in dependencies:
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "show", dep.name],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    dep.installed = True
                    # Extract version
                    for line in result.stdout.split('\n'):
                        if line.startswith('Version:'):
                            dep.version = line.split(':')[1].strip()
                            break
            except Exception as e:
                logger.warning(f"Failed to check {dep.name}: {e}")
        
        return dependencies
    
    @staticmethod
    def install_dependency(dep: DependencyInfo) -> bool:
        """
        Install a dependency.
        
        Args:
            dep: Dependency to install
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Installing {dep.name}...")
            result = subprocess.run(
                dep.install_command.split(),
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully installed {dep.name}")
                return True
            else:
                logger.error(f"Failed to install {dep.name}: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error installing {dep.name}: {e}")
            return False


class ConfigurationWizard:
    """Interactive configuration wizard."""
    
    def __init__(self):
        """Initialize configuration wizard."""
        self.config: Dict[str, Any] = {}
    
    def run(self) -> Dict[str, Any]:
        """
        Run configuration wizard.
        
        Returns:
            Configuration dictionary
        """
        print("\n" + "="*70)
        print("LOCAL AI PLATFORM - CONFIGURATION WIZARD")
        print("="*70 + "\n")
        
        # Hardware check
        hardware = HardwareDetector.detect()
        print(f"Detected Hardware:")
        print(f"  OS: {hardware.os_name} {hardware.os_version}")
        print(f"  CPU: {hardware.cpu_cores} cores @ {hardware.cpu_frequency:.0f} MHz")
        print(f"  RAM: {hardware.total_memory_gb:.1f} GB total, {hardware.available_memory_gb:.1f} GB available")
        print(f"  Disk: {hardware.disk_space_gb:.1f} GB total")
        print(f"  GPU: {hardware.gpu_info if hardware.has_gpu else 'None'}")
        print()
        
        # Model selection
        print("Model Selection:")
        print("  1. Qwen2.5-Coder 1.5B (Q4_K_M, ~1.2 GB, 4 GB RAM)")
        print("  2. Qwen2.5-Coder 3B (Q4_K_M, ~2.1 GB, 6 GB RAM)")
        print("  3. Skip model download (install manually later)")
        
        model_choice = input("\nSelect model [1-3]: ").strip()
        
        if model_choice == "1":
            self.config['model'] = "qwen2.5-coder-1.5b-instruct"
            self.config['download_model'] = True
        elif model_choice == "2":
            self.config['model'] = "qwen2.5-coder-3b-instruct"
            self.config['download_model'] = True
        else:
            self.config['model'] = None
            self.config['download_model'] = False
        
        # Installation directory
        default_dir = str(Path.home() / "local-ai")
        install_dir = input(f"\nInstallation directory [{default_dir}]: ").strip()
        self.config['install_dir'] = install_dir if install_dir else default_dir
        
        # API server configuration
        start_server = input("\nStart API server on startup? [y/N]: ").strip().lower()
        self.config['start_server'] = start_server == 'y'
        
        if self.config['start_server']:
            host = input("API server host [127.0.0.1]: ").strip()
            port = input("API server port [8000]: ").strip()
            self.config['server_host'] = host if host else "127.0.0.1"
            self.config['server_port'] = int(port) if port else 8000
        
        # Desktop shortcut
        create_shortcut = input("\nCreate desktop shortcut? [y/N]: ").strip().lower()
        self.config['create_shortcut'] = create_shortcut == 'y'
        
        return self.config


class ModelDownloader:
    """Download and install models."""
    
    def __init__(self, install_dir: str):
        """
        Initialize model downloader.
        
        Args:
            install_dir: Installation directory
        """
        self.install_dir = Path(install_dir)
        self.models_dir = self.install_dir / "models"
    
    def download_model(self, model_name: str) -> bool:
        """
        Download a model.
        
        Args:
            model_name: Name of model to download
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from models.manager import get_model_manager
            from models.registry import get_model_registry
            
            # Create models directory
            self.models_dir.mkdir(parents=True, exist_ok=True)
            
            # Get model registry
            registry = get_model_registry()
            model = registry.get_model(model_name)
            
            if not model:
                logger.error(f"Model not found: {model_name}")
                return False
            
            # Download model
            logger.info(f"Downloading {model_name}...")
            manager = get_model_manager()
            success = manager.install_model(model_name)
            
            if success:
                logger.info(f"Successfully downloaded {model_name}")
                return True
            else:
                logger.error(f"Failed to download {model_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error downloading model: {e}")
            return False


class SystemIntegrator:
    """Integrate with system (shortcuts, PATH, etc.)."""
    
    @staticmethod
    def create_shortcut(install_dir: str) -> bool:
        """
        Create desktop shortcut.
        
        Args:
            install_dir: Installation directory
            
        Returns:
            True if successful, False otherwise
        """
        try:
            os_name = platform.system()
            
            if os_name == "Windows":
                import winshell
                from win32com.client import Dispatch
                
                desktop = winshell.desktop()
                path = os.path.join(desktop, "Local AI.lnk")
                target = os.path.join(install_dir, "cli", "main.py")
                wDir = os.path.dirname(target)
                icon = os.path.join(install_dir, "icon.ico") if os.path.exists(os.path.join(install_dir, "icon.ico")) else None
                
                shell = Dispatch('WScript.Shell')
                shortcut = shell.CreateShortCut(path)
                shortcut.Targetpath = f'"{sys.executable}"'
                shortcut.Arguments = f'"{target}"'
                shortcut.WorkingDirectory = wDir
                if icon:
                    shortcut.IconLocation = icon
                shortcut.save()
                
                logger.info(f"Created desktop shortcut: {path}")
                return True
                
            elif os_name == "Linux":
                desktop = Path.home() / "Desktop"
                shortcut_path = desktop / "local-ai.desktop"
                
                desktop_entry = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Local AI
Comment=Local AI Development Platform
Exec={sys.executable} {install_dir}/cli/main.py
Icon={install_dir}/icon.png
Terminal=true
Categories=Development;
"""
                
                shortcut_path.write_text(desktop_entry)
                shortcut_path.chmod(0o755)
                
                logger.info(f"Created desktop shortcut: {shortcut_path}")
                return True
                
            elif os_name == "Darwin":  # macOS
                # macOS doesn't use desktop shortcuts the same way
                logger.info("Desktop shortcuts not supported on macOS")
                return False
                
        except Exception as e:
            logger.error(f"Failed to create shortcut: {e}")
            return False
    
    @staticmethod
    def add_to_path(install_dir: str) -> bool:
        """
        Add installation directory to PATH.
        
        Args:
            install_dir: Installation directory
            
        Returns:
            True if successful, False otherwise
        """
        try:
            os_name = platform.system()
            
            if os_name == "Windows":
                # Add to user PATH via registry
                import winreg
                
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Environment",
                    0,
                    winreg.KEY_READ
                )
                
                current_path, _ = winreg.QueryValueEx(key, "Path")
                winreg.CloseKey(key)
                
                if install_dir not in current_path:
                    key = winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER,
                        r"Environment",
                        0,
                        winreg.KEY_SET_VALUE
                    )
                    
                    new_path = f"{current_path};{install_dir}"
                    winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
                    winreg.CloseKey(key)
                    
                    # Notify system of environment change
                    import ctypes
                    ctypes.windll.user32.SendMessageTimeoutW(
                        0xFFFF, 0x1A, 0, "Environment", 0, 5000
                    )
                    
                    logger.info(f"Added {install_dir} to PATH")
                    return True
                    
            elif os_name == "Linux":
                # Add to .bashrc or .zshrc
                shell_rc = Path.home() / ".bashrc"
                if not shell_rc.exists():
                    shell_rc = Path.home() / ".zshrc"
                
                if shell_rc.exists():
                    with open(shell_rc, 'a') as f:
                        f.write(f'\nexport PATH="$PATH:{install_dir}"\n')
                    logger.info(f"Added {install_dir} to PATH in {shell_rc}")
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to add to PATH: {e}")
            return False


class Installer:
    """Main installer class."""
    
    def __init__(self):
        """Initialize installer."""
        self.hardware: Optional[HardwareInfo] = None
        self.dependencies: List[DependencyInfo] = []
        self.config: Dict[str, Any] = {}
    
    def pre_install_check(self, interactive: bool = True) -> bool:
        """
        Run pre-installation checks.
        
        Args:
            interactive: Whether to ask for user input
            
        Returns:
            True if checks pass, False otherwise
        """
        print("\n" + "="*70)
        print("PRE-INSTALLATION CHECKS")
        print("="*70 + "\n")
        
        # Check Python version
        is_compatible, version = DependencyChecker.check_python_version()
        print(f"Python version: {version}")
        
        if not is_compatible:
            print("ERROR: Python 3.8 or higher required")
            return False
        
        print("[OK] Python version compatible")
        
        # Check hardware
        self.hardware = HardwareDetector.detect()
        print(f"[OK] Hardware detected: {self.hardware.cpu_cores} cores, {self.hardware.total_memory_gb:.1f} GB RAM")
        
        # Check disk space
        if self.hardware.disk_space_gb < 5:
            print("ERROR: At least 5 GB disk space required")
            return False
        
        print("[OK] Sufficient disk space")
        
        # Check dependencies
        self.dependencies = DependencyChecker.check_dependencies()
        missing_required = [d for d in self.dependencies if d.required and not d.installed]
        
        if missing_required:
            print(f"\nMissing required dependencies: {len(missing_required)}")
            for dep in missing_required:
                print(f"  - {dep.name}")
            
            if interactive:
                install_now = input("\nInstall missing dependencies now? [y/N]: ").strip().lower()
                if install_now == 'y':
                    for dep in missing_required:
                        if not DependencyChecker.install_dependency(dep):
                            print(f"Failed to install {dep.name}")
                            return False
                else:
                    print("Installation cancelled")
                    return False
            else:
                print("Run with 'install' command to install dependencies")
                return False
        
        print("[OK] All dependencies installed")
        
        return True
    
    def install(self) -> bool:
        """
        Run installation process.
        
        Returns:
            True if successful, False otherwise
        """
        print("\n" + "="*70)
        print("LOCAL AI PLATFORM - INSTALLATION")
        print("="*70 + "\n")
        
        # Pre-installation checks
        if not self.pre_install_check():
            return False
        
        # Configuration wizard
        wizard = ConfigurationWizard()
        self.config = wizard.run()
        
        # Create installation directory
        install_dir = Path(self.config['install_dir'])
        install_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\nInstalling to: {install_dir}")
        
        # Copy files (in real implementation, this would copy from source)
        print("Copying files...")
        # For now, we assume files are already in place
        
        # Download model if requested
        if self.config.get('download_model') and self.config.get('model'):
            downloader = ModelDownloader(str(install_dir))
            if not downloader.download_model(self.config['model']):
                print("Warning: Model download failed, but installation will continue")
        
        # Create shortcut if requested
        if self.config.get('create_shortcut'):
            SystemIntegrator.create_shortcut(str(install_dir))
        
        # Add to PATH
        SystemIntegrator.add_to_path(str(install_dir))
        
        # Save configuration
        config_file = install_dir / "config" / "user_config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
        
        print(f"\n[OK] Installation completed successfully!")
        print(f"[OK] Configuration saved to: {config_file}")
        
        return True


class Uninstaller:
    """Uninstaller class."""
    
    @staticmethod
    def uninstall(install_dir: str) -> bool:
        """
        Uninstall Local AI Platform.
        
        Args:
            install_dir: Installation directory
            
        Returns:
            True if successful, False otherwise
        """
        print("\n" + "="*70)
        print("LOCAL AI PLATFORM - UNINSTALLATION")
        print("="*70 + "\n")
        
        install_path = Path(install_dir)
        
        if not install_path.exists():
            print(f"Installation directory not found: {install_dir}")
            return False
        
        confirm = input(f"Remove {install_dir} and all its contents? [y/N]: ").strip().lower()
        
        if confirm != 'y':
            print("Uninstallation cancelled")
            return False
        
        try:
            # Remove shortcut
            os_name = platform.system()
            if os_name == "Windows":
                import winshell
                desktop = winshell.desktop()
                shortcut = os.path.join(desktop, "Local AI.lnk")
                if os.path.exists(shortcut):
                    os.remove(shortcut)
                    print("[OK] Removed desktop shortcut")
            elif os_name == "Linux":
                desktop = Path.home() / "Desktop"
                shortcut = desktop / "local-ai.desktop"
                if shortcut.exists():
                    shortcut.unlink()
                    print("[OK] Removed desktop shortcut")
            
            # Remove directory
            import shutil
            shutil.rmtree(install_path)
            print(f"[OK] Removed installation directory: {install_path}")
            
            print("\n[OK] Uninstallation completed successfully!")
            return True
            
        except Exception as e:
            print(f"Error during uninstallation: {e}")
            return False


# Main entry point
def main():
    """Main installer entry point."""
    print("Local AI Platform Installer")
    print("="*70)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "install":
            installer = Installer()
            success = installer.install()
            sys.exit(0 if success else 1)
            
        elif command == "uninstall":
            install_dir = sys.argv[2] if len(sys.argv) > 2 else str(Path.home() / "local-ai")
            uninstaller = Uninstaller()
            success = uninstaller.uninstall(install_dir)
            sys.exit(0 if success else 1)
            
        elif command == "check":
            # Just run checks
            if Installer().pre_install_check(interactive=False):
                print("\n[OK] All checks passed")
                sys.exit(0)
            else:
                print("\n[ERROR] Some checks failed")
                sys.exit(1)
    else:
        print("Usage:")
        print("  python installer.py install")
        print("  python installer.py uninstall [directory]")
        print("  python installer.py check")
        sys.exit(1)


if __name__ == "__main__":
    main()