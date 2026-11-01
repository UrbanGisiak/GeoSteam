"""Raporty z pobierania: plik tekstowy (txt) i arkusz Excel (xlsx)."""
import os

import pandas as pd

from . import magazyn

FORMATY = {"xlsx": ("xlsx",), "txt": ("txt",), "txt i xlsx": ("txt", "xlsx")}
MAX_ZMIAN_NA_WARSTWE = 20_000  # ograniczenie rozmiaru arkusza; reszta jest liczona, ale nie wypisywana
IGNOROWANE_W_ZMIANACH = {"geometry", "data_pobrania"}


def opis_warstwy(wynik):
    if wynik["status"] != "OK":
        return wynik["status"]
    if wynik["przed"] is None:
        return f"pierwsze pobranie, {wynik['po']} obiektów"
    return (
        f"przed {wynik['przed']}, po {wynik['po']}, bez zmian {wynik['bez_zmian']}, "
        f"dodane {wynik['dodane_n']}, usunięte {wynik['usuniete_n']}"
    )


def _tekst_txt(sciezka, linie, wyniki, zaczeto):
    podsumowanie = [f"{w['zrodlo']} / {w['warstwa']}: {opis_warstwy(w)}" for w in wyniki]
    tresc = [
        f"RAPORT GEOSTEAM - start {zaczeto:%Y-%m-%d %H:%M}",
        "",
        "PODSUMOWANIE",
        *podsumowanie,
        "",
        "DZIENNIK",
        *linie,
    ]
    with open(sciezka, "w", encoding="utf-8") as plik:
        plik.write("\n".join(tresc) + "\n")


def _wiersz_zmiany(zrodlo, warstwa, typ, wiersz):
    atrybuty = "; ".join(
        f"{kolumna}={wartosc}" for kolumna, wartosc in wiersz.items() if kolumna not in IGNOROWANE_W_ZMIANACH
    )
    return {"Źródło": zrodlo, "Warstwa": warstwa, "Zmiana": typ, "Atrybuty": atrybuty[:1000]}


def _tekst_xlsx(sciezka, wyniki):
    podsumowanie, zmiany = [], []
    for w in wyniki:
        uwaga = ""
        if w["status"] == "OK" and w["przed"] is not None:
            for typ, gdf in (("dodany", w["dodane"]), ("usunięty", w["usuniete"])):
                for _, wiersz in gdf.head(MAX_ZMIAN_NA_WARSTWE).iterrows():
                    zmiany.append(_wiersz_zmiany(w["zrodlo"], w["warstwa"], typ, wiersz))
                if len(gdf) > MAX_ZMIAN_NA_WARSTWE:
                    uwaga = f"pokazano {MAX_ZMIAN_NA_WARSTWE} z {len(gdf)} zmian ({typ})"
        podsumowanie.append({
            "Źródło": w["zrodlo"],
            "Plik": w["plik"],
            "Warstwa": w["warstwa"],
            "Data": w["data"],
            "Przed": w.get("przed"),
            "Po": w.get("po"),
            "Bez zmian": w.get("bez_zmian"),
            "Dodane": w.get("dodane_n"),
            "Usunięte": w.get("usuniete_n"),
            "Status": w["status"],
            "Uwaga": uwaga,
        })

    with pd.ExcelWriter(sciezka, engine="openpyxl") as arkusz:
        liczby = ["Przed", "Po", "Bez zmian", "Dodane", "Usunięte"]
        for nazwa, dane in (("Podsumowanie", podsumowanie), ("Zmiany", zmiany)):
            ramka = pd.DataFrame(dane)
            if nazwa == "Podsumowanie":
                ramka = ramka.astype({kolumna: "Int64" for kolumna in liczby})
            ramka.to_excel(arkusz, sheet_name=nazwa, index=False)
            ws = arkusz.sheets[nazwa]
            for kolumna in ws.columns:
                szerokosc = max((len(str(komorka.value or "")) for komorka in kolumna), default=8)
                ws.column_dimensions[kolumna[0].column_letter].width = min(szerokosc + 2, 60)
            ws.freeze_panes = "A2"


def zapisz(linie, wyniki, formaty, zaczeto):
    """Zapisuje raporty w wybranych formatach. Zwraca listę ścieżek plików."""
    os.makedirs(magazyn.KATALOG_RAPORTOW, exist_ok=True)
    znacznik = zaczeto.strftime("%Y-%m-%d_%H-%M-%S")
    sciezki = []
    if "txt" in formaty:
        sciezka = os.path.join(magazyn.KATALOG_RAPORTOW, f"raport_{znacznik}.txt")
        _tekst_txt(sciezka, linie, wyniki, zaczeto)
        sciezki.append(sciezka)
    if "xlsx" in formaty:
        sciezka = os.path.join(magazyn.KATALOG_RAPORTOW, f"raport_{znacznik}.xlsx")
        _tekst_xlsx(sciezka, wyniki)
        sciezki.append(sciezka)
    return sciezki
