@echo off
echo Activating WMS System...

echo Starting Backend (Port 8000)...
start "WMS Backend" cmd /k "uv run uvicorn app.main:app --reload --port 8000"

timeout /t 3 /nobreak >nul

echo Starting Frontend (Port 5000)...
start "WMS Frontend" cmd /k "uv run python app.py"

echo System Activated!
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5000
echo.
pause
