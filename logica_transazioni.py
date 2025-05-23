#logica, aggiornamenti e giroconto

from storage import carica_conti, salva_conti, carica_transazioni, salva_transazioni

import json
import os

FILE_CONTI = "data/conti.json"

def carica_conti():
    if not os.path.exists(FILE_CONTI):
        return {}
    with open(FILE_CONTI, "r") as f:
        return json.load(f)

def salva_conti(conti):
    with open(FILE_CONTI, "w") as f:
        json.dump(conti, f, indent=4)


def aggiungi_transazione(transazione):
    transazioni = carica_transazioni()
    transazioni.append(transazione)
    salva_transazioni(transazioni)

def registra_transazione(importo, conto, categoria, descrizione, data=None):
    if data is None:
        from datetime import datetime
        data = datetime.now().strftime("%Y-%m-%d")

    transazione = {
        "data": data,
        "conto": conto,
        "importo": importo,
        "categoria": categoria,
        "descrizione": descrizione
    }

    # Aggiorna saldo conto
    aggiorna_saldo(conto, importo)

    # Salva transazione
    aggiungi_transazione(transazione)

def giroconto(conto_origine, conto_destinazione, importo):
    if importo <= 0:
        raise ValueError("L'importo deve essere positivo.")

    conti = carica_conti()

    if conto_origine not in conti:
        raise ValueError(f"Il conto di origine '{conto_origine}' non esiste.")
    if conto_destinazione not in conti:
        raise ValueError(f"Il conto di destinazione '{conto_destinazione}' non esiste.")

    if conti[conto_origine] < importo:
        raise ValueError("Saldo insufficiente per completare il giroconto.")

    # Uscita dal conto origine
    registra_transazione(conto_origine, f"Giroconto verso {conto_destinazione}", -importo, "giroconto")

    # Entrata nel conto destinazione
    registra_transazione(conto_destinazione, f"Giroconto da {conto_origine}", importo, "giroconto")

def aggiorna_saldo(nome_conto, importo):
    conti = carica_conti()
    if nome_conto not in conti:
        conti[nome_conto] = 0
    conti[nome_conto] += importo
    salva_conti(conti)