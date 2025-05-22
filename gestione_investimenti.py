import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import json
from datetime import datetime
import yfinance as yf
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

percorso_file = "data/investimenti.json"

if os.path.exists(percorso_file):
    try:
        with open(percorso_file, "r") as f:
            contenuto = f.read().strip()
            if contenuto:
                investimenti = json.loads(contenuto)
            else:
                investimenti = {}
    except json.JSONDecodeError:
        print("Errore nel parsing del file JSON. Il file potrebbe essere corrotto.")
        investimenti = {}
else:
    investimenti = {}

def calcola_valore_portafoglio(investimenti):
    valore_totale = 0.0

    for ticker, dati in investimenti.items():
        try:
            info = yf.Ticker(ticker).info
            prezzo_attuale = info.get("regularMarketPrice")

            if prezzo_attuale is not None:
                valore_totale += prezzo_attuale * dati["quantita"]
        except Exception as e:
            print(f"Errore nel recupero del prezzo per {ticker}: {e}")

    return valore_totale

def carica_storico():
    percorso_storico = "data/storico_portafoglio.json"
    try:
        with open(percorso_storico, "r") as f:
            storico = json.load(f)
            # Lista di tuple (data stringa, valore)
            return [(item["data"], item["valore"]) for item in storico]
    except FileNotFoundError:
        return []

def salva_valore_portafoglio(valore_totale):
    percorso_storico = "data/storico_portafoglio.json"

    try:
        with open(percorso_storico, "r") as f:
            storico = json.load(f)
    except FileNotFoundError:
        storico = []

    oggi = datetime.now().strftime("%Y-%m-%d")

    # se più movimenti nella stessa data
    if storico and storico[-1]["data"] == oggi:
        storico[-1]["valore"] = valore_totale
    else:
        storico.append({"data": oggi, "valore": valore_totale})

    with open(percorso_storico, "w") as f:
        json.dump(storico, f, indent=2)

def mostra_grafico_andamento(frame_genitore, percorso_storico="data/storico_portafoglio.json"):
    # Pulisce eventuali grafici o widget precedenti
    for widget in frame_genitore.winfo_children():
        widget.destroy()

    try:
        with open(percorso_storico, "r") as f:
            storico = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        tk.Label(frame_genitore, text="Nessun dato disponibile per il grafico.", bg="lightgray", height=5).pack(fill="x")
        return

    if not storico or len(storico) < 2:
        tk.Label(frame_genitore, text="Dati insufficienti per generare un grafico, torna domani :P", bg="lightgray", height=5).pack(fill="x")
        return

    try:
        date = [datetime.strptime(d, "%Y-%m-%d") for d in storico.keys()]
        valori = list(storico.values())

        fig, ax = plt.subplots(figsize=(5, 2.5))
        ax.plot(date, valori, marker='o', color='green')
        ax.set_title("Valore portafoglio nel tempo")
        ax.set_xlabel("Data")
        ax.set_ylabel("Valore (€)")
        ax.grid(True)

        canvas = FigureCanvasTkAgg(fig, master=frame_genitore)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", padx=20, pady=5)
    except Exception as e:
        print(f"Errore nella generazione del grafico: {e}")
        tk.Label(frame_genitore, text="Errore nella visualizzazione del grafico.", bg="lightgray", height=5).pack(fill="x")

def calcola_pmu(storico):
    totale_costo = 0
    totale_quantita = 0

    for op in storico:
        if op["tipo"] == "acquisto":
            totale_costo += op["quantita"] * op["prezzo_unitario"]
            totale_quantita += op["quantita"]
        elif op["tipo"] == "vendita":
            totale_quantita -= op["quantita"]

    if totale_quantita == 0:
        return 0

    return totale_costo / totale_quantita

def calcola_quantita_posseduta(storico):
    return sum(
        op["quantita"] if op.get("tipo", "acquisto") == "acquisto" else -op["quantita"]
        for op in storico
    )

