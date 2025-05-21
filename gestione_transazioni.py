import json
import os

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

def aggiungi_transazione(transazione):
    transazioni = carica_transazioni()
    transazioni.append(transazione)
    salva_transazioni(transazioni)


