@echo off
rem Campus AI - one-click local run (Windows)
echo.
echo [1/2] Starting FastAPI backend on http://127.0.0.1:8000
echo       (open http://127.0.0.1:8000 in your browser once started)
echo.
start "Campus AI Backend" cmd /k "cd backend && python -m uvicorn app.main:app --port 8000"
echo.
echo [2/2] Opening the frontend dev server (http://localhost:5173)...
echo.
start "Campus AI Frontend" cmd /k "cd frontend && npm run dev"
echo Done. If the frontend needs dependencies, run: cd frontend && npm install
