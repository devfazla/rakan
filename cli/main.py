"""
RAKAN - Main CLI Entry Point
Provides the command-line interface for RAKAN.
"""

import sys
import argparse
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
from cli.utils import terminal, print_banner, print_version, print_help_summary


def show_ascii_intro():
    """Display RAKAN ASCII art introduction with responsive sizing."""
    try:
        import shutil
        terminal_width = shutil.get_terminal_size().columns
        
        ascii_file = project_root / "rakan_ascii.txt"
        if ascii_file.exists():
            with open(ascii_file, 'r') as f:
                ascii_content = f.read()
                # Extract ASCII art from between the triple quotes
                if '"""' in ascii_content:
                    start = ascii_content.find('"""') + 3
                    end = ascii_content.rfind('"""')
                    if start < end:
                        ascii_art = ascii_content[start:end].strip()
                        
                        # Responsive scaling based on terminal width
                        if terminal_width < 60:
                            # Very small terminal - show simple version
                            terminal.print_colored("RAKAN - Local AI Development Platform", 'cyan', bold=True)
                            terminal.print_colored("Created by DevFazla", 'magenta')
                            print()
                        elif terminal_width < 80:
                            # Small terminal - show condensed version
                            lines = ascii_art.split('\n')
                            condensed = [line for line in lines if line.strip()]
                            for line in condensed[:3]:  # Show first 3 lines
                                terminal.print_colored(line, 'cyan')
                            terminal.print_colored("RAKAN - Local AI Development Platform", 'cyan', bold=True)
                            print()
                        else:
                            # Normal terminal - show full version
                            terminal.print_colored(ascii_art, 'cyan')
                            print()
        else:
            terminal.print_colored("RAKAN - Local AI Development Platform", 'cyan', bold=True)
            terminal.print_colored("Created by DevFazla", 'magenta')
            print()
    except Exception:
        terminal.print_colored("RAKAN - Local AI Development Platform", 'cyan', bold=True)
        terminal.print_colored("Created by DevFazla", 'magenta')
        print()


class RAKANCLI:
    """Main CLI application for RAKAN."""
    
    def __init__(self):
        self.config_manager = None
        self.logger = None
        
    def setup(self):
        """Setup CLI environment."""
        # Setup configuration and logging
        self.config_manager = get_config_manager()
        setup_logging_from_config()
        self.logger = get_logger(__name__)
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser."""
        parser = argparse.ArgumentParser(
            prog='rakan',
            description='RAKAN - A local-first AI coding assistant',
            epilog='For more information, visit https://devfazla.com or check the documentation.',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        parser.epilog = """
Examples:
  rakan doctor              Check system health
  rakan model list          List available models
  rakan model use <name>    Select a model
  rakan chat                Start interactive chat
  
