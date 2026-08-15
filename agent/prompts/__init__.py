"""
Local AI Platform - Agent Prompts Module
Prompt construction and templates.
"""

from .builder import PromptBuilder, PromptTemplate, get_prompt_builder

__all__ = [
    'PromptBuilder',
    'PromptTemplate',
    'get_prompt_builder'
]
