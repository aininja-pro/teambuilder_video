#!/usr/bin/env bash
set -euxo pipefail

echo "🚀 Building TeamBuilders Video App..."

# Python deps
pip install -r requirements.txt

# Frontend build (static export)
pushd video-scope-analyzer
npm ci
npm run build
# ✅ Guard: ensure the logo exists in the export
test -f out/assets/team-builders-logo.png || { echo "❌ Logo missing in export"; ls -R out | sed -n '1,200p'; exit 1; }
popd

# Publish the export for FastAPI to serve
rm -rf video-scope-analyzer/backend/static
mkdir -p video-scope-analyzer/backend/static
rsync -a --delete video-scope-analyzer/out/ video-scope-analyzer/backend/static/

echo "✅ Build complete!"