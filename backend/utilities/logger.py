import os
import datetime
import inspect
from dotenv import load_dotenv


def get_function_name():
    # Get the current function name dynamically
    frame = inspect.currentframe()
    function_name = inspect.getframeinfo(frame.f_back).function
    return function_name


def log_info(message):
    log_message('INFO', message)


def log_error(error_message, model_name_or_func=None):
    log_message('ERROR', f'{model_name_or_func}: {error_message}')


def log_warning(warning_message, model_name_or_func=None):
    log_message('WARNING', f'{model_name_or_func}: {warning_message}')


# Do not directly call log_message. Call log_info, log_error, log_warning instead.
def log_message(log_level, message):
    # Create the directory if it doesn't exist
    log_directory = './log'
    now = datetime.datetime.now()
    date_format = now.strftime("%y%m%d")

    os.makedirs(log_directory, exist_ok=True)
    log_file_name = f"{date_format}_audit.log"
    log_file_path = os.path.abspath(os.path.join(log_directory, log_file_name))

    # Log the message to a file or perform other error handling actions
    with open(log_file_path, 'a') as f:
        log_entry = f"{now} [{log_level}] {message}\n"
        f.write(log_entry)

    # If log level is error, append to another error log
    if log_level in ['ERROR', 'WARNING', 'CRITICAL', 'FATAL']:
        log_error_file_name = f"{date_format}_error.log"
        log_error_file_path = os.path.abspath(os.path.join(log_directory, log_error_file_name))
        with open(log_error_file_path, 'a') as f:
            log_entry = f"{now} [{log_level}] {message}\n"
            f.write(log_entry)
