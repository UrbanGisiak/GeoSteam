@echo off
cd /d "%~dp0"

if not exist ".venv-build\Scripts\python.exe" (
    echo Tworzenie srodowiska do budowy w folderze .venv-build ...
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

echo Budowanie GeoSteam (kilka minut) ...
".venv-build\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onedir --windowed --name GeoSteam ^
    --add-data "zrodla.json;." --collect-all pyogrio --collect-all pyproj ^
    --hidden-import pobieracz.gui pobieracz_start.py
if errorlevel 1 (
    echo Budowanie nie powiodlo sie. Sprawdz komunikaty powyzej.
    pause
    exit /b 1
)

echo.
echo Gotowe: dist\GeoSteam\GeoSteam.exe
echo Caly folder dist\GeoSteam\ skopiuj w dowolne miejsce, np. C:\GeoSteam\. Obok exe powstana zrodla.json, dane\ i raporty\.
pause
