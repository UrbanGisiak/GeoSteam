"""Konfiguracja źródeł, zapis warstw do GeoPackage i raporty zmian."""
import datetime
import json
import os
import shutil
import sys

import pyogrio

# w exe (PyInstaller) pliki obok programu leżą w folderze exe, a nie w folderze rozpakowania
if getattr(sys, "frozen", False):
    KATALOG_APLIKACJI = os.path.dirname(sys.executable)
    KATALOG_ZASOBOW = sys._MEIPASS
else:
    KATALOG_APLIKACJI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    KATALOG_ZASOBOW = KATALOG_APLIKACJI
PLIK_ZRODEL = os.path.join(KATALOG_APLIKACJI, "zrodla.json")
KATALOG_RAPORTOW = os.path.join(KATALOG_APLIKACJI, "raporty")


def wczytaj_konfiguracje():
    if not os.path.exists(PLIK_ZRODEL):
        # pierwsze uruchomienie exe: domyślna lista źródeł wbudowana w program
        shutil.copyfile(os.path.join(KATALOG_ZASOBOW, "zrodla.json"), PLIK_ZRODEL)
    with open(PLIK_ZRODEL, encoding="utf-8") as plik:
        return json.load(plik)


def zapisz_konfiguracje(konfiguracja):
    with open(PLIK_ZRODEL, "w", encoding="utf-8") as plik:
        json.dump(konfiguracja, plik, ensure_ascii=False, indent=2)


def folder_danych(konfiguracja):
    return os.path.join(KATALOG_APLIKACJI, konfiguracja["folder_danych"])


def _warstwy_w_pliku(plik):
    if not os.path.exists(plik):
        return []
    return [nazwa for nazwa, _typ in pyogrio.list_layers(plik)]


def zapisz_warstwe(plik, warstwa, gdf):
    """Zastępuje jedną warstwę w GeoPackage, pozostałe warstwy zostają. Zwraca liczbę obiektów przed i po."""
    stara = None
    if warstwa in _warstwy_w_pliku(plik):
        stara = pyogrio.read_info(plik, layer=warstwa)["features"]
    gdf = gdf.assign(data_pobrania=datetime.date.today().isoformat())
    gdf.to_file(plik, layer=warstwa, driver="GPKG")
    return stara, len(gdf)


def zapisz_raport(linie):
    os.makedirs(KATALOG_RAPORTOW, exist_ok=True)
    znacznik = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    sciezka = os.path.join(KATALOG_RAPORTOW, f"raport_{znacznik}.txt")
    with open(sciezka, "w", encoding="utf-8") as plik:
        plik.write("\n".join(linie) + "\n")
    return sciezka
