#!/bin/bash

# Multi-Agent Betting System Setup Script

echo "=================================="
echo "Multi-Agent Betting System Setup"
echo "=================================="
echo ""

# Check Python
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
echo "✓ Python $PYTHON_VERSION found"

# Check Node.js
echo "Checking Node.js installation..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16 or higher."
    exit 1
fi
NODE_VERSION=$(node --version)
echo "✓ Node.js $NODE_VERSION found"

# Check npm
echo "Checking npm installation..."
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm."
    exit 1
fi
NPM_VERSION=$(npm --version)
echo "✓ npm $NPM_VERSION found"

echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install Python dependencies"
    exit 1
fi
echo "✓ Python dependencies installed"

echo ""
echo "Installing Node.js dependencies..."
cd scraper
npm install
if [ $? -ne 0 ]; then
    echo "❌ Failed to install Node.js dependencies"
    exit 1
fi
cd ..
echo "✓ Node.js dependencies installed"

echo ""
echo "Setting up configuration..."
if [ ! -f "config/.env" ]; then
    cp config/.env.example config/.env
    echo "✓ Created config/.env from template"
    echo "⚠️  Please edit config/.env and add your API keys!"
else
    echo "✓ config/.env already exists"
fi

echo ""
echo "Creating necessary directories..."
mkdir -p logs data
echo "✓ Directories created"

echo ""
echo "Making scripts executable..."
chmod +x run.py scheduler.py setup.sh
echo "✓ Scripts are now executable"

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Edit config/.env and add your API keys"
echo "2. Edit config/config.yaml to customize settings"
echo "3. Test the system: python run.py --test-notification"
echo "4. Run the system: python run.py"
echo "5. Start scheduler: python scheduler.py"
echo ""
echo "For detailed instructions, see README.md"
echo ""
