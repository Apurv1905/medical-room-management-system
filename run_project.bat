
@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment nahi mila!
    pause
    exit /b 1
)

start "" cmd /c "timeout /t 3 /nobreak >nul & start "" http://127.0.0.1:8000/"

".venv\Scripts\python.exe" manage.py runserver

pause
