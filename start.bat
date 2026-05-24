@echo off
chcp 65001 > nul
title CPA Tutor Launcher

echo ==========================================
echo   CPA Tutor -- Starting...
echo ==========================================

cd /d "%~dp0backend"
echo Starting backend server...
start "CPA-Backend" /MIN python -m uvicorn main:app --host 127.0.0.1 --port 8000

cd /d "%~dp0frontend"
echo Starting frontend dev server...
start "CPA-Frontend" /MIN npm run dev

echo Waiting for servers to be ready...
timeout /t 5 /nobreak > nul

echo Opening browser...
start http://localhost:5173

echo.
echo Backend:  http://localhost:8000/docs
echo Frontend: http://localhost:5173
echo.
echo You can close this window. Servers run in background.
timeout /t 3 /nobreak > nul
