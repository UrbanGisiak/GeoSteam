"""Punkt wejścia dla PyInstaller (plik GeoSteam.exe). Zwykłe uruchomienie: python -m geosteam."""
import os
import sys
import traceback


def _zglos_blad(tresc):
    """Exe bez konsoli nie pokazuje błędów, więc zapisujemy je obok programu i pokazujemy okno."""
    sciezka = os.path.join(os.path.dirname(sys.executable), "blad.txt")
    with open(sciezka, "w", encoding="utf-8") as plik:
        plik.write(tresc)
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, f"Blad uruchomienia. Szczegoly w pliku:\n{sciezka}", "GeoSteam", 0x10)


if __name__ == "__main__":
    try:
        from geosteam.__main__ import main

        main()
    except BaseException:
        if not getattr(sys, "frozen", False):
            raise
        if sys.stderr:
            traceback.print_exc()
        _zglos_blad(traceback.format_exc())
        sys.exit(1)  # Harmonogram zadań Windows ma widzieć błąd
