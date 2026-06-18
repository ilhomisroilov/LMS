@echo off
REM One-time backend setup: venv, deps, migrate, seed.
cd /d "%~dp0..\backend"
python -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist "..\.env" copy "..\.env.example" "..\.env"
alembic upgrade head
python -m app.seed
echo Backend ready. Start it with: scripts\run_backend.bat
