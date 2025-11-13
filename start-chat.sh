#!/bin/bash
# Start the betting system chat interface

echo "🎲 Starting Betting System Chat Interface..."
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating it..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Check for required environment file
if [ ! -f "config/.env" ]; then
    echo "❌ Error: config/.env not found"
    echo "Please create config/.env with your GOOGLE_API_KEY"
    exit 1
fi

# Check for data files
if [ ! -f "data/results.json" ]; then
    echo "⚠️  No recommendations found. You should run 'python run.py' first to generate betting recommendations."
    echo ""
    read -p "Would you like to run the betting system first? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python run.py
        echo ""
    fi
fi

# Start the chat
echo "✓ Starting chat interface..."
echo ""
python chat.py
