@echo off
setlocal

REM Always run from project root (where this .bat lives)
cd /d "%~dp0"

REM Require existing venv (no install flow)
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] .venv not found. Please create it first.
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"

echo Starting FastAPI server on http://localhost:8000 ...
start "" http://localhost:8000/dashboard/
python -m uvicorn app.main:app --port 8000
