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


# --- Servizi per Investimenti ---

def aggiungi_nuovo_investimento(nome_strumento, simbolo=None, tipo_asset=None,
                                quantita_str="0", pmc_unitario_str=None, costo_totale_carico_str=None,
                                valore_attuale_unitario_str=None, data_valore_attuale_input=None,
                                # Può essere str o datetime
                                id_conto_detenzione_fk=None, valuta="EUR",
                                data_primo_acquisto_input=None,  # Può essere str o datetime
                                note=None):
    if not nome_strumento or not nome_strumento.strip():
        raise ValueError("Nome strumento mancante.")
    if not tipo_asset or not tipo_asset.strip():
        raise ValueError("Tipo asset mancante.")

    try:
        quantita = float(quantita_str)
        if quantita < 0: raise ValueError("La quantità non può essere negativa.")
    except ValueError:
        raise ValueError("Quantità non valida.")

    pmc_unitario = None
    if pmc_unitario_str is not None and pmc_unitario_str.strip():
        try:
            pmc_unitario = float(pmc_unitario_str)
        except ValueError:
            raise ValueError("PMC unitario non valido.")

    costo_totale_carico = None
    if costo_totale_carico_str is not None and costo_totale_carico_str.strip():
        try:
            costo_totale_carico = float(costo_totale_carico_str)
        except ValueError:
            raise ValueError("Costo totale di carico non valido.")

    # Logica per derivare pmc o costo_totale se uno è mancante e l'altro c'è
    if quantita > 0:
        if pmc_unitario is not None and costo_totale_carico is None:
            costo_totale_carico = pmc_unitario * quantita
        elif costo_totale_carico is not None and pmc_unitario is None:
            pmc_unitario = costo_totale_carico / quantita
    elif quantita == 0 and (pmc_unitario is not None or costo_totale_carico is not None):
        # Se quantità è 0, PMC e costo carico dovrebbero essere 0 o None
        pmc_unitario = 0.0
        costo_totale_carico = 0.0

    val_attuale_unitario = None
    if valore_attuale_unitario_str is not None and valore_attuale_unitario_str.strip():
        try:
            val_attuale_unitario = float(valore_attuale_unitario_str)
        except ValueError:
            raise ValueError("Valore attuale unitario non valido.")

    data_val_attuale_db = None
    if data_valore_attuale_input:
        if isinstance(data_valore_attuale_input, str):
            try:
                data_val_attuale_db = datetime.strptime(data_valore_attuale_input, "%Y-%m-%d").strftime(
                    "%Y-%m-%d %H:%M:%S")  # Aggiunge ora default
            except ValueError:
                data_val_attuale_db = datetime.strptime(data_valore_attuale_input, "%Y-%m-%d %H:%M:%S").strftime(
                    "%Y-%m-%d %H:%M:%S")  # Già completo
        elif isinstance(data_valore_attuale_input, date):  # Oggetto date
            data_val_attuale_db = data_valore_attuale_input.strftime("%Y-%m-%d") + " " + datetime.now().strftime(
                "%H:%M:%S")
        else:  # Oggetto datetime
            data_val_attuale_db = data_valore_attuale_input.strftime("%Y-%m-%d %H:%M:%S")
    else:  # Se non fornita e c'è un valore attuale, usa oggi
        if val_attuale_unitario is not None:
            data_val_attuale_db = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    data_primo_acq_db = None
    if data_primo_acquisto_input:
        if isinstance(data_primo_acquisto_input, str):
            try:
                data_primo_acq_db = datetime.strptime(data_primo_acquisto_input, "%Y-%m-%d").strftime("%Y-%m-%d")
            except ValueError:
                raise ValueError("Formato data primo acquisto non valido (YYYY-MM-DD).")
        elif isinstance(data_primo_acquisto_input, date):
            data_primo_acq_db = data_primo_acquisto_input.strftime("%Y-%m-%d")
        else:  # datetime
            data_primo_acq_db = data_primo_acquisto_input.strftime("%Y-%m-%d")
    else:  # Data primo acquisto obbligatoria se si inserisce una posizione
        if quantita > 0 or costo_totale_carico is not None:  # O pmc_unitario
            data_primo_acq_db = datetime.now().strftime("%Y-%m-%d")  # Default a oggi
            # raise ValueError("Data primo acquisto mancante.")

    id_inv = database.aggiungi_investimento_db(
        nome_strumento.strip(), simbolo.strip() if simbolo else None, tipo_asset.strip(),
        quantita, pmc_unitario, costo_totale_carico,
        val_attuale_unitario, data_val_attuale_db,
        id_conto_detenzione_fk if id_conto_detenzione_fk else None,
        valuta.strip().upper(), data_primo_acq_db, note.strip() if note else None
    )
    if id_inv is None:
        raise Exception(f"Impossibile aggiungere l'investimento '{nome_strumento}'.")

    # Se è stato specificato un conto di detenzione e un costo, registra una transazione di uscita
    if id_conto_detenzione_fk and costo_totale_carico is not None and costo_totale_carico > 0:
        try:
            registra_nuova_transazione(  # La tua funzione esistente
                id_conto_fk=id_conto_detenzione_fk,
                importo_str=str(-costo_totale_carico),  # Uscita
                categoria="Investimenti",  # O una categoria più specifica
                descrizione=f"Acquisto: {quantita} di {nome_strumento}",
                data_transazione_input=data_primo_acq_db,  # Data dell'acquisto
                tipo_transazione="AcquistoInvestimento"
            )
        except Exception as e_trans:
            print(
                f"ATTENZIONE: Investimento ID {id_inv} creato, ma errore registrazione transazione di acquisto: {e_trans}")
            # Qui potresti voler annullare la creazione dell'investimento o loggare l'errore in modo più visibile

    return id_inv


