import database  # Il nostro modulo per le interazioni con SQLite
from datetime import datetime, date  # Per la gestione delle date
import decimal  # Opzionale, per una maggiore precisione con gli importi se necessario


# --- Servizi per i Conti ---

def crea_nuovo_conto(nome_conto, saldo_iniziale_str="0.0", tipo_conto=None, valuta='EUR'):
    """
    Servizio per creare un nuovo conto.
    Esegue validazione e poi chiama la funzione del database.
    Restituisce l'ID del nuovo conto o solleva un'eccezione in caso di errore.
    """
    if not nome_conto or not nome_conto.strip():
        raise ValueError("Il nome del conto non può essere vuoto.")
    try:
        saldo_iniziale_float = float(saldo_iniziale_str)
    except ValueError:
        raise ValueError("Il saldo iniziale deve essere un numero valido.")

    id_conto = database.aggiungi_conto_db(nome_conto.strip(), saldo_iniziale_float, tipo_conto, valuta)
    if id_conto is None:
        # L'errore specifico (es. conto duplicato) è già stato stampato da aggiungi_conto_db
        raise Exception(f"Impossibile creare il conto '{nome_conto}'. Controllare i log per dettagli.")
    return id_conto


def ottieni_conto_per_id(id_conto):
    return database.get_conto_by_id_db(id_conto)


def ottieni_conto_per_nome(nome_conto):  # Utile se l'utente inserisce nomi
    return database.get_conto_by_nome_db(nome_conto)


def ottieni_tutti_i_conti(solo_attivi=True):
    conti = database.get_tutti_i_conti_db(solo_attivi)
    # Qui potresti voler fare ulteriori elaborazioni, es. formattare il saldo
    # for conto in conti:
    #     conto['saldo_formattato'] = f"{conto['saldo_attuale']:.2f} {conto['valuta']}"
    return conti


def modifica_nome_conto(id_conto, nuovo_nome):
    if not nuovo_nome or not nuovo_nome.strip():
        raise ValueError("Il nuovo nome del conto non può essere vuoto.")
    if not database.aggiorna_nome_conto_db(id_conto, nuovo_nome.strip()):
        # L'errore specifico è già stato stampato dalla funzione db
        raise Exception(f"Impossibile aggiornare il nome del conto ID {id_conto}.")
    return True


def disattiva_conto(id_conto):
    # Prima di disattivare, potresti voler controllare se il saldo è zero,
    # o altre logiche di business.
    if not database.imposta_stato_conto_db(id_conto, attivo=False):
        raise Exception(f"Impossibile disattivare il conto ID {id_conto}.")
    return True


def riattiva_conto(id_conto):
    if not database.imposta_stato_conto_db(id_conto, attivo=True):
        raise Exception(f"Impossibile riattivare il conto ID {id_conto}.")
    return True


def elimina_definitivamente_conto(id_conto):
    """
    Tenta di eliminare fisicamente un conto.
    Si affida a ON DELETE RESTRICT nel DB per impedire l'eliminazione se ci sono transazioni.
    """
    conto = ottieni_conto_per_id(id_conto) # Utile per il messaggio di errore o conferma
    if not conto:
        raise ValueError(f"Conto ID {id_conto} non trovato.")

    # Opzionale: controllo del saldo prima di tentare l'eliminazione
    # if conto['saldo_attuale'] != 0.0:
    #     raise ValueError(f"Il saldo del conto '{conto['nome_conto']}' non è zero. Azzera prima il saldo.")

    if not database.elimina_conto_db(id_conto):
        # L'errore specifico (es. IntegrityError a causa di transazioni)
        # è già stato stampato da database.elimina_conto_db
        raise Exception(f"Impossibile eliminare il conto '{conto['nome_conto']}'. Controlla i log per dettagli (potrebbe avere transazioni associate).")
    print(f"Conto '{conto['nome_conto']}' eliminato con successo dal servizio.")
    return True


# --- Servizi per le Transazioni ---

