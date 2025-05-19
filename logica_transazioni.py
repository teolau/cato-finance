from gestione_transazioni import aggiungi_transazione
from gestione_conti import aggiorna_saldo

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
