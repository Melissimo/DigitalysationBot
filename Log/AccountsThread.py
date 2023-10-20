import re
import sys
import requests
import math
import os
import sqlite3
from PyQt5.QtCore import QEventLoop, QTimer
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel
from PyQt5.QtWidgets import QHeaderView, QTableView, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5 import QtWidgets
from Custom_Logger import setup_logger  # Importa la funzione di logging personalizzata
from DigitalysationTelegramBot import Ui_DigitalysationTelegramBot  # Importa la tua classe UI
from threading import Thread, Lock



def init_ui(ui):
    setup_logger("Proxies", "Initializing UI")
    ui.textEdit.clear()
    ui.MessageLabel.setText("Introduci una lista di proxies (un proxy per linea) con questo formato: IP_address:port:username:password")
    ui.MessageLabel.update()
    return True

def init_db():
    current_path = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_path, "database.db")
    
    db = sqlite3.connect(db_path)
    cursor = db.cursor()
    
    # Crea la tabella Proxies se non esiste
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Proxies (
        id INTEGER PRIMARY KEY,
        proxy_address TEXT,
        status TEXT
    )
    """)
    db.commit()
    
    return db


def init_table_view(ui, db):
    # Crea un oggetto cursore dal database, verificando il tipo di 'db'
    if not isinstance(db, sqlite3.Connection):
        db = sqlite3.connect(db)
    
    cursor = db.cursor()
    
    # Esegui la query per ottenere tutti i dati dalla tabella Proxies
    cursor.execute("SELECT * FROM Proxies")
    rows = cursor.fetchall()
    
    # Imposta il numero di righe e colonne nel QTableWidget
    ui.tableView.setRowCount(len(rows))
    ui.tableView.setColumnCount(len(rows[0]) if rows else 0)
    
    # Riempi il QTableWidget con i dati
    for i, row in enumerate(rows):
        for j, value in enumerate(row):
            cell = QtWidgets.QTableWidgetItem(str(value))
            ui.tableView.setItem(i, j, cell)

def enable_invio_button(ui):
    setup_logger("Proxies", "Enabling Invio Button")
    ui.Invio.setEnabled(True)


def proxies_ini(ui,db):
    setup_logger("Proxies", "Starting proxies_ini")
    if init_ui(ui) and init_db():
        if init_table_view(ui, db):
            enable_invio_button(ui)
            
    loop = QEventLoop()

    def on_invio_clicked():
        setup_logger("Proxies", "Invio Button Clicked, Running controllo_lista_proxies")
        controllo_lista_proxies(ui)
        setup_logger("Proxies", "Finished Running controllo_lista_proxies")
        loop.quit()

    ui.Invio.clicked.connect(on_invio_clicked)

    loop.exec_()
def is_valid_ip(ip):
    setup_logger("Proxies", "Verifica validità IP.")
    pattern = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
    return bool(pattern.match(ip))

def is_valid_port(port):
    setup_logger("Proxies","Verifica validità porta.")
    return port.isdigit() and (1000 <= int(port) <= 65535)

lock = Lock()

def threaded_test_proxies(proxy_chunk, thread_number, final_list):
    verify_list(proxy_chunk, thread_number, final_list)

def get_thread_lists(proxy_list, num_threads):
    chunk_size = math.ceil(len(proxy_list) / num_threads)
    return [proxy_list[i:i + chunk_size] for i in range(0, len(proxy_list), chunk_size)]

def verify_list(proxy_list, thread_number, final_list):
    for proxy in proxy_list:
        ip, port, username, password = proxy.split(":")
        working = 0
        geo = 'Unknown'
        errori = 0
        try:
            proxy_dict = {"http": f"http://{username}:{password}@{ip}:{port}/"}
            r = requests.get("http://ipinfo.io/json", proxies=proxy_dict, timeout=5)
            geo = r.json().get('region', 'Unknown')
            working = 1
        except Exception as e:
            errori = 1

        with lock:
            final_list.append({"ip": ip, "port": port, "username": username, "password": password, "working": working, "geo": geo, "errori": errori})

def test_proxies(proxy_list, ui):
    setup_logger("Proxies", "Starting to test proxies.")
    final_list = []
    num_threads = 4
    proxy_chunks = get_thread_lists(proxy_list, num_threads)

    threads = []
    for i, chunk in enumerate(proxy_chunks):
        thread = Thread(target=threaded_test_proxies, args=(chunk, i, final_list))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    setup_logger("Proxies", f"Final list before return: {final_list}")
    update_proxies_database(final_list, ui=ui)
    setup_logger("Proxies", "Finished testing proxies and updated database.")

def controllo_lista_proxies(ui):
    setup_logger("Proxies", "Inizio controllo lista proxy.")
    text_content = ui.textEdit.toPlainText()
    lines = text_content.split("\n")
    valid_proxies = []
    malformed_count = 0
    
    for line in lines:
        components = line.split(":")
        if len(components) == 4:
            ip, port, username, password = components
            if is_valid_ip(ip) and is_valid_port(port):
                valid_proxies.append(line)
            else:
                malformed_count += 1
        else:
            malformed_count += 1
    
    if malformed_count > 0:
        ui.MessageLabel.setText(f"{malformed_count} proxies sono formattati in modo errato.")
        ui.Invio.setEnabled(False)
    else:
        ui.MessageLabel.setText("Tutti i proxy sono formattati correttamente.")
        ui.Invio.setEnabled(True)

    return valid_proxies

"""
def reload_table_data(ui, thread_obj):
    setup_logger("Proxies", "Inizio del caricamento dei dati nella tabella.")
    if thread_obj is not None:
        thread_obj.init_text_edit.emit()
    
    db_path = os.path.join(os.getcwd(), 'database.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    model = QStandardItemModel()
    ui.tableView.setModel(model)

    if ui and ui.tableView:
        setup_logger("Proxies", "Esecuzione della query SQL per ottenere i dati.")
        cursor.execute("SELECT * FROM Proxies ORDER BY ID")
        data_list = cursor.fetchall()

        for i, record in enumerate(data_list):
            items = []
            for j, value in enumerate(record):
                item = QStandardItem(str(value))
                items.append(item)
            model.appendRow(items)

        setup_logger("Proxies", "Impostazioni dell'aspetto della tabella.")
        
        if thread_obj is not None:
            thread_obj.hide_first_table_column.emit()
            thread_obj.resize_table_to_contents.emit()

    if conn:
        conn.close()
        setup_logger("Proxies", "Chiusura della connessione al database.")

def scroll_table_to_bottom(ui, thread_obj):
    setup_logger("Proxies", "Scrolling della tabella verso il basso.")
    if ui and ui.tableView:
        if thread_obj is not None:
            thread_obj.scroll_table_to_bottom.emit()

def reorder_ids(conn, thread_obj):
    setup_logger("Proxies", "Inizio del riordino degli ID.")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Proxies ORDER BY ID")
        rows = cursor.fetchall()
        
        reordered_rows = []
        
        for i, row in enumerate(rows, start=1):
            old_id, IP_Address, Port, Username, Password, Working, Geo, Errori = row
            reordered_row = (i, IP_Address, Port, Username, Password, Working, Geo, Errori)
            reordered_rows.append(reordered_row)
        
        cursor.execute("DELETE FROM Proxies")
        cursor.executemany("INSERT INTO Proxies (ID, IP_Address, Port, Username, Password, Working, Geo, Errori) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", reordered_rows)
        conn.commit()
        
    except sqlite3.Error as e:
        setup_logger("Proxies", f"Errore durante il riordino del database: {e}")
        conn.rollback()

def update_proxies_database(final_list, ui=None, thread_obj=None):
    setup_logger("Proxies", "Inizio dell'aggiornamento del database dei proxy.")
    
    if thread_obj is not None:
        thread_obj.init_text_edit.emit()
    
    db_path = os.path.join(os.getcwd(), 'database.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        for proxy in final_list:
            IP_Address = proxy['ip']
            Port = proxy['port']
            Username = proxy['username']
            Password = proxy['password']
            Working = proxy['working']
            Geo = proxy['geo']
            Errori = proxy['errori']

            cursor.execute("SELECT * FROM Proxies WHERE IP_Address=? AND Port=?", (IP_Address, Port))
            existing_record = cursor.fetchone()
            
            if existing_record:
                new_errori = Errori + 1 if not Working else Errori
                cursor.execute("UPDATE Proxies SET Username=?, Password=?, Working=?, Geo=?, Errori=? WHERE IP_Address=? AND Port=?",
                               (Username, Password, Working, Geo, new_errori, IP_Address, Port))
            else:
                cursor.execute("INSERT INTO Proxies (IP_Address, Port, Username, Password, Working, Geo, Errori) VALUES (?, ?, ?, ?, ?, ?, ?)",
                               (IP_Address, Port, Username, Password, Working, Geo, Errori))
            conn.commit()

        reorder_ids(conn, thread_obj)
        
    except sqlite3.Error as e:
        setup_logger("Proxies", f"Errore durante l'aggiornamento del database: {e}")
        conn.rollback()
        
    finally:
        reload_table_data(ui, thread_obj)
        scroll_table_to_bottom(ui, thread_obj)
        
        if conn:
            conn.close()
            setup_logger("Proxies", "Chiusura della connessione al database.")
"""
def reload_table_data(ui):
    setup_logger("Proxies", "Inizio del caricamento dei dati nella tabella.")
    
    # Inizializza il TextEdit, se necessario (il codice esatto potrebbe variare)
    # ui.someTextEdit.initialize_somehow()
    
    db_path = os.path.join(os.getcwd(), 'database.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    model = QStandardItemModel()
    ui.tableView.setModel(model)

    if ui and ui.tableView:
        setup_logger("Proxies", "Esecuzione della query SQL per ottenere i dati.")
        cursor.execute("SELECT * FROM Proxies ORDER BY ID")
        data_list = cursor.fetchall()

        for i, record in enumerate(data_list):
            items = []
            for j, value in enumerate(record):
                item = QStandardItem(str(value))
                items.append(item)
            model.appendRow(items)

        setup_logger("Proxies", "Impostazioni dell'aspetto della tabella.")
        
        # Nascondi la prima colonna
        ui.tableView.hideColumn(0)
        
        # Ridimensiona le colonne in base al contenuto
        ui.tableView.resizeColumnsToContents()

    if conn:
        conn.close()
        setup_logger("Proxies", "Chiusura della connessione al database.")

def scroll_table_to_bottom(ui):
    setup_logger("Proxies", "Scrolling della tabella verso il basso.")
    if ui and ui.tableView:
        
        # Scorri la tabella fino in fondo
        ui.tableView.scrollToBottom()

def reorder_ids(conn):
    setup_logger("Proxies", "Inizio del riordino degli ID.")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Proxies ORDER BY ID")
        rows = cursor.fetchall()
        
        reordered_rows = []
        
        for i, row in enumerate(rows, start=1):
            old_id, IP_Address, Port, Username, Password, Working, Geo, Errori = row
            reordered_row = (i, IP_Address, Port, Username, Password, Working, Geo, Errori)
            reordered_rows.append(reordered_row)
        
        cursor.execute("DELETE FROM Proxies")
        cursor.executemany("INSERT INTO Proxies (ID, IP_Address, Port, Username, Password, Working, Geo, Errori) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", reordered_rows)
        conn.commit()
        
    except sqlite3.Error as e:
        setup_logger("Proxies", f"Errore durante il riordino del database: {e}")
        conn.rollback()

def update_proxies_database(final_list, ui=None):
    setup_logger("Proxies", "Inizio dell'aggiornamento del database dei proxy.")
    
    # Inizializza il TextEdit, se necessario (il codice esatto potrebbe variare)
    # ui.someTextEdit.initialize_somehow()
    
    db_path = os.path.join(os.getcwd(), 'database.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        for proxy in final_list:
            IP_Address = proxy['ip']
            Port = proxy['port']
            Username = proxy['username']
            Password = proxy['password']
            Working = proxy['working']
            Geo = proxy['geo']
            Errori = proxy['errori']

            cursor.execute("SELECT * FROM Proxies WHERE IP_Address=? AND Port=?", (IP_Address, Port))
            existing_record = cursor.fetchone()
            
            if existing_record:
                new_errori = Errori + 1 if not Working else Errori
                cursor.execute("UPDATE Proxies SET Username=?, Password=?, Working=?, Geo=?, Errori=? WHERE IP_Address=? AND Port=?",
                               (Username, Password, Working, Geo, new_errori, IP_Address, Port))
            else:
                cursor.execute("INSERT INTO Proxies (IP_Address, Port, Username, Password, Working, Geo, Errori) VALUES (?, ?, ?, ?, ?, ?, ?)",
                               (IP_Address, Port, Username, Password, Working, Geo, Errori))
            conn.commit()

        reorder_ids(conn)
        
    except sqlite3.Error as e:
        setup_logger("Proxies", f"Errore durante l'aggiornamento del database: {e}")
        conn.rollback()
        
    finally:
        reload_table_data(ui)
        scroll_table_to_bottom(ui)
        
        if conn:
            conn.close()
            setup_logger("Proxies", "Chiusura della connessione al database.")


def main():
    setup_logger("Main", "App avviata.")
    app = QtWidgets.QApplication([])
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_DigitalysationTelegramBot()
    ui.setupUi(MainWindow)
    
    loop = QEventLoop()
    QTimer.singleShot(300, loop.quit)
    loop.exec_()
    
    init_ui(ui)
    db = init_db()
    if db is None:
        sys.exit(1)
    
    init_table_view(ui, db)
    
    init_table_view(ui, db)
    enable_invio_button(ui)
    
    # Inseriamo qui proxies_ini
    proxies_ini(ui,db)
    
    MainWindow.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()