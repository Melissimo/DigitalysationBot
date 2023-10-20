# PyQt5 imports
from PyQt5 import QtCore
from PyQt5.QtSql import QSqlDatabase, QSqlQuery, QSqlTableModel
from PyQt5.QtWidgets import QHeaderView, QTableView, QMessageBox, QTableWidgetItem
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import pyqtSignal, QObject

# Standard library and third-party imports
import os
import re
import math
import time
from threading import Thread, Lock
from time import sleep

# Requests imports
from requests import Session
from requests.exceptions import Timeout, ConnectionError

# Custom imports
from Custom_Logger import setup_logger
from functools import partial

# Inizializzazione della variabile globale

global first_run
first_run = True
global partial_second_run
global partial_controllo_lista_proxies
global conn

class SignalEmitter(QObject):
    endProcessSignal = pyqtSignal()

signal_emitter = SignalEmitter()

def second_run(ui):
    global partial_second_run
    global first_run
    first_run = False
    handle_proxies(ui)
    
def Init_UIProxies(ui, conn):
    global first_run
    global partial_second_run
    global partial_controllo_lista_proxies
    try:
        setup_logger("Proxies", "Inizio inizializzazione UI per la gestione dei proxy.")  # Log inizio inizializzazione UI
        partial_second_run = partial(second_run, ui)
        signal_emitter.endProcessSignal.connect(partial_second_run)

        if not isinstance(conn, QSqlDatabase) or not conn.isOpen():  # Verifica se conn è un'istanza di QSqlDatabase e aperta
            setup_logger("Proxies", "La connessione deve essere un'istanza di QSqlDatabase e deve essere aperta.")
            return

        ui.Proxies.setDisabled(True)  # Disattiva pulsante Proxies
        ui.Accounts.setDisabled(True)  # Disattiva pulsante Accounts
        ui.Adder.setDisabled(True)  # Disattiva pulsante Adder
        QCoreApplication.processEvents()  # Forza aggiornamento UI

        ui.Invio.setEnabled(True)  # Attiva pulsante Invio
        ui.textEdit.setEnabled(True)  # Attiva textEdit
        QCoreApplication.processEvents()  # Forza aggiornamento UI

        ui.MessageLabel.setText("Introduci una lista di proxies (un proxy per linea) con questo formato: IP_address:port:username:password")  # Imposta testo label
        ui.MessageLabel.setAlignment(QtCore.Qt.AlignCenter)  # Allinea al centro il testo della label
        ui.MessageLabel.setWordWrap(True)  # Abilita a capo automatico per la label
        QCoreApplication.processEvents()  # Forza aggiornamento UI
                                                           
        partial_controllo_lista_proxies = partial(controllo_lista_proxies, ui, conn)
        ui.Invio.clicked.connect(partial_controllo_lista_proxies)  # Connette il pulsante Invio alla funzione di controllo
        setup_logger("Proxies", "Pulsante Invio connesso alla funzione di controllo della lista dei proxy.")
    
    except Exception as e:  # Gestisce eventuali eccezioni durante il processo
        setup_logger("Proxies", f"Eccezione catturata durante l'inizializzazione UI: {e}")

def loadProxiesToTableView(ui, conn):
    try:
        setup_logger("Proxies", "Inizio caricamento dei proxy nella TableView.")  # Log inizio operazione
        if not conn.isOpen():  # Controlla se la connessione è aperta
            setup_logger("Proxies", "La connessione deve essere aperta.")
            return

        if ui is None:  # Controlla se l'oggetto UI è nullo
            setup_logger("Proxies", "Oggetto UI è nullo. Impossibile procedere.")
            return

        model = QSqlTableModel()  # Crea un nuovo modello QSqlTableModel
        model.setTable("Proxies")  # Imposta la tabella da utilizzare
        model.select()  # Seleziona tutti i dati nella tabella

        ui.tableView.setModel(model)  # Imposta il modello per la TableView
        QCoreApplication.processEvents()  # Forza aggiornamento UI

        ui.tableView.hideColumn(0)  # Nasconde la colonna "ID"
        QCoreApplication.processEvents()  # Forza aggiornamento UI

        ui.tableView.resizeColumnsToContents()  # Ridimensiona le colonne in base al contenuto
        QCoreApplication.processEvents()  # Forza aggiornamento UI

        setup_logger("Proxies", "Caricamento dei proxy nella TableView completato.")  # Log fine operazione

    except Exception as e:  # Cattura e registra eventuali eccezioni
        setup_logger("Proxies", f"Eccezione catturata durante il caricamento dei proxy nella TableView: {e}")