def registra_nuova_transazione(id_conto_fk, importo_str, categoria, descrizione,
                               data_transazione_input=None,  # Può essere stringa "YYYY-MM-DD" o datetime.date
                               tags_str=None, tipo_transazione=None):
    """
    Servizio per registrare una nuova transazione.
    Converte e valida i dati prima di chiamare la funzione del database.
    """
    try:
        importo_float = float(importo_str)
    except ValueError:
        raise ValueError("L'importo deve essere un numero valido.")

    if not id_conto_fk: raise ValueError("ID Conto mancante.")
    if not categoria: raise ValueError("Categoria mancante.")

    data_transazione_db_str = None
    if isinstance(data_transazione_input, str):  # Es. "YYYY-MM-DD"
        try:
            # Aggiungi l'ora corrente se viene passata solo la data
            dt_obj = datetime.strptime(data_transazione_input, "%Y-%m-%d")
            data_transazione_db_str = dt_obj.strftime("%Y-%m-%d") + " " + datetime.now().strftime("%H:%M:%S")
        except ValueError:
            # Prova se è già un formato datetime completo
            try:
                datetime.strptime(data_transazione_input, "%Y-%m-%d %H:%M:%S")
                data_transazione_db_str = data_transazione_input
            except ValueError:
                raise ValueError("Formato data non valido. Usare 'YYYY-MM-DD' o 'YYYY-MM-DD HH:MM:SS'.")
    elif isinstance(data_transazione_input, date):  # Se la GUI usa un datepicker che restituisce date object
        data_transazione_db_str = data_transazione_input.strftime("%Y-%m-%d") + " " + datetime.now().strftime(
            "%H:%M:%S")
    elif data_transazione_input is None:
        data_transazione_db_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    else:
        raise ValueError("Tipo di data non supportato.")

    # Logica per tipo_transazione se non specificato
    if tipo_transazione is None:
        if categoria.lower() == "giroconto":  # Caso semplice
            tipo_transazione = "Giroconto_Out" if importo_float < 0 else "Giroconto_In"
        else:
            tipo_transazione = "Uscita" if importo_float < 0 else "Entrata"

    id_trans = database.registra_transazione_db(
        id_conto_fk, importo_float, categoria, descrizione,
        data_transazione_db_str, tags_str, tipo_transazione
    )
    if id_trans is None:
        raise Exception("Impossibile registrare la transazione.")
    return id_trans


def esegui_giroconto(id_conto_origine, id_conto_destinazione, importo_str, descrizione,
                     data_giroconto_input=None):
    """
    Servizio per eseguire un giroconto.
    Crea due transazioni collegate.
    """
    try:
        importo_float = float(importo_str)
    except ValueError:
        raise ValueError("L'importo del giroconto deve essere un numero valido.")

    if importo_float <= 0:
        raise ValueError("L'importo del giroconto deve essere positivo.")
    if id_conto_origine == id_conto_destinazione:
        raise ValueError("I conti di origine e destinazione non possono essere gli stessi.")

    # Verifica esistenza conti e saldo (opzionale qui, potrebbe essere fatto dalla UI o dal DB)
    conto_origine_obj = ottieni_conto_per_id(id_conto_origine)
    conto_dest_obj = ottieni_conto_per_id(id_conto_destinazione)
    if not conto_origine_obj: raise ValueError(f"Conto origine ID {id_conto_origine} non trovato.")
    if not conto_dest_obj: raise ValueError(f"Conto destinazione ID {id_conto_destinazione} non trovato.")
    # if conto_origine_obj['saldo_attuale'] < importo_float:
    #     raise ValueError(f"Saldo insufficiente su '{conto_origine_obj['nome_conto']}'.")

    data_db_str = None
    if isinstance(data_giroconto_input, str):
        try:
            dt_obj = datetime.strptime(data_giroconto_input, "%Y-%m-%d")
            data_db_str = dt_obj.strftime("%Y-%m-%d") + " " + datetime.now().strftime("%H:%M:%S")
        except ValueError:
            try:
                datetime.strptime(data_giroconto_input, "%Y-%m-%d %H:%M:%S")
                data_db_str = data_giroconto_input
            except ValueError:
                raise ValueError("Formato data giroconto non valido.")
    elif isinstance(data_giroconto_input, date):
        data_db_str = data_giroconto_input.strftime("%Y-%m-%d") + " " + datetime.now().strftime("%H:%M:%S")
    else:  # Se None o altro, usa data corrente
        data_db_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = None
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")

        # Transazione di Uscita
        desc_out = f"{descrizione} (-> {conto_dest_obj['nome_conto']})"
        cursor.execute('''
            INSERT INTO transazioni (id_conto_fk, data_transazione, descrizione, importo, categoria, tipo_transazione)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (id_conto_origine, data_db_str, desc_out, -importo_float, "Giroconto", "Giroconto_Out"))
        id_transazione_uscita = cursor.lastrowid
        if not id_transazione_uscita: raise Exception("Creazione transazione di uscita fallita.")

        cursor.execute("UPDATE conti SET saldo_attuale = saldo_attuale - ? WHERE id_conto = ?",
                       (importo_float, id_conto_origine))

        # Transazione di Entrata
        desc_in = f"{descrizione} (<- {conto_origine_obj['nome_conto']})"
        cursor.execute('''
            INSERT INTO transazioni (id_conto_fk, data_transazione, descrizione, importo, categoria, tipo_transazione, id_transazione_collegata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
        id_conto_destinazione, data_db_str, desc_in, importo_float, "Giroconto", "Giroconto_In", id_transazione_uscita))
        if not cursor.lastrowid: raise Exception("Creazione transazione di entrata fallita.")

        cursor.execute("UPDATE conti SET saldo_attuale = saldo_attuale + ? WHERE id_conto = ?",
                       (importo_float, id_conto_destinazione))

        conn.commit()
        return True
    except Exception as e:
        if conn: conn.rollback()
        # Potrebbe essere utile loggare l'errore originale e poi rilanciare un errore più generico o specifico del servizio
        print(f"Errore servizio giroconto: {e}")
        raise Exception(f"Errore durante l'esecuzione del giroconto: {e}")
    finally:
        if conn: conn.close()


