#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "Stopping any existing FitHub AI frontend on port 5173"
pkill -f "vite" 2>/dev/null || true

VM_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
echo "Starting FitHub AI frontend on http://0.0.0.0:5173"
if [[ -n "${VM_IP}" ]]; then
  echo "LAN frontend URL: http://${VM_IP}:5173"
  echo "Friendly frontend URL, after hosts-file setup: http://fithub.local:5173"
fi
exec npm --prefix src/frontend run dev -- --host 0.0.0.0 --port 5173
