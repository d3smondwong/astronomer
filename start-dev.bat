@echo off
REM start-dev.bat
REM Launches the full Huat Life dev stack, each process in its own window:
REM   1. FastAPI backend    (conda env: astronomer)
REM   2. Firebase emulators (firestore + auth)
REM   3. Next.js frontend   (apps/web)
REM
REM Usage (from repo root):  double-click, or run  start-dev.bat

echo Starting Huat Life dev stack...

REM START /d "<dir>" sets the working directory for each new window explicitly.
REM The trailing "." on the root path avoids the  \"  escaped-quote gotcha.

REM 1. Backend - from repo root so the apps.backend module resolves.
start "backend"   /d "%~dp0."        cmd /k "conda activate astronomer && python -m apps.backend.main"

REM 2. Firebase emulators (firestore + auth).
start "emulators" /d "%~dp0apps\web" cmd /k "npm run emulators"

REM 3. Next.js frontend.
start "frontend"  /d "%~dp0apps\web" cmd /k "npm run dev"

echo.
echo Launched 3 windows: backend, emulators, frontend.
echo   Backend:    http://localhost:8000
echo   Emulators:  http://localhost:4000 (UI)
echo   Frontend:   http://localhost:3000
echo.
pause
