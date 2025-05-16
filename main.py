import tkinter as tk
from tkinter import messagebox
import json
import os
import gestione_conti

DATA_PATH = "data/conti.json"

# Se il file non esiste, crealo con dati di default
def inizializza_file_conti():
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(DATA_PATH):
        conti_default = {
            "Conto Corrente": 0.0,
            "Investimenti": 0.0,
            "Prepagata": 0.0,
            "Contanti": 0.0
        }
        with open(DATA_PATH, "w") as f:
            json.dump(conti_default, f, indent=4)

# Carica i conti da file
def carica_conti():
    if not os.path.exists(DATA_PATH):
        return {}
    with open(DATA_PATH, "r") as f:
        return json.load(f)

# Salva i conti su file
def salva_conti(conti):
    with open(DATA_PATH, "w") as f:
        json.dump(conti, f, indent=4)

# Aggiorna l'interfaccia con i saldi correnti
def aggiorna_saldi():
    global conti
    conti = carica_conti()
    saldi_testo = ""
    for conto, saldo in conti.items():
        saldi_testo += f"{conto}: {saldo:.2f} €\n"
    saldo_label.config(text=saldi_testo)

# Placeholder per le azioni future
def aggiungi_transazione():
    messagebox.showinfo("Azione", "Funzione: Aggiungi Transazione")

def giroconto():
    messagebox.showinfo("Azione", "Funzione: Giroconto")

def visualizza_storico():
    messagebox.showinfo("Azione", "Funzione: Storico Conti")

def gestisci_conti():
    gestione_conti.apri_finestra_gestione_conti(root, aggiorna_saldi)

# Inizializza file
inizializza_file_conti()

# Setup GUI
root = tk.Tk()
root.title("Gestionale Finanze Personali")

saldo_label = tk.Label(root, text="", font=("Arial", 12), justify="left")
saldo_label.pack(padx=10, pady=10)
aggiorna_saldi()

btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

tk.Button(btn_frame, text="➕ Aggiungi Transazione", width=25, command=aggiungi_transazione).grid(row=0, column=0, padx=5, pady=5)
tk.Button(btn_frame, text="🔄 Giroconto", width=25, command=giroconto).grid(row=1, column=0, padx=5, pady=5)
tk.Button(btn_frame, text="📈 Storico Conti", width=25, command=visualizza_storico).grid(row=0, column=1, padx=5, pady=5)
tk.Button(btn_frame, text="⚙️ Gestisci Conti", width=25, command=gestisci_conti).grid(row=1, column=1, padx=5, pady=5)

root.mainloop()
