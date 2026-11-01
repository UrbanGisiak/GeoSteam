# Pobieracz danych GIS (EZiUDP / WFS)

Prosta aplikacja do pobierania i aktualizacji warstw GIS z usług WFS wskazanych w katalogu
EZiUDP (GUGiK). Warstwy zapisywane są w plikach GeoPackage (`.gpkg`).

## Instalacja na Windows

1. Zainstaluj Python 3.12 lub nowszy ze strony [python.org](https://www.python.org/downloads/).
   Na pierwszym ekranie instalatora zaznacz **Add python.exe to PATH**.
2. Uruchom `uruchom.bat`. Przy pierwszym uruchomieniu skrypt tworzy folder `.venv`
   i instaluje biblioteki (kilka minut). Kolejne uruchomienia są szybkie.

## Wersja .exe (bez instalacji Pythona)

Program można spakować do folderu `GeoSteam\` z plikiem `GeoSteam.exe`, który działa na Windows bez zainstalowanego Pythona.

1. Na dowolnym Windowsie z Pythonem 3.12+ uruchom `build_exe.bat` (raz). Powstanie `dist\GeoSteam\`.
2. Skopiuj cały folder `GeoSteam\` na docelowy komputer, np. do `C:\GeoSteam\`.
   Nie umieszczaj go w `Program Files` - program zapisuje pliki obok siebie.
3. Uruchom `GeoSteam.exe`. Przy pierwszym uruchomieniu obok exe powstaną `zrodla.json` (domyślna lista źródeł), `dane\` i `raporty\`.

Aktualizacja w tle, np. w Harmonogramie zadań: program `GeoSteam.exe` z argumentem `--aktualizuj`
(zadanie uruchom w folderze `GeoSteam\`). Wynik zapisuje się w `raporty\`.

Uwagi:
- Program nie ma okna konsoli, więc błędy z `--aktualizuj` widać w raporcie w `raporty\`.
- Jeśli program nie wystartuje, obok `GeoSteam.exe` pojawi się plik `blad.txt` z treścią błędu.
- Antywirus (np. Defender) może zgłaszać pliki spakowane PyInstallerem jako podejrzane. To znany problem tego narzędzia.
  Wtedy trzeba dodać wyjątek dla folderu `GeoSteam\`.

## Obsługa

**1. Wyszukaj zbiór** - wpisz TERYT lub fragment nazwy zbioru i kliknij *Szukaj*.
Zostaną pokazane zbiory z usługą pobierania.

**2. Wybierz usługę** - kliknij zbiór, potem usługę oznaczoną `[WFS]`, potem *Pokaż warstwy WFS*.
Zaznacz potrzebne warstwy (bez zaznaczenia zostaną pobrane wszystkie) i kliknij *Dodaj do listy źródeł*.

**3. Aktualizuj** - zaznacz źródła (lub wszystkie) i kliknij *Aktualizuj*. Warstwa w pliku `.gpkg`
jest zastępowana nową wersją, a pozostałe warstwy w tym pliku zostają. Po każdej aktualizacji
w folderze `raporty` zapisywany jest raport z liczbą obiektów przed i po.

Lista źródeł jest w pliku `zrodla.json`. Folder danych zmienisz przyciskiem *Zmień folder danych*
(np. na folder w OneDrive).

## Aktualizacja bez okna

`aktualizuj.bat` aktualizuje wszystkie źródła i wypisuje postęp w konsoli.
Do automatycznej aktualizacji (np. w Harmonogramie zadań Windows) użyj polecenia:

    .venv\Scripts\python.exe -m pobieracz --aktualizuj

uruchamianego z tego folderu.

## Ograniczenia

- Obsługiwane są tylko usługi **WFS**. Usługi ATOM, WCS, SOS i inne są oznaczone jako `[inna usługa]`.
- Jeśli serwer nie obsługuje stronicowania (`startIndex`), warstwa pobierana jest jednym żądaniem.
- Gdy serwer ma problem z certyfikatem SSL, aplikacja ponawia żądanie bez weryfikacji i pisze o tym w dzienniku.
- Gdy pobieranie warstwy się nie uda lub zwróci zero obiektów, stara wersja warstwy zostaje bez zmian.
- Nazwy warstw w GeoPackage są zgodne z dotychczasowymi skryptami (słownik `nazwy_warstw` w `zrodla.json`).

## Pliki

- `pobieracz/` - kod aplikacji
- `zrodla.json` - lista źródeł, folder danych i nazwy warstw
- `requirements.txt` - biblioteki (geopandas, pyogrio, requests)
- `uruchom.bat` / `aktualizuj.bat` - uruchomienie na Windows
- `dane/` - domyślny folder z plikami `.gpkg` (tworzony automatycznie)
- `raporty/` - raporty z aktualizacji (tworzony automatycznie)
