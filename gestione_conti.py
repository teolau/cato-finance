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

def aggiungi_conto(nome_conto, saldo_iniziale=0.0):
    conti = carica_conti()
    if nome_conto in conti:
        raise ValueError("Conto già esistente.")
    conti[nome_conto] = saldo_iniziale
    salva_conti(conti)

def rimuovi_conto(nome_conto):
    conti = carica_conti()
    if nome_conto not in conti:
        raise ValueError("Conto inesistente.")
    del conti[nome_conto]
    salva_conti(conti)

def modifica_saldo(nome_conto, nuovo_saldo, aggiungi_transazione):
    #dependency injection per aggiungi_transazione bc im a lazy ass
    conti = carica_conti()
    if nome_conto not in conti:
        raise ValueError("Conto inesistente.")
    saldo_attuale = conti[nome_conto]
    differenza = nuovo_saldo - saldo_attuale
    if differenza == 0:
        return  # niente da modificare
    # NON aggiornare conti[nome_conto] qui, ma solo tramite aggiungi_transazione
    aggiungi_transazione(nome_conto, "🛠 Correzione manuale", differenza, "correzione")

def aggiorna_saldo(nome_conto, importo):
    conti = carica_conti()
    if nome_conto not in conti:
        conti[nome_conto] = 0
    conti[nome_conto] += importo
    salva_conti(conti)


