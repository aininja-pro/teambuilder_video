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

echo "📁 Copying React build to FastAPI static directory..."
# Copy React build output to FastAPI static directory
# Check where Next.js actually builds to
if [ -d "./out" ]; then
    cp -r ./out ./backend/static
    echo "✅ Copied from ./out"
elif [ -d "./.next/static" ]; then
    mkdir -p ./backend/static
    cp -r ./.next/* ./backend/static/
    echo "✅ Copied from ./.next"
else
    echo "❌ Build output not found in expected locations"
    ls -la
fi

echo "✅ Build complete!"