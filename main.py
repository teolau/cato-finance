import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
from storage import carica_conti, carica_transazioni
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import json
import os
import database
import services


# --- Costanti e Configurazioni Globali ---
DATA_DIR = "data"
CONFIG_PATH_MAIN = os.path.join(DATA_DIR, "dashboard_config.json")
DEFAULT_CONFIG_PATH_MAIN = os.path.join(DATA_DIR, "dashboard_config_default.json")

INITIAL_GRID_ROWS = 6
INITIAL_GRID_COLS = 6

WIDGETS = [
    {"nome": "saldo", "label": "Saldo Totale", "size": (3, 2), "factory": "widget_saldo"},
    {"nome": "transazioni", "label": "Ultime Transazioni", "size": (3, 2), "factory": "widget_transazioni"},
    {"nome": "investimenti", "label": "Portafoglio Investimenti", "size": (4, 2), "factory": "widget_investimenti"},
    {"nome": "bilancio", "label": "Bilancio Mensile", "size": (2, 2), "factory": "widget_bilancio"},
    {"nome": "obiettivi", "label": "Obiettivi Risparmio", "size": (2, 2), "factory": "widget_goal"},
    {"nome": "watchlist", "label": "Watchlist Azioni", "size": (2, 4), "factory": "widget_watchlist"},
    {"nome": "scontrini", "label": "Scansione Scontrini", "size": (2, 1), "factory": "widget_scontrini_placeholder"},
    {"nome": "statistiche_spese", "label": "Statistiche Spese", "size": (2, 1),
     "factory": "widget_statistiche_placeholder"},
    {"nome": "prossime_spese", "label": "Prossime Spese", "size": (2, 1),
     "factory": "widget_prossime_spese_placeholder"},
    {"nome": "calendario", "label": "Calendario Finanziario", "size": (2, 1),
     "factory": "widget_calendario_placeholder"},
    {"nome": "storico_saldo", "label": "Storico Saldo", "size": (2, 1), "factory": "widget_storico_saldo_placeholder"},
    {"nome": "crediti_debiti", "label": "Crediti e Debiti", "size": (2, 1),
     "factory": "widget_crediti_debiti_placeholder"},
]

# --- Stato Globale dell'Applicazione ---
app_state = {
    "edit_mode_active": False,
    "dashboard_config": None,
    "main_frame_ref": None,
    "app_root_ref": None,
    "widget_frame_ref": None,
    "displayed_widgets_map": {},
    "drag_data": {}
}


# --- Funzioni Factory per i Widget della Dashboard ---
# Il parametro 'parent_for_this_widget_content' è il frame in cui il contenuto
# effettivo del widget (es. un LabelFrame) deve essere inserito.
# In modalità modifica, sarà il 'wrapper'. In modalità visualizzazione, sarà 'widget_frame_ref'.

def widget_saldo(parent_for_this_widget_content):
    frame = ttkb.LabelFrame(parent_for_this_widget_content, text="Saldo Totale", padding=10)
    try:
        conti = services.ottieni_tutti_i_conti(solo_attivi=True)  # Chiama il servizio
        if conti is None:  # services.py potrebbe restituire None in caso di errore grave non gestito
            raise Exception("Errore nel caricamento dei conti.")

        saldo_totale = sum(float(c['saldo_attuale']) for c in conti)

        ttkb.Label(frame, text=f"€ {saldo_totale:.2f}", font=("Segoe UI", 16)).pack(pady=5)
        if not conti:
            ttkb.Label(frame, text="Nessun conto attivo trovato.", bootstyle=INFO).pack(pady=5)
        else:
            for conto_dict in conti:
                ttkb.Label(frame, text=f"{conto_dict['nome_conto']}: € {float(conto_dict['saldo_attuale']):.2f}",
                           font=("Segoe UI", 9), bootstyle=SECONDARY).pack(anchor="w", padx=10)
    except Exception as e:
        print(f"Errore in widget_saldo: {e}")
        ttkb.Label(frame, text=f"Errore caricamento saldi:\n{e}", bootstyle=DANGER, wraplength=200).pack(pady=5)
    return frame


