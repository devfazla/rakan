# Model Specification

## Overview
The model layer manages AI model discovery, installation, validation, and selection. It provides a registry-based system for managing GGUF models with hardware-aware recommendations.

## Model Registry

### Registry Structure
Models are defined in a registry file that contains metadata for available models.

```yaml
# config/models.yaml
models:
  qwen2.5-coder-1.5b-instruct:
    display_name: "Qwen2.5-Coder 1.5B Instruct"
    description: "Small coding-focused model for low-resource systems"
    parameters: "1.5B"
    quantization: "Q4_K_M"
    architecture: "Qwen2"
    context_length: 32768
    file_size_gb: 1.2
    ram_required_gb: 4
    recommended_ram_gb: 6
    download_url: "https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf"
    checksum: "sha256:abc123..."
    use_case: "coding"
    language: "multilingual"
    license: "apache-2.0"
    enabled: true
    tags: ["coding", "small", "fast"]
    
  qwen2.5-coder-3b-instruct:
    display_name: "Qwen2.5-Coder 3B Instruct"
    description: "Balanced coding model for general development"
    parameters: "3B"
    quantization: "Q4_K_M"
    architecture: "Qwen2"
    context_length: 32768
    file_size_gb: 2.1
    ram_required_gb: 6
    recommended_ram_gb: 8
    download_url: "https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct-GGUF/resolve/main/qwen2.5-coder-3b-instruct-q4_k_m.gguf"
    checksum: "sha256:def456..."
    use_case: "coding"
    language: "multilingual"
    license: "apache-2.0"
    enabled: true
    tags: ["coding", "balanced", "quality"]
```

### Model Metadata Fields
- **name**: Internal identifier for the model
- **display_name**: Human-readable name
- **description**: Brief description of the model
- **parameters**: Model parameter count (e.g., "1.5B", "3B")
- **quantization**: Quantization level (e.g., "Q4_K_M", "Q5_K_M")
- **architecture**: Model architecture (e.g., "Qwen2", "Llama2")
- **context_length**: Maximum context window size
- **file_size_gb**: Model file size in gigabytes
- **ram_required_gb**: Minimum RAM required
- **recommended_ram_gb**: Recommended RAM for good performance
- **download_url**: URL to download the GGUF file
- **checksum**: SHA256 checksum for verification
- **use_case**: Primary use case (coding, chat, general)
- **language**: Language support
- **license**: Model license
- **enabled**: Whether the model is available for use
- **tags**: Array of tags for filtering

## Model Manager

### Model Manager Interface
```python
class ModelManager:
    def __init__(self, config_path, model_dir):
        self.config_path = config_path
        self.model_dir = model_dir
        self.registry = self.load_registry()
        
    def list_models(self, installed_only=False):
        """List available and/or installed models"""
        pass
        
    def get_model_info(self, model_name):
        """Get detailed information about a model"""
        pass
        
    def install_model(self, model_name, url=None, force=False):
        """Download and install a model"""
        pass
        
    def remove_model(self, model_name, force=False):
        """Remove an installed model"""
        pass
        
    def validate_model(self, model_name):
        """Validate model file integrity"""
        pass
        
    def get_default_model(self):
        """Get the currently default model"""
        pass
        
    def set_default_model(self, model_name):
        """Set the default model"""
        pass
        
    def get_recommended_models(self, hardware_info):
        """Get models recommended for specific hardware"""
        pass
        
    def check_disk_space(self, required_gb):
        """Check if sufficient disk space is available"""
        pass
```

### Model Installation Process
```
1. Validation
   - Check if model already exists
   - Verify model is in registry
   - Check available disk space
   - Validate download URL

2. Download
   - Download with progress indication
   - Support resume on interruption
   - Verify download integrity

3. Validation
   - Verify checksum
   - Validate GGUF format
   - Test model loading

4. Registration
   - Add to installed models
   - Update registry
   - Set as default if first model

5. Verification
   - Test inference
   - Check memory usage
   - Report results
```

### Model Removal Process
```
1. Validation
   - Check if model is installed
   - Check if model is default
   - Confirm removal (unless forced)

2. Removal
   - Delete model file
   - Update registry
   - Update default if needed

3. Cleanup
   - Remove any temporary files
   - Update model cache
```

## Hardware Detection

