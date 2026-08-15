# Security Specification

## Overview
This document outlines the security architecture, threat model, and security measures for the Local AI platform. As a system that provides AI agents with access to developer tools, security is paramount.

## Threat Model

### Primary Threats
1. **Command Injection**: Malicious input leading to arbitrary command execution
2. **Path Traversal**: Accessing files outside intended directories
3. **Resource Exhaustion**: Denial of service through resource consumption
4. **Data Exfiltration**: Unauthorized access to sensitive data
5. **Privilege Escalation**: Gaining higher privileges than intended
6. **Supply Chain Attacks**: Compromised dependencies or models
7. **Model Poisoning**: Malicious or manipulated model files
8. **Credential Theft**: Accessing passwords, keys, or tokens

### Trust Boundaries
- **User to Agent**: User input must be validated
- **Agent to Tools**: Tool execution must be controlled
- **Tools to System**: System access must be limited
- **Provider to Models**: Model files must be verified
- **Installer to System**: Installation must be safe

## Security Architecture

### Defense in Depth
```
User Input
    ↓
Input Validation
    ↓
Permission System
    ↓
Tool Execution
    ↓
Resource Limits
    ↓
System Interface
    ↓
Operating System
```

### Security Layers

#### Layer 1: Input Validation
- Validate all user inputs
- Sanitize command arguments
- Validate file paths
- Check parameter types and ranges

#### Layer 2: Permission System
- Explicit permission grants
- Permission levels (ALLOW, READ, CONFIRM, EXPLICIT, DENY)
- Audit logging of all decisions
- Temporary and permanent permissions

#### Layer 3: Tool Execution
- Tool whitelisting
- Parameter validation
- Execution sandboxing
- Timeout enforcement

#### Layer 4: Resource Limits
- Memory limits
- CPU time limits
- Disk space limits
- Network rate limits

#### Layer 5: System Interface
- Platform-aware path handling
- Privilege separation
- Secure temporary file handling
- Secure IPC mechanisms

## Security Components

### Permission System

#### Permission Levels
```python
class PermissionLevel(Enum):
    ALLOW = "allow"           # No confirmation needed (safe operations)
    READ = "read"             # Read operations allowed
    CONFIRM = "confirm"       # User confirmation required
    EXPLICIT = "explicit"    # Explicit approval required (dangerous)
    DENY = "deny"            # Always denied (forbidden operations)
```

#### Permission Rules
```yaml
# config/permissions.yaml
tool_permissions:
  read_file:
    level: "read"
    allowed_paths: ["./", "~/.local-ai"]
    denied_paths: ["/etc/", "/sys/", "~/secrets/"]
    
  write_file:
    level: "confirm"
    allowed_paths: ["./", "~/.local-ai"]
    denied_paths: ["/etc/", "/sys/", "~/secrets/"]
    
  run_command:
    level: "explicit"
    denied_commands: ["rm -rf /", "mkfs", "dd if=/dev/zero"]
    
  git_push:
    level: "explicit"
    requires_confirmation: true
    
  install_package:
    level: "explicit"
    requires_confirmation: true
```

#### Permission Request Flow
```
1. Agent requests tool execution
   ↓
2. Permission manager checks rules
   ↓
3. If permission level is ALLOW/READ: Execute
   ↓
4. If permission level is CONFIRM/EXPLICIT: Request user approval
   ↓
5. User approves or denies
   ↓
6. Log decision
   ↓
7. Execute or deny based on decision
```

### Input Validation

#### Command Validation
```python
def validate_command(command):
    """Validate a shell command for safe execution"""
    # Block dangerous commands
    dangerous_patterns = [
        r'mkfs',
        r'rm\s+-rf\s+/',
        r'dd\s+if=/dev/zero',
        r':(){ :|:& };:',  # Fork bomb
        r'chmod\s+777',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, command):
            raise SecurityError("Dangerous command detected")
    
    # Validate syntax
    try:
        subprocess.run(['bash', '-n', command], check=True)
    except subprocess.CalledProcessError:
        raise SecurityError("Invalid command syntax")
    
    return True
```

#### Path Validation
```python
def validate_path(path, allowed_bases, denied_patterns):
    """Validate a file path for safe access"""
    # Resolve to absolute path
    abs_path = os.path.abspath(path)
    
    # Check against denied patterns
    for pattern in denied_patterns:
        if re.search(pattern, abs_path):
            raise SecurityError("Path matches denied pattern")
    
    # Check against allowed bases
    is_allowed = False
    for base in allowed_bases:
        base_abs = os.path.abspath(base)
        if abs_path.startswith(base_abs):
            is_allowed = True
            break
    
    if not is_allowed:
        raise SecurityError("Path outside allowed directories")
    
    return abs_path
```

### Tool Security

