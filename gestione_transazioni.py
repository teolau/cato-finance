#GUI transazioni

from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from logica_transazioni import registra_transazione

def mostra_transazioni(cont_transactions, titolo="Transazioni"):
    """Mostra una finestra con una lista delle transazioni passate."""
    finestra = tk.Toplevel()
    finestra.title(titolo)
    finestra.geometry("600x400")

    tree = ttk.Treeview(finestra, columns=("Data", "Conto", "Categoria", "Importo", "Descrizione"), show="headings")
    for col in tree["columns"]:
        tree.heading(col, text=col)
        tree.column(col, width=100)
    tree.pack(fill=tk.BOTH, expand=True)

    # Colori pastello
    tree.tag_configure("entrata", background="#d5f5d5")
    tree.tag_configure("uscita", background="#f7d6d6")

    for tr in cont_transactions:
        importo = tr["importo"]
        tag = "entrata" if importo >= 0 else "uscita"
        tree.insert("", "end", values=(
            tr["data"], tr["conto"], tr["categoria"], f'{importo:.2f}', tr["descrizione"]
        ), tags=(tag,))

def aggiungi_transazione_popup(root, conti):
    def aggiorna_campi(*args):
        if tipo_var.get() == "Giroconto":
            conto_label.config(text="Conto origine:")
            categoria_label.config(text="Conto destinazione:")
            categoria_entry.grid_remove()
            conto_combo.grid(row=1, column=1, sticky="w", pady=3)
            categoria_combo.grid(row=2, column=1, sticky="w", pady=3)
        else:
            conto_label.config(text="Conto:")
            categoria_label.config(text="Categoria:")
            categoria_combo.grid_remove()
            categoria_entry.grid(row=2, column=1, sticky="w", pady=3)
            conto_combo.grid(row=1, column=1, sticky="w", pady=3)

    def conferma():
        try:
            tipo = tipo_var.get()
            data = data_entry.get()
            datetime.strptime(data, "%Y-%m-%d")  # valida la data

            if tipo == "Giroconto":
                conto_origine = conto_var.get()
                conto_destinazione = categoria_var.get()
                importo = float(importo_entry.get())
                descrizione = descrizione_entry.get()
                if conto_origine not in conti or conto_destinazione not in conti:
                    raise ValueError("Conto origine o destinazione non valido.")
                # Esegui giroconto
                registra_transazione(-importo, conto_origine, "Giroconto", descrizione, data)
                registra_transazione(importo, conto_destinazione, "Giroconto", descrizione, data)
            else:
                conto = conto_var.get()
                categoria = categoria_entry.get()
                importo = float(importo_entry.get())
                descrizione = descrizione_entry.get()
                if tipo == "Uscita":
                    importo = -importo
                if conto not in conti:
                    raise ValueError("Conto non valido.")
                registra_transazione(importo, conto, categoria, descrizione, data)

            messagebox.showinfo("Successo", "Transazione aggiunta.")
            finestra.destroy()

        except Exception as e:
            messagebox.showerror("Errore", f"Errore: {e}")

    # --- GUI ---
    finestra = tk.Toplevel(root)
    finestra.title("Aggiungi Transazione")
    finestra.geometry("370x320")
    finestra.resizable(False, False)

    form_frame = tk.Frame(finestra, padx=10, pady=10)
    form_frame.pack(fill="both", expand=True)

    tipo_var = tk.StringVar(value="Entrata")
    conto_var = tk.StringVar()
    categoria_var = tk.StringVar()

    # Etichette
    tipo_label = tk.Label(form_frame, text="Tipo:")
    conto_label = tk.Label(form_frame, text="Conto:")
    categoria_label = tk.Label(form_frame, text="Categoria:")

    tipo_label.grid(row=0, column=0, sticky="e", pady=3, padx=(0, 5))
    conto_label.grid(row=1, column=0, sticky="e", pady=3, padx=(0, 5))
    categoria_label.grid(row=2, column=0, sticky="e", pady=3, padx=(0, 5))

    # Campi
    tipo_combo = ttk.Combobox(form_frame, textvariable=tipo_var, values=["Entrata", "Uscita", "Giroconto"], width=20)
    conto_combo = ttk.Combobox(form_frame, textvariable=conto_var, values=list(conti.keys()), width=20)
    categoria_entry = tk.Entry(form_frame, width=22)
    categoria_combo = ttk.Combobox(form_frame, textvariable=categoria_var, values=list(conti.keys()), width=20)

    tipo_combo.grid(row=0, column=1, sticky="w", pady=3)
    conto_combo.grid(row=1, column=1, sticky="w", pady=3)
    categoria_entry.grid(row=2, column=1, sticky="w", pady=3)

    importo_label = tk.Label(form_frame, text="Importo:")
    importo_entry = tk.Entry(form_frame, width=22)
    importo_label.grid(row=3, column=0, sticky="e", pady=3, padx=(0, 5))
    importo_entry.grid(row=3, column=1, sticky="w", pady=3)

    descrizione_label = tk.Label(form_frame, text="Descrizione:")
    descrizione_entry = tk.Entry(form_frame, width=22)
    descrizione_label.grid(row=4, column=0, sticky="e", pady=3, padx=(0, 5))
    descrizione_entry.grid(row=4, column=1, sticky="w", pady=3)

    data_label = tk.Label(form_frame, text="Data (YYYY-MM-DD):")
    data_entry = tk.Entry(form_frame, width=22)
    data_entry.insert(0, datetime.today().strftime("%Y-%m-%d"))
    data_label.grid(row=5, column=0, sticky="e", pady=3, padx=(0, 5))
    data_entry.grid(row=5, column=1, sticky="w", pady=3)

    # Conferma
    btn_frame = tk.Frame(finestra)
    btn_frame.pack(pady=10)
    conferma_btn = tk.Button(btn_frame, text="Conferma", command=conferma)
    conferma_btn.pack()

    # Collegamento evento
    tipo_var.trace_add("write", aggiorna_campi)
    aggiorna_campi()



