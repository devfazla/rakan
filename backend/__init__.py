"""
Local AI Platform - Backend Module
Backend API and services.
"""

from .api import Server, create_server

try:
    from .api import APIv1
    APIv1_AVAILABLE = True
except ImportError:
    APIv1_AVAILABLE = False

__all__ = [
    'Server',
    'create_server',
    'APIv1' if APIv1_AVAILABLE else None
]
