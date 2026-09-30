@echo off
title QuantumRoute - Launcher
echo ========================================================
echo  QuantumRoute: Quantum-Inspired Traffic Optimization
echo  Smart India Hackathon Prototype
echo ========================================================
echo.

echo [1/3] Checking Python installation...
py --version >nul 2>&1
if %errorlevel% neq 0 (
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Python not found. Please install Python 3.10+ and add it to PATH.
        pause
        exit /b 1
    )
    set PY_CMD=python
) else (
    set PY_CMD=py
)

echo [2/3] Starting FastAPI Backend on http://127.0.0.1:8000 ...
if exist .venv\Scripts\python.exe (
    set PY_CMD=.venv\Scripts\python.exe
)
start "QuantumRoute Backend" cmd /k "%PY_CMD% -m uvicorn backend.api:app --host 127.0.0.1 --port 8000 --reload"

echo [3/3] Starting Next.js Web App on http://127.0.0.1:3000 ...
cd web
start "QuantumRoute Web" cmd /k "npm run dev"
cd ..

echo.
echo ========================================================
echo  QuantumRoute is running!
echo  Backend:  http://127.0.0.1:8000
echo  Web App:  http://127.0.0.1:3000
echo ========================================================
echo.
pause
