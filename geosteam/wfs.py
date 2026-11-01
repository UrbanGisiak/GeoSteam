"""Obsługa usług WFS: lista warstw (GetCapabilities) i pobieranie obiektów stronami (GetFeature)."""
import os
import tempfile
import urllib.parse
import xml.etree.ElementTree as ET

import geopandas as gpd
import pandas as pd
import requests
import urllib3

UKLAD = "EPSG:2180"  # PL-1992, układ używany w zbiorach GUGiK
ROZMIAR_STRONY = 1000
# kolejność prób: GML 3.2 (WFS 2.0), GML 3.1.1 (WFS 1.1), domyślny format serwera
FORMATY = ["application/gml+xml; version=3.2", "text/xml; subtype=gml/3.1.1", None]


def _nazwa(znacznik):
    return znacznik.rsplit("}", 1)[-1]


def _tekst_dziecka(element, nazwa):
    for dziecko in element:
        if _nazwa(dziecko.tag) == nazwa:
            return (dziecko.text or "").strip()
    return ""


def _adres_bazowy(adres):
    """Usuwa parametry zapytania z adresu, np. ?service=WFS&request=GetCapabilities."""
    return urllib.parse.urlsplit(adres)._replace(query="").geturl()


def _pobierz(adres, parametry, log, timeout=(30, 600)):
    try:
        odpowiedz = requests.get(adres, params=parametry, timeout=timeout)
    except requests.exceptions.SSLError:
        # część serwerów ma niepełne łańcuchy certyfikatów, dlatego ponawiamy bez weryfikacji
        log(f"[UWAGA] Błąd certyfikatu SSL, ponawiam bez weryfikacji: {adres}")
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        odpowiedz = requests.get(adres, params=parametry, timeout=timeout, verify=False)
    odpowiedz.raise_for_status()
    return odpowiedz.content


def pobierz_capabilities(adres, log=print, timeout=(30, 600)):
    """Zwraca wersję usługi WFS i listę (nazwa, tytuł) jej warstw."""
    tresc = _pobierz(_adres_bazowy(adres), {"service": "WFS", "request": "GetCapabilities"}, log, timeout)
    korzen = ET.fromstring(tresc)
    if _nazwa(korzen.tag) != "WFS_Capabilities":
        raise ValueError("Adres nie zwraca dokumentu WFS (GetCapabilities)")
    wersja = korzen.get("version", "1.1.0")
    warstwy = []
    for element in korzen.iter():
        if _nazwa(element.tag) == "FeatureType":
            nazwa = _tekst_dziecka(element, "Name")
            if nazwa:
                warstwy.append((nazwa, _tekst_dziecka(element, "Title") or nazwa))
    return wersja, warstwy


def dostepne_uslugi(adresy, log=print):
    """Z podanych adresów zostawia tylko usługi WFS, które zgłaszają co najmniej jedną warstwę."""
    uslugi = []
    for adres in adresy:
        try:
            wersja, warstwy = pobierz_capabilities(adres, log, timeout=(15, 60))
        except Exception as blad:  # nie-WFS, błąd sieci albo HTML zamiast XML
            log(f"[INFO] Pomijam {adres}: {type(blad).__name__} {str(blad)[:120]}")
            continue
        if warstwy:
            uslugi.append({"adres": adres, "wersja": wersja, "warstwy": warstwy})
    return uslugi


def _parametry_getfeature(nazwa, wersja, start, limit):
    parametry = {"service": "WFS", "version": wersja, "request": "GetFeature", "srsName": UKLAD}
    if wersja.startswith("2"):
        parametry["typeNames"] = nazwa
        if limit:
            parametry["count"] = limit
    else:
        parametry["typeName"] = nazwa
        if limit:
            parametry["maxFeatures"] = limit
    if start:
        parametry["startIndex"] = start
    return parametry


def _opis_bledu(tresc):
    try:
        korzen = ET.fromstring(tresc)
        teksty = [e.text for e in korzen.iter() if _nazwa(e.tag) == "ExceptionText" and e.text]
        if teksty:
            return " ".join("; ".join(teksty).split())[:200]
    except ET.ParseError:
        pass
    return " ".join(tresc[:200].decode("utf-8", "replace").split())


def _czytaj_gml(tresc):
    with tempfile.TemporaryDirectory() as katalog:
        sciezka = os.path.join(katalog, "odpowiedz.gml")
        with open(sciezka, "wb") as plik:
            plik.write(tresc)
        return gpd.read_file(sciezka)


def _pobierz_strone(adres, nazwa, wersja, start, log, limit=ROZMIAR_STRONY):
    bledy = []
    for format_wyjscia in FORMATY:
        parametry = _parametry_getfeature(nazwa, wersja, start, limit)
        if format_wyjscia:
            parametry["outputFormat"] = format_wyjscia
        try:
            tresc = _pobierz(adres, parametry, log)
        except requests.RequestException as blad:
            bledy.append(str(blad))
            continue
        if b"ExceptionReport" in tresc[:4096] or b"ServiceException" in tresc[:4096]:
            bledy.append(_opis_bledu(tresc))
            continue
        try:
            return _czytaj_gml(tresc)
        except Exception as blad:  # GDAL nie rozpoznał odpowiedzi jako GML
            bledy.append(str(blad))
    raise RuntimeError("; ".join(bledy))


def _pobierz_stronami(adres, nazwa, wersja, log):
    strony = []
    start = 0
    while True:
        strona = _pobierz_strone(adres, nazwa, wersja, start, log)
        # serwer ignorujący startIndex zwraca w kółko tę samą porcję, nie można go w ten sposób pobrać
        if strony and len(strona) and strona.geometry.iloc[0] == strony[-1].geometry.iloc[0]:
            raise RuntimeError("serwer ignoruje startIndex")
        strony.append(strona)
        log(f"    od obiektu {start}: {len(strona)}")
        if len(strona) < ROZMIAR_STRONY:
            return pd.concat(strony, ignore_index=True)
        start += ROZMIAR_STRONY


def pobierz_warstwe(adres, nazwa, wersja, log=print):
    """Pobiera wszystkie obiekty warstwy. Gdy stronicowanie zawiedzie, warstwa idzie jednym żądaniem."""
    adres = _adres_bazowy(adres)
    try:
        return _pobierz_stronami(adres, nazwa, wersja, log)
    except Exception as blad:
        log(f"[UWAGA] Stronicowanie nie działa ({str(blad)[:200]}), pobieram warstwę jednym żądaniem")
    return _pobierz_strone(adres, nazwa, wersja, 0, log, limit=None)
