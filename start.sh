#!/bin/bash
set -e

echo "🚀 Starting TeamBuilders Video App..."

# Install and start Redis locally
echo "🔴 Installing Redis..."
apt-get update && apt-get install -y redis-server ffmpeg
redis-server --daemonize yes --port 6379

# Wait for Redis to start
sleep 2

# Start RQ worker in background
echo "👷 Starting background worker..."
cd video-scope-analyzer/backend
rq worker uploads --url redis://localhost:6379 &

# Start FastAPI server
echo "🌐 Starting server on port $PORT..."
uvicorn main:app --host 0.0.0.0 --port $PORT