"""Klient API EZiUDP (Ewidencja Zbiorów i Usług Danych Przestrzennych, GUGiK)."""
import re

import requests

ADRES_API = "https://integracja.gugik.gov.pl/eziudp/api.php"

# tematy wg EZiUDP (kod INSPIRE i nazwa), parametr API: temat
TEMATY = [
    ("1.1", "Systemy odniesienia za pomocą współrzędnych"),
    ("1.2", "Systemy siatek geograficznych"),
    ("1.3", "Nazwy geograficzne"),
    ("1.4", "Jednostki administracyjne"),
    ("1.5", "Adresy"),
    ("1.6", "Działki ewidencji gruntów"),
    ("1.7", "Sieci transportowe"),
    ("1.8", "Hydrografia"),
    ("1.9", "Obszary chronione"),
    ("2.1", "Ukształtowanie terenu"),
    ("2.2", "Użytkowanie ziemi"),
    ("2.3", "Ortoobrazy"),
    ("2.4", "Geologia"),
    ("3.1", "Jednostki statystyczne"),
    ("3.2", "Budynki"),
    ("3.3", "Gleba"),
    ("3.4", "Zagospodarowanie przestrzenne"),
    ("3.5", "Zdrowie i bezpieczeństwo ludności"),
    ("3.6", "Usługi użyteczności publicznej i służby państwowe"),
    ("3.7", "Urządzenia do monitorowania środowiska"),
    ("3.8", "Obiekty produkcyjne i przemysłowe"),
    ("3.9", "Obiekty rolnicze oraz akwakultury"),
    ("3.10", "Rozmieszczenie ludności (demografia)"),
    ("3.11", "Gospodarowanie obszarem, strefy ograniczone i regulacyjne oraz jednostki sprawozdawcze"),
    ("3.12", "Strefy zagrożenia naturalnego"),
    ("3.13", "Warunki atmosferyczne"),
]


def szukaj_zbiorow(rodzaj="", teryt="", zbior="", temat=""):
    """Zwraca zbiory danych z usługą pobierania, pasujące do podanych kryteriów."""
    parametry = {
        "format": "json",
        "usluga": "pobierania",
        "rodzaj": rodzaj,
        "teryt": teryt,
        "zbior": zbior,
        "temat": temat,
    }
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
