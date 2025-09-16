#!/bin/bash

# AIOM4B Startup Script

echo "🚀 Starting AIOM4B Application..."

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed. Please install Poetry first."
    echo "Visit: https://python-poetry.org/docs/#installation"
    exit 1
fi

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ FFmpeg is not installed. Please install FFmpeg first."
    echo "macOS: brew install ffmpeg"
    echo "Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo "Windows: Download from https://ffmpeg.org/download.html"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/output data/backup data/logs source

# Install Python dependencies
echo "📦 Installing Python dependencies..."
poetry install

# Start the API server
echo "🌐 Starting API server..."
poetry run uvicorn aiom4b.main:app --host 0.0.0.0 --port 8000 --reload &

# Wait a moment for the server to start
sleep 3

# Check if the web UI directory exists
if [ -d "web-ui" ]; then
    echo "🎨 Starting web UI..."
    cd web-ui
    
    # Check if Node.js is installed
    if ! command -v node &> /dev/null; then
        echo "⚠️  Node.js is not installed. Skipping web UI startup."
        echo "Install Node.js to use the web interface."
    else
        # Install npm dependencies if node_modules doesn't exist
        if [ ! -d "node_modules" ]; then
            echo "📦 Installing web UI dependencies..."
            npm install
        fi
        
        # Start the web UI
        npm run dev &
        echo "✅ Web UI started at http://localhost:3000"
    fi
    
    cd ..
else
    echo "⚠️  Web UI directory not found. Skipping web UI startup."
fi

echo ""
echo "✅ AIOM4B is now running!"
echo "📡 API Server: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "🎨 Web UI: http://localhost:3000"
echo ""
echo "💡 Usage:"
echo "  CLI: poetry run python -m aiom4b.cli --help"
echo "  API: curl http://localhost:8000/api/v1/folders"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user to stop
wait
