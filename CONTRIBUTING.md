# Contributing to Local AI Development Platform

Thank you for your interest in contributing to the Local AI Development Platform! This document provides guidelines and instructions for contributors.

## Development Philosophy

Before contributing, please understand our core development principles:

- **Modular Architecture**: Clean separation between layers
- **Simple Solutions**: Prefer simplicity over unnecessary abstraction
- **No Hard-coding**: Configuration belongs in files, not code
- **Incremental Development**: Build features step by step
- **Cross-Platform**: Support both Linux and Windows
- **Security First**: Permission-based access, audit logging
- **Performance**: Optimize for low-resource hardware

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Basic understanding of the project architecture
- Familiarity with the documentation

### Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/local-ai.git
   cd local-ai
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install development dependencies (when available):
   ```bash
   pip install -e ".[dev]"
   ```

5. Run tests to verify setup:
   ```bash
   python -m pytest
   ```

## Development Workflow

### Understanding the Codebase

Before making changes:

1. Read the [ARCHITECTURE.md](docs/ARCHITECTURE.md)
2. Review the [ROADMAP.md](docs/ROADMAP.md) for current phase
3. Check relevant specifications (CLI_SPEC.md, AGENT_SPEC.md, etc.)
4. Inspect existing code in the relevant module
5. Understand the testing approach

### Making Changes

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following the existing code style
3. Add tests for your changes
4. Update documentation if needed
5. Run tests to ensure nothing breaks

### Commit Guidelines

Follow these commit message guidelines:

```
feat: add model registry implementation
fix: handle missing model file gracefully
docs: update installation guide
test: add unit tests for permission system
refactor: simplify tool execution logic
chore: update dependencies
```

Commit messages should:
- Use the present tense ("add" not "added")
- Be concise but descriptive
- Reference relevant issues if applicable
- Follow the Conventional Commits specification

### Pull Request Process

1. Update your branch with the latest main:
   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. Push your changes:
   ```bash
   git push origin feature/your-feature-name
   ```

3. Create a pull request with:
   - Clear description of changes
   - Reference to related issues
   - Testing performed
   - Documentation updates

4. Respond to review feedback promptly

## Code Style Guidelines

### General Principles

- **Readability**: Code should be easy to understand
- **Maintainability**: Easy to modify and extend
- **Consistency**: Follow existing patterns
- **Simplicity**: Avoid over-engineering

### Python-Specific Guidelines

- Follow PEP 8 style guide
- Use type hints where appropriate
- Keep functions focused and small
- Avoid global mutable state
- Use descriptive variable names
- Add docstrings for public functions

### File Organization

- Keep files focused on single responsibility
- Avoid giant files (>500 lines)
- Follow the established directory structure
- Use meaningful file names

## Testing Guidelines

### Test Structure

- Unit tests for individual components
- Integration tests for component interactions
- End-to-end tests for critical workflows

### Writing Tests

1. Test both success and failure cases
2. Use descriptive test names
3. Mock external dependencies
4. Keep tests independent
5. Make tests fast and reliable

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/unit/test_model_manager.py

# Run with coverage
python -m pytest --cov=local_ai
```

## Documentation Guidelines

### When to Update Documentation

- Architecture changes: Update ARCHITECTURE.md
- New features: Update relevant specification files
- API changes: Update appropriate spec files
- User-facing changes: Update README.md or GUIDE.md
- Installation changes: Update INSTALLER_SPEC.md

### Documentation Style

- Use clear, concise language
- Include code examples
- Keep documentation up to date with code
- Use consistent formatting
- Include diagrams where helpful

## Specific Contribution Areas

### Core Contributions

- **Agent Layer**: Tool implementation, permission system
- **Provider Layer**: LLM provider implementations
- **Model System**: Model management, validation
- **CLI**: Command implementations
- **Web UI**: Frontend components and pages

### Infrastructure Contributions

- **Testing**: Test frameworks, test cases
- **Documentation**: Guides, specifications
- **Installer**: Installation scripts, detection
- **Performance**: Optimization, benchmarking

### Community Contributions

- **Bug Reports**: Clear, reproducible bug reports
- **Feature Requests**: Well-thought-out proposals
- **Documentation Improvements**: Clarifications, corrections
- **Code Reviews**: Reviewing pull requests

## Security Considerations

When contributing, keep security in mind:

- Never commit secrets or API keys
- Validate all user inputs
- Follow permission system guidelines
- Update security documentation for relevant changes
- Report security vulnerabilities privately

## Performance Considerations

- Optimize for low-resource hardware
- Avoid unnecessary memory usage
- Consider CPU efficiency
- Profile performance-critical code
- Use efficient algorithms and data structures

## Cross-Platform Considerations

- Test on both Linux and Windows
- Use platform-agnostic paths
- Avoid OS-specific hard-coding
- Handle platform differences gracefully
- Document platform-specific behavior

## Questions and Support

- Check existing documentation first
- Search existing issues and PRs
- Ask questions in GitHub Discussions
- Be specific and provide context

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes for significant contributions
- Project documentation for major features

## Code of Conduct

Be respectful and constructive:
- Treat all contributors with respect
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other contributors

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Local AI Development Platform! Your contributions help make AI development tools accessible to everyone.
