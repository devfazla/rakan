"""
Local AI Platform - Git Integration
Provides Git status, diff, and change context for projects.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging
import subprocess

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class GitStatus:
    """Git status information."""
    branch: str
    is_clean: bool
    modified_files: List[str]
    added_files: List[str]
    deleted_files: List[str]
    untracked_files: List[str]
    staged_files: List[str]


@dataclass
class GitDiff:
    """Git diff information."""
    file_path: str
    changes: str
    added_lines: int
    removed_lines: int
    is_staged: bool


class GitIntegration:
    """Git integration for project context."""
    
    def __init__(self, project_root: str):
        """
        Initialize Git integration.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root).resolve()
        self.git_dir = self.project_root / '.git'
        self.is_git_repo = self.git_dir.exists()
    
    def check_git_repo(self) -> bool:
        """
        Check if project is a Git repository.
        
        Returns:
            True if Git repository, False otherwise
        """
        return self.is_git_repo
    
    def get_git_status(self) -> Optional[GitStatus]:
        """
        Get Git status.
        
        Returns:
            GitStatus or None if not a Git repo
        """
        if not self.is_git_repo:
            return None
        
        try:
            # Get current branch
            branch = self._run_git_command(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
            branch = branch.strip() if branch else 'unknown'
            
            # Get status
            status_output = self._run_git_command(['git', 'status', '--porcelain'])
            
            modified_files = []
            added_files = []
            deleted_files = []
            untracked_files = []
            staged_files = []
            
            for line in status_output.split('\n'):
                if not line:
                    continue
                
                status_code = line[:2]
                file_path = line[3:]
                
                # Parse status codes
                if status_code.startswith('M'):
                    modified_files.append(file_path)
                elif status_code.startswith('A'):
                    added_files.append(file_path)
                elif status_code.startswith('D'):
                    deleted_files.append(file_path)
                elif status_code.startswith('??'):
                    untracked_files.append(file_path)
                
                # Check if staged (first character is not space)
                if status_code[0] in ['M', 'A', 'D']:
                    staged_files.append(file_path)
            
            is_clean = not (modified_files or added_files or deleted_files or untracked_files)
            
            return GitStatus(
                branch=branch,
                is_clean=is_clean,
                modified_files=modified_files,
                added_files=added_files,
                deleted_files=deleted_files,
                untracked_files=untracked_files,
                staged_files=staged_files
            )
            
        except Exception as e:
            logger.error(f"Failed to get Git status: {e}")
            return None
    
    def get_file_diff(self, file_path: str, staged: bool = False) -> Optional[GitDiff]:
        """
        Get diff for a specific file.
        
        Args:
            file_path: Path to file (relative to project root)
            staged: Whether to get staged diff
            
        Returns:
            GitDiff or None if error
        """
        if not self.is_git_repo:
            return None
        
        try:
            # Build git diff command
            command = ['git', 'diff']
            if staged:
                command.append('--staged')
            command.append(file_path)
            
            diff_output = self._run_git_command(command)
            
            # Count added and removed lines
            added_lines = diff_output.count('\n+') - diff_output.count('\n+++')
            removed_lines = diff_output.count('\n-') - diff_output.count('\n---')
            
            return GitDiff(
                file_path=file_path,
                changes=diff_output,
                added_lines=max(0, added_lines),
                removed_lines=max(0, removed_lines),
                is_staged=staged
            )
            
        except Exception as e:
            logger.error(f"Failed to get diff for {file_path}: {e}")
            return None
    
    def get_all_diffs(self, max_files: int = 10) -> List[GitDiff]:
        """
        Get diffs for all changed files.
        
        Args:
            max_files: Maximum number of files to get diffs for
            
        Returns:
            List of GitDiff objects
        """
        if not self.is_git_repo:
            return []
        
        status = self.get_git_status()
        if not status:
            return []
        
        diffs = []
        
        # Get diffs for modified and added files
        for file_path in status.modified_files + status.added_files:
            if len(diffs) >= max_files:
                break
            
            diff = self.get_file_diff(file_path)
            if diff:
                diffs.append(diff)
        
        return diffs
    
    def get_commit_history(self, max_commits: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent commit history.
        
        Args:
            max_commits: Maximum number of commits to retrieve
            
        Returns:
            List of commit information dictionaries
        """
        if not self.is_git_repo:
            return []
        
        try:
            command = ['git', 'log', f'-{max_commits}', '--pretty=format:%H|%an|%ad|%s', '--date=short']
            output = self._run_git_command(command)
            
            commits = []
            for line in output.split('\n'):
                if not line:
                    continue
                
                parts = line.split('|', 3)
                if len(parts) == 4:
                    commits.append({
                        'hash': parts[0],
                        'author': parts[1],
                        'date': parts[2],
                        'message': parts[3]
                    })
            
            return commits
            
        except Exception as e:
            logger.error(f"Failed to get commit history: {e}")
            return []
    
    def get_current_commit(self) -> Optional[str]:
        """
        Get current commit hash.
        
        Returns:
            Commit hash or None if error
        """
        if not self.is_git_repo:
            return None
        
        try:
            commit_hash = self._run_git_command(['git', 'rev-parse', 'HEAD'])
            return commit_hash.strip() if commit_hash else None
        except Exception as e:
            logger.error(f"Failed to get current commit: {e}")
            return None
    
    def get_changed_files_summary(self) -> Dict[str, Any]:
        """
        Get summary of changed files.
        
        Returns:
            Dictionary with change summary
        """
        status = self.get_git_status()
        if not status:
            return {}
        
        return {
            'branch': status.branch,
            'is_clean': status.is_clean,
            'total_changes': len(status.modified_files) + len(status.added_files) + len(status.deleted_files),
            'modified_count': len(status.modified_files),
            'added_count': len(status.added_files),
            'deleted_count': len(status.deleted_files),
            'untracked_count': len(status.untracked_files),
            'staged_count': len(status.staged_files)
        }
    
    def _run_git_command(self, command: List[str]) -> str:
        """
        Run a Git command and return output.
        
        Args:
            command: Git command to run
            
        Returns:
            Command output
        """
        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.warning(f"Git command failed: {' '.join(command)}")
                return ""
            
            return result.stdout
            
        except subprocess.TimeoutExpired:
            logger.error(f"Git command timed out: {' '.join(command)}")
            return ""
        except Exception as e:
            logger.error(f"Failed to run Git command: {e}")
            return ""
    
    def format_git_context(self) -> str:
        """
        Format Git context for prompt injection.
        
        Returns:
            Formatted Git context string
        """
        if not self.is_git_repo:
            return "This project is not a Git repository."
        
        status = self.get_git_status()
        if not status:
            return "Could not retrieve Git status."
        
        lines = []
        
        lines.append("## Git Status")
        lines.append(f"Branch: {status.branch}")
        lines.append(f"Clean: {status.is_clean}")
        
        if not status.is_clean:
            lines.append("\n### Changes:")
            
            if status.modified_files:
                lines.append(f"Modified ({len(status.modified_files)}):")
                for file in status.modified_files[:5]:
                    lines.append(f"  - {file}")
                if len(status.modified_files) > 5:
                    lines.append(f"  ... and {len(status.modified_files) - 5} more")
            
            if status.added_files:
                lines.append(f"Added ({len(status.added_files)}):")
                for file in status.added_files[:5]:
                    lines.append(f"  - {file}")
                if len(status.added_files) > 5:
                    lines.append(f"  ... and {len(status.added_files) - 5} more")
            
            if status.deleted_files:
                lines.append(f"Deleted ({len(status.deleted_files)}):")
                for file in status.deleted_files[:5]:
                    lines.append(f"  - {file}")
            
            if status.staged_files:
                lines.append(f"Staged ({len(status.staged_files)}):")
                for file in status.staged_files[:5]:
                    lines.append(f"  - {file}")
        
        # Recent commits
        commits = self.get_commit_history(3)
        if commits:
            lines.append("\n### Recent Commits:")
            for commit in commits:
                lines.append(f"- {commit['hash'][:8]}: {commit['message']} ({commit['date']})")
        
        return "\n".join(lines)


# Global Git integration cache
_git_integrations: Dict[str, GitIntegration] = {}


def get_git_integration(project_root: str) -> GitIntegration:
    """
    Get Git integration for a project.
    
    Args:
        project_root: Project root directory
        
    Returns:
        GitIntegration instance
    """
    project_root = str(Path(project_root).resolve())
    
    if project_root not in _git_integrations:
        _git_integrations[project_root] = GitIntegration(project_root)
    
    return _git_integrations[project_root]


# Example usage and testing
if __name__ == "__main__":
    # Test Git integration
    print("Testing Git Integration...")
    
    # Test on current directory
    current_dir = Path.cwd()
    git = get_git_integration(str(current_dir))
    
    # Check if Git repo
    is_repo = git.check_git_repo()
    print(f"\nIs Git repository: {is_repo}")
    
    if is_repo:
        # Get status
        status = git.get_git_status()
        if status:
            print(f"\nGit Status:")
            print(f"  Branch: {status.branch}")
            print(f"  Clean: {status.is_clean}")
            print(f"  Modified: {len(status.modified_files)}")
            print(f"  Added: {len(status.added_files)}")
            print(f"  Deleted: {len(status.deleted_files)}")
            print(f"  Untracked: {len(status.untracked_files)}")
            print(f"  Staged: {len(status.staged_files)}")
        
        # Get changed files summary
        summary = git.get_changed_files_summary()
        print(f"\nChanges summary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
        
        # Get commit history
        commits = git.get_commit_history(3)
        print(f"\nRecent commits:")
        for commit in commits:
            print(f"  - {commit['hash'][:8]}: {commit['message']}")
        
        # Format context
        print(f"\nFormatted Git context:")
        context = git.format_git_context()
        print(context[:500] + "...")
        
        # Get diffs for changed files
        if status and status.modified_files:
            print(f"\nGetting diff for first modified file...")
            diff = git.get_file_diff(status.modified_files[0])
            if diff:
                print(f"  File: {diff.file_path}")
                print(f"  Added lines: {diff.added_lines}")
                print(f"  Removed lines: {diff.removed_lines}")
                print(f"  Changes preview: {diff.changes[:200]}...")
    else:
        print("Not a Git repository, skipping Git-specific tests")
    
    print("\nGit integration test completed!")