def widget_transazioni(parent_for_this_widget_content):
    frame = ttkb.LabelFrame(parent_for_this_widget_content, text="Ultime Transazioni", padding=10)
    try:
        # Recupera, ad esempio, le ultime 5 transazioni da tutti i conti
        # services.ottieni_transazioni_filtrate non ha ancora un ordinamento per "ultime" globale,
        # ma get_transazioni_db ordina per data_transazione DESC.
        transazioni = services.ottieni_transazioni_filtrate(limit=5)  # Chiama il servizio
        if transazioni is None:
            raise Exception("Errore nel caricamento delle transazioni.")

        if not transazioni:
            ttkb.Label(frame, text="Nessuna transazione trovata.", bootstyle=INFO).pack(pady=5)
        else:
            # Il Treeview è più adatto per le transazioni, ma per un widget semplice usiamo Label
            for tr in transazioni:  # Ricorda che get_transazioni_db ora restituisce anche nome_conto
                importo = float(tr['importo'])
                # nome_conto_trans = tr.get('nome_conto', tr['id_conto_fk']) # Nome conto è già nel dict da get_transazioni_db
                riga = f"{datetime.strptime(tr['data_transazione'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m')} | {tr['nome_conto'][:10]}.. | {tr['descrizione'][:15]}... | {importo:.2f}€"
                colore = SUCCESS if importo >= 0 else DANGER
                ttkb.Label(frame, text=riga, font=("Segoe UI", 9), bootstyle=colore).pack(anchor="w", fill=X)
    except Exception as e:
        print(f"Errore in widget_transazioni: {e}")
        ttkb.Label(frame, text=f"Errore caricamento transazioni:\n{e}", bootstyle=DANGER, wraplength=200).pack(pady=5)
    return frame


def widget_investimenti(parent_for_this_widget_content):
    frame = ttkb.LabelFrame(parent_for_this_widget_content, text="Valore Portafoglio Investimenti", padding=10)
    ttkb.Label(frame, text="[Grafico Investimenti Placeholder]", font=("Segoe UI", 12, "italic"),
               bootstyle=SECONDARY).pack(expand=True)
    return frame


def widget_bilancio(parent_for_this_widget_content):
    frame = ttkb.LabelFrame(parent_for_this_widget_content, text="Bilancio Mensile", padding=10)
    try:
        oggi = datetime.now()
        primo_giorno_mese_dt = oggi.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Per l'ultimo giorno del mese, vai al primo del prossimo e togli un giorno
        # (o usa calendar.monthrange)
        import calendar
        _, ultimo_giorno_num = calendar.monthrange(oggi.year, oggi.month)
        ultimo_giorno_mese_dt = oggi.replace(day=ultimo_giorno_num, hour=23, minute=59, second=59, microsecond=999999)

        # Converti in stringhe per la funzione di servizio/db se necessario,
        # o modifica il servizio per accettare datetime
        data_inizio_str = primo_giorno_mese_dt.strftime("%Y-%m-%d %H:%M:%S")
        data_fine_str = ultimo_giorno_mese_dt.strftime("%Y-%m-%d %H:%M:%S")

        transazioni_mese = services.ottieni_transazioni_filtrate(
            data_inizio_str=data_inizio_str,
            data_fine_str=data_fine_str
        )
        if transazioni_mese is None:
            raise Exception("Errore caricamento transazioni per bilancio.")

        entrate = sum(float(t["importo"]) for t in transazioni_mese if float(t["importo"]) > 0)
        uscite = abs(sum(
            float(t["importo"]) for t in transazioni_mese if float(t["importo"]) < 0))  # Valore assoluto per le uscite
        bilancio = entrate - uscite

        ttkb.Label(frame, text=f"Entrate: € {entrate:.2f}", font=("Segoe UI", 10), bootstyle=SUCCESS).pack(anchor="w")
        ttkb.Label(frame, text=f"Uscite: € {uscite:.2f}", font=("Segoe UI", 10), bootstyle=DANGER).pack(anchor="w")
        ttkb.Label(frame, text=f"Bilancio: € {bilancio:.2f}", font=("Segoe UI", 12, "bold"),
                   bootstyle=(SUCCESS if bilancio >= 0 else DANGER)).pack(anchor="w", pady=(5, 0))
    except Exception as e:
        print(f"Errore in widget_bilancio: {e}")
        ttkb.Label(frame, text=f"Errore calcolo bilancio:\n{e}", bootstyle=DANGER, wraplength=200).pack(pady=5)
    return frame


