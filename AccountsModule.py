from PyQt5.QtCore import QCoreApplication, Qt, QObject, pyqtSignal
from PyQt5.QtSql import QSqlDatabase, QSqlQuery, QSqlTableModel, QSqlQuery
from PyQt5.QtWidgets import QStatusBar, QMessageBox
import phonenumbers
from functools import partial
import os
# Importazione del tuo modulo logger
from Custom_Logger import setup_logger  
# Importazione del tuo modulo emettitore di segnali
from functools import partial
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QInputDialog
from telethon import TelegramClient
import random
import string
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
import random
import string
import asyncio
from PyQt5.QtSql import QSqlQuery


class SignalEmitter(QObject):
    my_signal = pyqtSignal()
    endProcessSignal = pyqtSignal()

signal_emitter = SignalEmitter()

global conn
global first_run
first_run = True

def second_run(ui):
    global partial_second_run
    global first_run
    first_run = False
    handle_accounts(ui)

# Connettere il segnale allo slot (la funzione second_run, in questo caso)
signal_emitter.my_signal.connect(second_run)
# Emettere il segnale, innescando la funzione second_run
#signal_emitter.my_signal.emit()

def Init_UIAccounts(ui, conn):
    try:
        setup_logger("Accounts", "Inizio inizializzazione UI per la gestione degli accounts.")  # Log inizio inizializzazione UI
        partial_second_run = partial(second_run, ui)
        signal_emitter.endProcessSignal.connect(partial_second_run)

        if not isinstance(conn, QSqlDatabase) or not conn.isOpen():  # Verifica se conn è un'istanza di QSqlDatabase e aperta
            setup_logger("Accounts", "La connessione deve essere un'istanza di QSqlDatabase e deve essere aperta.")
            return

        ui.Proxies.setDisabled(True)  # Disattiva pulsante Proxies
        ui.Accounts.setDisabled(True)  # Disattiva pulsante Accounts
        ui.Adder.setDisabled(True)  # Disattiva pulsante Adder
        QCoreApplication.processEvents()  # Forza aggiornamento UI

        ui.Invio.setEnabled(True)  # Attiva pulsante Invio
        ui.textEdit.setEnabled(True)  # Attiva textEdit
        QCoreApplication.processEvents()  # Forza aggiornamento UI

        ui.MessageLabel.setText("Introduci una lista di numeri (uno per linea)")  # Imposta testo label
        ui.MessageLabel.setAlignment(Qt.AlignCenter)  # Allinea al centro il testo della label
        ui.MessageLabel.setWordWrap(True)  # Abilita a capo automatico per la label
        QCoreApplication.processEvents()  # Forza aggiornamento UI
                                                           
        partial_controllo_lista_accounts = partial(controllo_lista_accounts, ui, conn)
        ui.Invio.clicked.connect(partial_controllo_lista_accounts)
        setup_logger("Accounts", "Pulsante Invio connesso alla funzione di controllo della lista degli accounts.")
            
    except Exception as e:  # Gestisce eventuali eccezioni durante il processo
        setup_logger("Accounts", f"Eccezione catturata durante l'inizializzazione UI: {e}")

def loadAccountsToTableView(ui, conn):
    try:
        setup_logger("Accounts", "Inizio caricamento degli accounts nella TableView.")  # Log inizio operazione
        if not conn.isOpen():  # Controlla se la connessione è aperta
            setup_logger("Accounts", "La connessione deve essere aperta.")
            return

        if ui is None:  # Controlla se l'oggetto UI è nullo
            setup_logger("Accounts", "Oggetto UI è nullo. Impossibile procedere.")
            return

        model = QSqlTableModel()  # Crea un nuovo modello QSqlTableModel
        model.setTable("Account_sessions")  # Imposta la tabella da utilizzare
        model.select()  # Seleziona tutti i dati nella tabella

        ui.tableView.setModel(model)  # Imposta il modello per la TableView
        QCoreApplication.processEvents()  # Forza aggiornamento UI

        ui.tableView.hideColumn(0)  # Nasconde la colonna "ID"
        QCoreApplication.processEvents()  # Forza aggiornamento UI

        ui.tableView.resizeColumnsToContents()  # Ridimensiona le colonne in base al contenuto
        QCoreApplication.processEvents()  # Forza aggiornamento UI

        setup_logger("Accounts", "Caricamento degli accounts nella TableView completato.")  # Log fine operazione

    except Exception as e:  # Cattura e registra eventuali eccezioni
        setup_logger("Accounts", f"Eccezione catturata durante il caricamento degli accounts nella TableView: {e}")

