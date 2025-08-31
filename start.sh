#!/bin/bash
set -e

cd video-scope-analyzer/backend

# Start RQ worker with production Redis
echo "Starting RQ worker..."
rq worker uploads --url $REDIS_URL &

# Start FastAPI
echo "Starting FastAPI..."
uvicorn main:app --host 0.0.0.0 --port $PORT