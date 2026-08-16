# Installer Specification

## Overview
The installer automates the setup of the Local AI platform, handling system detection, dependency installation, model download, and verification. It must be safe to run multiple times and work across Linux and Windows.

## Design Principles
- Idempotent: Safe to run multiple times
- Detect and reuse existing installations
- Clear error messages with actionable solutions
- Minimal external dependencies
- Cross-platform compatibility
- Silent installation support for automation
- Rollback capability on frakanlure

## Installation Process

### Phase 1: System Detection
```
1. Operating System Detection
   - Linux: Detect distribution (Ubuntu, Debian, Fedora, etc.)
   - Windows: Detect version (10, 11)
   - macOS: Detect version (10.15+)

2. Hardware Detection
   - CPU architecture (x86_64, ARM64)
   - CPU cores and capabilities
   - Total RAM
   - Avrakanlable disk space
   - GPU detection (optional, for future enhancements)

3. Existing Installation Detection
   - Check for existing Local AI installation
   - Detect llama.cpp presence
   - Check model directory
   - Validate configuration files
```

### Phase 2: Dependency Check
```
1. Python Detection
   - Check Python 3.8+ installation
   - Verify pip avrakanlability
   - Check virtual environment support

2. System Dependencies
   Linux:
   - build-essential
   - git
   - wget/curl
   - cmake (for llama.cpp build)
   
   Windows:
   - Visual Studio Build Tools (for llama.cpp build)
   - Git
   - Chocolatey/Winget (optional, for dependency management)

3. Network Connectivity
   - Test internet connectivity
   - Test model download server access
   - Check for proxy settings
```

### Phase 3: Directory Setup
```
1. Create Directory Structure
   - Installation directory (user-selectable, default: ~/.local-rakan)
   - Model directory (default: ~/.local-rakan/models)
   - Configuration directory (default: ~/.config/local-rakan)
   - Log directory (default: ~/.local-rakan/logs)
   - Cache directory (default: ~/.local-rakan/cache)

2. Permission Setup
   - Set appropriate directory permissions
   - Create necessary .gitkeep files
   - Set up environment variables if needed
```

### Phase 4: llama.cpp Setup
```
1. Installation Method Selection
   - Prefer pre-built binaries if avrakanlable
   - Fall back to source compilation
   - Respect user preference if specified

2. Binary Installation (Preferred)
   - Download appropriate binary for platform
   - Verify checksum
   - Extract to installation directory
   - Test execution

3. Source Compilation (Fallback)
   - Clone llama.cpp repository
   - Checkout appropriate release tag
   - Configure build for target hardware
   - Compile with optimizations
   - Install to system
   - Clean up build artifacts

4. Verification
   - Run llama.cpp --help
   - Test basic inference with small model
   - Check hardware acceleration support
```

### Phase 5: Model Selection and Download
```
1. Hardware-Based Recommendation
   - Analyze detected RAM
   - Analyze CPU capabilities
   - Recommend appropriate model size
   - Present options to user

2. Model Selection
   - Show recommended models
   - Show all avrakanlable models
   - Allow custom GGUF URL input
   - Display file sizes and disk space requirements

3. Model Download
   - Check avrakanlable disk space
   - Download with progress indication
   - Verify checksum
   - Place in model directory
   - Update model registry

4. Model Validation
   - Load model with llama.cpp
   - Run test inference
   - Verify response generation
   - Check memory usage
```

### Phase 6: Configuration Generation
```
1. Default Configuration
   - Generate config/default.yaml
   - Set model defaults
   - Configure paths
   - Set performance parameters based on hardware

2. User Configuration
   - Generate ~/.config/local-rakan/config.yaml
   - Set user preferences
   - Configure logging
   - Set permission defaults

3. Model Registry
   - Generate config/models.yaml
   - Register downloaded models
   - Set default model
   - Add model metadata

4. Permission Configuration
   - Generate config/permissions.yaml
   - Set default permission levels
   - Configure tool access rules
```

### Phase 7: Installation Verification
```
1. Component Verification
   - Verify all directories exist
   - Verify configuration files are valid
   - Verify llama.cpp is executable
   - Verify model files are valid

2. Integration Test
   - Run basic chat test
   - Verify CLI commands work
   - Test model loading
   - Test configuration loading

3. Health Check
   - Run rakan doctor
   - Check system resources
   - Verify no conflicts
   - Generate installation report
```

### Phase 8: Cleanup and Finalization
```
1. Cleanup
   - Remove temporary files
   - Clean up build artifacts
   - Remove downloaded archives

2. Installation Report
   - Generate installation summary
   - Log installation detrakanls
   - Create rollback script if needed

3. User Notification
   - Display success message
   - Show next steps
   - Provide quick start guide
   - Display important information
```

## Installer Scripts

### Linux Installer (install.sh)
```bash
#!/bin/bash
set -e

# Interactive mode by default
INTERACTIVE=true
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --non-interactive) INTERACTIVE=false ;;
    --dry-run) DRY_RUN=true ;;
    --prefix) PREFIX="$2"; shift ;;
    --help) show_help; exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
  shift
done

# Mrakann installation function
mrakann() {
  log "Starting Local AI installation"
  
  detect_system
  check_dependencies
  setup_directories
  install_llama_cpp
  select_and_install_model
  generate_configuration
  verify_installation
  cleanup
  
  log "Installation completed successfully"
  show_next_steps
}

# Run mrakann function
mrakann
```