def ottieni_transazioni_filtrate(id_conto_fk=None, data_inizio_str=None, data_fine_str=None, categoria=None, limit=None,
                                 offset=0):
    # Qui puoi aggiungere logica per convertire le stringhe di data in oggetti datetime se necessario
    # o validare i formati prima di passarli a database.get_transazioni_db
    return database.get_transazioni_db(id_conto_fk, data_inizio_str, data_fine_str, categoria, limit, offset)


def ottieni_transazione_singola(id_transazione):
    return database.get_transazione_by_id_db(id_transazione)


def modifica_transazione_esistente(id_transazione, id_conto_fk_nuovo, importo_nuovo_str, categoria_nuova,
                                   descrizione_nuova, data_trans_nuova_input, tags_nuovi_str=None,
                                   tipo_trans_nuovo=None, id_trans_collegata_nuova=None):
    try:
        importo_nuovo_float = float(importo_nuovo_str)
    except ValueError:
        raise ValueError("Nuovo importo non valido.")

    data_trans_db_str = None
    if isinstance(data_trans_nuova_input, str):
        try:
            dt_obj = datetime.strptime(data_trans_nuova_input, "%Y-%m-%d")
            data_trans_db_str = dt_obj.strftime("%Y-%m-%d") + " " + datetime.now().strftime(
                "%H:%M:%S")  # Aggiungi ora corrente
        except ValueError:
            try:
                datetime.strptime(data_trans_nuova_input, "%Y-%m-%d %H:%M:%S")
                data_trans_db_str = data_trans_nuova_input
            except ValueError:
                raise ValueError("Formato data per modifica non valido.")
    elif isinstance(data_trans_nuova_input, date):
        data_trans_db_str = data_trans_nuova_input.strftime("%Y-%m-%d") + " " + datetime.now().strftime("%H:%M:%S")
    else:
        raise ValueError("Tipo di data per modifica non supportato.")

    if not database.aggiorna_transazione_db(id_transazione, id_conto_fk_nuovo, importo_nuovo_float, categoria_nuova,
                                            descrizione_nuova, data_trans_db_str, tags_nuovi_str,
                                            tipo_trans_nuovo, id_trans_collegata_nuova):
        raise Exception(f"Impossibile aggiornare la transazione ID {id_transazione}.")
    return True


def elimina_transazione_esistente(id_transazione):
    if not database.elimina_transazione_db(id_transazione):
        raise Exception(f"Impossibile eliminare la transazione ID {id_transazione}.")
    return True


# --- Servizi di Correzione Saldo (dal vecchio gestione_conti.py, adattato) ---
def correggi_saldo_manuale(id_conto, nuovo_saldo_desiderato_str, data_correzione_input=None):
    conto = ottieni_conto_per_id(id_conto)
    if not conto:
        raise ValueError(f"Conto ID {id_conto} non trovato per la correzione del saldo.")

    try:
        nuovo_saldo_desiderato_float = float(nuovo_saldo_desiderato_str)
    except ValueError:
        raise ValueError("Il nuovo saldo desiderato deve essere un numero.")

    saldo_attuale_db = conto['saldo_attuale']  # Saldo letto dal DB
    differenza = nuovo_saldo_desiderato_float - saldo_attuale_db

    if abs(differenza) < 0.001:  # Tolleranza per errori floating point
        print(f"Nessuna correzione di saldo necessaria per '{conto['nome_conto']}'.")
        return True  # Nessuna operazione richiesta

    descrizione_corr = f"Correzione manuale saldo (da {saldo_attuale_db:.2f} a {nuovo_saldo_desiderato_float:.2f})"

    # La data per la transazione di correzione
    data_corr_db_str = None
    if isinstance(data_correzione_input, str):
        try:
            dt_obj = datetime.strptime(data_correzione_input, "%Y-%m-%d")
            data_corr_db_str = dt_obj.strftime("%Y-%m-%d") + " " + datetime.now().strftime("%H:%M:%S")
        except ValueError:
            try:
                datetime.strptime(data_correzione_input, "%Y-%m-%d %H:%M:%S")
                data_corr_db_str = data_correzione_input
            except ValueError:
                raise ValueError("Formato data correzione non valido.")
    elif isinstance(data_correzione_input, date):
        data_corr_db_str = data_correzione_input.strftime("%Y-%m-%d") + " " + datetime.now().strftime("%H:%M:%S")
    else:  # Se None, usa data corrente
        data_corr_db_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Registra la transazione di correzione. Questa aggiornerà il saldo_attuale in DB.
    id_trans_corr = database.registra_transazione_db(
        id_conto, differenza, "Correzione Saldo", descrizione_corr,
        data_transazione_str=data_corr_db_str, tipo_transazione="Correzione"
    )
    if id_trans_corr is None:
        raise Exception("Impossibile registrare la transazione di correzione saldo.")
    return True