def is_valid_phone_number(number):
    try:
        parsed_number = phonenumbers.parse(number, None)
        return phonenumbers.is_valid_number(parsed_number)
    except phonenumbers.phonenumberutil.NumberParseException:
        return False

def controllo_lista_accounts(ui, conn):
    try:
        setup_logger("Accounts", "Avvio della funzione controllo_lista_accounts.")
        
        if not isinstance(conn, QSqlDatabase):
            setup_logger("Accounts", "La connessione deve essere un'istanza di QSqlDatabase.")
            return

        if ui is None:
            setup_logger("Accounts", "Oggetto UI è nullo. Impossibile procedere.")
            return

        text_content = ui.textEdit.toPlainText()
        lines = text_content.split("\n")

        valid_accounts = []
        malformed_count = 0

        for line in lines:
            setup_logger("Accounts", f"Controllo della linea: {line}.")
    
            clean_line = ''.join(ch for ch in line if ch.isnumeric() or ch == '+' or ch == ' ')
    
            if clean_line.startswith('+'):  # Verifica se la linea già inizia con '+'
                formatted_line = ''.join(clean_line.split())
            else:
                formatted_line = "+" + ''.join(clean_line.split())

            if is_valid_phone_number(formatted_line):
                valid_accounts.append(formatted_line)
                setup_logger("Accounts", f"Account valido trovato: {formatted_line}.")
            else:
                malformed_count += 1
                setup_logger("Accounts", f"Account malformato: {line}.")

        if malformed_count:
            ui.MessageLabel.setText(f"Sono stati eliminati {malformed_count} account perché malformati.")
            QCoreApplication.processEvents()

        if valid_accounts:
            ui.Invio.setEnabled(True)
            QCoreApplication.processEvents()
        else:
            ui.MessageLabel.setText("Nessun account valido rilevato: riprova.")
            ui.Invio.setEnabled(False)
            QCoreApplication.processEvents()

        setup_logger("Accounts", f"Controllo lista account completato. {malformed_count} account malformati rimossi.")
        valid_accounts_str = '\n'.join(valid_accounts)
        ui.textEdit.setPlainText(valid_accounts_str)
        QCoreApplication.processEvents()

        avvia_sessions(valid_accounts, conn)

    except Exception as e:
        setup_logger("Accounts", f"Eccezione catturata durante il controllo della lista degli account: {e}")