def widget_goal(parent_for_this_widget_content):
    frame = ttkb.LabelFrame(parent_for_this_widget_content, text="Obiettivi di Risparmio", padding=10)
    obiettivi = [
        {"nome": "Vacanza Tokyo", "attuale": 2200, "target": 3000},
        {"nome": "Nuovo PC", "attuale": 500, "target": 1500}
    ]
    for obiettivo in obiettivi:
        ttkb.Label(frame, text=f"{obiettivo['nome']}: {obiettivo['attuale']} / {obiettivo['target']} €",
                   font=("Segoe UI", 10)).pack(anchor="w", fill=X, padx=5)
        prog_val = (obiettivo['attuale'] / obiettivo['target']) * 100 if obiettivo['target'] > 0 else 0
        ttkb.Progressbar(frame, value=prog_val, bootstyle=INFO).pack(fill=X, pady=(2, 8), padx=5)
    return frame


def widget_watchlist(parent_for_this_widget_content):
    frame = ttkb.LabelFrame(parent_for_this_widget_content, text="Watchlist Azioni", padding=10)
    watchlist_items = [{"ticker": "AAPL", "prezzo": 185.20, "var": +1.25},
                       {"ticker": "TSLA", "prezzo": 172.55, "var": -2.14}]
    for t in watchlist_items:
        colore = SUCCESS if t["var"] >= 0 else DANGER
        riga = f"{t['ticker']}: € {t['prezzo']:.2f} ({t['var']:+.2f}%)"
        ttkb.Label(frame, text=riga, font=("Segoe UI", 10), bootstyle=colore).pack(anchor="w")
    return frame


def _create_placeholder_factory(title_text):
    def factory(parent_for_this_widget_content):
        frame = ttkb.LabelFrame(parent_for_this_widget_content, text=title_text, padding=10)
        ttkb.Label(frame, text=f"[{title_text} Placeholder]", font=("Segoe UI", 10, "italic"),
                   bootstyle=SECONDARY).pack(expand=True, fill=BOTH)
        return frame

    return factory


widget_scontrini_placeholder = _create_placeholder_factory("Scansione Scontrini")
widget_statistiche_placeholder = _create_placeholder_factory("Statistiche Spese")
widget_prossime_spese_placeholder = _create_placeholder_factory("Prossime Spese")
widget_calendario_placeholder = _create_placeholder_factory("Calendario Finanziario")
widget_storico_saldo_placeholder = _create_placeholder_factory("Storico Saldo")
widget_crediti_debiti_placeholder = _create_placeholder_factory("Crediti e Debiti")

WIDGET_FACTORIES = {
    "widget_saldo": widget_saldo, "widget_transazioni": widget_transazioni,
    "widget_investimenti": widget_investimenti, "widget_bilancio": widget_bilancio,
    "widget_goal": widget_goal, "widget_watchlist": widget_watchlist,
    "widget_scontrini_placeholder": widget_scontrini_placeholder,
    "widget_statistiche_placeholder": widget_statistiche_placeholder,
    "widget_prossime_spese_placeholder": widget_prossime_spese_placeholder,
    "widget_calendario_placeholder": widget_calendario_placeholder,
    "widget_storico_saldo_placeholder": widget_storico_saldo_placeholder,
    "widget_crediti_debiti_placeholder": widget_crediti_debiti_placeholder,
}


def load_dashboard_config():
    global app_state
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(CONFIG_PATH_MAIN, "r") as f:
            app_state["dashboard_config"] = json.load(f)
    except FileNotFoundError:
        try:
            with open(DEFAULT_CONFIG_PATH_MAIN, "r") as f_default:
                app_state["dashboard_config"] = json.load(f_default)
            with open(CONFIG_PATH_MAIN, "w") as f_current:
                json.dump(app_state["dashboard_config"], f_current, indent=4)
        except FileNotFoundError:
            app_state["dashboard_config"] = {"grid_rows": INITIAL_GRID_ROWS, "grid_cols": INITIAL_GRID_COLS,
                                             "widgets": []}
            if not os.path.exists(DEFAULT_CONFIG_PATH_MAIN):
                with open(DEFAULT_CONFIG_PATH_MAIN, "w") as f_def_new: json.dump(app_state["dashboard_config"],
                                                                                 f_def_new, indent=4)
    except Exception as e:
        messagebox.showerror("Errore Caricamento Config", f"Errore: {e}")
        app_state["dashboard_config"] = {"grid_rows": INITIAL_GRID_ROWS, "grid_cols": INITIAL_GRID_COLS, "widgets": []}


