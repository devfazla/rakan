# RAKAN

A modular, portable, local-first AI coding assistant that runs on consumer hardware.

## Overview

RAKAN is a self-hosted AI development platform designed to run on modest hardware (8GB RAM, Intel i3 CPU, no GPU) while providing powerful AI-assisted coding capabilities. It prioritizes privacy, portability, and performance.

## Creator

**DevFazla** - Software Developer  
- Website: [https://devfazla.com](https://devfazla.com)  
- Social: [@devfazla](https://twitter.com/devfazla)  
- GitHub: [https://github.com/devfazla](https://github.com/devfazla)

## Key Features

- **Local-First**: All AI processing happens on your machine - no data leaves your system
- **Privacy-Focused**: Your code and conversations never leave your local environment
- **Portable**: Cross-platform support for Linux and Windows
- **CPU-Friendly**: Optimized for systems without dedicated GPUs
- **Modular Architecture**: Clean separation between interface, agent, provider, and engine layers
- **Multiple Model Support**: Works with GGUF quantized models
- **Flexible**: Switch between models without changing application code
- **Dual Interface**: Both CLI and Web UI
- **Project Aware**: Understands and works with local software projects
- **Controlled Tool Access**: Secure, permission-based access to filesystem, terminal, and Git

## Target Hardware

- **RAM**: 8 GB (6 GB recommended for comfortable use)
- **CPU**: Intel Core i3 10th generation or equivalent
- **GPU**: Not required (CPU-based inference)
- **Storage**: SSD with at least 10 GB free space
- **OS**: Linux and Windows support

## Quick Start

### Installation

**Single Command Installation:**
```bash
python install.py
```

This single command handles everything:
- Checks Python installation
- Installs all dependencies
- Sets up the `rakan` command on your system
- Creates necessary directories
- Configures the environment

After installation, close and reopen your terminal, then run:
```bash
rakan
```

### Basic Usage

**Interactive Mode (Default):**
```bash
rakan
```
This starts an interactive CLI session where you can:
- Type `help` for available commands
- Use commands like `doctor`, `model list`, `chat`, etc.
- Type `exit` to quit

**Direct Commands:**
```bash
rakan doctor              # Check system health
rakan model list          # List available models
rakan chat                # Start interactive chat
rakan web                 # Start web server
rakan agent               # Run agent
```

**Start All Components:**
```bash
rakan start               # Start all RAKAN components
```

## Architecture

The platform follows a layered architecture:

```
┌─────────────────┐
│   Web UI / CLI   │
└────────┬────────┘
         │
┌────────▼────────┐
│   Agent Layer   │
│  Context, Tools │
└────────┬────────┘
         │
┌────────▼────────┐
│ Provider Layer  │
└────────┬────────┘
         │
┌────────▼────────┐
│    llama.cpp    │
└────────┬────────┘
         │
┌────────▼────────┐
│   GGUF Models   │
└─────────────────┘
```

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture information.

## Documentation

- [User Manual](docs/USER_MANUAL.md) - Complete user guide with installation and usage
- [Architecture](docs/ARCHITECTURE.md) - System architecture and design
- [Roadmap](docs/ROADMAP.md) - Development phases and timeline
- [CLI Specification](docs/CLI_SPEC.md) - Command-line interface details
- [Agent Specification](docs/AGENT_SPEC.md) - Agent capabilities and tools
- [Model Specification](docs/MODEL_SPEC.md) - Model management and registry
- [Security](docs/SECURITY.md) - Security architecture and practices

## Current Status

**Status**: ✅ **COMPLETE** - All 9 development phases completed

RAKAN is now fully functional with:
- ✅ Complete model management system
- ✅ Interactive chat with streaming
- ✅ Multi-language project context understanding
- ✅ Tool-based agent system with permissions
- ✅ HTTP API for external integration
- ✅ Modern web interface
- ✅ Cross-platform installer
- ✅ Comprehensive testing

See [PROJECT_COMPLETION.md](docs/PROJECT_COMPLETION.md) for detailed completion report.

## Development Philosophy

- **Modular**: Clean separation of concerns
- **Simple**: Prefer simple solutions over unnecessary abstraction
- **Configurable**: Configuration in files, not hard-coded
- **Incremental**: Build features step by step
- **Testable**: Every major feature must be testable independently
- **Cross-Platform**: Works on Linux and Windows
- **Secure**: Permission-based tool access with audit logging

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[License to be determined - see LICENSE file](LICENSE)

## Safety and Security

This project follows security best practices:

- Permission-based tool access
- Audit logging of all operations
- Input validation and sanitization
- Resource limits and timeouts
- Model verification and validation
- Secure file handling

See [SECURITY.md](docs/SECURITY.md) for detailed security information.

## Acknowledgments

- [llama.cpp](https://github.com/ggerganov/llama.cpp) - Inference engine
- [Qwen](https://github.com/QwenLM/Qwen) - Model architecture
- The open-source AI community

## Support

For issues, questions, or contributions:
- GitHub Issues: [Report bugs or request features]
- Documentation: [Check the docs folder](docs/)
- Security: [See SECURITY.md](docs/SECURITY.md)

---

**Note**: This project is in active development. APIs and features may change as we evolve the platform.
