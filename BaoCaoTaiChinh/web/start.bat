@echo off
echo ================================================================================
echo Starting FastAPI Financial Dashboard Server
echo ================================================================================
echo.

cd /d %~dp0

echo Starting server with auto-reload...
echo.
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

pause

