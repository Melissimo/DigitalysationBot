import json  # Importa il modulo json per lavorare con file JSON
import time  # Importa il modulo time per le operazioni relative al tempo
import random  # Importa il modulo random per generare numeri casuali
import asyncio  # Importa il modulo asyncio per la programmazione asincrona
import logging  # Importa il modulo logging per la registrazione degli eventi
import platform  # Importa il modulo platform per ottenere informazioni sulla piattaforma
import traceback  # Importa il modulo traceback per il debug
import configparser  # Importa il modulo configparser per leggere i file di configurazione
from pathlib import Path  # Importa Path da pathlib per lavorare con i percorsi dei file
from sqlite3 import OperationalError  # Importa OperationalError da sqlite3 per gestire errori del database
from typing import List, Dict, Union  # Importa tipi specifici da typing per annotazioni di tipo

from pyrogram.errors import ReactionInvalid, UserNotParticipant  # Importa errori specifici da pyrogram
from pyrogram.handlers.message_handler import MessageHandler  # Importa MessageHandler da pyrogram per gestire i messaggi
from pyrogram import filters, types  # Importa classi e funzioni specifiche da pyrogram
from pyrogram.errors.exceptions.unauthorized_401 import UserDeactivatedBan  # Importa un errore specifico da pyrogram
from pyrogram.client import Client
from pyrogram.sync import idle

from config import CHANNELS, POSSIBLE_KEY_NAMES, EMOJIS  # Importa variabili di configurazione da un file esterno
from converters import SessionConvertor, convert_tdata  # Importa funzioni di conversione da un file esterno
"""
if platform.system() != 'Windows':  # Controlla se il sistema operativo non è Windows
    import uvloop  # Importa uvloop se il sistema non è Windows
    uvloop.install()  # Installa uvloop
"""
TRY_AGAIN_SLEEP = 20  # Imposta un intervallo di tempo per riprovare in caso di errore

BASE_DIR = Path(__file__).parent  # Ottiene la directory base del file corrente
WORK_DIR = BASE_DIR.joinpath('sessions')  # Crea il percorso alla directory delle sessioni
LOGS_DIR = BASE_DIR.joinpath('logs')  # Crea il percorso alla directory dei log
TDATAS_DIR = BASE_DIR.joinpath('tdatas')  # Crea il percorso alla directory tdatas
SUCCESS_CONVERT_TDATA_DIR = TDATAS_DIR.joinpath('success')  # Crea il percorso alla directory dei tdata di successo
UNSUCCESSFUL_CONVERT_TDATA_DIR = TDATAS_DIR.joinpath('unsuccessful')  # Crea il percorso alla directory dei tdata non riusciti

BANNED_SESSIONS_DIR = WORK_DIR.joinpath('banned_sessions')  # Crea il percorso alla directory delle sessioni bannate
UNNECESSARY_SESSIONS_DIR = WORK_DIR.joinpath('unnecessary_sessions')  # Crea il percorso alla directory delle sessioni non necessarie

CONFIG_FILE_SUFFIXES = ('.ini', '.json')  # Definisce i suffissi dei file di configurazione supportati

LOGS_DIR.mkdir(exist_ok=True)  # Crea la directory dei log se non esiste

loggers = ['info', 'error']  # Definisce i tipi di logger
formatter = logging.Formatter('%(name)s %(asctime)s %(levelname)s %(message)s')  # Imposta il formato dei log

this_media_id = None  # Inizializza una variabile per memorizzare l'ID del media

for logger_name in loggers:  # Itera sui tipi di logger
    logger = logging.getLogger(logger_name)  # Ottiene il logger corrente
    logger.setLevel(logging.INFO)  # Imposta il livello del logger a INFO
    log_filepath = LOGS_DIR.joinpath(logger_name + '.log')  # Crea il percorso al file di log
    handler = logging.FileHandler(log_filepath)  # Crea un gestore di file di log
    handler.setFormatter(formatter)  # Imposta il formato del gestore di file di log
    logger.addHandler(handler)  # Aggiunge il gestore al logger
    logger.warning('Start reaction bot.')  # Registra un avviso nel logger

error = logging.getLogger('error')  # Ottiene il logger degli errori
info = logging.getLogger('info')  # Ottiene il logger delle informazioni

