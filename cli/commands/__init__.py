"""
Local AI Platform - CLI Commands Module
Contains command implementations for the CLI interface.
"""

from .doctor import run_doctor, SystemDoctor
from .model import list_models, install_model, remove_model, use_model, model_info
from .chat import chat
from .project import project_context, init_project
from .agent_cmd import agent_command, show_permissions, show_audit_log, start_server

__all__ = [
    'run_doctor',
    'SystemDoctor',
    'list_models',
    'install_model',
    'remove_model',
    'use_model',
    'model_info',
    'chat',
    'project_context',
    'init_project',
    'agent_command',
    'show_permissions',
    'show_audit_log',
    'start_server'
]
