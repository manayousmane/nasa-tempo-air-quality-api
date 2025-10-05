#!/bin/bash
# Render deployment script for NASA TEMPO API (Simplified version)
echo "🚀 Starting NASA TEMPO Air Quality API on Render (Simplified)..."

# Use simplified main file to avoid dependency issues
exec python -m uvicorn simple_main:app --host 0.0.0.0 --port $PORT --workers 1