### Hardware Information
```python
class HardwareDetector:
    def detect(self):
        return {
            'os': self.detect_os(),
            'cpu_arch': self.detect_cpu_arch(),
            'cpu_cores': self.detect_cpu_cores(),
            'total_ram_gb': self.detect_ram(),
            'available_disk_gb': self.detect_disk(),
            'gpu': self.detect_gpu()
        }
        
    def detect_os(self):
        """Detect operating system"""
        import platform
        return platform.system()
        
    def detect_cpu_arch(self):
        """Detect CPU architecture"""
        import platform
        return platform.machine()
        
    def detect_cpu_cores(self):
        """Detect CPU core count"""
        import psutil
        return psutil.cpu_count()
        
    def detect_ram(self):
        """Detect total RAM in GB"""
        import psutil
        return psutil.virtual_memory().total / (1024**3)
        
    def detect_disk(self):
        """Detect available disk space in GB"""
        import psutil
        return psutil.disk_usage('/').free / (1024**3)
        
    def detect_gpu(self):
        """Detect GPU (optional)"""
        # Future implementation
        return None
```

### Model Recommendation Algorithm
```python
def recommend_models(hardware_info, model_registry):
    """Recommend models based on hardware"""
    total_ram = hardware_info['total_ram_gb']
    cpu_cores = hardware_info['cpu_cores']
    
    recommended = []
    
    for model_name, model_info in model_registry.items():
        if not model_info.get('enabled', True):
            continue
            
        # Check RAM requirements
        if total_ram < model_info['ram_required_gb']:
            continue
            
        # Score the model
        score = 0
        
        # Prefer models that use 50-70% of available RAM
        ram_ratio = model_info['ram_required_gb'] / total_ram
        if 0.5 <= ram_ratio <= 0.7:
            score += 10
        elif 0.3 <= ram_ratio < 0.5:
            score += 5
            
        # Prefer smaller models for fewer CPU cores
        if cpu_cores <= 4 and model_info['parameters'] in ['1.5B', '3B']:
            score += 5
            
        # Prefer faster quantization for low-end systems
        if total_ram <= 8 and model_info['quantization'] == 'Q4_K_M':
            score += 3
            
        recommended.append((model_name, score))
    
    # Sort by score and return
    recommended.sort(key=lambda x: x[1], reverse=True)
    return [name for name, score in recommended]
```

## Model Storage

### Directory Structure
```
~/.local-ai/
├── models/
│   ├── qwen2.5-coder-1.5b-instruct-q4_k_m.gguf
│   ├── qwen2.5-coder-3b-instruct-q4_k_m.gguf
│   └── .registry.json
└── cache/
    └── downloads/
```

### Model Registry File
```json
{
  "installed_models": {
    "qwen2.5-coder-1.5b-instruct": {
      "file": "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf",
      "installed_at": "2026-08-14T10:30:00Z",
      "size_bytes": 1234567890,
      "checksum_verified": true,
      "last_used": "2026-08-14T15:45:00Z"
    }
  },
  "default_model": "qwen2.5-coder-1.5b-instruct"
}
```

## Model Loading

### Loading Strategy
```python
class ModelLoader:
    def __init__(self, model_manager, llama_cpp_path):
        self.model_manager = model_manager
        self.llama_cpp_path = llama_cpp_path
        self.loaded_models = {}  # Cache of loaded models
        
    def load_model(self, model_name):
        """Load a model into memory"""
        # Check if already loaded
        if model_name in self.loaded_models:
            return self.loaded_models[model_name]
            
        # Get model info
        model_info = self.model_manager.get_model_info(model_name)
        model_path = os.path.join(self.model_manager.model_dir, model_info['file'])
        
        # Load model with llama.cpp
        model = self.load_with_llama_cpp(model_path, model_info)
        
        # Cache the loaded model
        self.loaded_models[model_name] = model
        
        return model
        
    def unload_model(self, model_name):
        """Unload a model from memory"""
        if model_name in self.loaded_models:
            del self.loaded_models[model_name]
            
    def unload_all(self):
        """Unload all models"""
        self.loaded_models.clear()
```

### Memory Management
```python
class MemoryManager:
    def __init__(self, hardware_info):
        self.hardware_info = hardware_info
        self.loaded_models = {}
        
    def can_load_model(self, model_info):
        """Check if model can be loaded given current memory usage"""
        total_ram = self.hardware_info['total_ram_gb']
        used_ram = self.get_used_ram()
        available_ram = total_ram - used_ram
        
        # Account for OS and other applications (reserve 2GB)
        available_ram -= 2
        
        return available_ram >= model_info['ram_required_gb']
        
    def get_memory_usage(self):
        """Get current memory usage statistics"""
        import psutil
        process = psutil.Process()
        return {
            'used_ram_gb': process.memory_info().rss / (1024**3),
            'loaded_models': list(self.loaded_models.keys()),
            'total_loaded_gb': sum(m['ram_required_gb'] for m in self.loaded_models.values())
        }
```

