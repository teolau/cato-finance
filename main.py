import tkinter as tk
from tkinter import messagebox, ttk
from gestione_conti import carica_conti, aggiungi_conto, rimuovi_conto, modifica_saldo
from utils.sfondo import scegli_sfondo_casuale, ridimensiona_sfondo
from gestione_transazioni import carica_transazioni, aggiungi_transazione
from datetime import datetime
from logica_transazioni import registra_transazione


def apri_popup_modifica_saldo(root, aggiorna_saldi_callback):
    conti = carica_conti()
    popup = tk.Toplevel(root)
    popup.title("Modifica Saldo")

    tk.Label(popup, text="Conto:").grid(row=0, column=0, padx=5, pady=5)
    entry_conto = ttk.Combobox(popup, values=list(conti.keys()))
    entry_conto.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(popup, text="Nuovo saldo:").grid(row=1, column=0, padx=5, pady=5)
    entry_saldo = tk.Entry(popup)
    entry_saldo.grid(row=1, column=1, padx=5, pady=5)

    def conferma():
        nome_conto = entry_conto.get()
        try:
            nuovo_saldo = float(entry_saldo.get())
        except ValueError:
            messagebox.showerror("Errore", "Inserisci un numero valido.")
            return

        try:
            modifica_saldo(nome_conto, nuovo_saldo, aggiungi_transazione)
        except Exception as e:
            messagebox.showerror("Errore", str(e))
            return

        popup.destroy()
        aggiorna_saldi_callback()

    tk.Button(popup, text="Conferma", command=conferma).grid(row=2, column=0, columnspan=2, pady=10)

def apri_finestra_gestione_conti(root=None, aggiorna_saldi_callback=None):
    finestra = tk.Toplevel()
    finestra.title("Gestione Conti")

    etichetta_saldi = tk.Label(finestra, text="")
    etichetta_saldi.pack(pady=10)

    if aggiorna_saldi_callback:
        aggiorna_saldi_callback()

    def aggiorna_saldi():
        conti = carica_conti()
        testo = "Saldi attuali:\n"
        for nome, saldo in conti.items():
            testo += f"{nome}: {saldo:.2f} €\n"
        etichetta_saldi.config(text=testo)

    def aggiungi():
        def conferma():
            nome = entry_nome.get()
            try:
                saldo = float(entry_saldo.get())
                aggiungi_conto(nome, saldo)
                aggiorna_saldi()
                popup.destroy()
            except Exception as e:
                messagebox.showerror("Errore", str(e))

        popup = tk.Toplevel(finestra)
        popup.title("Aggiungi Conto")
        tk.Label(popup, text="Nome:").grid(row=0, column=0)
        entry_nome = tk.Entry(popup)
        entry_nome.grid(row=0, column=1)

        tk.Label(popup, text="Saldo iniziale:").grid(row=1, column=0)
        entry_saldo = tk.Entry(popup)
        entry_saldo.grid(row=1, column=1)

        tk.Button(popup, text="Conferma", command=conferma).grid(row=2, columnspan=2, pady=10)

    def rimuovi():
        def conferma():
            nome = entry_nome.get()
            try:
                rimuovi_conto(nome)
                aggiorna_saldi()
                popup.destroy()
            except Exception as e:
                messagebox.showerror("Errore", str(e))

        popup = tk.Toplevel(finestra)
        popup.title("Rimuovi Conto")

        tk.Label(popup, text="Nome:").grid(row=0, column=0)

        entry_nome = ttk.Combobox(popup, values=list(carica_conti().keys()))
        entry_nome.grid(row=0, column=1)

        tk.Button(popup, text="Conferma", command=conferma).grid(row=1, columnspan=2, pady=10)

    frame_pulsanti = tk.Frame(finestra)
    frame_pulsanti.pack()

    tk.Button(frame_pulsanti, text="➕ Aggiungi Conto", command=aggiungi).pack(side=tk.LEFT, padx=5)
    tk.Button(frame_pulsanti, text="🗑️ Rimuovi Conto", command=rimuovi).pack(side=tk.LEFT, padx=5)
    tk.Button(frame_pulsanti, text="💰 Modifica Saldo", command=lambda: apri_popup_modifica_saldo(finestra, aggiorna_saldi)).pack(side=tk.LEFT, padx=5)

    aggiorna_saldi()