#### Tool Whitelisting
```python
class ToolRegistry:
    def __init__(self):
        self.registered_tools = {}
        
    def register(self, tool):
        """Register a tool with security metadata"""
        if not self.validate_tool(tool):
            raise SecurityError("Tool validation failed")
        self.registered_tools[tool.name()] = tool
        
    def validate_tool(self, tool):
        """Validate tool implementation"""
        # Check tool implements required methods
        # Check tool has permission level
        # Check tool has parameter validation
        return True
        
    def get_tool(self, name):
        """Get registered tool"""
        if name not in self.registered_tools:
            raise SecurityError("Tool not registered")
        return self.registered_tools[name]
```

#### Parameter Validation
```python
def validate_parameters(tool, parameters):
    """Validate tool parameters"""
    param_schema = tool.parameters()
    
    for param_name, param_value in parameters.items():
        if param_name not in param_schema:
            raise SecurityError(f"Unknown parameter: {param_name}")
        
        schema = param_schema[param_name]
        
        # Type validation
        if 'type' in schema:
            if not isinstance(param_value, schema['type']):
                raise SecurityError(f"Invalid type for {param_name}")
        
        # Range validation
        if 'min' in schema and param_value < schema['min']:
            raise SecurityError(f"Value below minimum for {param_name}")
        if 'max' in schema and param_value > schema['max']:
            raise SecurityError(f"Value above maximum for {param_name}")
        
        # Pattern validation
        if 'pattern' in schema:
            if not re.match(schema['pattern'], str(param_value)):
                raise SecurityError(f"Invalid format for {param_name}")
    
    return True
```

### Resource Limits

#### Memory Limits
```python
class MemoryLimiter:
    def __init__(self, max_memory_gb):
        self.max_memory_gb = max_memory_gb
        
    def check_memory(self):
        """Check if memory usage is within limits"""
        import psutil
        process = psutil.Process()
        memory_gb = process.memory_info().rss / (1024**3)
        
        if memory_gb > self.max_memory_gb:
            raise ResourceLimitError(f"Memory limit exceeded: {memory_gb}GB > {self.max_memory_gb}GB")
        
        return True
```

#### Execution Timeouts
```python
async def execute_with_timeout(func, timeout):
    """Execute function with timeout"""
    try:
        return await asyncio.wait_for(func, timeout=timeout)
    except asyncio.TimeoutError:
        raise ResourceLimitError("Execution timeout exceeded")
```

### Audit Logging

#### Audit Log Format
```json
{
  "timestamp": "2026-08-14T10:30:00Z",
  "event_type": "tool_execution",
  "tool": "run_command",
  "parameters": {
    "command": "ls -la"
  },
  "permission_level": "confirm",
  "decision": "approved",
  "user": "fazla",
  "session_id": "abc123",
  "result": "success",
  "duration_ms": 150
}
```

#### Audit Log Implementation
```python
class AuditLogger:
    def __init__(self, log_path):
        self.log_path = log_path
        
    def log(self, event):
        """Log security event"""
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(event) + '\n')
            
    def query(self, filters):
        """Query audit log"""
        events = []
        with open(self.log_path, 'r') as f:
            for line in f:
                event = json.loads(line)
                if self.matches_filters(event, filters):
                    events.append(event)
        return events
```

## Model Security

### Model Verification

#### Checksum Verification
```python
def verify_model_checksum(model_path, expected_checksum):
    """Verify model file integrity"""
    import hashlib
    
    sha256_hash = hashlib.sha256()
    with open(model_path, 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    actual_checksum = sha256_hash.hexdigest()
    if actual_checksum != expected_checksum:
        raise SecurityError("Model checksum verification failed")
    
    return True
```

#### Model Validation
```python
def validate_model_format(model_path):
    """Validate GGUF model format"""
    try:
        # Check file header
        with open(model_path, 'rb') as f:
            header = f.read(4)
            if header != b'GGUF':
                raise SecurityError("Invalid GGUF file header")
        
        # Additional validation checks
        # - Check tensor dimensions
        # - Verify architecture compatibility
        # - Validate vocabulary
        
        return True
    except Exception as e:
        raise SecurityError(f"Model validation failed: {str(e)}")
```

### Model Sandboxing

#### Isolated Execution
```python
class ModelSandbox:
    def __init__(self, model_path):
        self.model_path = model_path
        self.process = None
        
    def start(self):
        """Start model in isolated process"""
        # Use process isolation
        # Limit system calls
        # Restrict network access
        # Set resource limits
        pass
        
    def stop(self):
        """Stop isolated process"""
        if self.process:
            self.process.terminate()
```

## File System Security

### Secure File Handling

