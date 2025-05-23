#GUI conti

import tkinter as tk
from tkinter import messagebox, ttk
import logica_transazioni

def aggiungi_conto(nome_conto, saldo_iniziale=0.0):
    conti = logica_transazioni.carica_conti()
    if nome_conto in conti:
        raise ValueError("Conto già esistente.")
    conti[nome_conto] = saldo_iniziale
    logica_transazioni.salva_conti(conti)

def rimuovi_conto(nome_conto):
    conti = logica_transazioni.carica_conti()
    if nome_conto not in conti:
        raise ValueError("Conto inesistente.")
    del conti[nome_conto]
    logica_transazioni.salva_conti(conti)

def modifica_saldo(nome_conto, nuovo_saldo, aggiungi_transazione):
    #dependency injection per aggiungi_transazione bc im a lazy ass
    conti = logica_transazioni.carica_conti()
    if nome_conto not in conti:
        raise ValueError("Conto inesistente.")
    saldo_attuale = conti[nome_conto]
    differenza = nuovo_saldo - saldo_attuale
    if differenza == 0:
        return  # niente da modificare
    # NON aggiornare conti[nome_conto] qui, ma solo tramite aggiungi_transazione
    aggiungi_transazione(nome_conto, "🛠 Correzione manuale", differenza, "correzione")

def apri_popup_modifica_saldo(root, aggiorna_saldi_callback):
    conti = logica_transazioni.carica_conti()
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
            modifica_saldo(nome_conto, nuovo_saldo, logica_transazioni.aggiungi_transazione)
        except Exception as e:
            messagebox.showerror("Errore", str(e))
            return

        popup.destroy()
        aggiorna_saldi_callback()

    def azzera_tutti_i_conti():
        conferma = messagebox.askyesno(
            "Conferma Azzeramento",
            "Sei sicuro di voler azzerare **tutti i conti**? Questa operazione è irreversibile.",
            icon="warning"
        )
        if not conferma:
            return

        for conto in conti:
            try:
                modifica_saldo(conto, 0.0, logica_transazioni.aggiungi_transazione)
            except Exception as e:
                messagebox.showerror("Errore", f"Errore con il conto '{conto}': {str(e)}")

        messagebox.showinfo("Fatto", "Tutti i conti sono stati azzerati.")
        popup.destroy()
        aggiorna_saldi_callback()

    tk.Button(popup, text="Conferma", command=conferma).grid(row=2, column=0, columnspan=2, pady=10)
    tk.Button(
        popup, text="Azzera tutti i conti",
        command=azzera_tutti_i_conti,
        fg="white", bg="#cc4c4c", activebackground="#b33c3c"
    ).grid(row=3, column=0, columnspan=2, pady=(0, 10), ipadx=10)

def apri_finestra_gestione_conti(root=None, aggiorna_saldi_callback=None):

    finestra = tk.Toplevel()
    finestra.title("Gestione Conti")

    etichetta_saldi = tk.Label(finestra, text="")
    etichetta_saldi.pack(pady=10)

    if aggiorna_saldi_callback:
        aggiorna_saldi_callback()

    def aggiorna_saldi():
        conti = logica_transazioni.carica_conti()
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

        entry_nome = ttk.Combobox(popup, values=list(logica_transazioni.carica_conti().keys()))
        entry_nome.grid(row=0, column=1)

        tk.Button(popup, text="Conferma", command=conferma).grid(row=1, columnspan=2, pady=10)

    frame_pulsanti = tk.Frame(finestra)
    frame_pulsanti.pack()

    tk.Button(frame_pulsanti, text="➕ Aggiungi Conto", command=aggiungi).pack(side=tk.LEFT, padx=5)
    tk.Button(frame_pulsanti, text="🗑️ Rimuovi Conto", command=rimuovi).pack(side=tk.LEFT, padx=5)
    tk.Button(frame_pulsanti, text="💰 Modifica Saldo", command=lambda: apri_popup_modifica_saldo(finestra, aggiorna_saldi)).pack(side=tk.LEFT, padx=5)

    aggiorna_saldi()


