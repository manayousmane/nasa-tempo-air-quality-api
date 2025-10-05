#!/bin/bash
# Render deployment script for NASA TEMPO API
echo "🚀 Starting NASA TEMPO Air Quality API on Render..."

# Upgrade pip and setuptools
python -m pip install --upgrade pip setuptools wheel

# Start the application with explicit Python path
exec python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1