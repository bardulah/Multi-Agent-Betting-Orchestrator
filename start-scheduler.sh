#!/bin/bash
# Wrapper script to run the scheduler with proper venv activation

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
source venv/bin/activate

# Create necessary directories if they don't exist
mkdir -p data logs

# Run the scheduler
python scheduler.py "$@"
