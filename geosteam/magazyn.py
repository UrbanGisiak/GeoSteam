"""Konfiguracja źródeł, scenariusze, ustawienia, zapis warstw do GeoPackage i raporty zmian."""
import copy
import datetime
import json
import os
import re
import shutil
import sys

import geopandas as gpd
import pyogrio

# w exe (PyInstaller) pliki obok programu leżą w folderze exe, a nie w folderze rozpakowania
if getattr(sys, "frozen", False):
    KATALOG_APLIKACJI = os.path.dirname(sys.executable)
    KATALOG_ZASOBOW = sys._MEIPASS
else:
    KATALOG_APLIKACJI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    KATALOG_ZASOBOW = KATALOG_APLIKACJI
PLIK_ZRODEL = os.path.join(KATALOG_APLIKACJI, "zrodla.json")
PLIK_USTAWIEN = os.path.join(KATALOG_APLIKACJI, "ustawienia.json")
KATALOG_SCENARIUSZY = os.path.join(KATALOG_APLIKACJI, "scenariusze")
KATALOG_RAPORTOW = os.path.join(KATALOG_APLIKACJI, "raporty")

DOMYSLNE_USTAWIENIA = {
    "aktywny_scenariusz": None,
    "format_raportu": "xlsx",
    "harmonogram": {"wlaczony": False, "co_minut": 1440, "ostatnie_uruchomienie": None},
}


def wczytaj_konfiguracje():
    if not os.path.exists(PLIK_ZRODEL):
        # pierwsze uruchomienie exe: domyślna lista źródeł wbudowana w program
        shutil.copyfile(os.path.join(KATALOG_ZASOBOW, "zrodla.json"), PLIK_ZRODEL)
    with open(PLIK_ZRODEL, encoding="utf-8") as plik:
        return json.load(plik)


def zapisz_konfiguracje(konfiguracja):
    with open(PLIK_ZRODEL, "w", encoding="utf-8") as plik:
        json.dump(konfiguracja, plik, ensure_ascii=False, indent=2)


def wczytaj_ustawienia():
    ustawienia = copy.deepcopy(DOMYSLNE_USTAWIENIA)
    if os.path.exists(PLIK_USTAWIEN):
        with open(PLIK_USTAWIEN, encoding="utf-8") as plik:
            zapisane = json.load(plik)
        harmonogram = zapisane.pop("harmonogram", {})
        if "co_godzin" in harmonogram:  # wersja starsza niż ustawienia w minutach
            harmonogram.setdefault("co_minut", harmonogram.pop("co_godzin") * 60)
            harmonogram.pop("co_godzin", None)
        ustawienia.update(zapisane)
        ustawienia["harmonogram"].update(harmonogram)
    return ustawienia


def zapisz_ustawienia(ustawienia):
    with open(PLIK_USTAWIEN, "w", encoding="utf-8") as plik:
        json.dump(ustawienia, plik, ensure_ascii=False, indent=2)


def folder_danych(konfiguracja):
    return os.path.join(KATALOG_APLIKACJI, konfiguracja["folder_danych"])


def _nazwa_scenariusza(nazwa):
    czysta = re.sub(r"[^\w \-]", "_", nazwa).strip()
    if not czysta:
        raise ValueError("Podaj nazwę scenariusza.")
    return czysta


def sciezka_scenariusza(nazwa):
    return os.path.join(KATALOG_SCENARIUSZY, nazwa + ".json")


def lista_scenariuszy():
    """Nazwy scenariuszy z folderu scenariusze. Gdy folder jest pusty, tworzy scenariusz 'domyslny'."""
    os.makedirs(KATALOG_SCENARIUSZY, exist_ok=True)
    if not any(plik.endswith(".json") for plik in os.listdir(KATALOG_SCENARIUSZY)):
        zapisz_scenariusz("domyslny", wczytaj_konfiguracje())
    return sorted(os.path.splitext(plik)[0] for plik in os.listdir(KATALOG_SCENARIUSZY) if plik.endswith(".json"))


def zapisz_scenariusz(nazwa, konfiguracja, nadpisz=False):
    """Zapisuje konfigurację jako scenariusz. Zwraca nazwę pliku bez rozszerzenia."""
    nazwa = _nazwa_scenariusza(nazwa)
    sciezka = sciezka_scenariusza(nazwa)
    if os.path.exists(sciezka) and not nadpisz:
        raise FileExistsError(nazwa)
    os.makedirs(KATALOG_SCENARIUSZY, exist_ok=True)
    with open(sciezka, "w", encoding="utf-8") as plik:
        json.dump(konfiguracja, plik, ensure_ascii=False, indent=2)
    return nazwa


def wczytaj_scenariusz(sciezka):
    """Sprawdza plik scenariusza i zapisuje go jako aktywną listę źródeł (zrodla.json)."""
    with open(sciezka, encoding="utf-8") as plik:
        scenariusz = json.load(plik)
    if not isinstance(scenariusz, dict) or not isinstance(scenariusz.get("folder_danych"), str) \
            or not isinstance(scenariusz.get("zrodla"), list):
        raise ValueError("Plik nie jest scenariuszem GeoSteam (brak folder_danych albo zrodla).")
    scenariusz.setdefault("nazwy_warstw", {})
    zapisz_konfiguracje(scenariusz)
    return scenariusz


def dodaj_zrodlo_do_scenariusza(nazwa, zrodlo):
    """Dopisuje źródło do zapisanego scenariusza. Odrzuca duplikat (ten sam adres i te same warstwy)."""
    sciezka = sciezka_scenariusza(nazwa)
    with open(sciezka, encoding="utf-8") as plik:
        scenariusz = json.load(plik)
    if not isinstance(scenariusz, dict) or not isinstance(scenariusz.get("zrodla"), list):
        raise ValueError("Wybrany plik nie jest scenariuszem GeoSteam.")
    if any(z["wfs_url"] == zrodlo["wfs_url"] and z["warstwy"] == zrodlo["warstwy"] for z in scenariusz["zrodla"]):
        raise ValueError("To samo źródło jest już w scenariuszu.")
    scenariusz["zrodla"].append(zrodlo)
    with open(sciezka, "w", encoding="utf-8") as plik:
        json.dump(scenariusz, plik, ensure_ascii=False, indent=2)


def _warstwy_w_pliku(plik):
    if not os.path.exists(plik):
        return []
    return [nazwa for nazwa, _typ in pyogrio.list_layers(plik)]


def wczytaj_warstwe(plik, warstwa):
    """Obiekty warstwy z GeoPackage albo None, gdy warstwy jeszcze nie ma."""
    if warstwa not in _warstwy_w_pliku(plik):
        return None
    return gpd.read_file(plik, layer=warstwa)


def zapisz_warstwe(plik, warstwa, gdf):
    """Zastępuje jedną warstwę w GeoPackage, pozostałe warstwy zostają."""
    gdf = gdf.assign(data_pobrania=datetime.date.today().isoformat())
    gdf.to_file(plik, layer=warstwa, driver="GPKG")
