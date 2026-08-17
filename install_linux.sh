#!/bin/bash
# RAKAN Installation Script for Linux and macOS
# This script adds RAKAN to your system PATH

set -e

# Check for force mode
FORCE_MODE=0
if [ "$1" = "--force" ] || [ "$1" = "-f" ]; then
    FORCE_MODE=1
fi

if [ $FORCE_MODE -eq 1 ]; then
    echo "Force mode enabled - proceeding with reinstallation"
fi

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

# Check for existing installation
if [ -f "$HOME/.rakan/.installation_info" ]; then
    if [ $FORCE_MODE -eq 0 ]; then
        echo "===================================="
        echo "Existing Installation Detected"
        echo "===================================="
        echo ""
        echo "RAKAN appears to be already installed."
        echo ""
        EXISTING_INSTALL=$(cat "$HOME/.rakan/.installation_info")
        echo "Previous installation: $EXISTING_INSTALL"
        echo "Current directory: $RAKAN_DIR"
        echo ""
        
        # Check if the installation directory exists
        if [ -d "$EXISTING_INSTALL" ]; then
            if [ "$RAKAN_DIR" = "$EXISTING_INSTALL" ]; then
                echo "This is the same installation directory."
                echo "No installation needed."
                echo ""
                echo "To reinstall, first uninstall with:"
                echo "  rakan uninstall"
                echo "Or reinstall with force flag:"
                echo "  ./install_linux.sh --force"
                exit 0
            else
                echo "Different installation directory detected."
                echo ""
                echo "Options:"
                echo "  1. Cancel and use existing installation"
                echo "  2. Reinstall this location"
                echo "  3. Uninstall existing and install new"
                echo ""
                read -p "Your choice (1/2/3): " choice
                
                if [ "$choice" = "1" ]; then
                    echo "Installation cancelled."
                    echo "Using existing installation at: $EXISTING_INSTALL"
                    exit 0
                elif [ "$choice" = "2" ]; then
                    echo "Proceeding with reinstallation..."
                    echo "This will overwrite the existing installation."
                elif [ "$choice" = "3" ]; then
                    echo "Please uninstall existing installation first:"
                    echo "  rakan uninstall"
                    echo "Then run this installation again."
                    exit 0
                else
                    echo "Invalid choice. Installation cancelled."
                    exit 0
                fi
            fi
        else
            echo "Previous installation directory not found."
            echo "This may be a corrupted installation."
            echo ""
            echo "Options:"
            echo "  1. Clean up and reinstall this location"
            echo "  2. Cancel and investigate"
            echo ""
            read -p "Your choice (1/2): " choice
            
            if [ "$choice" = "1" ]; then
                echo "Cleaning up corrupted installation marker..."
                rm "$HOME/.rakan/.installation_info"
                echo "[OK] Removed corrupted marker"
                echo "Proceeding with installation..."
            elif [ "$choice" = "2" ]; then
                echo "Installation cancelled."
                echo "Please check: $EXISTING_INSTALL"
                exit 0
            else
                echo "Invalid choice. Installation cancelled."
                exit 0
            fi
        fi
    else
        echo "Force mode enabled - skipping duplicate check"
        EXISTING_INSTALL=$(cat "$HOME/.rakan/.installation_info")
        echo "Previous installation: $EXISTING_INSTALL"
        echo "Proceeding with reinstallation..."
        echo ""
    fi
else
    # Check if data directory exists but no marker
    if [ -d "$HOME/.rakan/models" ]; then
        echo "Found existing RAKAN data directory."
        echo "This contains your models, logs, and configuration."
        echo ""
        echo "This is not a duplicate installation - the data directory"
        echo "is shared across installations. This is safe to continue."
        echo ""
        echo "Proceeding with installation..."
        echo "Your existing data will be preserved."
        echo ""
    fi
fi

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

# Create installation marker
mkdir -p "$HOME/.rakan"
echo "$RAKAN_DIR" > "$HOME/.rakan/.installation_info"
echo "Installation marker created: $HOME/.rakan/.installation_info"
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