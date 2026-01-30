#!/bin/bash

# Quick build script for PyNigiri

set -e

echo "==================================="
echo "PyNigiri Build Script"
echo "==================================="
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d'.' -f1,2)
echo "Python version: $PYTHON_VERSION"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "Error: This script must be run from the python/ directory"
    exit 1
fi

# Parse command line arguments
MODE="install"
if [ "$1" = "dev" ] || [ "$1" = "develop" ]; then
    MODE="develop"
elif [ "$1" = "clean" ]; then
    echo "Cleaning build artifacts..."
    rm -rf build/ dist/ *.egg-info/
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    echo "Clean complete!"
    exit 0
fi

echo ""
echo "Build mode: $MODE"
echo ""

# Install dependencies
echo "Installing build dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install scikit-build-core pybind11 numpy

# Build and install
if [ "$MODE" = "develop" ]; then
    echo ""
    echo "Installing in development mode..."
    python3 -m pip install -e . --verbose
else
    echo ""
    echo "Installing..."
    python3 -m pip install . --verbose
fi

# Test import
echo ""
echo "Testing import..."
python3 -c "import pynigiri; print('✓ PyNigiri imported successfully'); print(f'  Version: {pynigiri.__version__}')"

echo ""
echo "==================================="
echo "Build complete!"
echo "==================================="
echo ""
echo "Usage:"
echo "  import pynigiri as ng"
echo ""
echo "Next steps:"
echo "  - Run examples: python examples/basic_routing.py"
echo "  - Run tests: pytest tests/"
echo "  - Read docs: less README.md"
echo ""
