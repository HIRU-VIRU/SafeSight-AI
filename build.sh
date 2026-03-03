#!/usr/bin/env bash
# =============================================================================
# build.sh – SafeSight AI build script
# Run by Render (and locally) before starting the server.
#
# Steps:
#   1. Install Python dependencies
#   2. Install Node.js dependencies and build the React frontend
#   3. Download YOLO model if MODEL_DOWNLOAD_URL is set and best.pt is missing
#   4. Create required runtime directories
# =============================================================================
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   SafeSight AI – Build                  ║"
echo "╚══════════════════════════════════════════╝"

# ── 1. Python dependencies ────────────────────────────────────────────────────
echo ""
echo "▶ [1/4] Installing Python dependencies..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo "  ✅ Python deps installed"

# ── 2. Frontend build ─────────────────────────────────────────────────────────
echo ""
echo "▶ [2/4] Building React frontend..."
if [ ! -d "frontend/node_modules" ]; then
  npm ci --prefix frontend --silent
fi
npm run build --prefix frontend --silent
echo "  ✅ Frontend built → frontend/dist/"

# ── 3. YOLO model ─────────────────────────────────────────────────────────────
echo ""
echo "▶ [3/4] Checking YOLO model..."
MODEL_PATH="${MODEL_PATH:-model/best.pt}"

if [ ! -f "$MODEL_PATH" ]; then
  if [ -n "${MODEL_DOWNLOAD_URL:-}" ]; then
    echo "  ⬇  Downloading model from \$MODEL_DOWNLOAD_URL..."
    mkdir -p "$(dirname "$MODEL_PATH")"
    curl -fsSL "$MODEL_DOWNLOAD_URL" -o "$MODEL_PATH"
    echo "  ✅ Model downloaded → $MODEL_PATH"
  else
    echo "  ⚠️  Model not found at $MODEL_PATH and MODEL_DOWNLOAD_URL is not set."
    echo "      Upload best.pt to the repo or set MODEL_DOWNLOAD_URL."
    echo "      API-only mode will still work; inference endpoints will fail."
  fi
else
  SIZE=$(du -sh "$MODEL_PATH" | cut -f1)
  echo "  ✅ Model found: $MODEL_PATH ($SIZE)"
fi

# ── 4. Runtime directories ────────────────────────────────────────────────────
echo ""
echo "▶ [4/4] Creating runtime directories..."
DATABASE_PATH="${DATABASE_PATH:-safesight.db}"
STORAGE_PATH="${STORAGE_PATH:-storage/violations}"
DEMO_STORAGE_PATH="${DEMO_STORAGE_PATH:-storage/demo}"
LOG_PATH="${LOG_PATH:-logs}"

mkdir -p "$STORAGE_PATH"
mkdir -p "$DEMO_STORAGE_PATH"
mkdir -p "$LOG_PATH"
mkdir -p "$(dirname "$DATABASE_PATH")"
echo "  ✅ Directories ready"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   Build complete ✅                      ║"
echo "╚══════════════════════════════════════════╝"
echo ""
