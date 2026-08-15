"""
Local AI Platform - Backend Sessions Module
Session management for conversations.
"""

from .session import Message, Session, SessionManager, get_session_manager

__all__ = [
    'Message',
    'Session',
    'SessionManager',
    'get_session_manager'
]
