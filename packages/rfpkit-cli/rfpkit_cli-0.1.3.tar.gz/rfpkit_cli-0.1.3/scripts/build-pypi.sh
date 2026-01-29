#!/bin/bash
set -e

echo "🔧 Building RFP Kit CLI for PyPI..."

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found. Please run this script from the project root."
    exit 1
fi

# Install build dependencies
echo "📦 Installing build dependencies..."
pip install --upgrade pip build twine hatch

# Install project dependencies for testing
echo "📦 Installing project dependencies..."
pip install typer rich httpx[socks] platformdirs readchar truststore

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ src/rfpkit_cli.egg-info/

# Verify package structure
echo "🔍 Verifying package structure..."
if [ -f "src/rfpkit_cli/__init__.py" ]; then
    echo "✅ Package structure looks good"
    echo "✅ Found __init__.py with version: $(grep '__version__' src/rfpkit_cli/__init__.py | cut -d'"' -f2)"
else
    echo "❌ Error: Package structure is incorrect"
    exit 1
fi

# Build the package
echo "🏗️  Building package..."
python -m build

# Check the built package
echo "✅ Checking built package..."
python -m twine check dist/*

# List built files
echo "📋 Built files:"
ls -la dist/

echo ""
echo "🎉 Build completed successfully!"
echo ""
echo "To test locally:"
echo "  pip install dist/rfpkit_cli-*.whl"
echo "  rfpkit --help"
echo ""
echo "To publish to PyPI (requires API token):"
echo "  python -m twine upload dist/*"
echo ""
echo "Or create a git tag and push to trigger automatic PyPI publish:"
echo "  git tag v0.1.0"
echo "  git push origin v0.1.0"