# gestione_conti.py

import tkinter as tk
from tkinter import messagebox
import json
import os
from gestione_transazioni import aggiungi_transazione

DATA_PATH = "data/conti.json"

def carica_conti():
    if not os.path.exists(DATA_PATH):
        return {}
    with open(DATA_PATH, "r") as f:
        return json.load(f)

def salva_conti(conti):
    with open(DATA_PATH, "w") as f:
        json.dump(conti, f, indent=4)

def apri_finestra_gestione_conti(root, aggiorna_saldi_callback):
    finestra = tk.Toplevel(root)
    finestra.title("Gestione Conti")

    # Lista dei conti esistenti
    conti = carica_conti()
    lista_conti = tk.Listbox(finestra, width=40)
    for conto in conti:
        lista_conti.insert(tk.END, conto)
    lista_conti.pack(padx=10, pady=10)

    # Entry per nuovo conto
    frame_nuovo_conto = tk.Frame(finestra)
    frame_nuovo_conto.pack(padx=10, pady=5)
    tk.Label(frame_nuovo_conto, text="Nome nuovo conto:").pack(side=tk.LEFT)
    entry_nuovo_conto = tk.Entry(frame_nuovo_conto)
    entry_nuovo_conto.pack(side=tk.LEFT)

    # Entry per saldo iniziale
    frame_saldo_iniziale = tk.Frame(finestra)
    frame_saldo_iniziale.pack(padx=10, pady=5)
    tk.Label(frame_saldo_iniziale, text="Saldo iniziale:").pack(side=tk.LEFT)
    entry_saldo_iniziale = tk.Entry(frame_saldo_iniziale)
    entry_saldo_iniziale.pack(side=tk.LEFT)

    # Funzione per aggiungere conto
    def aggiungi_conto():
        nome = entry_nuovo_conto.get().strip()
        saldo = entry_saldo_iniziale.get().strip()
        if not nome:
            messagebox.showwarning("Attenzione", "Inserisci un nome per il conto.")
            return
        if nome in conti:
            messagebox.showwarning("Attenzione", "Il conto esiste già.")
            return
        try:
            saldo = float(saldo)
        except ValueError:
            messagebox.showwarning("Attenzione", "Inserisci un saldo valido.")
            return
        conti[nome] = saldo
        salva_conti(conti)
        lista_conti.insert(tk.END, nome)
        entry_nuovo_conto.delete(0, tk.END)
        entry_saldo_iniziale.delete(0, tk.END)
        aggiorna_saldi_callback()

    # Funzione per rimuovere conto
    def rimuovi_conto():
        selezione = lista_conti.curselection()
        if not selezione:
            messagebox.showwarning("Attenzione", "Seleziona un conto da rimuovere.")
            return
        nome = lista_conti.get(selezione[0])
        conferma = messagebox.askyesno("Conferma", f"Sei sicuro di voler rimuovere il conto '{nome}'?")
        if conferma:
            del conti[nome]
            salva_conti(conti)
            lista_conti.delete(selezione[0])
            aggiorna_saldi_callback()

    # Entry per modifica saldo
    frame_modifica_saldo = tk.Frame(finestra)
    frame_modifica_saldo.pack(padx=10, pady=5)
    tk.Label(frame_modifica_saldo, text="Nuovo saldo per conto selezionato:").pack(side=tk.LEFT)
    entry_modifica_saldo = tk.Entry(frame_modifica_saldo)
    entry_modifica_saldo.pack(side=tk.LEFT)

    def modifica_saldo():
        selezione = lista_conti.curselection()
        if not selezione:
            messagebox.showwarning("Attenzione", "Seleziona un conto da modificare.")
            return
        nome = lista_conti.get(selezione[0])
        nuovo_saldo = entry_modifica_saldo.get().strip()
        try:
            nuovo_saldo = float(nuovo_saldo)
        except ValueError:
            messagebox.showwarning("Attenzione", "Inserisci un saldo valido.")
            return
        conferma = messagebox.askyesno("Conferma", f"Vuoi impostare il saldo di '{nome}' a {nuovo_saldo:.2f} €?")
        if conferma:
            aggiungi_transazione("correzione", nome, nuovo_saldo, "correzione manuale", "Correzione saldo manuale")
            entry_modifica_saldo.delete(0, tk.END)
            aggiorna_saldi_callback()


    # Pulsanti
    frame_pulsanti = tk.Frame(finestra)
    frame_pulsanti.pack(padx=10, pady=10)
    tk.Button(frame_pulsanti, text="Aggiungi Conto", command=aggiungi_conto).pack(side=tk.LEFT, padx=5)
    tk.Button(frame_pulsanti, text="Rimuovi Conto", command=rimuovi_conto).pack(side=tk.LEFT, padx=5)
    tk.Button(frame_pulsanti, text="💰 Modifica Saldo", command=modifica_saldo).pack(side=tk.LEFT, padx=5)

