@echo off
cd /d "%~dp0..\bot"
call ..\backend\.venv\Scripts\activate
pip install -q -r requirements.txt
python -m main
