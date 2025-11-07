#!/bin/bash
# Launch ReaperVC
# Voice control for REAPER DAW

cd "$(dirname "$0")"

echo "=========================================="
echo "  ReaperVC - Voice Control for REAPER"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
	echo "[ERROR] Virtual environment not found"
	echo "Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
	exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Run ReaperVC
python3 src/reapervc.py

deactivate
