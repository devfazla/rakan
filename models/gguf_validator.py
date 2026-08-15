"""
Local AI Platform - GGUF Validator
Handles GGUF file detection, validation, and verification.
"""

import sys
import struct
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent.core import get_logger


@dataclass
class GGUFHeader:
    """Data class for GGUF file header information."""
    magic: str
    version: int
    tensor_count: int
    metadata: Dict[str, Any]
    valid: bool


class GGUFValidator:
    """Validates GGUF model files."""
    
    # GGUF magic number
    GGUF_MAGIC = b'GGUF'
    
    def __init__(self):
        """Initialize GGUF validator."""
        self.logger = get_logger(__name__)
    
    def validate_gguf_file(self, file_path: Path) -> Tuple[bool, Optional[GGUFHeader]]:
        """
        Validate a GGUF file.
        
        Args:
            file_path: Path to the GGUF file
            
        Returns:
            Tuple of (is_valid, header_info)
        """
        self.logger.info(f"Validating GGUF file: {file_path}")
        
        if not file_path.exists():
            self.logger.error(f"File does not exist: {file_path}")
            return False, None
        
        if not file_path.is_file():
            self.logger.error(f"Path is not a file: {file_path}")
            return False, None
        
        try:
            header = self._read_gguf_header(file_path)
            if header and header.valid:
                self.logger.info(f"Valid GGUF file: {file_path}")
                return True, header
            else:
                self.logger.error(f"Invalid GGUF file: {file_path}")
                return False, header
                
        except Exception as e:
            self.logger.error(f"Error validating GGUF file: {e}")
            return False, None
    
    def _read_gguf_header(self, file_path: Path) -> Optional[GGUFHeader]:
        """
        Read GGUF file header.
        
        Args:
            file_path: Path to the GGUF file
            
        Returns:
            GGUFHeader instance or None if invalid
        """
        try:
            with open(file_path, 'rb') as f:
                # Read magic number (4 bytes)
                magic = f.read(4)
                if magic != self.GGUF_MAGIC:
                    self.logger.error(f"Invalid magic number: {magic}")
                    return GGUFHeader(magic='', version=0, tensor_count=0, metadata={}, valid=False)
                
                # Read version (uint32)
                version = struct.unpack('<I', f.read(4))[0]
                
                # Read tensor count (uint64)
                tensor_count = struct.unpack('<Q', f.read(8))[0]
                
                # Read metadata key-value count (uint64)
                kv_count = struct.unpack('<Q', f.read(8))[0]
                
                # Read metadata
                metadata = {}
                for _ in range(kv_count):
                    key_length = struct.unpack('<Q', f.read(8))[0]
                    key = f.read(key_length).decode('utf-8')
                    
                    value_type = struct.unpack('<I', f.read(4))[0]
                    value = self._read_gguf_value(f, value_type)
                    
                    metadata[key] = value
                
                return GGUFHeader(
                    magic=magic.decode('utf-8', errors='ignore'),
                    version=version,
                    tensor_count=tensor_count,
                    metadata=metadata,
                    valid=True
                )
                
        except Exception as e:
            self.logger.error(f"Error reading GGUF header: {e}")
            return GGUFHeader(magic='', version=0, tensor_count=0, metadata={}, valid=False)
    
    def _read_gguf_value(self, f, value_type: int) -> Any:
        """
        Read a GGUF value based on type.
        
        Args:
            f: File object
            value_type: GGUF value type
            
        Returns:
            Parsed value
        """
        # GGUF value types (simplified)
        type_mapping = {
            0: 'uint8',
            1: 'uint8',
            2: 'int8',
            3: 'uint16',
            4: 'int16',
            5: 'uint32',
            6: 'int32',
            7: 'float32',
            8: 'bool',
            9: 'string',
            10: 'array',
            11: 'uint64',
            12: 'int64',
            13: 'float64'
        }
        
        if value_type == 0:  # uint8
            return struct.unpack('<B', f.read(1))[0]
        elif value_type == 1:  # uint8
            return struct.unpack('<B', f.read(1))[0]
        elif value_type == 2:  # int8
            return struct.unpack('<b', f.read(1))[0]
        elif value_type == 3:  # uint16
            return struct.unpack('<H', f.read(2))[0]
        elif value_type == 4:  # int16
            return struct.unpack('<h', f.read(2))[0]
        elif value_type == 5:  # uint32
            return struct.unpack('<I', f.read(4))[0]
        elif value_type == 6:  # int32
            return struct.unpack('<i', f.read(4))[0]
        elif value_type == 7:  # float32
            return struct.unpack('<f', f.read(4))[0]
        elif value_type == 8:  # bool
            return struct.unpack('<?', f.read(1))[0]
        elif value_type == 9:  # string
            length = struct.unpack('<Q', f.read(8))[0]
            return f.read(length).decode('utf-8')
        elif value_type == 10:  # array
            length = struct.unpack('<Q', f.read(8))[0]
            array_type = struct.unpack('<I', f.read(4))[0]
            return [self._read_gguf_value(f, array_type) for _ in range(length)]
        elif value_type == 11:  # uint64
            return struct.unpack('<Q', f.read(8))[0]
        elif value_type == 12:  # int64
            return struct.unpack('<q', f.read(8))[0]
        elif value_type == 13:  # float64
            return struct.unpack('<d', f.read(8))[0]
        else:
            self.logger.warning(f"Unknown GGUF value type: {value_type}")
            return None
    
    def detect_gguf_files(self, directory: Path) -> list[Path]:
        """
        Detect GGUF files in a directory.
        
        Args:
            directory: Directory to search
            
        Returns:
            List of GGUF file paths
        """
        self.logger.info(f"Detecting GGUF files in: {directory}")
        
        if not directory.exists():
            self.logger.warning(f"Directory does not exist: {directory}")
            return []
        
        gguf_files = []
        for file_path in directory.rglob('*.gguf'):
            is_valid, _ = self.validate_gguf_file(file_path)
            if is_valid:
                gguf_files.append(file_path)
                self.logger.debug(f"Found valid GGUF file: {file_path}")
        
        self.logger.info(f"Found {len(gguf_files)} valid GGUF files")
        return gguf_files
    
    def get_model_info_from_gguf(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Extract model information from GGUF file.
        
        Args:
            file_path: Path to the GGUF file
            
        Returns:
            Dictionary with model information or None if invalid
        """
        is_valid, header = self.validate_gguf_file(file_path)
        
        if not is_valid or not header:
            return None
        
        # Extract common metadata fields
        metadata = header.metadata
        
        info = {
            'file_path': str(file_path),
            'file_size_bytes': file_path.stat().st_size,
            'gguf_version': header.version,
            'tensor_count': header.tensor_count,
            'architecture': metadata.get('general.architecture', 'unknown'),
            'quantization': metadata.get('general.quantization_version', 'unknown'),
            'context_length': metadata.get('llama.context_length', 0),
            'embedding_length': metadata.get('llama.embedding_length', 0),
            'block_count': metadata.get('llama.block_count', 0),
            'name': metadata.get('general.name', 'unknown'),
            'description': metadata.get('general.description', ''),
            'author': metadata.get('general.author', 'unknown'),
            'license': metadata.get('general.license', 'unknown')
        }
        
        return info
    
    def quick_validate(self, file_path: Path) -> bool:
        """
        Quick validation of GGUF file (magic number only).
        
        Args:
            file_path: Path to the GGUF file
            
        Returns:
            True if file appears to be valid GGUF, False otherwise
        """
        try:
            with open(file_path, 'rb') as f:
                magic = f.read(4)
                return magic == self.GGUF_MAGIC
        except Exception:
            return False


# Global validator instance
_validator = None


def get_gguf_validator() -> GGUFValidator:
    """
    Get global GGUF validator instance.
    
    Returns:
        GGUFValidator instance
    """
    global _validator
    if _validator is None:
        _validator = GGUFValidator()
    return _validator


# Example usage and testing
if __name__ == "__main__":
    # Test GGUF validator
    print("Testing GGUF Validator...")
    
    validator = get_gguf_validator()
    
    # Test with a placeholder file
    test_file = Path(__file__).parent.parent / 'test_placeholder.gguf'
    
    # Create a test file with invalid GGUF format
    with open(test_file, 'wb') as f:
        f.write(b'INVALID')
    
    print(f"\nTesting with invalid file: {test_file}")
    is_valid, header = validator.validate_gguf_file(test_file)
    print(f"Valid: {is_valid}")
    
    # Test quick validation
    is_quick_valid = validator.quick_validate(test_file)
    print(f"Quick valid: {is_quick_valid}")
    
    # Clean up
    test_file.unlink()
    
    # Test detection in directory
    models_dir = Path.home() / '.local-ai' / 'models'
    if models_dir.exists():
        print(f"\nDetecting GGUF files in: {models_dir}")
        gguf_files = validator.detect_gguf_files(models_dir)
        print(f"Found {len(gguf_files)} GGUF files")
        for gguf_file in gguf_files:
            print(f"  - {gguf_file.name}")
    else:
        print(f"\nModels directory does not exist: {models_dir}")
    
    print("\nGGUF validator test completed!")
