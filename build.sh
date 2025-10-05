#!/bin/bash
# Build script for Render
echo "🔧 Build process starting..."

# Upgrade pip with retries
python -m pip install --upgrade pip setuptools wheel --no-cache-dir

# Install dependencies with specific options for Render
#!/bin/bash
# Robust build script for Render deployment
set -e

echo "🔧 Setting up build environment..."

# Update system packages and build tools
echo "📦 Upgrading pip and build tools..."
python -m pip install --upgrade pip
pip install --upgrade setuptools wheel

# Set environment variables for compilation
export PIP_NO_CACHE_DIR=1
export PIP_DISABLE_PIP_VERSION_CHECK=1

# Install dependencies with specific flags to avoid compilation issues
echo "📚 Installing dependencies..."
pip install --no-deps setuptools wheel
pip install --prefer-binary --no-build-isolation -r requirements.txt

echo "✅ Build completed successfully!"

echo "✅ Build completed successfully"
