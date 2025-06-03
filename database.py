import sqlite3
import os
from datetime import datetime

# --- Configurazioni Database ---
DATA_DIR = "data"
DB_FILENAME = "cato_finance.db"
DB_PATH = os.path.join(DATA_DIR, DB_FILENAME)


# --- Funzioni di Connessione e Setup ---
def get_db_connection():
    """
    Stabilisce e restituisce una connessione al database SQLite.
    Crea la directory dei dati se non esiste.
    Configura row_factory per accedere alle colonne per nome.
    """
    os.makedirs(DATA_DIR, exist_ok=True)  # Crea la directory 'data' se non esiste
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Permette di accedere ai risultati come dizionari (o oggetti simili)
    conn.execute("PRAGMA foreign_keys = ON;")  # Abilita il supporto per le foreign key (importante!)
    return conn


def initialize_database():
    """
    Crea le tabelle del database ('conti' e 'transazioni') se non esistono già.
    Questa funzione dovrebbe essere chiamata una volta all'avvio dell'applicazione.
    """
    print(f"Inizializzazione database a: {DB_PATH}")
    conn = None  # Inizializza conn a None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Tabella Conti
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conti (
                id_conto INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_conto TEXT NOT NULL UNIQUE,
                saldo_attuale REAL NOT NULL DEFAULT 0.0,
                tipo_conto TEXT, 
                valuta TEXT DEFAULT 'EUR',
                data_creazione TEXT NOT NULL,
                attivo INTEGER DEFAULT 1 CHECK(attivo IN (0, 1))
            )
        ''')
        print("Tabella 'conti' verificata/creata.")

        # Tabella Transazioni
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transazioni (
                id_transazione INTEGER PRIMARY KEY AUTOINCREMENT,
                id_conto_fk INTEGER NOT NULL,
                data_transazione TEXT NOT NULL, -- Formato ISO: "YYYY-MM-DD HH:MM:SS"
                descrizione TEXT,
                importo REAL NOT NULL,
                categoria TEXT,
                tags TEXT, -- Per ora una stringa, es. "vacanza,regalo,figli"
                tipo_transazione TEXT, -- Es. 'Entrata', 'Uscita', 'Giroconto_Out', 'Giroconto_In', 'SaldoIniziale', 'Correzione'
                id_transazione_collegata INTEGER, -- Per collegare le due parti di un giroconto
                FOREIGN KEY (id_conto_fk) REFERENCES conti (id_conto) ON DELETE RESTRICT ON UPDATE CASCADE
                -- ON DELETE RESTRICT: impedisce di cancellare un conto se ha transazioni
                -- ON UPDATE CASCADE: se id_conto cambia (raro con AUTOINCREMENT), aggiorna anche qui
            )
        ''')
        print("Tabella 'transazioni' verificata/creata.")

        cursor.execute('''
                CREATE TABLE IF NOT EXISTS investimenti (
                    id_investimento INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome_strumento TEXT NOT NULL, -- Es. "Azioni Apple Inc.", "ETF Vanguard S&P 500"
                    simbolo TEXT,                 -- Es. "AAPL", "VOO" (Opzionale, ma utile per fetch prezzi)
                    tipo_asset TEXT NOT NULL,     -- Es. "Azione", "ETF", "Obbligazione", "Fondo Comune", "Criptovaluta", "Immobiliare", "Altro"
                    quantita REAL NOT NULL DEFAULT 0.0,
                    pmc_unitario REAL,            -- Prezzo Medio di Carico unitario (costo medio per azione/quota)
                    costo_totale_carico REAL,     -- Costo totale per acquisire la posizione attuale (quantita * pmc + commissioni totali)
                                                  -- Potrebbe essere ricalcolato o memorizzato
                    valore_attuale_unitario REAL, -- Valore corrente di una singola unità (aggiornato manualmente o via API)
                    data_valore_attuale TEXT,     -- Data dell'ultimo aggiornamento del valore_attuale_unitario
                    id_conto_detenzione_fk INTEGER, -- Opzionale: Conto da cui sono stati prelevati i fondi o dove è depositato lo strumento
                                                  -- Può essere NULL se non si vuole collegare a un conto di cassa specifico
                    valuta TEXT DEFAULT 'EUR',
                    data_primo_acquisto TEXT,     -- Data del primo acquisto per questo strumento
                    data_ultima_modifica TEXT NOT NULL, -- Data dell'ultima modifica a questo record (acquisto, vendita, aggiornamento valore)
                    note TEXT,
                    attivo INTEGER DEFAULT 1 CHECK(attivo IN (0, 1)), -- 1 se la posizione è ancora aperta, 0 se chiusa
                    FOREIGN KEY (id_conto_detenzione_fk) REFERENCES conti (id_conto) ON DELETE SET NULL ON UPDATE CASCADE
                    -- ON DELETE SET NULL: se il conto di detenzione viene cancellato, l'investimento non viene cancellato ma perde il collegamento
                )
            ''')
        print("Tabella 'investimenti' verificata/creata.")

        # Indici per la tabella investimenti
        cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_investimenti_nome 
                ON investimenti (nome_strumento)
            ''')
        cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_investimenti_tipo_asset
                ON investimenti (tipo_asset)
            ''')
        print("Indici per 'investimenti' verificati/creati.")

        # Indici per migliorare le performance delle query
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_transazioni_data 
            ON transazioni (data_transazione DESC)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_transazioni_id_conto_fk 
            ON transazioni (id_conto_fk)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_conti_nome
            ON conti (nome_conto)
        ''')
        print("Indici verificati/creati.")

        conn.commit()
        print("Database inizializzato con successo.")

    except sqlite3.Error as e:
        print(f"Errore durante l'inizializzazione del database SQLite: {e}")
        if conn:
            conn.rollback()  # Annulla le modifiche in caso di errore
    finally:
        if conn:
            conn.close()



# --- Funzioni CRUD per Conti ---

def aggiungi_conto_db(nome_conto, saldo_iniziale=0.0, tipo_conto=None, valuta='EUR'):
    """
    Aggiunge un nuovo conto al database.
    Se saldo_iniziale è diverso da zero, registra anche una transazione di "SaldoIniziale".
    Restituisce l'ID del conto appena creato o None in caso di errore.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        data_creazione_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("BEGIN TRANSACTION")

        cursor.execute('''
            INSERT INTO conti (nome_conto, saldo_attuale, tipo_conto, valuta, data_creazione, attivo)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', (nome_conto, float(saldo_iniziale), tipo_conto, valuta, data_creazione_str))
        id_nuovo_conto = cursor.lastrowid

        if float(saldo_iniziale) != 0 and id_nuovo_conto is not None:
            # La transazione di saldo iniziale NON deve modificare ulteriormente il saldo del conto
            # perché lo abbiamo già impostato con saldo_iniziale.
            # La funzione registra_transazione_db dovrà tenerne conto.
            # Oppure, non aggiorniamo saldo_attuale qui e lo facciamo fare solo da registra_transazione_db.
            # Per coerenza, facciamo che registra_transazione_db aggiorna sempre il saldo,
            # quindi il saldo_attuale nella tabella conti è sempre la "verità".
            # Quando si aggiunge un conto con saldo iniziale, il saldo_attuale è già quello.
            # La transazione di SaldoIniziale serve solo per tracciabilità.

            # Modifichiamo l'approccio: il saldo del conto è la somma delle sue transazioni.
            # Ma per semplicità iniziale, manteniamo saldo_attuale in conti e lo aggiorniamo.
            # La transazione "SaldoIniziale" non dovrebbe causare un doppio conteggio.
            # Una soluzione è che registra_transazione_db NON aggiorni il saldo se tipo=="SaldoIniziale".
            # Per ora, per semplicità, la transazione SaldoIniziale NON modifica il saldo_attuale
            # perché è già stato impostato alla creazione del conto.
            # La sua registrazione è puramente per lo storico.

            # Semplifichiamo: il saldo_attuale è la verità, la transazione è solo storica.
            # Non c'è bisogno di chiamare registra_transazione_db qui se la logica di aggiornamento saldo è separata.
            # Però, per avere traccia, inseriamo una transazione di tipo SaldoIniziale.
            # Questa transazione non deve modificare il saldo_attuale della tabella conti
            # perché è già stato impostato.
            # Assumiamo che registra_transazione_db non aggiorni il saldo_attuale per tipo "SaldoIniziale"

            # Se il saldo iniziale è != 0, creiamo una transazione fittizia di tipo SaldoIniziale
            # ma non chiamiamo registra_transazione_db completa che aggiornerebbe di nuovo il saldo
            cursor.execute('''
                INSERT INTO transazioni (id_conto_fk, data_transazione, descrizione, importo, categoria, tipo_transazione)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
            id_nuovo_conto, data_creazione_str, "Saldo iniziale", float(saldo_iniziale), "Sistema", "SaldoIniziale"))

        conn.commit()
        print(f"Conto '{nome_conto}' aggiunto con ID: {id_nuovo_conto}, saldo: {saldo_iniziale}")
        return id_nuovo_conto
    except sqlite3.IntegrityError:
        print(f"Errore DB: Il conto '{nome_conto}' esiste già o un altro vincolo è stato violato.")
        if conn: conn.rollback()
        return None
    except ValueError:
        print(f"Errore Valore: saldo_iniziale '{saldo_iniziale}' non è un numero valido.")
        if conn: conn.rollback()
        return None
    except Exception as e:
        print(f"Errore imprevisto durante l'aggiunta del conto '{nome_conto}': {e}")
        if conn: conn.rollback()
        return None
    finally:
        if conn: conn.close()


def get_conto_by_id_db(id_conto):
    """Recupera un conto specifico per ID."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM conti WHERE id_conto = ?", (id_conto,))
        conto = cursor.fetchone()  # Restituisce una riga (sqlite3.Row) o None
        return dict(conto) if conto else None  # Converti in dizionario se trovato
    except Exception as e:
        print(f"Errore durante il recupero del conto ID {id_conto}: {e}")
        return None
    finally:
        if conn: conn.close()


def get_conto_by_nome_db(nome_conto):
    """Recupera un conto specifico per nome."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM conti WHERE nome_conto = ?", (nome_conto,))
        conto = cursor.fetchone()
        return dict(conto) if conto else None
    except Exception as e:
        print(f"Errore durante il recupero del conto '{nome_conto}': {e}")
        return None
    finally:
        if conn: conn.close()


def get_tutti_i_conti_db(solo_attivi=True):
    """Recupera tutti i conti, opzionalmente solo quelli attivi."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM conti"
        if solo_attivi:
            query += " WHERE attivo = 1"
        query += " ORDER BY nome_conto"
        cursor.execute(query)
        conti = cursor.fetchall()  # Lista di righe (sqlite3.Row)
        return [dict(conto) for conto in conti]  # Converti ogni riga in dizionario
    except Exception as e:
        print(f"Errore durante il recupero di tutti i conti: {e}")
        return []
    finally:
        if conn: conn.close()


def aggiorna_nome_conto_db(id_conto, nuovo_nome_conto):
    """Aggiorna il nome di un conto esistente."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE conti SET nome_conto = ? WHERE id_conto = ?", (nuovo_nome_conto, id_conto))
        conn.commit()
        return cursor.rowcount > 0  # True se almeno una riga è stata aggiornata
    except sqlite3.IntegrityError:
        print(f"Errore DB: Il nome '{nuovo_nome_conto}' è già in uso o altro vincolo violato.")
        if conn: conn.rollback()
        return False
    except Exception as e:
        print(f"Errore durante l'aggiornamento del nome del conto ID {id_conto}: {e}")
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()


def aggiorna_saldo_conto_direttamente_db(id_conto, variazione_importo):
    """
    Aggiorna direttamente il saldo_attuale di un conto.
    Usato da registra_transazione_db.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE conti SET saldo_attuale = saldo_attuale + ? 
            WHERE id_conto = ?
        ''', (float(variazione_importo), id_conto))
        conn.commit()
        return cursor.rowcount > 0
    except ValueError:
        print(
            f"Errore Valore: variazione_importo '{variazione_importo}' non è un numero valido per aggiornare il saldo del conto ID {id_conto}.")
        if conn: conn.rollback()  # Anche se qui non fa molto perché non è in una BEGIN/COMMIT esterna
        return False
    except Exception as e:
        print(f"Errore durante l'aggiornamento diretto del saldo del conto ID {id_conto}: {e}")
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()


