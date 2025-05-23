import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
from storage import carica_conti, carica_transazioni
import random
from datetime import datetime
import json

def apri_dashboard(main_frame):
    for widget in main_frame.winfo_children():
        widget.destroy()

    titolo = ttkb.Label(main_frame, text="Dashboard", font=("Segoe UI", 16, "bold"))
    titolo.pack(pady=(10, 20))

    # Container widget principale con grid
    widget_frame = ttkb.Frame(main_frame)
    widget_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)

    for i in range(4):
        widget_frame.columnconfigure(i, weight=1)
        widget_frame.rowconfigure(i, weight=1)

    def widget_saldo():
        frame = ttkb.LabelFrame(widget_frame, text="Saldo Totale", padding=10)
        conti = carica_conti()
        saldo_totale = sum(conti.values())
        ttkb.Label(frame, text=f"€ {saldo_totale:.2f}", font=("Segoe UI", 16)).pack()
        for nome, saldo in conti.items():
            ttkb.Label(frame, text=f"{nome}: € {saldo:.2f}", font=("Segoe UI", 9), foreground="gray").pack(anchor="w", padx=20)
        return frame

    def widget_transazioni():
        frame = ttkb.LabelFrame(widget_frame, text="Ultime Transazioni", padding=10)
        transazioni = carica_transazioni()
        for tr in sorted(transazioni, key=lambda x: x["data"], reverse=True)[:5]:
            riga = f"{tr['data']} | {tr['categoria']} | {tr['importo']} €"
            colore = "green" if tr["importo"] >= 0 else "#bb4444"
            ttkb.Label(frame, text=riga, font=("Segoe UI", 10), foreground=colore).pack(anchor="w")
        return frame

    def widget_investimenti():
        frame = ttkb.LabelFrame(widget_frame, text="Valore Portafoglio Investimenti", padding=10)
        ttkb.Label(frame, text="[Grafico qui]", font=("Segoe UI", 12, "italic"), foreground="gray").pack()
        return frame

    def widget_bilancio():
        frame = ttkb.LabelFrame(widget_frame, text="Bilancio Mensile", padding=10)
        transazioni = carica_transazioni()
        transazioni_mese = [t for t in transazioni if t["data"].startswith(datetime.today().strftime("%Y-%m"))]
        entrate = sum(t["importo"] for t in transazioni_mese if t["importo"] > 0)
        uscite = -sum(t["importo"] for t in transazioni_mese if t["importo"] < 0)
        bilancio = entrate - uscite
        ttkb.Label(frame, text=f"Entrate: € {entrate:.2f}", font=("Segoe UI", 10)).pack(anchor="w")
        ttkb.Label(frame, text=f"Uscite: € {uscite:.2f}", font=("Segoe UI", 10)).pack(anchor="w")
        ttkb.Label(frame, text=f"Bilancio: € {bilancio:.2f}", font=("Segoe UI", 12, "bold"),
                   foreground=("green" if bilancio >= 0 else "red")).pack(anchor="w", pady=(5, 0))
        return frame

    def widget_goal():
        frame = ttkb.LabelFrame(widget_frame, text="Obiettivi di Risparmio", padding=10)
        ttkb.Label(frame, text="Vacanza Tokyo: 2200 / 3000 €", font=("Segoe UI", 10)).pack(anchor="w")
        ttkb.Progressbar(frame, value=2200 / 3000 * 100).pack(fill=X, pady=5)
        ttkb.Label(frame, text="Nuovo PC: 500 / 1500 €", font=("Segoe UI", 10)).pack(anchor="w")
        ttkb.Progressbar(frame, value=500 / 1500 * 100).pack(fill=X, pady=5)
        return frame

    def widget_watchlist():
        frame = ttkb.LabelFrame(widget_frame, text="Watchlist Azioni", padding=10)
        titoli = [
            {"ticker": "AAPL", "prezzo": 185.20, "var": +1.25},
            {"ticker": "TSLA", "prezzo": 172.55, "var": -2.14},
            {"ticker": "MSFT", "prezzo": 317.30, "var": +0.65},
            {"ticker": "NVDA", "prezzo": 872.14, "var": -0.78},
            {"ticker": "ENI.MI", "prezzo": 14.67, "var": +0.42}
        ]
        for t in titoli:
            colore = "green" if t["var"] >= 0 else "#bb4444"
            riga = f"{t['ticker']}: € {t['prezzo']:.2f} ({t['var']:+.2f}%)"
            ttkb.Label(frame, text=riga, font=("Segoe UI", 10), foreground=colore).pack(anchor="w")
        return frame

    def widget_scontrini():
        frame = ttkb.LabelFrame(widget_frame, text="Scansione Scontrini", padding=10)
        ttkb.Label(frame, text="[Carica uno scontrino per analizzare i dati]", font=("Segoe UI", 10),
                   foreground="gray").pack(anchor="center")
        return frame

    def widget_statistiche_spese():
        frame = ttkb.LabelFrame(widget_frame, text="Grafico Spese per Categoria", padding=10)
        ttkb.Label(frame, text="[Grafico a torta delle spese mensili qui]", font=("Segoe UI", 10, "italic"),
                   foreground="gray").pack(anchor="center")
        return frame

    def widget_prossime_spese():
        frame = ttkb.LabelFrame(widget_frame, text="Prossime Spese Ricorrenti", padding=10)
        ttkb.Label(frame, text="[Visualizzazione delle prossime spese ricorrenti]", font=("Segoe UI", 10),
                   foreground="gray").pack(anchor="center")
        return frame

    def widget_calendario():
        frame = ttkb.LabelFrame(widget_frame, text="Calendario Finanziario", padding=10)
        ttkb.Label(frame, text="[Eventi e scadenze finanziarie nel calendario]", font=("Segoe UI", 10),
                   foreground="gray").pack(anchor="center")
        return frame

    def widget_storico_saldo():
        frame = ttkb.LabelFrame(widget_frame, text="Storico del Saldo", padding=10)
        ttkb.Label(frame, text="[Grafico dell'evoluzione del saldo nel tempo]", font=("Segoe UI", 10),
                   foreground="gray").pack(anchor="center")
        return frame

    def widget_crediti_debiti():
        frame = ttkb.LabelFrame(widget_frame, text="Crediti e Debiti", padding=10)
        ttkb.Label(frame, text="[Elenco crediti e debiti con importi e scadenze]", font=("Segoe UI", 10),
                   foreground="gray").pack(anchor="center")
        return frame

    widget_map = {
        "saldo": widget_saldo,
        "transazioni": widget_transazioni,
        "investimenti": widget_investimenti,
        "bilancio": widget_bilancio,
        "obiettivi": widget_goal,
        "watchlist": widget_watchlist,
        "scontrini": widget_scontrini,
        "statistiche_spese": widget_statistiche_spese,
        "prossime_spese": widget_prossime_spese,
        "calendario": widget_calendario,
        "storico_saldo": widget_storico_saldo,
        "crediti_debiti": widget_crediti_debiti
    }

    try:
        with open("data/dashboard_config.json", "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        config = []

    for w in config:
        if w.get("visible", False) and w["nome"] in widget_map:
            frame = widget_map[w["nome"]]()
            frame.grid(
                row=w["row"],
                column=w["column"],
                rowspan=w.get("rowspan", 1),
                columnspan=w.get("columnspan", 1),
                padx=5, pady=5,
                sticky="nsew"
            )

    def apri_configuratore():
        print("TODO: apri configuratore dashboard")

    btn_config = ttkb.Button(main_frame, text="⚙️", bootstyle="secondary")
    btn_config.place(relx=1.0, rely=0.0, anchor="ne", x=-10, y=15)
    btn_config.config(command=apri_configuratore)



def apri_conti(main_frame):
    for widget in main_frame.winfo_children():
        widget.destroy()
    ttkb.Label(main_frame, text="Sezione Conti", font=("Segoe UI", 16, "bold")).pack(pady=20)

def apri_transazioni(main_frame):
    for widget in main_frame.winfo_children():
        widget.destroy()
    ttkb.Label(main_frame, text="Storico Transazioni", font=("Segoe UI", 16, "bold")).pack(pady=20)

def apri_investimenti(main_frame):
    for widget in main_frame.winfo_children():
        widget.destroy()
    ttkb.Label(main_frame, text="Portafoglio Investimenti", font=("Segoe UI", 16, "bold")).pack(pady=20)

def saluto_random(nome="Matteo"):
    ora = datetime.now().hour

    if 5 <= ora < 12:
        saluto = "Buongiorno"
    elif 12 <= ora < 18:
        saluto = "Buon pomeriggio"
    elif 18 <= ora < 22:
        saluto = "Buonasera"
    else:
        saluto = "Ciao"

    return f"{saluto}, {nome}!"

def main():
    app = ttkb.Window(themename="superhero")
    app.title("Cato Finance")
    app.geometry("1280x720")
    app.minsize(800, 500)

    # Centra la finestra sullo schermo
    app.update_idletasks()
    width = app.winfo_width()
    height = app.winfo_height()
    x = (app.winfo_screenwidth() // 2) - (width // 2)
    y = (app.winfo_screenheight() // 2) - (height // 2)
    app.geometry(f"{width}x{height}+{x}+{y}")

    # Layout principale con grid
    app.columnconfigure(0, weight=1, minsize=350, uniform='a')
    app.columnconfigure(1, weight=5, uniform='a')  # main
    app.rowconfigure(0, weight=1)

    sidebar = ttkb.Frame(app, padding=(15, 10), bootstyle="dark")
    sidebar.grid(row=0, column=0, sticky="nswe")

    main_frame = ttkb.Frame(app)
    main_frame.grid(row=0, column=1, sticky="nswe")

    # Sidebar - Saluto e navigazione
    ttkb.Label(sidebar, text=saluto_random(), font=("Segoe UI", 12)).pack(pady=(20, 30))

    ttkb.Button(sidebar, text="🏠 Dashboard", bootstyle=SECONDARY, command=lambda: apri_dashboard(main_frame)).pack(
        fill=X, padx=10, pady=5)
    ttkb.Button(sidebar, text="💼 Conti", bootstyle=SECONDARY, command=lambda: apri_conti(main_frame)).pack(fill=X,
                                                                                                           padx=10,
                                                                                                           pady=5)
    ttkb.Button(sidebar, text="📜 Transazioni", bootstyle=SECONDARY, command=lambda: apri_transazioni(main_frame)).pack(
        fill=X, padx=10, pady=5)
    ttkb.Button(sidebar, text="📈 Investimenti", bootstyle=SECONDARY,
                command=lambda: apri_investimenti(main_frame)).pack(fill=X, padx=10, pady=5)
    ttkb.Button(sidebar, text="⚙️ Impostazioni", bootstyle=SECONDARY).pack(fill=X, padx=10, pady=5)

    # Mostra la dashboard all'avvio
    apri_dashboard(main_frame)

        # Pulsante flottante +
        # Pulsante flottante con menu
    def mostra_menu(event):
        menu = ttkb.Menu(app, tearoff=0)
        menu.add_command(label="Aggiungi Transazione", command=lambda: print("Transazione"))
        menu.add_command(label="Aggiungi Obiettivo di Risparmio", command=lambda: print("Obiettivo"))
        menu.add_separator()
        menu.add_command(label="Altro...", command=lambda: print("Altro"))
        menu.tk_popup(event.x_root, event.y_root)

    btn_plus = ttkb.Button(app, text="➕", bootstyle="success", width=3)
    btn_plus.place(relx=0.97, rely=0.93, anchor="center")
    btn_plus.bind("<Button-1>", mostra_menu)

    app.mainloop()


if __name__ == "__main__":
    main()