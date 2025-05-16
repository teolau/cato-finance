import os
import json
from datetime import datetime

# Percorso del file transazioni
PERCORSO_TRANSAZIONI = os.path.join("data", "transazioni.json")


def carica_transazioni():
    if os.path.exists(PERCORSO_TRANSAZIONI):
        with open(PERCORSO_TRANSAZIONI, "r") as f:
            return json.load(f)
    return []


def salva_transazioni(transazioni):
    with open(PERCORSO_TRANSAZIONI, "w") as f:
        json.dump(transazioni, f, indent=4)


def aggiungi_transazione(tipo, conto, importo, categoria, descrizione=""):
    transazioni = carica_transazioni()
    transazione = {
        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tipo": tipo,  # "entrata", "uscita", "correzione", "giraconto"
        "conto": conto,
        "importo": importo,
        "categoria": categoria,
        "descrizione": descrizione
    }
    transazioni.append(transazione)
    salva_transazioni(transazioni)

    # Aggiorna saldo nel file conti
    from gestione_conti import carica_conti, salva_conti
    conti = carica_conti()
    if conto not in conti:
        raise ValueError(f"Il conto '{conto}' non esiste.")

    if tipo == "entrata":
        conti[conto] += importo
    elif tipo == "uscita":
        conti[conto] -= importo
    elif tipo == "correzione":
        conti[conto] = importo
    elif tipo == "giraconto":
        pass  # gestito a parte

    salva_conti(conti)
