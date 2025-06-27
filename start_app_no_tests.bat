@echo off
echo Starting Crypto Trading Assistant (Backend + Frontend) - NO STARTUP TESTS
echo ========================================================================

echo.
echo [0/3] Stopping existing servers...
echo ----------------------------------
echo Killing existing Node.js processes (Angular frontend)...
taskkill /f /im node.exe >nul 2>&1
echo Killing existing Python processes (FastAPI backend)...
taskkill /f /im python.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo.
echo [1/3] Starting Backend (FastAPI) - SKIPPING STARTUP TESTS...
echo -----------------------------------------------------------
start "Backend Server" cmd /k "cd crypto_assistant_backend && echo Backend starting on http://localhost:8000 (NO TESTS) && set SKIP_STARTUP_TESTS=true && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo.
echo [2/3] Starting Frontend (Angular)...
echo ------------------------------------
timeout /t 3 /nobreak >nul
start "Frontend Server" cmd /k "cd angular-frontend && echo Frontend starting on http://localhost:4200 && yarn start"

echo.
echo ========================================================================
echo Both servers are starting in separate windows (NO STARTUP TESTS):
echo - Backend:  http://localhost:8000
echo - Frontend: http://localhost:4200
echo - API Docs: http://localhost:8000/docs
echo.
echo NOTE: Startup tests are SKIPPED for faster development
echo Use 'start_app.bat' if you want to run startup tests
echo.
echo Close this window or press any key to exit...
pause >nul