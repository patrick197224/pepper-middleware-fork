#!/usr/bin/env bash
# Automated setup for Human Detection Node
# Creates virtual environment, installs dependencies, downloads models
# Author: Siddharth Patni

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Download models
echo ""
echo "🧠 Downloading pre-trained models..."
cd models
bash download_models.sh
cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Activate the virtual environment:"
echo "      source venv/bin/activate"
echo ""
echo "   2. Test the detection script:"
echo "      python detect_human.py --method hog --camera 0"
echo ""
echo "   3. When using with Node-RED, make sure the venv is activated"
echo "      or update the Node-RED script to use: venv/bin/python3"
echo ""
