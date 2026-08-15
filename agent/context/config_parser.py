"""
Local AI Platform - Configuration Parser
Parses project configuration files for context understanding.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging
import re

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ConfigFile:
    """Parsed configuration file."""
    path: str
    type: str
    content: Dict[str, Any]
    raw_content: str


class ConfigParser:
    """Parses various project configuration files."""
    
    def __init__(self, project_root: str):
        """
        Initialize configuration parser.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root).resolve()
        self.config_files: Dict[str, ConfigFile] = {}
        
        # Define configuration file patterns
        self.config_patterns = {
            'python': {
                'requirements.txt': self._parse_requirements_txt,
                'setup.py': self._parse_setup_py,
                'pyproject.toml': self._parse_pyproject_toml,
                'Pipfile': self._parse_pipfile,
                'poetry.lock': self._parse_poetry_lock
            },
            'javascript': {
                'package.json': self._parse_package_json,
                'tsconfig.json': self._parse_tsconfig_json,
                'babel.config.js': self._parse_babel_config,
                'webpack.config.js': self._parse_webpack_config
            },
            'flutter': {
                'pubspec.yaml': self._parse_pubspec_yaml,
                'pubspec.lock': self._parse_pubspec_lock
            },
            'dart': {
                'pubspec.yaml': self._parse_pubspec_yaml,
                'pubspec.lock': self._parse_pubspec_lock
            },
            'android': {
                'build.gradle': self._parse_build_gradle,
                'build.gradle.kts': self._parse_build_gradle_kts,
                'AndroidManifest.xml': self._parse_android_manifest,
                'settings.gradle': self._parse_settings_gradle
            },
            'ios': {
                'Podfile': self._parse_podfile,
                'Podfile.lock': self._parse_podfile_lock,
                'Info.plist': self._parse_info_plist,
                'project.pbxproj': self._parse_xcode_project
            },
            'rust': {
                'Cargo.toml': self._parse_cargo_toml,
                'Cargo.lock': self._parse_cargo_lock
            },
            'go': {
                'go.mod': self._parse_go_mod,
                'go.sum': self._parse_go_sum
            },
            'java': {
                'pom.xml': self._parse_pom_xml,
                'build.gradle': self._parse_build_gradle
            },
            'api': {
                'openapi.yaml': self._parse_openapi_yaml,
                'openapi.json': self._parse_openapi_json,
                'swagger.yaml': self._parse_swagger_yaml,
                'swagger.json': self._parse_swagger_json
            },
            'general': {
                '.env': self._parse_env_file,
                '.gitignore': self._parse_gitignore,
                'docker-compose.yml': self._parse_docker_compose,
                'Dockerfile': self._parse_dockerfile
            }
        }
    
    def parse_all_configs(self) -> Dict[str, ConfigFile]:
        """
        Parse all configuration files in the project.
        
        Returns:
            Dictionary of ConfigFile objects
        """
        self.config_files = {}
        
        for category, patterns in self.config_patterns.items():
            for filename, parser_func in patterns.items():
                file_path = self.project_root / filename
                
                if file_path.exists() and file_path.is_file():
                    try:
                        raw_content = file_path.read_text(encoding='utf-8', errors='ignore')
                        parsed_content = parser_func(raw_content, filename)
                        
                        config_file = ConfigFile(
                            path=filename,
                            type=category,
                            content=parsed_content,
                            raw_content=raw_content
                        )
                        
                        self.config_files[filename] = config_file
                        logger.info(f"Parsed config file: {filename}")
                        
                    except Exception as e:
                        logger.warning(f"Failed to parse {filename}: {e}")
        
        return self.config_files
    
    def get_dependencies(self) -> Dict[str, List[str]]:
        """
        Extract dependencies from all config files.
        
        Returns:
            Dictionary mapping file types to dependency lists
        """
        dependencies = {}
        
        for filename, config_file in self.config_files.items():
            deps = self._extract_dependencies(config_file)
            if deps:
                dependencies[filename] = deps
        
        return dependencies
    
    def get_project_metadata(self) -> Dict[str, Any]:
        """
        Extract project metadata from config files.
        
        Returns:
            Dictionary with project metadata
        """
        metadata = {
            'name': None,
            'version': None,
            'description': None,
            'author': None,
            'license': None,
            'repository': None
        }
        
        for config_file in self.config_files.values():
            if 'name' in config_file.content:
                metadata['name'] = config_file.content['name']
            if 'version' in config_file.content:
                metadata['version'] = config_file.content['version']
            if 'description' in config_file.content:
                metadata['description'] = config_file.content['description']
            if 'author' in config_file.content:
                metadata['author'] = config_file.content['author']
            if 'license' in config_file.content:
                metadata['license'] = config_file.content['license']
            if 'repository' in config_file.content:
                metadata['repository'] = config_file.content['repository']
        
        return metadata
    
    def _extract_dependencies(self, config_file: ConfigFile) -> List[str]:
        """Extract dependencies from a config file."""
        if 'dependencies' in config_file.content:
            deps = config_file.content['dependencies']
            if isinstance(deps, dict):
                return list(deps.keys())
            elif isinstance(deps, list):
                return deps
        return []
    
    # Parser functions for specific file types
    
    def _parse_requirements_txt(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse requirements.txt file."""
        dependencies = []
        
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('-'):
                # Extract package name (before version specifiers)
                package = re.split(r'[<>=!~]', line)[0].strip()
                if package:
                    dependencies.append(package)
        
        return {'dependencies': dependencies, 'type': 'python'}
    
    def _parse_setup_py(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse setup.py file (basic extraction)."""
        # Basic extraction using regex
        name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
        version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
        
        return {
            'name': name_match.group(1) if name_match else None,
            'version': version_match.group(1) if version_match else None,
            'type': 'python'
        }
    
    def _parse_pyproject_toml(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse pyproject.toml file."""
        try:
            import tomli
            parsed = tomli.loads(content)
            return parsed
        except ImportError:
            # Fallback to basic parsing
            return self._basic_toml_parse(content)
    
    def _parse_pipfile(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse Pipfile."""
        try:
            import tomli
            parsed = tomli.loads(content)
            return parsed
        except ImportError:
            return self._basic_toml_parse(content)
    
    def _parse_poetry_lock(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse poetry.lock (basic)."""
        try:
            import tomli
            parsed = tomli.loads(content)
            return parsed
        except ImportError:
            return {}
    
    def _parse_package_json(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse package.json file."""
        try:
            import json
            parsed = json.loads(content)
            return parsed
        except Exception:
            return {}
    
    def _parse_tsconfig_json(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse tsconfig.json file."""
        try:
            import json
            parsed = json.loads(content)
            return parsed
        except Exception:
            return {}
    
    def _parse_babel_config(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse babel.config.js (basic)."""
        # This is JavaScript, basic extraction only
        return {'type': 'javascript', 'format': 'js'}
    
    def _parse_webpack_config(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse webpack.config.js (basic)."""
        return {'type': 'javascript', 'format': 'js'}
    
    def _parse_cargo_toml(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse Cargo.toml file."""
        try:
            import tomli
            parsed = tomli.loads(content)
            return parsed
        except ImportError:
            return self._basic_toml_parse(content)
    
    def _parse_cargo_lock(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse Cargo.lock (basic)."""
        try:
            import tomli
            parsed = tomli.loads(content)
            return parsed
        except ImportError:
            return {}
    
    def _parse_go_mod(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse go.mod file."""
        lines = content.split('\n')
        dependencies = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('//') and not line.startswith('module'):
                # Extract package name
                parts = line.split()
                if parts:
                    dependencies.append(parts[0])
        
        return {'dependencies': dependencies, 'type': 'go'}
    
    def _parse_go_sum(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse go.sum (basic)."""
        return {'type': 'go'}
    
    def _parse_pom_xml(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse pom.xml (basic)."""
        # Basic XML parsing
        name_match = re.search(r'<name>([^<]+)</name>', content)
        version_match = re.search(r'<version>([^<]+)</version>', content)
        
        return {
            'name': name_match.group(1) if name_match else None,
            'version': version_match.group(1) if version_match else None,
            'type': 'java'
        }
    
    def _parse_build_gradle(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse build.gradle (basic)."""
        return {'type': 'java', 'format': 'gradle'}
    
    def _parse_env_file(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse .env file."""
        env_vars = {}
        
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
        
        return {'environment_variables': env_vars, 'type': 'env'}
    
    def _parse_gitignore(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse .gitignore file."""
        patterns = []
        
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                patterns.append(line)
        
        return {'ignore_patterns': patterns, 'type': 'git'}
    
    def _parse_docker_compose(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse docker-compose.yml (basic)."""
        try:
            import yaml
            parsed = yaml.safe_load(content)
            return parsed
        except ImportError:
            return {'type': 'docker'}
    
    def _parse_dockerfile(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse Dockerfile (basic)."""
        # Extract FROM instructions
        from_matches = re.findall(r'FROM\s+([^\s]+)', content)
        
        return {
            'base_images': from_matches,
            'type': 'docker'
        }
    
    def _basic_toml_parse(self, content: str) -> Dict[str, Any]:
        """Basic TOML parsing without tomli."""
        # Very basic TOML parsing (just for key=value pairs)
        result = {}
        
        for line in content.split('\n'):
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                result[key] = value
        
        return result
    
    def _basic_yaml_parse(self, content: str) -> Dict[str, Any]:
        """Basic YAML parsing without yaml library."""
        # Very basic YAML parsing (just for key=value pairs)
        result = {}
        
        for line in content.split('\n'):
            line = line.strip()
            if ':' in line and not line.startswith('#'):
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                result[key] = value
        
        return result
    
    def _parse_pubspec_yaml(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse pubspec.yaml file."""
        try:
            import yaml
            parsed = yaml.safe_load(content)
            return parsed
        except ImportError:
            return self._basic_yaml_parse(content)
    
    def _parse_pubspec_lock(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse pubspec.lock (basic)."""
        try:
            import yaml
            parsed = yaml.safe_load(content)
            return parsed
        except ImportError:
            return {}
    
    def _parse_build_gradle_kts(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse build.gradle.kts (basic)."""
        return {'type': 'android', 'format': 'kotlin_gradle'}
    
    def _parse_android_manifest(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse AndroidManifest.xml (basic)."""
        # Basic XML parsing
        package_match = re.search(r'package="([^"]+)"', content)
        
        return {
            'package': package_match.group(1) if package_match else None,
            'type': 'android'
        }
    
    def _parse_settings_gradle(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse settings.gradle (basic)."""
        return {'type': 'android', 'format': 'gradle'}
    
    def _parse_podfile(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse Podfile (basic)."""
        # Extract pod dependencies
        pods = re.findall(r"pod\s+['\"]([^'\"]+)['\"]", content)
        
        return {
            'dependencies': pods,
            'type': 'ios'
        }
    
    def _parse_podfile_lock(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse Podfile.lock (basic)."""
        return {'type': 'ios'}
    
    def _parse_info_plist(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse Info.plist (basic)."""
        # Basic plist parsing
        bundle_id = re.search(r'CFBundleIdentifier\s*<string>([^<]+)</string>', content)
        bundle_name = re.search(r'CFBundleName\s*<string>([^<]+)</string>', content)
        
        return {
            'bundle_id': bundle_id.group(1) if bundle_id else None,
            'bundle_name': bundle_name.group(1) if bundle_name else None,
            'type': 'ios'
        }
    
    def _parse_xcode_project(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse project.pbxproj (basic)."""
        return {'type': 'ios', 'format': 'xcode'}
    
    def _parse_openapi_yaml(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse OpenAPI YAML specification."""
        try:
            import yaml
            parsed = yaml.safe_load(content)
            return parsed
        except ImportError:
            return self._basic_yaml_parse(content)
    
    def _parse_openapi_json(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse OpenAPI JSON specification."""
        try:
            import json
            parsed = json.loads(content)
            return parsed
        except Exception:
            return {}
    
    def _parse_swagger_yaml(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse Swagger YAML specification."""
        try:
            import yaml
            parsed = yaml.safe_load(content)
            return parsed
        except ImportError:
            return self._basic_yaml_parse(content)
    
    def _parse_swagger_json(self, content: str, filename: str) -> Dict[str, Any]:
        """Parse Swagger JSON specification."""
        try:
            import json
            parsed = json.loads(content)
            return parsed
        except Exception:
            return {}
    
    def _basic_toml_parse(self, content: str) -> Dict[str, Any]:
        """Basic TOML parsing without tomli."""
        # Very basic TOML parsing (just for key=value pairs)
        result = {}
        
        for line in content.split('\n'):
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                result[key] = value
        
        return result


# Global config parser cache
_config_parsers: Dict[str, ConfigParser] = {}


def get_config_parser(project_root: str) -> ConfigParser:
    """
    Get config parser for a project.
    
    Args:
        project_root: Project root directory
        
    Returns:
        ConfigParser instance
    """
    project_root = str(Path(project_root).resolve())
    
    if project_root not in _config_parsers:
        _config_parsers[project_root] = ConfigParser(project_root)
    
    return _config_parsers[project_root]


# Example usage and testing
if __name__ == "__main__":
    # Test config parser
    print("Testing Configuration Parser...")
    
    # Test on current directory
    current_dir = Path.cwd()
    parser = get_config_parser(str(current_dir))
    
    # Parse all configs
    print(f"\nParsing configs from: {current_dir}")
    configs = parser.parse_all_configs()
    
    print(f"Found {len(configs)} config files:")
    for filename, config in configs.items():
        print(f"  - {filename} ({config.type})")
    
    # Get dependencies
    dependencies = parser.get_dependencies()
    print(f"\nDependencies:")
    for filename, deps in dependencies.items():
        print(f"  {filename}:")
        for dep in deps[:5]:  # Show first 5
            print(f"    - {dep}")
        if len(deps) > 5:
            print(f"    ... and {len(deps) - 5} more")
    
    # Get metadata
    metadata = parser.get_project_metadata()
    print(f"\nProject metadata:")
    for key, value in metadata.items():
        print(f"  {key}: {value}")
    
    print("\nConfiguration parser test completed!")
