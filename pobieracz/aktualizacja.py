"""Aktualizacja źródeł: pobranie warstw z WFS i podmiana ich w plikach GeoPackage."""
import datetime
import os

from . import magazyn, wfs


def nazwa_warstwy(nazwa_wfs, nazwy_warstw):
    """Nazwa warstwy w GeoPackage: z mapowania z konfiguracji albo bez prefiksu, np. 'ms:A01_X' -> 'A01_X'."""
    return nazwy_warstw.get(nazwa_wfs, nazwa_wfs.rsplit(":", 1)[-1])


def _aktualizuj_zrodlo(zrodlo, folder, nazwy_warstw, log):
    plik = os.path.join(folder, zrodlo["plik"])
    os.makedirs(folder, exist_ok=True)
    wersja, dostepne = wfs.pobierz_capabilities(zrodlo["wfs_url"], log)
    dostepne_nazwy = [nazwa for nazwa, _tytul in dostepne]
    do_pobrania = zrodlo["warstwy"] or dostepne_nazwy
    log(f"WFS {wersja}, warstw do pobrania: {len(do_pobrania)}")
    for nazwa in do_pobrania:
        if nazwa not in dostepne_nazwy:
            log(f"[BŁĄD] Brak warstwy {nazwa} w usłudze")
            continue
        log(f"  Pobieranie {nazwa}")
        try:
            gdf = wfs.pobierz_warstwe(zrodlo["wfs_url"], nazwa, wersja, log)
        except Exception as blad:
            log(f"[BŁĄD] {nazwa}: {blad}")
            continue
        if gdf.empty:
            log(f"[UWAGA] {nazwa}: brak obiektów, poprzednia wersja warstwy pozostaje bez zmian")
            continue
        warstwa = nazwa_warstwy(nazwa, nazwy_warstw)
        stara, nowa = magazyn.zapisz_warstwe(plik, warstwa, gdf)
        poprzednio = "brak" if stara is None else stara
        log(f"[OK] {warstwa}: {poprzednio} -> {nowa} obiektów (zmiana: {nowa - (stara or 0):+d})")
    zrodlo["ostatnia_aktualizacja"] = datetime.datetime.now().isoformat(timespec="minutes")


def aktualizuj(konfiguracja, zrodla, log=print):
    """Aktualizuje podane źródła, zapisuje konfigurację i raport. Zwraca ścieżkę raportu."""
    folder = magazyn.folder_danych(konfiguracja)
    linie = []

    def raportuj(linia):
        linie.append(linia)
        log(linia)

    raportuj(f"Start aktualizacji: {datetime.datetime.now():%Y-%m-%d %H:%M}, folder: {folder}")
    for zrodlo in zrodla:
        raportuj(f"=== {zrodlo['nazwa']} ===")
        try:
            _aktualizuj_zrodlo(zrodlo, folder, konfiguracja["nazwy_warstw"], raportuj)
        except Exception as blad:
            raportuj(f"[BŁĄD] Źródło pominięte: {blad}")
    magazyn.zapisz_konfiguracje(konfiguracja)
    sciezka = magazyn.zapisz_raport(linie)
    raportuj(f"Raport zapisano: {sciezka}")
    return sciezka
