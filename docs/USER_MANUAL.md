# RAKAN User Manual

Complete guide for installing, configuring, and using RAKAN - your local AI development assistant.

## Table of Contents

1. [Introduction](#introduction)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Getting Started](#getting-started)
6. [CLI Commands](#cli-commands)
7. [Web Interface](#web-interface)
8. [Model Management](#model-management)
9. [Project Context](#project-context)
10. [Agent System](#agent-system)
11. [Troubleshooting](#troubleshooting)
12. [Advanced Usage](#advanced-usage)

---

## Introduction

RAKAN is a modular, portable, local-first AI coding assistant that runs on consumer hardware. It provides powerful AI-assisted coding capabilities while maintaining complete privacy - all processing happens on your machine.

### Key Features

- **Local-First**: All AI processing happens on your machine
- **Privacy-Focused**: Your code and conversations never leave your system
- **Portable**: Cross-platform support for Linux and Windows
- **CPU-Friendly**: Optimized for systems without dedicated GPUs
- **Modular Architecture**: Clean separation between interface, agent, provider, and engine layers
- **Multiple Model Support**: Works with GGUF quantized models
- **Flexible**: Switch between models without changing application code
- **Dual Interface**: Both CLI and Web UI
- **Project Aware**: Understands and works with local software projects
- **Controlled Tool Access**: Secure, permission-based access to filesystem, terminal, and Git

---

## System Requirements

### Minimum Requirements

- **RAM**: 8 GB (6 GB recommended for comfortable use)
- **CPU**: Intel Core i3 10th generation or equivalent
- **GPU**: Not required (CPU-based inference)
- **Storage**: SSD with at least 10 GB free space
- **OS**: Linux or Windows

### Recommended Requirements

- **RAM**: 16 GB
- **CPU**: Intel Core i5 or equivalent
- **Storage**: SSD with 20 GB free space
- **Python**: 3.8 or higher

---

## Installation

### Option 1: Automatic Installation (Recommended)

#### Windows

Run the automatic installation script:
```bash
install_windows.bat
```

This script will:
- Check for Python installation
- Create a batch file wrapper for RAKAN
- Add RAKAN to your system PATH
- Provide instructions for manual PATH setup if needed

After installation, close and reopen your terminal, then run:
```bash
rakan --help
```

#### Linux/macOS

Run the automatic installation script:
```bash
chmod +x install_linux.sh
./install_linux.sh
```

This script will:
- Check for Python installation
- Create a shell script wrapper for RAKAN
- Add RAKAN to your PATH in your shell configuration
- Provide instructions for reloading your shell

After installation, run:
```bash
source ~/.bashrc  # or ~/.zshrc
rakan --help
```

#### Cross-platform Python

Run the Python installation script:
```bash
python install.py
```

This script works on all platforms and handles platform-specific setup automatically.

### Option 2: Manual Installation

#### Prerequisites

- Python 3.8 or higher
- pip package manager

#### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/devfazla/rakan.git
   cd rakan
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run RAKAN:
   ```bash
   python cli/main.py --help
   ```

4. (Optional) Create an alias for easier access:
   ```bash
   # Add to your shell configuration (~/.bashrc, ~/.zshrc, etc.)
   alias rakan='python /path/to/rakan/cli/main.py'
   ```
   ```

4. (Optional) Install optional dependencies for web UI:
   ```bash
   pip install fastapi uvicorn websockets
   ```

---

## Configuration

### Configuration Files

RAKAN uses YAML configuration files located in the `config/` directory:

- `config/default.yaml` - Main configuration
- `config/models.yaml` - Model registry
- `config/permissions.yaml` - Permission rules

### Key Configuration Options

#### Application Settings

```yaml
application:
  name: "RAKAN"
  version: "0.1.0"
  debug: false
  log_level: "INFO"
```

#### Model Configuration

```yaml
model:
  default: "qwen2.5-coder-1.5b-instruct"
  auto_unload: true
  max_loaded_models: 1
  context_size: 2048
  temperature: 0.7
```

#### Performance Settings

```yaml
performance:
  enable_mmap: true
  memory_fraction: 0.8
  low_resource_mode: true
```

### Custom Configuration

Create a user configuration file in `~/.config/rakan/user_config.yaml` to override defaults:

```yaml
model:
  default: "qwen2.5-coder-3b-instruct"
  temperature: 0.8

agent:
  max_history_messages: 50
```

---

## Getting Started

### First Steps

1. **Check System Health**
   ```bash
   rakan doctor
   ```

2. **List Available Models**
   ```bash
   rakan model list
   ```

3. **Install a Model**
   ```bash
   rakan model install qwen2.5-coder-1.5b-instruct
   ```

4. **Select Active Model**
   ```bash
   rakan model use qwen2.5-coder-1.5b-instruct
   ```

5. **Start Chat**
   ```bash
   rakan chat
   ```

### Quick Test

Test your installation with a simple chat session:

```bash
rakan chat
```

Then try:
```
You: Hello! Can you help me write a Python function?
RAKAN: Of course! What kind of function would you like me to help you with?
```

---

## CLI Commands

### System Commands

#### `rakan doctor`
Check system health and configuration.

```bash
rakan doctor
rakan doctor --detailed
rakan doctor --fix
```

### Model Commands

#### `rakan model list`
List available and installed models.

```bash
rakan model list
rakan model list --available
rakan model list --installed
```

#### `rakan model install`
Download and install a model.

```bash
rakan model install qwen2.5-coder-1.5b-instruct
```

#### `rakan model remove`
Remove an installed model.

```bash
rakan model remove qwen2.5-coder-1.5b-instruct
```

#### `rakan model use`
Select active model.

```bash
rakan model use qwen2.5-coder-1.5b-instruct
```

#### `rakan model info`
Show detailed information about a model.

```bash
rakan model info qwen2.5-coder-1.5b-instruct
```

### Chat Commands

#### `rakan chat`
Start interactive chat session.

```bash
rakan chat
rakan chat --model qwen2.5-coder-3b-instruct
rakan chat --project ./my-project
rakan chat --session my-session
rakan chat --temperature 0.8
```

### Project Commands

#### `rakan project context`
Show project context information.

```bash
rakan project context
rakan project context --directory ./my-project
rakan project context --build-context --query "database"
```

#### `rakan project init`
Initialize project for AI understanding.

```bash
rakan project init
rakan project init --directory ./my-project
rakan project init --force
```

### Agent Commands

#### `rakan agent run`
Run agent in interactive mode.

```bash
rakan agent run
rakan agent run --mode interactive
rakan agent run --mode single --task "Fix the bug"
rakan agent run --auto-approve
```

#### `rakan agent permissions`
Show permission rules.

```bash
rakan agent permissions
```

#### `rakan agent audit`
Show audit log.

```bash
rakan agent audit
rakan agent audit --limit 20
```

### Server Commands

#### `rakan server`
Start API server.

```bash
rakan server
rakan server --host 0.0.0.0 --port 8000
```

---

## Web Interface

### Starting the Web Server

```bash
rakan server
```

Access the web interface at `http://localhost:8000`

### Web Interface Features

#### Chat Interface
- Real-time chat with AI assistant
- Message history
- Auto-scroll to latest messages
- Send with Enter, new line with Shift+Enter

#### Model Selection
- Dropdown to select active model
- Model options: Default, Qwen2.5-Coder 1.5B, Qwen2.5-Coder 3B

#### Session Management
- List of chat sessions
- Active session highlighting
- Session selection

#### Project Context
- Project name and type display
- File count and Git status
- Static context information

#### Agent Status
- Agent status (Idle/Busy)
- Task execution count
- Memory usage

#### Theme Support
- Dark theme (default)
- Light theme option
- Theme toggle button

### API Endpoints

#### Health Check
```
GET /api/v1/health
```

#### Agent Execution
```
POST /api/v1/agent
Content-Type: application/json

{
  "message": "Your task here",
  "context": {},
  "auto_approve": false
}
```

#### Model List
```
GET /api/v1/models
```

#### Chat
```
POST /api/v1/chat
Content-Type: application/json

{
  "message": "Your message",
  "model": "qwen2.5-coder-1.5b-instruct",
  "session_id": "optional-session-id",
  "temperature": 0.7,
  "max_tokens": 1024
}
```

#### Session Management
```
GET /api/v1/sessions
GET /api/v1/sessions/{session_id}
DELETE /api/v1/sessions/{session_id}
```

---

## Model Management

### Available Models

#### Qwen2.5-Coder 1.5B Instruct
- **Size**: ~1.2 GB
- **RAM**: 4 GB required
- **Context**: 32,768 tokens
- **Quantization**: Q4_K_M
- **Use Case**: General coding assistance, resource-constrained systems

#### Qwen2.5-Coder 3B Instruct
- **Size**: ~2.1 GB
- **RAM**: 6 GB required
- **Context**: 32,768 tokens
- **Quantization**: Q4_K_M
- **Use Case**: More complex coding tasks, better reasoning

### Model Operations

#### Installing a Model
```bash
rakan model install qwen2.5-coder-1.5b-instruct
```

#### Checking Installation Status
```bash
rakan model info qwen2.5-coder-1.5b-instruct
```

#### Switching Models
```bash
rakan model use qwen2.5-coder-3b-instruct
```

#### Removing a Model
```bash
rakan model remove qwen2.5-coder-1.5b-instruct
```

---

## Project Context

### Supported Languages

RAKAN understands projects in 13+ programming languages:
- Python, JavaScript, Rust, Go, Java, C++, Ruby, PHP
- Flutter, Dart, Android, iOS
- API specifications (OpenAPI, Swagger)

### Using Project Context

#### Analyze a Project
```bash
rakan project context --directory ./my-project
```

#### Build Context for AI
```bash
rakan project context --build-context --query "authentication"
```

#### Initialize Project Instructions
```bash
rakan project init --directory ./my-project
```

This creates `.local-ai/instructions.md` where you can provide project-specific guidance.

---

## Agent System

### Available Tools

RAKAN includes 7 default tools:

1. **read_file** - Read file contents
2. **write_file** - Write content to files (requires approval)
3. **list_directory** - List directory contents
4. **search_files** - Search for files by pattern
5. **execute_command** - Execute shell commands (requires approval)
6. **git_status** - Get Git repository status
7. **git_diff** - Get Git diff for changes

### Permission System

RAKAN uses a permission-based system for safety:

- **READ operations**: Allowed by default
- **WRITE operations**: Require confirmation
- **DANGEROUS operations**: Denied by default
- **System paths**: Protected (e.g., /etc, ~/.ssh)

### Using the Agent

#### Interactive Mode
```bash
rakan agent run
```

Then ask the agent to perform tasks:
```
You: Read the README file
You: List Python files in the project
You: Check git status
```

#### Single Task Mode
```bash
rakan agent run --mode single --task "Read the configuration file"
```

#### Permission Checking
```bash
rakan agent permissions
```

#### Audit Log
```bash
rakan agent audit
```

---

## Troubleshooting

### Common Issues

#### Model Not Found
**Problem**: Model not installed or not found
**Solution**: 
```bash
rakan model list
rakan model install qwen2.5-coder-1.5b-instruct
```

#### Memory Issues
**Problem**: Out of memory errors
**Solution**: 
- Use smaller model (1.5B instead of 3B)
- Reduce context size in configuration
- Close other applications

#### Permission Denied
**Problem**: Tool execution denied
**Solution**: 
- Check permission rules: `rakan agent permissions`
- Use appropriate file paths
- Run with `--auto-approve` if you trust the operation

#### Server Won't Start
**Problem**: API server fails to start
**Solution**: 
- Install FastAPI: `pip install fastapi uvicorn websockets`
- Check port availability
- Check firewall settings

#### Slow Performance
**Problem**: Slow response times
**Solution**: 
- Use smaller model
- Reduce context size
- Enable low resource mode in configuration
- Close other applications

### Getting Help

1. Check system health: `rakan doctor`
2. Review configuration: `~/.config/rakan/user_config.yaml`
3. Check logs: `~/.rakan/logs/rakan.log`
4. Check audit log: `rakan agent audit`
5. Report issues: [GitHub Issues](https://github.com/devfazla/rakan/issues)

---

## Advanced Usage

### Custom Configuration

Create `~/.config/rakan/user_config.yaml`:

```yaml
model:
  default: "qwen2.5-coder-3b-instruct"
  temperature: 0.8
  max_tokens: 2048

agent:
  max_history_messages: 200
  enable_planning: true

performance:
  memory_fraction: 0.9
  low_resource_mode: false
```

### Integration with Development Workflow

#### VS Code Integration
Create a VS Code task in `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "RAKAN Chat",
      "type": "shell",
      "command": "rakan",
      "args": ["chat"],
      "problemMatcher": []
    },
    {
      "label": "RAKAN Project Context",
      "type": "shell",
      "command": "rakan",
      "args": ["project", "context"]
    }
  ]
}
```

#### Git Integration
RAKAN automatically detects Git repositories and provides:
- Git status information
- Git diff for changes
- Commit history context

### API Integration

Use RAKAN's HTTP API in your applications:

```python
import requests

# Chat with RAKAN
response = requests.post('http://localhost:8000/api/v1/chat', json={
    'message': 'Write a Python function',
    'model': 'qwen2.5-coder-1.5b-instruct',
    'temperature': 0.7
})

print(response.json()['response'])
```

### Batch Processing

Use the agent for batch operations:

```bash
rakan agent run --mode single --task "Analyze all Python files"
```

---

## Safety and Security

### Privacy Guarantees

- **Local Processing**: All AI inference happens on your machine
- **No Cloud Dependencies**: No data sent to external services
- **No Telemetry**: Optional anonymous telemetry (disabled by default)
- **Secure File Handling**: Permission-based access control

### Security Features

- **Permission System**: All operations require appropriate permissions
- **Audit Logging**: Complete audit trail of all operations
- **Path Protection**: System paths protected from access
- **Command Filtering**: Dangerous commands blocked
- **Input Validation**: All inputs validated and sanitized

### Best Practices

1. **Review Permissions**: Regularly check `rakan agent permissions`
2. **Audit Operations**: Monitor `rakan agent audit`
3. **Secure Configuration**: Keep sensitive data out of config files
4. **Regular Updates**: Keep RAKAN updated for security patches
5. **Backup Configuration**: Backup your custom configurations

---

## Uninstallation

### Windows

1. Run the uninstaller:
   ```bash
   python installer/installer.py uninstall
   ```

2. Or manually remove:
   - Delete installation directory
   - Remove desktop shortcut
   - Remove from PATH

### Linux

```bash
python installer/installer.py uninstall
```

Or manually remove:
```bash
rm -rf ~/.rakan
rm -rf ~/.config/rakan
```

---

## Support and Community

### Getting Help

- **Documentation**: Check this manual and [docs/](docs/) folder
- **GitHub Issues**: [Report bugs](https://github.com/devfazla/rakan/issues)
- **Website**: [https://devfazla.com](https://devfazla.com)
- **Social**: [@devfazla](https://twitter.com/devfazla)

### Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Acknowledgments

- [llama.cpp](https://github.com/ggerganov/llama.cpp) - Inference engine
- [Qwen](https://github.com/QwenLM/Qwen) - Model architecture
- The open-source AI community

---

## Version History

### Version 0.1.0 (Current)
- Complete model management system
- Interactive chat with streaming
- Multi-language project context understanding
- Tool-based agent system with permissions
- HTTP API for external integration
- Modern web interface
- Cross-platform installer
- Comprehensive testing

---

## Uninstallation

### Uninstall RAKAN

To uninstall RAKAN from your system:

```bash
rakan uninstall
```

This will:
- Show what will be removed
- Ask for confirmation (y/n)
- Remove the wrapper file
- Remove the data directory (~/.rakan)
- Remove PATH entries
- Provide manual cleanup instructions if needed

**Force uninstall (skip confirmation):**
```bash
rakan uninstall --force
```

**What gets removed:**
- Wrapper file (rakan.bat on Windows, rakan on Linux/macOS)
- Data directory (~/.rakan)
- PATH entries
- Models and configuration

**Manual cleanup (if needed):**

**Windows:**
1. Delete wrapper file: `C:\Users\YourName\rakan.bat`
2. Remove from PATH:
   - Press Win+R, type "sysdm.cpl"
   - Go to Advanced tab, click Environment Variables
   - Under User variables, find PATH and click Edit
   - Remove your user directory from the list
3. Delete data directory: `C:\Users\YourName\.rakan`

**Linux/macOS:**
1. Delete wrapper file: `~/.local/bin/rakan`
2. Remove from shell config (~/.bashrc, ~/.zshrc, etc.)
3. Delete data directory: `~/.rakan`

---

## License

[See LICENSE file](LICENSE) for license information.

---

**RAKAN** - Your Local AI Development Assistant  
Created by **DevFazla**  
Website: [https://devfazla.com](https://devfazla.com)  
Social: [@devfazla](https://twitter.com/devfazla)
