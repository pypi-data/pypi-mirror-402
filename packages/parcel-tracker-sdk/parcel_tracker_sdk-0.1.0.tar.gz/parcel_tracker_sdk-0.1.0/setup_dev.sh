#!/bin/bash
# Setup script for ParcelTracker SDK development environment

set -e

echo "Setting up ParcelTracker SDK development environment..."

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip3 install -e ".[dev]" --quiet

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

# Create examples directory if it doesn't exist
if [ ! -d "examples" ]; then
    mkdir -p examples
fi

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source .venv/bin/activate"
echo ""
echo "To run tests:"
echo "  pytest tests/ -v"
echo ""
echo "To run type checking:"
echo "  mypy src/parcel_tracker_sdk/"
echo ""
echo "To format code:"
echo "  black src/parcel_tracker_sdk/"
echo "  isort src/parcel_tracker_sdk/"
