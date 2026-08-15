"""
Local AI Platform - Models Module
Model registry and management functionality.
"""

from .registry import ModelRegistry, ModelInfo, get_model_registry
from .manager import ModelManager, InstalledModel, get_model_manager
from .gguf_validator import GGUFValidator, GGUFHeader, get_gguf_validator
from .hardware_detector import HardwareDetector, get_hardware_detector
from .downloader import ModelDownloader, DownloadProgress, get_model_downloader

__all__ = [
    'ModelRegistry',
    'ModelInfo', 
    'get_model_registry',
    'ModelManager',
    'InstalledModel',
    'get_model_manager',
    'GGUFValidator',
    'GGUFHeader',
    'get_gguf_validator',
    'HardwareDetector',
    'get_hardware_detector',
    'ModelDownloader',
    'DownloadProgress',
    'get_model_downloader'
]
