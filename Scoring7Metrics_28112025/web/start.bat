@echo off
echo Starting Scoring 7 Metrics Dashboard API Server...
echo.

cd /d %~dp0

REM Check if virtual environment exists
if exist .venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Using system Python.
)

echo.
echo Starting FastAPI server on http://localhost:8000
echo Press Ctrl+C to stop the server
echo.

python app.py --host 0.0.0.0 --port 8000

pause

