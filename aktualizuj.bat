@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Najpierw uruchom uruchom.bat, zeby zainstalowac biblioteki.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m geosteam --aktualizuj
pause
