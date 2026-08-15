"""
Local AI Platform - File Search and Indexing
Search and index files for project context.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass
import re
import json
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FileIndex:
    """Index of files in a project."""
    project_root: str
    files: Dict[str, Dict[str, Any]]
    by_extension: Dict[str, List[str]]
    by_directory: Dict[str, List[str]]
    last_updated: str


@dataclass
class SearchResult:
    """Result from file search."""
    file_path: str
    match_type: str  # 'name', 'content', 'both'
    matches: List[str]
    relevance_score: float


class FileSearcher:
    """Search and index files in a project."""
    
    def __init__(self, project_root: str):
        """
        Initialize file searcher.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root).resolve()
        self.index: Optional[FileIndex] = None
        self.common_ignore_patterns = [
            '__pycache__', 'node_modules', '.git', '.venv', 'venv',
            'target', 'build', 'dist', '.next', '.nuxt',
            '*.pyc', '*.pyo', '*.pyd', '*.so', '*.dll',
            '*.exe', '*.bin', '*.class', '*.jar',
            '*.log', '*.tmp', '*.swp', '*.bak'
        ]
    
    def build_index(self, force_rebuild: bool = False) -> FileIndex:
        """
        Build file index for the project.
        
        Args:
            force_rebuild: Force rebuild even if index exists
            
        Returns:
            FileIndex
        """
        logger.info(f"Building file index for: {self.project_root}")
        
        files = {}
        by_extension = {}
        by_directory = {}
        
        # Walk through project directory
        for file_path in self.project_root.rglob('*'):
            if not file_path.is_file():
                continue
            
            # Skip ignored patterns
            if self._should_ignore(file_path):
                continue
            
            # Get relative path
            rel_path = file_path.relative_to(self.project_root)
            rel_path_str = str(rel_path)
            
            # File information
            file_info = {
                'path': rel_path_str,
                'absolute_path': str(file_path),
                'size': file_path.stat().st_size,
                'extension': file_path.suffix,
                'directory': str(rel_path.parent),
                'name': file_path.name
            }
            
            files[rel_path_str] = file_info
            
            # Index by extension
            ext = file_path.suffix
            if ext not in by_extension:
                by_extension[ext] = []
            by_extension[ext].append(rel_path_str)
            
            # Index by directory
            dir_path = str(rel_path.parent)
            if dir_path not in by_directory:
                by_directory[dir_path] = []
            by_directory[dir_path].append(rel_path_str)
        
        # Create index
        self.index = FileIndex(
            project_root=str(self.project_root),
            files=files,
            by_extension=by_extension,
            by_directory=by_directory,
            last_updated=None  # Could add timestamp
        )
        
        logger.info(f"Indexed {len(files)} files")
        return self.index
    
    def search_by_name(self, pattern: str, case_sensitive: bool = False) -> List[SearchResult]:
        """
        Search files by name pattern.
        
        Args:
            pattern: Search pattern (supports wildcards)
            case_sensitive: Whether search is case sensitive
            
        Returns:
            List of SearchResult
        """
        if not self.index:
            self.build_index()
        
        results = []
        
        # Convert pattern to regex
        regex_pattern = pattern.replace('*', '.*').replace('?', '.')
        if not case_sensitive:
            regex_pattern = regex_pattern.lower()
        
        for file_path, file_info in self.index.files.items():
            name = file_info['name']
            search_name = name if case_sensitive else name.lower()
            
            if re.search(regex_pattern, search_name):
                results.append(SearchResult(
                    file_path=file_path,
                    match_type='name',
                    matches=[name],
                    relevance_score=1.0
                ))
        
        return results
    
    def search_by_extension(self, extensions: List[str]) -> List[SearchResult]:
        """
        Search files by extension.
        
        Args:
            extensions: List of file extensions (e.g., ['.py', '.js'])
            
        Returns:
            List of SearchResult
        """
        if not self.index:
            self.build_index()
        
        results = []
        
        for ext in extensions:
            if ext in self.index.by_extension:
                for file_path in self.index.by_extension[ext]:
                    results.append(SearchResult(
                        file_path=file_path,
                        match_type='extension',
                        matches=[ext],
                        relevance_score=1.0
                    ))
        
        return results
    
    def search_by_content(
        self,
        pattern: str,
        extensions: Optional[List[str]] = None,
        max_results: int = 50
    ) -> List[SearchResult]:
        """
        Search files by content pattern.
        
        Args:
            pattern: Content pattern to search for
            extensions: Optional file extensions to limit search
            max_results: Maximum number of results
            
        Returns:
            List of SearchResult
        """
        if not self.index:
            self.build_index()
        
        results = []
        
        # Limit search by extension if specified
        files_to_search = self.index.files
        if extensions:
            files_to_search = {
                path: info for path, info in self.index.files.items()
                if info['extension'] in extensions
            }
        
        # Search file contents
        for file_path, file_info in files_to_search.items():
            try:
                # Skip large files
                if file_info['size'] > 1024 * 1024:  # 1MB limit
                    continue
                
                with open(file_info['absolute_path'], 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Search for pattern
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    results.append(SearchResult(
                        file_path=file_path,
                        match_type='content',
                        matches=matches[:10],  # Limit matches
                        relevance_score=len(matches)
                    ))
                
            except Exception as e:
                logger.debug(f"Error searching {file_path}: {e}")
                continue
        
        # Sort by relevance and limit results
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:max_results]
    
    def get_files_in_directory(self, directory: str) -> List[str]:
        """
        Get all files in a directory.
        
        Args:
            directory: Directory path (relative to project root)
            
        Returns:
            List of file paths
        """
        if not self.index:
            self.build_index()
        
        # Normalize directory path
        dir_path = directory.replace('\\', '/')
        if not dir_path.endswith('/'):
            dir_path += '/'
        
        # Get files in directory
        files = []
        for file_path, file_info in self.index.files.items():
            if file_info['directory'].startswith(dir_path):
                files.append(file_path)
        
        return files
    
    def get_file_content(self, file_path: str, max_lines: int = 100) -> Optional[str]:
        """
        Get content of a file.
        
        Args:
            file_path: Path to file (relative to project root)
            max_lines: Maximum lines to return
            
        Returns:
            File content or None if error
        """
        if not self.index:
            self.build_index()
        
        if file_path not in self.index.files:
            return None
        
        file_info = self.index.files[file_path]
        abs_path = file_info['absolute_path']
        
        try:
            with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            if max_lines:
                lines = lines[:max_lines]
            
            return ''.join(lines)
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    def _should_ignore(self, file_path: Path) -> bool:
        """
        Check if file should be ignored.
        
        Args:
            file_path: File path to check
            
        Returns:
            True if should ignore
        """
        rel_path = file_path.relative_to(self.project_root)
        rel_path_str = str(rel_path)
        
        # Check ignore patterns
        for pattern in self.common_ignore_patterns:
            if pattern.startswith('*'):
                # Extension pattern
                if rel_path_str.endswith(pattern[1:]):
                    return True
            elif pattern in rel_path_str:
                # Directory pattern
                return True
        
        return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the file index.
        
        Returns:
            Dictionary with index statistics
        """
        if not self.index:
            self.build_index()
        
        return {
            'total_files': len(self.index.files),
            'total_extensions': len(self.index.by_extension),
            'total_directories': len(self.index.by_directory),
            'project_root': self.index.project_root,
            'last_updated': self.index.last_updated
        }


# Global file searcher cache
_file_searchers: Dict[str, FileSearcher] = {}


def get_file_searcher(project_root: str) -> FileSearcher:
    """
    Get file searcher for a project.
    
    Args:
        project_root: Project root directory
        
    Returns:
        FileSearcher instance
    """
    project_root = str(Path(project_root).resolve())
    
    if project_root not in _file_searchers:
        _file_searchers[project_root] = FileSearcher(project_root)
    
    return _file_searchers[project_root]


# Example usage and testing
if __name__ == "__main__":
    # Test file search
    print("Testing File Search and Indexing...")
    
    # Test on current directory
    current_dir = Path.cwd()
    searcher = get_file_searcher(str(current_dir))
    
    # Build index
    print(f"\nBuilding index for: {current_dir}")
    index = searcher.build_index()
    
    # Get stats
    stats = searcher.get_index_stats()
    print(f"\nIndex Statistics:")
    print(f"  Total files: {stats['total_files']}")
    print(f"  Extensions: {stats['total_extensions']}")
    print(f"  Directories: {stats['total_directories']}")
    
    # Search by name
    print(f"\nSearching for Python files...")
    py_files = searcher.search_by_extension(['.py'])
    print(f"  Found {len(py_files)} Python files")
    for result in py_files[:5]:
        print(f"    - {result.file_path}")
    
    # Search by content
    print(f"\nSearching for 'import' in files...")
    import_results = searcher.search_by_content('import', extensions=['.py'], max_results=5)
    print(f"  Found {len(import_results)} files with 'import'")
    for result in import_results:
        print(f"    - {result.file_path} ({result.relevance_score} matches)")
    
    # Get files in directory
    print(f"\nFiles in 'agent' directory:")
    agent_files = searcher.get_files_in_directory('agent')
    for file_path in agent_files[:5]:
        print(f"    - {file_path}")
    
    print("\nFile search test completed!")
