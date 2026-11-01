"""Okno aplikacji. Tkinter jest w standardowym instalatorze Pythona dla Windows, więc nie trzeba go dokładać."""
import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import aktualizacja, eziudp, magazyn, wfs

RODZAJE = ["wszystkie", "centralne", "wojewodztwa", "powiaty", "gminy"]


class Aplikacja:
    def __init__(self, okno):
        self.okno = okno
        self.konfiguracja = magazyn.wczytaj_konfiguracje()
        self.kolejka = queue.Queue()
        self.zajete = False
        self.zbiory = []  # wyniki wyszukiwania w EZiUDP
        self.wybrany_zbior = None
        self.uslugi = []  # adresy usług pobierania wybranego zbioru
        self.warstwy_wfs = []  # (nazwa, tytuł) warstw załadowanych z usługi
        self.adres_wfs = None  # usługa, z której załadowano warstwy

        okno.title("Pobieranie danych GIS - EZiUDP / WFS")
        okno.geometry("1000x880")
        self._zbuduj()
        self._odswiez_zrodla()
        self._przetwarzaj_kolejke()

    # --- budowa okna ---

    def _zbuduj(self):
        glowna = ttk.Frame(self.okno, padding=8)
        glowna.pack(fill="both", expand=True)
        self._sekcja_szukania(glowna)
        self._sekcja_uslug(glowna)
        self._sekcja_zrodel(glowna)
        self._sekcja_dziennika(glowna)

    def _sekcja_szukania(self, rodzic):
        ramka = ttk.LabelFrame(rodzic, text="1. Wyszukaj zbiór w katalogu EZiUDP", padding=6)
        ramka.pack(fill="both", expand=True, pady=(0, 6))
        wiersz = ttk.Frame(ramka)
        wiersz.pack(fill="x")
        self.rodzaj = tk.StringVar(value="wszystkie")
        self.teryt = tk.StringVar()
        self.nazwa_zbioru = tk.StringVar()
        ttk.Label(wiersz, text="Rodzaj:").pack(side="left")
        ttk.Combobox(wiersz, textvariable=self.rodzaj, values=RODZAJE, state="readonly", width=12).pack(side="left", padx=(4, 12))
        ttk.Label(wiersz, text="TERYT:").pack(side="left")
        ttk.Entry(wiersz, textvariable=self.teryt, width=10).pack(side="left", padx=(4, 12))
        ttk.Label(wiersz, text="Nazwa zbioru:").pack(side="left")
        ttk.Entry(wiersz, textvariable=self.nazwa_zbioru, width=32).pack(side="left", padx=(4, 12))
        ttk.Button(wiersz, text="Szukaj", command=self._szukaj).pack(side="left")
        self.tabela_zbiorow = self._tabela(
            ramka, [("idiip", "Identyfikator", 130), ("zbior", "Zbiór", 430), ("organ", "Organ", 320)], wysokosc=6
        )
        self.tabela_zbiorow.bind("<<TreeviewSelect>>", self._wybrano_zbior)

    def _sekcja_uslug(self, rodzic):
        ramka = ttk.LabelFrame(rodzic, text="2. Usługi pobierania zbioru i warstwy WFS", padding=6)
        ramka.pack(fill="both", expand=True, pady=(0, 6))
        lewa = ttk.Frame(ramka)
        lewa.pack(side="left", fill="both", expand=True, padx=(0, 6))
        prawa = ttk.Frame(ramka)
        prawa.pack(side="left", fill="both", expand=True)
        ttk.Label(lewa, text="Usługi pobierania (WFS jest obsługiwany):").pack(anchor="w")
        self.lista_uslug = self._lista(lewa, wysokosc=5, tryb="browse")
        ttk.Button(lewa, text="Pokaż warstwy WFS", command=self._pokaz_warstwy).pack(anchor="w", pady=4)
        ttk.Label(prawa, text="Warstwy usługi (bez zaznaczenia - wszystkie):").pack(anchor="w")
        self.lista_warstw = self._lista(prawa, wysokosc=5, tryb="extended")
        ttk.Button(prawa, text="Dodaj do listy źródeł", command=self._dodaj_zrodlo).pack(anchor="w", pady=4)

    def _sekcja_zrodel(self, rodzic):
        ramka = ttk.LabelFrame(rodzic, text="3. Źródła i aktualizacja", padding=6)
        ramka.pack(fill="both", expand=True, pady=(0, 6))
        self.tabela_zrodel = self._tabela(
            ramka,
            [("nazwa", "Źródło", 380), ("plik", "Plik GeoPackage", 170), ("warstwy", "Warstwy", 80),
             ("aktualizacja", "Ostatnia aktualizacja", 150)],
            wysokosc=6,
            tryb="extended",
        )
        przyciski = ttk.Frame(ramka)
        przyciski.pack(fill="x", pady=4)
        ttk.Button(przyciski, text="Aktualizuj zaznaczone", command=self._aktualizuj_zaznaczone).pack(side="left")
        ttk.Button(przyciski, text="Aktualizuj wszystkie", command=self._aktualizuj_wszystkie).pack(side="left", padx=4)
        ttk.Button(przyciski, text="Usuń z listy", command=self._usun_zrodlo).pack(side="left")
        ttk.Button(przyciski, text="Otwórz folder danych", command=self._otworz_folder).pack(side="right")
        ttk.Button(przyciski, text="Zmień folder danych...", command=self._zmien_folder).pack(side="right", padx=4)
        self.etykieta_folderu = ttk.Label(ramka, text="")
        self.etykieta_folderu.pack(anchor="w")

    def _sekcja_dziennika(self, rodzic):
        ramka = ttk.LabelFrame(rodzic, text="Dziennik", padding=6)
        ramka.pack(fill="both", expand=True)
        obszar = ttk.Frame(ramka)
        obszar.pack(fill="both", expand=True)
        self.dziennik = tk.Text(obszar, height=10, wrap="word", state="disabled")
        przewijanie = ttk.Scrollbar(obszar, orient="vertical", command=self.dziennik.yview)
        self.dziennik.configure(yscrollcommand=przewijanie.set)
        self.dziennik.pack(side="left", fill="both", expand=True)
        przewijanie.pack(side="right", fill="y")

    def _tabela(self, rodzic, kolumny, wysokosc, tryb="browse"):
        ramka = ttk.Frame(rodzic)
        ramka.pack(fill="both", expand=True, pady=4)
        tabela = ttk.Treeview(
            ramka, columns=[id_ for id_, _, _ in kolumny], show="headings", height=wysokosc, selectmode=tryb
        )
        for id_, naglowek, szerokosc in kolumny:
            tabela.heading(id_, text=naglowek)
            tabela.column(id_, width=szerokosc)
        przewijanie = ttk.Scrollbar(ramka, orient="vertical", command=tabela.yview)
        tabela.configure(yscrollcommand=przewijanie.set)
        tabela.pack(side="left", fill="both", expand=True)
        przewijanie.pack(side="right", fill="y")
        return tabela

    def _lista(self, rodzic, wysokosc, tryb):
        ramka = ttk.Frame(rodzic)
        ramka.pack(fill="both", expand=True)
        lista = tk.Listbox(ramka, height=wysokosc, selectmode=tryb, exportselection=False)
        przewijanie = ttk.Scrollbar(ramka, orient="vertical", command=lista.yview)
        lista.configure(yscrollcommand=przewijanie.set)
        lista.pack(side="left", fill="both", expand=True)
        przewijanie.pack(side="right", fill="y")
        return lista

    # --- praca w tle i dziennik ---

    def _dopisz(self, linia):
        self.dziennik.configure(state="normal")
        self.dziennik.insert("end", linia + "\n")
        self.dziennik.see("end")
        self.dziennik.configure(state="disabled")

    def _log_z_watku(self, linia):
        self.kolejka.put(lambda: self._dopisz(linia))

    def _przetwarzaj_kolejke(self):
        # Tkinter nie jest bezpieczny wątkowo, więc wątki tylko wkładają funkcje do kolejki
        try:
            while True:
                self.kolejka.get_nowait()()
        except queue.Empty:
            pass
        self.okno.after(100, self._przetwarzaj_kolejke)

    def _uruchom(self, praca, po_zakonczeniu=None):
        if self.zajete:
            messagebox.showinfo("Pobieranie", "Trwa inna operacja, poczekaj na jej zakończenie.")
            return
        self.zajete = True

        def watek():
            try:
                wynik = praca()
            except Exception as blad:
                wynik = blad
            self.kolejka.put(lambda: self._zakoncz(wynik, po_zakonczeniu))

        threading.Thread(target=watek, daemon=True).start()

    def _zakoncz(self, wynik, po_zakonczeniu):
        self.zajete = False
        if isinstance(wynik, Exception):
            self._dopisz(f"[BŁĄD] {wynik}")
            messagebox.showerror("Błąd", str(wynik))
        elif po_zakonczeniu:
            po_zakonczeniu(wynik)

    # --- wyszukiwanie w EZiUDP ---

    def _szukaj(self):
        rodzaj = "" if self.rodzaj.get() == "wszystkie" else self.rodzaj.get()
        teryt, nazwa = self.teryt.get().strip(), self.nazwa_zbioru.get().strip()
        self._uruchom(lambda: eziudp.szukaj_zbiorow(rodzaj, teryt, nazwa), self._pokaz_zbiory)

    def _pokaz_zbiory(self, zbiory):
        self.zbiory = zbiory
        self.tabela_zbiorow.delete(*self.tabela_zbiorow.get_children())
        for i, zbior in enumerate(zbiory):
            self.tabela_zbiorow.insert("", "end", iid=str(i), values=(zbior["idiip"], zbior["zbior"], zbior["organ"]))
        self._dopisz(f"Znaleziono zbiorów z usługą pobierania: {len(zbiory)}")

    def _wybrano_zbior(self, _zdarzenie):
        zaznaczone = self.tabela_zbiorow.selection()
        if not zaznaczone:
            return
        self.wybrany_zbior = self.zbiory[int(zaznaczone[0])]
        self.uslugi = [eziudp.oczysc_adres(adres) for adres in self.wybrany_zbior["uslugi"]["pobierania"]]
        self.lista_uslug.delete(0, "end")
        for adres in self.uslugi:
            oznaczenie = "[WFS]" if eziudp.czy_wfs(adres) else "[inna usługa]"
            self.lista_uslug.insert("end", f"{oznaczenie} {adres}")
        self.lista_warstw.delete(0, "end")
        self.warstwy_wfs = []
        self.adres_wfs = None

    def _pokaz_warstwy(self):
        wybrane = self.lista_uslug.curselection()
        if not wybrane:
            messagebox.showinfo("Pobieranie", "Wybierz usługę z listy.")
            return
        adres = self.uslugi[wybrane[0]]
        if not eziudp.czy_wfs(adres):
            messagebox.showinfo("Pobieranie", "Ta aplikacja obsługuje tylko usługi WFS.")
            return

        def po_zakonczeniu(wynik):
            _wersja, self.warstwy_wfs = wynik
            self.adres_wfs = adres
            self.lista_warstw.delete(0, "end")
            for nazwa, tytul in self.warstwy_wfs:
                self.lista_warstw.insert("end", f"{nazwa}  ({tytul})")
            self._dopisz(f"Warstw w usłudze: {len(self.warstwy_wfs)}")

        self._uruchom(lambda: wfs.pobierz_capabilities(adres, self._log_z_watku), po_zakonczeniu)

    def _dodaj_zrodlo(self):
        if self.wybrany_zbior is None or self.adres_wfs is None:
            messagebox.showinfo("Dodawanie", "Wybierz zbiór i usługę WFS, potem kliknij 'Pokaż warstwy WFS'.")
            return
        warstwy = [self.warstwy_wfs[i][0] for i in self.lista_warstw.curselection()]
        if not warstwy and not messagebox.askyesno("Dodawanie", "Nie zaznaczono warstw. Dodać wszystkie warstwy usługi?"):
            return
        if any(z["wfs_url"] == self.adres_wfs and z["warstwy"] == warstwy for z in self.konfiguracja["zrodla"]):
            messagebox.showinfo("Dodawanie", "To samo źródło jest już na liście.")
            return
        zrodlo = {
            "nazwa": self.wybrany_zbior["zbior"],
            "wfs_url": self.adres_wfs,
            "plik": self.wybrany_zbior["idiip"].replace(".", "_") + ".gpkg",
            "warstwy": warstwy,
            "ostatnia_aktualizacja": None,
        }
        self.konfiguracja["zrodla"].append(zrodlo)
        magazyn.zapisz_konfiguracje(self.konfiguracja)
        self._odswiez_zrodla()
        self._dopisz(f"Dodano źródło: {zrodlo['nazwa']} ({len(warstwy) or 'wszystkie'} warstw)")

    # --- źródła i aktualizacja ---

    def _odswiez_zrodla(self):
        self.tabela_zrodel.delete(*self.tabela_zrodel.get_children())
        for i, zrodlo in enumerate(self.konfiguracja["zrodla"]):
            self.tabela_zrodel.insert(
                "",
                "end",
                iid=str(i),
                values=(
                    zrodlo["nazwa"],
                    zrodlo["plik"],
                    len(zrodlo["warstwy"]) or "wszystkie",
                    zrodlo["ostatnia_aktualizacja"] or "-",
                ),
            )
        self.etykieta_folderu.configure(text=f"Folder danych: {magazyn.folder_danych(self.konfiguracja)}")

    def _aktualizuj_zaznaczone(self):
        zaznaczone = self.tabela_zrodel.selection()
        if not zaznaczone:
            messagebox.showinfo("Aktualizacja", "Zaznacz źródła na liście.")
            return
        self._aktualizuj([self.konfiguracja["zrodla"][int(i)] for i in zaznaczone])

    def _aktualizuj_wszystkie(self):
        self._aktualizuj(self.konfiguracja["zrodla"])

    def _aktualizuj(self, zrodla):
        if not zrodla:
            messagebox.showinfo("Aktualizacja", "Lista źródeł jest pusta.")
            return
        self._uruchom(
            lambda: aktualizacja.aktualizuj(self.konfiguracja, zrodla, self._log_z_watku),
            lambda raport: self._zakoncz_aktualizacje(raport),
        )

    def _zakoncz_aktualizacje(self, sciezka_raportu):
        self._odswiez_zrodla()
        self._dopisz(f"Gotowe. Raport: {sciezka_raportu}")

    def _usun_zrodlo(self):
        zaznaczone = self.tabela_zrodel.selection()
        if not zaznaczone:
            return
        if not messagebox.askyesno("Usuwanie", "Usunąć zaznaczone źródła z listy?\nPliki GeoPackage zostaną na dysku."):
            return
        for i in sorted((int(i) for i in zaznaczone), reverse=True):
            del self.konfiguracja["zrodla"][i]
        magazyn.zapisz_konfiguracje(self.konfiguracja)
        self._odswiez_zrodla()

    def _zmien_folder(self):
        wybrany = filedialog.askdirectory(initialdir=magazyn.folder_danych(self.konfiguracja))
        if wybrany:
            self.konfiguracja["folder_danych"] = wybrany
            magazyn.zapisz_konfiguracje(self.konfiguracja)
            self._odswiez_zrodla()

    def _otworz_folder(self):
        folder = magazyn.folder_danych(self.konfiguracja)
        os.makedirs(folder, exist_ok=True)
        os.startfile(folder)  # aplikacja jest przeznaczona dla Windows


def uruchom():
    okno = tk.Tk()
    Aplikacja(okno)
    okno.mainloop()
