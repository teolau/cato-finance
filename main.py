import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
from storage import carica_conti, carica_transazioni  # Assicurati che questo file esista e funzioni
import tkinter as tk
from tkinter import messagebox  # Importato specificamente
from datetime import datetime
import json
import os  # Importato per os.path e os.makedirs

# --- Costanti e Configurazioni Globali ---
DATA_DIR = "data"
CONFIG_PATH_MAIN = os.path.join(DATA_DIR, "dashboard_config.json")
DEFAULT_CONFIG_PATH_MAIN = os.path.join(DATA_DIR, "dashboard_config_default.json")

INITIAL_GRID_ROWS = 6
INITIAL_GRID_COLS = 6

WIDGETS = [
    {"nome": "saldo", "label": "Saldo Totale", "size": (3, 2)},  # (cols, rows)
    {"nome": "transazioni", "label": "Ultime Transazioni", "size": (3, 2)},
    {"nome": "investimenti", "label": "Portafoglio Investimenti", "size": (4, 2)},
    {"nome": "bilancio", "label": "Bilancio Mensile", "size": (2, 2)},
    {"nome": "obiettivi", "label": "Obiettivi Risparmio", "size": (2, 2)},
    {"nome": "watchlist", "label": "Watchlist Azioni", "size": (2, 4)},
    {"nome": "scontrini", "label": "Scansione Scontrini", "size": (2, 1)},
    {"nome": "statistiche_spese", "label": "Statistiche Spese", "size": (2, 1)},
    {"nome": "prossime_spese", "label": "Prossime Spese", "size": (2, 1)},
    {"nome": "calendario", "label": "Calendario Finanziario", "size": (2, 1)},
    {"nome": "storico_saldo", "label": "Storico Saldo", "size": (2, 1)},
    {"nome": "crediti_debiti", "label": "Crediti e Debiti", "size": (2, 1)}
]


# Nota: Ho invertito size in WIDGETS per coerenza con (col, row) come nel tuo codice originale,
# ma la classe ConfigDashboardWindow internamente si aspetta (cols, rows) per "size".
# Ho aggiornato l'uso di widget_info["size"] in ConfigDashboardWindow per riflettere questo.
# In WIDGETS: "size": (column_span, row_span)

