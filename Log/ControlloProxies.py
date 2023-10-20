from PyQt5.QtCore import QTimer
import ProxyTester  # Assume that the testing function is in a module called ProxyTester
import re
from Custom_Logger import setup_logger  # Import setup_logger

def is_valid_ip(ip):
    setup_logger("Proxies", "Verifica validità IP.")
    pattern = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
    return bool(pattern.match(ip))

def is_valid_port(port):
    setup_logger("Proxies","Verifica validità porta.")
    return port.isdigit() and (1000 <= int(port) <= 65535)

def controllo_lista_proxies(thread_obj):
    setup_logger("Proxies","Inizio controllo lista proxy.")
    thread_obj.buttonStatusChanged.emit(False)  # Emits signal to disable button
    text_content = thread_obj.ui.textEdit.toPlainText()
    lines = text_content.split("\n")

    if not lines or all(not line.strip() for line in lines):
        setup_logger("Proxies","Nessun proxy inserito.")
        thread_obj.validationStatusUpdated.emit("Nessun proxy inserito. Inserisci i proxies secondo questo formato:\nIP Address:Port:Username:Password")
        thread_obj.buttonStatusChanged.emit(True)
        return

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
        elif len(components) == 2:
            ip, port = components
            if is_valid_ip(ip) and is_valid_port(port):
                valid_proxies.append(f"{ip}:{port}::")
            else:
                malformed_count += 1
        else:
            malformed_count += 1

    if not valid_proxies:
        setup_logger("Proxies","Nessun proxy valido rilevato.")
        thread_obj.validationStatusUpdated.emit("Nessun proxy rilevato: riprova. Inserisci i proxies secondo questo formato:\nIP Address:Port:Username:Password")
        thread_obj.buttonStatusChanged.emit(True)
        return

    if malformed_count > 0:
        setup_logger("Proxies", f"{malformed_count} proxies malformati rimossi.")
        thread_obj.validationStatusUpdated.emit(f"Sono stati eliminati {malformed_count} proxies perché malformati.")

    QTimer.singleShot(3000, lambda: execute_test_and_update(valid_proxies, thread_obj))

def execute_test_and_update(valid_proxies, thread_obj):
    setup_logger("Proxies","Inizio test proxy.")
    try:
        ProxyTester.test_proxies(valid_proxies, thread_obj=thread_obj)
    finally:
        thread_obj.buttonStatusChanged.emit(True)  # Emits signal to enable button
        thread_obj.validationStatusUpdated.emit("Test completato. Il database è stato aggiornato")
        setup_logger("Proxies","Test proxy completato.")