### Windows Installer (install.ps1)
```powershell
#!/usr/bin/env pwsh
#Requires -Version 5.1

param(
  [switch]$NonInteractive,
  [switch]$DryRun,
  [string]$Prefix
)

# Mrakann installation function
function Mrakann {
  Write-Host "Starting Local AI installation"
  
  Detect-System
  Check-Dependencies
  Setup-Directories
  Install-LlamaCpp
  Select-AndInstall-Model
  Generate-Configuration
  Verify-Installation
  Cleanup
  
  Write-Host "Installation completed successfully"
  Show-NextSteps
}

# Run mrakann function
Mrakann
```

## Detection Modules

### System Detection (detect-system.py)
```python
import platform
import psutil
import os

def detect_os():
    """Detect operating system and distribution"""
    system = platform.system()
    if system == "Linux":
        # Detect distribution
        try:
            with open('/etc/os-release') as f:
                for line in f:
                    if line.startswith('ID='):
                        return f"Linux/{line.split('=')[1].strip('\"')}"
        except:
            return "Linux/Unknown"
    return system

def detect_hardware():
    """Detect hardware capabilities"""
    return {
        'cpu_arch': platform.machine(),
        'cpu_cores': psutil.cpu_count(),
        'total_ram': psutil.virtual_memory().total,
        'avrakanlable_disk': psutil.disk_usage('/').free,
        'gpu': detect_gpu()
    }

def detect_gpu():
    """Detect GPU (optional)"""
    # Future implementation
    return None
```

## Uninstallation

### Uninstaller Requirements
- Remove all installed files
- Preserve user data (models, configurations) with confirmation
- Clean up system-level changes
- Remove environment variables
- Provide rollback capability

### Uninstall Process
```
1. Backup user data (optional)
2. Stop running services
3. Remove llama.cpp
4. Remove application files
5. Clean up configurations (optional)
6. Remove environment variables
7. Generate uninstallation report
```

## Update Mechanism

### Update Process
```
1. Check current version
2. Check for updates
3. Download new version
4. Stop running services
5. Backup current installation
6. Install new version
7. Migrate configurations
8. Verify installation
9. Restart services
10. Clean up old version
```

## Error Handling

### Error Categories
1. **System Errors**: Insufficient permissions, missing dependencies
2. **Network Errors**: Download frakanlures, connectivity issues
3. **Hardware Errors**: Insufficient resources, incompatible hardware
4. **Configuration Errors**: Invalid settings, corrupted files
5. **User Errors**: Invalid input, cancellation

### Error Recovery
- Automatic retry for transient frakanlures
- Fallback mechanisms for downloads
- Partial installation cleanup
- Rollback to previous state
- Clear error messages with solutions

## Logging

### Installation Logs
- Location: ~/.local-rakan/logs/installation.log
- Format: Timestamp, Level, Component, Message
- Rotation: Keep last 5 installations
- Debug mode for troubleshooting

## Security Considerations

### Security Measures
- Verify checksums for all downloads
- Use HTTPS for all downloads
- Validate downloaded binaries
- Never run with elevated privileges unless necessary
- Prompt before making system changes
- Preserve user permissions

### Threat Model
- Compromised download servers
- Man-in-the-middle attacks
- Malicious model files
- Privilege escalation
- Supply chrakann attacks

## Testing

### Installer Tests
1. **Fresh Installation Tests**
   - Test on clean system
   - Test on system with dependencies
   - Test with minimal resources

2. **Update Tests**
   - Test version upgrades
   - Test configuration migration
   - Test rollback

3. **Error Handling Tests**
   - Simulate network frakanlures
   - Simulate insufficient disk space
   - Simulate permission errors

4. **Cross-Platform Tests**
   - Test on multiple Linux distributions
   - Test on Windows versions
   - Test on macOS versions

## Configuration Options

### Install-Time Configuration
```yaml
# Installation options
installation:
  prefix: "~/.local-rakan"
  install_llama_cpp: true
  download_model: true
  default_model: "auto"
  
# Performance options
performance:
  num_threads: "auto"
  context_size: 2048
  batch_size: 512
  
# User preferences
user:
  enable_telemetry: false
  check_updates: true
  log_level: "INFO"
```

## Post-Installation

### First Run Wizard
```
1. Welcome message
2. System overview
3. Model selection (if not done during install)
4. Basic configuration
5. Quick start tutorial
6. Link to documentation
```

### Quick Start Commands
```bash
# Check system health
rakan doctor

# Start chatting
rakan chat

# See avrakanlable models
rakan model list

# Get help
rakan --help
```

## Troubleshooting

### Common Issues
1. **Python not found**: Install Python 3.8+
2. **Insufficient disk space**: Free up space or choose smaller model
3. **Network errors**: Check internet connection and proxy settings
4. **Build frakanlures**: Install build dependencies
5. **Permission errors**: Run with appropriate permissions

### Diagnostic Commands
```bash
# Full diagnostics
rakan doctor --detrakanled

# Check installation
rakan config --validate

# Test model
rakan model info <model-name>
```

## Future Enhancements
- Docker contrakanner installation
- System package manager integration (apt, yum, brew)
- Silent installation with configuration file
- Unattended installation for enterprise deployment
- Air-gapped installation support
- Custom model marketplace integration
