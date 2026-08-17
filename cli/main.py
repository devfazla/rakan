"""
RAKAN - Main CLI Entry Point
Interactive CLI that captures terminal like claudecode
"""

import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent.core import setup_logging_from_config, get_config_manager, get_logger
from cli.commands.doctor import run_doctor
from cli.commands.model import list_models, install_model, remove_model, use_model, model_info
from cli.commands.chat import chat
from cli.commands.project import project_context, init_project
from cli.commands.agent_cmd import agent_command, show_permissions, show_audit_log, start_server


def show_ascii_intro():
    """Display RAKAN ASCII art introduction."""
    try:
        ascii_file = project_root / "rakan_ascii.txt"
        if ascii_file.exists():
            with open(ascii_file, 'r') as f:
                ascii_content = f.read()
                if '"""' in ascii_content:
                    start = ascii_content.find('"""') + 3
                    end = ascii_content.rfind('"""')
                    if start < end:
                        ascii_art = ascii_content[start:end].strip()
                        print(ascii_art)
                        print()
        else:
            print("RAKAN - Local AI Development Platform")
            print("@devFazla")
            print()
    except Exception:
        print("RAKAN - Local AI Development Platform")
        print("@devFazla")
        print()


class RAKANCLI:
    """Interactive CLI that captures terminal like claudecode."""
    
    def __init__(self):
        self.config_manager = None
        self.logger = None
        self.running = True
        
    def setup(self):
        """Setup CLI environment."""
        self.config_manager = get_config_manager()
        setup_logging_from_config()
        self.logger = get_logger(__name__)
    
    def show_help(self):
        """Show help menu."""
        print("\n" + "=" * 60)
        print("RAKAN - Interactive CLI")
        print("=" * 60)
        print("\nAvailable commands:")
        print("  help          - Show this help")
        print("  start         - Start all RAKAN components")
        print("  cli           - Already in CLI mode")
        print("  web           - Start web server")
        print("  engine        - Start inference engine")
        print("  doctor        - Check system health")
        print("  model list    - List available models")
        print("  model install <name> - Install a model")
        print("  model use <name>     - Select active model")
        print("  chat          - Start interactive chat")
        print("  project       - Project context operations")
        print("  agent         - Agent operations")
        print("  server        - Start API server")
        print("  status        - Show system status")
        print("  uninstall      - Uninstall RAKAN")
        print("  exit          - Exit RAKAN")
        print("=" * 60 + "\n")
    
    def handle_command(self, command_line):
        """Handle user command."""
        parts = command_line.strip().split()
        if not parts:
            return
        
        command = parts[0].lower()
        args = parts[1:]
        
        try:
            if command in ['exit', 'quit', 'q']:
                self.running = False
                print("Goodbye!")
                return
            
            elif command == 'help':
                self.show_help()
            
            elif command == 'doctor':
                run_doctor(detailed='--detailed' in args, fix='--fix' in args)
            
            elif command == 'model':
                if not args:
                    list_models(None)
                elif args[0] == 'list':
                    list_models(None)
                elif args[0] == 'install' and len(args) > 1:
                    install_model(args[1])
                elif args[0] == 'remove' and len(args) > 1:
                    remove_model(args[1])
                elif args[0] == 'use' and len(args) > 1:
                    use_model(args[1])
                elif args[0] == 'info' and len(args) > 1:
                    model_info(args[1])
                else:
                    print("Unknown model command. Use 'model list' for available commands.")
            
            elif command == 'chat':
                # Create a simple args object
                class Args:
                    pass
                args_obj = Args()
                args_obj.model = None
                args_obj.project = '.'
                args_obj.session = None
                args_obj.temperature = 0.7
                args_obj.max_tokens = 1024
                chat(args_obj)
            
            elif command == 'project':
                if not args:
                    print("Use 'project context' or 'project init'")
                elif args[0] == 'context':
                    class Args:
                        pass
                    args_obj = Args()
                    args_obj.directory = '.'
                    args_obj.build_context = False
                    args_obj.query = None
                    args_obj.strategy = 'structure'
                    args_obj.max_files = 5
                    args_obj.max_tokens = 2000
                    args_obj.show_context = False
                    project_context(args_obj)
                elif args[0] == 'init':
                    class Args:
                        pass
                    args_obj = Args()
                    args_obj.directory = '.'
                    args_obj.force = False
                    init_project(args_obj)
            
            elif command == 'agent':
                class Args:
                    pass
                args_obj = Args()
                args_obj.mode = 'interactive'
                args_obj.task = None
                args_obj.directory = '.'
                args_obj.auto_approve = False
                agent_command(args_obj)
            
            elif command == 'server':
                class Args:
                    pass
                args_obj = Args()
                args_obj.host = '127.0.0.1'
                args_obj.port = 8000
                print("Starting server... (Press Ctrl+C to stop)")
                start_server(args_obj)
            
            elif command == 'status':
                self.show_status()
            
            elif command == 'start':
                self.start_all()
            
            elif command == 'cli':
                # Already in CLI mode
                print("Already in CLI mode")
            
            elif command == 'web':
                self.start_web()
            
            elif command == 'engine':
                self.start_engine()
            
            elif command == 'uninstall':
                self.uninstall_rakan()
            
            else:
                print(f"Unknown command: {command}")
                print("Type 'help' for available commands")
        
        except KeyboardInterrupt:
            print("\nCommand interrupted. Type 'exit' to quit.")
        except Exception as e:
            print(f"Error: {e}")
    
    def show_status(self):
        """Show system status."""
        print("\n" + "=" * 60)
        print("RAKAN Status")
        print("=" * 60)
        
        # Show config status
        if self.config_manager:
            config = self.config_manager.get_config()
            print(f"Application: {config.get('name', 'RAKAN')}")
            print(f"Version: {config.get('version', '0.1.0')}")
        
        # Show directory status
        data_dir = os.path.expanduser("~/.rakan")
        if os.path.exists(data_dir):
            print(f"Data directory: {data_dir}")
            print(f"Models: {len(os.listdir(os.path.join(data_dir, 'models'))) if os.path.exists(os.path.join(data_dir, 'models')) else 0}")
        else:
            print("Data directory: Not created")
        
        print("=" * 60 + "\n")
    
    def start_all(self):
        """Start all RAKAN components."""
        print("\nStarting all RAKAN components...")
        print("This will start:")
        print("  - CLI (Interactive mode)")
        print("  - Web Server (http://localhost:8000)")
        print("  - Agent (Background)")
        print()
        print("Note: Starting all components simultaneously is not yet implemented.")
        print("Use individual commands:")
        print("  'web' to start web server")
        print("  'agent' to start agent")
        print("  Already in CLI mode")
    
    def start_web(self):
        """Start web server."""
        print("\nStarting web server...")
        class Args:
            pass
        args_obj = Args()
        args_obj.host = '127.0.0.1'
        args_obj.port = 8000
        print("Web server starting at http://localhost:8000")
        print("Press Ctrl+C to stop")
        try:
            start_server(args_obj)
        except KeyboardInterrupt:
            print("\nWeb server stopped")
    
    def start_engine(self):
        """Start engine."""
        print("\nStarting engine...")
        print("Engine starting...")
        print("Note: Full engine integration with llama.cpp is not yet implemented.")
        print("Use 'model list' and 'model install' to set up models first.")
    
    def uninstall_rakan(self):
        """Uninstall RAKAN from system."""
        import platform as pf
        import os
        import shutil
        
        print("=" * 60)
        print("RAKAN Uninstallation")
        print("=" * 60)
        print()
        
        print("This will remove:")
        print("  - Wrapper file")
        print("  - Data directory")
        print("  - PATH entry (manual instructions)")
        print()
        
        try:
            response = input("Do you want to proceed? (y/n): ").strip().lower()
            if response != 'y':
                print("Uninstallation cancelled.")
                return
        except (EOFError, KeyboardInterrupt):
            print("\nUninstallation cancelled.")
            return
        
        print()
        print("Starting uninstallation...")
        print()
        
        # Remove wrapper file
        system = pf.system()
        if system == "Windows":
            user_profile = os.path.expanduser("~")
            wrapper_file = os.path.join(user_profile, "rakan.bat")
        else:
            wrapper_file = os.path.join(os.path.expanduser("~/.local/bin"), "rakan")
        
        try:
            if os.path.exists(wrapper_file):
                os.remove(wrapper_file)
                print(f"[OK] Removed wrapper: {wrapper_file}")
            else:
                print(f"[MISSING] Wrapper not found: {wrapper_file}")
        except Exception as e:
            print(f"[ERROR] Failed to remove wrapper: {e}")
        
        # Remove data directory
        data_dir = os.path.expanduser("~/.rakan")
        try:
            if os.path.exists(data_dir):
                shutil.rmtree(data_dir)
                print(f"[OK] Removed data directory: {data_dir}")
            else:
                print(f"[MISSING] Data directory not found: {data_dir}")
        except Exception as e:
            print(f"[ERROR] Failed to remove data directory: {e}")
        
        print()
        print("=" * 60)
        print("Uninstallation Complete!")
        print("=" * 60)
        print()
        print("Please manually remove PATH entry if needed.")
        print("Thank you for using RAKAN!")
        print()
    
    def run_interactive(self):
        """Run interactive CLI loop."""
        show_ascii_intro()
        print("RAKAN Interactive CLI")
        print("Type 'help' for available commands, 'exit' to quit")
        print()
        
        while self.running:
            try:
                command = input("rakan> ").strip()
                if command:
                    self.handle_command(command)
            except EOFError:
                print("\nGoodbye!")
                break
            except KeyboardInterrupt:
                print("\nType 'exit' to quit or press Ctrl+C again to force quit")
                # Don't break on first Ctrl+C, give user a chance to type exit
    
    def run_command(self, command):
        """Run single command and exit."""
        show_ascii_intro()
        self.handle_command(command)


def main():
    """Main entry point."""
    cli = RAKANCLI()
    cli.setup()
    
    # Check if running in interactive mode or single command
    if len(sys.argv) > 1:
        # Single command mode
        command = ' '.join(sys.argv[1:])
        cli.run_command(command)
    else:
        # Interactive mode
        cli.run_interactive()


if __name__ == '__main__':
    main()