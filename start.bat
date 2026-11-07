@echo off
title InternReach - Plateforme Scientifique de Recherche de Stage

echo ============================================================
echo   InternReach - Swiss Scientific Internship Engine
echo   Systemes Embarques, IA et Traitement du Signal
echo ============================================================
echo.

echo [1/2] Lancement du Backend FastAPI sur http://127.0.0.1:8008...
start "InternReach Backend (FastAPI)" cmd /k "cd /d %~dp0backend && venv\Scripts\python.exe main.py"

echo [2/2] Lancement du Frontend Next.js sur http://localhost:3005...
start "InternReach Frontend (Next.js)" cmd /k "cd /d %~dp0frontend && npx.cmd pnpm dev"

echo.
echo ============================================================
echo   Backend API : http://127.0.0.1:8008/docs
echo   Frontend UI : http://localhost:3005
echo ============================================================
echo Ouverture automatique dans votre navigateur par defaut...
ping -n 4 127.0.0.1 >nul
start http://localhost:3005
