# app/utils.py
import logging
from logging.handlers import RotatingFileHandler
from app.config import settings

def setup_logging():
    """
    Configures the application's logging.
    Sets up a rotating file handler based on settings.
    """
    log_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Configure file handler
    log_handler = RotatingFileHandler(
        filename=settings.LOG_FILE,
        maxBytes=settings.LOG_MAX_BYTES,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    log_handler.setFormatter(log_formatter)

    # Get the root logger and add the handler
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO) # Set the desired log level

    # Avoid adding handler multiple times if setup_logging is called again
    if not any(isinstance(h, RotatingFileHandler) for h in root_logger.handlers):
        root_logger.addHandler(log_handler)

    # Optionally, add a stream handler for console output during development
    # console_handler = logging.StreamHandler()
    # console_handler.setFormatter(log_formatter)
    # if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
    #     root_logger.addHandler(console_handler)

    logging.info("Logging configured.")
