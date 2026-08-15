"""
Local AI Platform - Tool Execution System
Safe tool execution with permission management.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum
import logging
import subprocess
import json

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ToolPermission(Enum):
    """Permission levels for tool execution."""
    ALLOW = "allow"
    DENY = "deny"
    CONFIRM = "confirm"
    AUTO = "auto"


@dataclass
class ToolResult:
    """Result from tool execution."""
    success: bool
    output: str
    error: Optional[str]
    tool_name: str
    execution_time: float
    data: Optional[Dict[str, Any]] = None


@dataclass
class Tool:
    """Tool definition."""
    name: str
    description: str
    permission: ToolPermission
    dangerous: bool
    parameters: Dict[str, Any]
    execute_func: Callable


class ToolRegistry:
    """Registry for available tools."""
    
    def __init__(self):
        """Initialize tool registry."""
        self.tools: Dict[str, Tool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default tools."""
        # Filesystem tools
        self.register_tool(Tool(
            name="read_file",
            description="Read contents of a file",
            permission=ToolPermission.ALLOW,
            dangerous=False,
            parameters={"file_path": "str"},
            execute_func=self._read_file
        ))
        
        self.register_tool(Tool(
            name="write_file",
            description="Write content to a file",
            permission=ToolPermission.CONFIRM,
            dangerous=True,
            parameters={"file_path": "str", "content": "str"},
            execute_func=self._write_file
        ))
        
        self.register_tool(Tool(
            name="list_directory",
            description="List contents of a directory",
            permission=ToolPermission.ALLOW,
            dangerous=False,
            parameters={"directory": "str"},
            execute_func=self._list_directory
        ))
        
        self.register_tool(Tool(
            name="search_files",
            description="Search for files by pattern",
            permission=ToolPermission.ALLOW,
            dangerous=False,
            parameters={"pattern": "str", "directory": "str"},
            execute_func=self._search_files
        ))
        
        # Command execution tools
        self.register_tool(Tool(
            name="execute_command",
            description="Execute a shell command",
            permission=ToolPermission.CONFIRM,
            dangerous=True,
            parameters={"command": "str"},
            execute_func=self._execute_command
        ))
        
        # Git tools
        self.register_tool(Tool(
            name="git_status",
            description="Get git repository status",
            permission=ToolPermission.ALLOW,
            dangerous=False,
            parameters={},
            execute_func=self._git_status
        ))
        
        self.register_tool(Tool(
            name="git_diff",
            description="Get git diff for changes",
            permission=ToolPermission.ALLOW,
            dangerous=False,
            parameters={"file": "str"},
            execute_func=self._git_diff
        ))
    
    def register_tool(self, tool: Tool):
        """
        Register a tool.
        
        Args:
            tool: Tool to register
        """
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """
        Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool or None if not found
        """
        return self.tools.get(name)
    
    def list_tools(self) -> List[str]:
        """
        List all available tools.
        
        Returns:
            List of tool names
        """
        return list(self.tools.keys())
    
    def get_dangerous_tools(self) -> List[str]:
        """
        List dangerous tools.
        
        Returns:
            List of dangerous tool names
        """
        return [name for name, tool in self.tools.items() if tool.dangerous]
    
    # Tool execution functions
    
    def _read_file(self, parameters: Dict[str, Any]) -> ToolResult:
        """Read file contents."""
        import time
        start_time = time.time()
        
        try:
            file_path = parameters.get("file_path")
            if not file_path:
                return ToolResult(
                    success=False,
                    output="",
                    error="Missing file_path parameter",
                    tool_name="read_file",
                    execution_time=time.time() - start_time
                )
            
            path = Path(file_path)
            if not path.exists():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"File not found: {file_path}",
                    tool_name="read_file",
                    execution_time=time.time() - start_time
                )
            
            content = path.read_text(encoding='utf-8', errors='ignore')
            
            return ToolResult(
                success=True,
                output=content,
                error=None,
                tool_name="read_file",
                execution_time=time.time() - start_time,
                data={"file_size": len(content)}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e),
                tool_name="read_file",
                execution_time=time.time() - start_time
            )
    
    def _write_file(self, parameters: Dict[str, Any]) -> ToolResult:
        """Write content to a file."""
        import time
        start_time = time.time()
        
        try:
            file_path = parameters.get("file_path")
            content = parameters.get("content", "")
            
            if not file_path:
                return ToolResult(
                    success=False,
                    output="",
                    error="Missing file_path parameter",
                    tool_name="write_file",
                    execution_time=time.time() - start_time
                )
            
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
            
            return ToolResult(
                success=True,
                output=f"Successfully wrote {len(content)} characters to {file_path}",
                error=None,
                tool_name="write_file",
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e),
                tool_name="write_file",
                execution_time=time.time() - start_time
            )
    
    def _list_directory(self, parameters: Dict[str, Any]) -> ToolResult:
        """List directory contents."""
        import time
        start_time = time.time()
        
        try:
            directory = parameters.get("directory", ".")
            path = Path(directory)
            
            if not path.exists():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Directory not found: {directory}",
                    tool_name="list_directory",
                    execution_time=time.time() - start_time
                )
            
            if not path.is_dir():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Not a directory: {directory}",
                    tool_name="list_directory",
                    execution_time=time.time() - start_time
                )
            
            items = []
            for item in path.iterdir():
                item_type = "directory" if item.is_dir() else "file"
                items.append(f"{item.name} ({item_type})")
            
            output = "\n".join(items)
            
            return ToolResult(
                success=True,
                output=output,
                error=None,
                tool_name="list_directory",
                execution_time=time.time() - start_time,
                data={"item_count": len(items)}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e),
                tool_name="list_directory",
                execution_time=time.time() - start_time
            )
    
    def _search_files(self, parameters: Dict[str, Any]) -> ToolResult:
        """Search for files by pattern."""
        import time
        start_time = time.time()
        
        try:
            pattern = parameters.get("pattern", "*")
            directory = parameters.get("directory", ".")
            
            path = Path(directory)
            if not path.exists():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Directory not found: {directory}",
                    tool_name="search_files",
                    execution_time=time.time() - start_time
                )
            
            matches = list(path.rglob(pattern))
            output = "\n".join(str(m) for m in matches[:50])  # Limit to 50 results
            
            return ToolResult(
                success=True,
                output=output,
                error=None,
                tool_name="search_files",
                execution_time=time.time() - start_time,
                data={"match_count": len(matches)}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e),
                tool_name="search_files",
                execution_time=time.time() - start_time
            )
    
    def _execute_command(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute a shell command."""
        import time
        start_time = time.time()
        
        try:
            command = parameters.get("command")
            if not command:
                return ToolResult(
                    success=False,
                    output="",
                    error="Missing command parameter",
                    tool_name="execute_command",
                    execution_time=time.time() - start_time
                )
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\nErrors:\n{result.stderr}"
            
            return ToolResult(
                success=result.returncode == 0,
                output=output,
                error=None if result.returncode == 0 else f"Command failed with exit code {result.returncode}",
                tool_name="execute_command",
                execution_time=time.time() - start_time,
                data={"exit_code": result.returncode}
            )
            
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output="",
                error="Command timed out",
                tool_name="execute_command",
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e),
                tool_name="execute_command",
                execution_time=time.time() - start_time
            )
    
    def _git_status(self, parameters: Dict[str, Any]) -> ToolResult:
        """Get git status."""
        import time
        start_time = time.time()
        
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return ToolResult(
                success=True,
                output=result.stdout if result.returncode == 0 else "Not a git repository",
                error=None,
                tool_name="git_status",
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e),
                tool_name="git_status",
                execution_time=time.time() - start_time
            )
    
    def _git_diff(self, parameters: Dict[str, Any]) -> ToolResult:
        """Get git diff."""
        import time
        start_time = time.time()
        
        try:
            file = parameters.get("file", "")
            command = ["git", "diff"]
            if file:
                command.append(file)
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return ToolResult(
                success=True,
                output=result.stdout if result.returncode == 0 else "Not a git repository",
                error=None,
                tool_name="git_diff",
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e),
                tool_name="git_diff",
                execution_time=time.time() - start_time
            )


class ToolExecutor:
    """Executes tools with permission checking."""
    
    def __init__(self, registry: Optional[ToolRegistry] = None):
        """
        Initialize tool executor.
        
        Args:
            registry: Tool registry to use
        """
        self.registry = registry or ToolRegistry()
        self.permission_callback: Optional[Callable] = None
    
    def set_permission_callback(self, callback: Callable):
        """
        Set callback for permission requests.
        
        Args:
            callback: Function to call for permission requests
        """
        self.permission_callback = callback
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolResult:
        """
        Execute a tool with permission checking.
        
        Args:
            tool_name: Name of tool to execute
            parameters: Tool parameters
            
        Returns:
            ToolResult
        """
        tool = self.registry.get_tool(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                output="",
                error=f"Tool not found: {tool_name}",
                tool_name=tool_name,
                execution_time=0.0
            )
        
        # Check permission
        if tool.permission == ToolPermission.DENY:
            return ToolResult(
                success=False,
                output="",
                error=f"Tool execution denied: {tool_name}",
                tool_name=tool_name,
                execution_time=0.0
            )
        
        # Request confirmation if needed
        if tool.permission == ToolPermission.CONFIRM:
            if self.permission_callback:
                approved = self.permission_callback(tool_name, parameters)
                if not approved:
                    return ToolResult(
                        success=False,
                        output="",
                        error=f"Tool execution not approved: {tool_name}",
                        tool_name=tool_name,
                        execution_time=0.0
                    )
            else:
                # No callback set, deny by default for dangerous tools
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Tool execution requires approval: {tool_name}. Set permission callback.",
                    tool_name=tool_name,
                    execution_time=0.0
                )
        
        # Execute tool
        return tool.execute_func(parameters)


# Global tool executor instance
_tool_executor = None


def get_tool_executor() -> ToolExecutor:
    """
    Get global tool executor instance.
    
    Returns:
        ToolExecutor instance
    """
    global _tool_executor
    if _tool_executor is None:
        _tool_executor = ToolExecutor()
    return _tool_executor


# Example usage and testing
if __name__ == "__main__":
    # Test tool execution system
    print("Testing Tool Execution System...")
    
    executor = get_tool_executor()
    
    # List available tools
    print(f"\nAvailable tools: {executor.registry.list_tools()}")
    
    # Test safe tool
    print(f"\nTesting list_directory tool...")
    result = executor.execute_tool("list_directory", {"directory": "."})
    print(f"Success: {result.success}")
    print(f"Output: {result.output[:200]}...")
    
    # Test file read
    print(f"\nTesting read_file tool...")
    result = executor.execute_tool("read_file", {"file_path": "README.md"})
    print(f"Success: {result.success}")
    print(f"Output: {result.output[:200]}...")
    
    # Test dangerous tool (will be denied without callback)
    print(f"\nTesting write_file tool (no callback)...")
    result = executor.execute_tool("write_file", {"file_path": "test.txt", "content": "test"})
    print(f"Success: {result.success}")
    print(f"Error: {result.error}")
    
    print("\nTool execution system test completed!")
