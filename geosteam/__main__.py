"""Start aplikacji: bez argumentów otwiera okno, z opcją --aktualizuj aktualizuje wszystkie źródła w konsoli."""
import sys

from . import aktualizacja, magazyn, raport


def main():
    if "--aktualizuj" in sys.argv:
        konfiguracja = magazyn.wczytaj_konfiguracje()
        formaty = raport.FORMATY[magazyn.wczytaj_ustawienia()["format_raportu"]]
        aktualizacja.aktualizuj(konfiguracja, konfiguracja["zrodla"], lambda linia: print(linia, flush=True), formaty)
    else:
        from . import gui

        gui.uruchom()


if __name__ == "__main__":
    main()