def imposta_stato_conto_db(id_conto, attivo=True):
    """Imposta lo stato (attivo/inattivo) di un conto."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        stato = 1 if attivo else 0
        cursor.execute("UPDATE conti SET attivo = ? WHERE id_conto = ?", (stato, id_conto))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Errore durante l'impostazione dello stato del conto ID {id_conto}: {e}")
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()


def elimina_conto_db(id_conto):
    """
    Elimina un conto dal database.
    Fallirà se ON DELETE RESTRICT è attivo e ci sono transazioni collegate.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM conti WHERE id_conto = ?", (id_conto,))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"Conto ID {id_conto} eliminato con successo.")
            return True
        else:
            print(f"Nessun conto trovato con ID {id_conto} per l'eliminazione.")
            return False
    except sqlite3.IntegrityError as e:
        # Questo errore scatta a causa di ON DELETE RESTRICT se ci sono transazioni
        print(
            f"Errore di integrità durante l'eliminazione del conto ID {id_conto}: {e}. Probabilmente ha transazioni associate.")
        if conn: conn.rollback()
        return False
    except Exception as e:
        print(f"Errore imprevisto durante l'eliminazione del conto ID {id_conto}: {e}")
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()


# --- Funzioni CRUD per Transazioni ---

def registra_transazione_db(id_conto_fk, importo, categoria, descrizione,
                            data_transazione_str=None, tags=None, tipo_transazione=None,
                            id_transazione_collegata=None):
    """
    Registra una nuova transazione nel database e aggiorna il saldo del conto.
    Restituisce l'ID della transazione appena creata o None in caso di errore.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if data_transazione_str is None:
            data_transazione_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(data_transazione_str, datetime):
            data_transazione_str = data_transazione_str.strftime("%Y-%m-%d %H:%M:%S")

        importo_float = float(importo)  # Converte in float, solleva ValueError se non possibile

        cursor.execute("BEGIN TRANSACTION")  # Inizia transazione atomica

        cursor.execute('''
            INSERT INTO transazioni (id_conto_fk, data_transazione, descrizione, importo, categoria, tags, tipo_transazione, id_transazione_collegata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (id_conto_fk, data_transazione_str, descrizione, importo_float, categoria, tags, tipo_transazione,
              id_transazione_collegata))
        id_nuova_transazione = cursor.lastrowid

        # Aggiorna il saldo del conto SOLO se non è una transazione di tipo "SaldoIniziale"
        # perché il saldo iniziale è già gestito alla creazione del conto.
        if tipo_transazione != "SaldoIniziale":
            cursor.execute('''
                UPDATE conti SET saldo_attuale = saldo_attuale + ? 
                WHERE id_conto = ?
            ''', (importo_float, id_conto_fk))
            if cursor.rowcount == 0:
                raise Exception(f"Conto ID {id_conto_fk} non trovato per aggiornamento saldo.")

        conn.commit()  # Conferma entrambe le operazioni (INSERT transazione e UPDATE conto)
        print(f"Transazione ID {id_nuova_transazione} registrata per conto ID {id_conto_fk}.")
        return id_nuova_transazione
    except ValueError:  # Errore nella conversione dell'importo
        print(f"Errore Valore: importo '{importo}' non valido per la transazione.")
        if conn: conn.rollback()
        return None
    except Exception as e:
        print(f"Errore durante la registrazione della transazione: {e}")
        if conn: conn.rollback()
        return None
    finally:
        if conn: conn.close()


def get_transazioni_db(id_conto_fk=None, data_inizio=None, data_fine=None, categoria=None, limit=None, offset=0):
    """
    Recupera transazioni con filtri opzionali.
    data_inizio e data_fine devono essere stringhe "YYYY-MM-DD" o datetime objects.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        params = []
        query = '''
            SELECT t.*, c.nome_conto 
            FROM transazioni t
            JOIN conti c ON t.id_conto_fk = c.id_conto
        '''
        conditions = []

        if id_conto_fk is not None:
            conditions.append("t.id_conto_fk = ?")
            params.append(id_conto_fk)

        if data_inizio:
            if isinstance(data_inizio, datetime): data_inizio = data_inizio.strftime("%Y-%m-%d")
            conditions.append("date(t.data_transazione) >= date(?)")  # Compara solo la parte data
            params.append(data_inizio)

        if data_fine:
            if isinstance(data_fine, datetime): data_fine = data_fine.strftime("%Y-%m-%d")
            conditions.append("date(t.data_transazione) <= date(?)")
            params.append(data_fine)

        if categoria:
            conditions.append("t.categoria LIKE ?")  # Usiamo LIKE per ricerche parziali
            params.append(f"%{categoria}%")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY t.data_transazione DESC, t.id_transazione DESC"  # Ordina per data e poi ID

        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params.append(limit)
            params.append(offset)

        cursor.execute(query, params)
        transazioni = cursor.fetchall()
        return [dict(tr) for tr in transazioni]
    except Exception as e:
        print(f"Errore durante il recupero delle transazioni: {e}")
        return []
    finally:
        if conn: conn.close()


