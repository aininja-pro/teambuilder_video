#!/bin/bash
set -e

echo "🚀 Building TeamBuilders Video App..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install Node.js dependencies first
echo "📦 Installing Node.js dependencies..."
cd video-scope-analyzer
npm install
cd ..

# Build React app
echo "🏗️ Building React app..."
npm run build --prefix ./video-scope-analyzer

# Copy React output to backend/static directory
echo "📁 Copying React build to FastAPI static directory..."
rm -rf ./video-scope-analyzer/backend/static
mkdir -p ./video-scope-analyzer/backend/static
cp -r ./video-scope-analyzer/out/* ./video-scope-analyzer/backend/static/

echo "✅ Build complete!"