def avvia_sessions(valid_accounts, conn):
    try:
        setup_logger("Accounts", "Avvio della funzione avvia_sessions.")  # Log dell'inizio della funzione

        if not isinstance(conn, QSqlDatabase):  # Verifica del tipo di connessione
            setup_logger("Accounts", "La connessione deve essere un'istanza di QSqlDatabase.")
            return

        existing_sessions = []  # Lista per memorizzare le sessioni esistenti
        existing_tdata = []  # Lista per memorizzare le sessioni esistenti nella cartella Tdata
        nonexisting_sessions = []  # Lista per memorizzare le sessioni non esistenti

        sessions_path = os.path.join(os.getcwd(), "Sessions")  # Percorso alla cartella Sessions
        tdata_path = os.path.join(sessions_path, "Tdata")  # Percorso alla cartella Tdata

        query = QSqlQuery(conn)
        for phone_number in valid_accounts:
            setup_logger("Accounts", f"Controllo della sessione per il numero di telefono: {phone_number}.")
            
            # Query diretta sul database
            query.exec_(f"SELECT * FROM account_sessions WHERE Phone_Number = '{phone_number}'")
            
            session_exists_in_db = query.next()  # True se esiste un record, altrimenti False
            session_file_path = os.path.join(sessions_path, f"{phone_number}.session")  # Percorso al file di sessione

            # Controllo cartella Tdata e relative sessioni
            tdata_folder_path = os.path.join(tdata_path, phone_number.lstrip('+'))
            tdata_file_path = os.path.join(tdata_folder_path, f"{phone_number}.session")
            tdata_sub_folder_path = os.path.join(tdata_folder_path, 'Tdata')

            if session_exists_in_db and os.path.exists(session_file_path):
                existing_sessions.append(phone_number)
                setup_logger("Accounts", f"Sessione e file di sessione esistenti trovati per il numero di telefono: {phone_number}.")
            elif os.path.exists(tdata_folder_path) and os.path.exists(tdata_file_path) and os.path.exists(tdata_sub_folder_path):
                existing_tdata.append(phone_number)
                setup_logger("Accounts", f"File di sessione esistenti trovati nella cartella Tdata per il numero di telefono: {phone_number}.")
            else:
                nonexisting_sessions.append(phone_number)
                setup_logger("Accounts", f"Nessuna sessione o file di sessione esistenti trovati per il numero di telefono: {phone_number}.")

        # Gestione dei casi successivi, come l'aggiornamento delle liste di sessioni ecc.
        generate_clients()
    except Exception as e:
        setup_logger("Accounts", f"Eccezione catturata durante l'avvio delle sessioni: {e}")  # Log in caso di eccezione

def is_valid_api_id(api_id):
    return api_id.isdigit() and len(api_id) in [8, 9]

def is_valid_api_hash(api_hash):
    return len(api_hash) == 32  # assumendo che un API hash valido sia una stringa esadecimale di 32 caratteri

def generate_clients():
    global conn  # conn è una variabile globale di QSqlDatabase
    
    query = QSqlQuery(conn)
    
    # Riorganizza gli ID esistenti per essere sequenziali a partire da 1
    query.prepare("SET @new_id = 0;")
    query.exec_()
    query.prepare("UPDATE Automation_sessions SET ID = (@new_id := @new_id + 1) ORDER BY ID;")
    query.exec_()
    
    # Conta i record completi nella tabella
    query.prepare("SELECT COUNT(*) FROM Automation_sessions WHERE Api_Id IS NOT NULL AND Api_Hash IS NOT NULL AND Phone_Number IS NOT NULL;")
    query.exec_()
    query.next()
    num_records = query.value(0)
    
    if num_records > 0:
        query.prepare("SELECT * FROM Automation_sessions;")
        query.exec_()
        query.next()
        record = query.record()
        
        api_id = record.value("Api_Id")
        api_hash = record.value("Api_Hash")
        phone_number = record.value("Phone_Number")
        session_name = record.value("Session_Name")  # Aggiunto questo
        
        # Qui inserire il codice per testare il funzionamento dell'account con questi dati
        pass

    else:
        # Richiedi all'utente di inserire i dati
        phone_number, ok = QInputDialog.getText(None, "Account di automazione", "Inserisci il numero di telefono:")
        
        while not is_valid_phone_number(phone_number) and ok:
            phone_number, ok = QInputDialog.getText(None, "Account di automazione", "Immetti un numero di telefono valido:")
        
        api_id, ok = QInputDialog.getText(None, "Account di automazione", "Inserisci l'Api ID:")
        
        while not is_valid_api_id(api_id) and ok:
            api_id, ok = QInputDialog.getText(None, "Account di automazione", "Immetti un Api ID valido:")
        
        api_hash, ok = QInputDialog.getText(None, "Account di automazione", "Inserisci l'API Hash:")
        
        while not is_valid_api_hash(api_hash) and ok:
            api_hash, ok = QInputDialog.getText(None, "Account di automazione", "Immetti un API Hash valido:")

        # Genera un nome di sessione casuale di 5-10 caratteri
        session_name = ''.join(random.choices(string.ascii_letters, k=random.randint(5, 10)))
        
        # Ottieni il prossimo ID disponibile
        query.prepare("SELECT MAX(ID) FROM Automation_sessions;")
        query.exec_()
        query.next()
        max_id = query.value(0)
        
        if max_id is None or str(max_id).strip() == '':
            next_id = 1  # ID progressivo parte da 1 se max_id è None o stringa vuota
        else:
            max_id = int(str(max_id).strip())  # Converte in intero se necessario
            next_id = max_id + 1  # ID progressivo

                
        # Memorizzazione dei dati in corso
        query.prepare("INSERT INTO Automation_sessions (ID, Api_Id, Api_Hash, Phone_Number, Authorized, Session_Name) VALUES (?, ?, ?, ?, ?, ?);")
        query.addBindValue(next_id)
        query.addBindValue(api_id)
        query.addBindValue(api_hash)
        query.addBindValue(phone_number)
        query.addBindValue(0)  # Imposta Authorized a 0
        query.addBindValue(session_name)  # Aggiunge il nome di sessione generato
        query.exec_()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_client(api_id, api_hash, phone_number, session_name))

