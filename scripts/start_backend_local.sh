#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "Stopping any existing FitHub AI backend on port 8000"
pkill -f "uvicorn src.backend.app.main:app" 2>/dev/null || true

echo "Starting FitHub AI backend on http://127.0.0.1:8000"
exec .venv/bin/uvicorn src.backend.app.main:app --host 127.0.0.1 --port 8000 --reload --log-level info
