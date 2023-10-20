import struct  # Per la manipolazione di dati binari
import base64  # Per la codifica e decodifica in base64
import sqlite3  # Per la gestione del database SQLite
from pathlib import Path  # Per la manipolazione dei percorsi dei file
from typing import Union, Dict, Tuple, Coroutine, Any  # Per la tipizzazione statica
from telethon import TelegramClient  # Client Telethon per interagire con l'API di Telegram
from telethon.sessions import StringSession  # Per la gestione delle sessioni in Telethon
from telethon.tl.types import User  # Per rappresentare un utente Telegram
from pyrogram.client import Client # Client Pyrogram per interagire con l'API di Telegram
from pyrogram.storage.file_storage import FileStorage # Per la gestione della memorizzazione delle sessioni
from pyrogram.storage.storage import Storage

import logging  # Importa il modulo di logging

# Configura il logging
logging.basicConfig(level=logging.ERROR)

class SessionConvertor:
    def __init__(self, session_path: Path, config: Dict, work_dir: Path):
        try:
            if work_dir is None:  # Controllo se work_dir è None
                work_dir = Path(__file__).parent.parent.joinpath('sessions')  # Imposta il percorso di default
            self.session_path = session_path if session_path else work_dir  # Imposta il percorso della sessione
            self.inappropriate_sessions_path = work_dir.joinpath('unnecessary_sessions')  # Percorso per sessioni inutili
            self.api_id = config['api_id'] if config else None  # Imposta api_id
            self.api_hash = config['api_hash'] if config else None  # Imposta api_hash
            self.work_dir = work_dir  # Imposta la directory di lavoro
        except Exception as e:
            logging.error(f"Errore nell'inizializzazione di SessionConvertor: {e}")
            raise

    async def convert(self) -> None:  # Funzione principale per la conversione
        try:
            """Main func"""
            user_data, session_data = await self.__get_data_telethon_session()  # Ottiene i dati della sessione Telethon
            converted_sting_session = await self.get_converted_sting_session(session_data, user_data)  # Converte la sessione
            await self.move_file_to_unnecessary(self.session_path)  # Sposta il file di sessione inutile
            await self.save_pyrogram_session_file(converted_sting_session, session_data)  # Salva la nuova sessione Pyrogram
        except Exception as e:
            logging.error(f"Errore nella funzione convert: {e}")
            raise

    async def move_file_to_unnecessary(self, file_path: Path):  # Sposta i file di sessione inutili
        """Move the unnecessary Telethon session file to the directory with the unnecessary sessions"""
        if file_path.exists():  # Controlla se il file esiste
            file_path.rename(self.inappropriate_sessions_path.joinpath(file_path.name))  # Rinomina e sposta il file

    async def __get_data_telethon_session(self) -> Tuple[User, StringSession]:  # Ottiene dati della sessione Telethon
        try:
            """Get User and StringSession"""
            async with TelegramClient(self.session_path.with_suffix('').__str__(), self.api_id, self.api_hash) as client:  # Crea un client Telegram
                user_data = await client.get_me()  # Ottiene i dati dell'utente
                string_session = StringSession.save(client.session)  # Salva la sessione come stringa
                session_data = StringSession(string_session)  # Crea un oggetto StringSession
                return user_data, session_data  # Ritorna i dati dell'utente e della sessione
        except Exception as e:
            logging.error(f"Errore nella funzione __get_data_telethon_session: {e}")
            raise

    async def save_pyrogram_session_file(self, session_string: Union[str, Coroutine[Any, Any, str]],
                                         session_data: StringSession):  # Crea un file di sessione per Pyrogram
        try:
            """Create session file for pyrogram"""
            async with Client(self.session_path.stem, session_string=session_string, api_id=self.api_id,
                              api_hash=self.api_hash, workdir=self.work_dir.__str__()) as client:  # Crea un client Pyrogram
                user_data = await client.get_me()  # Ottiene i dati dell'utente
                client.storage = FileStorage(self.session_path.stem, self.work_dir)  # Imposta lo storage del client
                client.storage.conn = sqlite3.Connection(self.session_path)  # Crea una connessione SQLite
                client.storage.create()  # Crea il database
                await client.storage.dc_id(session_data.dc_id)  # Imposta l'ID del data center
                await client.storage.test_mode(False)  # Imposta la modalità di test a False
                await client.storage.auth_key(session_data.auth_key.key)  # Imposta la chiave di autenticazione
                await client.storage.user_id(user_data.id)  # Imposta l'ID dell'utente
                await client.storage.date(0)  # Imposta la data
                await client.storage.is_bot(False)  # Imposta se è un bot o meno
                await client.storage.save()  # Salva i dati della sessione
        except Exception as e:
            logging.error(f"Errore nella funzione save_pyrogram_session_file: {e}")
            raise



    @staticmethod
    async def get_converted_sting_session(session_data: StringSession, user_data: User) -> str:  # Converte in una sessione stringa
        """Convert to sting session"""
        pack = [  # Crea una lista con i dati della sessione e dell'utente
            Storage.SESSION_STRING_FORMAT,
            session_data.dc_id,
            None,
            session_data.auth_key.key,
            user_data.id,
            user_data.bot
        ]
        try:
            bytes_pack = struct.pack(*pack)  # Prova a impacchettare i dati in un oggetto bytes
        except struct.error as e:  # Gestisce l'errore se la struttura non è valida
            logging.error(f"Errore nella funzione get_converted_sting_session durante la prima impacchettazione: {e}")
            pack[0] = Storage.OLD_SESSION_STRING_FORMAT_64  # Usa un formato di sessione più vecchio
            try:
                bytes_pack = struct.pack(*pack)  # Impacchetta nuovamente i dati
            except struct.error as e:
                logging.error(f"Errore nella funzione get_converted_sting_session durante la seconda impacchettazione: {e}")
                raise

        encode_pack = base64.urlsafe_b64encode(bytes_pack)  # Codifica i dati in base64
        decode_pack = encode_pack.decode()  # Decodifica i dati in una stringa
        sting_session = decode_pack.rstrip("=")  # Rimuove eventuali "=" alla fine della stringa
        return sting_session  # Ritorna la sessione come stringa
