@echo off
title NUME - AI Marketing Assistant
echo ============================================
echo  NUME - starting backend + frontend
echo ============================================

set ROOT=%~dp0

REM --- Backend (FastAPI on :8000) ---
start "NUME Backend :8000" cmd /k "cd /d %ROOT%backend && call .venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

REM --- Frontend (Vite on :5173) ---
start "NUME Frontend :5173" cmd /k "cd /d %ROOT%frontend && npm run dev"

REM --- Open the app once the dev servers have had a moment to boot ---
timeout /t 8 /nobreak >nul
start "" http://localhost:5173

echo.
echo  Backend:  http://localhost:8000  (API docs: /docs)
echo  Frontend: http://localhost:5173
echo.
echo  Close the two server windows to stop everything.
timeout /t 5 >nul
exit
