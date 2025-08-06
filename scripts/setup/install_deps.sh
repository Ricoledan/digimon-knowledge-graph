#!/bin/bash
# Install Python dependencies based on available tools

echo "Installing Python dependencies..."
echo "==================================="

# Function to activate virtual environment
activate_venv() {
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        return 0
    elif [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        return 0
    fi
    return 1
}

# Check if we're in a Nix shell
if [ -n "$IN_NIX_SHELL" ]; then
    echo "[OK] Running in Nix shell - dependencies are already available"
    exit 0
fi

# Check for Poetry
if command -v poetry &> /dev/null && [ -f "pyproject.toml" ]; then
    echo "Installing Using Poetry to install dependencies..."
    poetry install
    echo "[OK] Dependencies installed with Poetry"
    echo "Note: Run 'poetry shell' to activate the environment"
    exit 0
fi

# Check for existing virtual environment
if activate_venv; then
    echo "Installing Using existing virtual environment..."
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "[OK] Dependencies installed in virtual environment"
    exit 0
fi

# Check for pyenv
if command -v pyenv &> /dev/null; then
    echo "Installing Using pyenv..."
    PYTHON_VERSION="3.11.8"
    
    if ! pyenv versions | grep -q "$PYTHON_VERSION"; then
        echo "Installing Python $PYTHON_VERSION..."
        pyenv install "$PYTHON_VERSION"
    fi
    
    pyenv local "$PYTHON_VERSION"
    python -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "[OK] Dependencies installed with pyenv + venv"
    exit 0
fi

# Fallback to system Python
if command -v python3 &> /dev/null; then
    echo "Installing Using system Python..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "[OK] Dependencies installed with system Python"
    echo "Note: Run 'source venv/bin/activate' to activate the environment"
    exit 0
fi

echo "ERROR: No suitable Python installation found"
exit 1