async def test_client(api_id, api_hash, phone_number, session_name):
    if not isinstance(session_name, str) or not session_name:
        print("Eccezione catturata: session_name non è una stringa valida.")
        return
    
    try:
        async with TelegramClient(StringSession(session_name), api_id, api_hash) as client:
            if not await client.is_user_authorized():
                await client.send_code_request(phone_number)
                code = input("Inserisci il codice di verifica: ")
                await client.sign_in(phone_number, code)

            me = await client.get_me()
            print(f"Benvenuto, {me.first_name}! ID utente: {me.id}")

    except Exception as e:
        print(f"Eccezione catturata durante l'avvio delle sessioni: {e}")



def handle_accounts(ui):
    global conn
    global first_run
    setup_logger("Accounts", "Inizio del maneggiamento del pulsante Accounts.")
    if first_run:
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))  # Ottieni la directory corrente
            database_path = os.path.join(current_dir, "database.db")  # Percorso del database
            conn = QSqlDatabase.addDatabase("QSQLITE")  # Aggiungi database
            conn.setDatabaseName(database_path)  # Nome del database

            if not conn.open():  # Apertura del database
                setup_logger("Accounts", "Impossibile aprire la connessione al database.")  # Log: Connessione fallita
                return
        except Exception as e:  # Cattura eccezioni
            setup_logger("Accounts", f"Eccezione catturata durante l'apertura del database: {e}")  # Log: Eccezione catturata
            return

        loadAccountsToTableView(ui, conn)  # Carica i proxy nella tabella
        Init_UIAccounts(ui, conn)  # Inizializza l'UI dei proxy
        
    else:    
        ui.Invio.clicked.disconnect #(partial_controllo_lista_accounts)
        #print("Disconnecting...")  # Sostituisci con il tuo metodo di logging

        # Chiudi la connessione al database
        conn.close()
        setup_logger("Accounts", "Connessione al database chiusa.")  # Log: Connessione chiusa

        # Aggiunta dei comandi prima del return
        ui.Invio.setEnabled(False)  # Disabilita il pulsante "Invio"
        ui.Proxies.setEnabled(True)  # Abilita il pulsante "Proxies"
        ui.Accounts.setEnabled(True)  # Abilita il pulsante "Accounts"
        ui.Adder.setEnabled(True)  # Abilita il pulsante "Adder"
        ui.textEdit.clear()  # Pulisci il campo "textEdit"

           
