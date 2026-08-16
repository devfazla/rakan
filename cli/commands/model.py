"""
Local AI Platform - Model CLI Commands
CLI commands for model management.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agent.core import get_logger
from models import get_model_manager, get_model_registry, get_hardware_detector


def list_models(args):
    """
    List available and/or installed models.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    logger = get_logger(__name__)
    manager = get_model_manager()
    
    logger.info("Listing models...")
    
    available_only = getattr(args, 'available', False)
    installed_only = getattr(args, 'installed', False)
    
    models = manager.list_models(installed_only=installed_only)
    
    print("\n" + "="*70)
    print("MODEL LIST")
    print("="*70 + "\n")
    
    if not available_only:
        print(f"Installed Models: {models['installed_count']}")
        if models['installed_count'] > 0:
            for model in models['installed']:
                print(f"  • {model['name']}")
                print(f"    Display: {model['display_name']}")
                print(f"    Size: {model['file_size_gb']} GB")
                print(f"    Installed: {model['installed_at']}")
                print(f"    Checksum verified: {model['checksum_verified']}")
                print()
        else:
            print("  No models installed")
            print("  Install models using: rakan model install <model-name>")
            print()
    
    if not installed_only:
        print(f"Available Models: {models['available_count']}")
        for model in models['available']:
            status = "[INSTALLED]" if model['installed'] else "[AVAILABLE]"
            print(f"  {status} {model['name']}")
            print(f"    Display: {model['display_name']}")
            print(f"    Parameters: {model['parameters']}")
            print(f"    Quantization: {model['quantization']}")
            print(f"    Size: {model['file_size_gb']} GB")
            print(f"    RAM required: {model['ram_required_gb']} GB")
            print()
    
    print("="*70 + "\n")
    
    return 0


def install_model(args):
    """
    Install a model.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    logger = get_logger(__name__)
    manager = get_model_manager()
    registry = get_model_registry()
    
    model_name = args.model_name
    custom_url = getattr(args, 'url', None)
    force = getattr(args, 'force', False)
    
    logger.info(f"Installing model: {model_name}")
    
    # Check if model exists in registry
    model_info = registry.get_model(model_name)
    if not model_info and not custom_url:
        logger.error(f"Model {model_name} not found in registry")
        print(f"Error: Model '{model_name}' not found in registry")
        print("Use 'rakan model list' to see available models")
        return 1
    
    # Show model information
    if model_info:
        print(f"\nInstalling: {model_info.display_name}")
        print(f"Parameters: {model_info.parameters}")
        print(f"Quantization: {model_info.quantization}")
        print(f"File size: {model_info.file_size_gb} GB")
        print(f"RAM required: {model_info.ram_required_gb} GB")
        print()
    
    # Perform installation
    import asyncio
    
    async def install_with_progress():
        def progress_callback(progress):
            percentage = progress.percentage
            downloaded_mb = progress.downloaded_bytes / (1024**2)
            total_mb = progress.total_bytes / (1024**2)
            speed_mbps = progress.speed_mbps
            eta = progress.eta_seconds
            
            print(f"\rProgress: {percentage:.1f}% | {downloaded_mb:.1f}/{total_mb:.1f} MB | "
                  f"{speed_mbps:.1f} MB/s | ETA: {eta:.0f}s", end='', flush=True)
        
        result = await manager.install_model_async(
            model_name=model_name,
            url=custom_url,
            force=force,
            progress_callback=progress_callback
        )
        
        print()  # New line after progress
        return result
    
    result = asyncio.run(install_with_progress())
    
    if result['success']:
        print(f"✓ Model '{model_name}' installed successfully")
        if result.get('file_path'):
            print(f"  Location: {result['file_path']}")
        return 0
    else:
        print(f"✗ Installation failed: {result['error']}")
        return 1


def remove_model(args):
    """
    Remove an installed model.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    logger = get_logger(__name__)
    manager = get_model_manager()
    
    model_name = args.model_name
    force = getattr(args, 'force', False)
    
    logger.info(f"Removing model: {model_name}")
    
    # Check if model is installed
    if model_name not in manager.installed_models:
        print(f"Error: Model '{model_name}' is not installed")
        return 1
    
    # Get model info for display
    model_info = manager.get_model_info(model_name)
    if model_info:
        print(f"\nRemoving: {model_info['display_name']}")
        print(f"Size: {model_info['file_size_gb']} GB")
        print()
    
    # Confirm removal unless forced
    if not force:
        response = input(f"Are you sure you want to remove '{model_name}'? (y/N): ")
        if response.lower() != 'y':
            print("Removal cancelled")
            return 0
    
    # Remove model
    if manager.remove_model(model_name, force=True):
        print(f"✓ Model '{model_name}' removed successfully")
        return 0
    else:
        print(f"✗ Failed to remove model '{model_name}'")
        return 1


