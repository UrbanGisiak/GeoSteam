"""Aktualizacja źródeł: pobranie warstw z WFS, porównanie z poprzednią wersją i podmiana w GeoPackage."""
import datetime
import os

from . import magazyn, porownanie, raport, wfs


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
    wyniki = []
    for nazwa in do_pobrania:
        warstwa = nazwa_warstwy(nazwa, nazwy_warstw)
        wynik = {
            "zrodlo": zrodlo["nazwa"],
            "plik": zrodlo["plik"],
            "warstwa": warstwa,
            "data": datetime.date.today().isoformat(),
            "status": "OK",
        }
        wyniki.append(wynik)
        if nazwa not in dostepne_nazwy:
            wynik["status"] = "BŁĄD: brak warstwy w usłudze"
            log(f"[BŁĄD] Brak warstwy {nazwa} w usłudze")
            continue
        log(f"  Pobieranie {nazwa}")
        try:
            gdf = wfs.pobierz_warstwe(zrodlo["wfs_url"], nazwa, wersja, log)
        except Exception as blad:
            wynik["status"] = f"BŁĄD: {blad}"[:300]
            log(f"[BŁĄD] {nazwa}: {blad}")
            continue
        if gdf.empty:
            wynik["status"] = "PUSTA: brak obiektów"
            log(f"[UWAGA] {nazwa}: brak obiektów, poprzednia wersja warstwy pozostaje bez zmian")
            continue
        try:
            poprzednia = magazyn.wczytaj_warstwe(plik, warstwa)
            porownane = porownanie.porownaj(poprzednia, gdf)
            magazyn.zapisz_warstwe(plik, warstwa, gdf)
        except Exception as blad:
            wynik["status"] = f"BŁĄD zapisu: {blad}"[:300]
            log(f"[BŁĄD] {warstwa}: {blad}")
            continue
        wynik.update(
            przed=porownane["przed"],
            po=porownane["po"],
            bez_zmian=porownane["bez_zmian"],
            dodane=porownane["dodane"],
            usuniete=porownane["usuniete"],
            dodane_n=None if porownane["dodane"] is None else len(porownane["dodane"]),
            usuniete_n=None if porownane["usuniete"] is None else len(porownane["usuniete"]),
        )
        log(f"[OK] {warstwa}: {raport.opis_warstwy(wynik)}")
    zrodlo["ostatnia_aktualizacja"] = datetime.datetime.now().isoformat(timespec="minutes")
    return wyniki


def aktualizuj(konfiguracja, zrodla, log=print, formaty=("xlsx",)):
    """Aktualizuje podane źródła, zapisuje konfigurację i raporty. Zwraca listę ścieżek raportów."""
    folder = magazyn.folder_danych(konfiguracja)
    zaczeto = datetime.datetime.now()
    linie, wyniki = [], []

    def raportuj(linia):
        linie.append(linia)
        log(linia)

    raportuj(f"Start aktualizacji: {zaczeto:%Y-%m-%d %H:%M}, folder: {folder}")
    for zrodlo in zrodla:
        raportuj(f"=== {zrodlo['nazwa']} ===")
        try:
            wyniki.extend(_aktualizuj_zrodlo(zrodlo, folder, konfiguracja["nazwy_warstw"], raportuj))
        except Exception as blad:
            raportuj(f"[BŁĄD] Źródło pominięte: {blad}")
            wyniki.append({
                "zrodlo": zrodlo["nazwa"],
                "plik": zrodlo["plik"],
                "warstwa": "-",
                "data": zaczeto.date().isoformat(),
                "status": f"BŁĄD źródła: {blad}"[:300],
            })
    magazyn.zapisz_konfiguracje(konfiguracja)
    sciezki = raport.zapisz(linie, wyniki, formaty, zaczeto)
    for sciezka in sciezki:
        raportuj(f"Raport zapisano: {sciezka}")
    return sciezki