def save_dashboard_config():
    global app_state
    if not app_state["dashboard_config"]: return
    try:
        with open(CONFIG_PATH_MAIN, "w") as f:
            json.dump(app_state["dashboard_config"], f, indent=4)
        if not app_state["edit_mode_active"]: messagebox.showinfo("Salvataggio", "Layout dashboard salvato.")
    except Exception as e:
        messagebox.showerror("Errore Salvataggio", f"Impossibile salvare: {e}")


def render_dashboard():
    global app_state
    if not app_state["main_frame_ref"] or not app_state["dashboard_config"]: return

    if app_state["widget_frame_ref"]:
        for child in app_state["widget_frame_ref"].winfo_children(): child.destroy()
    app_state["displayed_widgets_map"].clear()

    if not app_state["widget_frame_ref"] or not app_state["widget_frame_ref"].winfo_exists():
        app_state["widget_frame_ref"] = ttkb.Frame(app_state["main_frame_ref"])
        app_state["widget_frame_ref"].grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        app_state["main_frame_ref"].rowconfigure(1, weight=1)
        app_state["main_frame_ref"].columnconfigure(0, weight=1)

    cfg = app_state["dashboard_config"]
    rows = cfg.get("grid_rows", INITIAL_GRID_ROWS)
    cols = cfg.get("grid_cols", INITIAL_GRID_COLS)

    for i in range(cols): app_state["widget_frame_ref"].columnconfigure(i, weight=1, uniform="col_dash")
    for i in range(rows): app_state["widget_frame_ref"].rowconfigure(i, weight=1, uniform="row_dash")

    for widget_conf in cfg.get("widgets", []):
        if not widget_conf.get("visible", False): continue

        widget_name = widget_conf["nome"]
        widget_info = next((w for w in WIDGETS if w["nome"] == widget_name), None)
        if not widget_info: continue

        factory_name = widget_info.get("factory")
        if not factory_name or factory_name not in WIDGET_FACTORIES: continue

        actual_widget_content_labelframe = None  # Inizializza

        if app_state["edit_mode_active"]:
            wrapper = ttkb.Frame(app_state["widget_frame_ref"], relief=SOLID, borderwidth=1, padding=2)

            # Il LabelFrame (contenuto del widget) è figlio del WRAPPER
            actual_widget_content_labelframe = WIDGET_FACTORIES[factory_name](wrapper)
            actual_widget_content_labelframe.pack(expand=True, fill=BOTH, padx=5, pady=(15, 5))

            remove_btn = ttkb.Button(wrapper, text="✕", bootstyle=(DANGER, OUTLINE, TOOLBUTTON), width=2,
                                     command=lambda name=widget_name: remove_dashboard_widget(name))
            remove_btn.place(relx=1.0, rely=0.0, anchor="ne", x=-2, y=2)

            wrapper.grid(row=widget_conf["row"], column=widget_conf["column"],
                         rowspan=widget_conf.get("rowspan", 1), columnspan=widget_conf.get("columnspan", 1),
                         padx=7, pady=7, sticky="nsew")

            wrapper.bind("<ButtonPress-1>",
                         lambda event, w_name=widget_name, w_obj=wrapper: start_drag(event, w_name, w_obj))
            wrapper.bind("<B1-Motion>", lambda event, w_name=widget_name: do_drag(event, w_name))
            wrapper.bind("<ButtonRelease-1>", lambda event, w_name=widget_name: end_drag(event, w_name))

            app_state["displayed_widgets_map"][widget_name] = {"widget_obj": actual_widget_content_labelframe,
                                                               "wrapper": wrapper}
        else:
            # Il LabelFrame (contenuto del widget) è figlio di widget_frame_ref
            actual_widget_content_labelframe = WIDGET_FACTORIES[factory_name](app_state["widget_frame_ref"])
            actual_widget_content_labelframe.grid(row=widget_conf["row"], column=widget_conf["column"],
                                                  rowspan=widget_conf.get("rowspan", 1),
                                                  columnspan=widget_conf.get("columnspan", 1),
                                                  padx=5, pady=5, sticky="nsew")
            app_state["displayed_widgets_map"][widget_name] = {"widget_obj": actual_widget_content_labelframe,
                                                               "wrapper": None}

    if app_state["edit_mode_active"]:
        for r in range(rows):
            for c in range(cols):
                is_occupied = False
                for wc_check in cfg.get("widgets", []):
                    if wc_check.get("visible"):
                        r_start, c_start = wc_check["row"], wc_check["column"]
                        r_span, c_span = wc_check.get("rowspan", 1), wc_check.get("columnspan", 1)
                        if r_start <= r < r_start + r_span and c_start <= c < c_start + c_span:
                            is_occupied = True;
                            break
                if not is_occupied:
                    placeholder = ttkb.Frame(app_state["widget_frame_ref"], relief=SOLID, borderwidth=1)
                    placeholder.grid(row=r, column=c, rowspan=1, columnspan=1, padx=5, pady=5, sticky="nsew")
                    add_label = ttkb.Label(placeholder, text=f"+", bootstyle=(SECONDARY, LIGHT),
                                           font=("Segoe UI", 16, "bold"))
                    add_label.pack(expand=True)
                    placeholder.bind("<Button-1>", lambda e, r_val=r, c_val=c: add_widget_dialog(r_val, c_val))
                    add_label.bind("<Button-1>", lambda e, r_val=r, c_val=c: add_widget_dialog(r_val, c_val))