def get_transazione_by_id_db(id_transazione):
    """Recupera una transazione specifica per ID."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT t.*, c.nome_conto 
            FROM transazioni t
            JOIN conti c ON t.id_conto_fk = c.id_conto
            WHERE t.id_transazione = ?
        ''', (id_transazione,))
        transazione = cursor.fetchone()
        return dict(transazione) if transazione else None
    except Exception as e:
        print(f"Errore recupero transazione ID {id_transazione}: {e}")
        return None
    finally:
        if conn: conn.close()


def aggiorna_transazione_db(id_transazione, id_conto_fk_nuovo, importo_nuovo, categoria_nuova,
                            descrizione_nuova, data_transazione_nuova_str,
                            tags_nuovi=None,
                            tipo_transazione_nuovo=None,
                            id_transazione_collegata_nuova=None):
    """
    Aggiorna una transazione esistente.
    Questa è la funzione più complessa perché richiede di stornare il vecchio importo dal vecchio conto,
    e applicare il nuovo importo al nuovo (o stesso) conto.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Ottieni i dettagli della vecchia transazione
        # Recuperiamo anche il tipo, nel caso servisse per logiche future
        cursor.execute("SELECT id_conto_fk, importo, tipo_transazione FROM transazioni WHERE id_transazione = ?",
                       (id_transazione,))
        vecchia_trans_dati = cursor.fetchone()
        if not vecchia_trans_dati:
            raise ValueError(f"Transazione ID {id_transazione} non trovata.")

        id_conto_fk_vecchio = vecchia_trans_dati["id_conto_fk"]
        importo_vecchio = float(vecchia_trans_dati["importo"])
        # tipo_transazione_vecchio = vecchia_trans_dati["tipo_transazione"] # Non usato attivamente ora, ma utile averlo

        importo_nuovo_float = float(importo_nuovo)  # Solleva ValueError se non è un numero

        # Se il tipo_transazione originale era "SaldoIniziale", non dovrebbe essere modificato in modo da alterare il saldo.
        # Una transazione di SaldoIniziale, se modificata, dovrebbe probabilmente solo cambiare descrizione o data,
        # o essere eliminata e ricreata. Modificarne l'importo o il conto richiede attenzione.
        # Per ora, permettiamo la modifica, ma la logica di storno/applicazione saldi deve essere corretta.

        cursor.execute("BEGIN TRANSACTION")

        # 2. Storna l'effetto della vecchia transazione dal saldo del vecchio conto
        # SOLO se la vecchia transazione non era di tipo "SaldoIniziale"
        # (perché il SaldoIniziale non ha modificato il saldo del conto al momento della sua creazione)
        if vecchia_trans_dati["tipo_transazione"] != "SaldoIniziale":
            cursor.execute("UPDATE conti SET saldo_attuale = saldo_attuale - ? WHERE id_conto = ?",
                           (importo_vecchio, id_conto_fk_vecchio))

        # 3. Aggiorna la transazione con i nuovi dati
        cursor.execute('''
            UPDATE transazioni SET 
                id_conto_fk = ?, importo = ?, categoria = ?, descrizione = ?, 
                data_transazione = ?, tags = ?, tipo_transazione = ?, id_transazione_collegata = ?
            WHERE id_transazione = ?
        ''', (id_conto_fk_nuovo, importo_nuovo_float, categoria_nuova, descrizione_nuova,
              data_transazione_nuova_str, tags_nuovi, tipo_transazione_nuovo,
              id_transazione_collegata_nuova, id_transazione))

        # 4. Applica l'effetto della nuova transazione (con i nuovi dati) al saldo del nuovo (o stesso) conto
        # SOLO se la nuova transazione (o quella modificata) non è di tipo "SaldoIniziale"
        if tipo_transazione_nuovo != "SaldoIniziale":
            cursor.execute("UPDATE conti SET saldo_attuale = saldo_attuale + ? WHERE id_conto = ?",
                           (importo_nuovo_float, id_conto_fk_nuovo))
            if cursor.rowcount == 0 and id_conto_fk_nuovo is not None:  # Aggiunto controllo per id_conto_fk_nuovo
                # Questo potrebbe accadere se id_conto_fk_nuovo non esiste, il che dovrebbe essere impedito da un controllo FK
                # o se la query per qualche motivo non aggiorna righe.
                # Per sicurezza, potremmo voler verificare che il conto esista.
                # Ma la foreign key dovrebbe già gestire questo.
                pass  # Non sollevare eccezione qui, l'update potrebbe non aver trovato il conto se è stato cancellato nel frattempo (improbabile in una transazione)

        conn.commit()
        print(f"Transazione ID {id_transazione} aggiornata con successo.")
        return True
    except ValueError as ve:
        print(f"Errore Valore durante l'aggiornamento della transazione ID {id_transazione}: {ve}")
        if conn: conn.rollback()
        return False
    except Exception as e:
        print(f"Errore imprevisto durante l'aggiornamento della transazione ID {id_transazione}: {e}")
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()


