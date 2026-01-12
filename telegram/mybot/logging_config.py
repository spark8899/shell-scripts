import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    # Create a logger object
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Create a rotating file handler
    handler = RotatingFileHandler(
        'bot.log', # Name of the log file
        maxBytes=5*1024*1024,  # Maximum file size of 5MB
        backupCount=5 # Keep the last 5 log files
    )
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # Add the handler to the root logger
    logger.addHandler(handler)

    # setting httpx WARNING
    logging.getLogger("httpx").setLevel(logging.WARNING)

def get_logger(module_name):
    # Get a logger for the specified module
    return logging.getLogger(module_name)
