"""Klient API EZiUDP (Ewidencja Zbiorów i Usług Danych Przestrzennych, GUGiK)."""
import re

import requests

ADRES_API = "https://integracja.gugik.gov.pl/eziudp/api.php"


def szukaj_zbiorow(rodzaj="", teryt="", zbior=""):
    """Zwraca zbiory danych z usługą pobierania, pasujące do podanych kryteriów."""
    parametry = {"format": "json", "usluga": "pobierania", "rodzaj": rodzaj, "teryt": teryt, "zbior": zbior}
    odpowiedz = requests.get(ADRES_API, params={k: v for k, v in parametry.items() if v}, timeout=120)
    odpowiedz.raise_for_status()
    dane = odpowiedz.json()
    # zapytanie z parametrami zwraca listę, a bez parametrów słownik
    if isinstance(dane, list):
        dane = dane[0]
    return dane["data"]


def oczysc_adres(adres):
    """Usuwa prefiks typu usługi, np. 'WCS=https://...' -> 'https://...'."""
    return re.sub(r"^[A-Za-z]+=(?=https?://)", "", adres)


def czy_wfs(adres):
    """Rozpoznaje usługę WFS po adresie. Usługi pobierania są mieszane (WFS, ATOM, WCS, SOS...)."""
    return "wfs" in adres.lower()