apps = []  # Inizializza una lista vuota per le app
sent = []  # Inizializza una lista vuota per i messaggi inviati


async def send_reaction(client: Client, message: types.Message) -> None:
    """Handler per inviare reazioni"""
    emoji = random.choice(EMOJIS)  # Sceglie un emoji casuale dalla lista EMOJIS
    try:
        random_sleep_time = random.randint(1, 5)  # Genera un tempo di attesa casuale tra 1 e 5 secondi
        await asyncio.sleep(random_sleep_time)  # Aspetta per il tempo generato
        await client.send_reaction(chat_id=message.chat.id, message_id=message.id, emoji=emoji)  # Invia la reazione
    except ReactionInvalid:  # Gestisce l'eccezione per una reazione non valida
        error.warning(f'{emoji} - reazione non valida')
    except UserDeactivatedBan:  # Gestisce l'eccezione per una sessione bannata
        error.warning(f'Sessione bannata - {client.name}')
    except Exception:  # Gestisce tutte le altre eccezioni
        error.warning(traceback.format_exc())
    else:
        info.info(f'Sessione {client.name} inviata - {emoji}')  # Logga l'invio della reazione se tutto va bene


async def send_reaction_from_all_applications(_, message: types.Message) -> None:
    """
    A cosa serve? Perché non assegnare semplicemente una funzione handler a ciascuna app?
    
    La risposta è semplice, se diverse sessioni hanno lo stesso API_ID e API_HASH,
    solo una di quelle sessioni invierà una risposta!
    """

    global this_media_id  # scusate :)

    post = (message.chat.id, message.id)  # Crea una tupla con l'ID della chat e l'ID del messaggio
    if post in sent:  # Controlla se il post è già stato inviato
        return
    sent.append(post)  # Aggiunge il post alla lista dei post inviati

    if this_media_id == message.media_group_id and message.media_group_id is not None:  # Controlla se l'ID del media è lo stesso e non è None
        return

    this_media_id = message.media_group_id  # Imposta l'ID del media corrente

    for app, _, _ in apps:  # Itera su tutte le app
        await send_reaction(app, message)  # Invia la reazione per ogni app

async def get_chat_id(app: Client, chat_link: str) -> Union[int, str, None]:
    """Restituisce chat_id o None o solleva un AttributeError"""
    try:
        chat = await app.get_chat(chat_link)  # Prova a ottenere le informazioni sulla chat dal link fornito
    except:
        return None  # Se fallisce, restituisce None
    else:
        return chat.id  # Altrimenti, restituisce l'ID della chat

async def is_subscribed(app: Client, chat_link: str) -> bool:
    """Controlla se il canale è sottoscritto"""
    try:
        chat_id = await get_chat_id(app, chat_link)  # Ottiene l'ID della chat
        if chat_id is None:  # Se l'ID della chat è None, restituisce False
            return False
        await app.get_chat_member(chat_id, 'me')  # Prova a ottenere le informazioni sull'utente nel canale
    except (UserNotParticipant, AttributeError):  # Se l'utente non è un partecipante o si verifica un altro errore, restituisce False
        return False
    else:
        return True  # Se tutto va bene, restituisce True

async def make_work_dir() -> None:
    """Crea la directory delle sessioni se non esiste"""
    WORK_DIR.mkdir(exist_ok=True)  # Crea la directory delle sessioni se non esiste
    UNNECESSARY_SESSIONS_DIR.mkdir(exist_ok=True)  # Crea la directory per le sessioni non necessarie se non esiste
    BANNED_SESSIONS_DIR.mkdir(exist_ok=True)  # Crea la directory per le sessioni bannate se non esiste
    TDATAS_DIR.mkdir(exist_ok=True)  # Crea la directory per i dati T se non esiste
    SUCCESS_CONVERT_TDATA_DIR.mkdir(exist_ok=True)  # Crea la directory per i dati T convertiti con successo se non esiste
    UNSUCCESSFUL_CONVERT_TDATA_DIR.mkdir(exist_ok=True)  # Crea la directory per i dati T non convertiti con successo se non esiste

async def get_config_files_path() -> List[Path]:
    """Prende tutti i file di configurazione"""
    return [file for file in WORK_DIR.iterdir() if file.suffix.lower() in CONFIG_FILE_SUFFIXES]
    # Restituisce una lista di percorsi di file che hanno un suffisso corrispondente ai tipi di file di configurazione supportati

