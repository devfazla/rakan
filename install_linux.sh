#!/bin/bash
# RAKAN Installation Script for Linux and macOS
# This script adds RAKAN to your system PATH

set -e

echo "===================================="
echo "RAKAN Installation Script"
echo "===================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
RAKAN_DIR="$SCRIPT_DIR"

echo "RAKAN Directory: $RAKAN_DIR"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "Python found:"
python3 --version
echo ""

# Check if rakan is already in PATH
if command -v rakan &> /dev/null; then
    echo "RAKAN is already in PATH"
    which rakan
    echo ""
    read -p "Do you want to reinstall RAKAN? (y/n): " choice
    if [[ ! "$choice" =~ ^[Yy]$ ]]; then
        echo "Installation cancelled"
        exit 0
    fi
fi

# Determine the installation directory
INSTALL_DIR="$HOME/.local/bin"
mkdir -p "$INSTALL_DIR"

echo "Creating RAKAN wrapper at: $INSTALL_DIR/rakan"

# Create the shell script wrapper
cat > "$INSTALL_DIR/rakan" << EOF
#!/bin/bash
python3 "$RAKAN_DIR/cli/main.py" "\$@"
EOF

chmod +x "$INSTALL_DIR/rakan"

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create wrapper file"
    exit 1
fi

echo "Wrapper file created successfully"
echo ""

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "Adding ~/.local/bin to PATH..."
    
    # Detect shell configuration file
    SHELL_CONFIG=""
    if [ -n "$ZSH_VERSION" ]; then
        SHELL_CONFIG="$HOME/.zshrc"
    elif [ -n "$BASH_VERSION" ]; then
        SHELL_CONFIG="$HOME/.bashrc"
    fi
    
    if [ -z "$SHELL_CONFIG" ]; then
        SHELL_CONFIG="$HOME/.profile"
    fi
    
    echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$SHELL_CONFIG"
    echo "PATH added to $SHELL_CONFIG"
    echo ""
    echo "IMPORTANT: Run 'source $SHELL_CONFIG' or restart your terminal for changes to take effect"
else
    echo "~/.local/bin is already in PATH"
fi

echo ""
echo "===================================="
echo "Installation Complete!"
echo "===================================="
echo ""
echo "To use RAKAN:"
echo "1. Run: source $SHELL_CONFIG (or restart your terminal)"
echo "2. Run: rakan --help"
echo ""
echo "Wrapper file location: $INSTALL_DIR/rakan"
echo ""