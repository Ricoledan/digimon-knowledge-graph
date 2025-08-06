#!/bin/bash
# Check if all requirements are installed

echo "Checking system requirements..."
echo "================================="

MISSING_DEPS=0

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo "[OK] Python: $PYTHON_VERSION"
else
    echo "ERROR: Python 3 is not installed"
    MISSING_DEPS=$((MISSING_DEPS + 1))
fi

# Check Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,$//')
    echo "[OK] Docker: $DOCKER_VERSION"
else
    echo "ERROR: Docker is not installed"
    MISSING_DEPS=$((MISSING_DEPS + 1))
fi

# Check Docker Compose
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version | awk '{print $3}' | sed 's/,$//')
    echo "[OK] Docker Compose: $COMPOSE_VERSION"
else
    echo "ERROR: Docker Compose is not installed"
    MISSING_DEPS=$((MISSING_DEPS + 1))
fi

# Check optional tools
echo ""
echo "Optional tools:"

if command -v nix &> /dev/null; then
    NIX_VERSION=$(nix --version | awk '{print $3}')
    echo "[OK] Nix: $NIX_VERSION"
else
    echo "WARNING: Nix: Not installed (optional)"
fi

if command -v poetry &> /dev/null; then
    POETRY_VERSION=$(poetry --version | awk '{print $3}')
    echo "[OK] Poetry: $POETRY_VERSION"
else
    echo "WARNING: Poetry: Not installed (optional)"
fi

if command -v pyenv &> /dev/null; then
    PYENV_VERSION=$(pyenv --version | awk '{print $2}')
    echo "[OK] pyenv: $PYENV_VERSION"
else
    echo "WARNING: pyenv: Not installed (optional)"
fi

echo ""
if [ $MISSING_DEPS -eq 0 ]; then
    echo "All required dependencies are installed!"
    exit 0
else
    echo "ERROR: Missing $MISSING_DEPS required dependencies"
    exit 1
fi