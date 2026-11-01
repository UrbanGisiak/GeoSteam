"""Porównanie obiektów warstwy przed i po pobraniu: bez zmian, dodane, usunięte."""
import collections
import hashlib

import shapely

# pola techniczne, których zmiana między pobraniami nie oznacza zmiany danych
POMIJANE_KOLUMNY = {"geometry", "data_pobrania", "fid", "gml_id", "id"}


def _sygnatury(gdf, kolumny):
    geometrie = shapely.normalize(gdf.geometry.to_numpy())
    wkb = shapely.to_wkb(shapely.set_precision(geometrie, 0.001))  # zaokrąglenie do 1 mm
    sygnatury = []
    for geometria, wiersz in zip(wkb, gdf[kolumny].itertuples(index=False)):
        skrot = hashlib.sha1(geometria or b"")
        skrot.update("\x1f".join(str(wartosc) for wartosc in wiersz).encode("utf-8"))
        sygnatury.append(skrot.hexdigest())
    return sygnatury


def porownaj(stara, nowa):
    """Porównuje obiekty starej i nowej wersji warstwy. stara=None oznacza pierwsze pobranie.

    Zwraca słownik z liczbami oraz obiektami dodanymi i usuniętymi (GeoDataFrame).
    """
    if stara is None:
        return {"przed": None, "po": len(nowa), "bez_zmian": 0, "dodane": None, "usuniete": None}
    kolumny = sorted(
        k for k in nowa.columns if k in stara.columns and k.lower() not in POMIJANE_KOLUMNY
    )
    sig_stare = _sygnatury(stara, kolumny)
    sig_nowe = _sygnatury(nowa, kolumny)

    pozostale = collections.Counter(sig_stare)
    dodane = []
    for i, sygnatura in enumerate(sig_nowe):
        if pozostale[sygnatura] > 0:
            pozostale[sygnatura] -= 1
        else:
            dodane.append(i)

    pozostale = collections.Counter(sig_nowe)
    usuniete = []
    for i, sygnatura in enumerate(sig_stare):
        if pozostale[sygnatura] > 0:
            pozostale[sygnatura] -= 1
        else:
            usuniete.append(i)

    return {
        "przed": len(stara),
        "po": len(nowa),
        "bez_zmian": len(sig_nowe) - len(dodane),
        "dodane": nowa.iloc[dodane],
        "usuniete": stara.iloc[usuniete],
    }
