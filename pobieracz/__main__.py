"""Start aplikacji: bez argumentów otwiera okno, z opcją --aktualizuj aktualizuje wszystkie źródła w konsoli."""
import sys

from . import aktualizacja, magazyn


def main():
    if "--aktualizuj" in sys.argv:
        konfiguracja = magazyn.wczytaj_konfiguracje()
        aktualizacja.aktualizuj(konfiguracja, konfiguracja["zrodla"], lambda linia: print(linia, flush=True))
    else:
        from . import gui

        gui.uruchom()


if __name__ == "__main__":
    main()
