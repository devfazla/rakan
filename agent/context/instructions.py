"""
Local AI Platform - Project Instructions
Handles project-specific instructions and configuration.
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
class InstructionFile:
    """Instruction file information."""
    path: str
    content: str
    type: str  # 'instructions', 'config', 'readme'
    priority: int  # Higher priority instructions override lower


class InstructionManager:
    """Manages project instructions and configuration."""
    
    def __init__(self, project_root: str):
        """
        Initialize instruction manager.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root).resolve()
        self.instruction_files: List[InstructionFile] = []
        
        # Define instruction file locations and priorities
        self.instruction_locations = [
            ('.local-ai/instructions.md', 'instructions', 100),
            ('.local-ai/config.yaml', 'config', 90),
            ('.local-ai/config.json', 'config', 90),
            ('docs/INSTRUCTIONS.md', 'instructions', 80),
            ('docs/GUIDE.md', 'instructions', 70),
            ('docs/CONTRIBUTING.md', 'instructions', 60),
            ('README.md', 'readme', 50),
            ('.github/CONTRIBUTING.md', 'instructions', 40),
            ('CONTRIBUTING.md', 'instructions', 30)
        ]
    
    def load_instructions(self) -> List[InstructionFile]:
        """
        Load all instruction files from the project.
        
        Returns:
            List of InstructionFile objects
        """
        self.instruction_files = []
        
        for location, file_type, priority in self.instruction_locations:
            file_path = self.project_root / location
            
            if file_path.exists() and file_path.is_file():
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    
                    instruction_file = InstructionFile(
                        path=location,
                        content=content,
                        type=file_type,
                        priority=priority
                    )
                    
                    self.instruction_files.append(instruction_file)
                    logger.info(f"Loaded instruction file: {location}")
                    
                except Exception as e:
                    logger.warning(f"Failed to load instruction file {location}: {e}")
        
        # Sort by priority (highest first)
        self.instruction_files.sort(key=lambda x: x.priority, reverse=True)
        
        return self.instruction_files
    
    def get_combined_instructions(self) -> str:
        """
        Get combined instructions from all files.
        
        Returns:
            Combined instruction string
        """
        if not self.instruction_files:
            self.load_instructions()
        
        if not self.instruction_files:
            return ""
        
        combined_parts = []
        
        for instruction_file in self.instruction_files:
            combined_parts.append(f"# Instructions from {instruction_file.path}")
            combined_parts.append(instruction_file.content)
            combined_parts.append("")  # Empty line between files
        
        return "\n".join(combined_parts)
    
    def get_instructions_by_type(self, file_type: str) -> List[InstructionFile]:
        """
        Get instructions of a specific type.
        
        Args:
            file_type: Type of instructions ('instructions', 'config', 'readme')
            
        Returns:
            List of InstructionFile objects
        """
        if not self.instruction_files:
            self.load_instructions()
        
        return [f for f in self.instruction_files if f.type == file_type]
    
    def create_instruction_file(self, content: str, location: str = '.local-ai/instructions.md') -> bool:
        """
        Create a new instruction file.
        
        Args:
            content: Content to write
            location: Where to create the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if needed
            file_path = self.project_root / location
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            file_path.write_text(content, encoding='utf-8')
            
            logger.info(f"Created instruction file: {location}")
            
            # Reload instructions
            self.load_instructions()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create instruction file {location}: {e}")
            return False
    
    def parse_config_instructions(self) -> Dict[str, Any]:
        """
        Parse configuration from instruction files.
        
        Returns:
            Dictionary with configuration
        """
        config = {}
        
        config_files = self.get_instructions_by_type('config')
        
        for config_file in config_files:
            try:
                if config_file.path.endswith('.yaml') or config_file.path.endswith('.yml'):
                    try:
                        import yaml
                        parsed = yaml.safe_load(config_file.content)
                        if parsed:
                            config.update(parsed)
                    except ImportError:
                        logger.warning("PyYAML not available, skipping YAML config parsing")
                elif config_file.path.endswith('.json'):
                    import json
                    parsed = json.loads(config_file.content)
                    if parsed:
                        config.update(parsed)
            except Exception as e:
                logger.warning(f"Failed to parse config file {config_file.path}: {e}")
        
        return config
    
    def get_project_specific_guidelines(self) -> List[str]:
        """
        Extract specific guidelines from instruction files.
        
        Returns:
            List of guideline strings
        """
        guidelines = []
        
        instruction_files = self.get_instructions_by_type('instructions')
        
        for instruction_file in instruction_files:
            content = instruction_file.content.lower()
            
            # Look for common guideline keywords
            guideline_keywords = [
                'guideline', 'rule', 'convention', 'standard',
                'must', 'should', 'requirement', 'policy'
            ]
            
            lines = instruction_file.content.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in guideline_keywords):
                    guidelines.append(line.strip())
        
        return guidelines
    
    def get_code_style_preferences(self) -> Dict[str, Any]:
        """
        Extract code style preferences from instructions.
        
        Returns:
            Dictionary with style preferences
        """
        style_preferences = {
            'indentation': None,
            'line_length': None,
            'naming_convention': None,
            'docstring_style': None,
            'import_order': None
        }
        
        instruction_files = self.get_instructions_by_type('instructions')
        
        for instruction_file in instruction_files:
            content = instruction_file.content.lower()
            
            # Look for style preferences
            if 'tab' in content and 'space' in content:
                if 'use tab' in content:
                    style_preferences['indentation'] = 'tab'
                elif 'use space' in content:
                    style_preferences['indentation'] = 'space'
            
            if 'line length' in content or 'max line' in content:
                # Try to extract number
                import re
                numbers = re.findall(r'\d+', content)
                if numbers:
                    style_preferences['line_length'] = int(numbers[0])
            
            if 'camelcase' in content:
                style_preferences['naming_convention'] = 'camelCase'
            elif 'snake_case' in content or 'snake case' in content:
                style_preferences['naming_convention'] = 'snake_case'
        
        return style_preferences
    
    def get_tool_preferences(self) -> Dict[str, Any]:
        """
        Extract tool and framework preferences.
        
        Returns:
            Dictionary with tool preferences
        """
        tool_preferences = {
            'test_framework': None,
            'linting': None,
            'formatting': None,
            'build_system': None
        }
        
        instruction_files = self.get_instructions_by_type('instructions')
        
        for instruction_file in instruction_files:
            content = instruction_file.content.lower()
            
            # Test frameworks
            if 'pytest' in content:
                tool_preferences['test_framework'] = 'pytest'
            elif 'unittest' in content:
                tool_preferences['test_framework'] = 'unittest'
            elif 'jest' in content:
                tool_preferences['test_framework'] = 'jest'
            
            # Linting
            if 'eslint' in content:
                tool_preferences['linting'] = 'eslint'
            elif 'pylint' in content:
                tool_preferences['linting'] = 'pylint'
            elif 'flake8' in content:
                tool_preferences['linting'] = 'flake8'
            
            # Formatting
            if 'prettier' in content:
                tool_preferences['formatting'] = 'prettier'
            elif 'black' in content:
                tool_preferences['formatting'] = 'black'
            elif 'autopep8' in content:
                tool_preferences['formatting'] = 'autopep8'
        
        return tool_preferences


# Global instruction manager cache
_instruction_managers: Dict[str, InstructionManager] = {}


def get_instruction_manager(project_root: str) -> InstructionManager:
    """
    Get instruction manager for a project.
    
    Args:
        project_root: Project root directory
        
    Returns:
        InstructionManager instance
    """
    project_root = str(Path(project_root).resolve())
    
    if project_root not in _instruction_managers:
        _instruction_managers[project_root] = InstructionManager(project_root)
    
    return _instruction_managers[project_root]


# Example usage and testing
if __name__ == "__main__":
    # Test instruction manager
    print("Testing Instruction Manager...")
    
    # Test on current directory
    current_dir = Path.cwd()
    manager = get_instruction_manager(str(current_dir))
    
    # Load instructions
    print(f"\nLoading instructions from: {current_dir}")
    instructions = manager.load_instructions()
    
    print(f"Found {len(instructions)} instruction files:")
    for instruction in instructions:
        print(f"  - {instruction.path} ({instruction.type}, priority: {instruction.priority})")
    
    # Get combined instructions
    combined = manager.get_combined_instructions()
    print(f"\nCombined instructions length: {len(combined)} characters")
    print(f"First 200 characters: {combined[:200]}...")
    
    # Get specific type
    readme_files = manager.get_instructions_by_type('readme')
    print(f"\nREADME files: {len(readme_files)}")
    
    # Get guidelines
    guidelines = manager.get_project_specific_guidelines()
    print(f"\nGuidelines found: {len(guidelines)}")
    for guideline in guidelines[:3]:
        print(f"  - {guideline}")
    
    # Get style preferences
    style = manager.get_code_style_preferences()
    print(f"\nStyle preferences:")
    for key, value in style.items():
        print(f"  {key}: {value}")
    
    # Get tool preferences
    tools = manager.get_tool_preferences()
    print(f"\nTool preferences:")
    for key, value in tools.items():
        print(f"  {key}: {value}")
    
    print("\nInstruction manager test completed!")