def is_valid_ip(ip):
    setup_logger("Proxies", "Inizio verifica validità IP.")
    pattern = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
    return bool(pattern.match(ip))

def is_valid_port(port):
    setup_logger("Proxies", "Inizio verifica validità porta.")
    return port.isdigit() and (1000 <= int(port) <= 65535)

def validate_proxy(line):
    components = line.split(":")
    if len(components) == 4:
        ip, port, _, _ = components
    elif len(components) == 2:
        ip, port = components
    else:
        return False, None

    if is_valid_ip(ip) and is_valid_port(port):
        return True, line
    return False, None

def controllo_lista_proxies(ui, conn):
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
            QCoreApplication.processEvents()  # Forza l'aggiornamento dell'UI

        if valid_proxies:
            ui.Invio.setEnabled(True) 
            QCoreApplication.processEvents()  # Forza l'aggiornamento dell'UI 

        setup_logger("Proxies", f"Controllo lista proxy completato. {malformed_count} proxies malformati rimossi.")  
        valid_proxies_str = '\n'.join(valid_proxies)  
        ui.textEdit.setPlainText(valid_proxies_str)  # Aggiorna il textEdit con i proxy validi
        QCoreApplication.processEvents()  # Forza l'aggiornamento dell'UI
        sleep(2)

        Proxy_test(ui, valid_proxies, conn)  # Chiama la funzione per testare i proxy
        
    except Exception as e:
        setup_logger("Proxies", f"Eccezione catturata durante il controllo della lista dei proxy: {e}")  # Log in caso di eccezione

def verify_list(valid_proxies, thread_number, final_list, ui, lock):
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
                errori = 1  # Imposta errori a 1

            except ConnectionError:  # Gestisce gli errori di connessione
                errori = 1  # Imposta errori a 1

            except Exception as e:  # Gestisce altre eccezioni
                errori = 1  # Imposta errori a 1

            with lock:  # Usa un lock per l'aggiornamento sicuro della lista finale
                final_list.append({"ip": ip, "port": port, "username": username, "password": password, "working": working, "geo": geo, "errori": errori})  # Aggiunge il proxy alla lista finale
                QCoreApplication.processEvents()  # Forza l'aggiornamento dell'UI

    setup_logger("Proxies", f"Thread-{thread_number} terminato.")  # Log della fine del thread

def get_thread_lists(valid_proxies, num_threads, ui): 
    setup_logger("Proxies", "Divisione della lista proxy tra i thread.")
    chunk_size = math.ceil(len(valid_proxies) / num_threads)
    return [valid_proxies[i:i + chunk_size] for i in range(0, len(valid_proxies), chunk_size)]

def Proxy_test(ui, valid_proxies, conn, timeout=5):
    setup_logger("Proxies", "Inizio del test proxy.")  # Inizia il test dei proxy
    setup_logger("Proxies", f"Tipo di connessione all'inizio di Proxy_test: {type(conn)}")  # Log sul tipo di connessione
    setup_logger("Proxies", f"Stato di apertura della connessione all'inizio di Proxy_test: {conn.isOpen()}")  # Log sullo stato della connessione

    if not isinstance(conn, QSqlDatabase) or not conn.isOpen():  # Controlla il tipo e lo stato della connessione
        ui.MessageLabel.setText("La connessione è errata o non aperta.")  # Mostra un messaggio di errore
        QCoreApplication.processEvents()  # Aggiorna l'UI
        return
    
    ui.MessageLabel.setText("Test dei proxy in corso. Attendere")  # Imposta il messaggio nella label
    QCoreApplication.processEvents()  # Forza l'aggiornamento dell'UI

    lock = Lock()  # Inizializza un lock per il multithreading
    num_threads = min(10, len(valid_proxies))  # Imposta il numero di thread

    divided_proxy_lists = get_thread_lists(valid_proxies, num_threads, ui)  # Divide i proxy tra i thread
    final_list = []  # Inizializza la lista finale dei proxy
    threads = []  # Inizializza la lista dei thread

    # Avvia i thread per la verifica dei proxy
    for i, mini_list in enumerate(divided_proxy_lists):
        thread = Thread(target=verify_list, args=(mini_list, i, final_list, ui, lock))
        threads.append(thread)
        thread.start()
        setup_logger("Proxies", f"Thread-{i} avviato.")  # Log sull'avvio del thread

    # Attende il completamento di tutti i thread
    for t in threads:
        t.join()
        setup_logger("Proxies", f"Thread-{threads.index(t)} terminato.")  # Log sulla terminazione del thread

    # Tenta di aggiornare il database dei proxy
    if isinstance(conn, QSqlDatabase) and conn.isOpen():
        try:
            update_proxies_database(final_list, ui, conn)  
            ui.MessageLabel.setText("Test proxy completato e database aggiornato.")  # Mostra un messaggio di successo
            setup_logger("Proxies", "Database proxy aggiornato con successo.")  # Log sul successo dell'aggiornamento del database
        except Exception as e:
            ui.MessageLabel.setText("Errore durante l'aggiornamento del database.")  # Mostra un messaggio di errore
            setup_logger("Proxies", f"Errore durante l'aggiornamento del database: {e}")  # Log sull'errore nell'aggiornamento del database
    else:
        ui.MessageLabel.setText("La connessione è cambiata o è stata chiusa.")  # Mostra un messaggio di errore
        setup_logger("Proxies", "La connessione è cambiata o è stata chiusa.")  # Log sul cambiamento o sulla chiusura della connessione

    QCoreApplication.processEvents()  # Aggiorna l'UI

