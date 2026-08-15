"""
Local AI Platform - Context Builder
Builds relevant context from project files for AI understanding.
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
class ContextFile:
    """File included in context."""
    path: str
    content: str
    relevance_score: float
    reason: str  # Why this file was included


@dataclass
class ProjectContext:
    """Complete project context for AI."""
    project_info: Dict[str, Any]
    files: List[ContextFile]
    instructions: Optional[str]
    metadata: Dict[str, Any]


class ContextBuilder:
    """Builds context from project files and structure."""
    
    def __init__(self, project_root: str):
        """
        Initialize context builder.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root).resolve()
        
        # Import dependencies locally to avoid circular imports
        import sys
        context_dir = Path(__file__).parent
        sys.path.insert(0, str(context_dir))
        
        from detector import get_project_detector
        from searcher import get_file_searcher
        
        self.detector = get_project_detector()
        self.searcher = get_file_searcher(str(self.project_root))
        
        # Context building strategies
        self.strategies = {
            'recent': self._build_recent_context,
            'relevant': self._build_relevant_context,
            'structure': self._build_structure_context,
            'full': self._build_full_context
        }
    
    def build_context(
        self,
        query: Optional[str] = None,
        strategy: str = 'relevant',
        max_files: int = 10,
        max_tokens: int = 4000
    ) -> ProjectContext:
        """
        Build project context.
        
        Args:
            query: Optional query to guide context selection
            strategy: Context building strategy
            max_files: Maximum number of files to include
            max_tokens: Maximum tokens for context
            
        Returns:
            ProjectContext
        """
        logger.info(f"Building context with strategy: {strategy}")
        
        # Get project information
        project_info = self._get_project_info()
        
        # Build file context
        if strategy in self.strategies:
            context_files = self.strategies[strategy](query, max_files, max_tokens)
        else:
            context_files = self._build_relevant_context(query, max_files, max_tokens)
        
        # Get project instructions
        instructions = self._get_project_instructions()
        
        # Create context
        return ProjectContext(
            project_info=project_info,
            files=context_files,
            instructions=instructions,
            metadata={
                'strategy': strategy,
                'max_files': max_files,
                'max_tokens': max_tokens,
                'file_count': len(context_files),
                'estimated_tokens': self._estimate_context_tokens(context_files)
            }
        )
    
    def _get_project_info(self) -> Dict[str, Any]:
        """Get project information."""
        project_info = self.detector.detect_project(str(self.project_root))
        
        if project_info:
            return {
                'type': project_info.project_type,
                'name': project_info.name,
                'root': project_info.root_path,
                'languages': project_info.languages,
                'frameworks': project_info.frameworks,
                'build_systems': project_info.build_systems,
                'file_count': project_info.metadata['file_count']
            }
        else:
            return {
                'type': 'unknown',
                'name': self.project_root.name,
                'root': str(self.project_root),
                'languages': [],
                'frameworks': [],
                'build_systems': [],
                'file_count': 0
            }
    
    def _build_recent_context(
        self,
        query: Optional[str],
        max_files: int,
        max_tokens: int
    ) -> List[ContextFile]:
        """Build context from recently modified files."""
        # Get all files sorted by modification time
        all_files = list(self.searcher.index.files.values()) if self.searcher.index else []
        
        # Sort by modification time (requires file system access)
        files_with_time = []
        for file_info in all_files:
            try:
                file_path = Path(file_info['absolute_path'])
                mtime = file_path.stat().st_mtime
                files_with_time.append((file_info, mtime))
            except Exception:
                continue
        
        # Sort by most recent
        files_with_time.sort(key=lambda x: x[1], reverse=True)
        
        # Select top files
        context_files = []
        total_tokens = 0
        
        for file_info, _ in files_with_time[:max_files]:
            content = self.searcher.get_file_content(file_info['path'], max_lines=50)
            if content:
                tokens = len(content.split())
                if total_tokens + tokens <= max_tokens:
                    context_files.append(ContextFile(
                        path=file_info['path'],
                        content=content,
                        relevance_score=1.0,
                        reason='recently modified'
                    ))
                    total_tokens += tokens
        
        return context_files
    
    def _build_relevant_context(
        self,
        query: Optional[str],
        max_files: int,
        max_tokens: int
    ) -> List[ContextFile]:
        """Build context based on query relevance."""
        context_files = []
        
        if query:
            # Search for files matching query
            content_results = self.searcher.search_by_content(query, max_results=max_files)
            
            for result in content_results:
                content = self.searcher.get_file_content(result.file_path, max_lines=50)
                if content:
                    context_files.append(ContextFile(
                        path=result.file_path,
                        content=content,
                        relevance_score=result.relevance_score,
                        reason=f'contains "{query}"'
                    ))
        else:
            # If no query, use recent files
            return self._build_recent_context(query, max_files, max_tokens)
        
        return context_files
    
    def _build_structure_context(
        self,
        query: Optional[str],
        max_files: int,
        max_tokens: int
    ) -> List[ContextFile]:
        """Build context based on project structure."""
        context_files = []
        
        # Get important files based on project type
        project_info = self._get_project_info()
        project_type = project_info.get('type', 'generic')
        
        # Define important files by project type
        important_files = {
            'python': ['setup.py', 'requirements.txt', 'pyproject.toml', 'README.md'],
            'javascript': ['package.json', 'README.md'],
            'rust': ['Cargo.toml', 'README.md'],
            'go': ['go.mod', 'README.md'],
            'generic': ['README.md', 'LICENSE']
        }
        
        # Get important files for this project type
        files_to_include = important_files.get(project_type, important_files['generic'])
        
        for file_name in files_to_include:
            results = self.searcher.search_by_name(file_name)
            for result in results:
                content = self.searcher.get_file_content(result.file_path, max_lines=100)
                if content:
                    context_files.append(ContextFile(
                        path=result.file_path,
                        content=content,
                        relevance_score=1.0,
                        reason='important project file'
                    ))
        
        return context_files[:max_files]
    
    def _build_full_context(
        self,
        query: Optional[str],
        max_files: int,
        max_tokens: int
    ) -> List[ContextFile]:
        """Build full context with multiple strategies."""
        # Combine structure and recent context
        structure_files = self._build_structure_context(query, max_files // 2, max_tokens // 2)
        recent_files = self._build_recent_context(query, max_files // 2, max_tokens // 2)
        
        # Merge and deduplicate
        all_files = structure_files + recent_files
        seen_paths = set()
        merged_files = []
        
        for file in all_files:
            if file.path not in seen_paths:
                merged_files.append(file)
                seen_paths.add(file.path)
        
        return merged_files[:max_files]
    
    def _get_project_instructions(self) -> Optional[str]:
        """Get project-specific instructions."""
        # Look for instruction files
        instruction_files = [
            '.local-ai/instructions.md',
            '.local-ai/config.yaml',
            'docs/INSTRUCTIONS.md',
            'docs/GUIDE.md',
            'README.md'
        ]
        
        for instruction_file in instruction_files:
            try:
                content = self.searcher.get_file_content(instruction_file, max_lines=200)
                if content:
                    return content
            except Exception:
                continue
        
        return None
    
    def _estimate_context_tokens(self, context_files: List[ContextFile]) -> int:
        """Estimate total tokens in context."""
        total_tokens = 0
        for file in context_files:
            total_tokens += len(file.content.split())
        return total_tokens
    
    def format_context_for_prompt(self, context: ProjectContext) -> str:
        """
        Format context for prompt injection.
        
        Args:
            context: ProjectContext to format
            
        Returns:
            Formatted context string
        """
        lines = []
        
        # Project information
        lines.append("## Project Information")
        lines.append(f"Name: {context.project_info['name']}")
        lines.append(f"Type: {context.project_info['type']}")
        lines.append(f"Languages: {', '.join(context.project_info['languages'])}")
        lines.append(f"Frameworks: {', '.join(context.project_info['frameworks'])}")
        lines.append("")
        
        # Instructions
        if context.instructions:
            lines.append("## Project Instructions")
            lines.append(context.instructions)
            lines.append("")
        
        # File context
        if context.files:
            lines.append("## Relevant Files")
            for file in context.files:
                lines.append(f"### {file.path}")
                lines.append(f"Reason: {file.reason}")
                lines.append("```")
                lines.append(file.content)
                lines.append("```")
                lines.append("")
        
        return "\n".join(lines)


# Global context builder cache
_context_builders: Dict[str, ContextBuilder] = {}


def get_context_builder(project_root: str) -> ContextBuilder:
    """
    Get context builder for a project.
    
    Args:
        project_root: Project root directory
        
    Returns:
        ContextBuilder instance
    """
    project_root = str(Path(project_root).resolve())
    
    if project_root not in _context_builders:
        _context_builders[project_root] = ContextBuilder(project_root)
    
    return _context_builders[project_root]


# Example usage and testing
if __name__ == "__main__":
    # Test context builder
    print("Testing Context Builder...")
    
    # Test on current directory
    current_dir = Path.cwd()
    builder = get_context_builder(str(current_dir))
    
    # Build context with different strategies
    print(f"\nBuilding context with 'structure' strategy...")
    context = builder.build_context(strategy='structure', max_files=5)
    
    print(f"Project: {context.project_info['name']}")
    print(f"Type: {context.project_info['type']}")
    print(f"Files included: {len(context.files)}")
    print(f"Estimated tokens: {context.metadata['estimated_tokens']}")
    
    for file in context.files:
        print(f"  - {file.path} ({file.reason})")
    
    # Build context with query
    print(f"\nBuilding context with query 'model'...")
    context_query = builder.build_context(query='model', strategy='relevant', max_files=3)
    
    print(f"Files included: {len(context_query.files)}")
    for file in context_query.files:
        print(f"  - {file.path} ({file.reason})")
    
    # Format context for prompt
    print(f"\nFormatted context:")
    formatted = builder.format_context_for_prompt(context)
    print(formatted[:500] + "...")
    
    print("\nContext builder test completed!")
