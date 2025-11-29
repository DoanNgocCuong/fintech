#!/bin/bash

echo "Starting Scoring 7 Metrics Dashboard API Server..."
echo ""

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ -f ".venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "Virtual environment not found. Using system Python."
fi

echo ""
echo "Starting FastAPI server on http://localhost:8000"
echo "Press Ctrl+C to stop the server"
echo ""

python app.py --host 0.0.0.0 --port 8000