def recupera_info_ticker(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        if "shortName" not in info or info["regularMarketPrice"] is None:
            return None
        return {
            "nome": info["shortName"],
            "prezzo": info["regularMarketPrice"]
        }
    except Exception:
        return None

def acquista_azione(ticker, quantita, prezzo=None, data=None):
    ticker = ticker.upper()

    if prezzo is None:
        info = recupera_info_ticker(ticker)
        if not info:
            return {"successo": False, "errore": "Ticker non valido o dati non disponibili."}
        prezzo = info["prezzo"]

    if data is None:
        data = datetime.now().strftime("%Y-%m-%d")
    else:
        # Se viene passato un oggetto datetime.date, lo convertiamo in stringa
        if isinstance(data, datetime):
            data = data.strftime("%Y-%m-%d")
        elif hasattr(data, "strftime"):  # supporta anche date pure
            data = data.strftime("%Y-%m-%d")
        elif isinstance(data, str):
            pass  # già una stringa, assumiamo corretta
        else:
            return {"successo": False, "errore": "Formato data non valido."}

    operazione = {
        "tipo": "acquisto",
        "data": data,
        "quantita": quantita,
        "prezzo_unitario": prezzo
    }

    if ticker not in investimenti:
        investimenti[ticker] = []

    investimenti[ticker].append(operazione)

    with open(percorso_file, "w") as f:
        json.dump(investimenti, f, indent=4)

    valore = calcola_valore_portafoglio(investimenti)
    salva_valore_portafoglio(valore)

    return {"successo": True, "dati": operazione}

def apri_popup_acquisto():
    popup = tk.Toplevel()
    popup.title("Acquista Azione")
    larghezza = 350
    altezza = 250
    x = (popup.winfo_screenwidth() // 2) - (larghezza // 2)
    y = (popup.winfo_screenheight() // 2) - (altezza // 2)
    popup.geometry(f"{larghezza}x{altezza}+{x}+{y}")
    popup.resizable(False, False)

    # Etichette e campi base
    tk.Label(popup, text="Ticker:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
    entry_ticker = tk.Entry(popup)
    entry_ticker.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(popup, text="Quantità:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
    entry_quantita = tk.Entry(popup)
    entry_quantita.grid(row=1, column=1, padx=10, pady=5)

    usa_prezzo_attuale = tk.BooleanVar(value=True)
    check_prezzo_attuale = tk.Checkbutton(popup, text="Usa prezzo attuale", variable=usa_prezzo_attuale, command=lambda: toggle_campi_manual_price())
    check_prezzo_attuale.grid(row=2, column=0, columnspan=2, pady=5)

    # Campi per prezzo e data manuali
    tk.Label(popup, text="Prezzo (€):").grid(row=3, column=0, padx=10, pady=5, sticky="e")
    entry_prezzo = tk.Entry(popup)
    entry_prezzo.grid(row=3, column=1, padx=10, pady=5)

    tk.Label(popup, text="Data (YYYY-MM-DD):").grid(row=4, column=0, padx=10, pady=5, sticky="e")
    entry_data = tk.Entry(popup)
    entry_data.grid(row=4, column=1, padx=10, pady=5)

    # Funzione per abilitare/disabilitare i campi manuali
    def toggle_campi_manual_price():
        stato = "normal" if not usa_prezzo_attuale.get() else "disabled"
        entry_prezzo.config(state=stato)
        entry_data.config(state=stato)

    toggle_campi_manual_price()  # inizializza lo stato corretto

    def conferma_acquisto():
        ticker = entry_ticker.get().strip().upper()
        try:
            quantita = float(entry_quantita.get())
            if quantita <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Errore", "Inserisci una quantità valida.")
            return

        if usa_prezzo_attuale.get():
            risultato = acquista_azione(ticker, quantita)
        else:
            try:
                prezzo = float(entry_prezzo.get())
                data = datetime.strptime(entry_data.get(), "%Y-%m-%d").date()
            except ValueError:
                messagebox.showerror("Errore", "Prezzo o data non validi.")
                return
            risultato = acquista_azione(ticker, quantita, prezzo=prezzo, data=data)

        if risultato["successo"]:
            messagebox.showinfo("Successo", f"Acquistate {quantita} azioni di {ticker} a {risultato['dati']['prezzo_unitario']} €.")
            popup.destroy()
        else:
            messagebox.showerror("Errore", risultato["errore"])

    tk.Button(popup, text="Conferma", command=conferma_acquisto).grid(row=5, column=0, columnspan=2, pady=10)

def vendi_azione(ticker, quantita, prezzo=None, data=None):
    ticker = ticker.upper()

    if ticker not in investimenti or not investimenti[ticker]:
        return {"successo": False, "errore": "Nessuna azione registrata per questo ticker."}

    if prezzo is None:
        info = recupera_info_ticker(ticker)
        if not info:
            return {"successo": False, "errore": "Impossibile recuperare il prezzo corrente."}
        prezzo = info["prezzo"]

    if data is None:
        data = datetime.now().strftime("%Y-%m-%d")
    else:
        if isinstance(data, datetime):
            data = data.strftime("%Y-%m-%d")
        elif hasattr(data, "strftime"):
            data = data.strftime("%Y-%m-%d")
        elif isinstance(data, str):
            pass
        else:
            return {"successo": False, "errore": "Formato data non valido."}

    # Calcolo quantità posseduta
    storico = investimenti[ticker]
    quantita_posseduta = calcola_quantita_posseduta(storico)
    if quantita > quantita_posseduta:
        return {"successo": False, "errore": "Quantità non disponibile per la vendita."}

    # Calcolo PMU (prezzo medio unitario)
    pmu = calcola_pmu(storico)

    guadagno_per_azione = prezzo - pmu
    guadagno_totale = guadagno_per_azione * quantita

    operazione = {
        "tipo": "vendita",
        "data": data,
        "quantita": quantita,
        "prezzo_unitario": prezzo
    }

    investimenti[ticker].append(operazione)

    with open(percorso_file, "w") as f:
        json.dump(investimenti, f, indent=4)

    valore = calcola_valore_portafoglio(investimenti)
    salva_valore_portafoglio(valore)

    return {
        "successo": True,
        "dati": {
            "ticker": ticker,
            "quantita_venduta": quantita,
            "prezzo_vendita": prezzo,
            "pmu": pmu,
            "guadagno_per_azione": guadagno_per_azione,
            "guadagno_totale": guadagno_totale
        }
    }

def apri_popup_vendita():
    popup = tk.Toplevel()
    popup.title("Vendi Azione")

    larghezza = 350
    altezza = 300
    x = (popup.winfo_screenwidth() // 2) - (larghezza // 2)
    y = (popup.winfo_screenheight() // 2) - (altezza // 2)
    popup.geometry(f"{larghezza}x{altezza}+{x}+{y}")
    popup.resizable(False, False)

    # Etichetta e combobox per il ticker
    tk.Label(popup, text="Ticker:").grid(row=0, column=0, padx=10, pady=(15, 5), sticky="e")
    ticker_posseduti = sorted([t for t in investimenti if calcola_quantita_posseduta(investimenti[t]) > 0])
    entry_ticker = ttk.Combobox(popup, values=ticker_posseduti, state="readonly", width=18)
    entry_ticker.grid(row=0, column=1, padx=10, pady=(15, 5))

    # Etichetta e campo per la quantità
    tk.Label(popup, text="Quantità:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
    entry_quantita = tk.Entry(popup, width=20)
    entry_quantita.grid(row=1, column=1, padx=10, pady=5)

    # Etichetta quantità posseduta
    lbl_quantita_posseduta = tk.Label(popup, text="Quantità posseduta: -", font=("Arial", 9, "italic"))
    lbl_quantita_posseduta.grid(row=2, column=0, columnspan=2, pady=(10, 5))

    entry_ticker.bind("<FocusOut>", lambda e: aggiorna_quantita_posseduta())

    def aggiorna_quantita_posseduta():
        ticker = entry_ticker.get().upper()
        if ticker in investimenti:
            quantita = calcola_quantita_posseduta(investimenti[ticker])
            lbl_quantita_posseduta.config(text=f"Quantità posseduta: {quantita}")
        else:
            lbl_quantita_posseduta.config(text="Ticker non trovato.")

    # Checkbox "Usa prezzo attuale"
    usa_prezzo_attuale = tk.BooleanVar(value=True)
    check_prezzo_attuale = tk.Checkbutton(
        popup,
        text="Usa prezzo attuale",
        variable=usa_prezzo_attuale,
        command=lambda: toggle_campi_manual_price()
    )
    check_prezzo_attuale.grid(row=3, column=0, columnspan=2, pady=(10, 5))

    # Campi per data e prezzo manuali
    tk.Label(popup, text="Data (YYYY-MM-DD):").grid(row=4, column=0, padx=10, pady=5, sticky="e")
    entry_data = tk.Entry(popup, width=20)
    entry_data.grid(row=4, column=1, padx=10, pady=5)

    tk.Label(popup, text="Prezzo unitario (€):").grid(row=5, column=0, padx=10, pady=5, sticky="e")
    entry_prezzo = tk.Entry(popup, width=20)
    entry_prezzo.grid(row=5, column=1, padx=10, pady=5)

    # Funzione per abilitare/disabilitare i campi manuali
    def toggle_campi_manual_price():
        stato = "normal" if not usa_prezzo_attuale.get() else "disabled"
        entry_prezzo.config(state=stato)
        entry_data.config(state=stato)

    toggle_campi_manual_price()

    def conferma_vendita():
        ticker = entry_ticker.get().strip().upper()
        try:
            quantita = float(entry_quantita.get())
            if quantita <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Errore", "Inserisci una quantità valida.")
            return

        if usa_prezzo_attuale.get():
            risultato = vendi_azione(ticker, quantita)
        else:
            try:
                prezzo = float(entry_prezzo.get())
                data = datetime.strptime(entry_data.get(), "%Y-%m-%d").date()
            except ValueError:
                messagebox.showerror("Errore", "Prezzo o data non validi.")
                return
            risultato = vendi_azione(ticker, quantita, prezzo=prezzo, data=data)

        if risultato["successo"]:
            dati = risultato["dati"]
            messagebox.showinfo(
                "Vendita completata",
                f"Hai venduto {dati['quantita_venduta']} azioni di {dati['ticker']} a {dati['prezzo_vendita']:.2f} €\n"
                f"PMU: {dati['pmu']:.2f} €\n"
                f"Guadagno per azione: {dati['guadagno_per_azione']:.2f} €\n"
                f"Totale: {dati['guadagno_totale']:.2f} €"
            )
            popup.destroy()
        else:
            messagebox.showerror("Errore", risultato["errore"])

    tk.Button(popup, text="Conferma", command=conferma_vendita).grid(row=6, column=0, columnspan=2, pady=10)

def apri_finestra_investimenti():
    finestra = tk.Toplevel()
    finestra.title("Gestione Investimenti")
    larghezza = 850
    altezza = 600
    x = (finestra.winfo_screenwidth() // 2) - (larghezza // 2)
    y = (finestra.winfo_screenheight() // 2) - (altezza // 2)
    finestra.geometry(f"{larghezza}x{altezza}+{x}+{y}")

    # Valore totale portafoglio (inizialmente 0, verrà aggiornato dopo)
    lbl_valore_totale = tk.Label(finestra, text="Valore Totale: €0.00", font=("Helvetica", 14, "bold"))
    lbl_valore_totale.pack(pady=10)

    # Frame per il grafico
    frame_grafico = tk.Frame(finestra, bg="white")
    frame_grafico.pack(fill="x", padx=20, pady=5)

    mostra_grafico_andamento(frame_grafico)

    # Lista titoli
    frame_titoli = tk.Frame(finestra)
    frame_titoli.pack(fill="both", expand=True, padx=20, pady=10)

    colonne = ("Ticker", "Quantità", "Valore", "Variazione 1D")
    tabella = ttk.Treeview(frame_titoli, columns=colonne, show="headings", height=10)

    for col in colonne:
        tabella.heading(col, text=col)
        tabella.column(col, anchor="center")

    tabella.pack(fill="both", expand=True)

    valore_totale_portafoglio = 0.0

    for ticker, operazioni in investimenti.items():
        quantita_totale = calcola_quantita_posseduta(operazioni)

        if quantita_totale <= 0:
            continue  # Salta i titoli completamente venduti

        try:
            yf_ticker = yf.Ticker(ticker)
            info = yf_ticker.info
            prezzo_corrente = info.get("regularMarketPrice")
            prezzo_precedente = info.get("previousClose", prezzo_corrente)

            if prezzo_corrente is None:
                raise ValueError("Prezzo non disponibile")

            variazione = prezzo_corrente - prezzo_precedente
            variazione_percentuale = (variazione / prezzo_precedente) * 100 if prezzo_precedente else 0

            valore = quantita_totale * prezzo_corrente
            valore_totale_portafoglio += valore

            tabella.insert("", "end", values=(
                ticker,
                f"{quantita_totale}",
                f"{valore:.2f} €",
                f"{variazione_percentuale:+.2f}%"
            ))
        except Exception as e:
            tabella.insert("", "end", values=(
                ticker,
                f"{quantita_totale}",
                "Errore",
                "N/D"
            ))

    # Aggiorna il valore totale del portafoglio
    lbl_valore_totale.config(text=f"Valore Totale: €{valore_totale_portafoglio:,.2f}")

    # Pulsanti operazioni
    frame_bottoni = tk.Frame(finestra)
    frame_bottoni.pack(pady=10)

    btn_acquista = tk.Button(frame_bottoni, text="Acquista Azione", bg="#b3ffcc", command=apri_popup_acquisto)
    btn_acquista.grid(row=0, column=0, padx=10)

    btn_vendi = tk.Button(frame_bottoni, text="Vendi Azione", bg="#ffcccc", command=apri_popup_vendita)
    btn_vendi.grid(row=0, column=1, padx=10)

    btn_dettagli = tk.Button(frame_bottoni, text="Dettagli avanzati", width=18,
                             command=lambda: messagebox.showinfo("In sviluppo", "Dettagli avanzati in sviluppo"))
    btn_dettagli.grid(row=0, column=2, padx=10)

    btn_watchlist = tk.Button(frame_bottoni, text="Watchlist", width=15,
                              command=lambda: messagebox.showinfo("In sviluppo", "Watchlist in sviluppo"))
    btn_watchlist.grid(row=0, column=3, padx=10)
