#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "Stopping any existing FitHub AI backend on port 8000"
pkill -f "uvicorn src.backend.app.main:app" 2>/dev/null || true

VM_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
echo "Starting FitHub AI backend on http://0.0.0.0:8000"
if [[ -n "${VM_IP}" ]]; then
  echo "LAN backend URL: http://${VM_IP}:8000"
  echo "Friendly backend URL, after hosts-file setup: http://fithub.local:8000"
fi
exec .venv/bin/uvicorn src.backend.app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info