def toggle_edit_mode():
    global app_state
    app_state["edit_mode_active"] = not app_state["edit_mode_active"]

    if app_state.get("edit_mode_button_ref"):
        btn_text = "Salva Layout" if app_state["edit_mode_active"] else "Modifica Layout"
        style = SUCCESS if app_state["edit_mode_active"] else (SECONDARY, OUTLINE)
        app_state["edit_mode_button_ref"].config(text=btn_text, bootstyle=style)

    if not app_state["edit_mode_active"]: save_dashboard_config()
    render_dashboard()


def remove_dashboard_widget(widget_name_to_remove):
    global app_state
    config_widgets = app_state["dashboard_config"].get("widgets", [])
    for wc in config_widgets:
        if wc["nome"] == widget_name_to_remove: wc["visible"] = False; break
    render_dashboard()


def add_widget_dialog(target_row, target_col):
    global app_state
    dialog = ttkb.Toplevel(app_state["app_root_ref"])
    dialog.title("Aggiungi Widget")
    dialog.geometry("300x400");
    dialog.transient(app_state["app_root_ref"]);
    dialog.grab_set()
    ttkb.Label(dialog, text="Scegli un widget da aggiungere:", padding=10).pack()
    visible_widget_names = {wc['nome'] for wc in app_state["dashboard_config"]['widgets'] if wc.get('visible')}
    listbox = tk.Listbox(dialog, selectmode=SINGLE, exportselection=False, relief=SOLID, borderwidth=1)
    available_for_add = [w_info for w_info in WIDGETS if w_info['nome'] not in visible_widget_names]
    for w_info in available_for_add: listbox.insert(END, w_info['label'])
    listbox.pack(fill=BOTH, expand=True, padx=10, pady=5)
    if not available_for_add: ttkb.Label(dialog, text="Nessun widget disponibile.", bootstyle=INFO).pack(pady=10)

    def on_add_confirm():
        selected_indices = listbox.curselection()
        if not selected_indices or not available_for_add: dialog.destroy(); return
        selected_widget_info = available_for_add[selected_indices[0]]
        widget_name = selected_widget_info["nome"]
        found_in_config = False
        for wc in app_state["dashboard_config"]["widgets"]:
            if wc["nome"] == widget_name:
                wc.update({"visible": True, "row": target_row, "column": target_col,
                           "rowspan": selected_widget_info["size"][1], "columnspan": selected_widget_info["size"][0]})
                found_in_config = True;
                break
        if not found_in_config:
            app_state["dashboard_config"]["widgets"].append({
                "nome": widget_name, "visible": True, "row": target_row, "column": target_col,
                "rowspan": selected_widget_info["size"][1], "columnspan": selected_widget_info["size"][0]})
        dialog.destroy();
        render_dashboard()

    btn_frame = ttkb.Frame(dialog, padding=10);
    btn_frame.pack(fill=X)
    add_btn = ttkb.Button(btn_frame, text="Aggiungi", command=on_add_confirm, bootstyle=SUCCESS)
    add_btn.pack(side=LEFT, padx=5, expand=True, fill=X)
    if not available_for_add: add_btn.config(state=DISABLED)
    ttkb.Button(btn_frame, text="Annulla", command=dialog.destroy, bootstyle=LIGHT).pack(side=RIGHT, padx=5,
                                                                                         expand=True, fill=X)
    dialog.after(100, dialog.lift)


