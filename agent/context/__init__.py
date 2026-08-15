"""
Local AI Platform - Agent Context Module
Project context detection and understanding.
"""

from .detector import ProjectDetector, ProjectInfo, get_project_detector
from .searcher import FileSearcher, FileIndex, SearchResult, get_file_searcher
from .builder import ContextBuilder, ContextFile, ProjectContext, get_context_builder
from .instructions import InstructionManager, InstructionFile, get_instruction_manager
from .config_parser import ConfigParser, ConfigFile, get_config_parser
from .git_integration import GitIntegration, GitStatus, GitDiff, get_git_integration

__all__ = [
    'ProjectDetector',
    'ProjectInfo',
    'get_project_detector',
    'FileSearcher',
    'FileIndex',
    'SearchResult',
    'get_file_searcher',
    'ContextBuilder',
    'ContextFile',
    'ProjectContext',
    'get_context_builder',
    'InstructionManager',
    'InstructionFile',
    'get_instruction_manager',
    'ConfigParser',
    'ConfigFile',
    'get_config_parser',
    'GitIntegration',
    'GitStatus',
    'GitDiff',
    'get_git_integration'
]
