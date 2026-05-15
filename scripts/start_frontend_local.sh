#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "Stopping any existing FitHub AI frontend on port 5173"
pkill -f "vite" 2>/dev/null || true

echo "Starting FitHub AI frontend on http://127.0.0.1:5173"
exec npm --prefix src/frontend run dev -- --host 127.0.0.1 --port 5173
