import ttkbootstrap as ttkb
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, timedelta
import json
import os
import database
import services
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame # Utile per contenuti lunghi
from ttkbootstrap.dialogs import Messagebox # Per dialoghi ttkbootstrap-styled
from ttkbootstrap.toast import ToastNotification



# --- Costanti e Configurazioni Globali ---
DATA_DIR = "data"
CONFIG_PATH_MAIN = os.path.join(DATA_DIR, "dashboard_config.json")
DEFAULT_CONFIG_PATH_MAIN = os.path.join(DATA_DIR, "dashboard_config_default.json")

INITIAL_GRID_ROWS = 6
INITIAL_GRID_COLS = 6

# selected_account_id_for_transactions = None    (la uso se app_state mi dà problemi ma meglio evitare le global)

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
    "widget_frame_ref": None, # Per la dashboard
    "displayed_widgets_map": {}, # Per la dashboard
    "drag_data": {}, # Per la dashboard
    "widget_to_place_info": None, # Per la dashboard edit mode

    # Stato per la vista Conti e Transazioni (se non già qui, potresti aggiungerli)
    "selected_account_id_for_view": None,

    #VISTA INVESTIMENTI
    "inv_tree_ref": None,
    "inv_btn_modifica_ref": None,
    "inv_btn_aggiorna_val_ref": None,
    "inv_btn_acquista_ref": None,
    "inv_btn_vendi_ref": None,
    "inv_btn_chiudi_pos_ref": None,
    "inv_lbl_valore_tot_ref": None # Per il riepilogo
}


# --- Funzioni Factory per i Widget della Dashboard ---.

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


def apri_conti_e_transazioni_view(main_frame, app_root):
    # Usa le variabili globali definite a livello di modulo per i riferimenti ai widget
    global app_state, conti_tree, trans_tree, trans_labelframe
    global date_start_entry, date_end_entry, search_entry
    global btn_mod_conto, btn_correggi_saldo, btn_mod_trans, btn_del_trans

    app_state["selected_account_id_for_view"] = None
    app_state["active_view"] = "conti_transazioni"

    for widget in main_frame.winfo_children():
        widget.destroy()

    # --- INIZIO DEFINIZIONE FUNZIONI HELPER SPECIFICHE PER QUESTA VISTA ---
    # (Le tue funzioni helper definite qui, come nel tuo codice:
    # populate_conti_tree, populate_trans_tree, on_conto_select,
    # refresh_transactions_view, update_conti_buttons_state,
    # update_trans_buttons_state, refresh_all_views_callback)
    def attempt_sashpos_setup(paned_window_ref, main_frame_ref, sash_divisor=2.2):  # Funzione helper con nome standard
        """Tenta di impostare la posizione del sash, utile per il callback after."""
        try:
            if main_frame_ref.winfo_width() > 100:  # Assicurati che la larghezza sia ragionevolmente valida
                sash_position = int(main_frame_ref.winfo_width() / sash_divisor)
                paned_window_ref.sashpos(0, sash_position)
            else:
                # Potrebbe essere ancora troppo presto, si potrebbe aggiungere un contatore di tentativi
                # o semplicemente non fare nulla se la finestra è ancora troppo piccola.
                # print("Larghezza main_frame ancora non pronta per sashpos nel tentativo successivo.")
                pass
        except tk.TclError as e_retry:
            print(f"TclError nel tentativo successivo di impostare sashpos: {e_retry}")
        except Exception as e_gen:  # Cattura altri possibili errori
            print(f"Errore generico impostando sashpos nel tentativo successivo: {e_gen}")

        # Caricamento iniziale dati
        refresh_all_views_callback()  # Carica e imposta tutto
        on_conto_select()  # Per impostare lo stato iniziale del pannello transazioni

    def update_conti_buttons_state():
        if not conti_tree or not btn_gestisci_conto: return

        selected_items = conti_tree.selection()
        stato = NORMAL if selected_items else DISABLED
        btn_gestisci_conto.config(state=stato)

    def update_trans_buttons_state():
        if not trans_tree or not btn_mod_trans or not btn_del_trans: return
        selected_items = trans_tree.selection()
        stato = NORMAL if selected_items else DISABLED
        btn_mod_trans.config(state=stato)
        btn_del_trans.config(state=stato)

    def populate_conti_tree():
        if not conti_tree: return
        current_selection = conti_tree.selection()
        for item in conti_tree.get_children(): conti_tree.delete(item)
        try:
            lista_conti = services.ottieni_tutti_i_conti(solo_attivi=True)
            for conto_dict in lista_conti:
                conti_tree.insert("", END, iid=conto_dict['id_conto'],
                                  values=(conto_dict['nome_conto'], f"{float(conto_dict['saldo_attuale']):.2f} €"))
            if current_selection and conti_tree.exists(current_selection[0]):
                conti_tree.selection_set(current_selection[0])
                conti_tree.focus(current_selection[0])
        except Exception as e:
            Messagebox.show_error(f"Errore caricamento conti: {e}", "Errore Dati", parent=app_root)
        update_conti_buttons_state()

    def populate_trans_tree(data_s_param=None, data_e_param=None, search_term_param=None,
                            default_load=False):  # Aggiunto default_load come nel tuo codice
        if not trans_tree: return
        for item in trans_tree.get_children(): trans_tree.delete(item)
        try:
            transazioni_da_mostrare = None  # Inizializza
            if default_load and data_s_param is None and data_e_param is None and search_term_param is None:  # Caso di caricamento iniziale senza filtri specifici
                transazioni_da_mostrare = services.ottieni_transazioni_filtrate(
                    id_conto_fk=app_state.get("selected_account_id_for_view"),
                    # Non passare date se vuoi le ultime globali o del conto
                    limit=100
                )
            else:  # Caso con filtri applicati o lista passata (anche se transazioni_list non è un param qui)
                data_s_to_use = data_s_param if data_s_param is not None else (
                    date_start_entry.entry.get() if date_start_entry else None)
                data_e_to_use = data_e_param if data_e_param is not None else (
                    date_end_entry.entry.get() if date_end_entry else None)
                termine_ricerca_to_use = search_term_param.lower() if search_term_param is not None else (
                    search_entry.get().lower() if search_entry else "")

                try:
                    if data_s_to_use: datetime.strptime(data_s_to_use, "%Y-%m-%d")
                    if data_e_to_use: datetime.strptime(data_e_to_use, "%Y-%m-%d")
                except ValueError:
                    Messagebox.show_warning("Formato data non valido per il filtro. Usare YYYY-MM-DD.",
                                            "Attenzione Filtri", parent=app_root)
                    return
                transazioni_da_mostrare = services.ottieni_transazioni_filtrate(
                    id_conto_fk=app_state.get("selected_account_id_for_view"),
                    data_inizio_str=data_s_to_use, data_fine_str=data_e_to_use, limit=200
                )
                if termine_ricerca_to_use:
                    transazioni_da_mostrare = [t for t in transazioni_da_mostrare if termine_ricerca_to_use in t[
                        'descrizione'].lower() or termine_ricerca_to_use in t[
                                                   'categoria'].lower() or termine_ricerca_to_use in t[
                                                   'nome_conto'].lower()]

            if transazioni_da_mostrare:  # Controlla se ci sono transazioni da mostrare
                for tr in transazioni_da_mostrare:
                    importo_val = float(tr['importo'])
                    tag_colore = "entrata" if importo_val >= 0 else "uscita"
                    data_vis = datetime.strptime(tr['data_transazione'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%y %H:%M')
                    trans_tree.insert("", END, iid=tr['id_transazione'], values=(
                    data_vis, tr['nome_conto'], tr['descrizione'], tr['categoria'], f"{importo_val:.2f} €"),
                                      tags=(tag_colore,))
        except Exception as e:
            Messagebox.show_error(f"Errore caricamento transazioni: {e}", "Errore Dati", parent=app_root)
            print(f"Dettaglio errore populate_trans_tree: {e.__class__.__name__}: {e}")
        update_trans_buttons_state()

    def refresh_transactions_view(data_s_str_param=None, data_e_str_param=None,
                                  search_term_str_param=None):  # Rinominata e parametri
        # Questa è la funzione chiamata dal bottone Filtra
        data_s = data_s_str_param if data_s_str_param is not None else (
            date_start_entry.entry.get() if date_start_entry else None)
        data_e = data_e_str_param if data_e_str_param is not None else (
            date_end_entry.entry.get() if date_end_entry else None)
        search_term = search_term_str_param if search_term_str_param is not None else (
            search_entry.get() if search_entry else "")

        populate_trans_tree(
            data_s_param=data_s,
            data_e_param=data_e,
            search_term_param=search_term,
            default_load=False  # Indica che è un'azione di filtro, non il caricamento di default
        )

    def on_conto_select(event=None):
        global app_state, selected_account_id_for_transactions  # Assicurati che selected_account_id_for_transactions sia gestito
        if not conti_tree: return
        selected_items = conti_tree.selection()
        current_selected_id = None
        if selected_items:
            current_selected_id = selected_items[0]
            app_state["selected_account_id_for_view"] = current_selected_id  # Aggiorna app_state
            # selected_account_id_for_transactions = current_selected_id # Se usavi questa globale
            if trans_labelframe:
                try:
                    nome_conto_sel = conti_tree.item(current_selected_id)['values'][0]
                    trans_labelframe.config(text=f"Transazioni di: {nome_conto_sel}")
                except (tk.TclError, IndexError):
                    trans_labelframe.config(text="Transazioni")
        else:
            app_state["selected_account_id_for_view"] = None
            # selected_account_id_for_transactions = None
            if trans_labelframe: trans_labelframe.config(text="Tutte le Transazioni")

        # Quando un conto è selezionato/deselezionato, aggiorna le transazioni usando i filtri correnti
        refresh_transactions_view()
        update_conti_buttons_state()

    def refresh_all_views_callback():
        # global selected_account_id_for_transactions # Se la usi
        id_conto_sel = app_state.get("selected_account_id_for_view")  # Usa app_state
        # id_conto_sel = selected_account_id_for_transactions # Se usi la globale

        populate_conti_tree()

        if id_conto_sel and conti_tree and conti_tree.exists(id_conto_sel):
            conti_tree.selection_set(id_conto_sel)
            try:
                nome_c = conti_tree.item(id_conto_sel)['values'][0]
                if trans_labelframe: trans_labelframe.config(text=f"Transazioni di: {nome_c}")
            except (tk.TclError, IndexError):
                if trans_labelframe: trans_labelframe.config(text="Transazioni")
        else:
            app_state["selected_account_id_for_view"] = None  # Assicura che sia None
            # selected_account_id_for_transactions = None
            if trans_labelframe: trans_labelframe.config(text="Tutte le Transazioni")

        # Chiama populate_trans_tree senza parametri per usare i valori dei filtri e la selezione corrente
        populate_trans_tree(default_load=True)  # Indica che è un caricamento di default o post-azione
        # update_conti_buttons_state() # Già in populate_conti_tree
        # update_trans_buttons_state() # Già in populate_trans_tree

    # --- FINE DEFINIZIONE FUNZIONI HELPER ---

    # --- Header della Sezione ---
    header_sec = ttkb.Frame(main_frame, padding=(10, 10))
    header_sec.pack(fill=X)
    ttkb.Label(header_sec, text="Conti e Transazioni", font=("Segoe UI", 18, "bold")).pack(side=LEFT, padx=(0, 20))
    btn_nuova_transazione = ttkb.Button(header_sec, text="➕ Nuova Transazione", bootstyle=SUCCESS,
                                        command=lambda: apri_dialog_nuova_transazione(app_root,
                                                                                      refresh_all_views_callback))
    btn_nuova_transazione.pack(side=RIGHT)
    ttkb.Separator(main_frame, orient=HORIZONTAL).pack(fill=X, pady=5, padx=10)

    # --- Barra Filtri Globali ---
    filtri_frame = ttkb.Frame(main_frame, padding=(10, 0))
    filtri_frame.pack(fill=X, pady=(0, 10))
    ttkb.Label(filtri_frame, text="Periodo: Dal").pack(side=LEFT, padx=(0, 5))
    date_start_entry_widget = ttkb.DateEntry(filtri_frame, bootstyle=INFO, firstweekday=0,
                                             dateformat="%Y-%m-%d")  # Nome widget locale
    date_start_entry = date_start_entry_widget  # Assegna alla variabile globale/di modulo
    oggi_dt = datetime.today()
    data_inizio_str = (oggi_dt.replace(day=1) - timedelta(days=60)).replace(day=1).strftime("%Y-%m-%d")
    date_start_entry.entry.delete(0, END)
    date_start_entry.entry.insert(0, data_inizio_str)
    date_start_entry.pack(side=LEFT, padx=(0, 10))

    ttkb.Label(filtri_frame, text="Al").pack(side=LEFT, padx=(0, 5))
    date_end_entry_widget = ttkb.DateEntry(filtri_frame, bootstyle=INFO, firstweekday=0,
                                           dateformat="%Y-%m-%d")  # Nome widget locale
    date_end_entry = date_end_entry_widget  # Assegna
    data_fine_str = oggi_dt.strftime("%Y-%m-%d")
    date_end_entry.entry.delete(0, END)
    date_end_entry.entry.insert(0, data_fine_str)
    date_end_entry.pack(side=LEFT, padx=(0, 20))

    ttkb.Label(filtri_frame, text="Cerca:").pack(side=LEFT, padx=(0, 5))
    search_entry_widget = ttkb.Entry(filtri_frame, bootstyle=INFO)  # Nome widget locale
    search_entry = search_entry_widget  # Assegna
    search_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))

    btn_applica_filtri = ttkb.Button(filtri_frame, text="🔍", bootstyle=(INFO, OUTLINE),
                                     command=refresh_transactions_view)  # Ora refresh_transactions_view è definita
    btn_applica_filtri.pack(side=LEFT)

    # --- Layout Principale con PanedWindow ---
    paned_window = ttkb.PanedWindow(main_frame, orient=HORIZONTAL, bootstyle=PRIMARY)
    paned_window.pack(fill=BOTH, expand=True, padx=10, pady=5)

    # --- Pannello Conti (Sinistra) ---
    conti_panel_container = ttkb.Frame(paned_window, padding=0, width=400)  # Suggerisci larghezza iniziale
    conti_labelframe = ttkb.LabelFrame(conti_panel_container, text="I Miei Conti", padding=10, bootstyle=INFO)
    conti_labelframe.pack(fill=BOTH, expand=True)
    cols_conti = ("nome_conto", "saldo_attuale")
    conti_tree_widget = ttk.Treeview(conti_labelframe, columns=cols_conti, show="headings", height=8,
                                     selectmode="browse")
    conti_tree = conti_tree_widget  # Assegna alla variabile globale/di modulo
    conti_tree.heading("nome_conto", text="Nome Conto")
    conti_tree.heading("saldo_attuale", text="Saldo", anchor=E)  # Allineato a destra per numeri
    conti_tree.column("nome_conto", width=200, stretch=True, minwidth=180)
    conti_tree.column("saldo_attuale", width=120, stretch=False, anchor=E, minwidth=100)  # Allineato a destra
    conti_tree_scroll = ttkb.Scrollbar(conti_labelframe, orient=VERTICAL, command=conti_tree.yview,
                                       bootstyle="round-info")
    conti_tree.configure(yscrollcommand=conti_tree_scroll.set)
    conti_tree_scroll.pack(side=RIGHT, fill=Y)
    conti_tree.pack(fill=BOTH, expand=True, pady=(0, 10))
    conti_btn_frame = ttkb.Frame(conti_labelframe)
    conti_btn_frame.pack(fill=X)
    conti_btn_frame.columnconfigure((0, 1, 2), weight=1)  # Per far espandere i bottoni se usi grid
    btn_nuovo_conto = ttkb.Button(conti_btn_frame, text="➕ Nuovo", bootstyle=(SUCCESS, OUTLINE),  # width=10 rimosso
                                  command=lambda: apri_dialog_nuovo_conto(app_root, refresh_all_views_callback))
    btn_nuovo_conto.grid(row=0, column=0, padx=(0, 2), sticky="ew")  # Usa grid
    btn_gestisci_conto_widget = ttkb.Button(conti_btn_frame, text="⚙️ Gestisci Conto",
                                            bootstyle=(PRIMARY, OUTLINE),  # Stile generico
                                            state=DISABLED,
                                            command=lambda: apri_dialog_gestisci_conto(app_root,
                                                                                       refresh_all_views_callback))
    btn_gestisci_conto = btn_gestisci_conto_widget  # Assegna alla variabile che userà update_conti_buttons_state
    btn_gestisci_conto.grid(row=0, column=1, columnspan=2, padx=(2, 0), sticky="ew")  # Occupa le due colonne rimanenti


    paned_window.add(conti_panel_container, weight=1)

    # --- Pannello Transazioni (Destra) ---
    trans_panel_container = ttkb.Frame(paned_window, padding=0)
    trans_labelframe_widget = ttkb.LabelFrame(trans_panel_container, text="Transazioni", padding=10, bootstyle=PRIMARY)
    trans_labelframe = trans_labelframe_widget  # Assegna
    trans_labelframe.pack(fill=BOTH, expand=True)
    cols_trans = ("data", "conto", "descrizione", "categoria", "importo")
    trans_tree_widget = ttk.Treeview(trans_labelframe, columns=cols_trans, show="headings", height=10,
                                     selectmode="browse")
    trans_tree = trans_tree_widget  # Assegna
    # ... (resto della configurazione di trans_tree come prima, usando la variabile locale trans_tree)
    trans_tree.heading("data", text="Data", command=lambda: sort_treeview_column(trans_tree, "data", False))
    trans_tree.heading("conto", text="Conto", command=lambda: sort_treeview_column(trans_tree, "conto", False))
    trans_tree.heading("descrizione", text="Descrizione",
                       command=lambda: sort_treeview_column(trans_tree, "descrizione", False))
    trans_tree.heading("categoria", text="Categoria",
                       command=lambda: sort_treeview_column(trans_tree, "categoria", False))
    trans_tree.heading("importo", text="Importo", anchor=E,
                       command=lambda: sort_treeview_column(trans_tree, "importo", True))
    trans_tree.column("data", width=130, stretch=False, anchor=W, minwidth=110)
    trans_tree.column("conto", width=130, stretch=False, anchor=W, minwidth=100)
    trans_tree.column("descrizione", width=250, stretch=True, anchor=W, minwidth=150)
    trans_tree.column("categoria", width=120, stretch=False, anchor=W, minwidth=100)
    trans_tree.column("importo", width=100, stretch=False, anchor=E, minwidth=80)
    trans_tree.tag_configure("entrata",
                             foreground=app_root.style.colors.success if hasattr(app_root.style, 'colors') else 'green')
    trans_tree.tag_configure("uscita",
                             foreground=app_root.style.colors.danger if hasattr(app_root.style, 'colors') else 'red')
    trans_tree_scroll_y = ttkb.Scrollbar(trans_labelframe, orient=VERTICAL, command=trans_tree.yview,
                                         bootstyle="round-primary")
    trans_tree.configure(yscrollcommand=trans_tree_scroll_y.set)
    trans_tree_scroll_x = ttkb.Scrollbar(trans_labelframe, orient=HORIZONTAL, command=trans_tree.xview,
                                         bootstyle="round-primary")
    trans_tree.configure(xscrollcommand=trans_tree_scroll_x.set)
    trans_tree_scroll_y.pack(side=RIGHT, fill=Y);
    trans_tree_scroll_x.pack(side=BOTTOM, fill=X);
    trans_tree.pack(fill=BOTH, expand=True)
    trans_btn_frame = ttkb.Frame(trans_labelframe);
    trans_btn_frame.pack(fill=X, pady=(10, 0))
    btn_mod_trans_widget = ttkb.Button(trans_btn_frame, text="✏️ Modifica Transazione", bootstyle=(INFO, OUTLINE),
                                       state=DISABLED,
                                       command=lambda: apri_dialog_modifica_transazione(app_root,
                                                                                        refresh_all_views_callback))
    btn_mod_trans = btn_mod_trans_widget  # Assegna
    btn_mod_trans.pack(side=LEFT, padx=(0, 5))
    btn_del_trans_widget = ttkb.Button(trans_btn_frame, text="🗑️ Elimina Transazione", bootstyle=(DANGER, OUTLINE),
                                       state=DISABLED,
                                       command=lambda: elimina_transazione_selezionata(refresh_all_views_callback))
    btn_del_trans = btn_del_trans_widget  # Assegna
    btn_del_trans.pack(side=LEFT, padx=5)
    # CORREZIONE: Rimuovi minsize
    paned_window.add(trans_panel_container, weight=2)

    main_frame.update_idletasks()
    attempt_sashpos_setup(paned_window, main_frame, sash_divisor=2.25)  # Modificato sash_divisor

    # Binding Eventi (dopo che tutti i widget UI sono stati creati e i loro ref sono stati assegnati)
    conti_tree.bind("<<TreeviewSelect>>", on_conto_select)  # Usa la var locale/globale corretta
    trans_tree.bind("<<TreeviewSelect>>", lambda e: update_trans_buttons_state())  # Usa la var locale/globale corretta

    # Caricamento iniziale dati
    refresh_all_views_callback()