"""
def validate_proxy(line):
    
def controllo_lista_proxies(ui, conn, callback=None):
    try:
        setup_logger("Proxies", "Avvio della funzione controllo_lista_proxies.")  # Log dell'inizio della funzione

        if not isinstance(conn, QSqlDatabase):  # Verifica del tipo di connessione
            setup_logger("Proxies", "La connessione deve essere un'istanza di QSqlDatabase.")  
            return

        if ui is None:  # Verifica dell'oggetto UI
            setup_logger("Proxies", "Oggetto UI è nullo. Impossibile procedere.")  
            return

        text_content = ui.textEdit.toPlainText()  # Estrae il testo dal textEdit
        lines = text_content.split("\n")  # Suddivide il testo in linee

        if not lines or all(not line.strip() for line in lines):  # Caso nessun proxy inserito
            ui.MessageLabel.setText("Nessun proxy inserito. Inserisci i proxies secondo questo formato:\nIP Address:Port:Username:Password")
            setup_logger("Proxies", "Nessun proxy inserito.")  
            ui.Invio.setEnabled(True)  # Abilita il pulsante Invio
            QCoreApplication.processEvents()  # Forza l'aggiornamento dell'UI
            return

        valid_proxies = []
        malformed_count = 0  # Contatore per proxy malformati

        for line in lines:  # Ciclo di validazione dei proxy
            setup_logger("Proxies", f"Controllo della linea: {line}.")  
            is_valid, valid_line = validate_proxy(line)  # Utilizza la funzione validate_proxy

            if is_valid:  # Se il proxy è valido
                valid_proxies.append(valid_line)  
                setup_logger("Proxies", f"Proxy valido trovato: {valid_line}.")  
            else:  # Se il proxy è malformato
                malformed_count += 1  
                setup_logger("Proxies", f"Proxy malformato: {line}.")  

        if malformed_count:  # Gestisce i casi con proxy malformati e proxy validi
            ui.MessageLabel.setText(f"Sono stati eliminati {malformed_count} proxies perché malformati.")
            QCoreApplication.processEvents()  # Forza l'aggiornamento dell'UI

        if valid_proxies:
            ui.Invio.setEnabled(True) 
            QCoreApplication.processEvents()  # Forza l'aggiornamento dell'UI 
        else:
            ui.MessageLabel.setText("Nessun proxy valido rilevato: riprova.")
            ui.Invio.setEnabled(False)  # Disabilita il pulsante Invio
            QCoreApplication.processEvents()  # Forza l'aggiornamento dell'UI

        setup_logger("Proxies", f"Controllo lista proxy completato. {malformed_count} proxies malformati rimossi.")  
        valid_proxies_str = '\n'.join(valid_proxies)  
        ui.textEdit.setPlainText(valid_proxies_str)  # Aggiorna il textEdit con i proxy validi
        QCoreApplication.processEvents()  # Forza l'aggiornamento dell'UI
        

        Proxy_test(ui, valid_proxies, conn, callback=None)  # Chiama la funzione per testare i proxy
        
    except Exception as e:
        setup_logger("Proxies", f"Eccezione catturata durante il controllo della lista dei proxy: {e}")  # Log in caso di eccezione

def verify_list(valid_proxies, thread_number, final_list, ui, lock, callback=None):  # Funzione per verificare una lista di proxy
    setup_logger("Proxies", f"Inizio thread-{thread_number}.")  # Log dell'inizio del thread

    with Session() as session:  # Utilizzo di Session per una migliore gestione della connessione
        for proxy in valid_proxies:
            ip, port, username, password = proxy.split(":")  # Estrae le componenti del proxy
            working = 0  # Variabile per indicare se il proxy funziona
            geo = 'Unknown'  # Variabile per la località geografica del proxy
            errori = 0  # Variabile per il conteggio degli errori

            try:
                proxy_dict = {"http": f"http://{username}:{password}@{ip}:{port}/"}  # Forma la stringa del proxy
                r = session.get("http://ipinfo.io/json", proxies=proxy_dict, timeout=5)  # Richiesta HTTP
                geo = r.json().get('region', 'Unknown')  # Estrae la regione dal JSON
                working = 1  # Imposta working a 1, indicando che il proxy funziona
                setup_logger("Proxies", f"Proxy {ip}:{port} verificato con successo.")  # Log del successo nella verifica

            except Timeout:  # Gestisce i timeout
                setup_logger("Proxies", f"Timeout durante la verifica di {ip}:{port}.")  # Log del timeout
                errori = 1  # Imposta errori a 1

            except ConnectionError:  # Gestisce gli errori di connessione
                setup_logger("Proxies", f"Errore di connessione durante la verifica di {ip}:{port}.")  # Log dell'errore di connessione
                errori = 1  # Imposta errori a 1

            except Exception as e:  # Gestisce altre eccezioni
                setup_logger("Proxies", f"Eccezione generica riscontrata durante la verifica di {ip}:{port}. Eccezione: {e}")  # Log dell'eccezione
                errori = 1  # Imposta errori a 1

            with lock:  # Usa un lock per l'aggiornamento sicuro della lista finale
                final_list.append({"ip": ip, "port": port, "username": username, "password": password, "working": working, "geo": geo, "errori": errori})  # Aggiunge il proxy alla lista finale
                QCoreApplication.processEvents()  # Forza l'aggiornamento dell'UI

    setup_logger("Proxies", f"Thread-{thread_number} terminato.")  # Log della fine del thread

def get_thread_lists(valid_proxies, num_threads, ui): # Funzione per dividere la lista di proxy tra i thread
    setup_logger("Proxies", "Divisione della lista proxy tra i thread.")
    chunk_size = math.ceil(len(valid_proxies) / num_threads)
    return [valid_proxies[i:i + chunk_size] for i in range(0, len(valid_proxies), chunk_size)]

def Proxy_test(ui, valid_proxies, conn, timeout=5, callback=None): # Funzione principale per testare i proxy
    setup_logger("Proxies", "Inizio del test proxy.")  # Inizio del test dei proxy
    setup_logger("Proxies", f"Tipo di connessione all'inizio di Proxy_test: {type(conn)}") # Verifica del tipo e stato della connessione al database prima del test  
    setup_logger("Proxies", f"Stato di apertura della connessione all'inizio di Proxy_test: {conn.isOpen()}")  
    
    if not isinstance(conn, QSqlDatabase):
        ui.MessageLabel.setText("Tipo di connessione errato.")  # Messaggio di errore per tipo di connessione
        QCoreApplication.processEvents()  # Aggiornamento forzato dell'UI
        return
    if not conn.isOpen():
        ui.MessageLabel.setText("La connessione non è aperta.")  # Messaggio di errore per stato di connessione
        QCoreApplication.processEvents()  # Aggiornamento forzato dell'UI
        return
    ui.statusLabel.setText("Test dei proxy in corso. Attendere")  # Imposta il messaggio nella label
    QCoreApplication.processEvents()  # Forza l'aggiornamento dell'UI

    lock = Lock()  # Inizializza il lock per il multithreading
    num_threads = 10  # Numero predefinito di thread
    if len(valid_proxies) < num_threads:
        num_threads = len(valid_proxies)  # Regola il numero di thread in base ai proxy validi

    divided_proxy_lists = get_thread_lists(valid_proxies, num_threads, ui) # Divisione dei proxy validi tra i thread
    final_list = []  # Lista finale dei proxy verificati
    threads = []  # Lista dei thread

    for i, mini_list in enumerate(divided_proxy_lists): # Avvia i thread di verifica
        thread = Thread(target=verify_list, args=(mini_list, i, final_list, ui, lock))  
        threads.append(thread)  
        thread.start()  

    for t in threads: # Attesa del completamento di tutti i thread
        t.join()  

    if not isinstance(conn, QSqlDatabase) or not conn.isOpen(): # Verifica dello stato della connessione prima dell'aggiornamento del database
        ui.MessageLabel.setText("La connessione è cambiata o è stata chiusa.")  
        QCoreApplication.processEvents()  # Aggiornamento forzato dell'UI
        return

    try: # Tentativo di aggiornamento del database dei proxy
        update_proxies_database(final_list, ui, conn, callback)  
        ui.MessageLabel.setText("Test proxy completato e database aggiornato.")  
        QCoreApplication.processEvents()  # Aggiornamento forzato dell'UI
    except Exception as e:
        ui.MessageLabel.setText("Errore durante l'aggiornamento del database.")  
        QCoreApplication.processEvents()  # Aggiornamento forzato dell'UI

def scroll_table_to_bottom(ui, callback=None):
    setup_logger("Proxies", "Inizio dello scrolling della tabella verso il basso.")  # Inizio dello scrolling
    ui.tableView.scrollToBottom()  # Scrolling della tabella verso il basso
    QCoreApplication.processEvents()  # Aggiornamento forzato dell'UI
    setup_logger("Proxies", "Scrolling della tabella verso il basso completato.")  # Fine dello scrolling
    signal_emitter.endProcessSignal.emit()

def reorder_ids(conn):
    setup_logger("Proxies", "Inizio del riordino degli ID.")  # Log: Inizio del riordino degli ID
    if not isinstance(conn, QSqlDatabase) or not conn.isOpen():  # Verifica del tipo e dello stato della connessione
        setup_logger("Proxies", "La connessione deve essere un'istanza aperta di QSqlDatabase")  # Log: Tipo o stato della connessione errato
        return
    try:
        query = QSqlQuery(conn)  # Creazione dell'oggetto query
        if query.exec_("SELECT * FROM Proxies ORDER BY ID"):  # Recupero di tutte le righe ordinate per ID
            reordered_rows = []  # Lista per memorizzare le righe riordinate
            index = 1  # Inizializzazione dell'indice
            while query.next():  # Iterazione sulle righe della tabella
                old_id, IP_Address, Port, Username, Password, Working, Geo, Errori = query.value(0), query.value(1), query.value(2), query.value(3), query.value(4), query.value(5), query.value(6), query.value(7)  # Estrazione dei dati dalla riga corrente
                reordered_row = (index, IP_Address, Port, Username, Password, Working, Geo, Errori)  # Creazione della riga riordinata
                reordered_rows.append(reordered_row)  # Aggiunta della riga riordinata
                index += 1  # Incremento dell'indice
            query.exec_("DELETE FROM Proxies")  # Cancellazione dei dati esistenti
            query.prepare("INSERT INTO Proxies (ID, IP_Address, Port, Username, Password, Working, Geo, Errori) VALUES (?, ?, ?, ?, ?, ?, ?, ?)")  # Preparazione della query di inserimento
            for row in reordered_rows:  # Iterazione sulle righe riordinate
                query.addBindValue(row[0])  # Inserimento dei nuovi dati
                query.addBindValue(row[1])  # Inserimento dei nuovi dati
                query.addBindValue(row[2])  # Inserimento dei nuovi dati
                query.addBindValue(row[3])  # Inserimento dei nuovi dati
                query.addBindValue(row[4])  # Inserimento dei nuovi dati
                query.addBindValue(row[5])  # Inserimento dei nuovi dati
                query.addBindValue(row[6])  # Inserimento dei nuovi dati
                query.addBindValue(row[7])  # Inserimento dei nuovi dati
                if not query.exec_():  # Esecuzione della query
                    raise Exception(query.lastError().text())  # Eccezione in caso di errore
            QCoreApplication.processEvents()  # Aggiornamento forzato dell'UI
        else:
            setup_logger("Proxies", f"Errore durante l'esecuzione della query: {query.lastError().text()}")  # Log dell'errore
    except Exception as e:  # Gestione delle eccezioni
        setup_logger("Proxies", f"Errore durante il riordino del database: {e}")  # Log dell'errore

def update_proxies_database(final_list, ui, conn, callback=None):
    setup_logger("Proxies", "Inizio dell'aggiornamento del database dei proxy.")  # Log: Inizio dell'aggiornamento
    setup_logger("Proxies", f"Tipo di connessione all'inizio di update_proxies_database: {type(conn)}")  # Log: Tipo di connessione
    setup_logger("Proxies", f"Stato di apertura della connessione all'inizio di update_proxies_database: {conn.isOpen()}")  # Log: Stato di apertura

    if not isinstance(conn, QSqlDatabase) or not conn.isOpen():  # Verifica tipo e stato della connessione
        setup_logger("Proxies", "La connessione deve essere un'istanza aperta di QSqlDatabase all'inizio di update_proxies_database.")  # Log: Connessione non valida

    try:
        query = QSqlQuery(conn)  # Inizializzazione della query

        for proxy in final_list:  # Iterazione su tutti i proxy
            IP_Address, Port, Username, Password, Working, Geo, Errori = proxy['ip'], proxy['port'], proxy['username'], proxy['password'], proxy['working'], proxy['geo'], proxy['errori']  # Estrazione dati

            query.prepare("SELECT * FROM Proxies WHERE IP_Address=:ip AND Port=:port")  # Preparazione query SELECT
            query.bindValue(":ip", IP_Address)  # Binding IP_Address
            query.bindValue(":port", Port)  # Binding Port

            if query.exec_() and query.next():  # Esecuzione e verifica esistenza record
                new_errori = Errori + 1 if not Working else Errori  # Calcolo nuovi errori

                query.prepare("UPDATE Proxies SET Username=:username, Password=:password, Working=:working, Geo=:geo, Errori=:errori WHERE IP_Address=:ip AND Port=:port")  # Preparazione query UPDATE
                query.bindValue(":username", Username)  # Binding Username
                query.bindValue(":password", Password)  # Binding Password
                query.bindValue(":working", Working)  # Binding Working
                query.bindValue(":geo", Geo)  # Binding Geo
                query.bindValue(":errori", new_errori)  # Binding nuovi errori
                query.bindValue(":ip", IP_Address)  # Binding IP_Address
                query.bindValue(":port", Port)  # Binding Port

                if not query.exec_():  # Esecuzione query
                    raise Exception(query.lastError().text())  # Lancio eccezione in caso di errore

            else:
                query.prepare("INSERT INTO Proxies (IP_Address, Port, Username, Password, Working, Geo, Errori) VALUES (:ip, :port, :username, :password, :working, :geo, :errori)")  # Preparazione query INSERT
                query.bindValue(":ip", IP_Address)  # Binding IP_Address
                query.bindValue(":port", Port)  # Binding Port
                query.bindValue(":username", Username)  # Binding Username
                query.bindValue(":password", Password)  # Binding Password
                query.bindValue(":working", Working)  # Binding Working
                query.bindValue(":geo", Geo)  # Binding Geo
                query.bindValue(":errori", Errori)  # Binding Errori

                if not query.exec_():  # Esecuzione query
                    raise Exception(query.lastError().text())  # Lancio eccezione in caso di errore

        reorder_ids(conn)  # Riordino ID

    except Exception as e:  # Gestione eccezioni
        setup_logger("Proxies", f"Errore durante l'aggiornamento del database: {e}")  # Log errore

    finally:
        loadProxiesToTableView(ui, conn, callback)  # Caricamento dati nella tabella con callback
        scroll_table_to_bottom(ui, callback)  # Scorrimento in fondo alla tabella con callback
        setup_logger("Proxies", "Fine dell'aggiornamento del database dei proxy.")  # Log: Fine dell'aggiornamento

def second_run(ui, callback=None):
    global partial_second_run
    global first_run
    print("Esecuzione di second_run...")
    first_run = False
    signal_emitter.endProcessSignal.disconnect(partial_second_run)
    handle_proxies(ui, callback)
"""