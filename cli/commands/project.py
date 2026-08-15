"""
Local AI Platform - Project Context CLI Command
Commands for working with project context and AI understanding.
"""

import sys
from pathlib import Path
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def project_context(args):
    """
    Show project context information.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Add project root to path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    # Import context modules
    import agent.context.detector as detector_module
    import agent.context.searcher as searcher_module
    import agent.context.builder as builder_module
    import agent.context.instructions as instructions_module
    import agent.context.config_parser as config_parser_module
    import agent.context.git_integration as git_module
    
    # Get project directory
    project_dir = getattr(args, 'directory', '.')
    project_path = Path(project_dir).resolve()
    
    if not project_path.exists():
        print(f"Error: Directory does not exist: {project_dir}")
        return 1
    
    logger.info(f"Analyzing project context for: {project_path}")
    
    # Detect project
    print(f"\n{'='*70}")
    print("PROJECT DETECTION")
    print(f"{'='*70}\n")
    
    detector = detector_module.ProjectDetector()
    project_info = detector.detect_project(str(project_path))
    
    if project_info:
        print(f"Project Type: {project_info.project_type}")
        print(f"Project Name: {project_info.name}")
        print(f"Root Path: {project_info.root_path}")
        print(f"Languages: {', '.join(project_info.languages)}")
        print(f"Frameworks: {', '.join(project_info.frameworks)}")
        print(f"Build Systems: {', '.join(project_info.build_systems)}")
        print(f"File Count: {project_info.metadata['file_count']}")
        print(f"Total Size: {project_info.metadata['total_size'] / (1024**2):.2f} MB")
    else:
        print("No project detected")
        return 0
    
    # Show file search statistics
    print(f"\n{'='*70}")
    print("FILE INDEX")
    print(f"{'='*70}\n")
    
    searcher = searcher_module.FileSearcher(str(project_path))
    index = searcher.build_index()
    stats = searcher.get_index_stats()
    
    print(f"Total Files: {stats['total_files']}")
    print(f"Extensions: {stats['total_extensions']}")
    print(f"Directories: {stats['total_directories']}")
    
    # Show top extensions
    print(f"\nTop Extensions:")
    for ext, files in sorted(searcher.index.by_extension.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
        print(f"  {ext}: {len(files)} files")
    
    # Show instructions
    print(f"\n{'='*70}")
    print("PROJECT INSTRUCTIONS")
    print(f"{'='*70}\n")
    
    instruction_manager = instructions_module.InstructionManager(str(project_path))
    instructions = instruction_manager.load_instructions()
    
    if instructions:
        print(f"Found {len(instructions)} instruction files:")
        for instruction in instructions:
            print(f"  - {instruction.path} ({instruction.type}, priority: {instruction.priority})")
        
        # Show guidelines
        guidelines = instruction_manager.get_project_specific_guidelines()
        if guidelines:
            print(f"\nExtracted Guidelines ({len(guidelines)}):")
            for guideline in guidelines[:5]:
                print(f"  - {guideline}")
    else:
        print("No instruction files found")
    
    # Show configuration
    print(f"\n{'='*70}")
    print("CONFIGURATION FILES")
    print(f"{'='*70}\n")
    
    config_parser = config_parser_module.ConfigParser(str(project_path))
    configs = config_parser.parse_all_configs()
    
    if configs:
        print(f"Found {len(configs)} configuration files:")
        for filename, config in configs.items():
            print(f"  - {filename} ({config.type})")
        
        # Show dependencies
        dependencies = config_parser.get_dependencies()
        if dependencies:
            print(f"\nDependencies:")
            for filename, deps in dependencies.items():
                print(f"  {filename}:")
                for dep in deps[:5]:
                    print(f"    - {dep}")
                if len(deps) > 5:
                    print(f"    ... and {len(deps) - 5} more")
    else:
        print("No configuration files found")
    
    # Show Git status
    print(f"\n{'='*70}")
    print("GIT STATUS")
    print(f"{'='*70}\n")
    
    git = git_module.GitIntegration(str(project_path))
    if git.check_git_repo():
        status = git.get_git_status()
        if status:
            print(f"Branch: {status.branch}")
            print(f"Clean: {status.is_clean}")
            
            if not status.is_clean:
                print(f"\nChanges:")
                print(f"  Modified: {len(status.modified_files)}")
                print(f"  Added: {len(status.added_files)}")
                print(f"  Deleted: {len(status.deleted_files)}")
                print(f"  Untracked: {len(status.untracked_files)}")
                print(f"  Staged: {len(status.staged_files)}")
            
            # Show recent commits
            commits = git.get_commit_history(3)
            if commits:
                print(f"\nRecent Commits:")
                for commit in commits:
                    print(f"  - {commit['hash'][:8]}: {commit['message']} ({commit['date']})")
    else:
        print("Not a Git repository")
    
    # Build context if requested
    if getattr(args, 'build_context', False):
        print(f"\n{'='*70}")
        print("AI CONTEXT BUILDER")
        print(f"{'='*70}\n")
        
        builder = builder_module.ContextBuilder(str(project_path))
        context = builder.build_context(
            query=getattr(args, 'query', None),
            strategy=getattr(args, 'strategy', 'structure'),
            max_files=getattr(args, 'max_files', 5),
            max_tokens=getattr(args, 'max_tokens', 2000)
        )
        
        print(f"Context Strategy: {context.metadata['strategy']}")
        print(f"Files Included: {len(context.files)}")
        print(f"Estimated Tokens: {context.metadata['estimated_tokens']}")
        
        if context.files:
            print(f"\nContext Files:")
            for file in context.files:
                print(f"  - {file.path} ({file.reason})")
        
        # Show formatted context
        if getattr(args, 'show_context', False):
            formatted = builder.format_context_for_prompt(context)
            print(f"\n{'='*70}")
            print("FORMATTED CONTEXT FOR PROMPT")
            print(f"{'='*70}\n")
            print(formatted)
    
    print(f"\n{'='*70}")
    print("Analysis complete")
    print(f"{'='*70}\n")
    
    return 0


def init_project(args):
    """
    Initialize project for AI understanding.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    project_dir = getattr(args, 'directory', '.')
    project_path = Path(project_dir).resolve()
    
    print(f"Initializing project for AI understanding: {project_path}")
    
    # Create .local-ai directory
    local_ai_dir = project_path / '.local-ai'
    local_ai_dir.mkdir(parents=True, exist_ok=True)
    
    # Create instructions file
    instructions_file = local_ai_dir / 'instructions.md'
    
    if instructions_file.exists() and not getattr(args, 'force', False):
        print(f"Instructions file already exists: {instructions_file}")
        print("Use --force to overwrite")
        return 0
    
    # Default instructions template
    default_instructions = """# Project Instructions for AI Assistant

## Project Overview
Describe your project here, including its purpose and main functionality.

## Development Guidelines
- Add any specific coding guidelines for this project
- Mention preferred coding standards or conventions
- Note any specific requirements or constraints

## Architecture
- Describe the overall architecture
- Explain the main components and their relationships
- Include any architectural patterns used

## Important Files
- List important files and their purposes
- Highlight configuration files and their roles
- Note any critical source files

## Testing
- Describe the testing approach
- Mention any testing frameworks used
- Explain how to run tests

## Build and Deployment
- Explain the build process
- Describe deployment procedures
- Include any environment-specific instructions

## Notes
- Add any additional notes that would help the AI understand your project
- Include any project-specific conventions or practices
"""

    instructions_file.write_text(default_instructions)
    
    print(f"Created instructions file: {instructions_file}")
    print("Edit this file to provide project-specific instructions for the AI assistant")
    
    return 0