#!/usr/bin/env bash
# Quick start script for development

set -euo pipefail

PORT="${PORT:-3600}"
GPU="${GPU:-0}"

echo "================================================"
echo "EasyOCR API - Quick Start"
echo "================================================"
echo ""

# Check if running in Docker or local
if [ "${DOCKER:-0}" == "1" ]; then
    echo "🐳 Starting with Docker..."
    if [ "${GPU}" == "1" ]; then
        echo "   GPU mode enabled"
        docker-compose -f docker-compose.gpu.yml up
    else
        echo "   CPU mode"
        docker-compose up
    fi
else
    echo "🐍 Starting local development server..."
    echo "   Port: $PORT"
    echo ""

    # Create venv if it doesn't exist
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi

    # Activate venv
    source venv/bin/activate

    # Install/update dependencies
    echo "Installing dependencies..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt

    echo ""
    echo "✅ Starting uvicorn on http://localhost:$PORT"
    echo "   Docs: http://localhost:$PORT/docs"
    echo "   Health: http://localhost:$PORT/_health"
    echo ""

    # Run with reload for development
    exec uvicorn app.main:app --reload --host 0.0.0.0 --port "$PORT"
fi
