"""
Local AI Platform - Chat CLI Command
Interactive chat interface for the AI assistant.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def chat(args):
    """
    Interactive chat interface.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    logger.info("Starting chat interface...")
    
    # For now, just run demo mode since llama.cpp is not available
    return run_demo_chat()


def generate_demo_response(user_input: str) -> str:
    """Generate a demo response when llama.cpp is not available."""
    responses = [
        "I understand you're asking about: " + user_input + ". Since llama.cpp is not yet installed, I can't provide actual AI responses. This is a demo of the chat interface.",
        "That's an interesting question about: " + user_input + ". In the actual implementation, this would be processed by the loaded model through llama.cpp.",
        "I'd be happy to help with: " + user_input + ". However, the actual inference engine (llama.cpp) needs to be installed first for real AI responses.",
    ]
    
    # Simple rotation based on input length
    index = len(user_input) % len(responses)
    return responses[index]


def run_demo_chat() -> int:
    """Run a demo chat when llama.cpp is not available."""
    print(f"\n{'='*60}")
    print("DEMO MODE - Local AI Chat Interface")
    print(f"{'='*60}")
    print("This is a demonstration of the chat interface.")
    print("The actual AI responses require llama.cpp to be installed.")
    print("\nDemo conversation:")
    print("-" * 40)
    
    # Demo conversation
    demo_inputs = [
        "Hello, how are you?",
        "Can you help me write Python code?",
        "What's the weather like?",
    ]
    
    for i, user_input in enumerate(demo_inputs, 1):
        print(f"\nYou: {user_input}")
        print(f"AI: {generate_demo_response(user_input)}")
        if i < len(demo_inputs):
            print("(Demo continues...)")
    
    print("\n" + "-" * 40)
    print("Demo completed. Install llama.cpp for actual AI responses.")
    print(f"{'='*60}\n")
    
    return 0