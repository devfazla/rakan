"""
Local AI Platform - Agent CLI Command
Commands for agent operations and tool execution.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def agent_command(args):
    """
    Execute agent command.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Import agent components
    import agent.core.agent as agent_module
    import agent.tools.executor as tools_module
    import agent.tools.permissions as permissions_module
    
    # Get components
    agent = agent_module.get_agent()
    permission_manager = permissions_module.get_permission_manager()
    
    # Set permission callback for dangerous operations
    def permission_callback(tool_name: str, parameters: dict) -> bool:
        """Callback for permission requests."""
        print(f"\nPermission request for tool: {tool_name}")
        print(f"Parameters: {parameters}")
        
        if not args.auto_approve:
            response = input("Approve this operation? (y/N): ")
            return response.lower() == 'y'
        return True
    
    agent.tool_executor.set_permission_callback(permission_callback)
    
    # Set context
    project_dir = getattr(args, 'directory', '.')
    agent.set_context({
        "project_directory": project_dir,
        "auto_approve": args.auto_approve
    })
    
    # Execute based on mode
    if args.mode == 'interactive':
        return interactive_mode(agent, args)
    elif args.mode == 'single':
        return single_task_mode(agent, args)
    else:
        print(f"Unknown mode: {args.mode}")
        return 1


def interactive_mode(agent, args):
    """
    Interactive agent mode.
    
    Args:
        agent: Agent instance
        args: Command-line arguments
        
    Returns:
        Exit code
    """
    print(f"\n{'='*70}")
    print("INTERACTIVE AGENT MODE")
    print(f"{'='*70}")
    print("Type 'exit' or 'quit' to end the session")
    print(f"{'='*70}\n")
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("Ending agent session...")
                break
            
            if user_input.lower() == 'help':
                print("\nAvailable commands:")
                print("  exit/quit/q - End the session")
                print("  help - Show this help message")
                print("\nAsk the agent to perform tasks like:")
                print("  'Read the README file'")
                print("  'List directory contents'")
                print("  'Check git status'")
                print("  'Search for Python files'")
                continue
            
            # Process message
            print(f"\nAgent: ", end='', flush=True)
            response = agent.process_message(user_input)
            print(response)
            print()
            
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            break
        except Exception as e:
            print(f"Error: {e}")
            logger.error(f"Agent error: {e}")
            break
    
    return 0


def single_task_mode(agent, args):
    """
    Single task execution mode.
    
    Args:
        agent: Agent instance
        args: Command-line arguments
        
    Returns:
        Exit code
    """
    task = args.task
    
    if not task:
        print("Error: No task specified for single mode")
        print("Use --task to specify the task")
        return 1
    
    print(f"\nExecuting task: {task}")
    
    # Process the task
    response = agent.process_message(task)
    
    print(f"\nAgent response:\n{response}")
    
    return 0


def show_permissions(args):
    """
    Show current permission rules.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code
    """
    from agent.tools.permissions import get_permission_manager
    
    manager = get_permission_manager()
    rules = manager.get_rules()
    
    print(f"\n{'='*70}")
    print("PERMISSION RULES")
    print(f"{'='*70}\n")
    
    for operation, rule in rules.items():
        print(f"\nOperation: {operation}")
        print(f"  Level: {rule.level.value}")
        print(f"  Dangerous: {rule.dangerous}")
        print(f"  Requires confirmation: {rule.requires_confirmation}")
        
        if rule.denied_paths:
            print(f"  Denied paths: {', '.join(rule.denied_paths[:5])}")
        
        if rule.allowed_paths:
            print(f"  Allowed paths: {', '.join(rule.allowed_paths[:5])}")
    
    print(f"\n{'='*70}\n")
    
    return 0


def show_audit_log(args):
    """
    Show audit log.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code
    """
    from agent.tools.permissions import get_permission_manager
    
    manager = get_permission_manager()
    audit_log = manager.get_audit_log(limit=args.limit)
    
    print(f"\n{'='*70}")
    print("AUDIT LOG")
    print(f"{'='*70}\n")
    
    if not audit_log:
        print("No audit log entries")
        return 0
    
    for entry in audit_log:
        print(f"\nTimestamp: {entry['timestamp']}")
        print(f"Operation: {entry['operation']}")
        print(f"Allowed: {entry['allowed']}")
        print(f"Parameters: {entry['parameters']}")
        
        if entry['result']:
            print(f"Result: {entry['result']}")
    
    print(f"\n{'='*70}\n")
    
    return 0


def start_server(args):
    """
    Start the API server.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code
    """
    print(f"\n{'='*70}")
    print("STARTING API SERVER")
    print(f"{'='*70}\n")
    
    try:
        from backend.api import create_server
        
        server = create_server(
            host=args.host,
            port=args.port
        )
        
        print(f"Starting server on {args.host}:{args.port}")
        print("Press Ctrl+C to stop the server")
        print(f"{'='*70}\n")
        
        server.run()
        
    except ImportError as e:
        print(f"Error: {e}")
        print("Install FastAPI and Uvicorn: pip install fastapi uvicorn")
        return 1
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
        return 0
    except Exception as e:
        print(f"Error starting server: {e}")
        return 1