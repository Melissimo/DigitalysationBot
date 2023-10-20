import logging
import os

def setup_logger(process_type, message):
    log_folder = os.path.join(os.getcwd(), 'log')
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    # General Logger Configuration
    general_logger = logging.getLogger("General")
    general_logger.setLevel(logging.INFO)
    general_log_file = os.path.join(log_folder, "log.log")

    if not general_logger.hasHandlers():
        general_file_handler = logging.FileHandler(general_log_file, mode='a')  # Append mode
        general_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
        general_logger.addHandler(general_file_handler)
    
    # Log every message in the general log
    general_logger.info(f"{process_type}: {message}")

    # Specific Logger Configuration only for 'proxies' or 'accounts'
    if process_type.lower() in ['proxies', 'accounts']:
        specific_logger = logging.getLogger(process_type)
        specific_logger.setLevel(logging.INFO)
        specific_log_file = os.path.join(log_folder, f"{process_type.lower()}log.log")

        # Remove all handlers if it is 'accounts'
        if process_type.lower() == 'accounts':
            for handler in specific_logger.handlers[:]:
                specific_logger.removeHandler(handler)
        
        mode = 'w' if process_type.lower() == 'proxies' else 'a'  # Write mode for 'proxies', Append mode for 'accounts'
        
        specific_file_handler = logging.FileHandler(specific_log_file, mode=mode)
        specific_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
        specific_logger.addHandler(specific_file_handler)

        # Log the message in the specific log
        specific_logger.info(message)
