import logging
from logging.handlers import RotatingFileHandler

def setup_logger(name: str, path: str) -> logging.Logger:
    """Create a rotating file logger.

    Args:
        name (str): Logger name.
        path (str): Log file path.

    Returns:
        logging.Logger: Configured logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    handler = RotatingFileHandler(
        path,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )
    handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(handler)

    return logger
