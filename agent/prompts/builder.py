"""
Local AI Platform - Prompt Construction
Handles prompt building and formatting for LLM interactions.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PromptTemplate:
    """Template for prompt construction."""
    name: str
    system_prompt: str
    user_template: str
    assistant_template: str
    context_template: str
    max_history: int = 10


class PromptBuilder:
    """Builds prompts for LLM interactions."""
    
    def __init__(self):
        """Initialize prompt builder."""
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default prompt templates."""
        # Default coding assistant template
        self.templates['coding'] = PromptTemplate(
            name='coding',
            system_prompt="""You are a helpful AI coding assistant. You help with programming tasks, code understanding, debugging, and software development.

Follow these guidelines:
- Be concise and direct in your responses
- Provide clear, working code examples
- Explain your reasoning when appropriate
- Ask for clarification when you don't understand
- Consider security and best practices
- Use modern coding standards and patterns""",
            user_template='User: {content}',
            assistant_template='Assistant: {content}',
            context_template='Here is our conversation history:\n{history}\n\nCurrent task: {user_message}',
            max_history=10
        )
        
        # Default chat template
        self.templates['chat'] = PromptTemplate(
            name='chat',
            system_prompt="""You are a helpful AI assistant. You engage in conversations, answer questions, and provide assistance on various topics.

Be helpful, accurate, and considerate in your responses.""",
            user_template='Human: {content}',
            assistant_template='Assistant: {content}',
            context_template='Conversation history:\n{history}\n\nHuman: {user_message}',
            max_history=10
        )
        
        logger.info(f"Loaded {len(self.templates)} default templates")
    
    def register_template(self, template: PromptTemplate):
        """
        Register a custom prompt template.
        
        Args:
            template: PromptTemplate to register
        """
        self.templates[template.name] = template
        logger.info(f"Registered template: {template.name}")
    
    def build_prompt(
        self,
        user_message: str,
        template_name: str = 'coding',
        conversation_history: Optional[List[Dict[str, str]]] = None,
        context: Optional[str] = None,
        max_history: Optional[int] = None
    ) -> str:
        """
        Build a complete prompt from components.
        
        Args:
            user_message: Current user message
            template_name: Name of template to use
            conversation_history: Optional conversation history
            context: Optional additional context
            max_history: Maximum history messages to include
            
        Returns:
            Complete prompt string
        """
        template = self.templates.get(template_name, self.templates['coding'])
        
        # Start with system prompt
        prompt_parts = [template.system_prompt]
        
        # Add context if provided
        if context:
            prompt_parts.append(f"\n{context}")
        
        # Add conversation history
        if conversation_history:
            history_to_include = conversation_history[-max_history:] if max_history else conversation_history
            history_to_include = history_to_include[-template.max_history:]
            
            if history_to_include:
                history_text = "\n".join([
                    f"{msg['role']}: {msg['content']}"
                    for msg in history_to_include
                ])
                prompt_parts.append(f"\n{history_text}")
        
        # Add current user message
        if template.context_template:
            prompt_parts.append(
                template.context_template.format(
                    history=self._format_history(conversation_history, template.max_history) if conversation_history else "No previous conversation",
                    user_message=user_message
                )
            )
        else:
            prompt_parts.append(f"\n{template.user_template.format(content=user_message)}")
        
        return "\n".join(prompt_parts)
    
    def _format_history(self, conversation_history: List[Dict[str, str]], max_messages: int) -> str:
        """
        Format conversation history for prompt.
        
        Args:
            conversation_history: List of message dictionaries
            max_messages: Maximum messages to include
            
        Returns:
            Formatted history string
        """
        if not conversation_history:
            return "No previous conversation"
        
        history_to_include = conversation_history[-max_messages:]
        
        return "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in history_to_include
        ])
    
    def build_chat_prompt(
        self,
        messages: List[Dict[str, str]],
        template_name: str = 'coding'
    ) -> str:
        """
        Build a prompt from a list of messages.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            template_name: Name of template to use
            
        Returns:
            Complete prompt string
        """
        template = self.templates.get(template_name, self.templates['coding'])
        
        prompt_parts = [template.system_prompt]
        
        for msg in messages:
            if msg['role'] == 'user':
                prompt_parts.append(f"\n{template.user_template.format(content=msg['content'])}")
            elif msg['role'] == 'assistant':
                prompt_parts.append(f"\n{template.assistant_template.format(content=msg['content'])}")
            elif msg['role'] == 'system':
                prompt_parts.append(f"\nSystem: {msg['content']}")
        
        return "\n".join(prompt_parts)
    
    def extract_system_prompt(self, template_name: str = 'coding') -> str:
        """
        Extract system prompt from template.
        
        Args:
            template_name: Name of template
            
        Returns:
            System prompt string
        """
        template = self.templates.get(template_name, self.templates['coding'])
        return template.system_prompt
    
    def estimate_tokens(self, prompt: str) -> int:
        """
        Estimate token count for a prompt.
        
        Args:
            prompt: Prompt string
            
        Returns:
            Estimated token count
        """
        # Rough approximation: ~4 characters per token
        return len(prompt) // 4
    
    def truncate_for_context(
        self,
        prompt: str,
        max_tokens: int,
        from_bottom: bool = True
    ) -> str:
        """
        Truncate prompt to fit within token limit.
        
        Args:
            prompt: Prompt string
            max_tokens: Maximum tokens
            from_bottom: Whether to truncate from bottom (keep system prompt)
            
        Returns:
            Truncated prompt
        """
        current_tokens = self.estimate_tokens(prompt)
        
        if current_tokens <= max_tokens:
            return prompt
        
        # Calculate how much to truncate
        tokens_to_remove = current_tokens - max_tokens
        chars_to_remove = tokens_to_remove * 4
        
        if from_bottom:
            # Truncate from the end (keep system prompt)
            return prompt[:-chars_to_remove]
        else:
            # Truncate from the beginning
            return prompt[chars_to_remove:]
    
    def add_code_context(
        self,
        prompt: str,
        code: str,
        language: str = "python"
    ) -> str:
        """
        Add code context to a prompt.
        
        Args:
            prompt: Original prompt
            code: Code to add
            language: Programming language
            
        Returns:
            Prompt with code context
        """
        code_context = f"\n\nHere is the relevant code ({language}):\n```\n{code}\n```"
        return prompt + code_context
    
    def manage_context_window(
        self,
        conversation_history: List[Dict[str, str]],
        max_tokens: int,
        system_prompt: str
    ) -> tuple[List[Dict[str, str]], str]:
        """
        Manage context window by fitting conversation within token limit.
        
        Args:
            conversation_history: List of conversation messages
            max_tokens: Maximum token budget
            system_prompt: System prompt to include
            
        Returns:
            Tuple of (filtered_history, status_message)
        """
        # Count tokens for system prompt
        system_tokens = self.estimate_tokens(system_prompt)
        available_tokens = max_tokens - system_tokens
        
        if available_tokens <= 0:
            return [], f"System prompt alone exceeds token limit ({system_tokens} > {max_tokens})"
        
        # Calculate tokens for conversation history
        filtered_history = []
        used_tokens = system_tokens
        
        # Add messages from newest to oldest until we hit the limit
        for msg in reversed(conversation_history):
            msg_tokens = self.estimate_tokens(msg['content'])
            
            if used_tokens + msg_tokens <= available_tokens:
                filtered_history.insert(0, msg)
                used_tokens += msg_tokens
            else:
                break
        
        status = f"Using {len(filtered_history)}/{len(conversation_history)} messages ({used_tokens}/{max_tokens} tokens)"
        
        return filtered_history, status
    
    def get_context_stats(
        self,
        conversation_history: List[Dict[str, str]],
        system_prompt: str
    ) -> Dict[str, Any]:
        """
        Get statistics about context usage.
        
        Args:
            conversation_history: List of conversation messages
            system_prompt: System prompt
            
        Returns:
            Dictionary with context statistics
        """
        system_tokens = self.estimate_tokens(system_prompt)
        history_tokens = sum(self.estimate_tokens(msg['content']) for msg in conversation_history)
        total_tokens = system_tokens + history_tokens
        
        return {
            'system_tokens': system_tokens,
            'history_tokens': history_tokens,
            'total_tokens': total_tokens,
            'message_count': len(conversation_history),
            'estimated_chars': total_tokens * 4
        }
    
    def add_file_context(
        self,
        prompt: str,
        file_path: str,
        content: str
    ) -> str:
        """
        Add file context to a prompt.
        
        Args:
            prompt: Original prompt
            file_path: Path to the file
            content: File content
            
        Returns:
            Prompt with file context
        """
        file_context = f"\n\nFile: {file_path}\n```\n{content}\n```"
        return prompt + file_context