_ghost_window = None


def start_drag(event, widget_name, widget_object_wrapper):
    global app_state, _ghost_window
    if not app_state["edit_mode_active"]: return
    widget_conf = next((wc for wc in app_state["dashboard_config"]["widgets"] if wc["nome"] == widget_name), None)
    if not widget_conf: return

    app_state["drag_data"] = {"widget_name": widget_name, "item": widget_object_wrapper,
                              "start_x_root": event.x_root, "start_y_root": event.y_root,
                              "original_grid_info": widget_object_wrapper.grid_info(), "widget_conf": widget_conf}
    widget_object_wrapper.lift()
    if _ghost_window: _ghost_window.destroy()
    _ghost_window = ttkb.Toplevel(app_state["app_root_ref"]);
    _ghost_window.overrideredirect(True)
    _ghost_window.attributes("-alpha", 0.7)
    ghost_x, ghost_y = widget_object_wrapper.winfo_rootx(), widget_object_wrapper.winfo_rooty()
    _ghost_window.geometry(
        f"{widget_object_wrapper.winfo_width()}x{widget_object_wrapper.winfo_height()}+{ghost_x}+{ghost_y}")
    widget_label = next((w["label"] for w in WIDGETS if w["nome"] == widget_name), widget_name)
    ttkb.Label(_ghost_window, text=f"Muovi: {widget_label}", bootstyle=(PRIMARY, INVERSE), padding=10).pack(fill=BOTH,
                                                                                                            expand=True)
    _ghost_window.lift()


def do_drag(event, widget_name):
    global app_state, _ghost_window
    if not app_state["edit_mode_active"] or "item" not in app_state["drag_data"] or \
            not _ghost_window or not _ghost_window.winfo_exists(): return

    drag_info = app_state["drag_data"]
    # Calcola la nuova posizione del fantasma basata sul movimento del mouse dalla posizione iniziale del widget
    initial_widget_x = drag_info["item"].winfo_rootx() - (
                drag_info["start_x_root"] - drag_info["item"].winfo_rootx())  # Confuso, meglio più semplice
    initial_widget_y = drag_info["item"].winfo_rooty() - (drag_info["start_y_root"] - drag_info["item"].winfo_rooty())

    # Posizione del widget al momento del ButtonPress
    initial_wrapper_x_root = drag_info["item"].winfo_rootx()
    initial_wrapper_y_root = drag_info["item"].winfo_rooty()

    # Spostamento del mouse dalla sua posizione iniziale
    mouse_delta_x = event.x_root - drag_info["start_x_root"]
    mouse_delta_y = event.y_root - drag_info["start_y_root"]

    # Nuova posizione in alto a sinistra del fantasma
    new_ghost_x = initial_wrapper_x_root + mouse_delta_x
    new_ghost_y = initial_wrapper_y_root + mouse_delta_y

    _ghost_window.geometry(f"+{new_ghost_x}+{new_ghost_y}")