# --- Classe ConfigDashboardWindow (Modificata e Integrata) ---
class ConfigDashboardWindow:
    def __init__(self, master, refresh_callback, initial_grid_rows, initial_grid_cols, widgets_list, config_file_path,
                 default_config_file_path):
        self.master_window = master  # La finestra radice dell'app, non il main_frame
        self.refresh_callback = refresh_callback
        self.WIDGETS = widgets_list
        self.CONFIG_PATH = config_file_path
        self.DEFAULT_CONFIG_PATH = default_config_file_path

        self.window = ttkb.Toplevel(self.master_window)
        self.window.title("Configura Dashboard")
        self.window.geometry("1200x800")  # Aumentato un po'
        self.window.transient(self.master_window)
        self.window.grab_set()
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)  # Gestisce la chiusura dalla X

        self.selected_widget = None

        self.sidebar = ttkb.Frame(self.window, padding=10)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        self.grid_area_container = ttkb.Frame(self.window, padding=10)  # Contenitore per scrollbar se necessario
        self.grid_area_container.grid(row=0, column=1, sticky="nsew")
        self.grid_area_container.rowconfigure(0, weight=1)
        self.grid_area_container.columnconfigure(0, weight=1)

        self.grid_area = ttkb.Frame(self.grid_area_container)  # Frame effettivo per la griglia
        self.grid_area.grid(row=0, column=0, sticky="nsew")

        self.window.columnconfigure(1, weight=1)
        self.window.rowconfigure(0, weight=1)

        self.current_grid_rows = tk.IntVar(value=initial_grid_rows)
        self.current_grid_cols = tk.IntVar(value=initial_grid_cols)
        self._initialize_grid_slots()

        widget_list_frame = ttkb.LabelFrame(self.sidebar, text="Widget Disponibili", padding=10)
        widget_list_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self.widget_buttons = {}
        for i, widget_info in enumerate(self.WIDGETS):
            btn = ttkb.Button(widget_list_frame, text=widget_info["label"], width=25,
                              command=lambda w=widget_info: self.select_widget(w))
            btn.grid(row=i, column=0, sticky="ew", pady=2)
            self.widget_buttons[widget_info["nome"]] = btn

        grid_config_frame = ttkb.LabelFrame(self.sidebar, text="Dimensioni Griglia", padding=10)
        grid_config_frame.grid(row=1, column=0, sticky="ew", pady=10)
        ttkb.Label(grid_config_frame, text="Righe:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.rows_entry = ttkb.Entry(grid_config_frame, textvariable=self.current_grid_rows, width=5)
        self.rows_entry.grid(row=0, column=1)
        ttkb.Label(grid_config_frame, text="Colonne:").grid(row=1, column=0, sticky="w", padx=(0, 5), pady=(5, 0))
        self.cols_entry = ttkb.Entry(grid_config_frame, textvariable=self.current_grid_cols, width=5)
        self.cols_entry.grid(row=1, column=1, pady=(5, 0))
        ttkb.Button(grid_config_frame, text="Applica Dimensioni", command=self.update_grid_dimensions,
                    bootstyle=INFO).grid(row=2, column=0, columnspan=2, pady=(10, 0), sticky="ew")

        action_buttons_frame = ttkb.Frame(self.sidebar, padding=(0, 10))  # Rimosso padding 20
        action_buttons_frame.grid(row=2, column=0, sticky="sew", pady=(10, 0))
        self.sidebar.rowconfigure(2, weight=1)

        save_btn = ttkb.Button(action_buttons_frame, text="Salva e Chiudi", bootstyle=SUCCESS,
                               command=self.save_config_and_close)
        save_btn.pack(fill=X, pady=5)

        apply_btn = ttkb.Button(action_buttons_frame, text="Applica Modifiche", bootstyle=PRIMARY,
                                command=self.apply_changes_no_close)  # Nuovo pulsante
        apply_btn.pack(fill=X, pady=5)

        reset_btn = ttkb.Button(action_buttons_frame, text="Ripristina Default", bootstyle=DANGER,
                                command=self.reset_default_config)
        reset_btn.pack(fill=X, pady=5)

        cancel_btn = ttkb.Button(action_buttons_frame, text="Annulla", bootstyle=LIGHT,
                                 command=self._on_close)
        cancel_btn.pack(fill=X, pady=(5, 0))

        self.load_config_and_render()
        self.window.after(100, lambda: self.window.lift())  # Assicura che sia in primo piano

    def _on_close(self):
        # Qui potresti chiedere se salvare le modifiche non salvate
        self.window.grab_release()
        self.window.destroy()

    def _initialize_grid_slots(self):
        rows = self.current_grid_rows.get()
        cols = self.current_grid_cols.get()
        self.grid_slots = [[None for _ in range(cols)] for _ in range(rows)]

    def update_grid_dimensions(self):
        try:
            new_rows = int(self.rows_entry.get())
            new_cols = int(self.cols_entry.get())
        except ValueError:
            messagebox.showerror("Errore", "Righe e colonne devono essere numeri interi.", parent=self.window)
            return

        if new_rows <= 0 or new_cols <= 0:
            messagebox.showerror("Errore", "Righe e colonne devono essere maggiori di zero.", parent=self.window)
            self.current_grid_rows.set(len(self.grid_slots))
            self.current_grid_cols.set(len(self.grid_slots[0]) if self.grid_slots else 1)
            return

        placed_widgets_config = []
        added_names = set()
        for r_idx, row_list in enumerate(self.grid_slots):
            for c_idx, slot_name in enumerate(row_list):
                if slot_name and slot_name != "X" and slot_name not in added_names:
                    widget_info = next((w for w in self.WIDGETS if w["nome"] == slot_name), None)
                    if widget_info:
                        placed_widgets_config.append({
                            "nome": slot_name, "row": r_idx, "column": c_idx,
                            "size_cols": widget_info["size"][0], "size_rows": widget_info["size"][1]
                        })
                        added_names.add(slot_name)

        self.current_grid_rows.set(new_rows)  # Aggiorna le IntVar solo dopo la validazione
        self.current_grid_cols.set(new_cols)
        self._initialize_grid_slots()

        for config_item in placed_widgets_config:
            w_info = next((w for w in self.WIDGETS if w["nome"] == config_item["nome"]), None)
            if w_info:
                cols_needed, rows_needed = w_info["size"]
                if config_item["row"] + rows_needed <= new_rows and config_item["column"] + cols_needed <= new_cols:
                    can_place = True
                    for r_check in range(config_item["row"], config_item["row"] + rows_needed):
                        for c_check in range(config_item["column"], config_item["column"] + cols_needed):
                            if self.grid_slots[r_check][c_check] is not None:
                                can_place = False;
                                break
                        if not can_place: break
                    if can_place:
                        self._internal_place_widget_data(w_info, config_item["row"], config_item["column"])

        self.render_grid_placeholders_and_widgets()

    def select_widget(self, widget_info):
        self.selected_widget = widget_info

    def render_grid_placeholders_and_widgets(self):
        for widget_tk in self.grid_area.winfo_children():
            widget_tk.destroy()

        rows = self.current_grid_rows.get()
        cols = self.current_grid_cols.get()

        for r in range(rows):
            self.grid_area.rowconfigure(r, weight=1, uniform="row_config")
        for c in range(cols):
            self.grid_area.columnconfigure(c, weight=1, uniform="col_config")

        # Disegna prima i placeholder
        for r in range(rows):
            for c in range(cols):
                # Disegna un placeholder solo se la cella è completamente vuota (non "X")
                # e non è l'inizio di un widget già piazzato
                if self.grid_slots[r][c] is None:
                    frame = ttkb.Frame(self.grid_area, relief=RAISED, borderwidth=1)
                    frame.grid(row=r, column=c, sticky="nsew", padx=1, pady=1)
                    frame.bind("<Button-1>", lambda e, row=r, col=c: self.handle_grid_click(row, col))
                    # ttkb.Label(frame, text=f"{r},{c}").pack(expand=True) # Debug

        # Poi disegna i widget effettivi sopra/al posto dei placeholder
        drawn_widgets = set()
        for r in range(rows):
            for c in range(cols):
                widget_name = self.grid_slots[r][c]
                if widget_name and widget_name != "X" and widget_name not in drawn_widgets:
                    widget_info = next((w for w in self.WIDGETS if w["nome"] == widget_name), None)
                    if widget_info:
                        self._draw_widget_on_grid(widget_info, r, c)
                        drawn_widgets.add(widget_name)

    def handle_grid_click(self, row, col):
        if self.selected_widget:
            self.attempt_place_widget(self.selected_widget, row, col)
            self.selected_widget = None
        else:  # Click su cella vuota, o su un widget (gestito dal bind del widget)
            pass

    def _internal_place_widget_data(self, widget_info, row, col):
        cols_span, rows_span = widget_info["size"]
        for r_offset in range(rows_span):
            for c_offset in range(cols_span):
                current_r, current_c = row + r_offset, col + c_offset
                self.grid_slots[current_r][current_c] = widget_info["nome"] if (
                            r_offset == 0 and c_offset == 0) else "X"

    def attempt_place_widget(self, widget_info, row, col):
        if not widget_info: return

        cols_span, rows_span = widget_info["size"]
        grid_r_dim = self.current_grid_rows.get()
        grid_c_dim = self.current_grid_cols.get()

        is_widget_placed = any(
            self.grid_slots[r][c] == widget_info["nome"]
            for r in range(grid_r_dim) for c in range(grid_c_dim)
        )
        if is_widget_placed:
            messagebox.showwarning("Attenzione", f"Il widget '{widget_info['label']}' è già presente.",
                                   parent=self.window)
            return

        if row + rows_span > grid_r_dim or col + cols_span > grid_c_dim:
            messagebox.showerror("Errore", "Il widget non entra da questa posizione.", parent=self.window)
            return

        for r_offset in range(rows_span):
            for c_offset in range(cols_span):
                if self.grid_slots[row + r_offset][col + c_offset] is not None:
                    messagebox.showerror("Errore", "Spazio non sufficiente.", parent=self.window)
                    return

        self._internal_place_widget_data(widget_info, row, col)
        self.render_grid_placeholders_and_widgets()

    def remove_widget_at_cell(self, clicked_row, clicked_col):
        widget_name_in_cell = self.grid_slots[clicked_row][clicked_col]
        if not widget_name_in_cell: return

        origin_row, origin_col = -1, -1

        if widget_name_in_cell == "X":
            # Trova la cella d'origine (brute force, migliorabile)
            found_origin = False
            for r_scan in range(self.current_grid_rows.get()):
                for c_scan in range(self.current_grid_cols.get()):
                    slot_content = self.grid_slots[r_scan][c_scan]
                    if slot_content and slot_content != "X":
                        w_info_scan = next((w for w in self.WIDGETS if w["nome"] == slot_content), None)
                        if w_info_scan:
                            r_span, c_span = w_info_scan["size"][1], w_info_scan["size"][0]
                            if r_scan <= clicked_row < r_scan + r_span and \
                                    c_scan <= clicked_col < c_scan + c_span:
                                widget_name_in_cell = slot_content
                                origin_row, origin_col = r_scan, c_scan
                                found_origin = True;
                                break
                if found_origin: break
            if not found_origin: return
        else:
            origin_row, origin_col = clicked_row, clicked_col

        widget_info_to_remove = next((w for w in self.WIDGETS if w["nome"] == widget_name_in_cell), None)
        if not widget_info_to_remove: return

        cols_span, rows_span = widget_info_to_remove["size"]
        for r_offset in range(rows_span):
            for c_offset in range(cols_span):
                current_r, current_c = origin_row + r_offset, origin_col + c_offset
                if 0 <= current_r < self.current_grid_rows.get() and \
                        0 <= current_c < self.current_grid_cols.get():
                    self.grid_slots[current_r][current_c] = None

        self.render_grid_placeholders_and_widgets()

    def _draw_widget_on_grid(self, widget_info, row, col):
        cols_span, rows_span = widget_info["size"]

        widget_frame = ttkb.Frame(self.grid_area, relief=SOLID, borderwidth=1)  # Stile più visibile
        widget_frame.grid(row=row, column=col, rowspan=rows_span, columnspan=cols_span,
                          sticky="nsew", padx=1, pady=1)

        # Aggiungi un piccolo padding interno e centra il testo
        inner_frame = ttkb.Frame(widget_frame, padding=5)
        inner_frame.pack(expand=True, fill=BOTH)

        label = ttkb.Label(inner_frame, text=widget_info["label"], anchor="center")
        label.pack(expand=True, fill=BOTH)

        # Bind per la rimozione, assicurandosi che passi le coordinate corrette (quelle di origine)
        widget_frame.bind("<Button-3>", lambda e, r=row, c=col: self.remove_widget_at_cell(r, c))
        inner_frame.bind("<Button-3>", lambda e, r=row, c=col: self.remove_widget_at_cell(r, c))  # Anche su inner
        label.bind("<Button-3>", lambda e, r=row, c=col: self.remove_widget_at_cell(r, c))

    def _get_current_config_data(self):
        config_to_save = {
            "grid_rows": self.current_grid_rows.get(),
            "grid_cols": self.current_grid_cols.get(),
            "widgets": []
        }
        added_names = set()
        for r in range(self.current_grid_rows.get()):
            for c in range(self.current_grid_cols.get()):
                widget_name = self.grid_slots[r][c]
                if widget_name and widget_name != "X" and widget_name not in added_names:
                    widget_info = next((w for w in self.WIDGETS if w["nome"] == widget_name), None)
                    if widget_info:
                        config_to_save["widgets"].append({
                            "nome": widget_name, "visible": True, "row": r, "column": c,
                            "rowspan": widget_info["size"][1], "columnspan": widget_info["size"][0]
                        })
                        added_names.add(widget_name)
        return config_to_save

    def _save_to_file(self, config_data):
        try:
            os.makedirs(os.path.dirname(self.CONFIG_PATH), exist_ok=True)
            with open(self.CONFIG_PATH, "w") as f:
                json.dump(config_data, f, indent=4)
            return True
        except Exception as e:
            messagebox.showerror("Errore Salvataggio", f"Impossibile salvare la configurazione:\n{e}",
                                 parent=self.window)
            return False

    def apply_changes_no_close(self):
        current_config = self._get_current_config_data()
        if self._save_to_file(current_config):
            if self.refresh_callback:
                self.refresh_callback()
            messagebox.showinfo("Configurazione Applicata", "Le modifiche sono state applicate alla dashboard.",
                                parent=self.window)

    def save_config_and_close(self):
        current_config = self._get_current_config_data()
        if self._save_to_file(current_config):
            if self.refresh_callback:
                self.refresh_callback()
            self._on_close()  # Chiude la finestra

    def load_config_and_render(self):
        try:
            with open(self.CONFIG_PATH, "r") as f:
                config_data = json.load(f)

            loaded_rows = config_data.get("grid_rows", INITIAL_GRID_ROWS)  # Usa fallback
            loaded_cols = config_data.get("grid_cols", INITIAL_GRID_COLS)  # Usa fallback
            self.current_grid_rows.set(loaded_rows)
            self.current_grid_cols.set(loaded_cols)

            self._initialize_grid_slots()

            for item in config_data.get("widgets", []):
                if not item.get("visible", True): continue
                widget_name = item["nome"]
                widget_info = next((w for w in self.WIDGETS if w["nome"] == widget_name), None)
                if widget_info:
                    row, col = item["row"], item["column"]
                    # Nota: widget_info["size"] è (cols, rows)
                    if row + widget_info["size"][1] <= loaded_rows and col + widget_info["size"][0] <= loaded_cols:
                        self._internal_place_widget_data(widget_info, row, col)
        except FileNotFoundError:
            self._initialize_grid_slots()  # Inizia con griglia vuota se config non trovata
        except json.JSONDecodeError:
            messagebox.showerror("Errore Configurazione", f"File {self.CONFIG_PATH} corrotto.", parent=self.window)
            self._initialize_grid_slots()
        except Exception as e:
            messagebox.showerror("Errore Caricamento", f"Errore imprevisto: {e}", parent=self.window)
            self._initialize_grid_slots()

        self.render_grid_placeholders_and_widgets()

    def reset_default_config(self):
        if messagebox.askyesno("Conferma", "Ripristinare la configurazione predefinita?", parent=self.window):
            try:
                with open(self.DEFAULT_CONFIG_PATH, "r") as f_default:
                    default_config_data = json.load(f_default)

                if self._save_to_file(default_config_data):  # Salva default come corrente
                    self.load_config_and_render()  # Ricarica UI del configuratore
                    if self.refresh_callback:
                        self.refresh_callback()  # Aggiorna dashboard principale
                    messagebox.showinfo("Ripristino", "Configurazione predefinita ripristinata.", parent=self.window)
            except FileNotFoundError:
                messagebox.showerror("Errore", f"File default ({self.DEFAULT_CONFIG_PATH}) non trovato.",
                                     parent=self.window)
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile ripristinare: {e}", parent=self.window)


# --- Funzioni dell'Applicazione ---

def apri_dashboard(main_frame, app_root_window):  # Passa la finestra radice per Toplevel
    for widget in main_frame.winfo_children():
        widget.destroy()

    main_frame.columnconfigure(0, weight=1)  # Colonna unica per il contenuto della dashboard
    main_frame.rowconfigure(1, weight=1)  # Riga per i widget si espande

    header_frame = ttkb.Frame(main_frame)  # Frame per titolo e bottone config
    header_frame.grid(row=0, column=0, sticky="ew", pady=(10, 0), padx=20)
    header_frame.columnconfigure(0, weight=1)  # Titolo a sinistra

    titolo = ttkb.Label(header_frame, text="Dashboard", font=("Segoe UI", 18, "bold"))
    titolo.grid(row=0, column=0, sticky="w")

    widget_frame = ttkb.Frame(main_frame)  # Questo è il frame dove vanno i widget della dashboard
    widget_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

    current_rows_dash, current_cols_dash = INITIAL_GRID_ROWS, INITIAL_GRID_COLS
    widget_configurations_dash = []

    try:
        os.makedirs(DATA_DIR, exist_ok=True)  # Crea dir se non esiste
        with open(CONFIG_PATH_MAIN, "r") as f:
            config = json.load(f)
        current_rows_dash = config.get("grid_rows", INITIAL_GRID_ROWS)
        current_cols_dash = config.get("grid_cols", INITIAL_GRID_COLS)
        widget_configurations_dash = config.get("widgets", [])
    except FileNotFoundError:
        try:
            with open(DEFAULT_CONFIG_PATH_MAIN, "r") as f_default:
                config = json.load(f_default)
            current_rows_dash = config.get("grid_rows", INITIAL_GRID_ROWS)
            current_cols_dash = config.get("grid_cols", INITIAL_GRID_COLS)
            widget_configurations_dash = config.get("widgets", [])
            with open(CONFIG_PATH_MAIN, "w") as f_current:  # Salva default come corrente
                json.dump(config, f_current, indent=4)
        except FileNotFoundError:
            # Se anche il default non c'è, crea un file di config vuoto o con una base
            base_config = {"grid_rows": INITIAL_GRID_ROWS, "grid_cols": INITIAL_GRID_COLS, "widgets": []}
            with open(CONFIG_PATH_MAIN, "w") as f_current:
                json.dump(base_config, f_current, indent=4)
            # Potresti caricare una configurazione di default codificata qui se preferisci
        except Exception as e_load_default:
            messagebox.showerror("Errore Caricamento Default", f"Errore caricamento config default: {e_load_default}")
    except Exception as e:
        messagebox.showerror("Errore Caricamento Config", f"Errore caricamento dashboard: {e}")

    for i in range(current_cols_dash):
        widget_frame.columnconfigure(i, weight=1, uniform="col_dash")
    for i in range(current_rows_dash):
        widget_frame.rowconfigure(i, weight=1, uniform="row_dash")

    # Funzioni per creare i widget della dashboard
    def widget_saldo():
        frame = ttkb.LabelFrame(widget_frame, text="Saldo Totale", padding=10)
        try:
            conti = carica_conti()
            saldo_totale = sum(float(s) for s in conti.values())  # Assicura float
            ttkb.Label(frame, text=f"€ {saldo_totale:.2f}", font=("Segoe UI", 16)).pack(pady=5)
            for nome, saldo in conti.items():
                ttkb.Label(frame, text=f"{nome}: € {float(saldo):.2f}", font=("Segoe UI", 9), bootstyle=SECONDARY).pack(
                    anchor="w", padx=10)
        except Exception as e:
            ttkb.Label(frame, text=f"Errore caricamento dati: {e}", bootstyle=DANGER).pack()
        return frame

    def widget_transazioni():
        frame = ttkb.LabelFrame(widget_frame, text="Ultime Transazioni", padding=10)
        try:
            transazioni = carica_transazioni()
            for tr in sorted(transazioni, key=lambda x: x["data"], reverse=True)[:5]:
                importo = float(tr['importo'])
                riga = f"{tr['data']} | {tr['descrizione'][:20]}... | {tr['categoria']} | {importo:.2f} €"
                colore = SUCCESS if importo >= 0 else DANGER
                ttkb.Label(frame, text=riga, font=("Segoe UI", 10), bootstyle=colore).pack(anchor="w", fill=X)
        except Exception as e:
            ttkb.Label(frame, text=f"Errore caricamento dati: {e}", bootstyle=DANGER).pack()
        return frame

    def widget_investimenti():
        frame = ttkb.LabelFrame(widget_frame, text="Valore Portafoglio Investimenti", padding=10)
        ttkb.Label(frame, text="[Grafico Investimenti Placeholder]", font=("Segoe UI", 12, "italic"),
                   bootstyle=SECONDARY).pack(expand=True)
        return frame

    def widget_bilancio():
        frame = ttkb.LabelFrame(widget_frame, text="Bilancio Mensile", padding=10)
        try:
            transazioni = carica_transazioni()
            transazioni_mese = [t for t in transazioni if t["data"].startswith(datetime.today().strftime("%Y-%m"))]
            entrate = sum(float(t["importo"]) for t in transazioni_mese if float(t["importo"]) > 0)
            uscite = -sum(float(t["importo"]) for t in transazioni_mese if float(t["importo"]) < 0)
            bilancio = entrate - uscite
            ttkb.Label(frame, text=f"Entrate: € {entrate:.2f}", font=("Segoe UI", 10), bootstyle=SUCCESS).pack(
                anchor="w")
            ttkb.Label(frame, text=f"Uscite: € {uscite:.2f}", font=("Segoe UI", 10), bootstyle=DANGER).pack(anchor="w")
            ttkb.Label(frame, text=f"Bilancio: € {bilancio:.2f}", font=("Segoe UI", 12, "bold"),
                       bootstyle=(SUCCESS if bilancio >= 0 else DANGER)).pack(anchor="w", pady=(5, 0))
        except Exception as e:
            ttkb.Label(frame, text=f"Errore caricamento dati: {e}", bootstyle=DANGER).pack()
        return frame

    def widget_goal():
        frame = ttkb.LabelFrame(widget_frame, text="Obiettivi di Risparmio", padding=10)
        # Dati Mock
        obiettivi = [
            {"nome": "Vacanza Tokyo", "attuale": 2200, "target": 3000},
            {"nome": "Nuovo PC", "attuale": 500, "target": 1500}
        ]
        for obiettivo in obiettivi:
            ttkb.Label(frame, text=f"{obiettivo['nome']}: {obiettivo['attuale']} / {obiettivo['target']} €",
                       font=("Segoe UI", 10)).pack(anchor="w")
            prog_val = (obiettivo['attuale'] / obiettivo['target']) * 100 if obiettivo['target'] > 0 else 0
            ttkb.Progressbar(frame, value=prog_val, bootstyle=INFO).pack(fill=X, pady=(2, 8))
        return frame

    def widget_watchlist():
        frame = ttkb.LabelFrame(widget_frame, text="Watchlist Azioni", padding=10)
        # Dati Mock
        watchlist_items = [{"ticker": "AAPL", "prezzo": 185.20, "var": +1.25},
                           {"ticker": "TSLA", "prezzo": 172.55, "var": -2.14}]
        for t in watchlist_items:
            colore = SUCCESS if t["var"] >= 0 else DANGER
            riga = f"{t['ticker']}: € {t['prezzo']:.2f} ({t['var']:+.2f}%)"
            ttkb.Label(frame, text=riga, font=("Segoe UI", 10), bootstyle=colore).pack(anchor="w")
        return frame

    # Placeholder per gli altri widget
    def create_placeholder_widget(parent_frame, title):
        frame = ttkb.LabelFrame(parent_frame, text=title, padding=10)
        ttkb.Label(frame, text=f"[{title} - Contenuto Placeholder]", font=("Segoe UI", 10, "italic"),
                   bootstyle=SECONDARY).pack(expand=True)
        return frame

    widget_map = {
        "saldo": widget_saldo,
        "transazioni": widget_transazioni,
        "investimenti": widget_investimenti,
        "bilancio": widget_bilancio,
        "obiettivi": widget_goal,
        "watchlist": widget_watchlist,
        "scontrini": lambda: create_placeholder_widget(widget_frame, "Scansione Scontrini"),
        "statistiche_spese": lambda: create_placeholder_widget(widget_frame, "Statistiche Spese"),
        "prossime_spese": lambda: create_placeholder_widget(widget_frame, "Prossime Spese"),
        "calendario": lambda: create_placeholder_widget(widget_frame, "Calendario Finanziario"),
        "storico_saldo": lambda: create_placeholder_widget(widget_frame, "Storico Saldo"),
        "crediti_debiti": lambda: create_placeholder_widget(widget_frame, "Crediti e Debiti")
    }

    for w_conf in widget_configurations_dash:
        if w_conf.get("visible", False) and w_conf["nome"] in widget_map:
            try:
                widget_to_display = widget_map[w_conf["nome"]]()  # Chiamata alla funzione che crea il widget
                widget_to_display.grid(
                    row=w_conf["row"], column=w_conf["column"],
                    rowspan=w_conf.get("rowspan", 1), columnspan=w_conf.get("columnspan", 1),
                    padx=5, pady=5, sticky="nsew"
                )
            except Exception as e_widget_create:
                print(f"Errore creazione widget '{w_conf['nome']}': {e_widget_create}")
                # Potresti visualizzare un widget di errore sulla dashboard
                error_frame = ttkb.LabelFrame(widget_frame, text=f"Errore: {w_conf['nome']}", padding=5,
                                              bootstyle=DANGER)
                ttkb.Label(error_frame, text=f"Impossibile caricare:\n{e_widget_create}", wraplength=150).pack()
                error_frame.grid(row=w_conf["row"], column=w_conf["column"],
                                 rowspan=w_conf.get("rowspan", 1), columnspan=w_conf.get("columnspan", 1),
                                 padx=5, pady=5, sticky="nsew")

    def apri_configuratore_callback():
        try:
            with open(CONFIG_PATH_MAIN, "r") as f_cfg:
                cfg = json.load(f_cfg)
            initial_r_cfg = cfg.get("grid_rows", INITIAL_GRID_ROWS)
            initial_c_cfg = cfg.get("grid_cols", INITIAL_GRID_COLS)
        except:  # File non trovato o corrotto
            initial_r_cfg = INITIAL_GRID_ROWS
            initial_c_cfg = INITIAL_GRID_COLS

        ConfigDashboardWindow(
            app_root_window,  # Passa la finestra radice (app)
            lambda: apri_dashboard(main_frame, app_root_window),  # Callback
            initial_grid_rows=initial_r_cfg,
            initial_grid_cols=initial_c_cfg,
            widgets_list=WIDGETS,
            config_file_path=CONFIG_PATH_MAIN,
            default_config_file_path=DEFAULT_CONFIG_PATH_MAIN
        )

    btn_config = ttkb.Button(header_frame, text="⚙️ Configura", bootstyle=(SECONDARY, OUTLINE),
                             command=apri_configuratore_callback)
    btn_config.grid(row=0, column=1, sticky="e")


def apri_conti(main_frame, app_root_window):
    for widget in main_frame.winfo_children():
        widget.destroy()
    ttkb.Label(main_frame, text="Sezione Conti", font=("Segoe UI", 16, "bold")).pack(pady=20)
    # Qui andrà la logica e l'UI per la gestione dei conti


def apri_transazioni(main_frame, app_root_window):
    for widget in main_frame.winfo_children():
        widget.destroy()
    ttkb.Label(main_frame, text="Storico Transazioni", font=("Segoe UI", 16, "bold")).pack(pady=20)
    # Qui andrà la logica e l'UI per la gestione delle transazioni


def apri_investimenti(main_frame, app_root_window):
    for widget in main_frame.winfo_children():
        widget.destroy()
    ttkb.Label(main_frame, text="Portafoglio Investimenti", font=("Segoe UI", 16, "bold")).pack(pady=20)
    # Qui andrà la logica e l'UI per la gestione degli investimenti


def apri_impostazioni(main_frame, app_root_window):
    for widget in main_frame.winfo_children():
        widget.destroy()
    ttkb.Label(main_frame, text="Impostazioni Applicazione", font=("Segoe UI", 16, "bold")).pack(pady=20)
    # Qui andrà la logica e l'UI per le impostazioni globali


def saluto_random(nome="Utente"):  # Modificato nome default
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
    app = ttkb.Window(
        themename="superhero")  # Prova altri temi: "litera", "cosmo", "flatly", "journal", "darkly", "superhero", "solar", "cyborg", "vapor", "pulse", "united"
    app.title("Cato Finance")
    app.geometry("1280x720")
    app.minsize(900, 600)  # Min size leggermente aumentata

    app.update_idletasks()
    width = app.winfo_width()
    height = app.winfo_height()
    x = (app.winfo_screenwidth() // 2) - (width // 2)
    y = (app.winfo_screenheight() // 2) - (height // 2)
    app.geometry(f"{width}x{height}+{x}+{y}")

    app.columnconfigure(1, weight=1)
    app.rowconfigure(0, weight=1)

    sidebar = ttkb.Frame(app, padding=(10, 10), bootstyle=DARK, width=220)  # Larghezza sidebar
    sidebar.grid(row=0, column=0, sticky="ns")
    sidebar.grid_propagate(False)  # Impedisce alla sidebar di ridimensionarsi con il contenuto
    app.grid_columnconfigure(0, weight=0)  # Sidebar non si espande

    main_frame = ttkb.Frame(app, padding=0)  # Padding gestito internamente da apri_dashboard
    main_frame.grid(row=0, column=1, sticky="nsew")
    app.grid_columnconfigure(1, weight=1)

    ttkb.Label(sidebar, text=saluto_random(), font=("Segoe UI", 13, "bold"), bootstyle=(INVERSE, DARK)).pack(
        pady=(20, 25), padx=10)

    # Pulsanti della Sidebar
    nav_buttons_config = [
        ("🏠 Dashboard", lambda: apri_dashboard(main_frame, app)),
        ("💼 Conti", lambda: apri_conti(main_frame, app)),
        ("📜 Transazioni", lambda: apri_transazioni(main_frame, app)),
        ("📈 Investimenti", lambda: apri_investimenti(main_frame, app)),
    ]

    for text, command in nav_buttons_config:
        ttkb.Button(sidebar, text=text, bootstyle=(SECONDARY, DARK), command=command).pack(fill=X, padx=10, pady=6)

    # Separatore e Impostazioni in fondo
    ttkb.Separator(sidebar, bootstyle=SECONDARY).pack(fill=X, padx=10, pady=(15, 10))
    ttkb.Button(sidebar, text="⚙️ Impostazioni", bootstyle=(SECONDARY, DARK),
                command=lambda: apri_impostazioni(main_frame, app)).pack(fill=X, padx=10, side=BOTTOM,
                                                                         pady=(6, 15))  # Un solo pady

    apri_dashboard(main_frame, app)  # Mostra dashboard all'avvio

    def mostra_menu_plus(event):
        menu = ttkb.Menu(app, tearoff=0)
        # Queste sono azioni placeholder, dovrai implementare le finestre/funzioni reali
        menu.add_command(label="Aggiungi Transazione",
                         command=lambda: print("TODO: Apri finestra aggiungi transazione"))
        menu.add_command(label="Aggiungi Conto", command=lambda: print("TODO: Apri finestra aggiungi conto"))
        menu.add_command(label="Aggiungi Obiettivo", command=lambda: print("TODO: Apri finestra aggiungi obiettivo"))
        menu.add_separator()
        menu.add_command(label="Importa Estratto Conto",
                         command=lambda: print("TODO: Apri finestra importa estratto conto"))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        except tk.TclError:  # A volte può dare errore se il menu è già visibile o distrutto
            pass

    btn_plus = ttkb.Button(app, text="➕", bootstyle="success-outline", width=3) # o "success-toolbutton"
    btn_plus.place(relx=0.98, rely=0.95, anchor="se")  # Posizionato in basso a destra
    btn_plus.bind("<Button-1>", mostra_menu_plus)

    app.mainloop()


if __name__ == "__main__":
    # Assicurati che i file di configurazione di default esistano.
    # Se non esistono, creali con una struttura base.
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DEFAULT_CONFIG_PATH_MAIN):
        default_content = {
            "grid_rows": 6,
            "grid_cols": 6,
            "widgets": [  # Una configurazione di default minima
                {"nome": "saldo", "visible": True, "row": 0, "column": 0, "rowspan": 2, "columnspan": 3},
                {"nome": "transazioni", "visible": True, "row": 0, "column": 3, "rowspan": 2, "columnspan": 3},
                {"nome": "bilancio", "visible": True, "row": 2, "column": 0, "rowspan": 2, "columnspan": 2}
            ]
        }
        try:
            with open(DEFAULT_CONFIG_PATH_MAIN, "w") as f:
                json.dump(default_content, f, indent=4)
            print(f"Creato file di configurazione default: {DEFAULT_CONFIG_PATH_MAIN}")
        except Exception as e:
            print(f"Errore creazione file default config: {e}")

    main()