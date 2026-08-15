"""
Local AI Platform - Hardware Detector
Handles hardware detection and model recommendations.
"""

import sys
import os
import platform
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from agent.core import get_logger


class HardwareDetector:
    """Detects system hardware and provides model recommendations."""
    
    def __init__(self):
        """Initialize hardware detector."""
        self.logger = get_logger(__name__)
        self._cached_info = None
    
    def detect_hardware(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Detect system hardware information.
        
        Args:
            force_refresh: Force refresh of cached information
            
        Returns:
            Dictionary with hardware information
        """
        if self._cached_info and not force_refresh:
            return self._cached_info
        
        self.logger.info("Detecting system hardware...")
        
        hardware_info = {
            'os': self._detect_os(),
            'cpu_architecture': self._detect_cpu_architecture(),
            'cpu_cores': self._detect_cpu_cores(),
            'cpu_frequency': self._detect_cpu_frequency(),
            'total_memory_gb': self._detect_memory(),
            'available_memory_gb': self._detect_available_memory(),
            'disk_space_gb': self._detect_disk_space(),
            'gpu': self._detect_gpu()
        }
        
        self._cached_info = hardware_info
        self.logger.info(f"Hardware detection completed: {hardware_info}")
        
        return hardware_info
    
    def _detect_os(self) -> str:
        """Detect operating system."""
        return platform.system()
    
    def _detect_cpu_architecture(self) -> str:
        """Detect CPU architecture."""
        return platform.machine()
    
    def _detect_cpu_cores(self) -> int:
        """Detect CPU core count."""
        if PSUTIL_AVAILABLE:
            return psutil.cpu_count()
        return os.cpu_count() if hasattr(os, 'cpu_count') else 4
    
    def _detect_cpu_frequency(self) -> Optional[float]:
        """Detect CPU frequency in MHz."""
        if PSUTIL_AVAILABLE:
            freq = psutil.cpu_freq()
            return freq.current if freq else None
        return None
    
    def _detect_memory(self) -> float:
        """Detect total memory in GB."""
        if PSUTIL_AVAILABLE:
            return round(psutil.virtual_memory().total / (1024**3), 2)
        return 8.0  # Fallback estimate
    
    def _detect_available_memory(self) -> float:
        """Detect available memory in GB."""
        if PSUTIL_AVAILABLE:
            return round(psutil.virtual_memory().available / (1024**3), 2)
        return 4.0  # Fallback estimate
    
    def _detect_disk_space(self) -> float:
        """Detect available disk space in GB."""
        if PSUTIL_AVAILABLE:
            disk = psutil.disk_usage('/')
            return round(disk.free / (1024**3), 2)
        return 50.0  # Fallback estimate
    
    def _detect_gpu(self) -> Dict[str, Any]:
        """Detect GPU information."""
        # Basic GPU detection (can be extended with proper GPU libraries)
        gpu_info = {
            'available': False,
            'name': None,
            'memory_gb': 0
        }
        
        # Try to detect NVIDIA GPU
        try:
            import subprocess
            result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                gpu_info['available'] = True
                parts = result.stdout.strip().split(',')
                gpu_info['name'] = parts[0].strip()
                memory_str = parts[1].strip().replace('MiB', '').replace('GiB', '')
                gpu_info['memory_gb'] = round(float(memory_str) / 1024, 2) if 'MiB' in parts[1] else round(float(memory_str), 2)
        except (FileNotFoundError, subprocess.TimeoutExpired, ImportError):
            pass
        
        return gpu_info
    
    def get_hardware_profile(self, hardware_info: Optional[Dict[str, Any]] = None) -> str:
        """
        Determine hardware profile based on detected information.
        
        Args:
            hardware_info: Optional hardware information (will detect if not provided)
            
        Returns:
            Hardware profile name (low_end, mid_range, high_end)
        """
        if hardware_info is None:
            hardware_info = self.detect_hardware()
        
        total_ram = hardware_info.get('total_memory_gb', 0)
        cpu_cores = hardware_info.get('cpu_cores', 0)
        
        # Determine profile based on RAM and CPU
        if total_ram >= 16 and cpu_cores >= 8:
            return 'high_end'
        elif total_ram >= 8 and cpu_cores >= 4:
            return 'mid_range'
        else:
            return 'low_end'
    
    def get_model_recommendations(self, hardware_info: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Get model recommendations based on hardware.
        
        Args:
            hardware_info: Optional hardware information (will detect if not provided)
            
        Returns:
            List of recommended model names
        """
        from models.registry import get_model_registry
        
        if hardware_info is None:
            hardware_info = self.detect_hardware()
        
        registry = get_model_registry()
        return registry.get_recommended_models(hardware_info)
    
    def can_run_model(self, model_name: str, hardware_info: Optional[Dict[str, Any]] = None) -> bool:
        """
        Check if a model can run on the detected hardware.
        
        Args:
            model_name: Name of the model to check
            hardware_info: Optional hardware information (will detect if not provided)
            
        Returns:
            True if model can run, False otherwise
        """
        from models.registry import get_model_registry
        
        if hardware_info is None:
            hardware_info = self.detect_hardware()
        
        registry = get_model_registry()
        model_info = registry.get_model(model_name)
        
        if not model_info:
            return False
        
        # Check RAM requirements
        available_ram = hardware_info.get('available_memory_gb', 0)
        required_ram = model_info.ram_required_gb
        
        # Reserve 2GB for system and other applications
        if available_ram - 2 < required_ram:
            return False
        
        return True
    
    def get_performance_estimates(self, model_name: str, hardware_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get performance estimates for a model on the detected hardware.
        
        Args:
            model_name: Name of the model
            hardware_info: Optional hardware information (will detect if not provided)
            
        Returns:
            Dictionary with performance estimates
        """
        from models.registry import get_model_registry
        
        if hardware_info is None:
            hardware_info = self.detect_hardware()
        
        registry = get_model_registry()
        model_info = registry.get_model(model_name)
        
        if not model_info:
            return {'error': 'Model not found'}
        
        # Calculate performance estimates based on hardware
        total_ram = hardware_info.get('total_memory_gb', 0)
        cpu_cores = hardware_info.get('cpu_cores', 0)
        model_size_gb = model_info.file_size_gb
        model_params = model_info.parameters
        
        # RAM utilization
        ram_utilization = (model_info.ram_required_gb / total_ram) * 100
        
        # Performance category
        if ram_utilization < 50:
            performance = 'excellent'
        elif ram_utilization < 70:
            performance = 'good'
        elif ram_utilization < 90:
            performance = 'acceptable'
        else:
            performance = 'poor'
        
        # Estimated tokens per second (very rough estimate)
        # This is a simplified estimate - actual performance depends on many factors
        base_tps = 10  # Base tokens per second for 1.5B model on 4 cores
        params_multiplier = 1.5 if model_params == '1.5B' else (1.0 if model_params == '3B' else 0.5)
        cpu_multiplier = cpu_cores / 4  # Normalize to 4 cores
        estimated_tps = base_tps * params_multiplier * cpu_multiplier
        
        return {
            'model_name': model_name,
            'ram_utilization_percent': round(ram_utilization, 1),
            'performance_category': performance,
            'estimated_tokens_per_second': round(estimated_tps, 1),
            'recommended': ram_utilization < 70,
            'warnings': self._get_performance_warnings(ram_utilization, total_ram, model_info)
        }
    
    def _get_performance_warnings(self, ram_utilization: float, total_ram: float, model_info) -> List[str]:
        """Get performance warnings for a model."""
        warnings = []
        
        if ram_utilization > 90:
            warnings.append(f"Model requires {model_info.ram_required_gb}GB RAM, only {total_ram}GB available")
        
        if total_ram < 8:
            warnings.append("Limited RAM may affect system performance")
        
        if model_info.parameters in ['7B', '13B'] and total_ram < 16:
            warnings.append(f"{model_info.parameters} model requires 16GB+ RAM for good performance")
        
        return warnings
    
    def print_hardware_report(self, hardware_info: Optional[Dict[str, Any]] = None):
        """
        Print a formatted hardware report.
        
        Args:
            hardware_info: Optional hardware information (will detect if not provided)
        """
        if hardware_info is None:
            hardware_info = self.detect_hardware()
        
        print("\n" + "="*60)
        print("HARDWARE REPORT")
        print("="*60 + "\n")
        
        print("System Information:")
        print(f"  OS:              {hardware_info['os']}")
        print(f"  Architecture:    {hardware_info['cpu_architecture']}")
        print(f"  CPU Cores:       {hardware_info['cpu_cores']}")
        if hardware_info['cpu_frequency']:
            print(f"  CPU Frequency:   {hardware_info['cpu_frequency']:.0f} MHz")
        print(f"  Total Memory:    {hardware_info['total_memory_gb']} GB")
        print(f"  Available Memory: {hardware_info['available_memory_gb']} GB")
        print(f"  Available Disk:  {hardware_info['disk_space_gb']} GB")
        
        if hardware_info['gpu']['available']:
            print(f"  GPU:             {hardware_info['gpu']['name']}")
            print(f"  GPU Memory:      {hardware_info['gpu']['memory_gb']} GB")
        else:
            print(f"  GPU:             Not available/detected")
        
        print(f"\nHardware Profile: {self.get_hardware_profile(hardware_info)}")
        
        recommendations = self.get_model_recommendations(hardware_info)
        print(f"Recommended Models: {', '.join(recommendations) if recommendations else 'None'}")
        
        print("\n" + "="*60 + "\n")


# Global hardware detector instance
_hardware_detector = None


def get_hardware_detector() -> HardwareDetector:
    """
    Get global hardware detector instance.
    
    Returns:
        HardwareDetector instance
    """
    global _hardware_detector
    if _hardware_detector is None:
        _hardware_detector = HardwareDetector()
    return _hardware_detector


# Example usage and testing
if __name__ == "__main__":
    # Test hardware detector
    print("Testing Hardware Detector...")
    
    detector = HardwareDetector()
    
    # Detect hardware
    hardware_info = detector.detect_hardware()
    print("\nDetected Hardware:")
    for key, value in hardware_info.items():
        print(f"  {key}: {value}")
    
    # Get hardware profile
    profile = detector.get_hardware_profile()
    print(f"\nHardware Profile: {profile}")
    
    # Get model recommendations
    recommendations = detector.get_model_recommendations()
    print(f"\nRecommended Models: {recommendations}")
    
    # Check if specific model can run
    can_run = detector.can_run_model('qwen2.5-coder-1.5b-instruct')
    print(f"\nCan run qwen2.5-coder-1.5b-instruct: {can_run}")
    
    # Get performance estimates
    performance = detector.get_performance_estimates('qwen2.5-coder-1.5b-instruct')
    print(f"\nPerformance Estimates:")
    for key, value in performance.items():
        print(f"  {key}: {value}")
    
    # Print formatted report
    detector.print_hardware_report()
    
    print("\nHardware detector test completed!")
