import io  # Utilizzato per la manipolazione di stream di byte
import json  # Utilizzato per la serializzazione e deserializzazione JSON
import os  # Utilizzato per le operazioni di sistema operativo
import struct  # Utilizzato per interpretare dati impacchettati come oggetti Python
import hashlib  # Utilizzato per l'hashing (SHA-1, MD5, etc.)
import ipaddress  # Utilizzato per la manipolazione e l'analisi degli indirizzi IP
from typing import Union  # Per i tipi di unione nei suggerimenti di tipo
from pathlib import Path  # Utilizzato per la manipolazione del percorso del file system
from base64 import urlsafe_b64encode  # Utilizzato per l'encoding in base64
import sqlite3
import os
import cryptg  # Libreria per la crittografia
from telethon.sync import TelegramClient  # Client Telegram
from telethon.sessions import StringSession  # Sessioni di Telethon
from telethon_to_pyrogram import SessionConvertor  # Convertitore di sessione da Telethon a Pyrogram
import Proxy_selector
import logging  # Utilizzato per il logging

# Configurazione del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Trova la directory corrente e crea il percorso completo al file del database
current_dir = os.path.dirname(os.path.abspath(__file__))
database_path = os.path.join(current_dir, "database.db")

# Stabilisce una connessione al database
try:
    conn = sqlite3.connect(database_path)
except Exception as e:
    logging.error(f'Errore durante la connessione al database: {e}')
    exit(1)

# Creazione di un oggetto cursore
cursor = conn.cursor()

# Esecuzione della query per selezionare i dati dalla tabella
query = "SELECT Api_Id, Api_Hash FROM Automation_sessions WHERE ID = ?"
try:
    cursor.execute(query, (1,))  # Sostituisci 1 con l'ID desiderato
except Exception as e:
    logging.error(f'Errore durante l\'esecuzione della query: {e}')
    exit(1)

# Recupero dei dati
try:
    api_data = cursor.fetchone()
except Exception as e:
    logging.error(f'Errore durante il recupero dei dati: {e}')
    exit(1)

# Verifica se i dati sono stati recuperati
if api_data is not None:
    API_ID = api_data[0]  # Assegnazione diretta da campo Api_Id
    API_HASH = api_data[1]  # Assegnazione diretta da campo Api_Hash
    logging.info('Dati recuperati con successo.')
else:
    logging.warning('Nessun dato trovato per l\'ID specificato.')

# Configurazione del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Assegnazione proxy più veloce
try:
    best_proxy = Proxy_selector.get_best_working_proxy(conn)
except Exception as e:
    logging.error(f'Errore durante l\'assegnazione del miglior proxy: {e}')
    exit(1)

# Tabella che mappa i Data Centers (DC) di Telegram ai loro indirizzi IP e porte
DC_TABLE = {
    1: ('149.154.175.50', 443),
    2: ('149.154.167.51', 443),
    3: ('149.154.175.100', 443),
    4: ('149.154.167.91', 443),
    5: ('149.154.171.5', 443),
}

# Classe per leggere flussi di dati (stream)
class QDataStream:
    def __init__(self, data):  # Costruttore
        try:
            self.stream = io.BytesIO(data)  # Inizializza uno stream di byte
        except Exception as e:
            logging.error(f'Errore durante l\'inizializzazione dello stream di byte: {e}')
            exit(1)

    def read(self, n=None):  # Metodo per leggere n byte dallo stream
        try:
            if n < 0:  # Se n è minore di zero, imposta n a zero
                n = 0
            data = self.stream.read(n)  # Legge n byte
            if n != 0 and len(data) == 0:  # Controlla la fine del file (EOF)
                return None
            if n is not None and len(data) != n:  # Solleva un'eccezione se non riesce a leggere n byte
                raise Exception('unexpected eof')
            return data  # Ritorna i dati letti
        except Exception as e:
            logging.error(f'Errore durante la lettura dello stream: {e}')
            exit(1)

    def read_buffer(self):  # Metodo per leggere un buffer
        try:
            length_bytes = self.read(4)  # Legge 4 byte per determinare la lunghezza del buffer
            if length_bytes is None:  # Controlla la fine del file
                return None
            length = int.from_bytes(length_bytes, 'big', signed=True)  # Converte i byte della lunghezza in un intero
            data = self.read(length)  # Legge i dati del buffer
            if data is None:  # Controlla la fine del file
                raise Exception('unexpected eof')
            return data  # Ritorna i dati letti
        except Exception as e:
            logging.error(f'Errore durante la lettura del buffer: {e}')
            exit(1)