def end_drag(event, widget_name):
    global app_state, _ghost_window
    if not app_state["edit_mode_active"] or "item" not in app_state["drag_data"]: return
    if _ghost_window: _ghost_window.destroy(); _ghost_window = None

    original_widget_conf = app_state["drag_data"]["widget_conf"]
    drop_x_in_widget_frame = event.x_root - app_state["widget_frame_ref"].winfo_rootx()
    drop_y_in_widget_frame = event.y_root - app_state["widget_frame_ref"].winfo_rooty()
    grid_rows_total = app_state["dashboard_config"].get("grid_rows", INITIAL_GRID_ROWS)
    grid_cols_total = app_state["dashboard_config"].get("grid_cols", INITIAL_GRID_COLS)

    if app_state["widget_frame_ref"].winfo_width() > 1 and app_state["widget_frame_ref"].winfo_height() > 1:
        cell_width = app_state["widget_frame_ref"].winfo_width() / grid_cols_total
        cell_height = app_state["widget_frame_ref"].winfo_height() / grid_rows_total

        # Considera il centro del widget trascinato per il drop, o angolo alto-sx
        # Per semplicità, usiamo l'angolo alto-sx del punto di rilascio del mouse
        potential_col = int(drop_x_in_widget_frame / cell_width)
        potential_row = int(drop_y_in_widget_frame / cell_height)

        # Assicura che il widget non esca dalla griglia con il suo span
        widget_col_span = original_widget_conf.get("columnspan", 1)
        widget_row_span = original_widget_conf.get("rowspan", 1)

        target_col = max(0, min(potential_col, grid_cols_total - widget_col_span))
        target_row = max(0, min(potential_row, grid_rows_total - widget_row_span))

        can_place = True
        for r_offset in range(widget_row_span):
            for c_offset in range(widget_col_span):
                check_r, check_c = target_row + r_offset, target_col + c_offset
                for other_wc in app_state["dashboard_config"]["widgets"]:
                    if other_wc["nome"] == widget_name or not other_wc.get("visible"): continue
                    other_r_start, other_c_start = other_wc["row"], other_wc["column"]
                    other_r_span, other_c_span = other_wc.get("rowspan", 1), other_wc.get("columnspan", 1)
                    if other_r_start <= check_r < other_r_start + other_r_span and \
                            other_c_start <= check_c < other_c_start + other_c_span:
                        can_place = False;
                        break
                if not can_place: break
            if not can_place: break

        if can_place:
            original_widget_conf["row"] = target_row
            original_widget_conf["column"] = target_col
        render_dashboard()
    app_state["drag_data"] = {}


def apri_dashboard(main_frame_param, app_root_param):
    global app_state
    app_state["main_frame_ref"] = main_frame_param;
    app_state["app_root_ref"] = app_root_param
    for widget in main_frame_param.winfo_children(): widget.destroy()
    app_state["widget_frame_ref"] = None
    header_frame = ttkb.Frame(main_frame_param)
    header_frame.grid(row=0, column=0, sticky="ew", pady=(10, 0), padx=20)
    header_frame.columnconfigure(0, weight=1)
    ttkb.Label(header_frame, text="Dashboard", font=("Segoe UI", 18, "bold")).grid(row=0, column=0, sticky="w")
    edit_btn_text = "Salva Layout" if app_state["edit_mode_active"] else "Modifica Layout"
    edit_btn_style = SUCCESS if app_state["edit_mode_active"] else (SECONDARY, OUTLINE)
    edit_mode_button = ttkb.Button(header_frame, text=edit_btn_text, command=toggle_edit_mode, bootstyle=edit_btn_style)
    edit_mode_button.grid(row=0, column=1, sticky="e")
    app_state["edit_mode_button_ref"] = edit_mode_button
    main_frame_param.rowconfigure(1, weight=1);
    main_frame_param.columnconfigure(0, weight=1)
    if not app_state["dashboard_config"]: load_dashboard_config()
    render_dashboard()


def saluto_random(nome="Utente"):
    ora = datetime.now().hour
    saluto = "Ciao"
    if 5 <= ora < 12:
        saluto = "Buongiorno"
    elif 12 <= ora < 18:
        saluto = "Buon pomeriggio"
    elif 18 <= ora < 22:
        saluto = "Buonasera"
    return f"{saluto}, {nome}!"


def navigate_away_from_dashboard():
    global app_state
    if app_state["edit_mode_active"]:
        save_dashboard_config()  # Salva sempre prima di navigare via se in edit mode
        app_state["edit_mode_active"] = False


def apri_conti(main_frame, app_root):
    navigate_away_from_dashboard()
    for widget in main_frame.winfo_children(): widget.destroy()
    ttkb.Label(main_frame, text="Sezione Conti", font=("Segoe UI", 16, "bold")).pack(pady=20)


def apri_transazioni(main_frame, app_root):
    navigate_away_from_dashboard()
    for widget in main_frame.winfo_children(): widget.destroy()
    ttkb.Label(main_frame, text="Storico Transazioni", font=("Segoe UI", 16, "bold")).pack(pady=20)


def apri_investimenti(main_frame, app_root):
    navigate_away_from_dashboard()
    for widget in main_frame.winfo_children(): widget.destroy()
    ttkb.Label(main_frame, text="Portafoglio Investimenti", font=("Segoe UI", 16, "bold")).pack(pady=20)


def apri_impostazioni(main_frame, app_root):
    navigate_away_from_dashboard()
    for widget in main_frame.winfo_children(): widget.destroy()
    ttkb.Label(main_frame, text="Impostazioni Applicazione", font=("Segoe UI", 16, "bold")).pack(pady=20)


