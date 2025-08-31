#!/bin/bash
set -e

cd video-scope-analyzer/backend
uvicorn main:app --host 0.0.0.0 --port $PORT