def read_uint32(self):
    try:
        data = self.read(4)  # Legge 4 byte dal flusso di dati
        if data is None:     # Controlla se i dati letti sono None (cioè, se sono terminati i dati nel flusso)
            return None      # Restituisce None se non ci sono dati
        return int.from_bytes(data, 'big')  # Converte i 4 byte letti in un intero senza segno (big endian)
    except Exception as e:
        logging.error(f'Errore durante la lettura di un intero a 32 bit: {e}')
        exit(1)

def read_uint64(self):
    try:
        data = self.read(8)  # Legge 8 byte dal flusso di dati
        if data is None:     # Stesso controllo di sopra
            return None
        return int.from_bytes(data, 'big')  # Converte gli 8 byte letti in un intero senza segno (big endian)
    except Exception as e:
        logging.error(f'Errore durante la lettura di un intero a 64 bit: {e}')
        exit(1)

def read_int32(self):
    try:
        data = self.read(4)  # Legge 4 byte dal flusso di dati
        if data is None:     # Stesso controllo di sopra
            return None
        return int.from_bytes(data, 'big', signed=True)  # Converte i 4 byte letti in un intero con segno (big endian)
    except Exception as e:
        logging.error(f'Errore durante la lettura di un intero a 32 bit con segno: {e}')
        exit(1)

def create_local_key(passcode, salt):
    try:
        if passcode:                  
            iterations = 100_000      # Se è presente un passcode, usa 100.000 iterazioni
        else:
            iterations = 1           # Altrimenti usa solo 1 iterazione
        _hash = hashlib.sha512(salt + passcode + salt).digest()  # Calcola l'hash SHA-512
        return hashlib.pbkdf2_hmac('sha512', _hash, salt, iterations, 256)  # Crea una chiave locale usando PBKDF2
    except Exception as e:
        logging.error(f'Errore durante la creazione della chiave locale: {e}')
        exit(1)

def prepare_aes_oldmtp(auth_key, msg_key, send):                    # Definizione della funzione per preparare la cifratura AES
    try:
        if send:                                                         # Controllo se i dati sono in uscita
            x = 0  # Se i dati sono in uscita                             # Imposta x a 0 per dati in uscita
        else:                                                           
            x = 8  # Se i dati sono in entrata                            # Imposta x a 8 per dati in entrata
        
        # Le seguenti linee calcolano vari hash SHA-1 su porzioni dell'auth_key e del msg_key  # Commento generale sul calcolo degli hash
        sha1 = hashlib.sha1()                                            # Inizializza l'oggetto SHA-1
        sha1.update(msg_key)                                             # Aggiorna con msg_key
        sha1.update(auth_key[x:][:32])                                   # Aggiorna con una porzione di auth_key
        a = sha1.digest()                                                # Ottiene l'hash per 'a'

        sha1 = hashlib.sha1()                                            # Reinizializza l'oggetto SHA-1
        sha1.update(auth_key[32 + x:][:16])                              # Aggiorna con una porzione di auth_key
        sha1.update(msg_key)                                             # Aggiorna con msg_key
        sha1.update(auth_key[48 + x:][:16])                              # Aggiorna con un'altra porzione di auth_key
        b = sha1.digest()                                                # Ottiene l'hash per 'b'

        sha1 = hashlib.sha1()                                            # Reinizializza l'oggetto SHA-1
        sha1.update(auth_key[64 + x:][:32])                              # Aggiorna con una porzione di auth_key
        sha1.update(msg_key)                                             # Aggiorna con msg_key
        c = sha1.digest()                                                # Ottiene l'hash per 'c'

        sha1 = hashlib.sha1()                                            # Reinizializza l'oggetto SHA-1
        sha1.update(msg_key)                                             # Aggiorna con msg_key
        sha1.update(auth_key[96 + x:][:32])                              # Aggiorna con una porzione di auth_key
        d = sha1.digest()                                                # Ottiene l'hash per 'd'
        
        # Crea chiave e vettore di inizializzazione (IV) per la cifratura AES  # Commento generale sulla creazione di chiave e IV
        key = a[:8] + b[8:] + c[4:16]                                    # Crea la chiave AES
        iv = a[8:] + b[:8] + c[16:] + d[:8]                              # Crea il vettore di inizializzazione (IV)
        return key, iv                                                    # Ritorna chiave e IV
    except Exception as e:
        logging.error(f'Errore durante la preparazione della cifratura AES: {e}')
        exit(1)

def aes_decrypt_local(ciphertext, auth_key, key_128):  # Definizione della funzione per la decifratura AES
    try:
        key, iv = prepare_aes_oldmtp(auth_key, key_128, False)  # Prepara chiave e IV usando una funzione ausiliaria
        return cryptg.decrypt_ige(ciphertext, key, iv)  # Esegue la decifratura e ritorna il testo in chiaro
    except Exception as e:
        logging.error(f'Errore durante la decifratura AES locale: {e}')
        exit(1)