def main():
    global app_state
    app = ttkb.Window(themename="superhero");
    app.title("Cato Finance :)")
    app.geometry("1350x750");
    app.minsize(1000, 600);
    app_state["app_root_ref"] = app
    app.update_idletasks()
    width, height = app.winfo_width(), app.winfo_height()
    x, y = (app.winfo_screenwidth() // 2) - (width // 2), (app.winfo_screenheight() // 2) - (height // 2)
    app.geometry(f"{width}x{height}+{x}+{y}")
    app.columnconfigure(1, weight=1);
    app.rowconfigure(0, weight=1)
    sidebar = ttkb.Frame(app, padding=(10, 10), bootstyle=DARK, width=220)
    sidebar.grid(row=0, column=0, sticky="ns");
    sidebar.grid_propagate(False)
    app.grid_columnconfigure(0, weight=0)
    main_content_frame = ttkb.Frame(app, padding=0)
    main_content_frame.grid(row=0, column=1, sticky="nsew")
    ttkb.Label(sidebar, text=saluto_random(), font=("Segoe UI", 13, "bold"), bootstyle=(INVERSE, DARK)).pack(
        pady=(20, 25), padx=10)
    nav_buttons_config = [
        ("🏠 Dashboard", lambda: apri_dashboard(main_content_frame, app)),
        ("💼 Conti", lambda: apri_conti(main_content_frame, app)),
        ("📜 Transazioni", lambda: apri_transazioni(main_content_frame, app)),
        ("📈 Investimenti", lambda: apri_investimenti(main_content_frame, app)), ]
    for text, command in nav_buttons_config:
        ttkb.Button(sidebar, text=text, bootstyle=(SECONDARY, DARK), command=command).pack(fill=X, padx=10, pady=6)
    ttkb.Separator(sidebar, bootstyle=SECONDARY).pack(fill=X, padx=10, pady=(15, 10))
    ttkb.Button(sidebar, text="⚙️ Impostazioni App", bootstyle=(SECONDARY, DARK),
                command=lambda: apri_impostazioni(main_content_frame, app)).pack(fill=X, padx=10, side=BOTTOM,
                                                                                 pady=(0, 15))
    apri_dashboard(main_content_frame, app)

    def mostra_menu_plus(event):
        menu = ttkb.Menu(app, tearoff=0)
        menu.add_command(label="Aggiungi Transazione", command=lambda: print("TODO: Finestra Transazione"))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        except tk.TclError:
            pass

    btn_plus = ttkb.Button(app, text="➕", bootstyle="success-outline", width=3)
    btn_plus.place(relx=0.98, rely=0.95, anchor="se");
    btn_plus.bind("<Button-1>", mostra_menu_plus)

    def on_app_close():
        navigate_away_from_dashboard(); app.destroy()

    app.protocol("WM_DELETE_WINDOW", on_app_close)
    app.mainloop()


if __name__ == "__main__":
    database.initialize_database()
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DEFAULT_CONFIG_PATH_MAIN):
        default_widgets_config = []
        default_layout = [("saldo", 0, 0), ("transazioni", 0, 3), ("investimenti", 2, 0),
                          ("watchlist", 2, 4), ("bilancio", 4, 0), ("obiettivi", 4, 2)]
        placed_default_names = {item[0] for item in default_layout}
        for name, row, col in default_layout:
            w_info = next((w for w in WIDGETS if w['nome'] == name), None)
            if w_info: default_widgets_config.append({"nome": name, "visible": True, "row": row, "column": col,
                                                      "rowspan": w_info["size"][1], "columnspan": w_info["size"][0]})
        for w_info in WIDGETS:
            if w_info['nome'] not in placed_default_names:
                default_widgets_config.append({"nome": w_info['nome'], "visible": False, "row": 0, "column": 0,
                                               "rowspan": w_info["size"][1], "columnspan": w_info["size"][0]})
        default_content = {"grid_rows": INITIAL_GRID_ROWS, "grid_cols": INITIAL_GRID_COLS,
                           "widgets": default_widgets_config}
        try:
            with open(DEFAULT_CONFIG_PATH_MAIN, "w") as f:
                json.dump(default_content, f, indent=4)
            print(f"Creato file di configurazione default: {DEFAULT_CONFIG_PATH_MAIN}")
        except Exception as e:
            print(f"Errore creazione file default config: {e}")
    main()