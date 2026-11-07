@echo off
setlocal
title InternReach - Installation et Configuration de l'Environnement

echo ============================================================
echo   InternReach - Swiss Scientific Internship Engine
echo   Setup et Installation Automatique (Full-Stack)
echo ============================================================
echo.

set "ROOT_DIR=%~dp0"
set "BACKEND_DIR=%ROOT_DIR%backend"
set "FRONTEND_DIR=%ROOT_DIR%frontend"

:: -----------------------------------------------------------------------------
:: Etape 1: Verification des prerequis systeme (Python et Node.js)
:: -----------------------------------------------------------------------------
echo [1/4] Verification des prerequis systeme...

where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PY_CMD=python"
) else (
    where py >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        set "PY_CMD=py -3"
    ) else (
        echo [ERREUR] Python 3 n'a pas ete detecte dans votre PATH.
        echo Veuillez installer Python 3.10+ depuis https://www.python.org/
        echo en cochant bien la case "Add Python to PATH".
        pause
        exit /b 1
    )
)

for /f "tokens=*" %%v in ('%PY_CMD% --version 2^>^&1') do echo   - Python detecte : %%v

where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERREUR] Node.js n'a pas ete detecte dans votre PATH.
    echo Veuillez installer Node.js 18+ LTS depuis https://nodejs.org/
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('node --version 2^>^&1') do echo   - Node.js detecte : %%v

where pnpm >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PKG_MGR=pnpm"
) else (
    set "PKG_MGR=npx.cmd pnpm"
)
echo   - Gestionnaire de paquets : %PKG_MGR%
echo.

:: -----------------------------------------------------------------------------
:: Etape 2: Configuration du Backend Python (FastAPI)
:: -----------------------------------------------------------------------------
echo [2/4] Configuration du Backend Python (FastAPI)...
cd /d "%BACKEND_DIR%"

if not exist "venv\Scripts\python.exe" (
    echo   - Creation de l'environnement virtuel venv...
    %PY_CMD% -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo [ERREUR] Impossible de creer l'environnement virtuel venv.
        pause
        exit /b 1
    )
    echo   - venv cree avec succes.
) else (
    echo   - Environnement virtuel venv existant detecte.
)

echo   - Mise a jour de pip...
venv\Scripts\python.exe -m pip install --upgrade pip --quiet

echo   - Installation des dependances Python [requirements.txt]...
venv\Scripts\python.exe -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [ERREUR] Echec lors de l'installation des packages Python.
    pause
    exit /b 1
)

if exist "requirements-dev.txt" (
    echo   - Installation des dependances de dev [requirements-dev.txt]...
    venv\Scripts\python.exe -m pip install -r requirements-dev.txt --quiet
)

if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo   - Fichier backend\.env initialise depuis .env.example.
    )
)

if not exist "app\data" (
    mkdir "app\data"
    echo   - Dossier backend\app\data initialise.
)

echo   - Backend configure avec succes.
echo.

:: -----------------------------------------------------------------------------
:: Etape 3: Configuration du Frontend Next.js
:: -----------------------------------------------------------------------------
echo [3/4] Configuration du Frontend Next.js...
cd /d "%FRONTEND_DIR%"

echo   - Installation des modules Node.js [%PKG_MGR% install]...
call %PKG_MGR% install
if %ERRORLEVEL% neq 0 (
    echo   - Secours avec npm install...
    call npm install
    if %ERRORLEVEL% neq 0 (
        echo [ERREUR] Echec de l'installation des dependances frontend.
        pause
        exit /b 1
    )
)

echo   - Frontend configure avec succes.
echo.

:: -----------------------------------------------------------------------------
:: Etape 4: Finalisation
:: -----------------------------------------------------------------------------
cd /d "%ROOT_DIR%"
echo [4/4] Finalisation...
echo ============================================================
echo   Installation terminee avec succes !
echo ============================================================
echo.
echo Configuration optionnelle :
echo   - Cle d'API Gemini / Claude / OpenAI :
echo     * Soit dans backend\.env
echo     * Soit directement dans l'interface web (Bouton "BYOK API")
echo.
echo Pour demarrer la plateforme a tout moment :
echo   Double-cliquez sur "start.bat"
echo.

choice /C ON /D O /T 15 /M "Voulez-vous demarrer InternReach maintenant ? [O: Oui, N: Non]"
if errorlevel 2 (
    echo.
    echo Installation prete. Vous pouvez lancer start.bat a tout moment.
    goto :FINISH
)

echo.
echo Lancement d'InternReach via start.bat...
call "%ROOT_DIR%start.bat"

:FINISH
exit /b 0
