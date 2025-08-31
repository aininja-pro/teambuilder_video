#!/bin/bash
set -e

echo "🚀 Building TeamBuilders Video App..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install Node.js dependencies and build React app
echo "📦 Installing Node.js dependencies..."
cd video-scope-analyzer
npm install

echo "🏗️ Building React app..."
npm run build

echo "✅ Build complete!"