def ottieni_tutti_gli_investimenti(solo_attivi=True):
    investimenti = database.get_tutti_gli_investimenti_db(solo_attivi)
    # Calcola P/L e valore totale attuale per ogni investimento
    for inv in investimenti:
        val_tot_attuale = 0
        pl_assoluto = 0
        pl_percentuale = 0
        costo_carico = inv.get('costo_totale_carico')
        qta = inv.get('quantita')
        val_unit_attuale = inv.get('valore_attuale_unitario')

        if qta is not None and qta > 0 and val_unit_attuale is not None:
            val_tot_attuale = qta * val_unit_attuale
            if costo_carico is not None and costo_carico > 0:  # Evita divisione per zero se costo_carico è 0
                pl_assoluto = val_tot_attuale - costo_carico
                pl_percentuale = (pl_assoluto / costo_carico) * 100
            elif costo_carico == 0 and val_tot_attuale > 0:  # Acquistato a zero, ora ha valore
                pl_assoluto = val_tot_attuale
                pl_percentuale = float('inf')  # O un valore molto alto, o non mostrare %
            # Se costo_carico è None ma c'è un PMC e quantità
            elif costo_carico is None and inv.get('pmc_unitario') is not None and qta > 0:
                costo_carico_calc = inv['pmc_unitario'] * qta
                if costo_carico_calc > 0:
                    pl_assoluto = val_tot_attuale - costo_carico_calc
                    pl_percentuale = (pl_assoluto / costo_carico_calc) * 100
                elif costo_carico_calc == 0 and val_tot_attuale > 0:
                    pl_assoluto = val_tot_attuale
                    pl_percentuale = float('inf')

        inv['valore_totale_attuale_calc'] = val_tot_attuale
        inv['pl_assoluto_calc'] = pl_assoluto
        inv['pl_percentuale_calc'] = pl_percentuale
    return investimenti


