"""
Local AI Platform - Project Detection
Detects and initializes project context for AI understanding.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import json
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ProjectInfo:
    """Information about a detected project."""
    project_type: str
    root_path: str
    name: str
    languages: List[str]
    frameworks: List[str]
    config_files: List[str]
    build_systems: List[str]
    metadata: Dict[str, Any]


class ProjectDetector:
    """Detects project type and structure."""
    
    def __init__(self):
        """Initialize project detector."""
        self.project_patterns = {
            'python': {
                'files': ['requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile', 'poetry.lock'],
                'directories': ['.venv', 'venv', '__pycache__'],
                'extensions': ['.py']
            },
            'javascript': {
                'files': ['package.json', 'yarn.lock', 'package-lock.json', 'pnpm-lock.yaml'],
                'directories': ['node_modules', '.next', '.nuxt'],
                'extensions': ['.js', '.ts', '.jsx', '.tsx']
            },
            'flutter': {
                'files': ['pubspec.yaml', 'pubspec.lock'],
                'directories': ['lib', 'android', 'ios', 'build'],
                'extensions': ['.dart']
            },
            'dart': {
                'files': ['pubspec.yaml', 'pubspec.lock'],
                'directories': ['lib', 'bin'],
                'extensions': ['.dart']
            },
            'android': {
                'files': ['build.gradle', 'build.gradle.kts', 'AndroidManifest.xml', 'settings.gradle'],
                'directories': ['app', 'build', 'gradle'],
                'extensions': ['.kt', '.java', '.xml']
            },
            'ios': {
                'files': ['Podfile', 'Podfile.lock', 'Info.plist', 'project.pbxproj'],
                'directories': ['Pods', 'build', 'DerivedData'],
                'extensions': ['.swift', '.m', '.h']
            },
            'rust': {
                'files': ['Cargo.toml', 'Cargo.lock'],
                'directories': ['target'],
                'extensions': ['.rs']
            },
            'go': {
                'files': ['go.mod', 'go.sum'],
                'directories': [],
                'extensions': ['.go']
            },
            'java': {
                'files': ['pom.xml', 'build.gradle', 'gradle.properties'],
                'directories': ['target', 'build'],
                'extensions': ['.java', '.kt']
            },
            'cpp': {
                'files': ['CMakeLists.txt', 'Makefile', 'vcpkg.json'],
                'directories': ['build', 'cmake-build-*'],
                'extensions': ['.cpp', '.cc', '.cxx', '.h', '.hpp']
            },
            'ruby': {
                'files': ['Gemfile', 'Gemfile.lock'],
                'directories': [],
                'extensions': ['.rb']
            },
            'php': {
                'files': ['composer.json', 'composer.lock'],
                'directories': ['vendor'],
                'extensions': ['.php']
            },
            'api': {
                'files': ['openapi.yaml', 'openapi.json', 'swagger.yaml', 'swagger.json', 'api.yaml'],
                'directories': [],
                'extensions': ['.yaml', '.json']
            }
        }
        
        self.framework_patterns = {
            'python': {
                'django': ['manage.py', 'settings.py'],
                'flask': ['app.py', 'wsgi.py'],
                'fastapi': ['main.py', 'main'],
                'pytest': ['pytest.ini', 'setup.cfg', 'pyproject.toml'],
                'pytorch': ['requirements.txt'],  # Check content
                'tensorflow': ['requirements.txt']
            },
            'javascript': {
                'react': ['package.json'],  # Check content
                'vue': ['package.json'],  # Check content
                'angular': ['angular.json'],
                'nextjs': ['next.config.js'],
                'nuxt': ['nuxt.config.js'],
                'express': ['package.json'],
                'jest': ['jest.config.js']
            },
            'flutter': {
                'flutter': ['pubspec.yaml'],  # Check content
                'provider': ['pubspec.yaml'],  # Check content
                'bloc': ['pubspec.yaml'],  # Check content
                'riverpod': ['pubspec.yaml']  # Check content
            },
            'android': {
                'android': ['build.gradle', 'AndroidManifest.xml'],
                'kotlin': ['build.gradle.kts'],
                'java': ['build.gradle']
            },
            'ios': {
                'ios': ['Podfile', 'Info.plist'],
                'swiftui': ['Podfile'],
                'uikit': ['Podfile']
            },
            'api': {
                'openapi': ['openapi.yaml', 'openapi.json'],
                'swagger': ['swagger.yaml', 'swagger.json'],
                'graphql': ['schema.graphql', 'schema.gql']
            }
        }
    
    def detect_project(self, path: str) -> Optional[ProjectInfo]:
        """
        Detect project type from a given path.
        
        Args:
            path: Path to detect project in
            
        Returns:
            ProjectInfo or None if no project detected
        """
        project_path = Path(path).resolve()
        
        if not project_path.exists():
            logger.error(f"Path does not exist: {path}")
            return None
        
        # Find project root (contains config files)
        root_path = self._find_project_root(project_path)
        if not root_path:
            logger.warning(f"No project root found at: {path}")
            return None
        
        # Detect project type
        project_type = self._detect_project_type(root_path)
        if not project_type:
            logger.warning(f"Could not detect project type at: {root_path}")
            project_type = 'generic'
        
        # Detect languages
        languages = self._detect_languages(root_path)
        
        # Detect API projects separately
        has_api = self._detect_api_project(root_path)
        if has_api:
            languages.append('api')
        
        # Detect frameworks
        frameworks = self._detect_frameworks(root_path, languages)
        
        # Detect API frameworks if API project
        if 'api' in languages:
            api_frameworks = self._detect_api_frameworks(root_path)
            frameworks.extend(api_frameworks)
        
        # Find config files
        config_files = self._find_config_files(root_path)
        
        # Detect build systems
        build_systems = self._detect_build_systems(root_path)
        
        # Get project name
        project_name = root_path.name
        
        return ProjectInfo(
            project_type=project_type,
            root_path=str(root_path),
            name=project_name,
            languages=languages,
            frameworks=frameworks,
            config_files=config_files,
            build_systems=build_systems,
            metadata={
                'detected_at': None,  # Could add timestamp
                'file_count': self._count_files(root_path),
                'total_size': self._get_total_size(root_path)
            }
        )
    
    def _find_project_root(self, path: Path) -> Optional[Path]:
        """
        Find project root by looking for config files.
        
        Args:
            path: Starting path
            
        Returns:
            Project root path or None
        """
        current = path.resolve()
        
        # Check if current path has project indicators
        if self._has_project_indicators(current):
            return current
        
        # Walk up directory tree
        for parent in current.parents:
            if self._has_project_indicators(parent):
                return parent
        
        return None
    
    def _has_project_indicators(self, path: Path) -> bool:
        """Check if path has project indicator files."""
        # Common project indicators
        indicators = [
            'package.json', 'requirements.txt', 'Cargo.toml', 'go.mod',
            'pom.xml', 'CMakeLists.txt', 'Gemfile', 'composer.json',
            'setup.py', 'pyproject.toml', 'Makefile'
        ]
        
        for indicator in indicators:
            if (path / indicator).exists():
                return True
        
        # Check for .git directory
        if (path / '.git').exists():
            return True
        
        return False
    
    def _detect_project_type(self, path: Path) -> Optional[str]:
        """Detect project type based on files."""
        for project_type, patterns in self.project_patterns.items():
            for config_file in patterns['files']:
                if (path / config_file).exists():
                    return project_type
        
        return None
    
    def _detect_languages(self, path: Path) -> List[str]:
        """Detect programming languages in project."""
        languages = []
        
        for project_type, patterns in self.project_patterns.items():
            # Skip 'api' as it's not a programming language
            if project_type == 'api':
                continue
                
            # Check for config files
            for config_file in patterns['files']:
                if (path / config_file).exists():
                    if project_type not in languages:
                        languages.append(project_type)
                    break
            
            # Check for source files
            if project_type not in languages:
                source_files = list(path.rglob(f"*{patterns['extensions'][0]}"))
                if source_files:
                    languages.append(project_type)
        
        return languages
    
    def _detect_api_project(self, path: Path) -> bool:
        """Detect if project contains API specifications."""
        api_indicators = ['openapi.yaml', 'openapi.json', 'swagger.yaml', 'swagger.json', 'api.yaml']
        
        for indicator in api_indicators:
            if (path / indicator).exists():
                return True
        
        return False
    
    def _detect_frameworks(self, path: Path, languages: List[str]) -> List[str]:
        """Detect frameworks based on language."""
        frameworks = []
        
        for language in languages:
            if language in self.framework_patterns:
                for framework, indicators in self.framework_patterns[language].items():
                    for indicator in indicators:
                        if (path / indicator).exists():
                            # For package.json, check content
                            if indicator == 'package.json':
                                if self._check_package_json(path / indicator, framework):
                                    frameworks.append(framework)
                            # For pubspec.yaml, check content
                            elif indicator == 'pubspec.yaml':
                                if self._check_pubspec_yaml(path / indicator, framework):
                                    frameworks.append(framework)
                            else:
                                frameworks.append(framework)
                            break
        
        return frameworks
    
    def _detect_api_frameworks(self, path: Path) -> List[str]:
        """Detect API framework from specification files."""
        frameworks = []
        
        for indicator in ['openapi.yaml', 'openapi.json']:
            if (path / indicator).exists():
                frameworks.append('openapi')
                break
        
        for indicator in ['swagger.yaml', 'swagger.json']:
            if (path / indicator).exists():
                frameworks.append('swagger')
                break
        
        return frameworks
    
    def _check_package_json(self, package_json: Path, framework: str) -> bool:
        """Check package.json content for framework indicators."""
        try:
            with open(package_json, 'r') as f:
                content = f.read()
            
            # Framework-specific checks
            framework_keywords = {
                'react': ['react', 'react-dom'],
                'vue': ['vue'],
                'express': ['express'],
                'jest': ['jest'],
                'nextjs': ['next'],
                'nuxt': ['nuxt']
            }
            
            keywords = framework_keywords.get(framework, [])
            return any(keyword in content.lower() for keyword in keywords)
            
        except Exception:
            return False
    
    def _check_pubspec_yaml(self, pubspec_yaml: Path, framework: str) -> bool:
        """Check pubspec.yaml content for framework indicators."""
        try:
            with open(pubspec_yaml, 'r') as f:
                content = f.read()
            
            # Framework-specific checks
            framework_keywords = {
                'flutter': ['flutter', 'flutter sdk'],
                'provider': ['provider'],
                'bloc': ['bloc', 'flutter_bloc'],
                'riverpod': ['flutter_riverpod', 'riverpod']
            }
            
            keywords = framework_keywords.get(framework, [])
            return any(keyword in content.lower() for keyword in keywords)
            
        except Exception:
            return False
    
    def _find_config_files(self, path: Path) -> List[str]:
        """Find configuration files in project."""
        config_files = []
        
        common_configs = [
            '.gitignore', '.env', '.env.example',
            'tsconfig.json', 'jsconfig.json',
            'eslint.config.js', '.eslintrc.js', '.eslintrc.json',
            'prettier.config.js', '.prettierrc',
            'docker-compose.yml', 'Dockerfile',
            'README.md', 'LICENSE'
        ]
        
        for config in common_configs:
            if (path / config).exists():
                config_files.append(config)
        
        return config_files
    
    def _detect_build_systems(self, path: Path) -> List[str]:
        """Detect build systems."""
        build_systems = []
        
        build_indicators = {
            'npm': ['package.json'],
            'pip': ['requirements.txt', 'setup.py', 'pyproject.toml'],
            'cargo': ['Cargo.toml'],
            'go': ['go.mod'],
            'maven': ['pom.xml'],
            'gradle': ['build.gradle', 'build.gradle.kts'],
            'cmake': ['CMakeLists.txt'],
            'make': ['Makefile'],
            'docker': ['Dockerfile', 'docker-compose.yml'],
            'flutter': ['pubspec.yaml'],
            'cocoapods': ['Podfile'],
            'xcode': ['project.pbxproj']
        }
        
        for system, indicators in build_indicators.items():
            for indicator in indicators:
                if (path / indicator).exists():
                    build_systems.append(system)
                    break
        
        return build_systems
    
    def _count_files(self, path: Path) -> int:
        """Count total files in project."""
        try:
            return sum(1 for _ in path.rglob('*') if _.is_file())
        except Exception:
            return 0
    
    def _get_total_size(self, path: Path) -> int:
        """Get total size of project files."""
        try:
            return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        except Exception:
            return 0


# Global project detector instance
_project_detector = None


def get_project_detector() -> ProjectDetector:
    """
    Get global project detector instance.
    
    Returns:
        ProjectDetector instance
    """
    global _project_detector
    if _project_detector is None:
        _project_detector = ProjectDetector()
    return _project_detector


# Example usage and testing
if __name__ == "__main__":
    # Test project detection
    print("Testing Project Detection...")
    
    detector = get_project_detector()
    
    # Test on current directory
    current_dir = Path.cwd()
    print(f"\nDetecting project in: {current_dir}")
    
    project_info = detector.detect_project(str(current_dir))
    
    if project_info:
        print(f"\nProject Detected:")
        print(f"  Type: {project_info.project_type}")
        print(f"  Name: {project_info.name}")
        print(f"  Root: {project_info.root_path}")
        print(f"  Languages: {project_info.languages}")
        print(f"  Frameworks: {project_info.frameworks}")
        print(f"  Config files: {len(project_info.config_files)}")
        print(f"  Build systems: {project_info.build_systems}")
        print(f"  File count: {project_info.metadata['file_count']}")
        print(f"  Total size: {project_info.metadata['total_size'] / (1024**2):.2f} MB")
    else:
        print("No project detected")
    
    print("\nProject detection test completed!")
