@echo off
cd /d "%~dp0"

if not exist ".venv-build\Scripts\python.exe" (
    echo Tworzenie srodowiska do budowy exe w folderze .venv-build ...
    py -3 -m venv .venv-build
    if errorlevel 1 (
        echo Nie znaleziono Pythona 3. Zainstaluj Python ze strony python.org i zaznacz opcje "Add python.exe to PATH".
        pause
        exit /b 1
    )
)

echo Instalacja bibliotek i PyInstaller ...
".venv-build\Scripts\python.exe" -m pip install -r requirements.txt pyinstaller
if errorlevel 1 (
    echo Instalacja bibliotek nie powiodla sie. Sprawdz polaczenie z internetem i komunikaty powyzej.
    pause
    exit /b 1
)

echo Budowanie Pobieracz.exe (kilka minut) ...
".venv-build\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed --name Pobieracz ^
    --add-data "zrodla.json;." --collect-all pyogrio --collect-all pyproj ^
    --hidden-import pobieracz.gui pobieracz_start.py
if errorlevel 1 (
    echo Budowanie nie powiodlo sie. Sprawdz komunikaty powyzej.
    pause
    exit /b 1
)

echo.
echo Gotowe: dist\Pobieracz.exe
echo Kopiuj sam plik Pobieracz.exe w dowolne miejsce. Obok niego powstana zrodla.json, dane\ i raporty\.
pause