def mostra_saldi(frame, conti):
    for widget in frame.winfo_children():
        widget.destroy()  # pulisce il frame per aggiornare

    for nome, saldo in conti.items():
        testo = f"{nome}: € {saldo:.2f}"
        label = tk.Label(frame, text=testo, font=("Arial", 14))
        label.pack(anchor="w")

def centra_finestra(finestra, larghezza, altezza):
    finestra.update_idletasks()
    screen_width = finestra.winfo_screenwidth()
    screen_height = finestra.winfo_screenheight()
    x = (screen_width - larghezza) // 2
    y = (screen_height - altezza) // 2
    finestra.geometry(f"{larghezza}x{altezza}+{x}+{y}")

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

    for tr in cont_transactions:
        tree.insert("", "end", values=(
            tr["data"], tr["conto"], tr["categoria"], f'{tr["importo"]:.2f}', tr["descrizione"]
        ))

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


def main():
    root = tk.Tk()
    root.title("Cato Finance :)")

    larghezza = 400
    altezza = 400
    centra_finestra(root, larghezza, altezza)
    root.resizable(False, False)        #todo: quando lo sfondo diventa responsive eliminare questa riga

    conti = carica_conti()
    transazioni = carica_transazioni()

    # Carica sfondo
    root.sfondo_path = scegli_sfondo_casuale("sfondi")
    root.sfondo_img = ridimensiona_sfondo(root.sfondo_path, (larghezza, altezza))

    #label sfondo
    root.sfondo_label = tk.Label(root, image=root.sfondo_img)
    root.sfondo_label.image = root.sfondo_img
    root.sfondo_label.place(x=0, y=0, relwidth=1, relheight=1)
    root.sfondo_label.lower()  # Manda lo sfondo dietro

    # todo: Aggiorna sfondo al resize, per ora con questa funzione lo sfondo scompare all'apertura (problema con "root."?)
#    def aggiorna_sfondo(event):
#        nuovo = ridimensiona_sfondo(root.sfondo_path, (event.width, event.height))
#        root.sfondo_label.configure(image=nuovo)
#        root.sfondo_label.image = nuovo

#    root.bind("<Configure>", aggiorna_sfondo)


    tk.Label(root, text="Cato Finance :)", font=("Arial", 16), bg="white").pack(pady=10)

   # frame_saldi = tk.Frame(root, bg="white")
   # frame_saldi.pack(pady=10)

    frame_conti = tk.Frame(root, bg="white")
    frame_conti.pack(pady=15)

   # mostra_saldi(frame_saldi, conti)

    for nome_conto in conti:
        tk.Button(frame_conti, text=f"{nome_conto} ({conti[nome_conto]:.2f} €)",
                  command=lambda c=nome_conto: mostra_transazioni([tr for tr in transazioni if tr["conto"] == c],
                                                                  f"Transazioni - {c}")).pack(pady=5)

    btn_tutte = tk.Button(root, text="📜 Visualizza tutte le transazioni",
                          command=lambda: mostra_transazioni(transazioni, "Tutte le transazioni"))
    btn_tutte.pack(pady=5)

    btn_aggiungi = tk.Button(root, text="➕ Aggiungi transazione",
                             command=lambda: aggiungi_transazione_popup(root, conti))
    btn_aggiungi.pack(pady=5)

    tk.Button(root, text="💼 Gestione Conti",
              command=lambda: apri_finestra_gestione_conti(root, lambda: print("TODO aggiorna saldi"))).pack(pady=5)

    root.mainloop()


if __name__ == "__main__":
    main()
