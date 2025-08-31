#!/bin/bash
set -e

echo "🚀 Starting TeamBuilders Video App..."

# Go to backend directory  
cd video-scope-analyzer/backend

# Install dependencies in runtime environment  
echo "📦 Installing Python dependencies..."
pip install -r ../../requirements.txt

# For initial deployment, just run the main.py directly (it has uvicorn.run built-in)
echo "🌐 Starting server on port $PORT..."
export USE_REDIS=false
python main.py