async def config_from_ini_file(file_path: Path) -> Dict:
    """Estrae la configurazione dal file *.ini"""
    config_parser = configparser.ConfigParser()
    config_parser.read(file_path)
    section = config_parser.sections()[0]
    return {**config_parser[section]}
    # Legge il file .ini e restituisce un dizionario con le informazioni di configurazione

async def config_from_json_file(file_path: Path) -> Dict:
    """Estrae la configurazione dal file *.json"""
    with open(file_path) as f:
        return json.load(f)
    # Legge il file .json e restituisce un dizionario con le informazioni di configurazione

async def get_config(file_path: Path) -> Dict:
    """Restituisce il file di configurazione al percorso"""
    config_suffixes = {
        '.ini': config_from_ini_file,
        '.json': config_from_json_file,
    }
    suffix = file_path.suffix.lower()
    config = await config_suffixes[suffix](file_path)
    normalized_confing = {'name': file_path.stem}
    for key, values in POSSIBLE_KEY_NAMES.items():
        for value in values:
            if not config.get(value):
                continue
            normalized_confing[key] = config[value]
            break
    return normalized_confing
    # Normalizza le informazioni di configurazione e restituisce un dizionario

async def create_apps(config_files_paths: List[Path]) -> None:
    """
    Crea istanze 'Client' dai file di configurazione.
    **Se non c'è una chiave 'name' nel file di configurazione, allora il file di configurazione ha lo stesso nome della sessione!**
    """
    for config_file_path in config_files_paths:
        try:
            config_dict = await get_config(config_file_path)
            session_file_path = WORK_DIR.joinpath(config_file_path.with_suffix('.session'))
            apps.append((Client(workdir=WORK_DIR.__str__(), **config_dict), config_dict, session_file_path))
        except Exception:
            error.warning(traceback.format_exc())
    # Crea istanze del client Pyrogram in base ai file di configurazione e le aggiunge alla lista 'apps'

async def try_convert(session_path: Path, config: Dict) -> bool:
    """Prova a convertire la sessione se la sessione non riesce ad avviarsi in Pyrogram"""
    convertor = SessionConvertor(session_path, config, WORK_DIR)
    try:
        await convertor.convert()
    except OperationalError:
        if session_path.exists():
            await convertor.move_file_to_unnecessary(session_path)
        for suffix in CONFIG_FILE_SUFFIXES:
            config_file_path = session_path.with_suffix(suffix)
            if config_file_path.exists():
                await convertor.move_file_to_unnecessary(config_file_path)
        error.warning('La conservazione della sessione è fallita ' + session_path.stem)
        return False
    except Exception:
        error.warning(traceback.format_exc())
        return False
    else:
        return True
    # Prova a convertire il file di sessione. Se fallisce, sposta il file in una directory per file "non necessari".

def get_tdatas_paths() -> List[Path]:
    """Ottiene i percorsi alle directory tdata"""
    reserved_dirs = [SUCCESS_CONVERT_TDATA_DIR, UNSUCCESSFUL_CONVERT_TDATA_DIR]
    return [path for path in TDATAS_DIR.iterdir() if path not in reserved_dirs]
    # Restituisce una lista di percorsi alle directory tdata, escludendo le directory riservate.

async def move_session_to_ban_dir(session_path: Path):
    """Sposta il file nella directory dei ban"""
    if session_path.exists():
        await move_file(session_path, BANNED_SESSIONS_DIR)
    for suffix in CONFIG_FILE_SUFFIXES:
        config_file_path = session_path.with_suffix(suffix)
        if not config_file_path.exists():
            continue
        await move_file(config_file_path, BANNED_SESSIONS_DIR)
    # Sposta il file di sessione e il relativo file di configurazione nella directory dei file bannati.


async def move_file(path_from: Path, path_to: Path):
    """Spostamento di file o directory"""
    # Rinomina il percorso del file o della directory.
    path_from.rename(path_to.joinpath(path_from.name))

