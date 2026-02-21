#!/bin/bash
# DevLocal 개발서버 동시 실행 스크립트
# Backend: FastAPI (port 8000) + Frontend: Vite (port 5173)

trap 'kill 0' EXIT

echo "Starting FastAPI backend on :8000..."
cd "$(dirname "$0")"
python3 -m uvicorn backend.main:app --reload --port 8000 &

echo "Starting Vite frontend on :5173..."
cd frontend && npm run dev &

wait