def decrypt_local(data, key):  # Definizione della funzione per la decifratura locale
    try:
        encrypted_key = data[:16]  # Estrae la chiave cifrata dai dati
        data = aes_decrypt_local(data[16:], key, encrypted_key)  # Decifra i dati rimanenti
        sha1 = hashlib.sha1()  # Inizializza l'oggetto SHA-1
        sha1.update(data)  # Aggiorna con i dati decifrati
        if encrypted_key != sha1.digest()[:16]:  # Verifica l'integrità dei dati
            raise Exception('failed to decrypt')  # Solleva un'eccezione in caso di fallimento
        length = int.from_bytes(data[:4], 'little')  # Estrae la lunghezza dei dati
        data = data[4:length]  # Estrae i dati effettivi
        return QDataStream(data)  # Ritorna un oggetto QDataStream
    except Exception as e:
        logging.error(f'Errore durante la decifratura locale: {e}')
        exit(1)

def read_file(name):  # Definizione della funzione per la lettura del file
    try:
        with open(name, 'rb') as f:  # Apre il file in modalità binaria
            magic = f.read(4)  # Legge il magic number
            if magic != b'TDF$':  # Controlla il magic number
                raise Exception('invalid magic')  # Solleva un'eccezione se il magic number è invalido
            version_bytes = f.read(4)  # Legge la versione del file
            data = f.read()  # Legge i dati rimanenti
        data, digest = data[:-16], data[-16:]  # Separa i dati dal digest MD5
        data_len_bytes = len(data).to_bytes(4, 'little')  # Converte la lunghezza dei dati in byte
        md5 = hashlib.md5()  # Inizializza l'oggetto MD5
        md5.update(data)  # Aggiorna con i dati
        md5.update(data_len_bytes)  # Aggiorna con la lunghezza dei dati in byte
        md5.update(version_bytes)  # Aggiorna con la versione del file
        md5.update(magic)  # Aggiorna con il magic number
        digest = md5.digest()  # Calcola il digest MD5
        if md5.digest() != digest:  # Verifica l'integrità dei dati
            raise Exception('invalid digest')  # Solleva un'eccezione se il digest è invalido
        return QDataStream(data)  # Ritorna un oggetto QDataStream
    except Exception as e:
        logging.error(f'Errore durante la lettura del file: {e}')
        exit(1)

# Legge un file cifrato dal disco e lo decifra
def read_encrypted_file(name, key):
    try:
        stream = read_file(name)  # Legge il file usando la funzione ausiliaria
        encrypted_data = stream.read_buffer()  # Legge i dati cifrati
        return decrypt_local(encrypted_data, key)  # Decifra i dati e ritorna il risultato
    except Exception as e:
        logging.error(f'Errore durante la lettura del file cifrato: {e}')
        raise

def account_data_string(index=0):
    try:
        s = 'data'  # Inizializza la stringa con "data"
        if index > 0:  # Controlla se l'indice è maggiore di zero
            s += f'#{index + 1}'  # Aggiunge un numero all'estremità della stringa
        md5 = hashlib.md5()  # Crea un nuovo oggetto hash MD5
        md5.update(bytes(s, 'utf-8'))  # Aggiorna l'hash con la stringa codificata in UTF-8
        digest = md5.digest()  # Ottiene il digest dell'hash
        return digest[:8][::-1].hex().upper()[::-1]  # Restituisce una sottostringa dell'hash in esadecimale e maiuscolo
    except Exception as e:
        logging.error(f'Errore nella funzione account_data_string: {e}')
        raise

def read_user_auth(directory, local_key, index=0):
    try:
        name = account_data_string(index)  # Ottiene il nome del file dall'indice
        path = os.path.join(directory, f'{name}s')  # Costruisce il percorso completo del file
        stream = read_encrypted_file(path, local_key)  # Legge il file cifrato
        if stream.read_uint32() != 0x4B:  # Controlla un valore magico per verificare il formato del file
            raise Exception('unsupported user auth config')  # Solleva un'eccezione se il formato non è supportato
        stream = QDataStream(stream.read_buffer())  # Legge il buffer dal flusso
        user_id = stream.read_uint32()  # Legge l'ID utente
        main_dc = stream.read_uint32()  # Legge il data center principale
        # ... (il resto del codice è omesso per brevità)
    except Exception as e:
        logging.error(f'Errore nella funzione read_user_auth: {e}')
        raise

def build_session(dc, ip, port, key):
    try:
        ip_bytes = ipaddress.ip_address(ip).packed  # Converte l'indirizzo IP in una forma binaria
        data = struct.pack('>B4sH256s', dc, ip_bytes, port, key)  # Impacchetta i dati in una stringa binaria
        encoded_data = urlsafe_b64encode(data).decode('ascii')  # Codifica i dati in base64 e decodifica in ASCII
        return '1' + encoded_data  # Aggiunge un "1" all'inizio e restituisce la stringa
    except Exception as e:
        logging.error(f'Errore nella funzione build_session: {e}')
        raise

