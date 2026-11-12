@echo off
echo ===================================================
echo     Demarrage du Panel Etudiant CISCO (BUT)
echo ===================================================
echo.

start "Cisco Backend (FastAPI)" cmd /k "cd backend && .\.venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"
timeout /t 2 >nul
start "Cisco Frontend (SvelteKit)" cmd /k "cd frontend && npm run dev -- --open"

echo.
echo Les serveurs sont lances !
echo Frontend: http://localhost:5173
echo Backend API: http://localhost:8000/docs
echo ===================================================

