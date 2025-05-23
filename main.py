import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
from storage import carica_conti, carica_transazioni
import tkinter as tk
from datetime import datetime
import json

CONFIG_PATH = "data/dashboard_config.json"

GRID_ROWS = 6
GRID_COLS = 6

WIDGETS = [
    {"nome": "saldo", "label": "Saldo Totale", "size": (2, 1)},
    {"nome": "transazioni", "label": "Ultime Transazioni", "size": (2, 1)},
    {"nome": "investimenti", "label": "Portafoglio Investimenti", "size": (3, 1)},
    {"nome": "bilancio", "label": "Bilancio Mensile", "size": (1, 1)},
    {"nome": "obiettivi", "label": "Obiettivi Risparmio", "size": (2, 1)},
    {"nome": "watchlist", "label": "Watchlist Azioni", "size": (1, 2)},
    {"nome": "scontrini", "label": "Scansione Scontrini", "size": (1, 1)},
    {"nome": "statistiche_spese", "label": "Statistiche Spese", "size": (2, 1)},
    {"nome": "prossime_spese", "label": "Prossime Spese", "size": (1, 1)},
    {"nome": "calendario", "label": "Calendario Finanziario", "size": (2, 1)},
    {"nome": "storico_saldo", "label": "Storico Saldo", "size": (2, 1)},
    {"nome": "crediti_debiti", "label": "Crediti e Debiti", "size": (1, 1)}
]

class ConfigDashboardWindow:
    def __init__(self, master):
        self.window = ttkb.Toplevel(master)
        self.window.title("Configura Dashboard")
        self.window.geometry("1100x750")
        self.selected_widget = None

        self.sidebar = ttkb.Frame(self.window, padding=10)
        self.sidebar.grid(row=0, column=0, sticky="ns")  # CAMBIATO: pack -> grid

        self.grid_area = ttkb.Frame(self.window)
        self.grid_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)  # CAMBIATO: pack -> grid

        self.window.columnconfigure(1, weight=1)
        self.window.rowconfigure(0, weight=1)

        self.widget_buttons = {}
        self.rows_var = tk.IntVar(value=GRID_ROWS)
        self.cols_var = tk.IntVar(value=GRID_COLS)
        self.grid_slots = [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]

        for widget in WIDGETS:
            btn = ttkb.Button(self.sidebar, text=widget["label"], width=25,
                              command=lambda w=widget: self.select_widget(w))
            btn.grid(sticky="ew", pady=2)
            self.widget_buttons[widget["nome"]] = btn

        grid_config_frame = ttkb.Frame(self.sidebar)
        grid_config_frame.grid(sticky="ew", pady=(10, 15))
        ttkb.Label(grid_config_frame, text="Righe").grid(row=0, column=0)
        ttkb.Entry(grid_config_frame, textvariable=self.rows_var, width=4).grid(row=0, column=1, padx=3)
        ttkb.Label(grid_config_frame, text="Colonne").grid(row=0, column=2)
        ttkb.Entry(grid_config_frame, textvariable=self.cols_var, width=4).grid(row=0, column=3, padx=3)
        ttkb.Button(grid_config_frame, text="Applica", command=self.update_grid_dimensions).grid(row=0, column=4, padx=5)

        self.render_grid()
        self.load_config()
        self.refresh_grid_content()

        save_btn = ttkb.Button(self.sidebar, text="Salva Configurazione", bootstyle=SUCCESS,
                               command=self.save_config)
        save_btn.grid(sticky="ew", pady=20)

        reset_btn = ttkb.Button(self.sidebar, text="Ripristina Default", bootstyle=DANGER,
                                command=self.reset_default_config)
        reset_btn.grid(sticky="ew", pady=5)

    def update_grid_dimensions(self):
        global GRID_ROWS, GRID_COLS
        GRID_ROWS = self.rows_var.get()
        GRID_COLS = self.cols_var.get()
        self.grid_slots = [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.render_grid()
        self.refresh_grid_content()

    def select_widget(self, widget_info):
        self.selected_widget = widget_info

    def render_grid(self):
        for widget in self.grid_area.winfo_children():
            widget.destroy()

        for r in range(GRID_ROWS):
            self.grid_area.rowconfigure(r, weight=1)
        for c in range(GRID_COLS):
            self.grid_area.columnconfigure(c, weight=1)

        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                if self.grid_slots[r][c] is None:
                    frame = ttkb.Frame(self.grid_area, width=150, height=100, relief=RAISED, borderwidth=1)
                    frame.grid(row=r, column=c, sticky="nsew", padx=2, pady=2)
                    frame.bind("<Button-1>", lambda e, row=r, col=c: self.place_widget(row, col))

    def place_widget(self, row, col):
        if not self.selected_widget:
            return
        widget_info = self.selected_widget
        cols, rows = widget_info["size"]
        if row + rows > GRID_ROWS or col + cols > GRID_COLS:
            return
        for r in range(row, row + rows):
            for c in range(col, col + cols):
                if self.grid_slots[r][c] is not None:
                    return
        for r in range(row, row + rows):
            for c in range(col, col + cols):
                self.grid_slots[r][c] = widget_info["nome"] if (r == row and c == col) else "X"
        label = ttkb.Label(self.grid_area, text=widget_info["label"], relief=SOLID, borderwidth=1)
        label.grid(row=row, column=col, rowspan=rows, columnspan=cols, sticky="nsew", padx=2, pady=2)
        label.bind("<Button-3>", lambda e: self.remove_widget(row, col))
        self.selected_widget = None

    def remove_widget(self, row, col):
        widget_id = self.grid_slots[row][col]
        if not widget_id:
            return
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                if self.grid_slots[r][c] == widget_id or self.grid_slots[r][c] == "X":
                    self.grid_slots[r][c] = None
        self.refresh_grid_content()

    def refresh_grid_content(self):
        self.render_grid()
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                if self.grid_slots[r][c] and self.grid_slots[r][c] != "X":
                    w = next(w for w in WIDGETS if w["nome"] == self.grid_slots[r][c])
                    self._draw_widget(w, r, c)

    def _draw_widget(self, widget_info, row, col):
        cols, rows = widget_info["size"]
        for r in range(row, row + rows):
            for c in range(col, col + cols):
                self.grid_slots[r][c] = widget_info["nome"] if (r == row and c == col) else "X"
        label = ttkb.Label(self.grid_area, text=widget_info["label"], relief=SOLID, borderwidth=1)
        label.grid(row=row, column=col, rowspan=rows, columnspan=cols, sticky="nsew", padx=2, pady=2)
        label.bind("<Button-3>", lambda e: self.remove_widget(row, col))

    def save_config(self):
        config = []
        added = set()
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                nome = self.grid_slots[r][c]
                if nome and nome != "X" and nome not in added:
                    w = next(w for w in WIDGETS if w["nome"] == nome)
                    config.append({
                        "nome": nome,
                        "visible": True,
                        "row": r,
                        "column": c,
                        "rowspan": w["size"][1],
                        "columnspan": w["size"][0]
                    })
                    added.add(nome)
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=4)
        self.window.destroy()

    def reset_default_config(self):
        from tkinter import messagebox
        if messagebox.askyesno("Conferma", "Sei sicuro di voler ripristinare la configurazione predefinita?"):
            try:
                with open("data/dashboard_config_default.json", "r") as f:
                    default_config = json.load(f)
                with open(CONFIG_PATH, "w") as f:
                    json.dump(default_config, f, indent=4)
                self.window.destroy()
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile caricare il file di default:\n{e}")

    def load_config(self):
        try:
            with open(CONFIG_PATH, "r") as f:
                data = json.load(f)
            for item in data:
                if not item.get("visible", True):
                    continue
                nome = item["nome"]
                row = item["row"]
                col = item["column"]
                rowspan = item.get("rowspan", 1)
                columnspan = item.get("columnspan", 1)
                for r in range(row, row + rowspan):
                    for c in range(col, col + columnspan):
                        self.grid_slots[r][c] = nome if (r == row and c == col) else "X"
        except FileNotFoundError:
            pass

