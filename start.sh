#!/bin/bash
set -e

echo "🚀 Starting TeamBuilders Video App..."

# Go to backend directory  
cd video-scope-analyzer/backend

# Check if REDIS_URL is provided, otherwise run in simple mode
if [ -z "$REDIS_URL" ]; then
    echo "⚠️ No REDIS_URL provided, running in simple mode..."
    export USE_REDIS=false
else
    echo "✅ Using Redis at $REDIS_URL"
    # Start RQ worker in background
    rq worker uploads --url $REDIS_URL &
fi

# Start FastAPI server
echo "🌐 Starting server on port $PORT..."
python -m uvicorn main:app --host 0.0.0.0 --port $PORT