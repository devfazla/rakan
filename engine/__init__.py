"""
Local AI Platform - Engine Module
Inference engine interfaces and implementations.
"""

# Import directly from the module to avoid relative import issues
import sys
from pathlib import Path

# Add engine directory to path
engine_dir = Path(__file__).parent
sys.path.insert(0, str(engine_dir))

from llama_cpp.interface import LlamaCppInterface, InferenceResult, get_llama_cpp_interface

__all__ = [
    'LlamaCppInterface',
    'InferenceResult',
    'get_llama_cpp_interface'
]
