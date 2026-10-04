#!/usr/bin/env bash
# QuantumRoute - Cross-Platform Linux/macOS Launcher

echo "========================================================"
echo " QuantumRoute: Quantum-Inspired Traffic Optimization"
echo " Smart India Hackathon Prototype (SIH26137)"
echo "========================================================"
echo ""

# Find python command
if command -v python3 &>/dev/null; then
    PY_CMD="python3"
elif command -v python &>/dev/null; then
    PY_CMD="python"
else
    echo "[ERROR] Python 3 not found. Please install Python 3.10+."
    exit 1
fi

echo "[1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ..."
PYTHONPATH=. $PY_CMD -m uvicorn backend.api:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

echo "[2/2] Starting Next.js Web App on http://127.0.0.1:3000 ..."
npm run dev -- --port 3000 &
FRONTEND_PID=$!

echo ""
echo "========================================================"
echo " QuantumRoute is live!"
echo " Backend:  http://127.0.0.1:8000"
echo " Web App:  http://127.0.0.1:3000"
echo " Press CTRL+C to terminate both servers."
echo "========================================================"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