def elimina_transazione_db(id_transazione):
    """
    Elimina una transazione e aggiorna il saldo del conto associato.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Ottieni i dettagli della transazione da eliminare (per stornare il saldo)
        cursor.execute("SELECT id_conto_fk, importo FROM transazioni WHERE id_transazione = ?", (id_transazione,))
        trans_dati = cursor.fetchone()
        if not trans_dati:
            print(f"Transazione ID {id_transazione} non trovata per l'eliminazione.")
            return False

        id_conto_fk_trans = trans_dati["id_conto_fk"]
        importo_trans = float(trans_dati["importo"])

        cursor.execute("BEGIN TRANSACTION")

        # 2. Elimina la transazione
        cursor.execute("DELETE FROM transazioni WHERE id_transazione = ?", (id_transazione,))

        # 3. Storna l'importo dal saldo del conto
        cursor.execute("UPDATE conti SET saldo_attuale = saldo_attuale - ? WHERE id_conto = ?",
                       (importo_trans, id_conto_fk_trans))

        conn.commit()
        print(f"Transazione ID {id_transazione} eliminata e saldo del conto ID {id_conto_fk_trans} aggiornato.")
        return True
    except ValueError:  # Errore conversione importo (improbabile qui)
        print(f"Errore Valore durante l'eliminazione della transazione ID {id_transazione}.")
        if conn: conn.rollback()
        return False
    except Exception as e:
        print(f"Errore imprevisto durante l'eliminazione della transazione ID {id_transazione}: {e}")
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()


# --- Funzioni CRUD per Investimenti ---

def aggiungi_investimento_db(nome_strumento, simbolo, tipo_asset, quantita, pmc_unitario, costo_totale_carico,
                             valore_attuale_unitario, data_valore_attuale, id_conto_detenzione_fk,
                             valuta, data_primo_acquisto, note=None):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        data_ultima_modifica_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(data_primo_acquisto, datetime):  # Assicura formato stringa
            data_primo_acquisto = data_primo_acquisto.strftime("%Y-%m-%d")  # Solo data per acquisto
        if isinstance(data_valore_attuale, datetime):
            data_valore_attuale = data_valore_attuale.strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute('''
            INSERT INTO investimenti (nome_strumento, simbolo, tipo_asset, quantita, pmc_unitario, 
                                      costo_totale_carico, valore_attuale_unitario, data_valore_attuale, 
                                      id_conto_detenzione_fk, valuta, data_primo_acquisto, 
                                      data_ultima_modifica, note, attivo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ''', (
        nome_strumento, simbolo, tipo_asset, float(quantita), float(pmc_unitario) if pmc_unitario is not None else None,
        float(costo_totale_carico) if costo_totale_carico is not None else None,
        float(valore_attuale_unitario) if valore_attuale_unitario is not None else None,
        data_valore_attuale, id_conto_detenzione_fk, valuta, data_primo_acquisto,
        data_ultima_modifica_str, note))
        id_nuovo_investimento = cursor.lastrowid
        conn.commit()
        print(f"Investimento '{nome_strumento}' aggiunto con ID: {id_nuovo_investimento}")
        return id_nuovo_investimento
    except sqlite3.IntegrityError as e:  # Es. nome_strumento UNIQUE se lo aggiungi
        print(f"Errore DB aggiungendo investimento '{nome_strumento}': {e}")
        if conn: conn.rollback()
        return None
    except ValueError as e:
        print(f"Errore Valore aggiungendo investimento '{nome_strumento}': {e}")
        if conn: conn.rollback()
        return None
    except Exception as e:
        print(f"Errore imprevisto aggiungendo investimento '{nome_strumento}': {e}")
        if conn: conn.rollback()
        return None
    finally:
        if conn: conn.close()


def get_investimento_by_id_db(id_investimento):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM investimenti WHERE id_investimento = ?", (id_investimento,))
        inv = cursor.fetchone()
        return dict(inv) if inv else None
    except Exception as e:
        print(f"Errore recupero investimento ID {id_investimento}: {e}")
        return None
    finally:
        if conn: conn.close()


def get_tutti_gli_investimenti_db(solo_attivi=True):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM investimenti"
        if solo_attivi:
            query += " WHERE attivo = 1"
        query += " ORDER BY nome_strumento"  # O per data_ultima_modifica, etc.
        cursor.execute(query)
        investimenti = cursor.fetchall()
        return [dict(inv) for inv in investimenti]
    except Exception as e:
        print(f"Errore recupero tutti gli investimenti: {e}")
        return []
    finally:
        if conn: conn.close()


def aggiorna_dettagli_investimento_db(id_investimento, nome_strumento, simbolo, tipo_asset, valuta, note,
                                      data_primo_acquisto=None):
    """ Aggiorna campi che non cambiano quantità o valori monetari diretti (tranne valuta)."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        data_ultima_modifica_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        set_clauses = []
        params = []
        if nome_strumento is not None: set_clauses.append("nome_strumento = ?"); params.append(nome_strumento)
        if simbolo is not None: set_clauses.append("simbolo = ?"); params.append(simbolo)  # Può essere NULL
        if tipo_asset is not None: set_clauses.append("tipo_asset = ?"); params.append(tipo_asset)
        if valuta is not None: set_clauses.append("valuta = ?"); params.append(valuta)
        if note is not None: set_clauses.append("note = ?"); params.append(note)  # Può essere NULL
        if data_primo_acquisto is not None:
            if isinstance(data_primo_acquisto, datetime): data_primo_acquisto = data_primo_acquisto.strftime("%Y-%m-%d")
            set_clauses.append("data_primo_acquisto = ?");
            params.append(data_primo_acquisto)

        if not set_clauses: return True  # Niente da aggiornare

        set_clauses.append("data_ultima_modifica = ?");
        params.append(data_ultima_modifica_str)
        params.append(id_investimento)

        query = f"UPDATE investimenti SET {', '.join(set_clauses)} WHERE id_investimento = ?"
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Errore aggiornamento dettagli investimento ID {id_investimento}: {e}")
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()