#### Temporary Files
```python
import tempfile
import os

def create_temp_file():
    """Create secure temporary file"""
    # Use secure temporary directory
    temp_dir = tempfile.mkdtemp(prefix='local-ai_')
    
    # Set restrictive permissions
    os.chmod(temp_dir, 0o700)
    
    # Create file with restricted permissions
    fd, path = tempfile.mkstemp(dir=temp_dir)
    os.chmod(path, 0o600)
    
    return fd, path
```

#### Secure File Deletion
```python
def secure_delete(file_path):
    """Securely delete file"""
    # Overwrite file content
    with open(file_path, 'wb') as f:
        f.write(os.urandom(os.path.getsize(file_path)))
    
    # Remove file
    os.remove(file_path)
```

### Directory Access Control

#### Permission Management
```python
def set_directory_permissions(directory):
    """Set appropriate directory permissions"""
    # Directory: 750 (rwxr-x---)
    os.chmod(directory, 0o750)
    
    # Ensure ownership is correct
    # (platform-specific)
```

## Network Security

### Download Security

#### HTTPS Enforcement
```python
def validate_url(url):
    """Validate and enforce HTTPS"""
    parsed = urlparse(url)
    
    if parsed.scheme != 'https':
        raise SecurityError("Only HTTPS URLs are allowed")
    
    # Validate hostname
    if not parsed.hostname:
        raise SecurityError("Invalid URL hostname")
    
    return True
```

#### Certificate Verification
```python
import ssl
import certifi

def create_ssl_context():
    """Create SSL context with certificate verification"""
    context = ssl.create_default_context()
    context.load_verify_locations(certifi.where())
    context.verify_mode = ssl.CERT_REQUIRED
    return context
```

## Installation Security

### Installer Security

#### Dependency Verification
```python
def verify_dependency(dependency):
    """Verify dependency integrity"""
    # Check checksums
    # Verify signatures
    # Validate source
    pass
```

#### Secure Installation
```python
def secure_install(installer_path):
    """Run installer with security checks"""
    # Verify installer signature
    # Check installer permissions
    # Run with minimal privileges
    # Monitor installation process
    pass
```

## Configuration Security

### Sensitive Data Protection

#### Secret Management
```python
class SecretManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.secrets = {}
        
    def load_secrets(self):
        """Load secrets from secure storage"""
        # Use encrypted storage
        # Require authentication
        # Never log secrets
        pass
        
    def get_secret(self, key):
        """Get secret with logging prevention"""
        secret = self.secrets.get(key)
        # Prevent secret from appearing in logs
        return secret
```

#### Configuration Validation
```python
def validate_config(config):
    """Validate configuration for security issues"""
    # Check for hardcoded secrets
    # Validate file paths
    # Check permission settings
    # Verify network settings
    pass
```

## Security Best Practices

### Development Guidelines
1. **Never log sensitive data**: Passwords, keys, tokens
2. **Always validate input**: From users, files, network
3. **Use parameterized queries**: For any database operations
4. **Principle of least privilege**: Minimal required permissions
5. **Defense in depth**: Multiple security layers
6. **Security by default**: Secure configurations out of the box

### Operational Guidelines
1. **Regular updates**: Keep dependencies updated
2. **Security audits**: Regular security reviews
3. **Monitoring**: Monitor for suspicious activity
4. **Incident response**: Have a response plan
5. **Backup and recovery**: Regular secure backups
6. **Access control**: Restrict access to sensitive components

### User Guidelines
1. **Review permissions**: Understand what permissions are granted
2. **Use strong authentication**: For any authentication required
3. **Keep updated**: Update to latest security patches
4. **Report issues**: Report security concerns promptly
5. **Use network security**: VPNs, firewalls where appropriate

## Security Testing

### Security Tests
1. **Input validation tests**: Test with malicious inputs
2. **Permission tests**: Test permission enforcement
3. **Resource limit tests**: Test limit enforcement
4. **Authentication tests**: Test authentication mechanisms
5. **Network security tests**: Test network security measures

### Penetration Testing
- Regular penetration testing
- Third-party security audits
- Vulnerability scanning
- Dependency vulnerability scanning

## Incident Response

### Security Incident Process
1. **Detection**: Monitor for security events
2. **Analysis**: Investigate potential incidents
3. **Containment**: Limit damage
4. **Eradication**: Remove threat
5. **Recovery**: Restore systems
6. **Post-incident analysis**: Learn and improve

### Reporting Security Issues
- Private disclosure process
- Security contact information
- Responsible disclosure guidelines
- Bug bounty program (if applicable)

## Compliance

### Data Protection
- GDPR compliance considerations
- Data minimization principles
- User consent mechanisms
- Data retention policies

### Licensing
- License compliance for models
- License compliance for dependencies
- Attribution requirements

## Future Security Enhancements
- Hardware security modules (HSM) integration
- Advanced threat detection
- Behavioral analysis
- Anomaly detection
- Enhanced encryption
- Zero-trust architecture
- Secure enclaves for model execution