## Model Validation

### Checksum Verification
```python
def verify_checksum(file_path, expected_checksum):
    """Verify SHA256 checksum of a file"""
    import hashlib
    
    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    actual_checksum = sha256_hash.hexdigest()
    return actual_checksum == expected_checksum
```

### GGUF Format Validation
```python
def validate_gguf(file_path):
    """Validate that a file is a valid GGUF file"""
    try:
        # Check file header
        with open(file_path, 'rb') as f:
            header = f.read(4)
            if header != b'GGUF':
                return False
                
        # Try to load with llama.cpp
        # This will catch format errors
        return True
    except Exception:
        return False
```

### Model Testing
```python
def test_model(model_path, llama_cpp_path):
    """Test that a model can generate output"""
    import subprocess
    
    try:
        # Run simple inference test
        result = subprocess.run(
            [llama_cpp_path, '-m', model_path, '-p', 'Hello', '-n', '10'],
            capture_output=True,
            timeout=30
        )
        
        return result.returncode == 0
    except Exception:
        return False
```

## Configuration Integration

### Model Configuration
```yaml
# config/default.yaml
model:
  default: "qwen2.5-coder-1.5b-instruct"
  directory: "~/.local-ai/models"
  auto_unload: true
  max_loaded_models: 1
  context_size: 2048
  batch_size: 512
  num_threads: "auto"
  
performance:
  enable_mmap: true
  enable_mlock: false
  numa: false
```

### Runtime Configuration
```python
class ModelConfig:
    def __init__(self, config_path):
        self.config = self.load_config(config_path)
        
    def get_inference_params(self, model_name):
        """Get inference parameters for a model"""
        return {
            'context_size': self.config['model']['context_size'],
            'batch_size': self.config['model']['batch_size'],
            'num_threads': self.get_num_threads(),
            'enable_mmap': self.config['performance']['enable_mmap'],
            'enable_mlock': self.config['performance']['enable_mlock']
        }
        
    def get_num_threads(self):
        """Get number of threads to use"""
        threads = self.config['model']['num_threads']
        if threads == "auto":
            import psutil
            return psutil.cpu_count()
        return threads
```

## Error Handling

### Error Categories
1. **Download Errors**: Network failures, invalid URLs
2. **Validation Errors**: Checksum mismatches, invalid format
3. **Storage Errors**: Insufficient disk space, permission errors
4. **Loading Errors**: Memory issues, incompatible hardware
5. **Configuration Errors**: Invalid settings, missing files

### Error Recovery
```python
class ModelErrorHandler:
    def handle_download_error(self, error, model_name):
        # Log error
        # Suggest retry
        # Check network connectivity
        # Offer alternative mirror
        pass
        
    def handle_validation_error(self, error, model_name):
        # Log validation failure
        # Suggest re-download
        # Check for corrupted file
        pass
        
    def handle_loading_error(self, error, model_name):
        # Check memory availability
        # Suggest smaller model
        # Check hardware compatibility
        pass
```

## Performance Optimization

### Loading Optimization
- **Memory Mapping**: Use mmap for large model files
- **Lazy Loading**: Load model layers on demand
- **Model Caching**: Keep frequently used models in memory
- **Parallel Loading**: Load model components in parallel

### Inference Optimization
- **Batch Processing**: Process multiple tokens in batches
- **Context Management**: Efficient context window handling
- **Thread Allocation**: Optimal thread allocation for CPU
- **Memory Alignment**: Proper memory alignment for performance

## Security Considerations

### Download Security
- **HTTPS Only**: Require HTTPS for all downloads
- **Checksum Verification**: Verify all downloaded files
- **Source Validation**: Validate download sources
- **Sandboxing**: Isolate download process

### Model Security
- **Model Validation**: Validate model format before loading
- **Execution Sandbox**: Isolate model execution
- **Resource Limits**: Enforce memory and CPU limits
- **Audit Logging**: Log all model operations

### File Security
- **Permission Management**: Proper file permissions
- **Secure Storage**: Store models in secure location
- **Access Control**: Control model access
- **Integrity Checking**: Regular integrity checks

## Testing

### Unit Tests
- Model registry parsing
- Hardware detection
- Checksum verification
- GGUF validation
- Recommendation algorithm

### Integration Tests
- Model download and installation
- Model loading and inference
- Hardware-aware recommendations
- Configuration integration

### Performance Tests
- Model loading time
- Inference speed
- Memory usage
- Disk usage

## Future Enhancements
- Model fine-tuning support
- Model versioning
- Model marketplace integration
- Distributed model loading
- Model compression
- Custom model registration
- Model A/B testing
- Performance profiling