async def main():
    """
    Funzione principale:
        - Crea una directory di sessioni se non è già stata creata.
        - Prende tutti i file di configurazione (*.json, *.ini)
        - Crea client dai loro file di configurazione.
        - Esegue attraverso i client, aggiunge un gestore, avvia e unisce la chat.
        - Aspetta il completamento e termina (infinitamente)
    """
    await make_work_dir()
    # Crea la directory di lavoro se non esiste.

    tdatas_paths = get_tdatas_paths()
    # Ottiene i percorsi ai file tdata.

    for tdata_path in tdatas_paths:
        try:
            await convert_tdata(tdata_path, WORK_DIR)
            # Prova a convertire i dati tdata.
        except Exception:
            error.warning(traceback.format_exc())
            await move_file(tdata_path, UNSUCCESSFUL_CONVERT_TDATA_DIR)
            # Se fallisce, sposta il file nella directory degli insuccessi.
        else:
            await move_file(tdata_path, SUCCESS_CONVERT_TDATA_DIR)
            # Se riesce, sposta il file nella directory dei successi.

    config_files = await get_config_files_path()
    # Ottiene i percorsi ai file di configurazione.

    await create_apps(config_files)
    # Crea le applicazioni client dai file di configurazione.

    if not apps:
        raise Exception('No apps!')
        # Solleva un'eccezione se non ci sono applicazioni.

    message_handler = MessageHandler(send_reaction_from_all_applications, filters=filters.chat(CHANNELS))
    # Crea un gestore di messaggi.

    for app, config_dict, session_file_path in apps:
        app.add_handler(message_handler)
        # Aggiunge il gestore di messaggi all'applicazione.

        try:
            await app.start()
            # Prova ad avviare l'applicazione.
        except OperationalError:
            is_converted = await try_convert(session_file_path, config_dict)
            # Se c'è un errore operativo, prova a convertire la sessione.

            apps.remove((app, config_dict, session_file_path))
            # Rimuove l'applicazione dalla lista.

            if not is_converted:
                info.info(f'Did not convert - {app.name}')
                continue
                # Se la conversione fallisce, continua il ciclo.

            try:
                app = Client(workdir=WORK_DIR.__str__(), **config_dict)
                app.add_handler(message_handler)
                await app.start()
                # Prova a creare e avviare una nuova applicazione client.
            except Exception:
                error.warning(traceback.format_exc())
                # Registra l'errore se c'è un'eccezione.
            else:
                apps.append((app, config_dict, session_file_path))
                # Aggiunge la nuova applicazione alla lista se ha successo.

        except UserDeactivatedBan:
            await move_session_to_ban_dir(session_file_path)
            error.warning(f'Session banned - {app.name}')
            apps.remove((app, config_dict, session_file_path))
            continue
            # Se l'utente è bannato, sposta la sessione nella directory dei bannati e continua.

        except Exception:
            apps.remove((app, config_dict, session_file_path))
            error.warning(traceback.format_exc())
            continue
            # Se c'è un'altra eccezione, rimuove l'applicazione e continua.

        info.info(f'Session started - {app.name}')
        # Registra l'avvio della sessione.

        for channel in CHANNELS:
            subscribed = await is_subscribed(app, channel)
            # Controlla se l'applicazione è iscritta al canale.

            if not subscribed:
                random_sleep_time = random.randint(1, 10)
                await asyncio.sleep(random_sleep_time)
                await app.join_chat(channel)
                info.info(f'{app.name} joined - "@{channel}"')
                # Se non è iscritta, attende un tempo casuale e poi si unisce al canale.

    if not apps:
        raise Exception('No apps!')
        # Solleva un'eccezione se non ci sono applicazioni.

    info.warning('All sessions started!')
    await idle()
    # Registra l'avvio di tutte le sessioni e attende.

    for app, _, _ in apps:
        try:
            info.warning(f'Stopped - {app.name}')
            await app.stop()
            # Prova a fermare l'applicazione.
        except ConnectionError:
            pass
            # Ignora gli errori di connessione.

    apps[:] = []
    # Svuota la lista delle applicazioni.

def start():
    """Iniziamo"""
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
        # Esegue la funzione principale fino al completamento.
    except Exception:
        error.critical(traceback.format_exc())
        error.warning(f'Aspettando {TRY_AGAIN_SLEEP} sec. prima di riavviare il programma...')
        time.sleep(TRY_AGAIN_SLEEP)
        # Se c'è un'eccezione, attende un po' e poi riprova.

if __name__ == '__main__':
    while True:
        start()
        # Se questo script è il punto di ingresso, esegue la funzione start() in un ciclo infinito.