def ottieni_investimento_singolo(id_investimento):
    # Simile a ottieni_tutti_gli_investimenti ma per uno solo
    inv = database.get_investimento_by_id_db(id_investimento)
    if inv:
        # Calcola P/L come sopra
        val_tot_attuale = 0;
        pl_assoluto = 0;
        pl_percentuale = 0
        costo_carico = inv.get('costo_totale_carico')
        qta = inv.get('quantita')
        val_unit_attuale = inv.get('valore_attuale_unitario')
        if qta is not None and qta > 0 and val_unit_attuale is not None:
            val_tot_attuale = qta * val_unit_attuale
            if costo_carico is not None and costo_carico > 0:
                pl_assoluto = val_tot_attuale - costo_carico
                pl_percentuale = (pl_assoluto / costo_carico) * 100
            elif costo_carico == 0 and val_tot_attuale > 0:
                pl_assoluto = val_tot_attuale;
                pl_percentuale = float('inf')
            elif costo_carico is None and inv.get('pmc_unitario') is not None and qta > 0:
                costo_carico_calc = inv['pmc_unitario'] * qta
                if costo_carico_calc > 0:
                    pl_assoluto = val_tot_attuale - costo_carico_calc
                    pl_percentuale = (pl_assoluto / costo_carico_calc) * 100
                elif costo_carico_calc == 0 and val_tot_attuale > 0:
                    pl_assoluto = val_tot_attuale;
                    pl_percentuale = float('inf')

        inv['valore_totale_attuale_calc'] = val_tot_attuale
        inv['pl_assoluto_calc'] = pl_assoluto
        inv['pl_percentuale_calc'] = pl_percentuale
    return inv