# Conversione asincrona dei dati della sessione da Telethon a Pyrogram
async def convert_tdata(path: Union[str, Path], work_dir: Path):
    try:
        # Legge le informazioni dal file 'key_datas'
        stream = read_file(os.path.join(path, 'key_datas'))  # Legge il file 'key_datas' e lo memorizza in 'stream'
        salt = stream.read_buffer()  # Legge il sale dal flusso
        key_encrypted = stream.read_buffer()  # Legge la chiave cifrata dal flusso
        info_encrypted = stream.read_buffer()  # Legge le informazioni cifrate dal flusso

        # Decifra la chiave interna
        passcode_key = create_local_key(b'', salt)  # Crea una chiave locale utilizzando il sale
        key_inner_data = decrypt_local(key_encrypted, passcode_key)  # Decifra la chiave utilizzando la chiave locale
        local_key = key_inner_data.read(256)  # Legge i primi 256 byte della chiave decifrata

        # Decifra i dati delle informazioni
        info_data = decrypt_local(info_encrypted, local_key)  # Decifra le informazioni utilizzando la chiave locale
        count = info_data.read_uint32()  # Legge il numero di elementi da processare
        auth_key = []  # Inizializza una lista vuota per memorizzare le chiavi di autenticazione
        for _ in range(count):  # Itera per ogni elemento
            index = info_data.read_uint32()  # Legge l'indice corrente
            dc, key = read_user_auth(path, local_key, index)  # Legge i dati di autenticazione per l'indice corrente
            ip, port = DC_TABLE[dc]  # Ottiene l'indirizzo IP e la porta dal data center
            session = build_session(dc, ip, port, key)  # Costruisce una sessione
            auth_key.append(session)  # Aggiunge la sessione alla lista delle chiavi di autenticazione

        # Conversione effettiva
        await convert_telethon_session_to_pyrogram(auth_key, work_dir)  # Converte la sessione da Telethon a Pyrogram in modo asincrono
    except Exception as e:
        logging.error(f'Errore nella funzione convert_tdata: {e}')
        raise

# Salva il file di configurazione JSON
def save_config(work_dir: Path, phone: str, config: dict):
    try:
        config_path = work_dir.joinpath(phone + '.json')  # Crea il percorso del file di configurazione
        with open(config_path, 'w') as config_file:  # Apre il file in modalità scrittura
            json.dump(config, config_file)  # Salva il dizionario di configurazione nel file JSON
    except Exception as e:
        logging.error(f'Errore nella funzione save_config: {e}')
        raise

async def convert_telethon_session_to_pyrogram(auth_key, work_dir: Path, best_proxy=None):
    try:
        proxy = None  # Inizializza la variabile proxy a None
        if best_proxy:  # Controlla se è stato fornito un proxy
            ip, port, username, password = best_proxy[1], best_proxy[2], best_proxy[3], best_proxy[4]  # Estrae i dettagli del proxy
            proxy = (ip, int(port), username, password)  # Crea una tupla con i dettagli del proxy

        session = StringSession(auth_key[0])  # Crea una nuova sessione con la prima chiave di autenticazione
        async with TelegramClient(session, api_hash=API_HASH, api_id=API_ID, proxy=proxy) as client:  # Crea un client Telegram asincrono
            await client.connect()  # Tenta di connettersi al server Telegram
            _ = await client.get_me()  # Ottiene le informazioni sull'utente corrente

            # Ottenere i dati utente
            user_data = await client.get_me()  # Ottiene i dati dell'utente
            string_session = StringSession.save(client.session)  # Salva la sessione corrente come stringa
            session_data = StringSession(string_session)  # Crea una nuova sessione dalla stringa salvata
            phone = user_data.phone  # Estrae il numero di telefono dall'utente

            # Salva la configurazione e la sessione Pyrogram
            session_path = work_dir.joinpath(f'{phone}.session')  # Crea il percorso del file di sessione
            config = {  # Crea un dizionario con i dati di configurazione
                'phone': phone,
                'api_id': API_ID,
                'api_hash': API_HASH,
            }
            save_config(work_dir, phone, config)  # Chiama la funzione per salvare il file di configurazione
            converter = SessionConvertor(session_path, config, work_dir)  # Crea un nuovo convertitore di sessione
            converted_session = await converter.get_converted_sting_session(session_data, user_data)  # Ottiene la sessione convertita
            await converter.save_pyrogram_session_file(converted_session, session_data)  # Salva il file di sessione Pyrogram
    except Exception as e:
        logging.error(f'Errore nella funzione convert_telethon_session_to_pyrogram: {e}')
        raise
