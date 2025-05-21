from gestione_transazioni import aggiungi_transazione
from gestione_conti import aggiorna_saldo, carica_conti

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