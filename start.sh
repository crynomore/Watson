#!/usr/bin/env bash
# Starts the Watson backend server
set -e
cd "$(dirname "$0")"
[ -f .env ] && export $(grep -v '^#' .env | xargs) 2>/dev/null || true
echo "[Watson] Starting backend on http://127.0.0.1:8000"
echo "[Watson] Provider: ${AI_PROVIDER:-openai}  Model: ${MODEL:-default}"
echo "[Watson] Press Ctrl+C to stop."
echo ""
.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000
