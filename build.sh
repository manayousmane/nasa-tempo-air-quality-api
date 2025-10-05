#!/bin/bash
# Build script for Render
echo "🔧 Build process starting..."

# Upgrade pip with retries
python -m pip install --upgrade pip setuptools wheel --no-cache-dir

# Install dependencies with specific options for Render
#!/bin/bash
# Build script for Render deployment

echo "🔧 Installing dependencies with pre-compiled wheels..."

# Force use of pre-compiled wheels and avoid compilation
pip install --upgrade pip setuptools wheel
pip install --only-binary=all --prefer-binary -r requirements.txt

echo "✅ Dependencies installed successfully"

echo "✅ Build completed successfully"