def aggiorna_valore_investimento(id_investimento, nuovo_valore_unitario_str, data_valore_input=None):
    try:
        nuovo_valore = float(nuovo_valore_unitario_str)
    except ValueError:
        raise ValueError("Nuovo valore unitario non valido.")

    data_val_db = None
    if data_valore_input:
        if isinstance(data_valore_input, str):
            try:
                data_val_db = datetime.strptime(data_valore_input, "%Y-%m-%d").strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                data_val_db = datetime.strptime(data_valore_input, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(data_valore_input, date):
            data_val_db = data_valore_input.strftime("%Y-%m-%d") + " " + datetime.now().strftime("%H:%M:%S")
        else:  # datetime
            data_val_db = data_valore_input.strftime("%Y-%m-%d %H:%M:%S")
    else:
        data_val_db = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not database.aggiorna_valore_corrente_investimento_db(id_investimento, nuovo_valore, data_val_db):
        raise Exception(f"Impossibile aggiornare il valore dell'investimento ID {id_investimento}.")
    return True


def registra_acquisto_aggiuntivo(id_investimento, quantita_acquistata_str, prezzo_acquisto_unitario_str,
                                 commissioni_str="0.0", data_acquisto_input=None,
                                 id_conto_pagamento_fk=None):
    """
    Registra un acquisto aggiuntivo per un investimento esistente.
    Aggiorna la quantità, ricalcola il PMC e il costo totale di carico.
    Registra una transazione di uscita dal conto di pagamento, se specificato.
    """
    investimento_esistente = ottieni_investimento_singolo(id_investimento)
    if not investimento_esistente:
        raise ValueError(f"Investimento ID {id_investimento} non trovato.")

    try:
        quantita_acq = float(quantita_acquistata_str)
        prezzo_acq_unit = float(prezzo_acquisto_unitario_str)
        commissioni_acq = float(commissioni_str)
        if quantita_acq <= 0: raise ValueError("La quantità acquistata deve essere positiva.")
        if prezzo_acq_unit < 0: raise ValueError("Il prezzo di acquisto non può essere negativo.")  # 0 è ok
        if commissioni_acq < 0: raise ValueError("Le commissioni non possono essere negative.")
    except ValueError:
        raise ValueError("Quantità, prezzo o commissioni non validi.")

    data_acq_db_str = None
    if isinstance(data_acquisto_input, str) and data_acquisto_input.strip():
        try:
            dt_obj = datetime.strptime(data_acquisto_input, "%Y-%m-%d")
            data_acq_db_str = dt_obj.strftime("%Y-%m-%d") + " " + datetime.now().strftime("%H:%M:%S")
        except ValueError:
            try:
                datetime.strptime(data_acquisto_input, "%Y-%m-%d %H:%M:%S")
                data_acq_db_str = data_acquisto_input
            except ValueError:
                raise ValueError("Formato data acquisto non valido.")
    elif isinstance(data_acquisto_input, date):
        data_acq_db_str = data_acquisto_input.strftime("%Y-%m-%d") + " " + datetime.now().strftime("%H:%M:%S")
    else:  # Se None o altro, usa data corrente
        data_acq_db_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Calcolo nuovo stato della posizione
    costo_questo_acquisto = (quantita_acq * prezzo_acq_unit) + commissioni_acq

    quantita_precedente = float(investimento_esistente.get('quantita', 0.0))
    costo_totale_carico_precedente = float(investimento_esistente.get('costo_totale_carico', 0.0))

    # Se pmc_unitario non è memorizzato o è None, e costo_totale_carico_precedente è 0 ma quantità non lo è,
    # allora pmc_unitario_precedente potrebbe essere 0. In questo caso, il nuovo pmc sarà semplicemente prezzo_acq_unit
    # se la quantità precedente era 0.
    pmc_unitario_precedente = float(investimento_esistente.get('pmc_unitario', 0.0))
    if quantita_precedente == 0 and costo_totale_carico_precedente == 0:
        # Questo è effettivamente il primo lotto significativo, o la posizione era a zero
        pmc_unitario_precedente = 0  # Resetta per evitare calcoli errati se era None

    nuova_quantita_totale = quantita_precedente + quantita_acq
    nuovo_costo_totale_carico = costo_totale_carico_precedente + costo_questo_acquisto

    nuovo_pmc_unitario = 0
    if nuova_quantita_totale > 0:
        nuovo_pmc_unitario = nuovo_costo_totale_carico / nuova_quantita_totale
    else:  # Caso strano, ma per sicurezza
        nuovo_pmc_unitario = 0
        nuovo_costo_totale_carico = 0

    # Aggiorna il record dell'investimento nel DB
    if not database.aggiorna_posizione_investimento_db(id_investimento, nuova_quantita_totale, nuovo_pmc_unitario,
                                                       nuovo_costo_totale_carico):
        raise Exception(f"Impossibile aggiornare la posizione dell'investimento ID {id_investimento} nel database.")

    # Registra transazione di uscita dal conto di pagamento, se specificato
    if id_conto_pagamento_fk and costo_questo_acquisto > 0:
        try:
            registra_nuova_transazione(  # La tua funzione esistente
                id_conto_fk=id_conto_pagamento_fk,
                importo_str=str(-costo_questo_acquisto),  # Uscita
                categoria="Investimenti",
                descrizione=f"Acquisto: {quantita_acq} {investimento_esistente['nome_strumento']} @{prezzo_acq_unit:.2f}",
                data_transazione_input=data_acq_db_str,
                tipo_transazione="AcquistoInvestimento"
            )
        except Exception as e_trans:
            # Questo è un problema: l'investimento è stato aggiornato ma la transazione di cassa no.
            # Idealmente, tutto questo dovrebbe essere in una transazione DB più ampia,
            # o dovresti avere una logica di compensazione/rollback.
            # Per ora, stampiamo un avviso critico.
            print(f"ERRORE CRITICO: Posizione investimento ID {id_investimento} aggiornata, "
                  f"ma fallita registrazione transazione di cassa: {e_trans}")
            # Potresti voler sollevare un'eccezione qui per segnalare l'incoerenza.
            raise Exception(
                f"Incoerenza dati: investimento aggiornato ma transazione cassa fallita. Dettagli: {e_trans}")

    print(f"Acquisto aggiuntivo registrato per investimento ID {id_investimento}. Nuovo PMC: {nuovo_pmc_unitario:.2f}")
    return True


def registra_vendita_investimento(id_investimento, quantita_venduta_str, prezzo_vendita_unitario_str,
                                  commissioni_str="0.0", data_vendita_input=None,
                                  id_conto_accredito_fk=None):
    """
    Registra una vendita (parziale o totale) per un investimento esistente.
    Calcola il P/L della vendita, aggiorna la quantità e il costo di carico rimanente.
    Se la quantità va a zero, marca l'investimento come inattivo.
    Registra una transazione di entrata sul conto di accredito, se specificato.
    """
    investimento_esistente = ottieni_investimento_singolo(id_investimento)
    if not investimento_esistente:
        raise ValueError(f"Investimento ID {id_investimento} non trovato.")
    if not investimento_esistente.get('attivo', False):  # Deve essere attivo per essere venduto
        raise ValueError(f"L'investimento '{investimento_esistente['nome_strumento']}' è già chiuso/inattivo.")

    try:
        quantita_vend = float(quantita_venduta_str)
        prezzo_vend_unit = float(prezzo_vendita_unitario_str)
        commissioni_vend = float(commissioni_str)
        if quantita_vend <= 0: raise ValueError("La quantità venduta deve essere positiva.")
        if prezzo_vend_unit < 0: raise ValueError("Il prezzo di vendita non può essere negativo.")
        if commissioni_vend < 0: raise ValueError("Le commissioni non possono essere negative.")
    except ValueError:
        raise ValueError("Quantità, prezzo o commissioni di vendita non validi.")

    quantita_attuale = float(investimento_esistente['quantita'])
    if quantita_vend > quantita_attuale:
        raise ValueError(f"Quantità venduta ({quantita_vend}) supera la quantità disponibile ({quantita_attuale}).")

    data_vend_db_str = None
    if isinstance(data_vendita_input, str) and data_vendita_input.strip():
        try:
            dt_obj = datetime.strptime(data_vendita_input, "%Y-%m-%d")
            data_vend_db_str = dt_obj.strftime("%Y-%m-%d") + " " + datetime.now().strftime("%H:%M:%S")
        except ValueError:
            try:
                datetime.strptime(data_vendita_input, "%Y-%m-%d %H:%M:%S")
                data_vend_db_str = data_vendita_input
            except ValueError:
                raise ValueError("Formato data vendita non valido.")
    elif isinstance(data_vendita_input, date):
        data_vend_db_str = data_vendita_input.strftime("%Y-%m-%d") + " " + datetime.now().strftime("%H:%M:%S")
    else:
        data_vend_db_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Calcoli per la vendita
    ricavo_lordo_vendita = quantita_vend * prezzo_vend_unit
    ricavo_netto_vendita = ricavo_lordo_vendita - commissioni_vend

    pmc_unitario_attuale = float(investimento_esistente.get('pmc_unitario', 0.0))
    # Se pmc_unitario è 0 o None, e c'è costo_totale_carico, ricalcolalo.
    if pmc_unitario_attuale == 0 and investimento_esistente.get('costo_totale_carico') and quantita_attuale > 0:
        pmc_unitario_attuale = float(investimento_esistente['costo_totale_carico']) / quantita_attuale

    costo_del_venduto = quantita_vend * pmc_unitario_attuale
    profit_loss_vendita = ricavo_netto_vendita - costo_del_venduto

    # Aggiornamento della posizione rimanente
    nuova_quantita_rimanente = quantita_attuale - quantita_vend
    nuovo_costo_totale_carico_rimanente = 0
    nuovo_pmc_unitario_rimanente = pmc_unitario_attuale  # Il PMC non cambia con una vendita parziale (metodo del costo medio)

    if nuova_quantita_rimanente > 0.000001:  # Uso una piccola tolleranza per float
        # Il costo totale di carico della posizione rimanente è proporzionale
        costo_totale_carico_attuale = float(
            investimento_esistente.get('costo_totale_carico', pmc_unitario_attuale * quantita_attuale))
        nuovo_costo_totale_carico_rimanente = costo_totale_carico_attuale - costo_del_venduto
        # Ricalcola il PMC per la posizione rimanente per sicurezza, anche se dovrebbe rimanere uguale
        if nuovo_costo_totale_carico_rimanente > 0:
            nuovo_pmc_unitario_rimanente = nuovo_costo_totale_carico_rimanente / nuova_quantita_rimanente
        else:  # Se il costo rimanente è zero o negativo (strano), pmc è zero
            nuovo_pmc_unitario_rimanente = 0

    else:  # Venduto tutto o quasi (considera 0 se sotto una soglia minima)
        nuova_quantita_rimanente = 0
        nuovo_pmc_unitario_rimanente = 0
        nuovo_costo_totale_carico_rimanente = 0

    # Aggiorna il record dell'investimento nel DB
    if not database.aggiorna_posizione_investimento_db(id_investimento, nuova_quantita_rimanente,
                                                       nuovo_pmc_unitario_rimanente,
                                                       nuovo_costo_totale_carico_rimanente):
        raise Exception(f"Impossibile aggiornare la posizione dell'investimento ID {id_investimento} dopo la vendita.")

    # Se la quantità è zero, marca l'investimento come inattivo
    if nuova_quantita_rimanente == 0:
        if not database.imposta_stato_investimento_db(id_investimento, attivo=False):
            # Non fatale, ma da loggare
            print(
                f"ATTENZIONE: Vendita totale per investimento ID {id_investimento}, ma fallita impostazione a inattivo.")

    # Registra transazione di entrata sul conto di accredito, se specificato
    if id_conto_accredito_fk and ricavo_netto_vendita != 0:  # !=0 per gestire vendite a zero o con commissioni che azzerano
        try:
            desc_trans_vendita = f"Vendita: {quantita_vend} {investimento_esistente['nome_strumento']} @{prezzo_vend_unit:.2f}. P/L: {profit_loss_vendita:.2f}"
            registra_nuova_transazione(
                id_conto_fk=id_conto_accredito_fk,
                importo_str=str(ricavo_netto_vendita),  # Entrata
                categoria="Investimenti",  # O "Plusvalenza/Minusvalenza" o "Ricavi da Vendita"
                descrizione=desc_trans_vendita,
                data_transazione_input=data_vend_db_str,
                tipo_transazione="VenditaInvestimento"
            )
        except Exception as e_trans:
            print(f"ERRORE CRITICO: Posizione investimento ID {id_investimento} aggiornata per vendita, "
                  f"ma fallita registrazione transazione di cassa: {e_trans}")
            raise Exception(
                f"Incoerenza dati: investimento aggiornato per vendita ma transazione cassa fallita. Dettagli: {e_trans}")

    print(
        f"Vendita registrata per investimento ID {id_investimento}. P/L: {profit_loss_vendita:.2f}. Q.tà rimasta: {nuova_quantita_rimanente}")
    return {"profit_loss": profit_loss_vendita, "quantita_rimanente": nuova_quantita_rimanente}

def modifica_dati_investimento(id_investimento, nome_nuovo, simbolo_nuovo, tipo_nuovo, valuta_nuova, note_nuove,
                               data_acquisto_nuova_input=None):
    # Validazione
    if not nome_nuovo or not nome_nuovo.strip(): raise ValueError("Nome strumento mancante.")
    if not tipo_nuovo or not tipo_nuovo.strip(): raise ValueError("Tipo asset mancante.")

    data_acq_db = None
    if data_acquisto_nuova_input:
        if isinstance(data_acquisto_nuova_input, str):
            try:
                data_acq_db = datetime.strptime(data_acquisto_nuova_input, "%Y-%m-%d").strftime("%Y-%m-%d")
            except ValueError:
                raise ValueError("Formato data primo acquisto non valido (YYYY-MM-DD).")
        elif isinstance(data_acquisto_nuova_input, (date, datetime)):
            data_acq_db = data_acquisto_nuova_input.strftime("%Y-%m-%d")
        else:
            raise ValueError("Tipo data primo acquisto non valido.")

    if not database.aggiorna_dettagli_investimento_db(id_investimento, nome_nuovo.strip(),
                                                      simbolo_nuovo.strip() if simbolo_nuovo else None,
                                                      tipo_nuovo.strip(), valuta_nuova.strip().upper(),
                                                      note_nuove.strip() if note_nuove else None,
                                                      data_acq_db):
        raise Exception(f"Impossibile aggiornare i dettagli dell'investimento ID {id_investimento}.")
    return True


def chiudi_posizione_investimento(id_investimento):  # Marca come inattivo
    if not database.imposta_stato_investimento_db(id_investimento, attivo=False):
        raise Exception(f"Impossibile chiudere la posizione dell'investimento ID {id_investimento}.")
    # Qui dovresti anche gestire la logica di vendita finale se non già fatta.
    # Per esempio, se chiudi una posizione, il suo valore attuale e quantità potrebbero andare a zero.
    # O potresti creare una transazione di "vendita finale" che azzera la quantità.
    # Dipende da come vuoi gestire lo storico di una posizione chiusa.
    # Per ora, lo marca solo come inattivo.
    return True