For more information, see: https://github.com/devfazla/rakan
        """
        
        # Global options
        parser.add_argument(
            '--config',
            type=str,
            help='Path to configuration file'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
        parser.add_argument(
            '--quiet',
            action='store_true',
            help='Suppress output'
        )
        parser.add_argument(
            '--version',
            action='store_true',
            help='Show version information'
        )
        
        # Subcommands
        subparsers = parser.add_subparsers(
            dest='command',
            help='Available commands',
            metavar='COMMAND'
        )
        
        # rakan doctor
        self._add_doctor_command(subparsers)
        
        # rakan model
        model_parser = subparsers.add_parser(
            'model',
            help='Manage AI models'
        )
        model_subparsers = model_parser.add_subparsers(
            dest='model_command',
            help='Model management commands'
        )
        
        # rakan model list
        list_parser = model_subparsers.add_parser(
            'list',
            help='List available and installed models'
        )
        list_parser.add_argument(
            '--available',
            action='store_true',
            help='Show only available models'
        )
        list_parser.add_argument(
            '--installed',
            action='store_true',
            help='Show only installed models'
        )
        
        # rakan model install
        install_parser = model_subparsers.add_parser(
            'install',
            help='Download and install a model'
        )
        install_parser.add_argument(
            'model_name',
            type=str,
            help='Name of model to install'
        )
        
        # rakan model remove
        remove_parser = model_subparsers.add_parser(
            'remove',
            help='Remove an installed model'
        )
        remove_parser.add_argument(
            'model_name',
            type=str,
            help='Name of model to remove'
        )
        
        # rakan model use
        use_parser = model_subparsers.add_parser(
            'use',
            help='Select active model'
        )
        use_parser.add_argument(
            'model_name',
            type=str,
            help='Name of model to use'
        )
        
        # rakan model info
        info_parser = model_subparsers.add_parser(
            'info',
            help='Show detailed information about a model'
        )
        info_parser.add_argument(
            'model_name',
            type=str,
            help='Name of model'
        )
        
        # rakan chat
        chat_parser = subparsers.add_parser(
            'chat',
            help='Start interactive chat'
        )
        chat_parser.add_argument(
            '--model',
            type=str,
            help='Use specific model'
        )
        chat_parser.add_argument(
            '--project',
            type=str,
            help='Work with specific project'
        )
        chat_parser.add_argument(
            '--session',
            type=str,
            help='Resume existing session'
        )
        chat_parser.add_argument(
            '--temperature',
            type=float,
            default=0.7,
            help='Sampling temperature (0.0-2.0)'
        )
        chat_parser.add_argument(
            '--max-tokens',
            type=int,
            default=1024,
            help='Maximum tokens to generate'
        )
        
        # rakan project
        project_parser = subparsers.add_parser(
            'project',
            help='Project context and initialization'
        )
        project_subparsers = project_parser.add_subparsers(
            dest='project_command',
            help='Project management commands'
        )
        
        # rakan project context
        context_parser = project_subparsers.add_parser(
            'context',
            help='Show project context information'
        )
        context_parser.add_argument(
            '--directory',
            type=str,
            default='.',
            help='Project directory (default: current directory)'
        )
        context_parser.add_argument(
            '--build-context',
            action='store_true',
            help='Build AI context from project'
        )
        context_parser.add_argument(
            '--query',
            type=str,
            help='Query for context building'
        )
        context_parser.add_argument(
            '--strategy',
            type=str,
            default='structure',
            choices=['structure', 'recent', 'relevant', 'full'],
            help='Context building strategy'
        )
        context_parser.add_argument(
            '--max-files',
            type=int,
            default=5,
            help='Maximum files to include in context'
        )
        context_parser.add_argument(
            '--max-tokens',
            type=int,
            default=2000,
            help='Maximum tokens for context'
        )
        context_parser.add_argument(
            '--show-context',
            action='store_true',
            help='Show formatted context for prompt'
        )
        
        # rakan project init
        init_parser = project_subparsers.add_parser(
            'init',
            help='Initialize project for AI understanding'
        )
        init_parser.add_argument(
            '--directory',
            type=str,
            default='.',
            help='Project directory (default: current directory)'
        )
        init_parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite existing instructions file'
        )
        
        # rakan agent
        agent_parser = subparsers.add_parser(
            'agent',
            help='Agent operations and tool execution'
        )
        agent_subparsers = agent_parser.add_subparsers(
            dest='agent_command',
            help='Agent management commands'
        )
        
        # rakan agent run
        run_parser = agent_subparsers.add_parser(
            'run',
            help='Run agent in interactive mode'
        )
        run_parser.add_argument(
            '--mode',
            type=str,
            default='interactive',
            choices=['interactive', 'single'],
            help='Agent execution mode'
        )
        run_parser.add_argument(
            '--task',
            type=str,
            help='Task to execute (for single mode)'
        )
        run_parser.add_argument(
            '--directory',
            type=str,
            default='.',
            help='Working directory'
        )
        run_parser.add_argument(
            '--auto-approve',
            action='store_true',
            help='Auto-approve all operations'
        )
        
        # rakan agent permissions
        permissions_parser = agent_subparsers.add_parser(
            'permissions',
            help='Show permission rules'
        )
        
        # rakan agent audit
        audit_parser = agent_subparsers.add_parser(
            'audit',
            help='Show audit log'
        )
        audit_parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Maximum number of entries to show'
        )
        
        # rakan server
        server_parser = subparsers.add_parser(
            'server',
            help='Start API server'
        )
        server_parser.add_argument(
            '--host',
            type=str,
            default='127.0.0.1',
            help='Host to bind to'
        )
        server_parser.add_argument(
            '--port',
            type=int,
            default=8000,
            help='Port to bind to'
        )
        
        self._add_doctor_command(subparsers)
        
        return parser
    
    def _add_doctor_command(self, subparsers):
        """Add doctor command to parser."""
        doctor_parser = subparsers.add_parser(
            'doctor',
            help='Check system health and configuration'
        )
        doctor_parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix detected issues automatically'
        )
        doctor_parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed diagnostic information'
        )
    
    def run(self, args=None):
        """Run the CLI application."""
        # Setup environment
        self.setup()
        
        # Parse arguments
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)
        
        # Handle version
        if parsed_args.version:
            self.show_version()
            return 0
        
        # Handle no command
        if not parsed_args.command:
            print_banner()
            print_help_summary()
            parser.print_help()
            return 0
        
        # Handle verbose/quiet
        if parsed_args.verbose:
            self.logger.setLevel('DEBUG')
        elif parsed_args.quiet:
            self.logger.setLevel('ERROR')
        
        # Route to command handler
        try:
            return self.handle_command(parsed_args)
        except Exception as e:
            self.logger.error(f"Command failed: {e}")
            return 1
    
    def handle_command(self, args):
        """Route command to appropriate handler."""
        command = args.command
        
        if command == 'doctor':
            return self.handle_doctor(args)
        elif command == 'model':
            return self.handle_model(args)
        elif command == 'chat':
            return self.handle_chat(args)
        elif command == 'project':
            return self.handle_project(args)
        elif command == 'agent':
            return self.handle_agent(args)
        elif command == 'server':
            return start_server(args)
        else:
            self.logger.error(f"Unknown command: {command}")
            return 1
    
    def handle_doctor(self, args):
        """Handle doctor command."""
        return run_doctor(detailed=args.detailed, fix=args.fix)
    
    def handle_model(self, args):
        """Handle model commands."""
        model_command = args.model_command
        
        if model_command == 'list':
            return list_models(available=args.available, installed=args.installed)
        elif model_command == 'install':
            return install_model(args.model_name)
        elif model_command == 'remove':
            return remove_model(args.model_name)
        elif model_command == 'use':
            return use_model(args.model_name)
        elif model_command == 'info':
            return model_info(args.model_name)
        else:
            self.logger.error(f"Unknown model command: {model_command}")
            return 1
    
    def handle_chat(self, args):
        """Handle chat command."""
        return chat(args)
    
    def handle_project(self, args):
        """Handle project commands."""
        project_command = args.project_command
        
        if project_command == 'context':
            return project_context(args)
        elif project_command == 'init':
            return init_project(args)
        else:
            self.logger.error(f"Unknown project command: {project_command}")
            return 1
    
    def handle_agent(self, args):
        """Handle agent commands."""
        agent_command = args.agent_command
        
        if agent_command == 'run':
            return agent_command(args)
        elif agent_command == 'permissions':
            return show_permissions(args)
        elif agent_command == 'audit':
            return show_audit_log(args)
        else:
            self.logger.error(f"Unknown agent command: {agent_command}")
            return 1
    
    def show_version(self):
        """Show version information."""
        print_version()


def main():
    """Main entry point."""
    # Show ASCII intro
    show_ascii_intro()
    
    cli = RAKANCLI()
    sys.exit(cli.run())


if __name__ == '__main__':
    main()