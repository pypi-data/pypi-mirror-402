#!/bin/bash
set -e

# VLLMoni Installation Script
# This script installs vllmoni system-wide and sets up user configuration directory

VERSION="${VERSION:-latest}"
INSTALL_DIR="/usr/local/bin"
USER_CONFIG_DIR="${HOME}/.vllmoni"
GITHUB_REPO="uhh-hcds/vllmonitor"
INSTALL_METHOD="${INSTALL_METHOD:-pypi}"  # pypi or github

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

# Check if Python 3.12+ is available
check_python() {
    echo_info "Checking Python version..."
    if ! command -v python3 &> /dev/null; then
        echo_error "Python 3 is not installed. Please install Python 3.12 or higher."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 12 ]); then
        echo_error "Python 3.12 or higher is required. Found: Python $PYTHON_VERSION"
        exit 1
    fi
    
    echo_info "Python $PYTHON_VERSION detected"
}

# Check if pip is available
check_pip() {
    echo_info "Checking pip..."
    if ! command -v pip3 &> /dev/null; then
        echo_error "pip3 is not installed. Please install pip3."
        exit 1
    fi
}

# Check if Docker is installed
check_docker() {
    echo_info "Checking Docker..."
    if ! command -v docker &> /dev/null; then
        echo_warning "Docker is not installed. VLLMoni requires Docker to run containers."
        echo_warning "Please install Docker from: https://docs.docker.com/get-docker/"
    else
        echo_info "Docker is installed"
    fi
}

# Install vllmoni via pip or from GitHub
install_vllmoni() {
    echo_info "Installing vllmoni..."
    
    if [ "$INSTALL_METHOD" = "github" ]; then
        # Install from GitHub repository
        echo_info "Installing from GitHub repository..."
        
        if [ "$VERSION" = "latest" ]; then
            python -m pip install --user "git+https://github.com/${GITHUB_REPO}.git"
        else
            python -m pip install --user "git+https://github.com/${GITHUB_REPO}.git@${VERSION}"
        fi
    else
        # Install from PyPI
        echo_info "Installing from PyPI..."
        
        if [ "$VERSION" = "latest" ]; then
            # Try PyPI first, fallback to GitHub if not available
            if ! python -m pip install --user vllmoni; then
                echo_warning "Package not found on PyPI, installing from GitHub..."
                INSTALL_METHOD="github"
                install_vllmoni
                return
            fi
        else
            if ! python -m pip install --user "vllmoni==${VERSION}"; then
                echo_warning "Version ${VERSION} not found on PyPI, trying GitHub..."
                INSTALL_METHOD="github"
                install_vllmoni
                return
            fi
        fi
    fi
    
    echo_info "vllmoni installed successfully"
}

# Set up user configuration directory
setup_user_config() {
    echo_info "Setting up user configuration directory at ${USER_CONFIG_DIR}..."
    
    # Create user config directory structure
    mkdir -p "${USER_CONFIG_DIR}/conf/model"
    mkdir -p "${USER_CONFIG_DIR}/logs"
    
    # Create a README in the user config directory
    cat > "${USER_CONFIG_DIR}/README.md" << 'EOF'
# VLLMoni User Configuration

This directory contains your personal VLLMoni configurations.

## Directory Structure

- `conf/model/` - Custom model configurations (YAML files)
- `logs/` - Application logs

## Adding Custom Models

To add a custom model configuration:

1. Create a new YAML file in `conf/model/`, e.g., `my_model.yaml`
2. Define your model configuration:

```yaml
model_name: "your-org/your-model-name"
model_name_short: "my-model"
gpu_memory_utilization: 0.5
temperature: 0
max_tokens: 1000
max_model_len: 40000
tensor_parallel_size: 1
```

3. Use it with: `vllmoni run model=my_model`

## Environment Variables

You can set the following environment variables:

- `VLLMONI_CONFIG_PATH`: Override the config directory path (default: ~/.vllmoni/conf)
- `VLLMONI_DB_PATH`: Override the database path (default: ~/.vllmoni/vllmoni.db)

## Documentation

For more information, visit: https://github.com/uhh-hcds/vllmonitor
EOF
    
    # Create example model config
    cat > "${USER_CONFIG_DIR}/conf/model/example.yaml" << 'EOF'
# Example custom model configuration
# Copy this file and modify it for your own models

model_name: "meta-llama/Meta-Llama-3.1-8B-Instruct"
model_name_short: "example-model"
gpu_memory_utilization: 0.5
temperature: 0
max_tokens: 1000
max_model_len: 40000
tensor_parallel_size: 1
EOF
    
    echo_info "User configuration directory created at ${USER_CONFIG_DIR}"
}

# Add vllmoni to PATH if not already there
setup_path() {
    echo_info "Checking PATH configuration..."
    
    # Get the Python user base bin directory
    USER_BIN_DIR=$(python3 -m site --user-base)/bin
    
    # Check if it's in PATH
    if [[ ":$PATH:" != *":${USER_BIN_DIR}:"* ]]; then
        echo_warning "Python user bin directory is not in PATH: ${USER_BIN_DIR}"
        echo_info "Adding to PATH in shell configuration..."
        
        # Detect shell and add to appropriate config file
        if [ -n "$BASH_VERSION" ]; then
            SHELL_RC="${HOME}/.bashrc"
        elif [ -n "$ZSH_VERSION" ]; then
            SHELL_RC="${HOME}/.zshrc"
        else
            SHELL_RC="${HOME}/.profile"
        fi
        
        # Add to shell config if not already there
        if ! grep -q "export PATH=\"${USER_BIN_DIR}:\$PATH\"" "${SHELL_RC}" 2>/dev/null; then
            echo "" >> "${SHELL_RC}"
            echo "# Added by vllmoni installer" >> "${SHELL_RC}"
            echo "export PATH=\"${USER_BIN_DIR}:\$PATH\"" >> "${SHELL_RC}"
            echo_info "Added to ${SHELL_RC}"
            echo_warning "Please run: source ${SHELL_RC}"
        fi
    else
        echo_info "PATH is correctly configured"
    fi
}

# Initialize database
init_database() {
    echo_info "Initializing vllmoni database..."
    
    # Export environment variable for database location
    export VLLMONI_DB_PATH="${USER_CONFIG_DIR}/vllmoni.db"
    
    # Try to run init command
    if command -v vllmoni &> /dev/null; then
        vllmoni init || echo_warning "Database initialization will be done on first run"
    else
        echo_warning "vllmoni command not yet in PATH. Database will be initialized on first run."
    fi
}

# Main installation flow
main() {
    echo ""
    echo "========================================"
    echo "  VLLMoni Installation Script"
    echo "========================================"
    echo ""
    
    check_python
    check_pip
    check_docker
    
    echo ""
    install_vllmoni
    
    echo ""
    setup_user_config
    
    echo ""
    setup_path
    
    echo ""
    init_database
    
    echo ""
    echo "========================================"
    echo_info "Installation completed successfully!"
    echo "========================================"
    echo ""
    echo "Next steps:"
    echo "  1. Reload your shell or run: source ~/.bashrc (or ~/.zshrc)"
    echo "  2. Run: vllmoni init"
    echo "  3. Run: vllmoni run model=llama_3_1"
    echo ""
    echo "Custom model configurations: ${USER_CONFIG_DIR}/conf/model/"
    echo "Documentation: https://github.com/uhh-hcds/vllmonitor"
    echo ""
}

main
