"""
Local AI Platform - Model Downloader
Handles model downloads with progress tracking and checksum verification.
"""

import sys
import hashlib
import asyncio
import aiohttp
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent.core import get_logger


@dataclass
class DownloadProgress:
    """Data class for download progress information."""
    downloaded_bytes: int
    total_bytes: int
    percentage: float
    speed_mbps: float
    eta_seconds: float


class ModelDownloader:
    """Downloads model files with progress tracking and checksum verification."""
    
    def __init__(self, timeout: int = 3600, chunk_size: int = 8192):
        """
        Initialize model downloader.
        
        Args:
            timeout: Download timeout in seconds
            chunk_size: Download chunk size in bytes
        """
        self.logger = get_logger(__name__)
        self.timeout = timeout
        self.chunk_size = chunk_size
    
    async def download_file(
        self,
        url: str,
        destination: Path,
        expected_checksum: Optional[str] = None,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None
    ) -> Dict[str, Any]:
        """
        Download a file with progress tracking and checksum verification.
        
        Args:
            url: URL to download from
            destination: Destination file path
            expected_checksum: Expected SHA256 checksum (format: sha256:hash)
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with download result
        """
        result = {
            'success': False,
            'downloaded_bytes': 0,
            'total_bytes': 0,
            'checksum_verified': False,
            'error': None,
            'destination': str(destination)
        }
        
        self.logger.info(f"Starting download: {url}")
        
        try:
            # Ensure destination directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Download file
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}: {response.reason}")
                    
                    # Get file size
                    total_bytes = int(response.headers.get('content-length', 0))
                    result['total_bytes'] = total_bytes
                    
                    self.logger.info(f"File size: {total_bytes / (1024**3):.2f} GB")
                    
                    # Initialize checksum calculation
                    sha256_hash = hashlib.sha256()
                    
                    # Download with progress tracking
                    downloaded_bytes = 0
                    start_time = asyncio.get_event_loop().time()
                    
                    with open(destination, 'wb') as f:
                        async for chunk in response.content.iter_chunked(self.chunk_size):
                            f.write(chunk)
                            sha256_hash.update(chunk)
                            downloaded_bytes += len(chunk)
                            
                            # Calculate progress
                            if progress_callback and total_bytes > 0:
                                elapsed = asyncio.get_event_loop().time() - start_time
                                speed_mbps = (downloaded_bytes / (1024**2)) / elapsed if elapsed > 0 else 0
                                eta_seconds = (total_bytes - downloaded_bytes) / (speed_mbps * 1024**2) if speed_mbps > 0 else 0
                                
                                progress = DownloadProgress(
                                    downloaded_bytes=downloaded_bytes,
                                    total_bytes=total_bytes,
                                    percentage=(downloaded_bytes / total_bytes) * 100 if total_bytes > 0 else 0,
                                    speed_mbps=speed_mbps,
                                    eta_seconds=eta_seconds
                                )
                                progress_callback(progress)
                    
                    result['downloaded_bytes'] = downloaded_bytes
                    
                    # Verify checksum if provided
                    if expected_checksum:
                        self.logger.info("Verifying checksum...")
                        actual_hash = sha256_hash.hexdigest()
                        
                        if expected_checksum.startswith('sha256:'):
                            expected_hash = expected_checksum.split(':', 1)[1]
                        else:
                            expected_hash = expected_checksum
                        
                        if actual_hash == expected_hash:
                            result['checksum_verified'] = True
                            self.logger.info("Checksum verified successfully")
                        else:
                            error_msg = f"Checksum mismatch: expected {expected_hash}, got {actual_hash}"
                            self.logger.error(error_msg)
                            result['error'] = error_msg
                            # Delete corrupted file
                            destination.unlink()
                            return result
                    
                    result['success'] = True
                    self.logger.info(f"Download completed: {destination}")
                    
        except asyncio.TimeoutError:
            error_msg = f"Download timeout after {self.timeout} seconds"
            self.logger.error(error_msg)
            result['error'] = error_msg
        except Exception as e:
            error_msg = f"Download failed: {str(e)}"
            self.logger.error(error_msg)
            result['error'] = error_msg
            # Clean up partial download
            if destination.exists():
                destination.unlink()
        
        return result
    
    def calculate_checksum(self, file_path: Path) -> Optional[str]:
        """
        Calculate SHA256 checksum of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA256 checksum string or None if calculation fails
        """
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256_hash.update(chunk)
            return f"sha256:{sha256_hash.hexdigest()}"
        except Exception as e:
            self.logger.error(f"Failed to calculate checksum: {e}")
            return None
    
    def verify_checksum(self, file_path: Path, expected_checksum: str) -> bool:
        """
        Verify file checksum.
        
        Args:
            file_path: Path to the file
            expected_checksum: Expected checksum (format: sha256:hash)
            
        Returns:
            True if checksum matches, False otherwise
        """
        actual_checksum = self.calculate_checksum(file_path)
        if not actual_checksum:
            return False
        
        if expected_checksum.startswith('sha256:'):
            expected_hash = expected_checksum.split(':', 1)[1]
        else:
            expected_hash = expected_checksum
        
        actual_hash = actual_checksum.split(':', 1)[1] if ':' in actual_checksum else actual_checksum
        
        return actual_hash == expected_hash
    
    async def download_with_retry(
        self,
        url: str,
        destination: Path,
        expected_checksum: Optional[str] = None,
        max_retries: int = 3,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None
    ) -> Dict[str, Any]:
        """
        Download file with retry logic.
        
        Args:
            url: URL to download from
            destination: Destination file path
            expected_checksum: Expected SHA256 checksum
            max_retries: Maximum number of retry attempts
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with download result
        """
        for attempt in range(max_retries):
            self.logger.info(f"Download attempt {attempt + 1}/{max_retries}")
            
            result = await self.download_file(url, destination, expected_checksum, progress_callback)
            
            if result['success']:
                return result
            
            self.logger.warning(f"Download attempt {attempt + 1} failed: {result['error']}")
            
            if attempt < max_retries - 1:
                # Wait before retry
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return result


# Global downloader instance
_downloader = None


def get_model_downloader(timeout: int = 3600, chunk_size: int = 8192) -> ModelDownloader:
    """
    Get global model downloader instance.
    
    Args:
        timeout: Download timeout in seconds
        chunk_size: Download chunk size in bytes
        
    Returns:
        ModelDownloader instance
    """
    global _downloader
    if _downloader is None:
        _downloader = ModelDownloader(timeout, chunk_size)
    return _downloader


# Example usage and testing
if __name__ == "__main__":
    # Test model downloader
    print("Testing Model Downloader...")
    
    downloader = get_model_downloader()
    
    # Test checksum calculation
    test_file = Path(__file__).parent / "test_file.txt"
    with open(test_file, 'w') as f:
        f.write("Test content for checksum calculation")
    
    checksum = downloader.calculate_checksum(test_file)
    print(f"\nCalculated checksum: {checksum}")
    
    # Test checksum verification
    is_valid = downloader.verify_checksum(test_file, checksum)
    print(f"Checksum verification: {is_valid}")
    
    # Test with wrong checksum
    is_valid = downloader.verify_checksum(test_file, "sha256:wronghash")
    print(f"Wrong checksum verification: {is_valid}")
    
    # Clean up
    test_file.unlink()
    
    print("\nModel downloader test completed!")
    print("Note: Actual download testing requires network access and valid URLs")