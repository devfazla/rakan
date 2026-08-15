"""
Local AI Platform - Agent Core
Basic agent loop and planning system.
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
class AgentTask:
    """Task for the agent to execute."""
    task_id: str
    description: str
    tool_calls: List[Dict[str, Any]]
    status: str  # "pending", "in_progress", "completed", "failed"
    result: Optional[Any] = None


@dataclass
class AgentPlan:
    """Plan for task execution."""
    tasks: List[AgentTask]
    reasoning: str
    estimated_steps: int


class Agent:
    """Basic agent for task execution."""
    
    def __init__(self, tool_executor, permission_manager):
        """
        Initialize agent.
        
        Args:
            tool_executor: ToolExecutor instance
            permission_manager: PermissionManager instance
        """
        self.tool_executor = tool_executor
        self.permission_manager = permission_manager
        self.current_plan: Optional[AgentPlan] = None
        self.context: Dict[str, Any] = {}
        self.memory: List[Dict[str, Any]] = []
    
    def set_context(self, context: Dict[str, Any]):
        """
        Set agent context.
        
        Args:
            context: Context information
        """
        self.context = context
        logger.info(f"Agent context updated with {len(context)} keys")
    
    def add_to_memory(self, item: Dict[str, Any]):
        """
        Add item to agent memory.
        
        Args:
            item: Item to remember
        """
        self.memory.append(item)
        logger.info(f"Added item to memory (total: {len(self.memory)})")
    
    def plan_task(self, task_description: str) -> AgentPlan:
        """
        Create a plan for executing a task.
        
        Args:
            task_description: Description of task to accomplish
            
        Returns:
            AgentPlan
        """
        logger.info(f"Planning task: {task_description}")
        
        # Simple planning - in real implementation, this would use the LLM
        # For now, create a basic plan based on task description
        
        tasks = []
        
        # Analyze task and create tool calls
        if "read" in task_description.lower() or "file" in task_description.lower():
            tasks.append(AgentTask(
                task_id="read",
                description="Read file",
                tool_calls=[{"tool": "read_file", "parameters": {"file_path": "README.md"}}],
                status="pending"
            ))
        
        if "list" in task_description.lower() or "directory" in task_description.lower():
            tasks.append(AgentTask(
                task_id="list",
                description="List directory",
                tool_calls=[{"tool": "list_directory", "parameters": {"directory": "."}}],
                status="pending"
            ))
        
        if "git" in task_description.lower() or "status" in task_description.lower():
            tasks.append(AgentTask(
                task_id="git_status",
                description="Get git status",
                tool_calls=[{"tool": "git_status", "parameters": {}}],
                status="pending"
            ))
        
        # Create plan
        plan = AgentPlan(
            tasks=tasks,
            reasoning=f"Analyzing task: {task_description}. Breaking down into {len(tasks)} steps.",
            estimated_steps=len(tasks)
        )
        
        self.current_plan = plan
        return plan
    
    def execute_plan(self, plan: AgentPlan) -> Dict[str, Any]:
        """
        Execute a plan.
        
        Args:
            plan: AgentPlan to execute
            
        Returns:
            Execution results
        """
        logger.info(f"Executing plan with {len(plan.tasks)} tasks")
        
        results = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "task_results": []
        }
        
        for task in plan.tasks:
            task.status = "in_progress"
            
            for tool_call in task.tool_calls:
                tool_name = tool_call["tool"]
                parameters = tool_call["parameters"]
                
                # Check permission
                allowed, reason = self.permission_manager.check_permission(tool_name, parameters)
                
                if not allowed:
                    logger.warning(f"Tool execution denied: {tool_name} - {reason}")
                    self.permission_manager.log_operation(tool_name, parameters, False)
                    task.status = "failed"
                    results["tasks_failed"] += 1
                    results["task_results"].append({
                        "task": task.task_id,
                        "tool": tool_name,
                        "success": False,
                        "error": reason
                    })
                    break
                
                # Execute tool
                result = self.tool_executor.execute_tool(tool_name, parameters)
                
                # Log operation
                self.permission_manager.log_operation(tool_name, parameters, True, result)
                
                # Store result
                results["task_results"].append({
                    "task": task.task_id,
                    "tool": tool_name,
                    "success": result.success,
                    "output": result.output[:500] if result.output else None,
                    "error": result.error
                })
                
                # Add to memory
                self.add_to_memory({
                    "task": task.task_id,
                    "tool": tool_name,
                    "parameters": parameters,
                    "success": result.success,
                    "timestamp": None  # Could add timestamp
                })
                
                if not result.success:
                    task.status = "failed"
                    results["tasks_failed"] += 1
                    break
            
            if task.status != "failed":
                task.status = "completed"
                results["tasks_completed"] += 1
        
        return results
    
    def process_message(self, message: str) -> str:
        """
        Process a user message and generate response.
        
        Args:
            message: User message
            
        Returns:
            Agent response
        """
        logger.info(f"Processing message: {message}")
        
        # Plan task based on message
        plan = self.plan_task(message)
        
        # Execute plan
        results = self.execute_plan(plan)
        
        # Generate response
        response = self._generate_response(plan, results)
        
        return response
    
    def _generate_response(self, plan: AgentPlan, results: Dict[str, Any]) -> str:
        """
        Generate response from plan execution results.
        
        Args:
            plan: Executed plan
            results: Execution results
            
        Returns:
            Response string
        """
        response_parts = []
        
        response_parts.append(f"I executed {len(plan.tasks)} tasks:")
        response_parts.append(f"  - Tasks completed: {results['tasks_completed']}")
        response_parts.append(f"  - Tasks failed: {results['tasks_failed']}")
        
        for task_result in results['task_results']:
            response_parts.append(f"\nTask: {task_result['task']}")
            response_parts.append(f"  Tool: {task_result['tool']}")
            response_parts.append(f"  Success: {task_result['success']}")
            if task_result['success']:
                response_parts.append(f"  Output: {task_result['output'][:200]}...")
            else:
                response_parts.append(f"  Error: {task_result['error']}")
        
        return "\n".join(response_parts)


# Global agent instance
_agent = None


def get_agent(tool_executor=None, permission_manager=None) -> Agent:
    """
    Get global agent instance.
    
    Args:
        tool_executor: Optional ToolExecutor instance
        permission_manager: Optional PermissionManager instance
        
    Returns:
        Agent instance
    """
    global _agent
    if _agent is None:
        # Import locally to avoid circular imports
        import sys
        tools_dir = Path(__file__).parent.parent / 'tools'
        sys.path.insert(0, str(tools_dir))
        
        from executor import get_tool_executor
        from permissions import get_permission_manager
        
        _agent = Agent(
            tool_executor or get_tool_executor(),
            permission_manager or get_permission_manager()
        )
    return _agent


# Example usage and testing
if __name__ == "__main__":
    # Test agent
    print("Testing Agent...")
    
    # Get agent
    agent = get_agent()
    
    # Set context
    agent.set_context({
        "project_name": "local-ai",
        "current_directory": str(Path.cwd())
    })
    
    # Process message
    print(f"\nProcessing: 'Read the README file'")
    response = agent.process_message("Read the README file")
    print(f"\nResponse:\n{response}")
    
    # Process another message
    print(f"\nProcessing: 'List directory contents'")
    response = agent.process_message("List directory contents")
    print(f"\nResponse:\n{response}")
    
    # Get memory
    print(f"\nAgent memory items: {len(agent.memory)}")
    
    print("\nAgent test completed!")
