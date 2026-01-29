#!/bin/bash
set -e

# VLLMoni Uninstallation Script

USER_CONFIG_DIR="${HOME}/.vllmoni"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Uninstall vllmoni via pip
uninstall_vllmoni() {
    echo_info "Uninstalling vllmoni..."
    
    if pip3 show vllmoni &> /dev/null; then
        pip3 uninstall -y vllmoni
        echo_info "vllmoni uninstalled successfully"
    else
        echo_warning "vllmoni is not installed via pip"
    fi
}

# Remove user configuration directory
remove_user_config() {
    if [ -d "${USER_CONFIG_DIR}" ]; then
        echo ""
        echo_warning "This will delete your configuration directory: ${USER_CONFIG_DIR}"
        echo_warning "This includes all custom model configurations and logs."
        echo ""
        read -p "Do you want to remove the configuration directory? (y/N): " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "${USER_CONFIG_DIR}"
            echo_info "Configuration directory removed"
        else
            echo_info "Configuration directory preserved at: ${USER_CONFIG_DIR}"
            echo_info "You can manually remove it later if needed"
        fi
    else
        echo_info "No configuration directory found"
    fi
}

# Main uninstallation flow
main() {
    echo ""
    echo "========================================"
    echo "  VLLMoni Uninstallation Script"
    echo "========================================"
    echo ""
    
    uninstall_vllmoni
    
    echo ""
    remove_user_config
    
    echo ""
    echo "========================================"
    echo_info "Uninstallation completed!"
    echo "========================================"
    echo ""
    echo "Note: PATH modifications in your shell config files"
    echo "      (.bashrc, .zshrc, etc.) were not removed."
    echo "      You can manually remove them if desired."
    echo ""
}

main
