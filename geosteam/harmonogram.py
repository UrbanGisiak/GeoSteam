"""Harmonogram cyklicznej aktualizacji: kiedy uruchomić kolejną aktualizację wszystkich źródeł."""
import datetime


def nastepne_uruchomienie(harmonogram):
    """Termin kolejnej aktualizacji albo None, gdy harmonogram jest wyłączony lub jeszcze nie działał."""
    if not harmonogram["wlaczony"] or harmonogram["ostatnie_uruchomienie"] is None:
        return None
    ostatnie = datetime.datetime.fromisoformat(harmonogram["ostatnie_uruchomienie"])
    return ostatnie + datetime.timedelta(minutes=harmonogram["co_minut"])


def czy_pora(harmonogram, teraz):
    if not harmonogram["wlaczony"]:
        return False
    nastepne = nastepne_uruchomienie(harmonogram)
    return nastepne is None or teraz >= nastepne