def aggiorna_posizione_investimento_db(id_investimento, nuova_quantita, nuovo_pmc_unitario, nuovo_costo_totale_carico):
    """ Aggiorna quantità e valori di carico. Chiamato dopo un acquisto o vendita parziale. """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        data_ultima_modifica_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            UPDATE investimenti 
            SET quantita = ?, pmc_unitario = ?, costo_totale_carico = ?, data_ultima_modifica = ?
            WHERE id_investimento = ?
        ''', (float(nuova_quantita), float(nuovo_pmc_unitario) if nuovo_pmc_unitario is not None else None,
              float(nuovo_costo_totale_carico) if nuovo_costo_totale_carico is not None else None,
              data_ultima_modifica_str, id_investimento))
        conn.commit()
        return cursor.rowcount > 0
    except ValueError as e:
        print(f"Errore Valore aggiornando posizione investimento ID {id_investimento}: {e}")
        if conn: conn.rollback()
        return False
    except Exception as e:
        print(f"Errore aggiornamento posizione investimento ID {id_investimento}: {e}")
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()


def aggiorna_valore_corrente_investimento_db(id_investimento, nuovo_valore_unitario, data_valore_str=None):
    """ Aggiorna solo il valore di mercato attuale dell'investimento. """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if data_valore_str is None:
            data_valore_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(data_valore_str, datetime):
            data_valore_str = data_valore_str.strftime("%Y-%m-%d %H:%M:%S")

        data_ultima_modifica_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute('''
            UPDATE investimenti 
            SET valore_attuale_unitario = ?, data_valore_attuale = ?, data_ultima_modifica = ?
            WHERE id_investimento = ?
        ''', (float(nuovo_valore_unitario) if nuovo_valore_unitario is not None else None,
              data_valore_str, data_ultima_modifica_str, id_investimento))
        conn.commit()
        return cursor.rowcount > 0
    except ValueError as e:
        print(f"Errore Valore aggiornando valore corrente investimento ID {id_investimento}: {e}")
        if conn: conn.rollback()
        return False
    except Exception as e:
        print(f"Errore aggiornamento valore corrente investimento ID {id_investimento}: {e}")
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()


def imposta_stato_investimento_db(id_investimento, attivo=True):
    """ Imposta lo stato attivo/inattivo (posizione chiusa)."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        data_ultima_modifica_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        stato = 1 if attivo else 0
        cursor.execute("UPDATE investimenti SET attivo = ?, data_ultima_modifica = ? WHERE id_investimento = ?",
                       (stato, data_ultima_modifica_str, id_investimento))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Errore impostazione stato investimento ID {id_investimento}: {e}")
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()