def apri_dialog_gestisci_conto(app_root_param, callback_refresh):
    if not conti_tree or not conti_tree.selection():  # conti_tree deve essere accessibile
        Messagebox.show_info("Nessuna Selezione", "Seleziona un conto da gestire.", parent=app_root_param)
        return

    selected_item_id_str = conti_tree.selection()[0]
    id_conto_selezionato = int(selected_item_id_str)

    conto_originale = services.ottieni_conto_per_id(id_conto_selezionato)
    if not conto_originale:
        Messagebox.show_error(f"Conto ID {id_conto_selezionato} non trovato.", "Errore", parent=app_root_param)
        callback_refresh()
        return

    dialog = ttkb.Toplevel(master=app_root_param, title=f"⚙️ Gestisci Conto: {conto_originale['nome_conto']}")
    dialog.geometry("550x400")  # Un po' più grande per le schede
    dialog.transient(app_root_param)
    dialog.grab_set()
    dialog.resizable(False, False)  # O True se vuoi permettere resize

    # --- Notebook per le Schede ---
    notebook = ttk.Notebook(dialog, bootstyle="primary")  # Usa ttk.Notebook, non ttkb.Notebook se non esiste
    notebook.pack(fill=BOTH, expand=True, padx=10, pady=10)

    # --- Scheda 1: Dettagli Conto ---
    tab_dettagli = ttkb.Frame(notebook, padding=15)
    notebook.add(tab_dettagli, text="Dettagli Conto")

    # Variabili e Campi per la scheda Dettagli (come in apri_dialog_modifica_conto)
    nome_conto_var_gest = tk.StringVar(value=conto_originale['nome_conto'])
    tipo_conto_var_gest = tk.StringVar(value=conto_originale.get('tipo_conto', "Bancario"))
    valuta_var_gest = tk.StringVar(value=conto_originale.get('valuta', "EUR"))
    # Opzionale: stato attivo/inattivo
    attivo_var_gest = tk.BooleanVar(value=bool(conto_originale.get('attivo', 1)))

    ttkb.Label(tab_dettagli, text="Nome Conto:", anchor=W).grid(row=0, column=0, sticky="ew", pady=5, padx=(0, 10))
    nome_conto_entry_gest = ttkb.Entry(tab_dettagli, textvariable=nome_conto_var_gest, bootstyle=PRIMARY)
    nome_conto_entry_gest.grid(row=0, column=1, sticky="ew", pady=5)
    nome_conto_entry_gest.focus_set()
    nome_conto_entry_gest.select_range(0, END)

    tipi_conto_comuni = ["Bancario", "Carta di Credito", "Contanti", "Risparmio", "Investimento", "Altro"]
    ttkb.Label(tab_dettagli, text="Tipo Conto:", anchor=W).grid(row=1, column=0, sticky="ew", pady=5, padx=(0, 10))
    tipo_conto_combo_gest = ttkb.Combobox(tab_dettagli, textvariable=tipo_conto_var_gest, values=tipi_conto_comuni,
                                          bootstyle=PRIMARY, state="readonly")
    tipo_conto_combo_gest.grid(row=1, column=1, sticky="ew", pady=5)

    ttkb.Label(tab_dettagli, text="Valuta:", anchor=W).grid(row=2, column=0, sticky="ew", pady=5, padx=(0, 10))
    valuta_entry_gest = ttkb.Entry(tab_dettagli, textvariable=valuta_var_gest, bootstyle=PRIMARY)
    valuta_entry_gest.grid(row=2, column=1, sticky="ew", pady=5)

    # Checkbutton per stato Attivo/Inattivo
    chk_attivo_gest = ttkb.Checkbutton(tab_dettagli, variable=attivo_var_gest, text="Conto Attivo",
                                       bootstyle="primary-round-toggle")
    chk_attivo_gest.grid(row=3, column=1, sticky="w", pady=(10, 5))

    tab_dettagli.columnconfigure(1, weight=1)

    def on_salva_dettagli_conto():
        nuovo_nome = nome_conto_var_gest.get()
        nuovo_tipo = tipo_conto_var_gest.get()
        nuova_valuta = valuta_var_gest.get()
        nuovo_stato_attivo = attivo_var_gest.get()
        modifiche_effettuate = False
        try:
            if nuovo_nome != conto_originale['nome_conto']:
                services.modifica_nome_conto(id_conto_selezionato, nuovo_nome)
                modifiche_effettuate = True

            if nuovo_tipo != conto_originale.get('tipo_conto') or \
                    nuova_valuta != conto_originale.get('valuta') or \
                    nuovo_stato_attivo != bool(conto_originale.get('attivo')):
                # Aggiorna tipo, valuta e stato attivo direttamente o tramite un servizio dedicato
                conn = database.get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE conti SET tipo_conto = ?, valuta = ?, attivo = ? WHERE id_conto = ?",
                               (nuovo_tipo, nuova_valuta, 1 if nuovo_stato_attivo else 0, id_conto_selezionato))
                conn.commit()
                conn.close()
                modifiche_effettuate = True

            if modifiche_effettuate:
                toast = ToastNotification(
                    title="Dettagli Conto",
                    message="Dettagli del conto aggiornati con successo!",
                    duration=3000,  # Millisecondi (3 secondi)
                    bootstyle=SUCCESS,  # O INFO
                    alert=True,  # Fa un suono
                    position=(20, 20, 'se')
                    # Posizione: 20px dal basso, 20px da destra, angolo sud-est (rispetto alla root)
                )
                toast.show_toast()

                callback_refresh()
                # Se il nome è cambiato, aggiorna il titolo del dialogo
                conto_aggiornato = services.ottieni_conto_per_id(
                    id_conto_selezionato)  # Ricarica per avere i dati freschi
                if conto_aggiornato:
                    dialog.title(f"⚙️ Gestisci Conto: {conto_aggiornato['nome_conto']}")
                    # Aggiorna anche conto_originale per la scheda correggi saldo
                    global conto_originale_ref  # Se necessario per accedervi da altre funzioni interne al dialogo
                    conto_originale.update(conto_aggiornato)  # Aggiorna il dizionario
                    lbl_saldo_attuale_corr.config(
                        text=f"{float(conto_originale['saldo_attuale']):.2f} {conto_originale.get('valuta', 'EUR')}")
                    nuovo_saldo_entry_corr.delete(0, END)
                    nuovo_saldo_entry_corr.insert(0, f"{float(conto_originale['saldo_attuale']):.2f}")


        except ValueError as ve:
            Messagebox.show_warning(str(ve), "Dati Non Validi", parent=dialog, alert=True)
        except Exception as e:
            Messagebox.show_error(f"Errore imprevisto:\n{e}", "Errore Modifica Conto", parent=dialog, alert=True)

    btn_salva_dettagli = ttkb.Button(tab_dettagli, text="Salva Dettagli", command=on_salva_dettagli_conto,
                                     bootstyle=(SUCCESS, OUTLINE))
    btn_salva_dettagli.grid(row=4, column=1, sticky="e", pady=(15, 0))

    # --- Scheda 2: Correggi Saldo ---
    tab_correggi = ttkb.Frame(notebook, padding=15)
    notebook.add(tab_correggi, text="Correggi Saldo")

    # Campi per la scheda Correggi Saldo (come in apri_dialog_correggi_saldo)
    ttkb.Label(tab_correggi, text=f"Saldo Attuale:", anchor=W).grid(row=0, column=0, sticky="ew", pady=5, padx=(0, 10))
    lbl_saldo_attuale_corr = ttkb.Label(tab_correggi,
                                        text=f"{float(conto_originale['saldo_attuale']):.2f} {conto_originale.get('valuta', 'EUR')}",
                                        anchor=E)
    lbl_saldo_attuale_corr.grid(row=0, column=1, sticky="ew", pady=5)

    ttkb.Label(tab_correggi, text="Nuovo Saldo Desiderato:", anchor=W).grid(row=1, column=0, sticky="ew", pady=5,
                                                                            padx=(0, 10))
    nuovo_saldo_entry_corr = ttkb.Entry(tab_correggi, bootstyle=PRIMARY)
    nuovo_saldo_entry_corr.grid(row=1, column=1, sticky="ew", pady=5)
    nuovo_saldo_entry_corr.insert(0, f"{float(conto_originale['saldo_attuale']):.2f}")

    ttkb.Label(tab_correggi, text="Data Correzione:", anchor=W).grid(row=2, column=0, sticky="ew", pady=5, padx=(0, 10))
    data_correzione_entry_corr = ttkb.DateEntry(tab_correggi, bootstyle=PRIMARY, dateformat="%Y-%m-%d", firstweekday=0)
    data_correzione_entry_corr.grid(row=2, column=1, sticky="ew", pady=5)

    tab_correggi.columnconfigure(1, weight=1)

    def on_applica_correzione_saldo():
        nuovo_saldo_str = nuovo_saldo_entry_corr.get()
        data_corr_str_ui = data_correzione_entry_corr.entry.get()
        try:
            services.correggi_saldo_manuale(id_conto_selezionato, nuovo_saldo_str,
                                            data_correzione_input=data_corr_str_ui)
            toast = ToastNotification(
                title="Correzione Saldo",
                message="Saldo corretto e transazione di correzione registrata.",
                duration=3000,
                bootstyle=SUCCESS,
                alert=True,
                position=(20, 20, 'se')
            )
            toast.show_toast()
            # Aggiorna il saldo visualizzato nella scheda e il titolo del dialogo se necessario
            conto_aggiornato_post_corr = services.ottieni_conto_per_id(id_conto_selezionato)
            if conto_aggiornato_post_corr:
                global conto_originale_ref  # Se necessario
                conto_originale.update(conto_aggiornato_post_corr)  # Aggiorna il dizionario locale
                lbl_saldo_attuale_corr.config(
                    text=f"{float(conto_originale['saldo_attuale']):.2f} {conto_originale.get('valuta', 'EUR')}")
                nuovo_saldo_entry_corr.delete(0, END)
                nuovo_saldo_entry_corr.insert(0, f"{float(conto_originale['saldo_attuale']):.2f}")
                dialog.title(
                    f"⚙️ Gestisci Conto: {conto_originale['nome_conto']}")  # Ricarica il titolo con i dati aggiornati
            callback_refresh()  # Aggiorna la vista principale
        except ValueError as ve:
            Messagebox.show_warning(str(ve), "Dati Non Validi", parent=dialog, alert=True)
        except Exception as e:
            Messagebox.show_error(f"Errore imprevisto:\n{e}", "Errore Correzione Saldo", parent=dialog, alert=True)

    btn_applica_correzione = ttkb.Button(tab_correggi, text="Applica Correzione", command=on_applica_correzione_saldo,
                                         bootstyle=(SUCCESS, OUTLINE))
    btn_applica_correzione.grid(row=3, column=1, sticky="e", pady=(15, 0))

    # --- Pulsante Chiudi Dialogo ---
    # Messo fuori dal notebook, in fondo al dialogo principale
    action_frame_dialog = ttkb.Frame(dialog, padding=(0, 10, 0, 0))
    action_frame_dialog.pack(fill=X, side=BOTTOM, padx=15, pady=(0, 10))

    # Pulsante "Elimina Conto" (pericoloso, da usare con cautela)
    def on_elimina_conto_gestisci():
        if Messagebox.yesno(
                f"Sei sicuro di voler eliminare il conto '{conto_originale['nome_conto']}'?\nQuesta operazione è irreversibile e potrebbe fallire se ci sono transazioni associate.",
                "Conferma Eliminazione Conto", parent=dialog, alert=True) == "Yes":
            try:
                services.elimina_definitivamente_conto(id_conto_selezionato)
                toast = ToastNotification(
                    title="Conto Eliminato",
                    message=f"Il conto '{conto_originale['nome_conto']}' è stato eliminato.",
                    duration=3000, bootstyle=INFO, alert=True, position=(20, 20, 'se'))
                toast.show_toast()
                dialog.destroy()  # Chiudi il dialogo GESTISCI dopo l'eliminazione del conto
                callback_refresh()
            except Exception as e:
                Messagebox.show_error(f"Impossibile eliminare il conto:\n{e}", "Errore Eliminazione", parent=dialog,
                                      alert=True)

    btn_elimina_conto = ttkb.Button(action_frame_dialog, text="🗑️ Elimina Conto", command=on_elimina_conto_gestisci,
                                    bootstyle=DANGER)
    btn_elimina_conto.pack(side=LEFT, padx=(0, 5))

    btn_chiudi_dialog = ttkb.Button(action_frame_dialog, text="Chiudi", command=dialog.destroy, bootstyle=SECONDARY)
    btn_chiudi_dialog.pack(side=RIGHT)

    dialog.bind('<Escape>', lambda event: dialog.destroy())
    # Non c'è un'azione di "Invio" globale qui perché dipende dalla scheda attiva

    dialog.update_idletasks()
    # ... (codice centratura dialogo) ...
    parent_x = app_root_param.winfo_x();
    parent_y = app_root_param.winfo_y()
    parent_width = app_root_param.winfo_width();
    parent_height = app_root_param.winfo_height()
    dialog_width = dialog.winfo_width();
    dialog_height = dialog.winfo_height()
    x_pos = parent_x + (parent_width // 2) - (dialog_width // 2);
    y_pos = parent_y + (parent_height // 2) - (dialog_height // 2)
    dialog.geometry(f"+{x_pos}+{y_pos}")
    dialog.after(50, dialog.lift)
    dialog.after(100, nome_conto_entry_gest.focus_force)


def apri_dialog_nuova_transazione(app_root_param, callback_refresh):
    dialog = ttkb.Toplevel(master=app_root_param, title="➕ Nuova Transazione")
    # Aumenta un po' le dimensioni per farci stare tutti i campi
    dialog.geometry("550x460")  # Regola se necessario
    dialog.transient(app_root_param)
    dialog.grab_set()
    dialog.resizable(False, False)

    main_form_frame = ttkb.Frame(dialog, padding=20)
    main_form_frame.pack(fill=BOTH, expand=True)

    # --- Variabili Tkinter ---
    tipo_trans_var = tk.StringVar(value="Entrata")  # Default
    data_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))  # Solo data per DateEntry
    conto_var = tk.StringVar()
    conto_dest_var = tk.StringVar()  # Per giroconto
    categoria_var = tk.StringVar()
    importo_var = tk.StringVar(value="0.00")
    descrizione_var = tk.StringVar()

    # Futuro: tags_var = tk.StringVar()

    # --- Funzioni Helper Interne al Dialogo ---
    def aggiorna_visibilita_campi(*args):
        tipo_selezionato = tipo_trans_var.get()
        if tipo_selezionato == "Giroconto":
            # Mostra conto destinazione, nascondi categoria standard
            lbl_conto_origine.config(text="Conto Origine:")
            lbl_categoria.grid_remove()
            entry_categoria.grid_remove()
            lbl_conto_dest.grid()
            combo_conto_dest.grid()
        else:
            # Mostra categoria standard, nascondi conto destinazione
            lbl_conto_origine.config(text="Conto:")
            lbl_conto_dest.grid_remove()
            combo_conto_dest.grid_remove()
            lbl_categoria.grid()
            entry_categoria.grid()  # O un Combobox per categorie se le gestisci

        # Aggiorna etichetta importo per chiarezza
        if tipo_selezionato == "Uscita":
            lbl_importo.config(text="Importo (Uscita):")
        elif tipo_selezionato == "Entrata":
            lbl_importo.config(text="Importo (Entrata):")
        else:  # Giroconto
            lbl_importo.config(text="Importo Giroconto:")

    def on_conferma_nuova_transazione():
        tipo = tipo_trans_var.get()
        data_str_ui = data_entry.entry.get()  # Prende dalla DateEntry
        conto_sel = conto_var.get()
        descrizione_sel = descrizione_var.get()
        importo_str_sel = importo_var.get()

        try:
            # Validazione base UI (quella più approfondita è nel servizio)
            if not data_str_ui: raise ValueError("Data mancante.")
            datetime.strptime(data_str_ui, "%Y-%m-%d")  # Valida formato data UI

            if not conto_sel: raise ValueError("Conto mancante.")
            if not importo_str_sel: raise ValueError("Importo mancante.")
            float(importo_str_sel)  # Valida che sia un numero

            if tipo == "Giroconto":
                conto_dest_sel = conto_dest_var.get()
                categoria_sel = "Giroconto"  # Fissa per giroconti
                if not conto_dest_sel: raise ValueError("Conto destinazione mancante.")
                if conto_sel == conto_dest_sel: raise ValueError("I conti di un giroconto devono essere diversi.")

                services.esegui_giroconto(
                    services.ottieni_conto_per_nome(conto_sel)['id_conto'],  # Passa ID
                    services.ottieni_conto_per_nome(conto_dest_sel)['id_conto'],  # Passa ID
                    importo_str_sel,
                    descrizione_sel if descrizione_sel else "Giroconto",  # Default descrizione
                    data_str_ui  # Il servizio gestirà l'ora
                )
            else:  # Entrata o Uscita
                categoria_sel = categoria_var.get()
                if not categoria_sel: raise ValueError("Categoria mancante.")

                importo_effettivo_str = importo_str_sel
                if tipo == "Uscita":
                    # Assicura che l'importo sia negativo o rendilo negativo
                    if float(importo_str_sel) > 0:
                        importo_effettivo_str = str(-float(importo_str_sel))

                services.registra_nuova_transazione(
                    services.ottieni_conto_per_nome(conto_sel)['id_conto'],  # Passa ID
                    importo_effettivo_str,
                    categoria_sel,
                    descrizione_sel,
                    data_transazione_input=data_str_ui  # Il servizio gestirà l'ora
                    # tags_str=tags_var.get() # Per il futuro
                )

            # Non serve popup di successo qui, l'utente vede l'aggiornamento
            dialog.destroy()
            callback_refresh()

        except ValueError as ve:
            Messagebox.show_warning(str(ve), "Dati Non Validi", parent=dialog)
            if dialog.winfo_exists():  # Assicurati che il dialogo esista ancora
                nome_conto_entry.focus_set()
        except Exception as e:
            Messagebox.show_error(f"Errore imprevisto:\n{e}", "Errore Transazione", parent=dialog)
            print(f"Dettaglio errore nuova transazione: {type(e).__name__}: {e}")
            if dialog.winfo_exists():
                print(f"Dettaglio errore nuova transazione: {type(e).__name__}: {e}")

    # --- Layout del Form ---
    row_idx = 0

    # Tipo Transazione
    ttkb.Label(main_form_frame, text="Tipo Transazione:", anchor=W).grid(row=row_idx, column=0, sticky="ew", pady=2)
    tipo_frame = ttkb.Frame(main_form_frame)
    tipo_frame.grid(row=row_idx, column=1, sticky="ew", pady=2)
    row_idx += 1
    opzioni_tipo = ["Entrata", "Uscita", "Giroconto"]
    for i, opzione in enumerate(opzioni_tipo):
        rb = ttkb.Radiobutton(tipo_frame, text=opzione, variable=tipo_trans_var, value=opzione,
                              bootstyle="primary-toolbutton")
        rb.pack(side=LEFT, padx=(0, 5), fill=X, expand=True)
    tipo_trans_var.trace_add("write", aggiorna_visibilita_campi)  # Aggiorna UI al cambio

    # Data
    ttkb.Label(main_form_frame, text="Data:", anchor=W).grid(row=row_idx, column=0, sticky="ew", pady=2)
    data_entry = ttkb.DateEntry(main_form_frame, bootstyle=PRIMARY, dateformat="%Y-%m-%d", firstweekday=0)
    data_entry.entry.config(textvariable=data_var)  # Collega a data_var per impostare il default
    data_entry.grid(row=row_idx, column=1, sticky="ew", pady=2)
    row_idx += 1

    # Lista dei nomi dei conti per i Combobox
    try:
        nomi_conti_attivi = [c['nome_conto'] for c in services.ottieni_tutti_i_conti(solo_attivi=True)]
        if not nomi_conti_attivi:
            Messagebox.show_warning("Nessun Conto",
                                    "Non ci sono conti attivi. Creane uno prima di aggiungere transazioni.",
                                    parent=dialog)
            # Potresti disabilitare il form o chiudere il dialogo
            # dialog.after(100, dialog.destroy) # Chiude dopo un breve ritardo
            # return # Esce dalla funzione se non ci sono conti
    except Exception as e_conti:
        Messagebox.show_error(f"Errore caricamento conti: {e_conti}", parent=dialog)
        nomi_conti_attivi = ["Errore Caricamento Conti"]
        # dialog.after(100, dialog.destroy)
        # return

    # Conto (o Conto Origine)
    lbl_conto_origine = ttkb.Label(main_form_frame, text="Conto:", anchor=W)
    lbl_conto_origine.grid(row=row_idx, column=0, sticky="ew", pady=2)
    combo_conto = ttkb.Combobox(main_form_frame, textvariable=conto_var, values=nomi_conti_attivi, bootstyle=PRIMARY,
                                state="readonly")
    if nomi_conti_attivi and nomi_conti_attivi[0] != "Errore Caricamento Conti": conto_var.set(
        nomi_conti_attivi[0])  # Seleziona il primo
    combo_conto.grid(row=row_idx, column=1, sticky="ew", pady=2)
    row_idx += 1

    # Categoria (per Entrata/Uscita)
    lbl_categoria = ttkb.Label(main_form_frame, text="Categoria:", anchor=W)
    lbl_categoria.grid(row=row_idx, column=0, sticky="ew", pady=2)
    entry_categoria = ttkb.Entry(main_form_frame, textvariable=categoria_var, bootstyle=PRIMARY)
    entry_categoria.grid(row=row_idx, column=1, sticky="ew", pady=2)
    # entry_categoria.focus_set() # Focus dopo conto

    # Conto Destinazione (per Giroconto) - inizialmente nascosto
    lbl_conto_dest = ttkb.Label(main_form_frame, text="Conto Destinazione:", anchor=W)
    # Non fare .grid() subito, aggiorna_visibilita_campi lo gestirà
    combo_conto_dest = ttkb.Combobox(main_form_frame, textvariable=conto_dest_var, values=nomi_conti_attivi,
                                     bootstyle=PRIMARY, state="readonly")
    if len(nomi_conti_attivi) > 1 and nomi_conti_attivi[0] != "Errore Caricamento Conti":
        conto_dest_var.set(nomi_conti_attivi[1])  # Seleziona il secondo se esiste
    elif nomi_conti_attivi and nomi_conti_attivi[0] != "Errore Caricamento Conti":
        conto_dest_var.set(nomi_conti_attivi[0])

    # Importo
    lbl_importo = ttkb.Label(main_form_frame, text="Importo:", anchor=W)
    lbl_importo.grid(row=row_idx + 1, column=0, sticky="ew", pady=2)  # row_idx incrementato dopo categoria/conto_dest
    entry_importo = ttkb.Entry(main_form_frame, textvariable=importo_var, bootstyle=PRIMARY)
    entry_importo.grid(row=row_idx + 1, column=1, sticky="ew", pady=2)

    # Descrizione
    ttkb.Label(main_form_frame, text="Descrizione (Opzionale):", anchor=W).grid(row=row_idx + 2, column=0, sticky="ew",
                                                                                pady=2)
    entry_descrizione = ttkb.Entry(main_form_frame, textvariable=descrizione_var, bootstyle=PRIMARY)
    entry_descrizione.grid(row=row_idx + 2, column=1, sticky="ew", pady=2)

    # Configura espansione colonna 1
    main_form_frame.columnconfigure(1, weight=1)

    # Chiamata iniziale per impostare la visibilità corretta dei campi
    aggiorna_visibilita_campi()

    # --- Pulsanti di Azione ---
    action_frame = ttkb.Frame(dialog, padding=(0, 15, 0, 0))
    action_frame.pack(fill=X, side=BOTTOM, padx=20, pady=(15, 10))

    btn_conferma = ttkb.Button(action_frame, text="💾 Registra Transazione", command=on_conferma_nuova_transazione,
                               bootstyle=SUCCESS)
    btn_conferma.pack(side=RIGHT, padx=(5, 0))

    btn_annulla = ttkb.Button(action_frame, text="❌ Annulla", command=dialog.destroy, bootstyle=LIGHT)
    btn_annulla.pack(side=RIGHT)

    dialog.bind('<Return>', lambda event: on_conferma_nuova_transazione())
    dialog.bind('<Escape>', lambda event: dialog.destroy())

    dialog.update_idletasks()
    parent_x = app_root_param.winfo_x();
    parent_y = app_root_param.winfo_y()
    parent_width = app_root_param.winfo_width();
    parent_height = app_root_param.winfo_height()
    dialog_width = dialog.winfo_width();
    dialog_height = dialog.winfo_height()
    x_pos = parent_x + (parent_width // 2) - (dialog_width // 2)
    y_pos = parent_y + (parent_height // 2) - (dialog_height // 2)
    dialog.geometry(f"+{x_pos}+{y_pos}")

    dialog.after(50, dialog.lift)
    # dialog.after(100, entry_categoria.focus_force) # O un altro campo a seconda del tipo default
    if tipo_trans_var.get() == "Giroconto":
        dialog.after(100, combo_conto_dest.focus_force)
    else:
        dialog.after(100, entry_categoria.focus_force)


def apri_dialog_nuovo_conto(app_root_param, callback_refresh):
    dialog = ttkb.Toplevel(master=app_root_param, title="➕ Nuovo Conto")
    dialog.geometry("400x300")  # Regola dimensioni se necessario
    dialog.transient(app_root_param)  # Imposta come "figlia" della finestra principale
    dialog.grab_set()  # Rende la finestra modale
    dialog.resizable(False, False)

    form_frame = ttkb.Frame(dialog, padding=20)
    form_frame.pack(fill=BOTH, expand=True)

    # --- Campi del Form ---
    # Nome Conto
    ttkb.Label(form_frame, text="Nome Conto:", anchor=W).grid(row=0, column=0, sticky="ew", pady=(0, 5))
    nome_conto_entry = ttkb.Entry(form_frame, bootstyle=PRIMARY)
    nome_conto_entry.grid(row=0, column=1, sticky="ew", pady=(0, 5))
    nome_conto_entry.focus_set()  # Focus iniziale

    # Saldo Iniziale
    ttkb.Label(form_frame, text="Saldo Iniziale:", anchor=W).grid(row=1, column=0, sticky="ew", pady=5)
    saldo_entry = ttkb.Entry(form_frame, bootstyle=PRIMARY)
    saldo_entry.grid(row=1, column=1, sticky="ew", pady=5)
    saldo_entry.insert(0, "0.00")  # Valore di default

    # Tipo Conto (Opzionale - Combobox)
    tipi_conto_comuni = ["Bancario", "Carta di Credito", "Contanti", "Risparmio", "Investimento", "Altro"]
    ttkb.Label(form_frame, text="Tipo Conto (Opzionale):", anchor=W).grid(row=2, column=0, sticky="ew", pady=5)
    tipo_conto_combo = ttkb.Combobox(form_frame, values=tipi_conto_comuni, bootstyle=PRIMARY)
    tipo_conto_combo.grid(row=2, column=1, sticky="ew", pady=5)
    tipo_conto_combo.set("Bancario")  # Valore di default

    # Valuta (Opzionale - per ora fisso o Entry semplice)
    ttkb.Label(form_frame, text="Valuta:", anchor=W).grid(row=3, column=0, sticky="ew", pady=5)
    valuta_entry = ttkb.Entry(form_frame, bootstyle=PRIMARY)
    valuta_entry.grid(row=3, column=1, sticky="ew", pady=5)
    valuta_entry.insert(0, "EUR")  # Default

    # Configura espansione colonne nel form_frame
    form_frame.columnconfigure(1, weight=1)

    # --- Funzione di Conferma ---
    def on_conferma_nuovo_conto():
        nome = nome_conto_entry.get()
        saldo_str = saldo_entry.get()
        tipo = tipo_conto_combo.get()
        valuta = valuta_entry.get()

        try:
            # Chiamata al servizio per creare il conto
            services.crea_nuovo_conto(nome, saldo_str, tipo, valuta)
            # Messagebox.show_info("Conto Creato", f"Il conto '{nome}' è stato creato con successo.", parent=dialog)
            dialog.destroy()
            callback_refresh()  # Aggiorna la vista principale
        except ValueError as ve:  # Errori di validazione dal servizio
            Messagebox.show_warning(str(ve), "Dati Non Validi", parent=dialog)
            nome_conto_entry.focus_set()  # Rimetti focus sul primo campo problematico
        except Exception as e:  # Altri errori (es. DB)
            Messagebox.show_error(f"Errore imprevisto:\n{e}", "Errore Creazione Conto", parent=dialog)
            print(f"Dettaglio errore creazione conto: {type(e).__name__}: {e}")

    # --- Pulsanti di Azione ---
    action_frame = ttkb.Frame(dialog, padding=(0, 10, 0, 0))  # Padding solo sopra
    action_frame.pack(fill=X, side=BOTTOM, padx=20, pady=10)

    btn_conferma = ttkb.Button(action_frame, text="💾 Salva Conto", command=on_conferma_nuovo_conto, bootstyle=SUCCESS)
    btn_conferma.pack(side=RIGHT, padx=(5, 0))

    btn_annulla = ttkb.Button(action_frame, text="❌ Annulla", command=dialog.destroy, bootstyle=LIGHT)
    btn_annulla.pack(side=RIGHT)

    dialog.bind('<Return>', lambda event: on_conferma_nuovo_conto())  # Invio per confermare
    dialog.bind('<Escape>', lambda event: dialog.destroy())  # Escape per chiudere

    # Centra il dialogo rispetto alla finestra principale
    dialog.update_idletasks()  # Necessario per ottenere le dimensioni corrette
    parent_x = app_root_param.winfo_x()
    parent_y = app_root_param.winfo_y()
    parent_width = app_root_param.winfo_width()
    parent_height = app_root_param.winfo_height()
    dialog_width = dialog.winfo_width()
    dialog_height = dialog.winfo_height()
    x_pos = parent_x + (parent_width // 2) - (dialog_width // 2)
    y_pos = parent_y + (parent_height // 2) - (dialog_height // 2)
    dialog.geometry(f"+{x_pos}+{y_pos}")

    dialog.after(50, dialog.lift)  # Assicura che sia in primo piano
    dialog.after(100, nome_conto_entry.focus_force)  # Forza il focus


def apri_dialog_modifica_transazione(app_root_param, callback_refresh):
    if not trans_tree or not trans_tree.selection():
        Messagebox.show_info("Nessuna Selezione", "Seleziona una transazione da modificare.", parent=app_root_param)
        return

    selected_item_id_str = trans_tree.selection()[0]
    id_trans_da_modificare = int(selected_item_id_str)

    trans_originale = services.ottieni_transazione_singola(id_trans_da_modificare)
    if not trans_originale:
        Messagebox.show_error(f"Transazione ID {id_trans_da_modificare} non trovata.", "Errore", parent=app_root_param)
        callback_refresh()
        return

    dialog = ttkb.Toplevel(master=app_root_param, title="✏️ Modifica Transazione")
    dialog.geometry("520x460")  # Simile a nuova transazione
    dialog.transient(app_root_param)
    dialog.grab_set()
    dialog.resizable(False, False)

    main_form_frame = ttkb.Frame(dialog, padding=20)
    main_form_frame.pack(fill=BOTH, expand=True)

    # --- Variabili Tkinter e pre-popolamento ---
    # Determina il tipo basandosi sull'importo o sul campo tipo_transazione se esiste
    tipo_iniziale = "Entrata"
    importo_iniziale_abs_str = f"{abs(float(trans_originale['importo'])):.2f}"

    if trans_originale.get('tipo_transazione') == "Giroconto_Out" or \
            trans_originale.get('tipo_transazione') == "Giroconto_In" or \
            trans_originale.get('categoria', '').lower() == "giroconto":  # Fallback se tipo_transazione non c'è
        tipo_iniziale = "Giroconto"
    elif float(trans_originale['importo']) < 0:
        tipo_iniziale = "Uscita"

    tipo_trans_var = tk.StringVar(value=tipo_iniziale)

    data_dt_obj = datetime.strptime(trans_originale['data_transazione'], '%Y-%m-%d %H:%M:%S')
    data_var = tk.StringVar(value=data_dt_obj.strftime("%Y-%m-%d"))

    conto_var = tk.StringVar(value=trans_originale['nome_conto'])  # nome_conto è già joinato

    conto_dest_var = tk.StringVar()  # Da popolare se giroconto
    categoria_var = tk.StringVar(value=trans_originale['categoria'])
    importo_var = tk.StringVar(value=importo_iniziale_abs_str)  # Mostra sempre positivo nella UI
    descrizione_var = tk.StringVar(value=trans_originale['descrizione'])

    # Se è un giroconto, dobbiamo trovare il conto di destinazione/origine
    if tipo_iniziale == "Giroconto":
        categoria_var.set("Giroconto")  # La categoria è fissa
        # Trova la transazione collegata per pre-popolare l'altro conto
        id_collegata = trans_originale.get('id_transazione_collegata')
        conto_altro_capo = ""
        if id_collegata:
            trans_collegata = services.ottieni_transazione_singola(id_collegata)
            if trans_collegata: conto_altro_capo = trans_collegata['nome_conto']
        else:  # Prova a dedurlo dalla descrizione se id_collegata non c'è (vecchi dati?)
            desc = trans_originale['descrizione'].lower()
            if "->" in desc:
                conto_altro_capo = desc.split("->")[-1].strip().title()
            elif "<-" in desc:
                conto_altro_capo = desc.split("<-")[-1].strip().title()

        if trans_originale['tipo_transazione'] == "Giroconto_Out":  # Questo era l'origine, l'altro è dest
            conto_dest_var.set(conto_altro_capo if conto_altro_capo else "")
        elif trans_originale['tipo_transazione'] == "Giroconto_In":  # Questo era dest, l'altro è origine
            # In questo caso, il conto_var è il dest, e conto_dest_var è l'origine
            # Per UI, conto_var è sempre origine, conto_dest_var è sempre destinazione
            conto_var.set(conto_altro_capo if conto_altro_capo else "")  # Conto origine
            conto_dest_var.set(trans_originale['nome_conto'])  # Conto destinazione (quello corrente)

    # --- Funzioni Helper Interne al Dialogo (identiche a nuova transazione) ---
    def aggiorna_visibilita_campi_mod(*args):  # Nome leggermente diverso per evitare conflitti se definite globalmente
        tipo_selezionato = tipo_trans_var.get()
        if tipo_selezionato == "Giroconto":
            lbl_conto_origine_mod.config(text="Conto Origine:")
            lbl_categoria_mod.grid_remove();
            entry_categoria_mod.grid_remove()
            lbl_conto_dest_mod.grid();
            combo_conto_dest_mod.grid()
        else:
            lbl_conto_origine_mod.config(text="Conto:")
            lbl_conto_dest_mod.grid_remove();
            combo_conto_dest_mod.grid_remove()
            lbl_categoria_mod.grid();
            entry_categoria_mod.grid()

        if tipo_selezionato == "Uscita":
            lbl_importo_mod.config(text="Importo (Uscita):")
        elif tipo_selezionato == "Entrata":
            lbl_importo_mod.config(text="Importo (Entrata):")
        else:
            lbl_importo_mod.config(text="Importo Giroconto:")

    def on_conferma_modifica_transazione():
        tipo_nuovo = tipo_trans_var.get()
        data_str_ui_nuova = data_entry_mod.entry.get()
        conto_sel_nuovo = conto_var.get()
        descrizione_sel_nuova = descrizione_var.get()
        importo_str_sel_nuovo = importo_var.get()  # Questo è sempre positivo dalla UI

        try:
            if not data_str_ui_nuova: raise ValueError("Data mancante.")
            datetime.strptime(data_str_ui_nuova, "%Y-%m-%d")
            if not conto_sel_nuovo: raise ValueError("Conto mancante.")
            if not importo_str_sel_nuovo: raise ValueError("Importo mancante.")
            importo_ui_float = float(importo_str_sel_nuovo)
            if importo_ui_float <= 0: raise ValueError("L'importo nel campo deve essere positivo.")

            # NOTA: la modifica di un giroconto è complessa.
            # Un giroconto sono DUE transazioni. Modificarne una implica modificare anche l'altra.
            # O, più semplicemente, si elimina il vecchio giroconto e se ne crea uno nuovo.
            # Per ora, se si modifica un giroconto, lo trattiamo come eliminazione del vecchio
            # e creazione di un nuovo giroconto o di transazioni singole.
            # Questo semplifica enormemente la logica.
            if trans_originale.get('categoria', '').lower() == "giroconto" and tipo_nuovo != "Giroconto":
                # L'utente sta trasformando un giroconto in una transazione normale
                if not Messagebox.yesno("Attenzione",
                                        "Stai modificando un giroconto in una transazione singola. La transazione collegata verrà eliminata. Continuare?",
                                        parent=dialog):
                    return
                # Elimina la transazione originale (e la sua collegata se il servizio lo fa)
                services.elimina_transazione_esistente(id_trans_da_modificare)  # Questo deve gestire la collegata
                # Poi registra come nuova transazione singola
                categoria_sel_nuova = categoria_var.get()
                if not categoria_sel_nuova: raise ValueError("Categoria mancante.")
                importo_finale_str = importo_str_sel_nuovo
                if tipo_nuovo == "Uscita": importo_finale_str = str(-importo_ui_float)

                conto_obj_nuovo = services.ottieni_conto_per_nome(conto_sel_nuovo)
                if not conto_obj_nuovo: raise ValueError(f"Conto '{conto_sel_nuovo}' non trovato.")

                services.registra_nuova_transazione(
                    conto_obj_nuovo['id_conto'], importo_finale_str, categoria_sel_nuova,
                    descrizione_sel_nuova, data_transazione_input=data_str_ui_nuova
                )

            elif tipo_nuovo == "Giroconto":
                conto_dest_sel_nuovo = conto_dest_var.get()
                if not conto_dest_sel_nuovo: raise ValueError("Conto destinazione mancante.")
                if conto_sel_nuovo == conto_dest_sel_nuovo: raise ValueError(
                    "I conti di un giroconto devono essere diversi.")

                # Se la transazione originale era un giroconto, la eliminiamo e creiamo un nuovo giroconto
                if trans_originale.get('categoria', '').lower() == "giroconto":
                    services.elimina_transazione_esistente(
                        id_trans_da_modificare)  # Assumiamo che questo gestisca la collegata

                conto_origine_obj = services.ottieni_conto_per_nome(conto_sel_nuovo)
                conto_dest_obj = services.ottieni_conto_per_nome(conto_dest_sel_nuovo)
                if not conto_origine_obj: raise ValueError(f"Conto origine '{conto_sel_nuovo}' non trovato.")
                if not conto_dest_obj: raise ValueError(f"Conto destinazione '{conto_dest_sel_nuovo}' non trovato.")

                services.esegui_giroconto(
                    conto_origine_obj['id_conto'], conto_dest_obj['id_conto'],
                    importo_str_sel_nuovo,  # Importo (sempre positivo dalla UI)
                    descrizione_sel_nuova if descrizione_sel_nuova else "Giroconto",
                    data_giroconto_input=data_str_ui_nuova
                )
            else:  # Modifica di una transazione Entrata/Uscita standard
                categoria_sel_nuova = categoria_var.get()
                if not categoria_sel_nuova: raise ValueError("Categoria mancante.")

                importo_finale_float = importo_ui_float
                if tipo_nuovo == "Uscita": importo_finale_float = -importo_ui_float

                conto_obj_nuovo = services.ottieni_conto_per_nome(conto_sel_nuovo)
                if not conto_obj_nuovo: raise ValueError(f"Conto '{conto_sel_nuovo}' non trovato.")

                services.modifica_transazione_esistente(
                    id_trans_da_modificare,
                    conto_obj_nuovo['id_conto'],
                    str(importo_finale_float),  # Passa stringa come si aspetta il servizio per coerenza
                    categoria_sel_nuova,
                    descrizione_sel_nuova,
                    data_trans_nuova_input=data_str_ui_nuova,
                    # tipo_trans_nuovo=... (il servizio dovrebbe determinarlo o prenderlo)
                )

            dialog.destroy()
            callback_refresh()

        except ValueError as ve:
            if hasattr(dialog, 'bell'): dialog.bell()
            Messagebox.show_warning(str(ve), "Dati Non Validi", parent=dialog)
        except Exception as e:
            if hasattr(dialog, 'bell'): dialog.bell()
            Messagebox.show_error(f"Errore imprevisto:\n{e}", "Errore Modifica Transazione", parent=dialog)
            print(f"Dettaglio errore modifica transazione: {type(e).__name__}: {e}")

    # --- Layout del Form (simile a Nuova Transazione, ma con valori pre-popolati) ---
    row_idx_mod = 0
    ttkb.Label(main_form_frame, text="Tipo Transazione:", anchor=W).grid(row=row_idx_mod, column=0, sticky="ew", pady=2)
    tipo_frame_mod = ttkb.Frame(main_form_frame)
    tipo_frame_mod.grid(row=row_idx_mod, column=1, sticky="ew", pady=2);
    row_idx_mod += 1
    opzioni_tipo_mod = ["Entrata", "Uscita", "Giroconto"]
    for i, opzione in enumerate(opzioni_tipo_mod):
        rb_mod = ttkb.Radiobutton(tipo_frame_mod, text=opzione, variable=tipo_trans_var, value=opzione,
                                  bootstyle="primary-toolbutton")
        rb_mod.pack(side=LEFT, padx=(0, 5), fill=X, expand=True)
    tipo_trans_var.trace_add("write", aggiorna_visibilita_campi_mod)

    ttkb.Label(main_form_frame, text="Data:", anchor=W).grid(row=row_idx_mod, column=0, sticky="ew", pady=2)
    data_entry_mod = ttkb.DateEntry(main_form_frame, bootstyle=PRIMARY, dateformat="%Y-%m-%d", firstweekday=0)
    data_entry_mod.entry.config(textvariable=data_var)  # Usa data_var pre-popolata
    data_entry_mod.grid(row=row_idx_mod, column=1, sticky="ew", pady=2);
    row_idx_mod += 1

    nomi_conti_attivi_mod = [c['nome_conto'] for c in services.ottieni_tutti_i_conti(solo_attivi=True)]
    if not nomi_conti_attivi_mod: nomi_conti_attivi_mod = [
        conto_var.get()]  # Usa il conto originale se non ci sono altri attivi

    lbl_conto_origine_mod = ttkb.Label(main_form_frame, text="Conto:", anchor=W)
    lbl_conto_origine_mod.grid(row=row_idx_mod, column=0, sticky="ew", pady=2)
    combo_conto_mod = ttkb.Combobox(main_form_frame, textvariable=conto_var, values=nomi_conti_attivi_mod,
                                    bootstyle=PRIMARY, state="readonly")
    combo_conto_mod.grid(row=row_idx_mod, column=1, sticky="ew", pady=2);
    row_idx_categoria_mod = row_idx_mod;
    row_idx_mod += 1

    lbl_categoria_mod = ttkb.Label(main_form_frame, text="Categoria:", anchor=W)
    entry_categoria_mod = ttkb.Entry(main_form_frame, textvariable=categoria_var, bootstyle=PRIMARY)

    lbl_conto_dest_mod = ttkb.Label(main_form_frame, text="Conto Destinazione:", anchor=W)
    combo_conto_dest_mod = ttkb.Combobox(main_form_frame, textvariable=conto_dest_var, values=nomi_conti_attivi_mod,
                                         bootstyle=PRIMARY, state="readonly")

    lbl_categoria_mod.grid(row=row_idx_categoria_mod, column=0, sticky="ew", pady=2)
    entry_categoria_mod.grid(row=row_idx_categoria_mod, column=1, sticky="ew", pady=2)
    lbl_conto_dest_mod.grid(row=row_idx_categoria_mod, column=0, sticky="ew", pady=2);
    lbl_conto_dest_mod.grid_remove()
    combo_conto_dest_mod.grid(row=row_idx_categoria_mod, column=1, sticky="ew", pady=2);
    combo_conto_dest_mod.grid_remove()

    lbl_importo_mod = ttkb.Label(main_form_frame, text="Importo:", anchor=W)
    lbl_importo_mod.grid(row=row_idx_mod, column=0, sticky="ew", pady=2)
    entry_importo_mod = ttkb.Entry(main_form_frame, textvariable=importo_var, bootstyle=PRIMARY)
    entry_importo_mod.grid(row=row_idx_mod, column=1, sticky="ew", pady=2);
    row_idx_mod += 1

    ttkb.Label(main_form_frame, text="Descrizione (Opzionale):", anchor=W).grid(row=row_idx_mod, column=0, sticky="ew",
                                                                                pady=2)
    entry_descrizione_mod = ttkb.Entry(main_form_frame, textvariable=descrizione_var, bootstyle=PRIMARY)
    entry_descrizione_mod.grid(row=row_idx_mod, column=1, sticky="ew", pady=2);
    row_idx_mod += 1

    main_form_frame.columnconfigure(1, weight=1)
    aggiorna_visibilita_campi_mod()

    action_frame_mod = ttkb.Frame(dialog, padding=(0, 15, 0, 0))
    action_frame_mod.pack(fill=X, side=BOTTOM, padx=20, pady=(15, 10))
    btn_conferma_mod = ttkb.Button(action_frame_mod, text="💾 Salva Modifiche", command=on_conferma_modifica_transazione,
                                   bootstyle=SUCCESS)
    btn_conferma_mod.pack(side=RIGHT, padx=(5, 0))
    btn_annulla_mod = ttkb.Button(action_frame_mod, text="❌ Annulla", command=dialog.destroy, bootstyle=LIGHT)
    btn_annulla_mod.pack(side=RIGHT)
    dialog.bind('<Return>', lambda event: on_conferma_modifica_transazione())
    dialog.bind('<Escape>', lambda event: dialog.destroy())
    dialog.update_idletasks()
    parent_x = app_root_param.winfo_x();
    parent_y = app_root_param.winfo_y()
    parent_width = app_root_param.winfo_width();
    parent_height = app_root_param.winfo_height()
    dialog_width = dialog.winfo_width();
    dialog_height = dialog.winfo_height()
    x_pos = parent_x + (parent_width // 2) - (dialog_width // 2);
    y_pos = parent_y + (parent_height // 2) - (dialog_height // 2)
    dialog.geometry(f"+{x_pos}+{y_pos}")
    dialog.after(50, dialog.lift)
    # Focus iniziale
    entry_importo_mod.focus_set()
    entry_importo_mod.select_range(0, END)


def elimina_transazione_selezionata(callback_refresh_func): # Passiamo il callback direttamente
    if not trans_tree or not trans_tree.selection():
        Messagebox.show_info("Nessuna Selezione", "Seleziona una transazione da eliminare.", parent=app_state["app_root_ref"])
        return

    selected_item_id_str = trans_tree.selection()[0] # L'iid è l'id_transazione
    id_trans_da_eliminare = int(selected_item_id_str)

    # Recupera qualche dettaglio per il messaggio di conferma
    trans_details = services.ottieni_transazione_singola(id_trans_da_eliminare)
    if not trans_details:
        Messagebox.show_error(f"Transazione ID {id_trans_da_eliminare} non trovata nel database.", "Errore", parent=app_state["app_root_ref"])
        callback_refresh_func() # Ricarica la lista per sicurezza
        return

    msg_confirm = (f"Sei sicuro di voler eliminare la seguente transazione?\n\n"
                   f"Data: {datetime.strptime(trans_details['data_transazione'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')}\n"
                   f"Conto: {trans_details['nome_conto']}\n"
                   f"Descrizione: {trans_details['descrizione']}\n"
                   f"Importo: {trans_details['importo']:.2f} €\n\n"
                   f"Questa operazione è irreversibile.")

    conferma = Messagebox.yesno(msg_confirm, "Conferma Eliminazione", parent=app_state["app_root_ref"])

    if conferma == "Yes": # Messagebox.yesno restituisce stringhe "Yes"/"No"
        try:
            services.elimina_transazione_esistente(id_trans_da_eliminare)
            # Messagebox.show_info("Successo", "Transazione eliminata con successo.", parent=app_state["app_root_ref"]) # Opzionale
            callback_refresh_func()
        except Exception as e:
            Messagebox.show_error(f"Errore durante l'eliminazione:\n{e}", "Errore Eliminazione", parent=app_state["app_root_ref"])
            print(f"Dettaglio errore eliminazione transazione: {type(e).__name__}: {e}")


# Funzione helper per ordinare Treeview
def sort_treeview_column(tv, col, reverse):
    # Estrai i dati e l'iid di ogni riga
    data_list = [(tv.set(k, col), k) for k in tv.get_children('')]

    # Tenta la conversione a float per l'ordinamento numerico, altrimenti ordina come stringa
    try:
        # Per l'importo, rimuovi "€" e spazi, converti in float
        if col == "importo":
            data_list = [
                (float(val.replace("€", "").replace(".", "").replace(",", ".") if isinstance(val, str) else val), k) for
                val, k in data_list]
        elif col == "data":  # Ordina per data effettiva, non stringa formattata
            # Per la data, devi ottenere il valore originale non formattato o riconvertire
            # Questo è un po' più complesso se non salvi la data originale nel treeview item
            # Per ora, ordina la stringa come data se possibile, altrimenti alfanumerico
            def convert_date_for_sort(date_str):
                try:  # Tenta di parsare come DD/MM/YYYY HH:MM
                    return datetime.strptime(date_str, '%d/%m/%Y %H:%M')
                except ValueError:  # Altrimenti, come stringa
                    return date_str

            data_list = [(convert_date_for_sort(val), k) for val, k in data_list]
        else:  # Ordinamento stringa (case-insensitive)
            data_list = [(str(val).lower(), k) for val, k in data_list]

    except ValueError:  # Se la conversione a float fallisce per qualche riga, ordina come stringhe
        data_list.sort(key=lambda t: str(t[0]).lower(), reverse=reverse)
    else:  # Se la conversione ha avuto successo (o era stringa)
        data_list.sort(reverse=reverse)

    # Riordina gli item nel treeview
    for index, (val, k) in enumerate(data_list):
        tv.move(k, '', index)

    # Inverti la direzione per il prossimo click sulla stessa colonna
    tv.heading(col, command=lambda: sort_treeview_column(tv, col, not reverse))


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


def populate_investimenti_tree():
    # Accedi ai widget tramite app_state
    inv_tree_ui = app_state.get("inv_tree_ref")
    lbl_valore_tot_inv_ui = app_state.get("inv_lbl_valore_tot_ref")

    if not inv_tree_ui or not inv_tree_ui.winfo_exists():
        # print("DEBUG populate_investimenti_tree: inv_tree_ref non trovato o distrutto.")
        return

    current_selection = inv_tree_ui.selection()
    for item in inv_tree_ui.get_children():
        inv_tree_ui.delete(item)

    try:
        investimenti_list = services.ottieni_tutti_gli_investimenti(solo_attivi=True)
        if investimenti_list is None: investimenti_list = []

        for inv in investimenti_list:
            pmc_str = f"{float(inv['pmc_unitario']):.2f}" if inv.get('pmc_unitario') is not None else "-"
            val_att_unit_str = f"{float(inv['valore_attuale_unitario']):.2f}" if inv.get(
                'valore_attuale_unitario') is not None else "-"
            val_tot_att_str = f"{float(inv['valore_totale_attuale_calc']):.2f}" if inv.get(
                'valore_totale_attuale_calc') is not None else "-"

            pl_perc_val = inv.get('pl_percentuale_calc')
            pl_perc_str = "-"
            if pl_perc_val == float('inf'):
                pl_perc_str = "N/A (Inf)"  # O un altro indicatore come "+∞%"
            elif pl_perc_val is not None:
                pl_perc_str = f"{float(pl_perc_val):+.2f}%"  # Aggiunto '+' per i positivi

            data_val_att_str = datetime.strptime(inv['data_valore_attuale'], '%Y-%m-%d %H:%M:%S').strftime(
                '%d/%m/%y') if inv.get('data_valore_attuale') else "-"

            tag_colore = ""
            if inv.get('pl_assoluto_calc') is not None:
                if inv['pl_assoluto_calc'] > 0.001:
                    tag_colore = "entrata"  # Piccola tolleranza per float
                elif inv['pl_assoluto_calc'] < -0.001:
                    tag_colore = "uscita"

            inv_tree_ui.insert("", END, iid=inv['id_investimento'], values=(
                inv['nome_strumento'], inv.get('simbolo', '-'), inv['tipo_asset'],
                f"{float(inv['quantita']):.4f}",
                f"{pmc_str} {inv.get('valuta', 'EUR')}",
                f"{val_att_unit_str} {inv.get('valuta', 'EUR')}",
                f"{val_tot_att_str} {inv.get('valuta', 'EUR')}",
                pl_perc_str, data_val_att_str
            ), tags=(tag_colore,))

        if current_selection and len(current_selection) > 0 and inv_tree_ui.exists(current_selection[0]):
            inv_tree_ui.selection_set(current_selection[0])
            inv_tree_ui.focus(current_selection[0])

        # Aggiorna il riepilogo del portafoglio
        if lbl_valore_tot_inv_ui and lbl_valore_tot_inv_ui.winfo_exists():
            valore_complessivo = sum(i.get('valore_totale_attuale_calc', 0.0) for i in investimenti_list if
                                     i.get('valore_totale_attuale_calc') is not None)
            costo_complessivo_attivo = sum(i.get('costo_totale_carico', 0.0) for i in investimenti_list if
                                           i.get('costo_totale_carico') is not None and i.get('quantita',
                                                                                              0) > 0.00001 and i.get(
                                               'attivo'))  # Solo per posizioni attive con quantità

            pl_totale_abs = 0
            pl_perc_str_tot = "N/A"

            if valore_complessivo is not None and costo_complessivo_attivo is not None:
                pl_totale_abs = valore_complessivo - costo_complessivo_attivo
                if costo_complessivo_attivo > 0.001:  # Evita divisione per zero o costi irrisori
                    pl_perc_totale_calc = (pl_totale_abs / costo_complessivo_attivo) * 100
                    pl_perc_str_tot = f"{pl_perc_totale_calc:+.2f}%"
                elif valore_complessivo > 0:  # Costo zero ma valore positivo (es. crypto airdrop)
                    pl_perc_str_tot = "+Inf%"

            lbl_valore_tot_inv_ui.config(
                text=f"Valore Totale Portafoglio Attivo: {valore_complessivo:,.2f} €   |   P/L Totale: {pl_totale_abs:,.2f} € ({pl_perc_str_tot})"
            )

    except Exception as e:
        Messagebox.show_error(f"Errore caricamento investimenti: {e}", "Errore Dati",
                              parent=app_state.get("app_root_ref"))
        print(f"Dettaglio errore populate_investimenti_tree: {type(e).__name__}: {e}")

    update_investimenti_buttons_state()


def update_investimenti_buttons_state(event=None):
    # Accedi ai riferimenti dei bottoni e del treeview da app_state
    inv_tree_ui = app_state.get("inv_tree_ref")

    buttons_to_update = {
        "modifica": app_state.get("inv_btn_modifica_ref"),
        "aggiorna_val": app_state.get("inv_btn_aggiorna_val_ref"),
        "acquista": app_state.get("inv_btn_acquista_ref"),
        "vendi": app_state.get("inv_btn_vendi_ref"),
        "chiudi_pos": app_state.get("inv_btn_chiudi_pos_ref")
    }

    if not inv_tree_ui or not inv_tree_ui.winfo_exists() or not all(buttons_to_update.values()):
        # print("DEBUG update_investimenti_buttons_state: tree o uno o più bottoni non pronti.")
        # Se i bottoni non sono ancora creati, potresti disabilitarli di default
        # e abilitarli qui solo se esistono. Per ora, usciamo se non tutti sono pronti.
        return

    selected_items = inv_tree_ui.selection()
    stato_se_selezionato = NORMAL if selected_items else DISABLED

    for btn_widget in buttons_to_update.values():
        if btn_widget and btn_widget.winfo_exists():  # Controllo aggiuntivo
            btn_widget.config(state=stato_se_selezionato)


def apri_investimenti_view(main_frame, app_root_param):
    # app_state è già globale, non serve ridichiararlo qui
    # Rimuovi le vecchie dichiarazioni 'global inv_tree, btn_inv_modifica, ...'

    app_state["active_view"] = "investimenti"
    navigate_away_from_dashboard()

    for widget in main_frame.winfo_children():
        widget.destroy()

    # --- Header Sezione ---
    header_inv = ttkb.Frame(main_frame, padding=(10, 10))
    header_inv.pack(fill=X)
    ttkb.Label(header_inv, text="Portafoglio Investimenti", font=("Segoe UI", 18, "bold")).pack(side=LEFT, padx=(0, 20))

    btn_nuovo_inv = ttkb.Button(header_inv, text="➕ Nuovo Investimento", bootstyle=SUCCESS,
                                command=lambda: apri_dialog_nuovo_investimento(app_root_param,
                                                                               populate_investimenti_tree))
    btn_nuovo_inv.pack(side=RIGHT)
    ttkb.Separator(main_frame, orient=HORIZONTAL).pack(fill=X, pady=5, padx=10)

    # --- Riepilogo Portafoglio ---
    summary_frame = ttkb.Frame(main_frame, padding=(10, 0, 10, 10))
    summary_frame.pack(fill=X)
    lbl_valore_tot_inv_widget = ttkb.Label(summary_frame, text="Valore Totale Portafoglio: In caricamento...",
                                           font="-weight bold")
    lbl_valore_tot_inv_widget.pack(side=LEFT)
    app_state["inv_lbl_valore_tot_ref"] = lbl_valore_tot_inv_widget  # Salva riferimento in app_state

    # --- Treeview per gli Investimenti ---
    tree_frame = ttkb.Frame(main_frame, padding=(10, 0, 10, 10))
    tree_frame.pack(fill=BOTH, expand=True)

    cols_inv = ("nome", "simbolo", "tipo", "qta", "pmc", "val_att", "val_tot", "pl_perc", "data_val")
    inv_tree_widget = ttk.Treeview(tree_frame, columns=cols_inv, show="headings", height=15, selectmode="browse")
    app_state["inv_tree_ref"] = inv_tree_widget  # Salva riferimento in app_state

    # Configurazione headings e columns (usa app_state["inv_tree_ref"] o una var locale inv_tree_ui)
    inv_tree_ui = app_state["inv_tree_ref"]  # Per comodità
    inv_tree_ui.heading("nome", text="Nome Strumento", command=lambda: sort_treeview_column(inv_tree_ui, "nome", False))
    # ... (configura tutti gli altri headings e columns usando inv_tree_ui) ...
    inv_tree_ui.heading("simbolo", text="Simbolo", command=lambda: sort_treeview_column(inv_tree_ui, "simbolo", False))
    inv_tree_ui.heading("tipo", text="Tipo Asset", command=lambda: sort_treeview_column(inv_tree_ui, "tipo", False))
    inv_tree_ui.heading("qta", text="Quantità", anchor=E,
                        command=lambda: sort_treeview_column(inv_tree_ui, "qta", True))
    inv_tree_ui.heading("pmc", text="PMC Un.", anchor=E, command=lambda: sort_treeview_column(inv_tree_ui, "pmc", True))
    inv_tree_ui.heading("val_att", text="Val. Att. Un.", anchor=E,
                        command=lambda: sort_treeview_column(inv_tree_ui, "val_att", True))
    inv_tree_ui.heading("val_tot", text="Val. Totale", anchor=E,
                        command=lambda: sort_treeview_column(inv_tree_ui, "val_tot", True))
    inv_tree_ui.heading("pl_perc", text="P/L %", anchor=E,
                        command=lambda: sort_treeview_column(inv_tree_ui, "pl_perc", True))
    inv_tree_ui.heading("data_val", text="Agg. Val.", anchor=CENTER,
                        command=lambda: sort_treeview_column(inv_tree_ui, "data_val", False))

    inv_tree_ui.column("nome", width=200, stretch=True, minwidth=150)
    inv_tree_ui.column("simbolo", width=80, stretch=False, minwidth=60, anchor=CENTER)
    inv_tree_ui.column("tipo", width=120, stretch=False, minwidth=100)
    inv_tree_ui.column("qta", width=100, stretch=False, anchor=E, minwidth=80)
    inv_tree_ui.column("pmc", width=100, stretch=False, anchor=E, minwidth=80)
    inv_tree_ui.column("val_att", width=100, stretch=False, anchor=E, minwidth=80)
    inv_tree_ui.column("val_tot", width=120, stretch=False, anchor=E, minwidth=100)
    inv_tree_ui.column("pl_perc", width=80, stretch=False, anchor=E, minwidth=70)
    inv_tree_ui.column("data_val", width=100, stretch=False, anchor=CENTER, minwidth=80)

    inv_tree_ui.tag_configure("entrata", foreground=app_root_param.style.colors.success if hasattr(app_root_param.style,
                                                                                                   'colors') else 'green')
    inv_tree_ui.tag_configure("uscita", foreground=app_root_param.style.colors.danger if hasattr(app_root_param.style,
                                                                                                 'colors') else 'red')

    inv_tree_scroll_y = ttkb.Scrollbar(tree_frame, orient=VERTICAL, command=inv_tree_ui.yview,
                                       bootstyle="round-primary")
    inv_tree_ui.configure(yscrollcommand=inv_tree_scroll_y.set)
    inv_tree_scroll_x = ttkb.Scrollbar(tree_frame, orient=HORIZONTAL, command=inv_tree_ui.xview,
                                       bootstyle="round-primary")
    inv_tree_ui.configure(xscrollcommand=inv_tree_scroll_x.set)

    inv_tree_scroll_y.pack(side=RIGHT, fill=Y)
    inv_tree_scroll_x.pack(side=BOTTOM, fill=X)
    inv_tree_ui.pack(side=LEFT, fill=BOTH, expand=True)

    # --- Frame Pulsanti Azione per Riga Selezionata ---
    action_buttons_frame_inv = ttkb.Frame(main_frame, padding=(10, 10))
    action_buttons_frame_inv.pack(fill=X)

    btn_inv_modifica_widget = ttkb.Button(action_buttons_frame_inv, text="✏️ Modifica Dati", bootstyle=(INFO, OUTLINE),
                                          state=DISABLED,
                                          command=lambda: apri_dialog_modifica_investimento(app_root_param,
                                                                                            populate_investimenti_tree))
    app_state["inv_btn_modifica_ref"] = btn_inv_modifica_widget  # SALVA IN APP_STATE
    app_state["inv_btn_modifica_ref"].pack(side=LEFT, padx=3)

    btn_inv_aggiorna_val_widget = ttkb.Button(action_buttons_frame_inv, text="🔄 Aggiorna Valore",
                                              bootstyle=(PRIMARY, OUTLINE), state=DISABLED,
                                              command=lambda: apri_dialog_aggiorna_valore_investimento(app_root_param,
                                                                                                       populate_investimenti_tree))
    app_state["inv_btn_aggiorna_val_ref"] = btn_inv_aggiorna_val_widget  # SALVA IN APP_STATE
    app_state["inv_btn_aggiorna_val_ref"].pack(side=LEFT, padx=3)

    btn_inv_acquista_widget = ttkb.Button(action_buttons_frame_inv, text="➕ Acquista Altro",
                                          bootstyle=(SUCCESS, OUTLINE), state=DISABLED,
                                          command=lambda: apri_dialog_acquista_altro(app_root_param,
                                                                                     populate_investimenti_tree))
    app_state["inv_btn_acquista_ref"] = btn_inv_acquista_widget  # SALVA IN APP_STATE
    app_state["inv_btn_acquista_ref"].pack(side=LEFT, padx=3)

    btn_inv_vendi_widget = ttkb.Button(action_buttons_frame_inv, text="💰 Vendi", bootstyle=(WARNING, OUTLINE),
                                       state=DISABLED,
                                       command=lambda: apri_dialog_vendi_investimento(app_root_param,
                                                                                      populate_investimenti_tree))
    app_state["inv_btn_vendi_ref"] = btn_inv_vendi_widget  # SALVA IN APP_STATE
    app_state["inv_btn_vendi_ref"].pack(side=LEFT, padx=3)

    btn_inv_chiudi_pos_widget = ttkb.Button(action_buttons_frame_inv, text="❌ Chiudi Posizione",
                                            bootstyle=(DANGER, OUTLINE), state=DISABLED,
                                            command=lambda: chiudi_posizione_investimento_selezionato(app_root_param,
                                                                                                      populate_investimenti_tree))
    app_state["inv_btn_chiudi_pos_ref"] = btn_inv_chiudi_pos_widget  # SALVA IN APP_STATE
    app_state["inv_btn_chiudi_pos_ref"].pack(side=LEFT, padx=3)

    app_state["inv_tree_ref"].bind("<<TreeviewSelect>>",
                                   update_investimenti_buttons_state)  # Usa il riferimento da app_state

    populate_investimenti_tree()
    # update_investimenti_buttons_state() # Già chiamato da populate_investimenti_tree alla fine


def apri_dialog_nuovo_investimento(app_root_param, callback_refresh):
    dialog = ttkb.Toplevel(master=app_root_param, title="➕ Nuovo Investimento")
    dialog.geometry("620x550")
    dialog.transient(app_root_param)
    dialog.grab_set()
    dialog.resizable(False, False)  # Finestra non resizable

    # Frame principale per tutti i contenuti del dialogo
    main_dialog_frame = ttkb.Frame(dialog, padding=20)  # Padding generale per il dialogo
    main_dialog_frame.pack(fill=BOTH, expand=True)

    # Frame per i campi del form (questo non sarà più lo sf.container)
    form_frame = ttkb.Frame(main_dialog_frame)
    form_frame.pack(fill=BOTH, expand=True, pady=(0, 15))  # pady per separarlo dai bottoni sotto

    # Variabili Tkinter
    nome_var = tk.StringVar()
    simbolo_var = tk.StringVar()
    tipo_asset_var = tk.StringVar()
    quantita_var = tk.StringVar(value="0.0")
    pmc_unitario_var = tk.StringVar()
    costo_totale_carico_var = tk.StringVar()
    valuta_var = tk.StringVar(value="EUR")
    data_primo_acquisto_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
    conto_detenzione_var = tk.StringVar()
    # note_var non serve per Text widget, si usa .get("1.0", "end-1c")

    # Layout del Form
    row_idx = 0
    pady_val = (6, 2)  # Riduciamo un po' il padding verticale per far stare più cose
    label_width = 20  # Larghezza fissa per i Label per allineamento (opzionale)

    # Nome Strumento
    ttkb.Label(form_frame, text="Nome Strumento:", anchor=W, width=label_width).grid(row=row_idx, column=0, sticky="w",
                                                                                     pady=pady_val, padx=(0, 10))
    nome_entry = ttkb.Entry(form_frame, textvariable=nome_var, bootstyle=PRIMARY)
    nome_entry.grid(row=row_idx, column=1, columnspan=3, sticky="ew", pady=pady_val);
    row_idx += 1
    nome_entry.focus_set()

    # Simbolo/Ticker
    ttkb.Label(form_frame, text="Simbolo/Ticker (Opz.):", anchor=W, width=label_width).grid(row=row_idx, column=0,
                                                                                            sticky="w", pady=pady_val,
                                                                                            padx=(0, 10))
    simbolo_entry = ttkb.Entry(form_frame, textvariable=simbolo_var, bootstyle=PRIMARY)
    simbolo_entry.grid(row=row_idx, column=1, columnspan=3, sticky="ew", pady=pady_val);
    row_idx += 1

    # Tipo Asset
    tipi_asset_comuni = sorted(
        ["Azione", "ETF", "Obbligazione", "Fondo Comune", "Criptovaluta", "Immobiliare", "Materia Prima", "Altro"])
    ttkb.Label(form_frame, text="Tipo Asset:", anchor=W, width=label_width).grid(row=row_idx, column=0, sticky="w",
                                                                                 pady=pady_val, padx=(0, 10))
    tipo_asset_combo = ttkb.Combobox(form_frame, textvariable=tipo_asset_var, values=tipi_asset_comuni,
                                     bootstyle=PRIMARY, state="readonly")
    tipo_asset_combo.grid(row=row_idx, column=1, columnspan=3, sticky="ew", pady=pady_val);
    row_idx += 1
    if tipi_asset_comuni: tipo_asset_var.set("Azione")

    # Quantità e Valuta
    ttkb.Label(form_frame, text="Quantità:", anchor=W, width=label_width).grid(row=row_idx, column=0, sticky="w",
                                                                               pady=pady_val, padx=(0, 10))
    quantita_entry = ttkb.Entry(form_frame, textvariable=quantita_var, bootstyle=PRIMARY)
    quantita_entry.grid(row=row_idx, column=1, sticky="ew", pady=pady_val)
    ttkb.Label(form_frame, text="Valuta:", anchor=W).grid(row=row_idx, column=2, sticky="e", pady=pady_val,
                                                          padx=(5, 5))  # sticky 'e'
    valuta_entry = ttkb.Entry(form_frame, textvariable=valuta_var, bootstyle=PRIMARY, width=8)
    valuta_entry.grid(row=row_idx, column=3, sticky="w", pady=pady_val);
    row_idx += 1

    # PMC Unitario
    ttkb.Label(form_frame, text="PMC Unitario:", anchor=W, width=label_width).grid(row=row_idx, column=0, sticky="w",
                                                                                   pady=pady_val, padx=(0, 10))
    pmc_entry = ttkb.Entry(form_frame, textvariable=pmc_unitario_var, bootstyle=PRIMARY)
    pmc_entry.grid(row=row_idx, column=1, columnspan=3, sticky="ew", pady=pady_val);
    row_idx += 1

    # Costo Totale di Carico
    ttkb.Label(form_frame, text="Costo Tot. Carico (Opz.):", anchor=W, width=label_width).grid(row=row_idx, column=0,
                                                                                               sticky="w",
                                                                                               pady=pady_val,
                                                                                               padx=(0, 10))
    costo_entry = ttkb.Entry(form_frame, textvariable=costo_totale_carico_var, bootstyle=PRIMARY)
    costo_entry.grid(row=row_idx, column=1, columnspan=3, sticky="ew", pady=pady_val)
    ttkb.Label(form_frame, text="(Se inserito, sovrascrive PMC * Q.tà)", font="-size 8", bootstyle=SECONDARY).grid(
        row=row_idx + 1, column=1, columnspan=3, sticky="w", pady=(0, pady_val[0]));
    row_idx += 2  # Incrementa di 2 per il label piccolo

    # Data Primo Acquisto
    ttkb.Label(form_frame, text="Data Primo Acquisto:", anchor=W, width=label_width).grid(row=row_idx, column=0,
                                                                                          sticky="w", pady=pady_val,
                                                                                          padx=(0, 10))
    data_acq_entry = ttkb.DateEntry(form_frame, bootstyle=PRIMARY, dateformat="%Y-%m-%d", firstweekday=0)
    data_acq_entry.entry.config(textvariable=data_primo_acquisto_var)
    data_acq_entry.grid(row=row_idx, column=1, columnspan=3, sticky="ew", pady=pady_val);
    row_idx += 1

    # Conto di Detenzione/Pagamento
    try:
        nomi_conti_cassa = [c['nome_conto'] for c in services.ottieni_tutti_i_conti(solo_attivi=True) if
                            c.get('tipo_conto', '').lower() not in ["investimento"]]
        nomi_conti_cassa.insert(0, "")
    except Exception:
        nomi_conti_cassa = [""]
    ttkb.Label(form_frame, text="Conto Pagamento (Opz.):", anchor=W, width=label_width).grid(row=row_idx, column=0,
                                                                                             sticky="w", pady=pady_val,
                                                                                             padx=(0, 10))
    conto_det_combo = ttkb.Combobox(form_frame, textvariable=conto_detenzione_var, values=nomi_conti_cassa,
                                    bootstyle=PRIMARY, state="readonly")
    conto_det_combo.grid(row=row_idx, column=1, columnspan=3, sticky="ew", pady=pady_val);
    row_idx += 1

    # Note
    ttkb.Label(form_frame, text="Note (Opzionali):", anchor=NW, width=label_width).grid(row=row_idx, column=0,
                                                                                        sticky="nw", pady=pady_val,
                                                                                        padx=(0, 10))
    # Per tk.Text, è meglio dargli un frame contenitore se vuoi un bordo ttkbootstrap-like
    # e controllare l'espansione.
    note_outer_frame = ttkb.Frame(form_frame)  # Non serve bootstyle qui, è solo per layout
    note_outer_frame.grid(row=row_idx, column=1, columnspan=3, sticky="ew", pady=pady_val);
    row_idx += 1

    note_text = tk.Text(note_outer_frame, height=3, width=30, relief=SOLID, borderwidth=1, font=("Segoe UI", 9),
                        wrap=WORD)
    note_text_scroll = ttkb.Scrollbar(note_outer_frame, orient=VERTICAL, command=note_text.yview,
                                      bootstyle="round-primary-slim")
    note_text['yscrollcommand'] = note_text_scroll.set
    note_text_scroll.pack(side=RIGHT, fill=Y)  # Scrollbar a destra del Text
    note_text.pack(side=LEFT, fill=BOTH, expand=True)  # Text occupa il resto

    # Configura le colonne del form_frame per l'espansione
    form_frame.columnconfigure(0, weight=0)  # Colonna Label
    form_frame.columnconfigure(1, weight=1)  # Colonna Entry principale
    form_frame.columnconfigure(2, weight=0)  # Colonna Label valuta
    form_frame.columnconfigure(3, weight=0)  # Colonna Entry valuta

    # --- Funzione di Conferma (invariata) ---
    def on_conferma_nuovo_investimento():
        nome_val = nome_var.get()
        simbolo_val = simbolo_var.get()
        tipo_val = tipo_asset_var.get()
        qta_str = quantita_var.get()
        pmc_str = pmc_unitario_var.get()
        costo_str = costo_totale_carico_var.get()
        valuta_val = valuta_var.get()
        data_acq_str_ui = data_acq_entry.entry.get()
        conto_det_nome = conto_detenzione_var.get()
        id_conto_det_fk = None
        if conto_det_nome:
            conto_obj = services.ottieni_conto_per_nome(conto_det_nome)
            if conto_obj:
                id_conto_det_fk = conto_obj['id_conto']
            else:
                Messagebox.show_warning("Conto di pagamento selezionato non valido.", "Attenzione", parent=dialog,
                                        alert=True); return
        note_val = note_text.get("1.0", "end-1c").strip()

        try:
            services.aggiungi_nuovo_investimento(
                nome_strumento=nome_val, simbolo=simbolo_val, tipo_asset=tipo_val,
                quantita_str=qta_str, pmc_unitario_str=pmc_str, costo_totale_carico_str=costo_str,
                valore_attuale_unitario_str=None, data_valore_attuale_input=None,
                id_conto_detenzione_fk=id_conto_det_fk, valuta=valuta_val,
                data_primo_acquisto_input=data_acq_str_ui, note=note_val
            )
            toast = ToastNotification(title="Investimento Aggiunto", message=f"'{nome_val}' aggiunto!", duration=3000,
                                      bootstyle=SUCCESS, alert=True, position=(20, 20, 'se'))
            toast.show_toast()
            dialog.destroy()
            callback_refresh()
        except ValueError as ve:
            if hasattr(dialog, 'bell'): dialog.bell()
            Messagebox.show_warning(str(ve), "Dati Non Validi", parent=dialog, alert=True)
        except Exception as e:
            if hasattr(dialog, 'bell'): dialog.bell()
            Messagebox.show_error(f"Errore imprevisto:\n{e}", "Errore Creazione", parent=dialog, alert=True)
            print(f"Dettaglio errore nuovo investimento: {type(e).__name__}: {e}")

    # --- Pulsanti di Azione (figli di main_dialog_frame) ---
    action_frame = ttkb.Frame(main_dialog_frame)  # Figlio di main_dialog_frame
    action_frame.pack(fill=X, side=BOTTOM, pady=(10, 0))  # Padding sopra i bottoni

    btn_conferma = ttkb.Button(action_frame, text="💾 Salva Investimento", command=on_conferma_nuovo_investimento,
                               bootstyle=SUCCESS)
    btn_conferma.pack(side=RIGHT, padx=5)  # Aggiunto padx per separarlo dal bordo se è l'unico
    btn_annulla = ttkb.Button(action_frame, text="❌ Annulla", command=dialog.destroy, bootstyle=LIGHT)
    btn_annulla.pack(side=RIGHT, padx=(0, 5))

    dialog.bind('<Return>', lambda event: on_conferma_nuovo_investimento())
    dialog.bind('<Escape>', lambda event: dialog.destroy())

    dialog.update_idletasks()
    # Centratura
    parent_x = app_root_param.winfo_x();
    parent_y = app_root_param.winfo_y()
    parent_width = app_root_param.winfo_width();
    parent_height = app_root_param.winfo_height()

    # Usa le dimensioni richieste dal contenuto per il dialogo, ma con un minimo
    dialog_width = max(dialog.winfo_reqwidth() + 40, 600)  # +40 per il padding del main_dialog_frame
    dialog_height = max(dialog.winfo_reqheight() + 60, 550)  # +60 per padding e bottoni

    x_pos = parent_x + (parent_width // 2) - (dialog_width // 2);
    y_pos = parent_y + (parent_height // 2) - (dialog_height // 2)
    dialog.geometry(f"{dialog_width}x{dialog_height}+{x_pos}+{y_pos}")

    dialog.after(50, dialog.lift)
    dialog.after(100, nome_entry.focus_force)


def apri_impostazioni(main_frame, app_root):
    navigate_away_from_dashboard()
    for widget in main_frame.winfo_children(): widget.destroy()
    ttkb.Label(main_frame, text="Impostazioni Applicazione", font=("Segoe UI", 16, "bold")).pack(pady=20)


def main():
    global app_state
    app = ttkb.Window(themename="superhero");
    app.title("Cato Finance :)")
    app.geometry("1380x750");
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
        ("💼 Conti e Transazioni", lambda: apri_conti_e_transazioni_view(main_content_frame, app)),
        ("📈 Investimenti", lambda: apri_investimenti_view(main_content_frame, app)), ]
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