def scroll_table_to_bottom(ui):
    setup_logger("Proxies", "Inizio dello scrolling della tabella verso il basso.")  # Log dell'inizio dello scrolling
    ui.tableView.scrollToBottom()  # Esegue lo scrolling verso il basso
    QCoreApplication.processEvents()  # Aggiornamento dell'UI
    setup_logger("Proxies", "Scrolling della tabella verso il basso completato.")  # Log della fine dello scrolling
    signal_emitter.endProcessSignal.emit()  # Emissione del segnale di fine processo

def reorder_ids(conn):
    setup_logger("Proxies", "Inizio del riordino degli ID.")  # Log dell'inizio del riordino
    if not isinstance(conn, QSqlDatabase) or not conn.isOpen():  # Verifica del tipo e dello stato della connessione
        setup_logger("Proxies", "La connessione deve essere un'istanza aperta di QSqlDatabase.")  # Log dell'errore
        return

    try:
        query = QSqlQuery(conn)  # Inizializza la query
        if query.exec_("SELECT * FROM Proxies ORDER BY ID"):  # Esegue la query SQL per selezionare tutti i record
            reordered_rows = []  # Inizializza una lista vuota per le righe riordinate
            index = 1  # Inizializza l'indice di riordino
            while query.next():  # Ciclo per leggere tutti i record
                old_id, IP_Address, Port, Username, Password, Working, Geo, Errori = query.value(0), query.value(1), query.value(2), query.value(3), query.value(4), query.value(5), query.value(6), query.value(7)
                reordered_rows.append((index, IP_Address, Port, Username, Password, Working, Geo, Errori))  # Aggiunge la riga riordinata alla lista
                index += 1  # Incrementa l'indice

            query.exec_("DELETE FROM Proxies")  # Cancella tutti i record esistenti
            query.prepare("INSERT INTO Proxies (ID, IP_Address, Port, Username, Password, Working, Geo, Errori) VALUES (?, ?, ?, ?, ?, ?, ?, ?)")  # Prepara la query SQL per l'inserimento

            for row in reordered_rows:  # Ciclo per inserire le righe riordinate
                for val in row:
                    query.addBindValue(val)  # Aggiunge ciascun valore alla query
                if not query.exec_():  # Esegue la query
                    raise Exception(query.lastError().text())  # Lancia un'eccezione se la query fallisce

            QCoreApplication.processEvents()  # Aggiornamento dell'UI
        else:
            setup_logger("Proxies", f"Errore durante l'esecuzione della query: {query.lastError().text()}")  # Log dell'errore della query

    except Exception as e:  # Gestione delle eccezioni
        setup_logger("Proxies", f"Errore durante il riordino del database: {e}")  # Log dell'errore

