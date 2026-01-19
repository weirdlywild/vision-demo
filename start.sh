#!/bin/bash

echo "========================================"
echo "DIY Repair Diagnosis API"
echo "========================================"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo ""
    echo "Please create a .env file with your OpenAI API key:"
    echo "  1. Copy .env.example to .env"
    echo "  2. Edit .env and add your OpenAI API key"
    echo ""
    exit 1
fi

echo "Starting server..."
echo ""
echo "Web Interface: http://localhost:8000"
echo "API Docs:      http://localhost:8000/docs"
echo ""

# Activate virtual environment if it exists
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
fi

# Start the server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
