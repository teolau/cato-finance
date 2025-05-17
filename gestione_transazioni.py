import json
import os
from datetime import datetime

FILE_TRANSAZIONI = "data/transazioni.json"
FILE_CONTI = "data/conti.json"

def carica_transazioni():
    if not os.path.exists(FILE_TRANSAZIONI):
        return []
    with open(FILE_TRANSAZIONI, "r") as f:
        return json.load(f)

def salva_transazioni(transazioni):
    with open(FILE_TRANSAZIONI, "w") as f:
        json.dump(transazioni, f, indent=4)

def aggiungi_transazione(nome_conto, descrizione, importo, categoria):
    from gestione_conti import carica_conti, salva_conti
    conti = carica_conti()

    if nome_conto not in conti:
        raise ValueError("Conto inesistente.")

    conti[nome_conto] += importo
    salva_conti(conti)

    transazioni = carica_transazioni()
    transazioni.append({
        "data": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "conto": nome_conto,
        "descrizione": descrizione,
        "importo": importo,
        "categoria": categoria
    })
    salva_transazioni(transazioni)

