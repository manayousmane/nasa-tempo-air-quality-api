#!/bin/bash
# Render deployment script
echo "🚀 Starting NASA TEMPO Air Quality API on Render..."

# Install any missing dependencies
pip install --upgrade pip

# Start the application
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1