# Global prompt builder instance
_prompt_builder = None


def get_prompt_builder() -> PromptBuilder:
    """
    Get global prompt builder instance.
    
    Returns:
        PromptBuilder instance
    """
    global _prompt_builder
    if _prompt_builder is None:
        _prompt_builder = PromptBuilder()
    return _prompt_builder


# Example usage and testing
if __name__ == "__main__":
    # Test prompt builder
    print("Testing Prompt Builder...")
    
    builder = get_prompt_builder()
    
    # Test basic prompt building
    prompt = builder.build_prompt("Help me write a function to sort a list")
    print(f"\nBasic prompt:\n{prompt}")
    
    # Test with conversation history
    history = [
        {'role': 'user', 'content': 'What is Python?'},
        {'role': 'assistant', 'content': 'Python is a programming language.'}
    ]
    prompt_with_history = builder.build_prompt("How do I install it?", conversation_history=history)
    print(f"\nPrompt with history:\n{prompt_with_history}")
    
    # Test token estimation
    tokens = builder.estimate_tokens(prompt)
    print(f"\nEstimated tokens: {tokens}")
    
    # Test code context
    code = "def hello():\n    print('Hello, World!')"
    prompt_with_code = builder.add_code_context("Write a greeting function", code, "python")
    print(f"\nPrompt with code:\n{prompt_with_code}")
    
        # Test context window management
    history = [
        {'role': 'user', 'content': 'First message'},
        {'role': 'assistant', 'content': 'Response 1'},
        {'role': 'user', 'content': 'Second message'},
        {'role': 'assistant', 'content': 'Response 2'},
    ]
    
    filtered, status = builder.manage_context_window(history, 100, builder.extract_system_prompt())
    print(f"\nContext window management:")
    print(f"  {status}")
    print(f"  Filtered to {len(filtered)} messages")
    
    # Test context stats
    stats = builder.get_context_stats(history, builder.extract_system_prompt())
    print(f"\nContext stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Test truncation
    long_prompt = "A" * 10000
    truncated = builder.truncate_for_context(long_prompt, 100)
    print(f"\nOriginal length: {len(long_prompt)}, Truncated length: {len(truncated)}")
    
    print("\nPrompt builder test completed!")
