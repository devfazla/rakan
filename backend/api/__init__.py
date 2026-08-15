"""
Local AI Platform - Backend API Module
HTTP API server and endpoints.
"""

from .server import Server, create_server

try:
    from .server import APIv1
    APIv1_AVAILABLE = True
except ImportError:
    APIv1_AVAILABLE = False

__all__ = [
    'Server',
    'create_server',
    'APIv1' if APIv1_AVAILABLE else None
]