def apri_dashboard(main_frame):
    for widget in main_frame.winfo_children():
        widget.destroy()

    main_frame.columnconfigure(0, weight=1)
    main_frame.rowconfigure(1, weight=1)

    titolo = ttkb.Label(main_frame, text="Dashboard", font=("Segoe UI", 16, "bold"))
    titolo.grid(row=0, column=0, pady=(10, 20))

    widget_frame = ttkb.Frame(main_frame)
    widget_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

    for i in range(GRID_COLS):
        widget_frame.columnconfigure(i, weight=1, uniform="col")
    for i in range(GRID_ROWS):
        widget_frame.rowconfigure(i, weight=1, uniform="row")

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
        for t in [{"ticker": "AAPL", "prezzo": 185.20, "var": +1.25}, {"ticker": "TSLA", "prezzo": 172.55, "var": -2.14}]:
            colore = "green" if t["var"] >= 0 else "#bb4444"
            riga = f"{t['ticker']}: € {t['prezzo']:.2f} ({t['var']:+.2f}%)"
            ttkb.Label(frame, text=riga, font=("Segoe UI", 10), foreground=colore).pack(anchor="w")
        return frame

    def widget_scontrini():
        return ttkb.LabelFrame(widget_frame, text="Scansione Scontrini", padding=10)

    def widget_statistiche_spese():
        return ttkb.LabelFrame(widget_frame, text="Statistiche Spese", padding=10)

    def widget_prossime_spese():
        return ttkb.LabelFrame(widget_frame, text="Prossime Spese", padding=10)

    def widget_calendario():
        return ttkb.LabelFrame(widget_frame, text="Calendario Finanziario", padding=10)

    def widget_storico_saldo():
        return ttkb.LabelFrame(widget_frame, text="Storico del Saldo", padding=10)

    def widget_crediti_debiti():
        return ttkb.LabelFrame(widget_frame, text="Crediti e Debiti", padding=10)

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
        ConfigDashboardWindow(main_frame.winfo_toplevel())

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
    app.columnconfigure(0, weight=0)  # Sidebar: larghezza fissa
    app.columnconfigure(1, weight=1)  # Dashboard: si espande
    app.rowconfigure(0, weight=1)

    sidebar = ttkb.Frame(app, padding=(15, 10), bootstyle="dark", width=350)  #todo resize sidebar
    sidebar.grid(row=0, column=0, sticky="ns")
    app.grid_columnconfigure(0, weight=0)

    main_frame = ttkb.Frame(app)
    main_frame.grid(row=0, column=1, sticky="nsew")
    app.grid_columnconfigure(1, weight=1)  # espande solo la dashboard

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