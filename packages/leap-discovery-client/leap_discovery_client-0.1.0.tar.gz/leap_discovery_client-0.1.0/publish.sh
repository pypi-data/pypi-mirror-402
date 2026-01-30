#!/bin/bash
# Script to build and publish leap-discovery-client to PyPI
#
# Usage:
#   ./publish.sh [test|prod]
#
# Before publishing:
# 1. Update version in pyproject.toml
# 2. Update CHANGELOG if needed
# 3. Commit and tag the release
# 4. Run: ./publish.sh test  (to test on TestPyPI)
# 5. Run: ./publish.sh prod  (to publish to PyPI)

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "Error: pyproject.toml not found. Are you in the client package directory?"
    exit 1
fi

# Determine which PyPI to use
if [ "$1" == "test" ]; then
    REPOSITORY="--repository testpypi"
    echo "Publishing to TestPyPI..."
elif [ "$1" == "prod" ]; then
    REPOSITORY=""
    echo "Publishing to PyPI (production)..."
else
    echo "Usage: $0 [test|prod]"
    echo "  test - Publish to TestPyPI"
    echo "  prod - Publish to PyPI (production)"
    exit 1
fi

# Check for required tools
if ! command -v python &> /dev/null; then
    echo "Error: python not found"
    exit 1
fi

# Install build tools
echo "Installing build tools..."
python -m pip install --upgrade build twine

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info

# Build the package
echo "Building package..."
python -m build

# Check the build
echo "Checking built package..."
python -m twine check dist/*

# Upload
echo "Uploading to PyPI..."
if [ "$1" == "test" ]; then
    python -m twine upload $REPOSITORY dist/*
else
    echo "⚠️  WARNING: You are about to publish to PRODUCTION PyPI!"
    echo "Press Ctrl+C to cancel, or Enter to continue..."
    read
    python -m twine upload $REPOSITORY dist/*
fi

echo "✅ Package published successfully!"
echo ""
echo "Users can now install with:"
echo "  pip install leap-discovery-client"
echo "  pip install leap-discovery-client[pandas]"
