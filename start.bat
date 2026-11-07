@echo off
title Launching InternReach (Swiss Scientific Internship Platform)
echo ============================================================
echo   InternReach — Swiss Scientific Internship Engine
echo   Systèmes Embarqués, IA & Traitement de l'Information
echo ============================================================
echo.

echo [1/2] Starting Python FastAPI Backend on port 8008...
start "InternReach Backend (FastAPI)" cmd /k "cd /d %~dp0backend && venv\Scripts\python.exe main.py"

echo [2/2] Starting Next.js Frontend on port 3005...
start "InternReach Frontend (Next.js)" cmd /k "cd /d %~dp0frontend && npx.cmd pnpm dev"

echo.
echo ============================================================
echo  Backend API:  http://localhost:8008/docs
echo  Frontend UI:  http://localhost:3005
echo ============================================================
echo App is opening in your default browser...
timeout /t 3 >nul
start http://localhost:3005