def update_proxies_database(final_list, ui, conn):
    setup_logger("Proxies", "Inizio dell'aggiornamento del database dei proxy.")  # Log dell'inizio dell'aggiornamento
    setup_logger("Proxies", f"Tipo di connessione all'inizio di update_proxies_database: {type(conn)}")  # Log del tipo di connessione
    setup_logger("Proxies", f"Stato di apertura della connessione all'inizio di update_proxies_database: {conn.isOpen()}")  # Log dello stato di apertura della connessione

    if not isinstance(conn, QSqlDatabase) or not conn.isOpen():  # Verifica del tipo e dello stato della connessione
        setup_logger("Proxies", "La connessione deve essere un'istanza aperta di QSqlDatabase all'inizio di update_proxies_database.")  # Log in caso di connessione non valida
        return

    try:
        query = QSqlQuery(conn)  # Inizializzazione della query

        for proxy in final_list:  # Iterazione sui dati dei proxy
            IP_Address, Port, Username, Password, Working, Geo, Errori = proxy['ip'], proxy['port'], proxy['username'], proxy['password'], proxy['working'], proxy['geo'], proxy['errori']  # Estrazione dei dati

            query.prepare("SELECT * FROM Proxies WHERE IP_Address=:ip AND Port=:port")  # Preparazione della query SELECT
            query.bindValue(":ip", IP_Address)  # Associazione dell'IP_Address
            query.bindValue(":port", Port)  # Associazione della Porta

            if query.exec_() and query.next():  # Esecuzione della query e controllo se esiste già un record
                new_errori = Errori + 1 if not Working else Errori  # Calcolo dei nuovi errori
                
                query.prepare("UPDATE Proxies SET Username=:username, Password=:password, Working=:working, Geo=:geo, Errori=:errori WHERE IP_Address=:ip AND Port=:port")  # Preparazione della query UPDATE
                query.bindValue(":username", Username)  # Associazione del valore Username
                query.bindValue(":password", Password)  # Associazione del valore Password
                query.bindValue(":working", Working)  # Associazione del valore Working
                query.bindValue(":geo", Geo)  # Associazione del valore Geo
                query.bindValue(":errori", new_errori)  # Associazione del valore dei nuovi errori
                query.bindValue(":ip", IP_Address)  # Associazione del valore IP_Address
                query.bindValue(":port", Port)  # Associazione del valore Porta
                
                if not query.exec_():  # Esecuzione della query
                    raise Exception(query.lastError().text())  # Eccezione in caso di errore

            else:
                query.prepare("INSERT INTO Proxies (IP_Address, Port, Username, Password, Working, Geo, Errori) VALUES (:ip, :port, :username, :password, :working, :geo, :errori)")  # Preparazione della query INSERT
                query.bindValue(":ip", IP_Address)  # Associazione del valore IP_Address
                query.bindValue(":port", Port)  # Associazione del valore Porta
                query.bindValue(":username", Username)  # Associazione del valore Username
                query.bindValue(":password", Password)  # Associazione del valore Password
                query.bindValue(":working", Working)  # Associazione del valore Working
                query.bindValue(":geo", Geo)  # Associazione del valore Geo
                query.bindValue(":errori", Errori)  # Associazione del valore Errori
                
                if not query.exec_():  # Esecuzione della query
                    raise Exception(query.lastError().text())  # Eccezione in caso di errore

        reorder_ids(conn)  # Riordino degli ID

    except Exception as e:  # Gestione delle eccezioni
        setup_logger("Proxies", f"Errore durante l'aggiornamento del database: {e}")  # Log dell'errore

    finally:
        loadProxiesToTableView(ui, conn)  # Caricamento dei dati nella tabella
        scroll_table_to_bottom(ui)  # Scorrimento della tabella fino in fondo
        setup_logger("Proxies", "Fine dell'aggiornamento del database dei proxy.")  # Log della fine dell'aggiornamento

def handle_proxies(ui):
    global conn
    global first_run
    global second_run
    global partial_second_run
    global partial_controllo_lista_proxies
    setup_logger("Proxies", "Inizio del maneggiamento del pulsante Proxies.")
    
    if first_run:
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))  # Ottieni la directory corrente
            database_path = os.path.join(current_dir, "database.db")  # Percorso del database
            conn = QSqlDatabase.addDatabase("QSQLITE")  # Aggiungi database
            conn.setDatabaseName(database_path)  # Nome del database

            if not conn.open():  # Apertura del database
                setup_logger("Proxies", "Impossibile aprire la connessione al database.")  # Log: Connessione fallita
                return
        except Exception as e:  # Cattura eccezioni
            setup_logger("Proxies", f"Eccezione catturata durante l'apertura del database: {e}")  # Log: Eccezione catturata
            return

        loadProxiesToTableView(ui, conn)  # Carica i proxy nella tabella
        Init_UIProxies(ui, conn)  # Inizializza l'UI dei proxy
    else:    
        setup_logger("Proxies", "Disconnessione in corso")  # Metodo di logging personalizzato

        # Chiudi la connessione al database
        conn.close()
        setup_logger("Proxies", "Connessione al database chiusa.")  # Log: Connessione chiusa

        # Comandi da eseguire prima del return
        ui.Invio.setEnabled(False)  # Disabilita il pulsante "Invio"
        ui.Proxies.setEnabled(True)  # Abilita il pulsante "Proxies"
        ui.Accounts.setEnabled(True)  # Abilita il pulsante "Accounts"
        ui.Adder.setEnabled(True)  # Abilita il pulsante "Adder"
        ui.textEdit.clear()  # Pulisci il campo "textEdit"
