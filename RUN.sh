#!/usr/bin/env bash
# Campus AI - one-click local run (macOS/Linux)
set -e
cd "$(dirname "$0")"
echo "[1/2] Starting FastAPI backend on http://127.0.0.1:8000"
(cd backend && uvicorn app.main:app --port 8000) &
BACKEND=$!
echo "[2/2] Starting frontend dev server on http://localhost:5173"
(cd frontend && npm run dev) &
FRONTEND=$!
trap "kill $BACKEND $FRONTEND" EXIT
wait
