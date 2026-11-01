@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Tworzenie srodowiska Python w folderze .venv ...
    py -3 -m venv .venv
    if errorlevel 1 (
        echo Nie znaleziono Pythona 3. Zainstaluj Python ze strony python.org i zaznacz opcje "Add python.exe to PATH".
        pause
        exit /b 1
    )
)

echo Sprawdzanie i instalacja bibliotek ...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Instalacja bibliotek nie powiodla sie. Sprawdz polaczenie z internetem i komunikaty powyzej.
    pause
    exit /b 1
)

start "" ".venv\Scripts\pythonw.exe" -m pobieracz
