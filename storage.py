#questo file gestisce la lettura/scrittura su file .json


import json
import os

FILE_CONTI = "data/conti.json"
FILE_TRANSAZIONI = "data/transazioni.json"

def carica_conti():
    if not os.path.exists(FILE_CONTI):
        return {}
    with open(FILE_CONTI, "r") as f:
        return json.load(f)

def salva_conti(conti):
    with open(FILE_CONTI, "w") as f:
        json.dump(conti, f, indent=4)

def carica_transazioni():
    if not os.path.exists(FILE_TRANSAZIONI):
        return []
    with open(FILE_TRANSAZIONI, "r") as f:
        return json.load(f)

def salva_transazioni(transazioni):
    with open(FILE_TRANSAZIONI, "w") as f:
        json.dump(transazioni, f, indent=4)
