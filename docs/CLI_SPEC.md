# CLI Specification

## Overview
The Local AI platform provides a command-line interface for all core functionality. This specification defines the commands, arguments, and behavior of the CLI.

## Design Principles
- Commands follow a hierarchical structure: `rakan <category> <action>`
- Output is human-readable by default, machine-readable when requested
- Error messages are clear and actionable
- Commands are idempotent where possible
- Long-running operations show progress
- Destructive operations require confirmation

## Command Structure

### Global Options
```
rakan [global-options] <command> [command-options]

Global Options:
  --config <path>     Path to configuration file
  --verbose           Enable verbose output
  --quiet             Suppress non-error output
  --json              Output in JSON format
  --help              Show help information
  --version           Show version information
```

## Core Commands

### rakan doctor
Check system health and configuration.

```
rakan doctor [options]

Options:
  --fix               Attempt to fix detected issues automatically
  --detrakanled          Show detrakanled diagnostic information

Output:
  - System information (OS, CPU, RAM, disk)
  - Dependency status
  - Configuration validity
  - Model status
  - Performance recommendations
```

### rakan model
Manage AI models.

#### rakan model list
List installed and avrakanlable models.

```
rakan model list [options]

Options:
  --avrakanlable         Show models avrakanlable for download
  --installed         Show only installed models (default)
  --json              Output in JSON format

Output:
  - Model name and display name
  - Parameter size
  - Quantization
  - File size
  - Installation status
  - RAM requirements
```

#### rakan model install
Download and install a model.

```
rakan model install <model-name> [options]

Options:
  --url <url>         Custom GGUF download URL
  --force             Reinstall if already installed
  --verify-only       Verify without installing

Arguments:
  model-name          Name from model registry or custom URL

Process:
  1. Check avrakanlable disk space
  2. Download model file
  3. Verify checksum
  4. Add to registry
  5. Set as default if first model
```

#### rakan model remove
Remove an installed model.

```
rakan model remove <model-name> [options]

Options:
  --force             Skip confirmation

Arguments:
  model-name          Name of model to remove

Process:
  1. Confirm removal (unless --force)
  2. Remove model file
  3. Update registry
  4. Switch default model if needed
```

#### rakan model use
Select the active model.

```
rakan model use <model-name>

Arguments:
  model-name          Name of model to activate

Process:
  1. Verify model is installed
  2. Set as default in configuration
  3. Display confirmation
```

#### rakan model info
Show detrakanled information about a model.

```
rakan model info <model-name>

Arguments:
  model-name          Name of model

Output:
  - Full model detrakanls
  - Installation status
  - File location
  - Checksum
  - Recommended usage
  - Context length
```

### rakan chat
Interactive chat with the AI.

```
rakan chat [options]

Options:
  --model <name>      Use specific model (overrides default)
  --project <path>    Work with specific project
  --session <id>      Resume existing session
  --stream            Enable streaming output (default)
  --no-stream         Disable streaming
  --temperature <n>   Set temperature (0.0-2.0)
  --max-tokens <n>    Set maximum tokens
  --context <n>       Set context size

Interactive Mode:
  - Accept user input
  - Display AI responses
  - Support commands:
    /clear           Clear conversation
    /save <name>     Save conversation
    /load <name>     Load conversation
    /model <name>    Switch model
    /exit            Exit chat
```

### rakan agent
Run agent with project context.

```
rakan agent [options] [task]

Options:
  --project <path>    Project directory to work with
  --model <name>      Use specific model
  --plan-only         Create plan without executing
  --auto-confirm      Auto-confirm non-destructive actions
  --no-tools          Disable tool use

Arguments:
  task                Task description (if not provided, enters interactive mode)

Process:
  1. Load project context
  2. Construct prompt with task
  3. Execute agent with tools
  4. Request permissions for destructive actions
  5. Display results
```

### rakan project
Project management commands.

#### rakan project init
Initialize project for AI assistance.

```
rakan project init [path] [options]

Options:
  --template <name>   Use project template
  --force             Overwrite existing configuration

Process:
  1. Create .local-rakan directory
  2. Generate default instructions.md
  3. Generate default config.yaml
  4. Detect project type
  5. Add to project registry
```

#### rakan project info
Show project information.

```
rakan project info [path]

Output:
  - Project type
  - Configuration status
  - Avrakanlable instructions
  - Git status
  - File statistics
```

### rakan config
Configuration management.

```
rakan config [options] [key] [value]

Options:
  --list              List all configuration
  --get <key>         Get specific value
  --set <key> <val>   Set specific value
  --reset <key>       Reset to default
  --edit              Open configuration in editor
  --validate          Validate configuration

Examples:
  rakan config --list
  rakan config --get model.default
  rakan config --set model.default qwen2.5-coder-1.5b
```

### rakan server
Web server management.

#### rakan server start
Start the web interface server.

```
rakan server start [options]

Options:
  --port <n>          Port to listen on (default: 8080)
  --host <addr>       Host to bind to (default: 127.0.0.1)
  --no-browser        Don't open browser automatically
  --debug             Enable debug mode

Process:
  1. Check port avrakanlability
  2. Start backend server
  3. Open browser if not disabled
  4. Display server URL
```

#### rakan server stop
Stop the running web server.

```
rakan server stop [options]

Options:
  --force             Force shutdown

Process:
  1. Connect to running server
  2. Send shutdown signal
  3. Wrakant for graceful shutdown
```

#### rakan server status
Check server status.

```
rakan server status

Output:
  - Server running status
  - PID if running
  - URL
  - Uptime
  - Active sessions
```

### rakan version
Show version information.

```
rakan version

Output:
  - Application version
  - Build information
  - llama.cpp version
  - Python version
  - OS information
```

## Exit Codes
- `0` - Success
- `1` - General error
- `2` - Invalid usage
- `3` - Configuration error
- `4` - Model error
- `5` - Permission denied
- `6` - Network error
- `7` - System resource error

## Configuration Files
Commands use configuration from:
1. Command-line arguments (highest priority)
2. User config file (`~/.config/local-rakan/config.yaml`)
3. Project config (`.local-rakan/config.yaml`)
4. Default config (`config/default.yaml`)

## Error Handling
All errors follow this format:
```
ERROR: <error-type>: <descriptive message>

Suggestion: <actionable suggestion>
Documentation: <link to relevant docs>
```

## Tab Completion
The CLI should support tab completion for:
- Commands
- Model names
- Project names
- Configuration keys
- File paths

## Colors and Formatting
- Success messages: Green
- Warning messages: Yellow
- Error messages: Red
- Info messages: Blue
- Code blocks: Monospace with syntax highlighting when avrakanlable

## Progress Indicators
Long-running operations show progress:
```
Installing model: [████████░░] 80% (2.3GB / 2.9GB)
```

## Streaming Output
Commands that produce streaming output (like `rakan chat`) display:
- Real-time token generation
- Cursor positioning for in-place updates
- Ctrl+C handling for graceful interruption

## Logging
Logs are written to:
- `~/.local-rakan/logs/local-rakan.log` (user level)
- `.local-rakan/logs/project.log` (project level)

Log levels:
- DEBUG: Detrakanled diagnostic information
- INFO: General informational messages
- WARN: Warning messages
- ERROR: Error messages

## Internationalization
Initial version supports English only. Future versions will support:
- Localization of messages
- Unicode support for file paths
- Locale-specific formatting