def use_model(args):
    """
    Select a model as the default.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    logger = get_logger(__name__)
    manager = get_model_manager()
    
    model_name = args.model_name
    
    logger.info(f"Selecting model: {model_name}")
    
    # Select model
    result = manager.select_model(model_name)
    
    if result['success']:
        print(f"✓ {result['message']}")
        if result['model_info']:
            print(f"  Model: {result['model_info']['display_name']}")
            print(f"  Parameters: {result['model_info']['parameters']}")
            print(f"  RAM required: {result['model_info']['ram_required_gb']} GB")
        return 0
    else:
        print(f"✗ {result['message']}")
        return 1


def model_info(args):
    """
    Show detailed information about a model.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    logger = get_logger(__name__)
    manager = get_model_manager()
    registry = get_model_registry()
    
    model_name = args.model_name
    
    logger.info(f"Getting model info: {model_name}")
    
    # Get model information
    model_info = manager.get_model_info(model_name)
    
    if not model_info:
        print(f"Error: Model '{model_name}' not found")
        return 1
    
    print("\n" + "="*70)
    print("MODEL INFORMATION")
    print("="*70 + "\n")
    
    print(f"Name:              {model_info['name']}")
    print(f"Display Name:      {model_info['display_name']}")
    print(f"Description:       {model_info['description']}")
    print(f"Parameters:        {model_info['parameters']}")
    print(f"Quantization:      {model_info['quantization']}")
    print(f"Architecture:      {model_info['architecture']}")
    print(f"Context Length:    {model_info['context_length']}")
    print(f"File Size:         {model_info['file_size_gb']} GB")
    print(f"RAM Required:      {model_info['ram_required_gb']} GB")
    print(f"Recommended RAM:   {model_info['recommended_ram_gb']} GB")
    print(f"Use Case:          {model_info['use_case']}")
    print(f"Language:          {model_info['language']}")
    print(f"License:           {model_info['license']}")
    print(f"Tags:              {', '.join(model_info['tags'])}")
    print(f"Enabled:           {model_info['enabled']}")
    print(f"Installed:         {model_info['installed']}")
    
    if model_info['installed']:
        print(f"File Path:         {model_info['file_path']}")
        print(f"Installed At:      {model_info['installed_at']}")
        print(f"Checksum Verified: {model_info['checksum_verified']}")
    
    print(f"\nDownload URL:      {model_info['download_url']}")
    print(f"Checksum:           {model_info['checksum']}")
    
    # Show hardware compatibility
    detector = get_hardware_detector()
    hardware_info = detector.detect_hardware()
    can_run = detector.can_run_model(model_name, hardware_info)
    
    print(f"\nHardware Compatibility:")
    print(f"  Can run on current hardware: {can_run}")
    
    if not can_run:
        print(f"  Current RAM: {hardware_info['available_memory_gb']} GB available")
        print(f"  Required RAM: {model_info['ram_required_gb']} GB")
    
    print("\n" + "="*70 + "\n")
    
    return 0